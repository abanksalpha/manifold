# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import enum
import json
import logging
import mimetypes
import os
import re
import secrets
import select
import subprocess
import sys
import threading
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from errno import EPROTOTYPE
from http import HTTPStatus
from pathlib import Path

import flask
import stringcase
import waitress.wasyncore
from flask import Response, abort, request
from waitress.server import create_server

import aqt
import aqt.main
import aqt.operations
from anki import hooks
from anki.collection import OpChangesOnly, Progress, SearchNode
from anki.decks import UpdateDeckConfigs, UpdateDeckConfigsMode
from anki.scheduler.v3 import SchedulingStatesWithContext, SetSchedulingStatesRequest
from anki.utils import dev_mode
from aqt.changenotetype import ChangeNotetypeDialog
from aqt.deckoptions import DeckOptionsDialog
from aqt.operations import on_op_finished
from aqt.operations.deck import update_deck_configs as update_deck_configs_op
from aqt.progress import ProgressUpdate
from aqt.qt import *
from aqt.utils import aqt_data_path, show_warning, tr

# https://forums.ankiweb.net/t/anki-crash-when-using-a-specific-deck/22266
waitress.wasyncore._DISCONNECTED = waitress.wasyncore._DISCONNECTED.union({EPROTOTYPE})  # type: ignore

logger = logging.getLogger(__name__)
app = flask.Flask(__name__, root_path="/fake")


@dataclass
class LocalFileRequest:
    # base folder, eg media folder
    root: str
    # path to file relative to root folder
    path: str
    # collection media is untrusted user content; add-on web exports are not
    untrusted: bool = True


UNTRUSTED_MEDIA_CSP = "; ".join(
    (
        "default-src 'none'",
        "script-src 'none'",
        "connect-src 'none'",
        "object-src 'none'",
        "frame-src 'none'",
        "child-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "sandbox",
    )
)


def _editor_content_security_policy(port: int) -> str:
    csp_paths = (
        f"http://127.0.0.1:{port}/_anki/",
        f"http://127.0.0.1:{port}/_addons/",
    )
    return "; ".join((f"script-src {' '.join(csp_paths)}",))


@dataclass
class BundledFileRequest:
    # path relative to aqt data folder
    path: str


@dataclass
class NotFound:
    message: str


DynamicRequest = Callable[[], Response]


class PageContext(enum.IntEnum):
    UNKNOWN = enum.auto()
    EDITOR = enum.auto()
    REVIEWER = enum.auto()
    PREVIEWER = enum.auto()
    CARD_LAYOUT = enum.auto()
    DECK_OPTIONS = enum.auto()
    # something in /_anki/pages/
    NON_LEGACY_PAGE = enum.auto()
    # Do not use this if you present user content (e.g. content from cards), as it's a
    # security issue.
    ADDON_PAGE = enum.auto()


@dataclass
class LegacyPage:
    html: str
    context: PageContext


class MediaServer(threading.Thread):
    _ready = threading.Event()
    daemon = True

    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        super().__init__()
        self.is_shutdown = False
        # map of webview ids to pages
        self._legacy_pages: dict[int, LegacyPage] = {}

    def run(self) -> None:
        try:
            desired_host = os.getenv("ANKI_API_HOST", "127.0.0.1")
            desired_port = int(os.getenv("ANKI_API_PORT") or 0)
            self.server = create_server(
                app,
                host=desired_host,
                port=desired_port,
                clear_untrusted_proxy_headers=True,
                # Manifold generates each problem by shelling out to serve_live.py,
                # and that handler blocks its worker thread for the whole subprocess
                # (up to _MANIFOLD_SERVE_TIMEOUT). The session page keeps a few of
                # those generating in the background, so with waitress's default of 4
                # threads a burst of prefetches could hold every worker and stall an
                # unrelated request — e.g. the dashboard route's backend load — until
                # one finished. Give the pool enough headroom that navigation and the
                # page's own asset requests always get a free worker during generation.
                threads=12,
            )
            logger.info(
                "Serving on http://%s:%s",
                self.server.effective_host,  # type: ignore[union-attr]
                self.server.effective_port,  # type: ignore[union-attr]
            )

            self._ready.set()
            self.server.run()

        except Exception:
            if not self.is_shutdown:
                raise

    def shutdown(self) -> None:
        self.is_shutdown = True
        sockets = list(self.server._map.values())  # type: ignore
        for socket in sockets:
            socket.handle_close()
        # https://github.com/Pylons/webtest/blob/4b8a3ebf984185ff4fefb31b4d0cf82682e1fcf7/webtest/http.py#L93-L104
        self.server.task_dispatcher.shutdown()

    def getPort(self) -> int:
        self._ready.wait()
        return int(self.server.effective_port)  # type: ignore

    def set_page_html(
        self, id: int, html: str, context: PageContext = PageContext.UNKNOWN
    ) -> None:
        self._legacy_pages[id] = LegacyPage(html, context)

    def get_page(self, id: int) -> LegacyPage | None:
        return self._legacy_pages.get(id)

    def get_page_html(self, id: int) -> str | None:
        if page := self.get_page(id):
            return page.html
        else:
            return None

    def get_page_context(self, id: int) -> PageContext | None:
        if page := self.get_page(id):
            return page.context
        else:
            return None

    def clear_page_html(self, id: int) -> None:
        try:
            del self._legacy_pages[id]
        except KeyError:
            pass


@app.route("/favicon.ico")
def favicon() -> Response:
    request = BundledFileRequest(os.path.join("imgs", "favicon.ico"))
    return _handle_builtin_file_request(request)


def _mime_for_path(path: str) -> str:
    "Mime type for provided path/filename."

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    # Badly-behaved apps on Windows can alter the standard mime types in the registry, which can completely
    # break Anki's UI. So we hard-code the most common extensions.
    mime_types = {
        ".css": "text/css",
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".html": "text/html",
        ".htm": "text/html",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".ico": "image/x-icon",
        ".json": "application/json",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogg": "audio/ogg",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }

    if mime := mime_types.get(ext):
        return mime
    else:
        # fallback to mimetypes, which may consult the registry
        mime, _encoding = mimetypes.guess_type(path)
        return mime or "application/octet-stream"


def _text_response(code: HTTPStatus, text: str) -> Response:
    """Return an error message.

    Response is returned as text/plain, so no escaping of untrusted
    input is required."""
    resp = flask.make_response(text, code)
    resp.headers["Content-type"] = "text/plain"
    return resp


class UnsafePathException(Exception):
    def __init__(self, path: str):
        super().__init__(f"Invalid path: {path}")


def ensure_safe_path(base_dir: str | Path, path: str | Path) -> str:
    base_dir = os.path.realpath(base_dir)
    path = os.path.normpath(path)
    fullpath = os.path.abspath(os.path.join(base_dir, path))

    # protect against directory traversal: https://security.openstack.org/guidelines/dg_using-file-paths.html
    if not fullpath.startswith(base_dir + os.sep):
        raise UnsafePathException(path)
    return fullpath


_LOCALHOST_HOSTS = ("127.0.0.1", "localhost", "[::1]")

_ALLOWED_ORIGIN_PREFIXES = tuple(
    f"{scheme}{host}" for scheme in ("http://", "https://") for host in _LOCALHOST_HOSTS
)


def is_localhost_origin(origin: str) -> bool:
    for prefix in _ALLOWED_ORIGIN_PREFIXES:
        if (
            origin == prefix
            or origin.startswith(prefix + ":")
            or origin.startswith(prefix + "/")
        ):
            return True
    return False


def _handle_local_file_request(request: LocalFileRequest) -> Response:
    directory = request.root
    path = request.path
    try:
        isdir = os.path.isdir(os.path.join(directory, path))
    except ValueError:
        return _text_response(
            HTTPStatus.BAD_REQUEST, f"Path for '{directory} - {path}' is too long!"
        )

    fullpath = ensure_safe_path(directory, path)

    if isdir:
        return _text_response(
            HTTPStatus.FORBIDDEN,
            f"Path for '{directory} - {path}' is a directory (not supported)!",
        )

    try:
        mimetype = _mime_for_path(fullpath)
        if os.path.exists(fullpath):
            if fullpath.endswith(".css"):
                # caching css files prevents flicker in the webview, but we want
                # a short cache
                max_age = 10
            elif fullpath.endswith(".js") or fullpath.endswith(".mjs"):
                # don't cache js/mjs files. SvelteKit ships ES modules as .mjs; if
                # those fall through to the long-cache branch the webview keeps
                # serving stale bundles after a rebuild, so a code change appears to
                # have no effect until the cache expires.
                max_age = 0
            else:
                max_age = 60 * 60
            response = flask.send_file(
                fullpath,
                mimetype=mimetype,
                conditional=True,
                max_age=max_age,
                download_name="foo",  # type: ignore[call-arg]
            )
            if request.untrusted:
                # Prevent user-provided HTML/SVG from running as an active document.
                response.headers["Content-Security-Policy"] = UNTRUSTED_MEDIA_CSP
            return response
        else:
            print(f"Not found: {path}")
            return _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {path}")

    except Exception as error:
        if dev_mode:
            print(
                "Caught HTTP server exception,\n%s"
                % "".join(traceback.format_exception(*sys.exc_info())),
            )

        # swallow it - user likely surfed away from
        # review screen before an image had finished
        # downloading
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))


def _builtin_data(path: str) -> bytes:
    """Return data from file in aqt/data folder."""
    full_path = ensure_safe_path(aqt_data_path().parent, path)
    with open(full_path, "rb") as f:
        return f.read()


def _handle_builtin_file_request(request: BundledFileRequest) -> Response:
    path = request.path
    # do we need to serve the fallback page?
    immutable = "immutable" in path
    if path.startswith("sveltekit/") and not immutable:
        path = "sveltekit/index.html"
    mimetype = _mime_for_path(path)
    data_path = f"data/web/{path}"
    try:
        data = _builtin_data(data_path)
        response = Response(data, mimetype=mimetype)
        if immutable:
            response.headers["Cache-Control"] = "max-age=31536000"
        return response
    except FileNotFoundError:
        if dev_mode:
            print(f"404: {data_path}")
        resp = _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {path}")
        # we're including the path verbatim in our response, so we need to either use
        # plain text, or escape HTML characters to avoid reflecting untrusted input
        resp.headers["Content-type"] = "text/plain"
        return resp
    except Exception as error:
        if dev_mode:
            print(
                "Caught HTTP server exception,\n%s"
                % "".join(traceback.format_exception(*sys.exc_info())),
            )

        # swallow it - user likely surfed away from
        # review screen before an image had finished
        # downloading
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))


@app.route("/<path:pathin>", methods=["GET", "POST"])
def handle_request(pathin: str) -> Response:
    if os.environ.get("ANKI_API_HOST") != "0.0.0.0":
        host = request.headers.get("Host", "").lower()
        origin = request.headers.get("Origin", "").lower()
        allowed_hosts = tuple(f"{h}:" for h in _LOCALHOST_HOSTS)
        if not any(host.startswith(h) for h in allowed_hosts):
            logger.warning("denied non-local host: %s", host)
            abort(403)
        if origin and not is_localhost_origin(origin):
            logger.warning("denied non-local origin: %s", origin)
            abort(403)

    req = _extract_request(pathin)
    logger.debug("%s /%s", flask.request.method, pathin)

    try:
        if isinstance(req, NotFound):
            print(req.message)
            return _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {pathin}")
        elif callable(req):
            return _handle_dynamic_request(req)
        elif isinstance(req, BundledFileRequest):
            return _handle_builtin_file_request(req)
        elif isinstance(req, LocalFileRequest):
            return _handle_local_file_request(req)
        else:
            return _text_response(HTTPStatus.FORBIDDEN, f"unexpected request: {pathin}")
    except UnsafePathException as exc:
        return _text_response(HTTPStatus.FORBIDDEN, str(exc))


def is_sveltekit_page(path: str) -> bool:
    page_name = path.split("/")[0]
    return page_name in [
        "graphs",
        "congrats",
        "manifold",
        "manifold-dashboard",
        "manifold-onboarding",
        "manifold-session",
        "card-info",
        "change-notetype",
        "deck-options",
        "import-anki-package",
        "import-csv",
        "import-page",
        "image-occlusion",
    ]


def _extract_internal_request(
    path: str,
) -> BundledFileRequest | DynamicRequest | NotFound | None:
    "Catch /_anki references and rewrite them to web export folder."
    if is_sveltekit_page(path):
        path = f"_anki/sveltekit/_app/{path}"
    if path.startswith("_app/"):
        path = path.replace("_app", "_anki/sveltekit/_app")

    prefix = "_anki/"
    if not path.startswith(prefix):
        return None

    dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    additional_prefix = None

    if dirname == "_anki":
        if flask.request.method == "POST":
            return _extract_collection_post_request(filename)
        elif get_handler := _extract_dynamic_get_request(filename):
            return get_handler

        # remap legacy top-level references
        base, ext = os.path.splitext(filename)
        if ext == ".css":
            additional_prefix = "css/"
        elif ext == ".js":
            if base in ("jquery-ui", "jquery", "plot"):
                additional_prefix = "js/vendor/"
            else:
                additional_prefix = "js/"
    # handle requests for vendored libraries
    elif dirname == "_anki/js/vendor":
        base, ext = os.path.splitext(filename)

        if base == "jquery":
            base = "jquery.min"
            additional_prefix = "js/vendor/"

        elif base == "jquery-ui":
            base = "jquery-ui.min"
            additional_prefix = "js/vendor/"

    if additional_prefix:
        oldpath = path
        path = f"{prefix}{additional_prefix}{base}{ext}"
        print(f"legacy {oldpath} remapped to {path}")

    return BundledFileRequest(path=path[len(prefix) :])


def _extract_addon_request(path: str) -> LocalFileRequest | NotFound | None:
    "Catch /_addons references and rewrite them to addons folder."
    prefix = "_addons/"
    if not path.startswith(prefix):
        return None

    addon_path = path[len(prefix) :]

    try:
        manager = aqt.mw.addonManager
    except AttributeError as error:
        if dev_mode:
            print(f"_redirectWebExports: {error}")
        return None

    try:
        addon, sub_path = addon_path.split("/", 1)
    except ValueError:
        return None
    if not addon:
        return None

    pattern = manager.getWebExports(addon)
    if not pattern:
        return None

    if re.fullmatch(pattern, sub_path):
        return LocalFileRequest(
            root=manager.addonsFolder(), path=addon_path, untrusted=False
        )

    return NotFound(message=f"couldn't locate item in add-on folder {path}")


def _extract_request(
    path: str,
) -> LocalFileRequest | BundledFileRequest | DynamicRequest | NotFound:
    if internal := _extract_internal_request(path):
        return internal
    elif addon := _extract_addon_request(path):
        return addon

    if not aqt.mw.col:
        return NotFound(message=f"collection not open, ignore request for {path}")

    path = hooks.media_file_filter(path)
    return LocalFileRequest(root=aqt.mw.col.media.dir(), path=path)


def congrats_info() -> bytes:
    if not aqt.mw.col.sched._is_finished():
        aqt.mw.taskman.run_on_main(lambda: aqt.mw.moveToState("overview"))
    return raw_backend_request("congrats_info")()


def get_deck_configs_for_update() -> bytes:
    return aqt.mw.col._backend.get_deck_configs_for_update_raw(request.data)


def _on_update_deck_configs_success(input: UpdateDeckConfigs) -> None:
    is_compute_all = (
        input.mode == UpdateDeckConfigsMode.UPDATE_DECK_CONFIGS_MODE_COMPUTE_ALL_PARAMS
    )
    if not is_compute_all and isinstance(
        window := aqt.mw.app.activeModalWidget(), DeckOptionsDialog
    ):
        window.reject()


def update_deck_configs() -> bytes:
    # the regular change tracking machinery expects to be started on the main
    # thread and uses a callback on success, so we need to run this op on
    # main, and return immediately from the web request

    input = UpdateDeckConfigs()
    input.ParseFromString(request.data)

    def on_progress(progress: Progress, update: ProgressUpdate) -> None:
        if progress.HasField("compute_memory"):
            val = progress.compute_memory
            update.max = val.total_cards
            update.value = val.current_cards
            update.label = val.label
        elif progress.HasField("compute_params"):
            val2 = progress.compute_params
            # prevent an indeterminate progress bar from appearing at the start of each preset
            update.max = max(val2.total, 1)
            update.value = val2.current
            pct = str(int(val2.current / val2.total * 100) if val2.total > 0 else 0)
            label = tr.deck_config_optimizing_preset(
                current_count=val2.current_preset, total_count=val2.total_presets
            )
            if val2.reviews:
                reviews = tr.deck_config_percent_of_reviews(
                    pct=pct, reviews=val2.reviews
                )
            else:
                reviews = tr.qt_misc_processing()

            update.label = label + "\n" + reviews
        else:
            return
        if update.user_wants_abort:
            update.abort = True

    def handle_on_main() -> None:
        update_deck_configs_op(parent=aqt.mw, input=input).success(
            lambda _: _on_update_deck_configs_success(input)
        ).with_backend_progress(on_progress).run_in_background()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def get_scheduling_states_with_context() -> bytes:
    return SchedulingStatesWithContext(
        states=aqt.mw.reviewer.get_scheduling_states(),
        context=aqt.mw.reviewer.get_scheduling_context(),
    ).SerializeToString()


def set_scheduling_states() -> bytes:
    states = SetSchedulingStatesRequest()
    states.ParseFromString(request.data)
    aqt.mw.reviewer.set_scheduling_states(states)
    return b""


def import_done() -> bytes:
    def update_window_modality() -> None:
        if window := aqt.mw.app.activeModalWidget():
            from aqt.import_export.import_dialog import ImportDialog

            if isinstance(window, ImportDialog):
                window.hide()
                window.setWindowModality(Qt.WindowModality.NonModal)
                window.show()

    aqt.mw.taskman.run_on_main(update_window_modality)
    return b""


def import_request(endpoint: str) -> bytes:
    output = raw_backend_request(endpoint)()
    response = OpChangesOnly()
    response.ParseFromString(output)

    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        on_op_finished(aqt.mw, response, window)

    aqt.mw.taskman.run_on_main(handle_on_main)

    return output


def import_csv() -> bytes:
    return import_request("import_csv")


def import_anki_package() -> bytes:
    return import_request("import_anki_package")


def import_json_file() -> bytes:
    return import_request("import_json_file")


def import_json_string() -> bytes:
    return import_request("import_json_string")


def search_in_browser() -> bytes:
    node = SearchNode()
    node.ParseFromString(request.data)

    def handle_on_main() -> None:
        aqt.dialogs.open("Browser", aqt.mw, search=(node,))

    aqt.mw.taskman.run_on_main(handle_on_main)

    return b""


def change_notetype() -> bytes:
    data = request.data

    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, ChangeNotetypeDialog):
            window.save(data)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def deck_options_require_close() -> bytes:
    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, DeckOptionsDialog):
            window.require_close()

    # on certain linux systems, askUser's QMessageBox.question unsets the active window
    # so we wait for the next event loop before querying the next current active window
    aqt.mw.taskman.run_on_main(lambda: QTimer.singleShot(0, handle_on_main))
    return b""


def deck_options_ready() -> bytes:
    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, DeckOptionsDialog):
            window.set_ready()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def save_custom_colours() -> bytes:
    colors = [
        QColorDialog.customColor(i).name(QColor.NameFormat.HexRgb)
        for i in range(QColorDialog.customCount())
    ]
    aqt.mw.col.set_config("customColorPickerPalette", colors)
    return b""


# --- Manifold live problem generation (D44) ------------------------------------
# The runtime problem source is on-the-fly generation, not a persisted bank. The
# session page POSTs a due skill here; we shell out to the content-generation venv
# (which owns SymPy/Z3, kept out of the Anki runtime) to run serve_live.py, which
# generates a candidate, verifies it with verify.py (verification stays in the
# loop), and returns a verified item or an explicit ABSTAIN. No fabrication, no
# bank fallback: when a verified problem cannot be produced, the honest ABSTAIN is
# passed straight through for the UI to show.

_MANIFOLD_SERVE_TIMEOUT = 120  # generous: up to ~3 generate+verify attempts
_MANIFOLD_HINT_TIMEOUT = 60  # a hint is one model call, so far quicker than a problem


def _manifold_abstain_bytes(reason: str, detail: str) -> bytes:
    return json.dumps({"status": "abstain", "reason": reason, "detail": detail}).encode(
        "utf-8"
    )


def _manifold_generation_paths(
    script_name: str = "serve_live.py",
    script_override_env: str = "MANIFOLD_SERVE_LIVE",
) -> tuple[str, str] | None:
    """(python, <script>) for the content-generation venv, or None if absent.

    Honors the given script-override env and MANIFOLD_GEN_PYTHON, else walks up from
    this file to find manifold/content/generation/<script_name> (works whether aqt
    runs from source or an out/ copy). Both live-problem generation and the hint
    assistant share this venv resolution."""
    script = os.environ.get(script_override_env)
    python = os.environ.get("MANIFOLD_GEN_PYTHON")
    if not script:
        for parent in Path(__file__).resolve().parents:
            # Source checkout: the generation dir with its own .venv.
            candidate = parent / "manifold" / "content" / "generation" / script_name
            if candidate.exists():
                script = str(candidate)
                break
            # Packaged (Briefcase) standalone: a bundled generation dir + a relocatable
            # sidecar Python (with sympy/z3/numpy) sit in the app's Resources, so the
            # signed app generates problems with no dev source tree or venv present.
            bundled = parent / "manifold_gen" / script_name
            if bundled.exists():
                script = str(bundled)
                if not python:
                    for pyname in ("python3.13", "python3", "python"):
                        cand_py = parent / "manifold_py" / "bin" / pyname
                        if cand_py.exists():
                            python = str(cand_py)
                            break
                break
    if not script or not os.path.exists(script):
        return None
    if not python:
        python = str(Path(script).resolve().parent / ".venv" / "bin" / "python")
    if not os.path.exists(python):
        return None
    return python, script


# --- warm generation worker (deterministic fast path) --------------------------
# Shelling out a fresh Python per problem re-imports sympy/z3 and re-parses the
# template bank each time (~0.3s of pure cold-start) — which dominates a templated
# problem whose actual work is milliseconds. This keeps ONE serve_live.py
# --serve-daemon alive with all of that loaded, so a templated / banked problem is
# served in ms. A skill needing live LLM generation returns needs_live and is
# served by the cold path below (unchanged). Access is serialized: a fast serve is
# ms and a needs_live verdict returns at once, so the lock never wraps an LLM call.
_MANIFOLD_WORKER: subprocess.Popen | None = None
_MANIFOLD_WORKER_LOCK = threading.Lock()
_MANIFOLD_WORKER_READ_TIMEOUT = 15.0  # ms in practice; only guards a wedged worker


def _manifold_start_worker(python: str, script: str) -> subprocess.Popen | None:
    try:
        proc = subprocess.Popen(  # noqa: S603
            [python, script, "--serve-daemon"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    # Block until the daemon signals it has warmed (imports + banks loaded).
    ready = proc.stdout.readline() if proc.stdout else b""
    if not ready:
        proc.kill()
        return None
    return proc


def _manifold_serve_fast(python: str, script: str, body: bytes) -> bytes | None:
    """Serve one problem via the warm worker's deterministic path, or None to tell
    the caller to use the cold (LLM) path. Never raises: any worker trouble simply
    falls back to the cold path so a problem is still served."""
    if os.name != "posix":
        return None  # the worker read uses select(); other platforms use the cold path
    global _MANIFOLD_WORKER
    with _MANIFOLD_WORKER_LOCK:
        if _MANIFOLD_WORKER is None or _MANIFOLD_WORKER.poll() is not None:
            _MANIFOLD_WORKER = _manifold_start_worker(python, script)
        worker = _MANIFOLD_WORKER
        if worker is None or worker.stdin is None or worker.stdout is None:
            return None
        try:
            worker.stdin.write(body.strip() + b"\n")
            worker.stdin.flush()
            readable, _, _ = select.select(
                [worker.stdout], [], [], _MANIFOLD_WORKER_READ_TIMEOUT
            )
            if not readable:
                worker.kill()
                _MANIFOLD_WORKER = None
                return None
            line = worker.stdout.readline()
        except (BrokenPipeError, OSError, ValueError):
            _MANIFOLD_WORKER = None
            return None
    if not line:
        return None
    try:
        status = json.loads(line).get("status")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    # A served (or honestly-abstained) deterministic item is passed straight through;
    # needs_live / error falls through to the cold path.
    return line.strip() if status in ("ok", "abstain") else None


def manifold_next_problem() -> bytes:
    """Serve one Manifold problem, or a JSON ABSTAIN.

    Always returns a JSON verdict (``status`` ``ok`` or ``abstain``); the real
    reason is surfaced, never hidden and never faked. Templated / banked skills are
    served from the warm worker in milliseconds; skills that need live generation
    take the cold verify-in-the-loop path. The request body is the JSON skill spec
    from the session page."""
    paths = _manifold_generation_paths()
    if paths is None:
        return _manifold_abstain_bytes(
            "serve_live_unavailable",
            "the content-generation runtime (serve_live.py + its .venv) was not found; "
            "cannot generate a verified problem",
        )
    python, script = paths
    body = request.data or b"{}"
    # Fast path: a templated or banked problem, served from the warm worker in ms.
    fast = _manifold_serve_fast(python, script, body)
    if fast is not None:
        return fast
    try:
        proc = subprocess.run(
            [python, script, "--request-json", "-"],
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_MANIFOLD_SERVE_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _manifold_abstain_bytes(
            "generation_timeout",
            f"live generation did not finish within {_MANIFOLD_SERVE_TIMEOUT}s",
        )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        logger.warning(
            "manifold serve_live failed (exit %s): %s", proc.returncode, detail
        )
        return _manifold_abstain_bytes(
            "generation_failed", detail[:500] or f"serve_live exited {proc.returncode}"
        )
    out = proc.stdout.strip()
    if not out:
        return _manifold_abstain_bytes(
            "generation_failed", "serve_live produced no output"
        )
    try:
        json.loads(out)  # validate; pass the verdict through verbatim
    except json.JSONDecodeError as exc:
        return _manifold_abstain_bytes(
            "generation_failed", f"serve_live output was not valid JSON: {exc}"
        )
    return out


# --- Manifold lectures (Task 1) ------------------------------------------------
# New-skill teaching: a teach ("new") skill can carry a short, pre-authored lecture
# (method name + when to use it, a worked walk-through of a VERIFIED banked item, and
# a key takeaway) anchored to an item in teach_bank.json. Lectures are served from a
# static, pre-authored artifact (manifold/content/lectures/lectures.json), never
# generated live — the same "vetted content, no runtime fabrication" rule as the
# teach bank. A skill with no lecture yet is an honest "none", never a faked one.

_MANIFOLD_LECTURES_CACHE: dict[str, dict] | None = None


def _manifold_lectures_path() -> str | None:
    """Path to lectures.json (MANIFOLD_LECTURES override, else walk up to the repo)."""
    override = os.environ.get("MANIFOLD_LECTURES")
    if override:
        return override
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "manifold" / "content" / "lectures" / "lectures.json"
        if candidate.exists():
            return str(candidate)
    return None


def _load_manifold_lectures() -> dict[str, dict]:
    """Index lectures as skill_id -> lecture object, cached.

    A missing default file means "no lectures authored yet" (every lookup is an
    honest 'none'); an explicitly-configured MANIFOLD_LECTURES path that is missing
    or malformed fails loudly rather than degrading silently."""
    global _MANIFOLD_LECTURES_CACHE
    if _MANIFOLD_LECTURES_CACHE is not None:
        return _MANIFOLD_LECTURES_CACHE
    index: dict[str, dict] = {}
    path = _manifold_lectures_path()
    override = os.environ.get("MANIFOLD_LECTURES")
    if path and os.path.exists(path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        lectures = data.get("lectures") if isinstance(data, dict) else data
        for sid, lec in (lectures or {}).items():
            if isinstance(lec, dict) and lec.get("lecture_latex"):
                index[sid] = lec
    elif override:
        # A configured path that does not exist is a real setup error, not a gap.
        raise FileNotFoundError(
            f"MANIFOLD_LECTURES points to a missing file: {override}"
        )
    _MANIFOLD_LECTURES_CACHE = index
    return index


def manifold_lecture() -> bytes:
    """Return the pre-authored lecture for a teach skill, or an honest 'none'.

    Body is the JSON skill spec from the session page ({"skill_id": ...}). Returns
    ``{"status":"ok","lecture":{...}}`` when a lecture is authored for that skill, or
    ``{"status":"none","reason":"no_lecture"}`` when none exists yet. Never fabricates
    a lecture; a skill without one simply teaches through its worked solution."""
    body = request.data or b"{}"
    try:
        skill = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return json.dumps(
            {
                "status": "none",
                "reason": "bad_request",
                "detail": f"invalid request: {exc}",
            }
        ).encode("utf-8")
    skill_id = (skill or {}).get("skill_id")
    if not skill_id:
        return json.dumps(
            {"status": "none", "reason": "bad_request", "detail": "missing skill_id"}
        ).encode("utf-8")
    lecture = _load_manifold_lectures().get(skill_id)
    if lecture is None:
        return json.dumps({"status": "none", "reason": "no_lecture"}).encode("utf-8")
    return json.dumps({"status": "ok", "lecture": lecture}, ensure_ascii=False).encode(
        "utf-8"
    )


# --- Manifold hint assistant ---------------------------------------------------
# The session page lets a stuck learner ask a question about the current problem and
# get one hint back. We shell out to hint.py in the content-generation venv (same
# runtime resolution as live generation), which asks the model for a nudge toward
# the method and is given only the stem and choices the learner already sees, never
# the answer or the worked solution. It returns a verified-shape JSON verdict
# ({"status":"ok","hint":...} or an honest {"status":"abstain",...}); no fabricated
# hint, no canned fallback.


def manifold_import_seed() -> bytes:
    """Import the GRE seed deck into the open collection (idempotent).

    Reuses manifold/content/import_seed.py so onboarding on a fresh profile has
    skill cards to diagnose. Fails loudly (surfaced as JSON) if the seed or
    blueprint files are missing; never fabricates content."""
    import importlib.util

    script = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "manifold" / "content" / "import_seed.py"
        if candidate.exists():
            script = candidate
            break
    if script is None:
        return json.dumps(
            {"status": "error", "detail": "import_seed.py not found"}
        ).encode("utf-8")

    spec = importlib.util.spec_from_file_location(
        "manifold_import_seed_mod", str(script)
    )
    if spec is None or spec.loader is None:
        return json.dumps(
            {"status": "error", "detail": "could not load import_seed.py"}
        ).encode("utf-8")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import_seed_fn = getattr(module, "import_seed")
    added, skipped = import_seed_fn(aqt.mw.col)
    return json.dumps(
        {
            "status": "ok",
            "added": sum(added.values()),
            "skipped": sum(skipped.values()),
        }
    ).encode("utf-8")


def manifold_sync() -> bytes:
    """Trigger an Anki collection + media sync in the background so a finished
    Manifold session propagates to the learner's other devices (AnkiWeb or the
    configured server) without waiting for app close.

    Runs on the main thread (Qt sync touches the UI). No-op — not an error — when
    the user has not signed in to sync yet (nothing to sync to) or a sync is already
    running; a real sync failure surfaces through Anki's own sync error UI."""
    mw = aqt.mw
    if mw is None:
        return json.dumps({"status": "error", "detail": "no main window"}).encode(
            "utf-8"
        )

    def run() -> None:
        if mw.pm.sync_auth() is None:
            return  # not signed in to sync yet; nothing to sync to
        if mw.media_syncer.is_syncing():
            return  # a sync is already running
        mw._sync_collection_and_media(lambda: None)

    mw.taskman.run_on_main(run)
    return json.dumps({"status": "ok"}).encode("utf-8")


def manifold_hint() -> bytes:
    """Serve one answer-free hint for the current problem, or a JSON ABSTAIN.

    Always returns a JSON verdict (``status`` ``ok`` or ``abstain``); the real reason
    is surfaced, never hidden and never faked. The request body is the JSON problem
    context ({stem, choices, question, ...}) the session page POSTs."""
    paths = _manifold_generation_paths("hint.py", "MANIFOLD_HINT_SCRIPT")
    if paths is None:
        return _manifold_abstain_bytes(
            "hint_unavailable",
            "the content-generation runtime (hint.py + its .venv) was not found; "
            "cannot produce a hint",
        )
    python, script = paths
    body = request.data or b"{}"
    try:
        proc = subprocess.run(
            [python, script, "--request-json", "-"],
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_MANIFOLD_HINT_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _manifold_abstain_bytes(
            "hint_timeout",
            f"the hint did not finish within {_MANIFOLD_HINT_TIMEOUT}s",
        )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        logger.warning("manifold hint failed (exit %s): %s", proc.returncode, detail)
        return _manifold_abstain_bytes(
            "hint_error", detail[:500] or f"hint.py exited {proc.returncode}"
        )
    out = proc.stdout.strip()
    if not out:
        return _manifold_abstain_bytes("hint_error", "hint.py produced no output")
    try:
        json.loads(out)  # validate; pass the verdict through verbatim
    except json.JSONDecodeError as exc:
        return _manifold_abstain_bytes(
            "hint_error", f"hint.py output was not valid JSON: {exc}"
        )
    return out


# --- desktop Google sign-in (system-browser loopback) --------------------------
# Google blocks its OAuth consent screen inside embedded webviews
# ("disallowed_useragent"), so the Qt desktop shell cannot run signInWithPopup in
# its own webview. Instead this endpoint runs a one-shot loopback: it opens the
# user's real system browser to a tiny local page that performs the normal
# Firebase `signInWithPopup`, harvests the resulting Google ID token, and posts it
# back to this loopback server. The desktop webview then completes sign-in with
# `signInWithCredential(GoogleAuthProvider.credential(idToken))`.
#
# No secret and no extra OAuth client are needed: the popup runs in a REAL browser
# (where Google allows it) on the `localhost` authorized domain, using the same
# public web config as the app, and the harvested ID token's audience is exactly
# the project's web client — the one Firebase expects. Fails loud on any error.

_MANIFOLD_SIGNIN_PORT = 41599
_MANIFOLD_SIGNIN_TIMEOUT = 300  # seconds for the human to finish Google sign-in
_MANIFOLD_FIREBASE_SDK_VERSION = "12.15.0"
# Public web config (mirrors ts/lib/manifold/firebase.config.ts). Not a secret.
_MANIFOLD_FIREBASE_WEB_CONFIG = {
    "apiKey": "AIzaSyBI__PYNZ29WGUkk5nm6Y8Qay4sBQE-sAU",
    "authDomain": "manifold-gre.firebaseapp.com",
    "projectId": "manifold-gre",
    "storageBucket": "manifold-gre.firebasestorage.app",
    "messagingSenderId": "451162963698",
    "appId": "1:451162963698:web:7a00e66f0866fab4709a6b",
}


def _manifold_signin_html() -> str:
    """The standalone page served on the loopback: a real-browser Google popup
    that harvests the Google ID token and posts it back to /token."""
    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sign in to Manifold</title>
<style>
  body { font-family: system-ui, sans-serif; background:#f4f1ea; color:#16131c;
    display:flex; min-height:100vh; margin:0; align-items:center; justify-content:center; }
  .card { border:3px solid #16131c; background:#fff; box-shadow:6px 6px 0 0 #16131c;
    padding:28px 32px; max-width:380px; text-align:center; }
  h1 { margin:0 0 6px; font-size:1.3rem; }
  p { opacity:0.8; }
  button { border:3px solid #16131c; background:#ff6b6b; color:#16131c; font-weight:800;
    box-shadow:3px 3px 0 0 #16131c; padding:12px 20px; font-size:1rem; cursor:pointer; }
  button:disabled { opacity:0.6; cursor:default; }
  .err { color:#b00020; font-weight:700; }
</style>
</head>
<body>
<div class="card">
  <h1>Manifold</h1>
  <p id="status">Sign in with Google to sync your progress to this device.</p>
  <button id="go">Continue with Google</button>
</div>
<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/__SDK__/firebase-app.js";
  import { getAuth, GoogleAuthProvider, signInWithPopup }
    from "https://www.gstatic.com/firebasejs/__SDK__/firebase-auth.js";

  const app = initializeApp(__CONFIG__);
  const auth = getAuth(app);
  const statusEl = document.getElementById("status");
  const btn = document.getElementById("go");

  async function post(payload) {
    await fetch("/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    statusEl.textContent = "Opening Google sign-in…";
    try {
      const result = await signInWithPopup(auth, new GoogleAuthProvider());
      const credential = GoogleAuthProvider.credentialFromResult(result);
      const idToken = credential && credential.idToken;
      if (!idToken) {
        throw new Error("Google did not return an ID token");
      }
      await post({ id_token: idToken });
      statusEl.textContent = "Signed in. You can close this tab and return to Manifold.";
    } catch (e) {
      statusEl.className = "err";
      statusEl.textContent = "Sign-in failed: " + (e && e.message ? e.message : e);
      await post({ error: (e && e.message) ? e.message : String(e) });
    }
  });
</script>
</body>
</html>"""
    return template.replace("__SDK__", _MANIFOLD_FIREBASE_SDK_VERSION).replace(
        "__CONFIG__", json.dumps(_MANIFOLD_FIREBASE_WEB_CONFIG)
    )


def manifold_google_sign_in() -> bytes:
    """Run the system-browser loopback and return the Google ID token as JSON.

    Returns ``{"status":"ok","id_token":...}`` on success, or
    ``{"status":"error","reason":...,"detail":...}`` on any failure (port in use,
    the user cancelling, a timeout) — never a fabricated token."""
    import webbrowser
    from http.server import BaseHTTPRequestHandler, HTTPServer

    result: dict[str, str] = {}
    done = threading.Event()
    html = _manifold_signin_html().encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:  # silence access logs
            pass

        def do_GET(self) -> None:  # noqa: N802
            if self.path in ("/", "/index.html") or self.path.startswith("/?"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
            else:
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/token":
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            if isinstance(payload.get("id_token"), str):
                result["id_token"] = payload["id_token"]
            elif isinstance(payload.get("error"), str):
                result["error"] = payload["error"]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            done.set()

    try:
        server = HTTPServer(("127.0.0.1", _MANIFOLD_SIGNIN_PORT), Handler)
    except OSError as exc:
        return json.dumps(
            {
                "status": "error",
                "reason": "loopback_unavailable",
                "detail": f"could not start the sign-in loopback on port "
                f"{_MANIFOLD_SIGNIN_PORT}: {exc}",
            }
        ).encode("utf-8")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        opened = webbrowser.open(f"http://localhost:{_MANIFOLD_SIGNIN_PORT}/")
        if not opened:
            return json.dumps(
                {
                    "status": "error",
                    "reason": "browser_unavailable",
                    "detail": "could not open a system browser for Google sign-in",
                }
            ).encode("utf-8")
        finished = done.wait(timeout=_MANIFOLD_SIGNIN_TIMEOUT)
    finally:
        server.shutdown()
        server.server_close()

    if not finished:
        return json.dumps(
            {
                "status": "error",
                "reason": "timeout",
                "detail": f"no sign-in completed within {_MANIFOLD_SIGNIN_TIMEOUT}s",
            }
        ).encode("utf-8")
    if "id_token" in result:
        return json.dumps({"status": "ok", "id_token": result["id_token"]}).encode(
            "utf-8"
        )
    return json.dumps(
        {
            "status": "error",
            "reason": "sign_in_failed",
            "detail": result.get("error", "the browser did not return a token"),
        }
    ).encode("utf-8")


post_handler_list = [
    congrats_info,
    get_deck_configs_for_update,
    update_deck_configs,
    get_scheduling_states_with_context,
    set_scheduling_states,
    change_notetype,
    import_done,
    import_csv,
    import_anki_package,
    import_json_file,
    import_json_string,
    search_in_browser,
    deck_options_require_close,
    deck_options_ready,
    save_custom_colours,
    manifold_next_problem,
    manifold_lecture,
    manifold_hint,
    manifold_import_seed,
    manifold_sync,
    manifold_google_sign_in,
]


exposed_backend_list = [
    # CollectionService
    "latest_progress",
    "get_custom_colours",
    # DeckService
    "get_deck_names",
    "get_deck_id_by_name",
    "set_current_deck",
    # I18nService
    "i18n_resources",
    # ImportExportService
    "get_csv_metadata",
    "get_import_anki_package_presets",
    # NotesService
    "get_field_names",
    "get_note",
    # NotetypesService
    "get_notetype_names",
    "get_change_notetype_info",
    # StatsService
    "card_stats",
    "get_review_logs",
    "graphs",
    "get_graph_preferences",
    "set_graph_preferences",
    # ManifoldService
    "get_topic_graph",
    "build_session_queue",
    "get_problems_solved",
    "get_placement_state",
    "build_placement_exam",
    "apply_placement",
    "claim_account",
    # TagsService
    "complete_tag",
    # ImageOcclusionService
    "get_image_for_occlusion",
    "add_image_occlusion_note",
    "get_image_occlusion_note",
    "update_image_occlusion_note",
    "get_image_occlusion_fields",
    # SchedulerService
    "get_queued_cards",
    "answer_card",
    "grade_now",
    "compute_fsrs_params",
    "compute_optimal_retention",
    "set_wants_abort",
    "evaluate_params_legacy",
    "get_optimal_retention_parameters",
    "simulate_fsrs_review",
    "simulate_fsrs_workload",
    # DeckConfigService
    "get_ignored_before_count",
    "get_retention_workload",
]


def raw_backend_request(endpoint: str) -> Callable[[], bytes]:
    # check for key at startup
    from anki._backend import RustBackend

    assert hasattr(RustBackend, f"{endpoint}_raw")

    return lambda: getattr(aqt.mw.col._backend, f"{endpoint}_raw")(request.data)


# all methods in here require a collection
post_handlers = {
    stringcase.camelcase(handler.__name__): handler for handler in post_handler_list
} | {
    stringcase.camelcase(handler): raw_backend_request(handler)
    for handler in exposed_backend_list
}


def _extract_collection_post_request(path: str) -> DynamicRequest | NotFound:
    if not aqt.mw.col:
        return NotFound(message=f"collection not open, ignore request for {path}")
    if handler := post_handlers.get(path):
        # convert bytes/None into response
        def wrapped() -> Response:
            try:
                if data := handler():
                    response = flask.make_response(data)
                    response.headers["Content-Type"] = "application/binary"
                else:
                    response = _text_response(HTTPStatus.NO_CONTENT, "")
            except Exception as exc:
                print(traceback.format_exc())
                response = _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return response

        return wrapped
    else:
        return NotFound(message=f"{path} not found")


def _check_dynamic_request_permissions():
    if request.method == "GET":
        return

    def warn() -> None:
        show_warning(
            "Unexpected API access. Please report this message on the Anki forums."
        )

    # check content type header to ensure this isn't an opaque request from another origin
    if request.headers["Content-type"] != "application/binary":
        aqt.mw.taskman.run_on_main(warn)
        abort(403)

    # does page have access to entire API?
    if _have_api_access():
        return

    # whitelisted API endpoints for reviewer/previewer
    if request.path in (
        "/_anki/getSchedulingStatesWithContext",
        "/_anki/setSchedulingStates",
        "/_anki/i18nResources",
        "/_anki/congratsInfo",
    ):
        pass
    else:
        # other legacy pages may contain third-party JS, so we do not
        # allow them to access our API
        aqt.mw.taskman.run_on_main(warn)
        abort(403)


def _handle_dynamic_request(req: DynamicRequest) -> Response:
    _check_dynamic_request_permissions()
    try:
        return req()
    except Exception as e:
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


def legacy_page_data() -> Response:
    id = int(request.args["id"])
    page = aqt.mw.mediaServer.get_page(id)
    if page:
        response = Response(page.html, mimetype="text/html")
        # Prevent JS in field content from being executed in the editor, as it would
        # have access to our internal API, and is a security risk.
        if page.context == PageContext.EDITOR:
            response.headers["Content-Security-Policy"] = (
                _editor_content_security_policy(aqt.mw.mediaServer.getPort())
            )
        return response
    else:
        return _text_response(HTTPStatus.NOT_FOUND, "page not found")


_APIKEY = secrets.token_urlsafe(32)


def _have_api_access() -> bool:
    return (
        request.headers.get("Authorization") == f"Bearer {_APIKEY}"
        or os.environ.get("ANKI_API_HOST") == "0.0.0.0"
    )


# this currently only handles a single method; in the future, idempotent
# requests like i18nResources should probably be moved here
def _extract_dynamic_get_request(path: str) -> DynamicRequest | None:
    if path == "legacyPageData":
        return legacy_page_data
    else:
        return None
