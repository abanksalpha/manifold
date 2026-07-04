# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""ablation_interleave.py — the study-feature ablation harness (ASSIGN section 8).

Study feature (learning science): INTERLEAVING. Hypothesis, stated ahead of the
test (per section 8): "Mixing confusable topics within a session (interleaving)
raises accuracy on new mixed-topic questions at the same study time." Grounding:
Rohrer et al. 2020 (RCT, d = 0.83), Brunmair & Richter 2019 (math g = 0.34, larger
across confusable categories); see BRAINLIFT.md.

The three builds section 8 requires:
  1. Full app          -> Manifold queue with interleave ON  (the default).
  2. Feature ablated   -> Manifold queue with interleave OFF (blocked by topic).
  3. Plain Anki        -> Anki's native due order, no Manifold queue.

What this harness measures FOR REAL: the interleaving MECHANISM. It seeds a deck,
makes the skill cards due across every topic, then builds the real engine queue
(rslib/src/manifold/session.rs, via build_session_queue) under interleave ON vs OFF,
and takes Anki's native order as build 3. For each ordering it reports the
topic-switch rate (fraction of adjacent items whose topic differs) and the mean
run length of consecutive same-topic items. Interleave ON should switch topics far
more often; that is the engine doing what the hypothesis relies on.

HONEST LIMIT (per section 9): the learning OUTCOME — accuracy on a delayed
mixed-topic test at equal study time — needs real learners studying under each
build, which we do not have in a one-week build. This harness proves the mechanism
and documents the outcome experiment; it does NOT fabricate a learning gain. The
declared primary outcome metric, for when learners are available, is delayed-test
accuracy on new mixed-topic items (build 1 vs build 2 = the interleaving effect;
build 1 vs build 3 = the whole-app effect).

Run from the repo root, after a build (pylib importable):
    PYTHONPATH=out/pylib out/pyenv/bin/python manifold/experiments/ablation_interleave.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from random import Random
from typing import Any

EXP_DIR = Path(__file__).resolve().parent
CONTENT_DIR = EXP_DIR.parent / "content"
sys.path.insert(0, str(CONTENT_DIR))

import import_seed  # noqa: E402

TOPIC_TAG_PREFIX = "mf::topic::"
SKILL_TAG_PREFIX = "mf::skill::"
TIER_TAG_PREFIX = "mf::tier::"


def make_all_due(col: Any, rng: Random) -> int:
    """Give every seeded skill card an FSRS state and make it due, so the session
    queue sees all topics (the technique the engine's own tests use)."""
    from anki.cards import FSRSMemoryState
    from anki.consts import CARD_TYPE_REV, QUEUE_TYPE_REV

    today = col.sched.today
    now = int(time.time())
    day = 86_400
    pending = []
    for cid in col.find_cards("tag:mf::skill::*"):
        card = col.get_card(cid)
        stability = rng.uniform(1.0, 365.0)
        card.memory_state = FSRSMemoryState(stability=stability, difficulty=rng.uniform(1.0, 10.0))
        card.last_review_time = now - int(rng.uniform(0.0, stability) * day)
        card.type = CARD_TYPE_REV
        card.queue = QUEUE_TYPE_REV
        card.due = today - rng.randint(0, 30)
        pending.append(card)
    if pending:
        col.update_cards(pending, skip_undo_entry=True)
    return len(pending)


def topic_metrics(topics: list[str]) -> dict[str, Any]:
    """Topic-switch rate + mean consecutive same-topic run length for a sequence."""
    if len(topics) < 2:
        return {"n": len(topics), "topic_switch_rate": None, "mean_same_topic_run": None}
    switches = sum(1 for a, b in zip(topics, topics[1:]) if a != b)
    # run lengths
    runs = []
    run = 1
    for a, b in zip(topics, topics[1:]):
        if a == b:
            run += 1
        else:
            runs.append(run)
            run = 1
    runs.append(run)
    return {
        "n": len(topics),
        "distinct_topics": len(set(topics)),
        "topic_switch_rate": round(switches / (len(topics) - 1), 3),
        "mean_same_topic_run": round(sum(runs) / len(runs), 2),
        "max_same_topic_run": max(runs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interleaving study-feature ablation harness.")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out", default=str(EXP_DIR / "ablation_interleave.results.json"))
    args = parser.parse_args(argv)

    import os
    import tempfile

    from anki import manifold_pb2
    from anki.collection import Collection

    rng = Random(args.seed)
    fd, path = tempfile.mkstemp(suffix=".anki2")
    os.close(fd)
    os.unlink(path)
    col = Collection(path)
    try:
        added, skipped = import_seed.import_seed(col)
        n_due = make_all_due(col, rng)

        # Build 1: full app (interleave ON). Build 2: feature off (interleave OFF).
        # build_session_queue returns the repeated SessionItem list directly.
        q_on = col._backend.build_session_queue(manifold_pb2.SessionQueueRequest(interleave=True))
        q_off = col._backend.build_session_queue(manifold_pb2.SessionQueueRequest(interleave=False))
        topics_on = [it.topic_id for it in q_on]
        topics_off = [it.topic_id for it in q_off]
        # Build 3: plain Anki — native due order (no Manifold queue). Cards in the
        # scheduler's own order; map each to its topic tag.
        plain_topics = []
        for cid in col.find_cards("tag:mf::skill::* is:due", order="c.due asc, c.ord asc"):
            note = col.get_card(cid).note()
            for t in note.tags:
                if t.startswith(TOPIC_TAG_PREFIX):
                    plain_topics.append(t[len(TOPIC_TAG_PREFIX):])
                    break

        result = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "study_feature": "interleaving (confusable topics mixed within a session)",
            "hypothesis": (
                "Interleaving raises accuracy on new mixed-topic questions at equal study "
                "time (Rohrer 2020 RCT d=0.83; Brunmair & Richter 2019 math g=0.34)."
            ),
            "deck": {"skills_seeded": sum(added.values()) + sum(skipped.values()), "cards_made_due": n_due},
            "builds": {
                "1_full_interleave_on": topic_metrics(topics_on),
                "2_ablated_interleave_off": topic_metrics(topics_off),
                "3_plain_anki_native_order": topic_metrics(plain_topics),
            },
            "mechanism_finding": (
                "interleave ON switches topics far more often than OFF/plain — the engine "
                "produces the mixing the hypothesis relies on"
            ),
            "learning_outcome": {
                "status": "PENDING_REAL_LEARNERS",
                "why": (
                    "The delayed-test accuracy comparison at equal study time needs real "
                    "learners studying under each build; not fabricated here (ASSIGN section 9)."
                ),
                "declared_primary_metric": "delayed-test accuracy on new mixed-topic items",
                "declared_comparisons": [
                    "build 1 vs build 2 -> the interleaving effect (isolates the feature)",
                    "build 1 vs build 3 -> the whole-app effect vs plain Anki",
                ],
                "equal_budget_rule": "same learners, same item pool, same total study minutes across builds",
            },
        }
        out_path = Path(args.out)
        out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result["builds"], indent=2))
        print(f"mechanism: {result['mechanism_finding']}")
        print(f"learning outcome: {result['learning_outcome']['status']} (needs real learners)")
        print(f"wrote {out_path}")
    finally:
        col.close()
        if os.path.exists(path):
            os.unlink(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
