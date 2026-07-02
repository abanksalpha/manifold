# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Live end-to-end drive of the REAL Manifold desktop app.

Unlike the e2e harness (a synthetic offscreen launcher over an empty
collection), this boots the actual `./run` desktop application against a
freshly-seeded collection, exactly as a user would get it, then drives and
asserts every Manifold surface against that running app:

    1. seed a fresh temp base (prefs "test" profile + 121-skill collection)
    2. launch `./run -b <base> -p test` (real windowed app) with mediasrv on a
       free port and QtWebEngine remote-debugging on another free port
    3. confirm, via the remote-debugging /json target list, that the real Qt
       web view booted into the Manifold home (/manifold), not Anki's deck
       browser (feature 3a)
    4. run live_drive.mjs: a Playwright Chromium that drives features b-e
       against the app's mediasrv and screenshots each surface
    5. capture the FULL app/mediasrv log for the zero-error gate, then tear down

Run from the repo root after a build:

    out/pyenv/bin/python manifold/content/live_drive.py

Artifacts land in out/manifold-live/: app.log (full app+mediasrv log),
shots/*.png (per-surface screenshots).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT = REPO_ROOT / "out"
NODE = OUT / "extracted" / "node" / "bin" / "node"
NODE_BIN = OUT / "extracted" / "node" / "bin"
BROWSERS = OUT / "playwright-browsers"
LIVE_DIR = OUT / "manifold-live"
APP_LOG = LIVE_DIR / "app.log"
SHOT_DIR = LIVE_DIR / "shots"

sys.path.insert(0, str(SCRIPT_DIR))
import run_e2e_isolated as seedlib  # noqa: E402  (reuses free_port/_seed_prefs/seed_collection)


def wait_favicon(port: int, proc: subprocess.Popen, timeout: float = 150.0) -> None:
    url = f"http://127.0.0.1:{port}/favicon.ico"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"./run exited early (code {proc.returncode}); see {APP_LOG}")
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"mediasrv not ready on {port} within {timeout:.0f}s; see {APP_LOG}")


def wait_boot_url(cdp_port: int, timeout: float = 60.0) -> str:
    """Poll the QtWebEngine remote-debugging /json until the main web view is
    showing the Manifold home; return its URL. Proves feature 3a."""
    url = f"http://127.0.0.1:{cdp_port}/json"
    deadline = time.time() + timeout
    last: list[str] = []
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                targets = json.loads(resp.read().decode("utf-8"))
            last = [t.get("url", "") for t in targets]
            for u in last:
                if u.endswith("/manifold"):
                    return u
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(
        f"real web view never showed /manifold within {timeout:.0f}s; targets seen: {last}"
    )


def launch_run(base: Path, api_port: int, cdp_port: int):
    env = {
        **os.environ,
        "ANKI_API_PORT": str(api_port),
        # Allow the external Playwright Chromium to reach /_anki/* without the
        # internal bearer token (documented e2e escape), and skip Host/Origin
        # checks — the app itself is otherwise unchanged.
        "ANKI_API_HOST": "0.0.0.0",
        "QTWEBENGINE_REMOTE_DEBUGGING": str(cdp_port),
        "ANKIDEV": "1",
        "ANKI_SINGLE_INSTANCE_KEY": f"mf-live-{api_port}",
    }
    log = open(APP_LOG, "w", encoding="utf-8")
    proc = subprocess.Popen(
        ["./run", "-b", str(base), "-p", seedlib.TEST_PROFILE],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
        start_new_session=True,
    )
    return proc, log


def run_driver(api_port: int, cdp_port: int) -> int:
    env = {
        **os.environ,
        "MF_BASE_URL": f"http://127.0.0.1:{api_port}",
        "MF_SHOT_DIR": str(SHOT_DIR),
        "MF_CDP": f"http://127.0.0.1:{cdp_port}",
        "PLAYWRIGHT_BROWSERS_PATH": str(BROWSERS),
        "PATH": f"{NODE_BIN}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    cmd = [str(NODE), str(SCRIPT_DIR / "live_drive.mjs")]
    return subprocess.run(cmd, env=env, cwd=str(REPO_ROOT)).returncode


def teardown(proc: subprocess.Popen, log) -> None:
    """Stop the app as gracefully as possible.

    A graceful SIGINT lets Anki close its collection, web views and mediasrv in
    order, avoiding the QtWebEngine GPU-teardown / waitress socket-close races a
    hard group-kill would otherwise print at shutdown. Escalate only if the app
    does not exit on its own.
    """
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except ProcessLookupError:
        log.close()
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            proc.wait(timeout=20)
            break
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), sig)
            except ProcessLookupError:
                break
    else:
        proc.wait()
    log.close()


def main() -> int:
    if LIVE_DIR.exists():
        shutil.rmtree(LIVE_DIR)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    base = LIVE_DIR / "base"
    base.mkdir(parents=True, exist_ok=True)

    seedlib._seed_prefs(base)
    added, skipped = seedlib.seed_collection(base)
    print(f"seeded {added} notes (skipped {skipped}) at {base}/test", flush=True)

    api_port = seedlib.free_port()
    cdp_port = seedlib.free_port()
    print(f"launching ./run  (mediasrv={api_port}, remote-debug={cdp_port})", flush=True)
    proc, log = launch_run(base, api_port, cdp_port)
    driver_rc = 1
    boot_url = ""
    try:
        wait_favicon(api_port, proc)
        print(f"mediasrv ready on {api_port}", flush=True)
        boot_url = wait_boot_url(cdp_port)
        print(f"(3a) real app booted into: {boot_url}", flush=True)
        driver_rc = run_driver(api_port, cdp_port)
        # Let the driver's client sockets fully drain before shutting mediasrv
        # down, so waitress does not log a close event for a lingering channel.
        time.sleep(3)
    finally:
        teardown(proc, log)

    print(f"\nfull app/mediasrv log: {APP_LOG}")
    print(f"screenshots:           {SHOT_DIR}")
    if boot_url.endswith("/manifold") and driver_rc == 0:
        print("LIVE DRIVE PASSED")
        return 0
    print("LIVE DRIVE FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
