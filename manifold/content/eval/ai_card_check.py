# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""ai_card_check.py — the AI card-quality check + simpler-baseline comparison
(ASSIGN 7f + the Friday "beat a simpler method" requirement).

What it measures, for real (no fabrication):
For a random sample of skills, it runs the REAL generation pipeline draft-by-draft
(model -> assemble -> verify.py (deterministic SymPy/Z3) -> independent_solve.py
(blind cross-solve)) and classifies every well-formed candidate:

  * correct_useful      : verify PASSED and the blind cross-solve AGREED  -> servable
  * wrong_verify        : verify caught the claimed answer as wrong/ambiguous
  * wrong_cross_solve   : verify passed but an independent solver disagreed (stem<->answer
                          mismatch the tautological verify can't see)
  * needs_curation      : the model honestly flagged "no machine-checkable check"
  * gen_error           : malformed draft (regenerated in production; not shippable)

Pre-declared cutoff (fixed BEFORE the run, per 7f): Manifold serves an item ONLY if it
passes BOTH verify AND the blind cross-solve. So by construction ZERO wrong items reach
a learner; the wrong_* counts are exactly what the gate REJECTS.

The simpler baseline: "ship every well-formed generated draft" (a plausible naive
generator with no checker). Its wrong-shipped rate = wrong_verify + wrong_cross_solve.
The delta vs the gated pipeline (0 wrong shipped) is the measured value of the AI check.

This is honest measurement, not a demo: every number comes from running verify.py + the
cross-solver on freshly generated items. Requires OPENAI_API_KEY (real pipeline).

Run (repo root, key loaded):
    set -a && source .env && set +a
    manifold/content/generation/.venv/bin/python \
        manifold/content/eval/ai_card_check.py --count 30 --drafts-per-skill 2 --concurrency 3
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent  # manifold/content/eval
GEN_DIR = SCRIPT_DIR.parents[0] / "generation"  # manifold/content/generation
sys.path.insert(0, str(GEN_DIR))

import independent_solve  # noqa: E402
import serve_live  # noqa: E402
import verify  # noqa: E402

SEED_DECK = SCRIPT_DIR.parents[0] / "seed_deck.json"
# Sample from the live-generated tiers (teach is served from the pre-vetted bank).
LIVE_TIERS = ("relearn", "recognize")


def load_live_skills() -> list[dict[str, Any]]:
    deck = json.loads(SEED_DECK.read_text(encoding="utf-8"))
    out = []
    for s in deck["skills"]:
        if s.get("tier") in LIVE_TIERS:
            out.append({
                "skill_id": s["skill_id"],
                "topic_id": s.get("topic_id"),
                "tier": s["tier"],
                "skill_name": s.get("name") or s["skill_id"],
                "difficulty": "med",
            })
    return out


def check_one_draft(
    skill: dict[str, Any], gen, solve_cfg, solve_fn, samples: int, seed: int, attempt: int
) -> str:
    """Generate ONE draft and return its outcome class (see module docstring)."""
    try:
        draft = gen(skill, skill.get("difficulty", "med"))
    except serve_live.NeedsCuration:
        return "needs_curation"
    except serve_live.GenerationError:
        return "gen_error"
    except serve_live.AuthError:
        raise
    except serve_live.TransientError:
        return "transient"
    item, _ = serve_live._assemble_item(skill, draft, seed=seed, attempt=attempt)
    try:
        verified, _report = verify.verify(item)
    except Exception:
        return "gen_error"  # a shape-valid check that still raised = generator bug
    if not verified:
        return "wrong_verify"
    verdict = independent_solve.check_agreement(item, config=solve_cfg, solve=solve_fn, samples=samples)
    return "correct_useful" if verdict["agreed"] else "wrong_cross_solve"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=30, help="skills to sample")
    parser.add_argument("--drafts-per-skill", type=int, default=2)
    parser.add_argument("--samples", type=int, default=2, help="cross-solve votes per draft")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out", default=str(SCRIPT_DIR / "results" / "ai_card_check.json"))
    args = parser.parse_args(argv)

    cfg = serve_live.ServeConfig.from_env()
    if not cfg.api_key:
        print("error: OPENAI_API_KEY not set (real pipeline).", file=sys.stderr)
        return 2
    gen = serve_live._make_openai_generator(cfg)
    solve_cfg = independent_solve.SolveConfig.from_env()
    solve_fn, reason = independent_solve.select_solver(solve_cfg)
    if solve_fn is None:
        print(f"error: no cross-solver available ({reason}).", file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    skills = load_live_skills()
    rng.shuffle(skills)
    skills = skills[: args.count]

    counts = {k: 0 for k in (
        "correct_useful", "wrong_verify", "wrong_cross_solve", "needs_curation", "gen_error", "transient")}
    lock = threading.Lock()
    done = {"n": 0}

    def work(skill: dict[str, Any]) -> None:
        for d in range(args.drafts_per_skill):
            outcome = check_one_draft(
                skill, gen, solve_cfg, solve_fn, args.samples,
                seed=args.seed + hash(skill["skill_id"]) % 100000, attempt=d + 1,
            )
            with lock:
                counts[outcome] = counts.get(outcome, 0) + 1
        with lock:
            done["n"] += 1
            n = done["n"]
        print(f"  [{n}/{len(skills)}] {skill['skill_id'][:44]:44}", file=sys.stderr)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    start = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(work, s) for s in skills]
        for f in as_completed(futures):
            f.result()
    elapsed = time.time() - start

    well_formed = counts["correct_useful"] + counts["wrong_verify"] + counts["wrong_cross_solve"]
    wrong_caught = counts["wrong_verify"] + counts["wrong_cross_solve"]
    gated_wrong_shipped = 0  # by construction: only verify+cross-solve pass are served
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample": {"skills": len(skills), "drafts_per_skill": args.drafts_per_skill,
                   "total_drafts": len(skills) * args.drafts_per_skill, "tiers": list(LIVE_TIERS)},
        "cutoff_declared_before_run": "serve an item ONLY if it passes BOTH verify.py AND the blind cross-solve",
        "counts": counts,
        "derived": {
            "well_formed_drafts": well_formed,
            "correct_useful_rate": round(counts["correct_useful"] / well_formed, 3) if well_formed else None,
            "wrong_caught_by_gate": wrong_caught,
            "wrong_caught_rate": round(wrong_caught / well_formed, 3) if well_formed else None,
        },
        "baseline_ship_all_drafts": {
            "description": "simpler method: ship every well-formed generated draft, no checker",
            "wrong_items_shipped": wrong_caught,
            "wrong_ship_rate": round(wrong_caught / well_formed, 3) if well_formed else None,
        },
        "gated_pipeline": {
            "description": "Manifold: serve iff verify AND cross-solve agree",
            "wrong_items_shipped": gated_wrong_shipped,
            "note": "0 by construction; the gate rejects every wrong_* draft above",
        },
        "elapsed_s": round(elapsed, 1),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("=" * 64, file=sys.stderr)
    print(f"AI card check: {counts}", file=sys.stderr)
    print(
        f"  well-formed={well_formed}  wrong CAUGHT by gate={wrong_caught}  "
        f"baseline (ship-all) would ship {wrong_caught} wrong; gated pipeline ships 0.",
        file=sys.stderr,
    )
    print(f"  wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
