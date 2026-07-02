# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Reset all Manifold study progress in a collection.

Wipes study history so every skill returns to New while keeping the seeded deck
(notes/cards) intact:

  * every card is rescheduled as new via Anki's own `schedule_cards_as_new`,
    which resets its scheduling AND clears its FSRS memory state
    (rslib/src/scheduler/new.rs) — so the stability-based mastery signal resets;
  * the revlog is cleared, so the revlog-derived signals reset too: the teaching
    levels (New/Guided/Independent/Revisit), Performance, and the readiness
    give-up evidence.

The scheduler is Anki's; this only calls Anki's public reset op and deletes the
revlog rows — nothing is faked. The collection must NOT be open in a running app
(SQLite is single-writer), or the reset will fail / be lost.

Run from the repo root after a build (pylib + its compiled backend must import):

    PYTHONPATH=out/pylib out/pyenv/bin/python \
        manifold/content/reset_progress.py "/path/to/collection.anki2"
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def reset_progress(col: Any) -> tuple[int, int]:
    """Reset every card to New and clear the revlog.

    Returns (cards_reset, revlog_rows_deleted).
    """
    card_ids = list(col.find_cards(""))
    revlog_rows = int(col.db.scalar("select count() from revlog") or 0)
    if card_ids:
        # Anki's own "Forget": resets scheduling and clears FSRS memory state.
        col.sched.schedule_cards_as_new(card_ids)
    col.db.execute("delete from revlog")
    # Saving is automatic (col.save() is deprecated); col.close() flushes, and
    # main() reopens to verify the reset landed on disk.
    return len(card_ids), revlog_rows


def verify_reset(col: Any) -> None:
    """Fail loudly unless every card is New and the revlog is empty."""
    non_new = int(col.db.scalar("select count() from cards where type != 0") or 0)
    revlog = int(col.db.scalar("select count() from revlog") or 0)
    if non_new or revlog:
        raise RuntimeError(
            f"reset incomplete: {non_new} card(s) not New, {revlog} revlog row(s) remain"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset all Manifold study progress (all skills back to New)."
    )
    parser.add_argument("collection", help="path to the .anki2 collection to reset")
    args = parser.parse_args(argv)

    path = Path(args.collection)
    if not path.is_file():
        raise FileNotFoundError(f"collection not found: {path}")

    from anki.collection import Collection

    col = Collection(str(path))
    try:
        cards, revlog_rows = reset_progress(col)
    finally:
        col.close()

    # Reopen to confirm the reset persisted to disk before reporting success.
    col = Collection(str(path))
    try:
        verify_reset(col)
    finally:
        col.close()

    print(
        f"Reset {cards} card(s) to New and deleted {revlog_rows} revlog row(s).\n"
        f"Verified on reopen: all cards New, revlog empty — {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
