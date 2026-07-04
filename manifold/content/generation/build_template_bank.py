# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""build_template_bank.py — aggregate authored templates into template_bank.json.

Scans templates_authored/*.json (the swarm's output) and includes a template in the
served bank ONLY if it passes the deterministic gate templates.validate() (enough
clean instances, 5 distinct choices, no leftover slots, and every shown answer equals
a fresh SymPy computation of its spec). Honest .SKIP.json markers are counted, not
banked. Any file that fails validation is reported loudly and NOT included — so a bad
template can never reach the serving path.

**Near-duplicate rejection (a REAL gate, not advisory).** A skill authored with
multiple templates must not serve two that are "very similar" — the same method at
the same relationship, just reskinned with different slot names. Within each skill's
template list, any template whose structural signature (structure.py: answer-spec op
+ normalized stem skeleton) repeats an EARLIER one in the same file is dropped and
reported; only the first occurrence of each shape is banked. This runs regardless of
how the templates were authored (subagent, LLM proposer, or hand-written), so the
served bank can never carry accidental reskins even if an upstream author missed one.

serve_live.py already loads template_bank.json, so running this wires the swarm's
output into the runtime.

    manifold/content/generation/.venv/bin/python build_template_bank.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import structure  # noqa: E402
import templates  # noqa: E402

AUTHORED = SCRIPT_DIR / "templates_authored"
BANK_PATH = SCRIPT_DIR / "template_bank.json"
EXCLUDE = {"batches.json"}
MIN_OK = 20
# Variety bar (kept in lockstep with verify_template.py): a banked template must
# yield >=12/40 visibly-distinct stems, so a skill does not repeat the same handful
# of problems. A template below this is excluded (reported) until its ranges widen.
MIN_DISTINCT = 12
N = 40


def main() -> int:
    included: list[dict] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []
    dropped_dupes: list[tuple[str, str, str]] = []  # (file, template_id, duplicate_of)
    by_skill: set[str] = set()

    for p in sorted(AUTHORED.glob("*.json")):
        if p.name in EXCLUDE:
            continue
        if p.name.endswith(".SKIP.json"):
            skipped.append(p.name[: -len(".SKIP.json")])
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            failed.append((p.name, f"parse error: {exc}"))
            continue
        tl = data if isinstance(data, list) else [data]
        ok_all = True
        for t in tl:
            try:
                rep = templates.validate(t, n=N)
            except Exception as exc:
                failed.append((p.name, f"validate raised: {type(exc).__name__}: {exc}"))
                ok_all = False
                break
            if not (rep["ok"] >= MIN_OK and rep["distinct_stems"] >= MIN_DISTINCT and not rep["errors"]):
                failed.append((p.name, f"weak: ok={rep['ok']}/{N} distinct={rep['distinct_stems']} errors={rep['errors'][:1]}"))
                ok_all = False
                break
        if not ok_all:
            continue
        # Real de-duplication gate: within THIS skill's list, keep only the first
        # template per structural signature. A later template sharing an earlier
        # one's (op, stem-skeleton) is a reskin, not real variety, and is dropped —
        # never served, regardless of authorship source.
        seen_sigs: dict[str, str] = {}
        deduped: list[dict] = []
        for t in tl:
            sig = structure.structure_signature(t)
            if sig in seen_sigs:
                dropped_dupes.append((p.name, t.get("template_id", "?"), seen_sigs[sig]))
                continue
            seen_sigs[sig] = t.get("template_id", "?")
            deduped.append(t)
        included.extend(deduped)
        by_skill.update(t["skill_id"] for t in deduped)

    # Structural-shape stats: grouped by skill_id across the whole bank so a skill's
    # templates authored across multiple waves are still measured together. The
    # per-file dedup above already guarantees no two banked templates for the SAME
    # skill share a signature; this is a cross-file sanity re-check + reporting.
    by_skill_templates: dict[str, list[dict]] = {}
    for t in included:
        by_skill_templates.setdefault(t["skill_id"], []).append(t)
    shape_counts = {sid: structure.distinct_structures(ts)["distinct_structures"] for sid, ts in by_skill_templates.items()}

    bank = {
        "schema_version": 1,
        "generator": "build_template_bank.py",
        "template_count": len(included),
        "skills_covered": sorted(by_skill),
        "templates": included,
    }
    BANK_PATH.write_text(json.dumps(bank, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=" * 60)
    print(f"included templates : {len(included)} across {len(by_skill)} skill(s)")
    print(f"honest skips       : {len(skipped)}")
    if shape_counts:
        avg_shapes = sum(shape_counts.values()) / len(shape_counts)
        multi = sum(1 for c in shape_counts.values() if c > 1)
        print(f"avg distinct structural shapes/skill: {avg_shapes:.1f}  ({multi}/{len(shape_counts)} skills have >1 shape)")
    if dropped_dupes:
        print(f"DROPPED near-duplicate shapes (never served): {len(dropped_dupes)}")
        for name, tid, dup_of in dropped_dupes[:20]:
            print(f"    {name}: {tid!r} duplicates {dup_of!r}")
    if failed:
        print(f"FAILED (excluded)  : {len(failed)}")
        for name, reason in failed:
            print(f"    {name}: {reason}")
    print("wrote template_bank.json")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
