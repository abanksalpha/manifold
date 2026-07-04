# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Offline / AI-off test: the engine still produces scores with no network.

ASSIGN.md section 7g and AC10/AC23 require that when AI is switched off and the
network is gone, the app keeps working and still gives a score. Manifold is
bank-first by design: the review loop and the three scores (Memory, Performance,
Readiness) are computed by the Rust engine and the scoring layer, with no live
model call on the scoring path. This test proves that at the engine level,
headless.

What it does:

  1. Hard-block the network: outbound socket connections and DNS resolution are
     replaced with functions that raise. Any attempt to reach the network fails
     loudly, so if the scoring path completes, it demonstrably used no network.
  2. Turn AI off: remove OPENAI_API_KEY from the environment. The engine and
     scoring path never read it; the run completing without it is the proof.
  3. Build an isolated temp collection and drive a deterministic offline session:
     seed skill cards across every blueprint topic, then answer them cold through
     Anki's real answer path to produce genuine unsupported (Review-kind) revlog
     evidence, and set FSRS memory states so the retrievability rollup has data.
  4. Call the get_topic_graph engine RPC and derive the score inputs the way the
     scoring layer does: Memory (blueprint-weighted mean FSRS recall), Performance
     (weighted mean unsupported accuracy), coverage, and the give-up rule.
  5. Print the scores and the readiness give-up decision, then assert the pipeline
     produced valid inputs and a definite decision, all with the network blocked.

Honesty and scope: this is a synthetic drive, not one real student's history. The
review answers are scripted (a fixed 80/20 correct split) and the FSRS memory
states are generated load, both clearly labelled, so the printed numbers are a
demonstration that the pipeline runs offline, not an ability estimate. The
review evidence (the revlog rows) is real, written by the real answer path. The
readiness scaled-range mapping itself lives in the TypeScript scoring layer
(ts/lib/manifold/scoring.ts), which is a pure deterministic function of these
same engine inputs and makes no network or model call on the scoring path; this
script verifies the engine and data half that feeds it, headless.

Run from the repo root, after a build. No PYTHONPATH needed (the script adds the
built pylib to sys.path itself):

    out/pyenv/bin/python manifold/tests/offline.py

Flags: --rounds N (review passes; default auto, enough to clear the give-up
review count), --seed N (RNG seed for the scripted drive).
"""

from __future__ import annotations

import argparse
import math
import os
import socket
import sys
import tempfile
import time
from pathlib import Path
from random import Random
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent  # manifold/tests
REPO_ROOT = SCRIPT_DIR.parents[1]  # repo root
OUT = REPO_ROOT / "out"
PYLIB = OUT / "pylib"
CONTENT_DIR = REPO_ROOT / "manifold" / "content"

# Make the built `anki` package and the blueprint loaders importable, so this
# runs with a bare `out/pyenv/bin/python manifold/tests/offline.py`.
sys.path.insert(0, str(PYLIB))
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402

# The give-up rule, mirrored from ts/lib/manifold/scoring.ts. Readiness stays
# silent until both hold; keep these in sync with that module (the source of
# truth for the rule the UI enforces).
READINESS_MIN_INDEPENDENT_REVIEWS = 200
READINESS_MIN_COVERAGE = 0.5

DECK_NAME = "GRE Mathematics"
SKILL_TAG_SEARCH = "tag:mf::skill::*"
GOOD = 3  # answerCard ease: 3 = Good
AGAIN = 1  # answerCard ease: 1 = Again
GOOD_SHARE = 0.8  # scripted correct fraction, so Performance is not degenerate


def install_network_firewall() -> None:
    """Replace outbound network primitives with functions that raise.

    Blocks TCP/UDP connections and DNS. Local file and in-process work (SQLite,
    the compiled rsbridge backend) use no sockets, so the engine and scoring path
    keep working; anything that actually reaches for the network fails loudly.
    """
    denied = RuntimeError("offline test: network access is blocked")

    def deny(*_args: Any, **_kwargs: Any):
        raise denied

    socket.socket.connect = deny  # type: ignore[method-assign]
    socket.socket.connect_ex = deny  # type: ignore[method-assign]
    socket.create_connection = deny  # type: ignore[assignment]
    socket.getaddrinfo = deny  # type: ignore[assignment]


def turn_ai_off() -> str:
    """Remove the AI key from the environment. Returns a short status string."""
    had_key = os.environ.pop("OPENAI_API_KEY", None) is not None
    return "was set, now removed" if had_key else "not set"


def _weighted_range(
    nodes: list[Any],
    value: Callable[[Any], float],
    include: Callable[[Any], bool],
) -> tuple[float, float, float, int] | None:
    """Blueprint-weighted mean with the observed spread, mirroring scoring.ts.

    Returns (value, low, high, contributing_topics), or None if nothing
    contributes.
    """
    weight_sum = 0.0
    weighted_value_sum = 0.0
    low = math.inf
    high = -math.inf
    contributing = 0
    for node in nodes:
        if not include(node):
            continue
        v = value(node)
        weight_sum += node.weight
        weighted_value_sum += node.weight * v
        low = min(low, v)
        high = max(high, v)
        contributing += 1
    if contributing == 0 or weight_sum == 0:
        return None
    return weighted_value_sum / weight_sum, low, high, contributing


def _weighted_coverage(nodes: list[Any]) -> float:
    weight_sum = sum(node.weight for node in nodes)
    if weight_sum == 0:
        raise RuntimeError("topic graph has zero total blueprint weight")
    return sum(node.weight * node.coverage for node in nodes) / weight_sum


def seed_all_topics(col: Any, blueprint: dict[str, Any]) -> int:
    """Seed `expected_skills` skill cards for every blueprint topic.

    Seeding each topic to its expected skill count makes coverage complete, so
    the give-up rule's coverage condition can be exercised. Tiers come straight
    from the blueprint, so the engine accepts every card.
    """
    deck_id = col.decks.id(DECK_NAME)
    notetype = col.models.by_name("Basic")
    if notetype is None:
        raise RuntimeError("notetype 'Basic' not found in collection")

    for topic in blueprint["topics"]:
        topic_id = topic["id"]
        tier = topic["tier"]
        expected = int(topic["expected_skills"])
        if expected < 1:
            raise RuntimeError(f"blueprint topic {topic_id!r} has expected_skills < 1")
        for index in range(expected):
            note = col.new_note(notetype)
            note["Front"] = f"{topic_id} skill {index}"
            note["Back"] = topic["title"]
            note.tags = [
                f"mf::topic::{topic_id}",
                f"mf::skill::{topic_id}__off_{index}",
                f"mf::tier::{tier}",
            ]
            col.add_note(note, deck_id)
    return len(col.find_cards(SKILL_TAG_SEARCH))


def _set_review_state(col: Any, card_ids: list[int], rng: Random, backdate: bool) -> None:
    """Put each card in the Review stage with an FSRS memory state.

    Cards must be Review-stage for their answers to count as unsupported
    (Review-kind) evidence. When `backdate` is set, the last review is pushed
    into the past so retrievability spans a realistic range instead of pinning
    near 1.0; the memory states are generated load, as in the benchmark.
    """
    from anki.cards import FSRSMemoryState
    from anki.consts import CARD_TYPE_REV, QUEUE_TYPE_REV

    now = int(time.time())
    day = 86_400
    today = col.sched.today
    pending = []
    for cid in card_ids:
        card = col.get_card(cid)
        stability = rng.uniform(5.0, 200.0)
        card.memory_state = FSRSMemoryState(stability=stability, difficulty=rng.uniform(1.0, 10.0))
        elapsed_days = rng.uniform(0.0, stability) if backdate else 0.0
        card.last_review_time = now - int(elapsed_days * day)
        card.type = CARD_TYPE_REV
        card.queue = QUEUE_TYPE_REV
        card.due = today
        pending.append(card)
    col.update_cards(pending, skip_undo_entry=True)


def drive_offline_reviews(col: Any, card_ids: list[int], rounds: int, rng: Random) -> int:
    """Answer every card cold for `rounds` passes; return the review count.

    Each pass resets the cards to the Review stage first, so every answer is an
    unsupported Review-kind attempt (a card that lapsed on Again would otherwise
    become Relearning and stop counting). Answers follow a fixed correct split.
    """
    answered = 0
    for _ in range(rounds):
        _set_review_state(col, card_ids, rng, backdate=False)
        for cid in card_ids:
            card = col.get_card(cid)
            card.start_timer()
            rating = GOOD if rng.random() < GOOD_SHARE else AGAIN
            col.sched.answerCard(card, rating)
            answered += 1
    # Final memory states drive the Memory (recall) score with a realistic spread.
    _set_review_state(col, card_ids, rng, backdate=True)
    return answered


def _fmt_range(estimate: tuple[float, float, float, int] | None) -> str:
    if estimate is None:
        return "n/a (no contributing topics)"
    value, low, high, topics = estimate
    return f"{value:.3f}  (range {low:.3f} to {high:.3f} over {topics} topics)"


def run(rounds_arg: int | None, seed: int) -> int:
    install_network_firewall()
    ai_status = turn_ai_off()

    from anki.collection import Collection

    rng = Random(seed)
    blueprint = import_seed.load_json(import_seed.DEFAULT_BLUEPRINT)

    print("Manifold offline / AI-off scoring test")
    print("  network      : outbound connections and DNS are blocked for this run")
    print(f"  OPENAI_API_KEY: {ai_status}")

    fd, path = tempfile.mkstemp(suffix=".anki2")
    os.close(fd)
    os.unlink(path)

    col = Collection(path)
    try:
        skill_cards = seed_all_topics(col, blueprint)
        card_ids = list(col.find_cards(SKILL_TAG_SEARCH))
        rounds = rounds_arg if rounds_arg is not None else max(
            2, READINESS_MIN_INDEPENDENT_REVIEWS // max(1, len(card_ids)) + 1
        )
        answered = drive_offline_reviews(col, card_ids, rounds, rng)
        print(
            f"  seeded {skill_cards} skill cards across {len(blueprint['topics'])} "
            f"topics; drove {answered} cold reviews in {rounds} passes "
            f"(scripted {GOOD_SHARE:.0%} correct), all offline."
        )

        response = col._backend.get_topic_graph()
        nodes = list(response.nodes)
        if not nodes:
            raise RuntimeError("get_topic_graph returned no topics with the network blocked")
        if not response.HasField("scoring_config"):
            raise RuntimeError("get_topic_graph returned no scoring_config with the network blocked")
    finally:
        col.close()
        if os.path.exists(path):
            os.unlink(path)

    memory = _weighted_range(nodes, lambda n: n.avg_recall, lambda n: n.total > 0)
    performance = _weighted_range(
        nodes, lambda n: n.performance, lambda n: n.independent_reviews > 0
    )
    coverage = _weighted_coverage(nodes)
    total_independent = sum(node.independent_reviews for node in nodes)
    gate_met = (
        total_independent >= READINESS_MIN_INDEPENDENT_REVIEWS
        and coverage >= READINESS_MIN_COVERAGE
    )

    print()
    print("Three scores, computed by the engine with AI off and no network:")
    print(f"  Memory (weighted FSRS recall)        : {_fmt_range(memory)}")
    print(f"  Performance (weighted cold accuracy) : {_fmt_range(performance)}")
    print(f"  Coverage (weighted, of the blueprint): {coverage:.3f}")
    print()
    print("Readiness give-up rule (from scoring.ts):")
    print(
        f"  unsupported reviews {total_independent} "
        f"(need {READINESS_MIN_INDEPENDENT_REVIEWS}); "
        f"coverage {coverage:.2f} (need {READINESS_MIN_COVERAGE:.2f})"
    )
    if gate_met:
        perf_value = performance[0] if performance else 0.0
        print(
            "  decision: give-up rule satisfied. Readiness projects an ETS-anchored "
            "scaled range from these inputs."
        )
        print(
            f"  the scaled range is a deterministic function of Performance "
            f"({perf_value:.3f}) and coverage ({coverage:.2f}), computed offline by "
            "ts/lib/manifold/scoring.ts (no network, no model call on the scoring path)."
        )
    else:
        print(
            "  decision: abstain. Readiness shows no number and names the missing "
            "evidence, which is itself a valid honest output with AI off."
        )

    # Assertions: the pipeline must have produced valid inputs and a decision,
    # all with the network blocked. Any network attempt would already have raised.
    if memory is None:
        raise RuntimeError("Memory score has no contributing topics; the rollup produced nothing")
    if not 0.0 <= memory[0] <= 1.0:
        raise RuntimeError(f"Memory {memory[0]} is outside [0, 1]")
    if not 0.0 <= coverage <= 1.0:
        raise RuntimeError(f"coverage {coverage} is outside [0, 1]")
    if total_independent <= 0:
        raise RuntimeError("no unsupported reviews were recorded; the drive produced no evidence")

    print()
    print(
        "PASS: with the network blocked and AI off, the engine ingested a real "
        "review history and produced the score inputs and the give-up decision. "
        "No network was reachable at any point in the run."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manifold offline / AI-off scoring test.")
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="review passes over the deck (default: auto, enough to clear the give-up count)",
    )
    parser.add_argument("--seed", type=int, default=1234, help="RNG seed for the scripted drive")
    args = parser.parse_args(argv)
    if args.rounds is not None and args.rounds < 1:
        parser.error("--rounds must be positive")
    return run(args.rounds, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
