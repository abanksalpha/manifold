# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""build_skill_bank.py — deep per-skill bank across ALL tiers (content buildout).

Generalizes ``build_teach_bank.py`` from the teach tier / target 3 to **every
skill in the deck at a configurable target (default 30)**, so the runtime can be
flipped to bank-first and the live (AI-on) hot path retired for
``relearn``/``recognize`` too. See ``docs/manifold/plan-bank-buildout.md``.

One **focused unit of work per skill**: each skill gets its own generation loop,
its own quota, and its own gap record. Items are produced by the real live
pipeline (:func:`serve_live.next_problem`: generate -> verify -> deterministic
arithmetic re-check -> blind cross-solve), so a banked item is exactly what the
runtime would serve, materialized ahead of time. Nothing unverified or
un-cross-solved is ever written; skills short of target are recorded loudly in
the gaps file, never faked (standing no-fabrication rule).

Same crash-resilient/resumable design as the teach builder: every confirmed item
is appended to an items ``.jsonl`` as it is produced; a re-run loads that file and
only tops up skills still below target. Difficulty is rotated (easy/med/hard)
across calls for surface variety (D42).

Cost controls (this runs the REAL paid pipeline):
* ``--dry-run``          — print the work plan (skills x remaining, call envelope);
                           makes NO API calls.
* ``--max-calls-per-skill`` — cap ``next_problem`` calls for one skill.
* ``--max-total-calls`` — global ceiling across the whole run (0 = unlimited);
                           the run stops scheduling new calls once hit.

Requires OPENAI_API_KEY for a real (non-dry) run; fails loudly without it.

Run (repo root, key loaded):
    set -a && source .env && set +a
    manifold/content/generation/.venv/bin/python \
        manifold/content/generation/build_skill_bank.py \
        --tiers relearn,recognize --target 30 --concurrency 6 \
        --max-total-calls 200 --model gpt-4o-mini
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
ALL_TIERS = ("teach", "relearn", "recognize")
DIFFICULTIES = ("easy", "med", "hard")


def item_id(item: dict[str, Any]) -> str:
    """Stable id from the display-identity fields, for dedup / idempotent resume."""
    basis = json.dumps(
        {"stem": item.get("stem"), "choices": item.get("choices")},
        sort_keys=True,
        ensure_ascii=False,
    )
    return "mfbank_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def load_skills(tiers: set[str], topics: set[str] | None, only_skill: str | None) -> list[dict[str, Any]]:
    """Deck skills filtered by tier / topic / a single skill id."""
    deck = json.loads(SEED_DECK.read_text(encoding="utf-8"))
    skills = deck if isinstance(deck, list) else deck.get("skills", deck)
    out: list[dict[str, Any]] = []
    for s in skills:
        if s.get("tier") not in tiers:
            continue
        if topics and s.get("topic_id") not in topics:
            continue
        if only_skill and s.get("skill_id") != only_skill:
            continue
        out.append(
            {
                "skill_id": s["skill_id"],
                "topic_id": s.get("topic_id"),
                "tier": s.get("tier"),
                "skill_name": s.get("name") or s.get("skill_name") or s["skill_id"],
            }
        )
    return out


def load_existing(jsonl_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Resume state: skill_id -> [records] already confirmed (dedup by item_id)."""
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


def parse_csv(value: str | None, valid: tuple[str, ...] | None = None) -> set[str] | None:
    if not value:
        return None
    parts = {p.strip() for p in value.split(",") if p.strip()}
    if valid is not None:
        bad = parts - set(valid)
        if bad:
            raise SystemExit(f"error: unknown value(s) {sorted(bad)}; valid: {', '.join(valid)}")
    return parts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=30, help="confirmed items to aim for per skill")
    parser.add_argument("--tiers", default=",".join(ALL_TIERS), help="comma list of tiers to build")
    parser.add_argument("--topics", default=None, help="comma list of topic_ids to restrict to")
    parser.add_argument("--skill", default=None, help="build a single skill_id (for one-skill agents)")
    parser.add_argument("--max-calls-per-skill", type=int, default=90, help="cap next_problem calls per skill")
    parser.add_argument("--max-total-calls", type=int, default=0, help="global call ceiling (0 = unlimited)")
    parser.add_argument("--abandon-after", type=int, default=15, help="give up on a skill with ZERO confirmed after this many calls (0-yield guard)")
    parser.add_argument("--plateau-after", type=int, default=30, help="give up on a skill after this many calls with no NEW distinct item")
    parser.add_argument("--attempts", type=int, default=serve_live.DEFAULT_ATTEMPTS, help="verify attempts per call")
    parser.add_argument("--samples", type=int, default=2, help="blind cross-solve votes per candidate")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="cap number of skills (sanity/pilot runs)")
    parser.add_argument("--model", default=None, help="override the generator model (else OPENAI_MODEL)")
    parser.add_argument("--dry-run", action="store_true", help="print the work plan; make NO API calls")
    parser.add_argument("--items-out", default=str(SCRIPT_DIR / "skill_bank.items.jsonl"))
    parser.add_argument("--out", default=str(SCRIPT_DIR / "skill_bank.json"))
    parser.add_argument("--gaps-out", default=str(SCRIPT_DIR / "skill_bank_gaps.jsonl"))
    args = parser.parse_args(argv)

    tiers = parse_csv(args.tiers, ALL_TIERS) or set(ALL_TIERS)
    topics = parse_csv(args.topics)

    skills = load_skills(tiers, topics, args.skill)
    if args.limit > 0:
        skills = skills[: args.limit]
    if not skills:
        print("error: no skills matched the tier/topic/skill filters", file=sys.stderr)
        return 2

    items_path = Path(args.items_out)
    existing = load_existing(items_path)
    already = sum(len(v) for v in existing.values())

    remaining = {s["skill_id"]: max(0, args.target - len(existing.get(s["skill_id"], []))) for s in skills}
    total_remaining = sum(remaining.values())
    # Upper bound on calls this run could make (each skill capped independently).
    call_envelope = sum(min(args.max_calls_per_skill, r * args.attempts) for r in remaining.values())

    print(
        f"build_skill_bank: {len(skills)} skill(s) across tiers {sorted(tiers)}; "
        f"target={args.target}/skill; have {already} item(s); need {total_remaining} more; "
        f"call envelope <= {call_envelope}"
        + (f"; global cap {args.max_total_calls}" if args.max_total_calls else ""),
        file=sys.stderr,
    )

    if args.dry_run:
        # No API spend: just show what a real run would attempt.
        by_topic: dict[str, dict[str, int]] = {}
        for s in skills:
            b = by_topic.setdefault(s["topic_id"] or "(none)", {"skills": 0, "need": 0})
            b["skills"] += 1
            b["need"] += remaining[s["skill_id"]]
        print("DRY RUN (no API calls). Per-topic remaining need:", file=sys.stderr)
        for tid, b in sorted(by_topic.items()):
            print(f"  {tid:34} skills={b['skills']:3}  need={b['need']:4}", file=sys.stderr)
        print(
            f"  would target {total_remaining} new item(s); "
            f"set a real run with --max-total-calls to bound spend.",
            file=sys.stderr,
        )
        return 0

    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        print("error: OPENAI_API_KEY is not set (real pipeline, no fixtures). Load .env.", file=sys.stderr)
        return 2

    # The builder must GENERATE fresh items with a REAL generator (an explicit
    # generator bypasses serve_live's teach->bank routing so we actually deepen the
    # bank). Fixtures are deliberately ignored: the bank needs real, verified content.
    build_cfg = serve_live.ServeConfig.from_env()
    if build_cfg.fixtures_path:
        print(
            "warning: MANIFOLD_LIVE_FIXTURES is set but IGNORED for the bank build "
            "(the bank needs real content, not a fixture double).",
            file=sys.stderr,
        )
    if args.model:
        build_cfg.model = args.model
    generator = serve_live._make_openai_generator(build_cfg)
    print(f"  generator model: {build_cfg.model}; cross-solve samples: {args.samples}", file=sys.stderr)

    write_lock = threading.Lock()
    stop = threading.Event()  # tripped when the global call ceiling is reached
    items_fh = open(items_path, "a", encoding="utf-8")
    confirmed: dict[str, list[dict[str, Any]]] = {k: list(v) for k, v in existing.items()}
    seen_ids: set[str] = {it["item_id"] for v in existing.values() for it in v}
    counters = {"calls": 0, "ok": 0, "skills_done": 0}

    def persist(rec: dict[str, Any]) -> None:
        with write_lock:
            items_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            items_fh.flush()

    def reserve_call() -> bool:
        """Account one upcoming call against the global ceiling. False => stop."""
        with write_lock:
            if args.max_total_calls and counters["calls"] >= args.max_total_calls:
                stop.set()
                return False
            counters["calls"] += 1
            return True

    def work(skill: dict[str, Any]) -> None:
        sid = skill["skill_id"]
        have = list(confirmed.get(sid, []))
        calls = 0
        calls_since_new = 0
        abandoned = False
        while len(have) < args.target and calls < args.max_calls_per_skill:
            # Budget guards: bail on a 0-yield skill (verify structurally can't pass
            # it, e.g. a proof/recognition skill) or one that has stopped finding new
            # distinct items, instead of burning the full per-skill call cap.
            if not have and calls >= args.abandon_after:
                abandoned = True
                break
            if calls_since_new >= args.plateau_after:
                abandoned = True
                break
            if stop.is_set() or not reserve_call():
                break
            # Rotate difficulty for surface variety across a skill's 30 items.
            req = dict(skill)
            req["difficulty"] = DIFFICULTIES[calls % len(DIFFICULTIES)]
            calls += 1
            calls_since_new += 1
            try:
                result = serve_live.next_problem(
                    req, generate=generator, attempts=args.attempts, solve_samples=args.samples
                )
            except Exception as exc:  # a real pipeline bug: surface, never fake an item
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
                "tier": skill["tier"],
                "item": item,
                "verifier_report": result.get("verifier_report"),
                "cross_solved": True,
            }
            have.append(rec)
            calls_since_new = 0
            persist(rec)
        confirmed[sid] = have
        with write_lock:
            counters["skills_done"] += 1
            n = counters["skills_done"]
        if stop.is_set() and len(have) < args.target:
            flag = " (STOPPED: global cap)"
        elif abandoned:
            flag = " (abandoned: low yield)"
        else:
            flag = ""
        print(f"  [{n}/{len(skills)}] {sid[:44]:44} -> {len(have)}/{args.target}{flag}", file=sys.stderr)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(work, s) for s in skills]
        for fut in as_completed(futures):
            fut.result()
    items_fh.close()
    elapsed = time.time() - start

    all_items = [rec for recs in confirmed.values() for rec in recs]
    covered = sum(1 for s in skills if confirmed.get(s["skill_id"]))
    at_target = sum(1 for s in skills if len(confirmed.get(s["skill_id"], [])) >= args.target)
    gaps = [
        {
            "skill_id": s["skill_id"],
            "topic_id": s["topic_id"],
            "tier": s["tier"],
            "have": len(confirmed.get(s["skill_id"], [])),
            "target": args.target,
        }
        for s in skills
        if len(confirmed.get(s["skill_id"], [])) < args.target
    ]

    bank = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "build_skill_bank.py (serve_live: generate -> verify -> cross-solve)",
        "tiers": sorted(tiers),
        "target_per_skill": args.target,
        "skills": len(skills),
        "skills_covered": covered,
        "skills_at_target": at_target,
        "item_count": len(all_items),
        "items": all_items,
    }
    Path(args.out).write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.gaps_out).write_text(
        "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in gaps), encoding="utf-8"
    )

    rate = counters["ok"] / counters["calls"] if counters["calls"] else 0.0
    print("=" * 64, file=sys.stderr)
    print(
        f"skill bank: {len(all_items)} item(s); {at_target}/{len(skills)} skill(s) at target, "
        f"{covered}/{len(skills)} with >=1; {len(gaps)} below target "
        f"({sum(1 for g in gaps if g['have'] == 0)} at ZERO); "
        f"{counters['calls']} call(s), {counters['ok']} confirmed (yield {rate:.2f}) in {elapsed:.0f}s",
        file=sys.stderr,
    )
    if stop.is_set():
        print(f"  NOTE: global cap ({args.max_total_calls}) reached; re-run to continue (resumable).", file=sys.stderr)
    print(f"  wrote {args.out}; gaps -> {args.gaps_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
