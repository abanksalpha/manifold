# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""verify_template.py — the swarm's stop condition for one authored template file.

Loads a template JSON (a single object or a list) and runs the DETERMINISTIC gate
:func:`templates.validate`: instantiate 40 variants and require enough clean ones,
5-distinct choices each, no leftover slots, and — crucially — that every shown
answer equals a fresh SymPy computation of the spec (answer-faithfulness). Prints a
report and PASS/FAIL; exits non-zero unless every template passes. A subagent loops
until this prints PASS.

Note: this guarantees the answer matches the SPEC. The author is still responsible
for the stem PROSE matching the spec (reason it through); a batch stem-faithfulness
gate (independent solver) runs at integration.

    manifold/content/generation/.venv/bin/python verify_template.py templates_authored/<skill>.json
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

MIN_OK = 20
# Variety bar: a template must yield many VISIBLY-DIFFERENT problems (number
# replacement really varies the stem), not the same few repeated. 12/40 distinct
# stems is the required FLOOR (aim for >=20); it forces wide-enough parameter ranges
# while staying realistic for the few skills whose clean answer explodes for large n
# (e.g. Cayley n^(n-2), Hamiltonian (n-1)!/2). Widen ranges if a template falls short.
MIN_DISTINCT_STEMS = 12
N = 40


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: verify_template.py <template.json>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot read/parse {path}: {exc}")
        return 1
    tmpls = data if isinstance(data, list) else [data]
    all_ok = True
    for t in tmpls:
        tid = t.get("template_id", "?") if isinstance(t, dict) else "?"
        sid = t.get("skill_id", "?") if isinstance(t, dict) else "?"
        try:
            rep = templates.validate(t, n=N)
        except Exception as exc:
            print(f"FAIL [{sid} / {tid}]: validate raised {type(exc).__name__}: {exc}")
            all_ok = False
            continue
        ok = rep["ok"] >= MIN_OK and rep["distinct_stems"] >= MIN_DISTINCT_STEMS and not rep["errors"]
        print(
            f"{'PASS' if ok else 'FAIL'} [{sid} / {tid}]: "
            f"clean={rep['ok']}/{N} distinct_stems={rep['distinct_stems']} "
            f"distinct_answers={rep['distinct_answers']} errors={rep['errors'][:2]}"
        )
        all_ok = all_ok and ok
    if isinstance(tmpls, list) and len(tmpls) > 1:
        srep = structure.distinct_structures(tmpls)
        print(
            f"STRUCTURE: {srep['count']} templates, {srep['distinct_structures']} distinct shapes"
            + (f" -- DUPLICATE SHAPES (reskins, not real variety): {srep['duplicate_shapes']}"
               if srep["duplicate_shapes"] else "")
        )
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
