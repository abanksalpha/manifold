# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Functional check for the Manifold GRE Mathematics seed deck.

Run from the repo root after a build (the generated `anki` package and the
`tests` helper package both live under the built pylib):

    PYTHONPATH=out/pylib ANKI_TEST_MODE=1 out/pyenv/bin/python \
        manifold/content/verify_seed.py

This creates a fresh empty collection with pylib's own test factory
(tests.shared.getEmptyCol), imports seed_deck.json through import_seed, then
calls the new `get_topic_graph` RPC and asserts:

  (a) every seeded topic's `total` equals the number of skills authored for it;
  (b) every root topic (no prerequisites) is reported "unlocked";
  (c) a deep topic whose prerequisites are unmastered (metric_topology) is "locked".

It exits 0 only when all assertions pass; otherwise it raises and exits non-zero
so failures are loud.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONTENT_DIR.parents[1]

# pylib provides the `tests` package (tests.shared.getEmptyCol). The generated
# `anki` package is expected on PYTHONPATH (out/pylib) by the caller.
sys.path.insert(0, str(REPO_ROOT / "pylib"))
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402
from tests.shared import getEmptyCol  # noqa: E402


def main() -> int:
    seed = import_seed.load_json(import_seed.DEFAULT_SEED)
    blueprint = import_seed.load_json(import_seed.DEFAULT_BLUEPRINT)
    topics = import_seed.build_topic_index(blueprint)

    authored = Counter(skill["topic_id"] for skill in seed["skills"])

    col = getEmptyCol()
    try:
        added, skipped = import_seed.import_seed(col)
        nodes = col._backend.get_topic_graph().nodes
        by_id = {node.id: node for node in nodes}

        assert len(nodes) == len(topics), (
            f"expected {len(topics)} topic nodes, got {len(nodes)}"
        )

        # (a) each seeded topic's `total` equals the authored skill count.
        for topic_id, count in authored.items():
            node = by_id[topic_id]
            assert node.total == count, (
                f"topic {topic_id}: total={node.total} != authored={count}"
            )

        # (b) root topics (no prereqs) are unlocked on a freshly seeded deck.
        roots = [tid for tid, topic in topics.items() if not topic["prereqs"]]
        assert roots, "blueprint has no root topic"
        for topic_id in roots:
            state = by_id[topic_id].lock_state
            assert state == "unlocked", f"root topic {topic_id} is {state!r}, expected 'unlocked'"

        # (c) a deep topic whose prereqs are unmastered is locked.
        deep = "metric_topology"
        deep_state = by_id[deep].lock_state
        assert deep_state == "locked", f"{deep} is {deep_state!r}, expected 'locked'"
    finally:
        col.close()

    print("get_topic_graph functional check PASSED")
    print(f"  topic nodes returned : {len(nodes)} (blueprint topics: {len(topics)})")
    print(f"  notes added          : {sum(added.values())} (skipped: {sum(skipped.values())})")
    print("  per-topic [lock_state  mastered/total  coverage]:")
    for topic_id in topics:
        node = by_id[topic_id]
        print(
            f"    {topic_id:<20} {node.lock_state:<11} "
            f"{node.mastered}/{node.total:<3} cov={node.coverage:.2f}"
        )
    print(f"  (a) totals match authored counts for all {len(authored)} topics")
    print(f"  (b) root topic(s) unlocked: {', '.join(roots)}")
    print(f"  (c) deep topic 'metric_topology' lock_state: {by_id['metric_topology'].lock_state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
