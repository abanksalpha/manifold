# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""structure_report.py — report structural (problem-SHAPE) variety per skill.

Advisory only (see structure.py header): never gates banking. Run on one skill file
while authoring to sanity-check you haven't accidentally reskinned the same shape
twice, or run with no args for a repo-wide summary.

    .venv/bin/python structure_report.py                                    # all skills
    .venv/bin/python structure_report.py templates_authored/<skill_id>.json # one skill
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import structure  # noqa: E402

AUTHORED = SCRIPT_DIR / "templates_authored"
EXCLUDE = {"batches.json"}


def _load(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main(argv: list[str]) -> int:
    paths = (
        [Path(a) for a in argv]
        if argv
        else sorted(
            p
            for p in AUTHORED.glob("*.json")
            if p.name not in EXCLUDE and not p.name.endswith(".SKIP.json")
        )
    )
    total_tmpl = 0
    total_skills = 0
    dist_counts: list[int] = []
    low: list[tuple[str, int]] = []
    for p in paths:
        try:
            tl = _load(p)
        except Exception as exc:
            print(f"{p.name}: unreadable: {exc}")
            continue
        rep = structure.distinct_structures(tl)
        total_tmpl += rep["count"]
        total_skills += 1
        dist_counts.append(rep["distinct_structures"])
        if rep["duplicate_shapes"]:
            print(
                f"{p.stem}: {rep['count']} templates, {rep['distinct_structures']} distinct shapes "
                f"-- DUPLICATE SHAPES: {rep['duplicate_shapes']}"
            )
        if len(paths) == 1:
            print(json.dumps(rep, indent=1))
        if rep["distinct_structures"] < 3:
            low.append((p.stem, rep["distinct_structures"]))

    if len(paths) != 1:
        print("=" * 60)
        print(
            f"skills: {total_skills}  templates: {total_tmpl}  "
            f"avg templates/skill: {total_tmpl / max(1, total_skills):.1f}"
        )
        if dist_counts:
            print(
                f"avg distinct shapes/skill: {sum(dist_counts) / len(dist_counts):.1f}  "
                f"min: {min(dist_counts)}  max: {max(dist_counts)}"
            )
        print(f"skills with < 3 distinct shapes: {len(low)}")
        for sid, c in sorted(low, key=lambda x: x[1])[:30]:
            print(f"    {sid}: {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
