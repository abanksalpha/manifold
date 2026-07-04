# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""build_teach_bank.py — a 100%-working bank for the TEACH ("new") skills only (D44,
owner directive 2026-07-02).

Owner's runtime model: **teach/"new" skills are served from a pre-generated bank** of
fully-vetted problems (new material must be correct, and these carry the lectures);
**every other tier (relearn, recognize) is generated on the fly** at review and is NOT
banked. This builder produces the teach bank and nothing else.

"100% working" = every banked item passed BOTH gates: :mod:`verify` (SymPy/Z3/brute,
no LLM) AND an independent blind cross-solve (:mod:`independent_solve`). Items are
produced by the live pipeline (:func:`serve_live.next_problem`), so the bank is exactly
what the runtime would serve, just materialized ahead of time. Nothing unverified or
un-cross-solved is ever written; skills that cannot be confirmed after the budget are
reported loudly in the gaps file, never faked.

Coverage-first: it tries to reach ``--target`` items per teach skill, but guarantees the
attempt for every skill and records any that fall short. Crash-resilient + resumable:
each confirmed item is appended to ``teach_bank.items.jsonl`` as it is produced, and a
re-run loads that file and only tops up skills still below target.

Outputs:
* ``teach_bank.items.jsonl`` — append-only log of confirmed items (resume state).
* ``teach_bank.json``        — assembled bank {schema, generated_at, items:[...]}.
* ``teach_bank_gaps.jsonl``  — teach skills with fewer than target (esp. 0) confirmed.

Requires OPENAI_API_KEY (real pipeline, no fixtures; fails loudly without it).

Run (repo root, key loaded):
    set -a && source .env && set +a
    manifold/content/generation/.venv/bin/python \
        manifold/content/generation/build_teach_bank.py --target 3 --concurrency 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import serve_live  # noqa: E402

SEED_DECK = SCRIPT_DIR.parents[0] / "seed_deck.json"
TEACH_TIER = "teach"


def item_id(item: dict[str, Any]) -> str:
    basis = json.dumps(
        {"stem": item.get("stem"), "choices": item.get("choices")},
        sort_keys=True,
        ensure_ascii=False,
    )
    return "mfteach_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def load_teach_skills() -> list[dict[str, Any]]:
    deck = json.loads(SEED_DECK.read_text(encoding="utf-8"))
    skills = deck if isinstance(deck, list) else deck.get("skills", deck)
    out = []
    for s in skills:
        if s.get("tier") != TEACH_TIER:
            continue
        out.append(
            {
                "skill_id": s["skill_id"],
                "topic_id": s.get("topic_id"),
                "tier": TEACH_TIER,
                "skill_name": s.get("name") or s.get("skill_name") or s["skill_id"],
            }
        )
    return out


def load_existing(jsonl_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Resume state: skill_id -> [items] already confirmed (dedup by item_id)."""
    by_skill: dict[str, list[dict[str, Any]]] = {}
    if not jsonl_path.is_file():
        return by_skill
    seen: set[str] = set()
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        iid = rec.get("item_id")
        if iid in seen:
            continue
        seen.add(iid)
        by_skill.setdefault(rec.get("skill_id"), []).append(rec)
    return by_skill


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=3, help="confirmed items to aim for per teach skill")
    parser.add_argument("--max-calls-per-skill", type=int, default=8, help="cap next_problem calls per skill")
    parser.add_argument("--attempts", type=int, default=serve_live.DEFAULT_ATTEMPTS, help="verify attempts per call")
    parser.add_argument("--samples", type=int, default=2, help="blind cross-solve votes per candidate")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="cap skills (sanity runs)")
    parser.add_argument("--items-out", default=str(SCRIPT_DIR / "teach_bank.items.jsonl"))
    parser.add_argument("--out", default=str(SCRIPT_DIR / "teach_bank.json"))
    parser.add_argument("--gaps-out", default=str(SCRIPT_DIR / "teach_bank_gaps.jsonl"))
    args = parser.parse_args(argv)

    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        print("error: OPENAI_API_KEY is not set (real pipeline, no fixtures). Load .env.", file=sys.stderr)
        return 2

    # The BUILDER must GENERATE fresh items. At RUNTIME serve_live routes teach-tier
    # skills to the pre-vetted bank (teach = served from bank), so calling next_problem
    # with no generator would just re-serve existing items and never deepen. Pass an
    # explicit REAL generator to bypass that routing and actually produce new
    # candidates; the cross-solve gate stays real (next_problem resolves it from env).
    # This also deliberately ignores any MANIFOLD_LIVE_FIXTURES double — the bank must
    # be built from real, verified generations, never a test fixture.
    build_cfg = serve_live.ServeConfig.from_env()
    if build_cfg.fixtures_path:
        print(
            "warning: MANIFOLD_LIVE_FIXTURES is set but IGNORED for the bank build "
            "(the bank needs real content, not a fixture double).",
            file=sys.stderr,
        )
    generator = serve_live._make_openai_generator(build_cfg)

    skills = load_teach_skills()
    if args.limit > 0:
        skills = skills[: args.limit]
    if not skills:
        print("error: no teach skills found in seed_deck.json", file=sys.stderr)
        return 2

    items_path = Path(args.items_out)
    existing = load_existing(items_path)
    already = sum(len(v) for v in existing.values())
    print(
        f"build_teach_bank: {len(skills)} teach skill(s), target={args.target}/skill, "
        f"attempts={args.attempts}, samples={args.samples}, concurrency={args.concurrency}; "
        f"resume: {already} item(s) across {len(existing)} skill(s) already confirmed",
        file=sys.stderr,
    )

    write_lock = threading.Lock()
    items_fh = open(items_path, "a", encoding="utf-8")
    confirmed: dict[str, list[dict[str, Any]]] = {k: list(v) for k, v in existing.items()}
    seen_ids: set[str] = {it["item_id"] for v in existing.values() for it in v}
    counters = {"calls": 0, "ok": 0, "skills_done": 0}

    def persist(rec: dict[str, Any]) -> None:
        with write_lock:
            items_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            items_fh.flush()

    def work(skill: dict[str, Any]) -> None:
        sid = skill["skill_id"]
        have = list(confirmed.get(sid, []))
        calls = 0
        while len(have) < args.target and calls < args.max_calls_per_skill:
            calls += 1
            with write_lock:
                counters["calls"] += 1
            try:
                result = serve_live.next_problem(
                    skill, generate=generator, attempts=args.attempts, solve_samples=args.samples
                )
            except Exception as exc:  # a real pipeline bug: surface, do not fake an item
                serve_live._log(f"[{sid}] pipeline exception: {type(exc).__name__}: {exc}")
                break
            if result.get("status") != "ok":
                continue
            item = result["item"]
            iid = item_id(item)
            with write_lock:
                if iid in seen_ids:
                    continue  # duplicate stem; keep trying for variety
                seen_ids.add(iid)
                counters["ok"] += 1
            rec = {
                "item_id": iid,
                "skill_id": sid,
                "topic_id": skill["topic_id"],
                "tier": TEACH_TIER,
                "item": item,
                "verifier_report": result.get("verifier_report"),
                "cross_solved": True,
            }
            have.append(rec)
            persist(rec)
        confirmed[sid] = have
        with write_lock:
            counters["skills_done"] += 1
            n = counters["skills_done"]
        print(f"  [{n}/{len(skills)}] {sid[:46]:46} -> {len(have)}/{args.target}", file=sys.stderr)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(work, s) for s in skills]
        for fut in as_completed(futures):
            fut.result()
    items_fh.close()
    elapsed = time.time() - start

    all_items = [rec for recs in confirmed.values() for rec in recs]
    covered = sum(1 for s in skills if confirmed.get(s["skill_id"]))
    gaps = [
        {"skill_id": s["skill_id"], "topic_id": s["topic_id"], "have": len(confirmed.get(s["skill_id"], [])), "target": args.target}
        for s in skills
        if len(confirmed.get(s["skill_id"], [])) < args.target
    ]

    bank = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "build_teach_bank.py (serve_live: generate -> verify -> cross-solve)",
        "tier": TEACH_TIER,
        "target_per_skill": args.target,
        "teach_skills": len(skills),
        "skills_covered": covered,
        "item_count": len(all_items),
        "items": all_items,
    }
    Path(args.out).write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.gaps_out).write_text("".join(json.dumps(g, ensure_ascii=False) + "\n" for g in gaps), encoding="utf-8")

    print("=" * 64, file=sys.stderr)
    print(
        f"teach bank: {len(all_items)} item(s); coverage {covered}/{len(skills)} skills; "
        f"{len(gaps)} skill(s) below target ({sum(1 for g in gaps if g['have']==0)} at ZERO); "
        f"{counters['calls']} next_problem call(s) in {elapsed:.0f}s",
        file=sys.stderr,
    )
    print(f"  wrote {args.out}; gaps -> {args.gaps_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
