# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Run the Manifold Playwright e2e suite with per-test seed isolation.

Every Manifold e2e spec needs the seeded "GRE Mathematics" collection, and the
session spec grades cards (mutating scheduling state), so the three specs must
not share one collection. This runner gives each spec its own freshly-seeded,
throwaway Anki instance:

    for each spec in (home, dashboard, session):
        1. make a temp ANKI_BASE with a seeded "test" profile
        2. seed <base>/test/collection.anki2 via import_seed.py (121 skills)
        3. launch Anki headless (offscreen Qt + mediasrv) on a *free* port
        4. wait until mediasrv answers on that port
        5. run ONLY that spec with ANKI_E2E_REUSE_SERVER=1 against that port
        6. tear the instance down and delete the temp base

Nothing is mocked and no assertion is weakened; a fresh, correctly-seeded
collection is the only thing provided. The runner exits non-zero if any spec
fails or if fewer than all specs ran, so a partial run can never look green.

Run from the repo root after a build (needs the built pylib + qt and the
Playwright browsers, i.e. after `just test-e2e` has installed them at least
once):

    out/pyenv/bin/python manifold/content/run_e2e_isolated.py

Per-spec Anki logs are written to out/manifold-e2e/<spec>-server.log so a
failure can be traced to the real backend output.
"""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent  # manifold/content
REPO_ROOT = SCRIPT_DIR.parents[1]  # repo root
OUT = REPO_ROOT / "out"
PYENV_PY = OUT / "pyenv" / "bin" / "python"
NODE_BIN = OUT / "extracted" / "node" / "bin"
PLAYWRIGHT_CLI = REPO_ROOT / "node_modules" / "playwright" / "cli.js"
BROWSERS = OUT / "playwright-browsers"
LOG_DIR = OUT / "manifold-e2e"

# In-process seeding needs the built pylib (the generated `anki` package plus
# its compiled rsbridge backend) and the seed importer on the path. The prefs
# seeding is shared verbatim with the default launcher so the two stay in sync.
sys.path.insert(0, str(OUT / "pylib"))
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT / "qt" / "tests"))

import import_seed  # noqa: E402
from launch_anki_for_e2e import TEST_PROFILE, _seed_prefs  # noqa: E402

# The three Manifold specs, run one at a time each against its own fresh seed.
SPECS = [
    "ts/tests/e2e/manifold.test.ts",
    "ts/tests/e2e/manifold-dashboard.test.ts",
    "ts/tests/e2e/manifold-session.test.ts",
]


def free_port() -> int:
    """An ephemeral TCP port free at the moment of asking."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def seed_collection(base: Path) -> tuple[int, int]:
    """Create and seed <base>/test/collection.anki2, returning (added, skipped)."""
    from anki.collection import Collection

    profile_dir = base / TEST_PROFILE
    profile_dir.mkdir(parents=True, exist_ok=True)
    collection_path = profile_dir / "collection.anki2"
    col = Collection(str(collection_path))
    try:
        added, skipped = import_seed.import_seed(col)
    finally:
        col.close()
    return sum(added.values()), sum(skipped.values())


def launch_anki(base: Path, port: int, log_path: Path):
    """Spawn Anki headless with mediasrv pinned to `port`. Returns (proc, log)."""
    env = {
        **os.environ,
        "ANKI_BASE": str(base),
        "ANKI_API_PORT": str(port),
        "ANKI_SINGLE_INSTANCE_KEY": f"mf-e2e-{base.name}-{port}",
        # Lets Playwright's external Chromium reach /_anki/* without auth headers
        # (the documented e2e escape hatch); binds mediasrv on all interfaces.
        "ANKI_API_HOST": "0.0.0.0",
        "ANKIDEV": "1",
        # Manifold serves every problem via live generation (D44). For a hermetic,
        # offline, free e2e we inject a fixtures test double: it replaces ONLY the
        # model call, so serve_live.py still runs verify.py in the loop and every
        # served item is really verified (no fabrication).
        "MANIFOLD_LIVE_FIXTURES": str(
            REPO_ROOT / "manifold" / "content" / "generation" / "live_fixtures.e2e.json"
        ),
        # Independent cross-solve gate (D32 gate 5) also runs on the live path, so a
        # hermetic e2e needs a solver double too: a perfect blind solver that agrees
        # with any genuinely-verified item (the agreement logic still runs; only the
        # model call is replaced). Without it the verified fixture item would fail the
        # cross-solve gate for lack of a key and serve_live would (correctly) abstain.
        "MANIFOLD_SOLVE_FIXTURES": str(
            REPO_ROOT / "manifold" / "content" / "generation" / "solve_fixtures.e2e.json"
        ),
        # New-skill lectures (Task 1) are served from a static, pre-authored file.
        # For a hermetic e2e, point at a fixture whose single lecture is grounded in
        # a real VERIFIED teach_bank item, so the endpoint + render can be asserted
        # without depending on the full authored lectures.json.
        "MANIFOLD_LECTURES": str(
            REPO_ROOT / "manifold" / "content" / "lectures" / "lectures.e2e.json"
        ),
        # The hint assistant (ask-a-question-about-the-problem) is another live model
        # path. Inject a fixtures double so the endpoint + panel run hermetically: it
        # replaces ONLY the model call (get_hint's validation + honest-abstain logic
        # still run) and returns an answer-free, delimited-LaTeX hint for any skill.
        "MANIFOLD_HINT_FIXTURES": str(
            REPO_ROOT / "manifold" / "content" / "generation" / "hint_fixtures.e2e.json"
        ),
        "PYTHONPYCACHEPREFIX": str(OUT / "pycache"),
        "RUST_BACKTRACE": "1",
        # Headless Qt: mediasrv's HTTP stack renders to memory, no display needed.
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONUNBUFFERED": "1",
    }
    env.pop("QTWEBENGINE_REMOTE_DEBUGGING", None)
    env.pop("QTWEBENGINE_CHROMIUM_FLAGS", None)

    log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(PYENV_PY), str(REPO_ROOT / "tools" / "run.py"), "-p", TEST_PROFILE],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
        # Own process group so teardown can kill Anki and any child it spawned.
        start_new_session=True,
    )
    return proc, log


def wait_until_ready(port: int, proc: subprocess.Popen, timeout: float = 90.0) -> None:
    """Block until mediasrv answers /favicon.ico, or fail loudly."""
    url = f"http://127.0.0.1:{port}/favicon.ico"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"anki exited early with code {proc.returncode} before mediasrv came up"
            )
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"mediasrv did not answer on port {port} within {timeout:.0f}s")


def run_spec(spec: str, port: int) -> int:
    """Run one Playwright spec against the already-running server on `port`."""
    env = {
        **os.environ,
        # Reuse the server we started; Playwright will not launch its own.
        "ANKI_E2E_REUSE_SERVER": "1",
        "ANKI_API_PORT": str(port),
        "PLAYWRIGHT_BROWSERS_PATH": str(BROWSERS),
        "PATH": f"{NODE_BIN}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    cmd = [str(NODE_BIN / "node"), str(PLAYWRIGHT_CLI), "test", spec]
    return subprocess.run(cmd, env=env, cwd=str(REPO_ROOT)).returncode


def teardown(proc: subprocess.Popen, log) -> None:
    """Terminate the Anki process group and close its log."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
    finally:
        log.close()


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # The session spec saves a screenshot here; make sure the dir exists.
    (OUT / "manifold-render").mkdir(parents=True, exist_ok=True)

    results: dict[str, int] = {}
    for spec in SPECS:
        name = Path(spec).stem
        print(f"\n=== {name}: fresh seed + isolated run ===", flush=True)
        base = Path(tempfile.mkdtemp(prefix=f"mf-e2e-{name}-"))
        proc = None
        log = None
        try:
            _seed_prefs(base)
            added, skipped = seed_collection(base)
            print(f"  seeded {added} notes (skipped {skipped}) at {base}/test", flush=True)
            port = free_port()
            server_log = LOG_DIR / f"{name}-server.log"
            proc, log = launch_anki(base, port, server_log)
            print(f"  launched anki pid {proc.pid} on port {port}", flush=True)
            print(f"  server log: {server_log}", flush=True)
            wait_until_ready(port, proc)
            print(f"  mediasrv ready; running {spec}", flush=True)
            rc = run_spec(spec, port)
            results[name] = rc
            print(f"  {name}: {'PASS' if rc == 0 else 'FAIL'} (playwright exit {rc})", flush=True)
        finally:
            if proc is not None and log is not None:
                teardown(proc, log)
            shutil.rmtree(base, ignore_errors=True)

    print("\n=== manifold e2e summary (per-spec fresh seed) ===")
    for name, rc in results.items():
        print(f"  {name:32} {'PASS' if rc == 0 else 'FAIL'}")

    all_ran = len(results) == len(SPECS)
    all_passed = all(rc == 0 for rc in results.values())
    if all_ran and all_passed:
        print("ALL MANIFOLD E2E SPECS PASSED")
        return 0
    print("MANIFOLD E2E SUITE FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
