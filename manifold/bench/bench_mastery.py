# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Latency benchmark for the Manifold `get_topic_graph` engine RPC.

`get_topic_graph` is the single query behind the readiness dashboard. It walks
every `mf::skill::`-tagged card once, reads each card's FSRS state, and rolls the
result up the prerequisite DAG (see `rslib/src/manifold/mastery.rs` and
`docs/manifold/why-rust.md`). This script measures that query's wall-clock
latency on a deck the size of the shared 50,000-card reference deck, so the
"keep the rollup in Rust" claim can be checked with numbers.

Run from the repo root, after a build (so pylib and its compiled rsbridge
backend are importable), exactly like the seed importer/verifier:

    PYTHONPATH=out/pylib out/pyenv/bin/python manifold/bench/bench_mastery.py

Useful flags (all optional):

    --cards N             target card count (default 50000)
    --runs N              timed runs of get_topic_graph (default 50)
    --warmup N            untimed warmup runs, discarded (default 3)
    --studied-fraction F  fraction of cards given an FSRS memory state so the
                          per-card retrievability path is exercised (default 0.8)
    --seed N              RNG seed for reproducibility (default 1234)

How the deck is built: the authored seed skills (`manifold/content/seed_deck.json`)
are replicated into distinct skill variants per blueprint topic until the target
card count is reached, so the topic distribution mirrors the real seed. A
`--studied-fraction` of cards are given a synthetic-but-valid FSRS memory state
(varied stability/difficulty and a back-dated last review) so the engine computes
real retrievability for them; the rest stay new, as in a real mid-course
collection. The states are generated load, not real reviews, and the script says
so in its output; nothing here is written back to a real collection.

Nothing is faked in the measurement: it times the actual backend RPC over a real
on-disk collection and reports the observed p50, p95, and worst-case latency.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from random import Random
from typing import Any

BENCH_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BENCH_DIR.parent / "content"
# Reuse the seed loaders so the benchmark and the importer agree on shapes.
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402

TOPIC_TAG_PREFIX = "mf::topic::"
SKILL_TAG_PREFIX = "mf::skill::"
TIER_TAG_PREFIX = "mf::tier::"


def percentile(sorted_values: list[float], fraction: float) -> float:
    """Linear-interpolated percentile of an already-sorted list."""
    if not sorted_values:
        raise ValueError("no samples to take a percentile of")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * fraction
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return sorted_values[int(rank)]
    return sorted_values[low] * (high - rank) + sorted_values[high] * (rank - low)


def build_variant_plan(seed: dict[str, Any], target_cards: int) -> list[dict[str, str]]:
    """Replicate the authored seed skills into `target_cards` distinct variants.

    Round-robins across the seed skills so the per-topic distribution of the
    generated deck matches the seed's. Each variant gets a unique skill id so it
    counts as its own skill in the rollup, exactly like an authored skill would.
    """
    base_skills = seed["skills"]
    if not base_skills:
        raise ValueError("seed_deck.json has no 'skills' to scale")

    plan: list[dict[str, str]] = []
    variant = 0
    while len(plan) < target_cards:
        base = base_skills[len(plan) % len(base_skills)]
        # A new variant index every time we wrap around the seed list.
        if len(plan) % len(base_skills) == 0:
            variant += 1
        plan.append(
            {
                "topic_id": base["topic_id"],
                "skill_id": f"{base['skill_id']}__v{variant:05d}",
                "tier": base["tier"],
                "name": f"{base['name']} (variant {variant})",
                "title": "",  # filled in from the blueprint below
            }
        )
    return plan


def populate_collection(
    col: Any,
    plan: list[dict[str, str]],
    topics: dict[str, dict[str, Any]],
    studied_fraction: float,
    rng: Random,
) -> tuple[int, int]:
    """Add one Basic note per planned variant; give a fraction an FSRS state.

    Returns (cards_added, cards_with_state).
    """
    from anki.cards import FSRSMemoryState

    deck_id = col.decks.id("GRE Mathematics")
    notetype = col.models.by_name("Basic")
    if notetype is None:
        raise RuntimeError("notetype 'Basic' not found in collection")

    now = int(time.time())
    day = 86_400
    pending: list[Any] = []
    with_state = 0
    chunk = 2000

    for entry in plan:
        topic_id = entry["topic_id"]
        note = col.new_note(notetype)
        note["Front"] = entry["name"]
        note["Back"] = topics[topic_id]["title"]
        note.tags = [
            f"{TOPIC_TAG_PREFIX}{topic_id}",
            f"{SKILL_TAG_PREFIX}{entry['skill_id']}",
            f"{TIER_TAG_PREFIX}{entry['tier']}",
        ]
        col.add_note(note, deck_id)

        if rng.random() < studied_fraction:
            card = note.cards()[0]
            stability = rng.uniform(1.0, 365.0)
            card.memory_state = FSRSMemoryState(
                stability=stability,
                difficulty=rng.uniform(1.0, 10.0),
            )
            # Back-date the last review so retrievability spans a realistic range
            # rather than pinning at ~1.0.
            elapsed_days = rng.uniform(0.0, stability)
            card.last_review_time = now - int(elapsed_days * day)
            pending.append(card)
            with_state += 1

        if len(pending) >= chunk:
            col.update_cards(pending, skip_undo_entry=True)
            pending = []

    if pending:
        col.update_cards(pending, skip_undo_entry=True)

    return len(plan), with_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Manifold get_topic_graph latency.")
    parser.add_argument("--cards", type=int, default=50_000, help="target card count")
    parser.add_argument("--runs", type=int, default=50, help="timed runs")
    parser.add_argument("--warmup", type=int, default=3, help="untimed warmup runs")
    parser.add_argument(
        "--studied-fraction",
        type=float,
        default=0.8,
        help="fraction of cards given an FSRS memory state (0..1)",
    )
    parser.add_argument("--seed", type=int, default=1234, help="RNG seed")
    args = parser.parse_args(argv)

    if not 0.0 <= args.studied_fraction <= 1.0:
        parser.error("--studied-fraction must be between 0 and 1")
    if args.cards < 1 or args.runs < 1:
        parser.error("--cards and --runs must be positive")

    rng = Random(args.seed)
    seed = import_seed.load_json(import_seed.DEFAULT_SEED)
    blueprint = import_seed.load_json(import_seed.DEFAULT_BLUEPRINT)
    topics = import_seed.build_topic_index(blueprint)

    plan = build_variant_plan(seed, args.cards)

    from anki.collection import Collection

    fd, path = tempfile.mkstemp(suffix=".anki2")
    os.close(fd)
    os.unlink(path)

    col = Collection(path)
    try:
        print(
            f"Building a ~{args.cards}-card collection "
            f"({len(seed['skills'])} seed skills scaled into variants)..."
        )
        build_start = time.perf_counter()
        cards_added, with_state = populate_collection(
            col, plan, topics, args.studied_fraction, rng
        )
        build_secs = time.perf_counter() - build_start
        print(
            f"  built {cards_added} cards in {build_secs:.1f}s; "
            f"{with_state} carry a synthetic FSRS memory state "
            f"({with_state / cards_added:.0%}), the rest are new."
        )

        # Sanity: the RPC must succeed and see the cards before we time it.
        nodes = col._backend.get_topic_graph().nodes
        total_skills = sum(node.total for node in nodes)
        print(
            f"  get_topic_graph returns {len(nodes)} topic nodes covering "
            f"{total_skills} distinct skills."
        )

        for _ in range(args.warmup):
            col._backend.get_topic_graph()

        samples_ms: list[float] = []
        for _ in range(args.runs):
            start = time.perf_counter()
            col._backend.get_topic_graph()
            samples_ms.append((time.perf_counter() - start) * 1000.0)
    finally:
        col.close()
        if os.path.exists(path):
            os.unlink(path)

    samples_ms.sort()
    p50 = percentile(samples_ms, 0.50)
    p95 = percentile(samples_ms, 0.95)
    worst = samples_ms[-1]

    print()
    print(f"get_topic_graph latency over {args.runs} runs on {cards_added} cards:")
    print(f"  p50   : {p50:8.2f} ms")
    print(f"  p95   : {p95:8.2f} ms")
    print(f"  worst : {worst:8.2f} ms")
    print(f"  (min  : {samples_ms[0]:8.2f} ms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
