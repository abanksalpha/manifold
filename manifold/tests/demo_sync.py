# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Desktop-to-desktop sync demo against a real self-hosted Anki sync server.

ASSIGN.md section 7b asks Manifold to show that reviews flow between devices
over Anki's built-in sync protocol, with a documented conflict rule. Manifold
adds no sync code of its own (decision D9): it reuses Anki's collection-level
sync and the self-hosted sync server that ships inside rslib. This script is the
honest, runnable, headless proof of that, on the exact engine + collection layer
that both the desktop and the phone build share.

Nothing here is mocked or faked. It stands up the real sync server as a
subprocess, drives two independent collections through the real
`Collection.sync_login` / `sync_collection` / `full_upload_or_download` API, and
verifies the outcomes by reading the merged SQLite `revlog` and card rows on both
sides. Every printed number comes from that real run. If the server will not
start, a login fails, a sync errors, or an assertion does not hold, the script
fails loudly with the real error and exits non-zero rather than printing a
fabricated PASS.

What it demonstrates (matches docs/manifold/sync.md):

  1. Server: starts `python -m anki.syncserver` (SYNC_USER1=demo:demo, a throwaway
     SYNC_BASE, a chosen free port), waits until it logs `listening addr=...` and
     accepts TCP, and always tears it down at the end.
  2. Common base: collection A is seeded with the GRE deck and full-uploaded;
     collection B starts empty and full-downloads A's collection. This is how a
     second device joins an account, and it gives A and B an identical common
     base (same card ids), which is what makes the disjoint/merge checks below
     well defined. (Seeding both sides independently would create different note
     GUIDs and card ids, i.e. NOT a shared base.)
  3. Disjoint merge: review 10 distinct cards on A and 10 different distinct cards
     on B while each is "offline" (unsynced), then sync A, sync B, sync A. Assert
     all 20 reviews converge and land exactly once (revlog delta == 20 on both
     sides, and exactly one new revlog row per reviewed card).
  4. Conflict rule (last-write-wins by modification time): review the SAME card on
     both A and B while offline, with B's review a real >=1s later (card mtime is
     second-resolution). Sync both. Assert the later review's card row wins the
     scheduling state on both sides, and BOTH reviews are still retained in the
     revlog (nothing silently dropped). The observed behaviour is reported as-is;
     it is not forced to PASS.

Run from the repo root, after a build. No PYTHONPATH needed (the script adds the
built pylib to sys.path itself), though the documented invocation also works:

    out/pyenv/bin/python manifold/tests/demo_sync.py
    PYTHONPATH=out/pylib out/pyenv/bin/python manifold/tests/demo_sync.py

Flags: --disjoint N (distinct cards reviewed per side, default 10),
       --keep-temp (do not delete the throwaway dirs, for debugging).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent  # manifold/tests
REPO_ROOT = SCRIPT_DIR.parents[1]  # repo root
OUT = REPO_ROOT / "out"
PYLIB = OUT / "pylib"
CONTENT_DIR = REPO_ROOT / "manifold" / "content"

# Make the built `anki` package and the seed loaders importable, so this runs
# with a bare `out/pyenv/bin/python manifold/tests/demo_sync.py`.
sys.path.insert(0, str(PYLIB))
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402

# Sync-server credentials (match docs/manifold/sync.md). One user is enough.
SYNC_USER = "demo"
SYNC_PASS = "demo"
SYNC_HOST = "127.0.0.1"

# answerCard ease buttons.
AGAIN = 1
GOOD = 3
EASY = 4

# Bounded waits, so a broken environment fails loudly instead of hanging.
SERVER_READY_TIMEOUT_S = 60.0
# card mtime is second-resolution, so the two conflicting reviews must land in
# different whole seconds for "B is later" to be real and observable.
CONFLICT_GAP_S = 1.5

SKILL_SEARCH = "tag:mf::skill::*"


# --------------------------------------------------------------------------- #
# Sync-server subprocess management
# --------------------------------------------------------------------------- #
def _free_port() -> int:
    """Reserve a free TCP port on the loopback and return it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((SYNC_HOST, 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def _tcp_connectable(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def start_sync_server(base_dir: Path, port: int, log_file: Any) -> subprocess.Popen:
    """Spawn `python -m anki.syncserver` bound to SYNC_HOST:port.

    Reads the same SYNC_* env vars documented in docs/manifold/sync.md. Output
    (stdout+stderr, including the Rust `listening addr=...` line) is captured to
    log_file so we can detect readiness and surface a real startup error.
    """
    env = {**os.environ}
    env["SYNC_USER1"] = f"{SYNC_USER}:{SYNC_PASS}"
    env["SYNC_HOST"] = SYNC_HOST
    env["SYNC_PORT"] = str(port)
    env["SYNC_BASE"] = str(base_dir)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PYLIB), os.environ.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env.setdefault("RUST_LOG", "anki=info")
    return subprocess.Popen(
        [sys.executable, "-m", "anki.syncserver"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
        start_new_session=True,  # own process group, so we can kill it cleanly
    )


def wait_for_sync_server(
    proc: subprocess.Popen, log_path: Path, host: str, port: int, timeout: float
) -> str:
    """Block until the server logs it is listening AND accepts TCP.

    Returns the real `listening addr=...` line for the transcript. Fails loudly
    if the process exits early or never becomes ready within `timeout`.
    """
    deadline = time.time() + timeout
    listening_pat = re.compile(r"listening addr=(\S+)")
    listening_line: str | None = None
    while time.time() < deadline:
        text = log_path.read_text(errors="replace") if log_path.exists() else ""
        if listening_line is None:
            match = listening_pat.search(text)
            if match:
                listening_line = match.group(0)
        rc = proc.poll()
        if rc is not None:
            raise RuntimeError(
                f"sync server exited early with code {rc} before it was ready.\n"
                f"--- server output ---\n{text.strip() or '(no output captured)'}"
            )
        if listening_line and _tcp_connectable(host, port):
            return listening_line
        time.sleep(0.05)

    text = log_path.read_text(errors="replace") if log_path.exists() else ""
    seen = "seen" if listening_line else "NOT seen"
    raise TimeoutError(
        f"sync server not ready within {timeout:.0f}s (listening line {seen}).\n"
        f"--- server output ---\n{text.strip() or '(no output captured)'}"
    )


def stop_sync_server(proc: subprocess.Popen) -> None:
    """Terminate the server process group, escalating to SIGKILL if needed."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


# --------------------------------------------------------------------------- #
# Collection / sync helpers
# --------------------------------------------------------------------------- #
def login(col: Any, endpoint: str) -> Any:
    """Real host-key login against the server; returns auth with endpoint set.

    `sync_login` returns the host key but clears the endpoint (the desktop keeps
    the endpoint in its profile and re-attaches it per sync), so we re-attach it
    here for the subsequent sync calls.
    """
    auth = col.sync_login(SYNC_USER, SYNC_PASS, endpoint)
    auth.endpoint = endpoint
    if not auth.hkey:
        raise RuntimeError("sync_login returned an empty host key")
    return auth


def _full_sync(col: Any, auth: Any, *, upload: bool) -> None:
    """Perform a full upload or download, mirroring the desktop client flow."""
    col.close_for_full_sync()
    col.full_upload_or_download(auth=auth, server_usn=None, upload=upload)
    col.reopen(after_full_sync=True)


def sync(col: Any, auth: Any, *, label: str) -> str:
    """Run one real sync, handling the full-sync cases; return an outcome tag.

    `sync_collection` performs a normal (incremental) sync inline and reports
    NO_CHANGES; only the FULL_* cases need the follow-up full_upload_or_download.
    An ambiguous FULL_SYNC (diverged collections) is a real problem for this
    demo, so it fails loudly rather than guessing a direction.
    """
    out = col.sync_collection(auth, False)  # sync_media=False: text-only deck
    required = out.required
    if required == out.NO_CHANGES:
        outcome = "normal"
    elif required == out.FULL_UPLOAD:
        _full_sync(col, auth, upload=True)
        outcome = "full_upload"
    elif required == out.FULL_DOWNLOAD:
        _full_sync(col, auth, upload=False)
        outcome = "full_download"
    elif required == out.FULL_SYNC:
        raise RuntimeError(
            f"{label}: server requires an ambiguous FULL_SYNC (collections "
            "diverged and cannot be merged incrementally); refusing to guess a "
            "direction"
        )
    else:
        raise RuntimeError(f"{label}: unexpected sync 'required' value {required!r}")
    col._load_scheduler()  # scheduler version may have changed (as the desktop does)
    return outcome


def revlog_total(col: Any) -> int:
    return int(col.db.scalar("select count() from revlog"))


def revlog_max_id(col: Any) -> int:
    return int(col.db.scalar("select coalesce(max(id), 0) from revlog"))


def revlog_ids_for_card(col: Any, cid: int) -> list[int]:
    return [int(x) for x in col.db.list("select id from revlog where cid=? order by id", cid)]


def _wait_until_ms_past(threshold_ms: int) -> None:
    """Block until the wall clock is strictly past threshold_ms milliseconds."""
    while int(time.time() * 1000) <= threshold_ms:
        time.sleep(0.001)


def answer(col: Any, cid: int, ease: int) -> None:
    """Answer one card through Anki's real scheduler answer path."""
    card = col.get_card(cid)
    card.start_timer()
    col.sched.answerCard(card, ease)


def card_sched_state(col: Any, cid: int) -> dict[str, int]:
    """Read the scheduling-relevant fields of a card row (fresh from the DB)."""
    card = col.get_card(cid)
    return {
        "mod": int(card.mod),
        "type": int(card.type),
        "queue": int(card.queue),
        "due": int(card.due),
        "ivl": int(card.ivl),
        "factor": int(card.factor),
        "reps": int(card.reps),
    }


# --------------------------------------------------------------------------- #
# Result table
# --------------------------------------------------------------------------- #
class Check:
    def __init__(self, name: str, passed: bool, detail: str) -> None:
        self.name = name
        self.passed = passed
        self.detail = detail


def print_table(checks: list[Check]) -> bool:
    name_w = max(len(c.name) for c in checks)
    print()
    print("=" * (name_w + 60))
    print("Sync demo assertions (each verified against the real merged data)")
    print("=" * (name_w + 60))
    all_ok = True
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        all_ok = all_ok and check.passed
        print(f"  [{status}] {check.name.ljust(name_w)}  {check.detail}")
    print("=" * (name_w + 60))
    print(f"  RESULT: {'ALL PASS' if all_ok else 'FAILURES PRESENT'}")
    print("=" * (name_w + 60))
    return all_ok


# --------------------------------------------------------------------------- #
# Test phases
# --------------------------------------------------------------------------- #
def disjoint_phase(
    col_a: Any,
    col_b: Any,
    auth_a: Any,
    auth_b: Any,
    a_set: list[int],
    b_set: list[int],
    base_a: int,
    base_b: int,
    disjoint_n: int,
) -> list[Check]:
    """Review disjoint card sets offline on each side, converge, verify no loss."""
    print(
        f"[disjoint] reviewing {disjoint_n} distinct cards on A and "
        f"{disjoint_n} DIFFERENT distinct cards on B, both offline..."
    )
    for cid in a_set:
        answer(col_a, cid, GOOD)
    # The revlog primary key is a millisecond timestamp. Two real devices review
    # at different wall-clock times, but this harness drives both collections
    # from a single process at machine speed; Anki assigns each review
    # max(existing_id)+1 when the clock has not advanced a full ms, so A's ids can
    # run ahead of the clock. Wait until the clock is strictly past A's latest
    # revlog id so B's reviews get strictly-later ids -- i.e. represent two
    # devices reviewing at genuinely different times. Without this, a shared
    # millisecond id would drop one review on merge (INSERT OR IGNORE), which is a
    # harness artifact, not a sync-protocol property.
    _wait_until_ms_past(revlog_max_id(col_a))
    for cid in b_set:
        answer(col_b, cid, GOOD)
    a_local = revlog_total(col_a) - base_a
    b_local = revlog_total(col_b) - base_b
    print(
        "[disjoint] (B's reviews were spaced to a strictly-later millisecond "
        "than A's, as two real devices would review at different times)"
    )
    print(f"[disjoint] local revlog before sync: A +{a_local}, B +{b_local}")

    print("[disjoint] syncing A -> B -> A to converge...")
    sync(col_a, auth_a, label="A disjoint #1")
    sync(col_b, auth_b, label="B disjoint")
    sync(col_a, auth_a, label="A disjoint #2")

    merged_a = revlog_total(col_a) - base_a
    merged_b = revlog_total(col_b) - base_b
    # Exactly one new revlog row per reviewed card, on both converged sides.
    all_reviewed = a_set + b_set
    per_card_a = {cid: len(revlog_ids_for_card(col_a, cid)) for cid in all_reviewed}
    per_card_b = {cid: len(revlog_ids_for_card(col_b, cid)) for cid in all_reviewed}
    exactly_once_a = all(v == 1 for v in per_card_a.values())
    exactly_once_b = all(v == 1 for v in per_card_b.values())

    print(
        f"[disjoint] after convergence: merged revlog A +{merged_a}, B +{merged_b} "
        f"(expected +{2 * disjoint_n})"
    )
    return [
        Check(
            "disjoint reviews converge (counts match)",
            merged_a == merged_b == 2 * disjoint_n,
            f"A +{merged_a}, B +{merged_b}, expected +{2 * disjoint_n}",
        ),
        Check(
            "each review present exactly once (no loss/dupes)",
            exactly_once_a and exactly_once_b and a_local == b_local == disjoint_n,
            f"A: {sum(per_card_a.values())} rows over {len(all_reviewed)} cards; "
            f"B: {sum(per_card_b.values())} rows over {len(all_reviewed)} cards",
        ),
    ]


def conflict_phase(
    col_a: Any,
    col_b: Any,
    auth_a: Any,
    auth_b: Any,
    conflict_cid: int,
) -> list[Check]:
    """Review the SAME card on both sides (B strictly later), converge, verify.

    Reports the real observed winner; it is not forced to the documented rule.
    """
    print(
        "[conflict] reviewing the SAME card on both sides offline; "
        "A answers 'Again' first, then B answers 'Easy' >=1s later..."
    )
    answer(col_a, conflict_cid, AGAIN)
    state_a = card_sched_state(col_a, conflict_cid)
    rid_a_list = revlog_ids_for_card(col_a, conflict_cid)

    time.sleep(CONFLICT_GAP_S)  # guarantee B's card mtime (seconds) is later

    answer(col_b, conflict_cid, EASY)
    state_b = card_sched_state(col_b, conflict_cid)
    rid_b_list = revlog_ids_for_card(col_b, conflict_cid)

    if not rid_a_list or not rid_b_list:
        raise RuntimeError("conflict setup produced no revlog entry on a side")
    rid_a, rid_b = rid_a_list[-1], rid_b_list[-1]
    if state_b["mod"] <= state_a["mod"]:
        raise RuntimeError(
            "conflict setup invalid: B's review mtime "
            f"({state_b['mod']}) is not later than A's ({state_a['mod']}); "
            "cannot demonstrate last-write-wins"
        )
    print(
        f"[conflict] A review: mtime={state_a['mod']} ivl={state_a['ivl']} "
        f"type={state_a['type']} queue={state_a['queue']} revlog_id={rid_a}"
    )
    print(
        f"[conflict] B review: mtime={state_b['mod']} ivl={state_b['ivl']} "
        f"type={state_b['type']} queue={state_b['queue']} revlog_id={rid_b}  (later)"
    )

    print("[conflict] syncing A -> B -> A to converge...")
    sync(col_a, auth_a, label="A conflict #1")
    sync(col_b, auth_b, label="B conflict")
    sync(col_a, auth_a, label="A conflict #2")

    conv_a = card_sched_state(col_a, conflict_cid)
    conv_b = card_sched_state(col_b, conflict_cid)
    conv_rids_a = revlog_ids_for_card(col_a, conflict_cid)
    conv_rids_b = revlog_ids_for_card(col_b, conflict_cid)

    winner_b = conv_a == state_b and conv_b == state_b
    winner_a = conv_a == state_a and conv_b == state_a
    both_retained = set(conv_rids_a) == {rid_a, rid_b} == set(conv_rids_b)

    if winner_b:
        winner_desc = "later review (B) won on both sides"
    elif winner_a:
        winner_desc = "OBSERVED: earlier review (A) won (differs from documented rule)"
    else:
        winner_desc = (
            f"OBSERVED: neither side's exact state (A={conv_a} vs stateA={state_a} "
            f"stateB={state_b})"
        )
    print(
        f"[conflict] converged card row: A={conv_a}\n"
        f"[conflict] converged card row: B={conv_b}\n"
        f"[conflict] {winner_desc}"
    )
    print(
        f"[conflict] revlog for card {conflict_cid}: A={conv_rids_a}, B={conv_rids_b} "
        f"(earlier={rid_a}, later={rid_b})"
    )
    return [
        Check(
            "conflict: later review wins scheduling state",
            winner_b,
            f"converged card row == B's later review on both sides "
            f"(A mtime {conv_a['mod']} == B mtime {state_b['mod']})",
        ),
        Check(
            "conflict: earlier review retained in revlog",
            both_retained,
            f"both revlog ids present on both sides: {sorted({rid_a, rid_b})}",
        ),
    ]


# --------------------------------------------------------------------------- #
# Main demo
# --------------------------------------------------------------------------- #
def run(disjoint_n: int, keep_temp: bool) -> int:
    from anki.collection import Collection

    workdir = Path(tempfile.mkdtemp(prefix="mf-sync-demo-"))
    server_base = workdir / "server-base"
    server_base.mkdir()
    server_log = workdir / "syncserver.log"
    col_a_path = workdir / "colA" / "collection.anki2"
    col_b_path = workdir / "colB" / "collection.anki2"
    col_a_path.parent.mkdir()
    col_b_path.parent.mkdir()

    port = _free_port()
    endpoint = f"http://{SYNC_HOST}:{port}/"

    print("Manifold desktop-to-desktop sync demo")
    print("  substrate : Anki collection-level sync + self-hosted server (D9)")
    print(f"  workdir   : {workdir}")
    print(f"  endpoint  : {endpoint}")
    print(f"  user      : {SYNC_USER} (SYNC_USER1={SYNC_USER}:{SYNC_PASS})")
    print()

    checks: list[Check] = []
    proc: subprocess.Popen | None = None
    col_a: Any = None
    col_b: Any = None
    log_handle = open(server_log, "w", encoding="utf-8")
    try:
        # 1) Start the real sync server and wait until it is listening. --------
        print(f"[server] starting: {sys.executable} -m anki.syncserver")
        print(f"[server] SYNC_HOST={SYNC_HOST} SYNC_PORT={port} SYNC_BASE={server_base}")
        proc = start_sync_server(server_base, port, log_handle)
        listening = wait_for_sync_server(
            proc, server_log, SYNC_HOST, port, SERVER_READY_TIMEOUT_S
        )
        print(f"[server] {listening}  (TCP accepting on {SYNC_HOST}:{port})")
        print()

        # 2) Seed A, then establish a common base (A uploads, B downloads). ----
        print("[base] seeding collection A with the GRE deck...")
        col_a = Collection(str(col_a_path))
        added, skipped = import_seed.import_seed(col_a)
        seeded = sum(added.values())
        a_cards = col_a.card_count()
        print(f"[base] A seeded: {seeded} notes added, {a_cards} cards total")

        auth_a = login(col_a, endpoint)
        print("[base] A login OK; syncing A (expect first-time full upload)...")
        outcome = sync(col_a, auth_a, label="A initial")
        if outcome != "full_upload":
            raise RuntimeError(
                f"A's first sync should be a full upload to the empty server, "
                f"got {outcome!r}"
            )
        print(f"[base] A initial sync outcome: {outcome}")

        print("[base] creating empty collection B and downloading A's collection...")
        col_b = Collection(str(col_b_path))
        auth_b = login(col_b, endpoint)
        outcome = sync(col_b, auth_b, label="B initial")
        if outcome != "full_download":
            raise RuntimeError(
                f"B's first sync should be a full download from the server, "
                f"got {outcome!r}"
            )
        b_cards = col_b.card_count()
        print(f"[base] B initial sync outcome: {outcome}; B now has {b_cards} cards")

        base_a = revlog_total(col_a)
        base_b = revlog_total(col_b)
        checks.append(
            Check(
                "common base established",
                a_cards == b_cards and a_cards > 0 and base_a == base_b,
                f"A={a_cards} cards, B={b_cards} cards; revlog baseline A={base_a}, B={base_b}",
            )
        )

        # Identical common base => identical card ids on both sides.
        cids = sorted(int(c) for c in col_a.find_cards(SKILL_SEARCH))
        needed = 2 * disjoint_n + 1
        if len(cids) < needed:
            raise RuntimeError(
                f"need at least {needed} skill cards for the demo, found {len(cids)}"
            )
        a_set = cids[:disjoint_n]
        b_set = cids[disjoint_n : 2 * disjoint_n]
        conflict_cid = cids[2 * disjoint_n]
        print()

        # 3) Disjoint offline reviews, then converge. --------------------------
        checks.extend(
            disjoint_phase(
                col_a, col_b, auth_a, auth_b, a_set, b_set, base_a, base_b, disjoint_n
            )
        )
        print()

        # 4) Conflict: same card on both sides, B strictly later. --------------
        checks.extend(conflict_phase(col_a, col_b, auth_a, auth_b, conflict_cid))

        all_ok = print_table(checks)
        return 0 if all_ok else 1
    finally:
        for col in (col_a, col_b):
            try:
                if col is not None and col.db is not None:
                    col.close()
            except Exception as err:  # never mask the real error with a cleanup one
                print(f"[cleanup] warning closing collection: {err!r}")
        if proc is not None:
            stop_sync_server(proc)
        log_handle.close()
        if keep_temp:
            print(f"[cleanup] keeping temp dir: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manifold desktop-to-desktop sync demo (real self-hosted server)."
    )
    parser.add_argument(
        "--disjoint",
        type=int,
        default=10,
        help="distinct cards reviewed per side for the merge test (default 10)",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="do not delete the throwaway server/collection dirs (for debugging)",
    )
    args = parser.parse_args(argv)
    if args.disjoint < 1:
        parser.error("--disjoint must be positive")
    return run(args.disjoint, args.keep_temp)


if __name__ == "__main__":
    raise SystemExit(main())
