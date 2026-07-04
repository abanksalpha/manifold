# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""audit_templates.py — coverage + rendered-instance audit for authored templates.

Cross-references templates_authored/ against seed_deck.json and reports, per topic:
how many skills have a validated template, an honest SKIP, or nothing yet. With
``--dump`` it renders one instance per template (skill_id, op, code-computed answer,
stem) so a human can DETERMINISTICALLY eyeball that the stem prose matches the answer
(the one check the deterministic gate cannot make). It re-runs templates.validate() on
every file and flags any that would NOT bank, and any filename/skill_id mismatch.

    .venv/bin/python audit_templates.py                 # coverage summary
    .venv/bin/python audit_templates.py --dump          # + one rendered instance each
    .venv/bin/python audit_templates.py --dump --topic trigonometry
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import solver  # noqa: E402
import templates  # noqa: E402

AUTHORED = SCRIPT_DIR / "templates_authored"
DECK = SCRIPT_DIR.parent / "seed_deck.json"
EXCLUDE = {"batches.json"}
MIN_OK = 20
MIN_DISTINCT = 5
N = 40


def _load_authored() -> tuple[dict[str, list[dict]], set[str], list[str]]:
    """Return (skill_id -> [templates], skipped_skill_ids, problems)."""
    templated: dict[str, list[dict]] = defaultdict(list)
    skipped: set[str] = set()
    problems: list[str] = []
    for p in sorted(AUTHORED.glob("*.json")):
        if p.name in EXCLUDE:
            continue
        if p.name.endswith(".SKIP.json"):
            skipped.add(p.name[: -len(".SKIP.json")])
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{p.name}: unreadable JSON: {exc}")
            continue
        for t in data if isinstance(data, list) else [data]:
            sid = t.get("skill_id")
            if not sid:
                problems.append(f"{p.name}: template missing skill_id")
                continue
            if p.stem != sid and not isinstance(data, list):
                problems.append(f"{p.name}: filename != skill_id ({sid!r})")
            templated[sid].append(t)
    return templated, skipped, problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", action="store_true", help="render one instance per template")
    ap.add_argument("--topic", default=None, help="limit to one topic_id")
    ap.add_argument("--tier", default=None, help="limit to one tier")
    args = ap.parse_args(argv)

    deck = json.loads(DECK.read_text(encoding="utf-8"))
    skills = deck["skills"]
    templated, skipped, problems = _load_authored()

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for s in skills:
        by_topic[s["topic_id"]].append(s)

    tot_templated = tot_skipped = tot_missing = tot_failval = 0
    print(f"{'topic':38} {'tier':10} {'skills':>6} {'tmpl':>5} {'skip':>5} {'miss':>5} {'FAIL':>5}")
    print("-" * 86)
    for topic in sorted(by_topic):
        rows = by_topic[topic]
        tier = rows[0]["tier"]
        if args.tier and tier != args.tier:
            continue
        if args.topic and topic != args.topic:
            continue
        n_t = n_s = n_m = n_f = 0
        for s in rows:
            sid = s["skill_id"]
            if sid in templated:
                n_t += 1
                for t in templated[sid]:
                    try:
                        rep = templates.validate(t, n=N)
                        ok = rep["ok"] >= MIN_OK and rep["distinct_stems"] >= MIN_DISTINCT and not rep["errors"]
                    except Exception as exc:
                        ok = False
                        problems.append(f"{sid}: validate raised {type(exc).__name__}: {exc}")
                    if not ok:
                        n_f += 1
                        problems.append(f"{sid}: WOULD NOT BANK (validate weak/failed)")
            elif sid in skipped:
                n_s += 1
            else:
                n_m += 1
        tot_templated += n_t
        tot_skipped += n_s
        tot_missing += n_m
        tot_failval += n_f
        print(f"{topic:38} {tier:10} {len(rows):>6} {n_t:>5} {n_s:>5} {n_m:>5} {n_f:>5}")

    print("-" * 86)
    print(f"{'TOTAL':38} {'':10} {len(skills):>6} {tot_templated:>5} {tot_skipped:>5} {tot_missing:>5} {tot_failval:>5}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  {p}")

    if args.dump:
        print("\n" + "=" * 86 + "\nRENDERED INSTANCES (verify stem matches the code answer):")
        by_id = {s["skill_id"]: s for s in skills}
        for sid in sorted(templated):
            s = by_id.get(sid, {})
            if args.topic and s.get("topic_id") != args.topic:
                continue
            if args.tier and s.get("tier") != args.tier:
                continue
            for t in templated[sid]:
                try:
                    item = templates.instantiate(t, 3)
                    ans = item["choices"][item["correct_index"]]
                    op = t.get("answer_spec", {}).get("op", "?")
                    print(f"\n[{s.get('topic_id','?')}] {sid}  (op={op})  ANSWER={ans}")
                    print(f"  STEM: {item['stem']}")
                    print(f"  CHOICES: {item['choices']}")
                except Exception as exc:
                    print(f"\n[{s.get('topic_id','?')}] {sid}: INSTANTIATE FAILED: {type(exc).__name__}: {exc}")

    return 1 if (problems or tot_failval) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
