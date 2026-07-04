# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Crash-recovery test: kill the app mid-review, prove the collection survives.

ASSIGN.md section 7g asks us to kill the app in the middle of a review 20 times
in a row and show zero corrupted collections afterwards. This is the honest
engine/collection-level version of that test, runnable headless.

What it does (real, not simulated corruption):

  1. Build one isolated temp collection, seed it with Manifold skill cards.
  2. Repeat N times (default 20):
       a. Spawn a child process (this same file, --child) that opens the
          collection and answers cards in a tight loop through Anki's real answer
          path (col.sched.answerCard), cycling over the seeded cards and writing
          revlog and card rows on every answer, exactly as a live review does.
          Answering cards directly (not via the daily queue) keeps the reviewer
          writing continuously so the kill lands mid-write.
       b. Wait until the child signals it is actively reviewing, then send it
          SIGKILL after a short random delay, so the kill lands in the middle of
          the review write path (often mid-transaction).
       c. Reopen the collection in the parent and run Anki's own database check
          (col.fix_integrity). Assert it reports no problems, the collection is
          readable, and the Manifold engine RPC still works on it.
  3. Fail loudly on the first iteration whose reopened collection is not clean,
     naming the iteration and the problem. Print PASS only if all N reopen clean.

What it does and does not cover: this drives the shared Rust engine and the
SQLite-backed collection that both the desktop and the phone build use, so it
exercises the exact storage layer that would corrupt. The answer path it hammers
is scheduler-agnostic: the SQLite writes are identical whether FSRS or SM-2 is
active, so the integrity result holds either way. It does not launch the Qt
desktop shell or the Android app, so it does not cover a kill during UI teardown
or during a platform-specific file flush. The section 7g "both platforms" claim
still needs a per-app kill test on each shipped build; this proves the shared
engine and collection recover from an abrupt kill mid-write.

Run from the repo root, after a build. No PYTHONPATH needed (the script adds the
built pylib to sys.path itself):

    out/pyenv/bin/python manifold/tests/crash_loop.py

Flags: --iterations N (default 20), --seed N (RNG seed for the kill timing).
"""

from __future__ import annotations

import argparse
import os
import random
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent  # manifold/tests
REPO_ROOT = SCRIPT_DIR.parents[1]  # repo root
OUT = REPO_ROOT / "out"
PYLIB = OUT / "pylib"
CONTENT_DIR = REPO_ROOT / "manifold" / "content"

# Make the built `anki` package and the seed loaders importable, so this runs
# with a bare `out/pyenv/bin/python manifold/tests/crash_loop.py`.
sys.path.insert(0, str(PYLIB))
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402

DECK_NAME = "Manifold crash test"
TOPIC_TAG_PREFIX = "mf::topic::"
SKILL_TAG_PREFIX = "mf::skill::"
TIER_TAG_PREFIX = "mf::tier::"

SEED_CARDS = 1200
GOOD = 3  # answerCard ease: 3 = Good
READY_TIMEOUT_S = 45.0


def _blueprint_topic() -> tuple[str, str, str]:
    """A real (topic_id, tier, title) from the engine blueprint.

    Cards must carry a valid blueprint topic and matching tier, or the engine's
    get_topic_graph rejects them, so the reopen check would fail for the wrong
    reason. The first blueprint topic is a root, which is fine here.
    """
    blueprint = import_seed.load_json(import_seed.DEFAULT_BLUEPRINT)
    topic = blueprint["topics"][0]
    return topic["id"], topic["tier"], topic["title"]


TOPIC_ID, TIER, TOPIC_TITLE = _blueprint_topic()


def _add_skill_batch(col, deck_id, notetype, count: int) -> None:
    """Add `count` new Manifold skill cards to the deck."""
    for index in range(count):
        note = col.new_note(notetype)
        note["Front"] = f"crash skill {index}"
        note["Back"] = TOPIC_TITLE
        note.tags = [
            f"{TOPIC_TAG_PREFIX}{TOPIC_ID}",
            # Unique per note so each counts as its own skill in the rollup.
            f"{SKILL_TAG_PREFIX}crash_{index}",
            f"{TIER_TAG_PREFIX}{TIER}",
        ]
        col.add_note(note, deck_id)


def setup_collection(path: str) -> tuple[int, int]:
    """Create and seed the isolated test collection. Returns (cards, skills)."""
    from anki.collection import Collection

    col = Collection(path)
    try:
        deck_id = col.decks.id(DECK_NAME)
        notetype = col.models.by_name("Basic")
        if notetype is None:
            raise RuntimeError("notetype 'Basic' not found in collection")
        _add_skill_batch(col, deck_id, notetype, SEED_CARDS)
        cards = col.card_count()
        skills = sum(node.total for node in col._backend.get_topic_graph().nodes)
    finally:
        col.close()
    return cards, skills


def run_child(path: str, ready_path: str) -> int:
    """Answer cards in a tight loop until killed. Signals readiness once live.

    Cards are answered directly through Anki's real answer path, cycling over the
    seeded set, rather than pulled from the daily queue. That keeps the reviewer
    writing revlog and card rows continuously (so the SIGKILL lands mid-write)
    without depending on per-day new/review limits.
    """
    from anki.collection import Collection

    col = Collection(path)
    card_ids = col.find_cards(f"tag:{SKILL_TAG_PREFIX}*")
    if not card_ids:
        raise RuntimeError("no mf::skill cards found to review")

    reviewed = 0
    index = 0
    count = len(card_ids)
    while True:
        card = col.get_card(card_ids[index % count])
        index += 1
        card.start_timer()
        col.sched.answerCard(card, GOOD)
        reviewed += 1
        if reviewed == 1:
            # Only now are we provably mid-review; tell the parent to arm the kill.
            Path(ready_path).write_text("reviewing", encoding="utf-8")
    # Unreachable: the process is expected to be killed while looping.


def _spawn_child(path: str, ready_path: str, log_file) -> subprocess.Popen:
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(PYLIB), os.environ.get("PYTHONPATH", "")])}
    return subprocess.Popen(
        [sys.executable, str(SCRIPT_DIR / "crash_loop.py"), "--child", path, ready_path],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
        start_new_session=True,  # own process group, so we can kill it cleanly
    )


def _wait_until_reviewing(proc: subprocess.Popen, ready_path: Path) -> None:
    """Block until the child signals it is reviewing, or fail loudly."""
    deadline = time.time() + READY_TIMEOUT_S
    while time.time() < deadline:
        if ready_path.exists():
            return
        if proc.poll() is not None:
            raise RuntimeError(f"child exited early with code {proc.returncode} before reviewing")
        time.sleep(0.005)
    raise TimeoutError(f"child did not start reviewing within {READY_TIMEOUT_S:.0f}s")


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()


def reopen_check(path: str) -> tuple[bool, str, int]:
    """Reopen the collection and run Anki's DB check. Returns (ok, detail, cards)."""
    from anki.collection import Collection

    col = Collection(path)
    try:
        detail, ok = col.fix_integrity()
        cards = col.card_count()
        # The shared engine must also still read the collection.
        col._backend.get_topic_graph()
    finally:
        col.close()
    return ok, detail, cards


def run_harness(iterations: int, rng: random.Random) -> int:
    workdir = Path(tempfile.mkdtemp(prefix="mf-crash-"))
    path = str(workdir / "collection.anki2")
    try:
        cards, skills = setup_collection(path)
        print(
            f"Isolated collection at {path}\n"
            f"  seeded {cards} cards ({skills} skills)."
        )
        print(f"Killing a mid-review process {iterations} times, checking integrity each time:")

        failures: list[tuple[int, str]] = []
        for i in range(1, iterations + 1):
            ready_path = workdir / f"ready-{i}"
            log_path = workdir / f"child-{i}.log"
            if ready_path.exists():
                ready_path.unlink()

            with open(log_path, "w", encoding="utf-8") as log_file:
                proc = _spawn_child(path, str(ready_path), log_file)
                try:
                    _wait_until_reviewing(proc, ready_path)
                except (RuntimeError, TimeoutError) as err:
                    _kill_group(proc)
                    log = log_path.read_text(encoding="utf-8")
                    raise RuntimeError(f"iteration {i}: {err}\nchild output:\n{log}") from err
                # Let it review a little, then kill mid-write.
                time.sleep(rng.uniform(0.05, 0.30))
                _kill_group(proc)

            try:
                ok, detail, count = reopen_check(path)
            except Exception as err:  # a raise on open is itself a corruption signal
                ok, detail, count = False, f"reopen raised: {err!r}", -1

            status = "clean" if ok else "CORRUPT"
            print(f"  kill {i:2d}/{iterations}: reopened, {count} cards, integrity {status}")
            if not ok:
                failures.append((i, detail))

        # Final evidence that real reviews were written and survived the kills.
        from anki.collection import Collection

        col = Collection(path)
        try:
            revlog = col.db.scalar("select count() from revlog")
            final_cards = col.card_count()
        finally:
            col.close()

        print()
        if failures:
            print(f"FAIL: {len(failures)} of {iterations} kills left a non-clean collection.")
            for i, detail in failures:
                first_line = detail.strip().splitlines()[0] if detail.strip() else "(no detail)"
                print(f"  iteration {i}: {first_line}")
            return 1

        print(
            f"PASS: {iterations}/{iterations} mid-review kills reopened clean "
            f"(0 corrupted collections)."
        )
        print(
            f"  {revlog} reviews were written and survived across the kills; "
            f"the collection holds {final_cards} cards and still opens and reads."
        )
        return 0
    finally:
        # Best-effort cleanup of the throwaway collection.
        for child in workdir.glob("*"):
            try:
                child.unlink()
            except OSError:
                pass
        try:
            workdir.rmdir()
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manifold crash-recovery test (kill mid-review).")
    parser.add_argument("--iterations", type=int, default=20, help="number of mid-review kills")
    parser.add_argument("--seed", type=int, default=1234, help="RNG seed for kill timing")
    # Internal: run the reviewer child. Not part of the public interface.
    parser.add_argument("--child", nargs=2, metavar=("COLLECTION", "READY_FILE"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.child:
        return run_child(args.child[0], args.child[1])

    if args.iterations < 1:
        parser.error("--iterations must be positive")
    return run_harness(args.iterations, random.Random(args.seed))


if __name__ == "__main__":
    raise SystemExit(main())
