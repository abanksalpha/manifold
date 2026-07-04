# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""paraphrase.py — the paraphrase test (ASSIGN 7d), generation side.

7d proves you measure PERFORMANCE, not just memory: take a skill, ask it "in new
words", and check the item still tests the same idea. Manifold's architecture already
separates the two — MEMORY is FSRS recall of a practiced skill (mastery.rs), while
PERFORMANCE is a COLD, freshly generated exam-style item (Review-kind attempts only,
D20/D21) — so a performance item is never the memorized card wording.

This harness measures the GENERATION side of 7d on real content: the teach bank holds
multiple VERIFIED items per skill (the deepening produced 2-3 each for many skills).
Those are paraphrases — same skill, independently generated, each passing verify.py AND
the blind cross-solve. For every skill with >=2 items it reports:
  * surface variety: pairwise lexical similarity of stem+choices (leakage_check's
    shingle/Jaccard). LOW similarity = genuinely reworded, not the same card twice (D42).
  * correctness fidelity: every paraphrase is verify-passed + cross-solved, so the idea
    survives the rewording with a correct, checkable answer.

HONEST LIMIT (7d / section 9): the learner-side number 7d ultimately wants — a student's
recall on the card vs their accuracy on the reworded questions, and the GAP between them —
needs real per-student data. Manifold logs both channels already (memory = FSRS R;
performance = cold Review-kind correctness), so the pipeline exists; the gap awaits real
learners. This harness does NOT fabricate that gap; it measures paraphrase quality, which
is the precondition for the test to be meaningful.

Run: manifold/content/generation/.venv/bin/python manifold/content/eval/paraphrase.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
GEN_DIR = SCRIPT_DIR.parents[0] / "generation"
sys.path.insert(0, str(GEN_DIR))

import leakage_check  # noqa: E402

DEFAULT_BANK = GEN_DIR / "teach_bank.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Paraphrase quality test (7d, generation side).")
    parser.add_argument("--bank", default=str(DEFAULT_BANK))
    parser.add_argument("--shingle", type=int, default=leakage_check.DEFAULT_SHINGLE)
    parser.add_argument("--distinct-threshold", type=float, default=0.5,
                        help="pairwise similarity below this counts as a genuine paraphrase")
    parser.add_argument("--out", default=str(SCRIPT_DIR / "results" / "paraphrase.json"))
    args = parser.parse_args(argv)

    data = json.loads(Path(args.bank).read_text(encoding="utf-8"))
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for rec in data.get("items", []):
        by_skill.setdefault(rec["skill_id"], []).append(rec["item"])

    multi = {sid: items for sid, items in by_skill.items() if len(items) >= 2}
    per_skill = []
    all_sims = []
    genuine_pairs = 0
    total_pairs = 0
    for sid, items in sorted(multi.items()):
        sh = [leakage_check.shingles(leakage_check.tokenize(leakage_check.item_text(it)), args.shingle)
              for it in items]
        sims = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                s = leakage_check.jaccard(sh[i], sh[j])
                sims.append(s)
                all_sims.append(s)
                total_pairs += 1
                if s < args.distinct_threshold:
                    genuine_pairs += 1
        per_skill.append({
            "skill_id": sid, "n_items": len(items),
            "mean_pairwise_similarity": round(sum(sims) / len(sims), 3) if sims else None,
            "max_pairwise_similarity": round(max(sims), 3) if sims else None,
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "what_this_measures": "paraphrase quality (surface variety + correctness fidelity) of the "
        "multiple verified items per skill in the teach bank; the generation side of 7d.",
        "skills_with_paraphrases": len(multi),
        "total_paraphrase_pairs": total_pairs,
        "mean_pairwise_similarity_all": round(sum(all_sims) / len(all_sims), 3) if all_sims else None,
        "genuine_paraphrase_pairs": genuine_pairs,
        "genuine_pair_rate": round(genuine_pairs / total_pairs, 3) if total_pairs else None,
        "correctness_fidelity": "every item is verify-passed AND blind-cross-solved, so each "
        "paraphrase carries a correct, machine-checked answer (same idea survives rewording).",
        "learner_side_gap": {
            "status": "PENDING_REAL_LEARNERS",
            "wants": "student recall on the practiced card vs accuracy on reworded items, and the gap",
            "pipeline_ready": "Manifold logs memory (FSRS R) and performance (cold Review-kind "
            "correctness) separately, so the two channels exist; the gap awaits real learners.",
        },
        "per_skill": per_skill,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"paraphrase (7d, generation side): {len(multi)} skills with >=2 verified paraphrases, "
          f"{total_pairs} pairs")
    print(f"  mean pairwise similarity={report['mean_pairwise_similarity_all']} "
          f"(low = genuine rewording); genuine-pair rate={report['genuine_pair_rate']}")
    print(f"  learner-side recall-vs-accuracy gap: PENDING real learners (both channels logged)")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
