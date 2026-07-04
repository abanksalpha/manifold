# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""verify_faithfulness.py — the INTEGRATION stem-faithfulness gate for authored templates.

`verify_template.py` proves the served answer equals a fresh SymPy computation of the
answer-spec (answer-faithfulness). It CANNOT prove the stem PROSE actually describes that
spec: a template whose stem reads "third derivative" but whose spec computes the second is
internally answer-consistent yet wrong for the learner. This gate closes that hole exactly
as the runtime does for live items: it instantiates several variants of each template and
has an INDEPENDENT model (independent_solve.py, default gpt-4o) blind-solve each from only
the rendered stem + choices. If the blind solver lands on the code-computed answer often
enough, the stem faithfully describes the spec; otherwise the template is reported FAILING
and must be fixed or dropped before it is served.

This runs ONCE at integration (never on the serving path — served correctness stays purely
code-computed). It needs OPENAI_API_KEY (or MANIFOLD_SOLVE_FIXTURES for a hermetic double),
mirroring independent_solve.py. It NEVER fabricates a verdict: if the solver cannot run it
fails loud, so a template is never marked faithful without real evidence.

    set -a && source /path/to/.env && set +a
    manifold/content/generation/.venv/bin/python verify_faithfulness.py            # all authored
    manifold/content/generation/.venv/bin/python verify_faithfulness.py FILE...    # specific files
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import independent_solve  # noqa: E402
import templates  # noqa: E402

AUTHORED = SCRIPT_DIR / "templates_authored"
EXCLUDE = {"batches.json"}


def _iter_templates(paths: list[Path]):
    for p in paths:
        if p.name in EXCLUDE or p.name.endswith(".SKIP.json"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for t in data if isinstance(data, list) else [data]:
            yield p.name, t


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", help="template JSON files (default: all in templates_authored/)")
    ap.add_argument("--n", type=int, default=4, help="variants blind-solved per template")
    ap.add_argument("--samples", type=int, default=2, help="blind solves per variant")
    ap.add_argument("--threshold", type=float, default=0.75, help="min agreement fraction to pass")
    args = ap.parse_args(argv)

    # Resolve the solver up front so a missing key fails loud instead of per-template.
    cfg = independent_solve.SolveConfig.from_env()
    solve_fn, reason = independent_solve.select_solver(cfg)
    if solve_fn is None:
        print(f"error: no independent solver available ({reason}); set OPENAI_API_KEY or "
              f"MANIFOLD_SOLVE_FIXTURES", file=sys.stderr)
        return 2

    paths = [Path(f) for f in args.files] if args.files else sorted(AUTHORED.glob("*.json"))
    failures: list[str] = []
    checked = 0
    for name, t in _iter_templates(paths):
        tid = t.get("template_id", "?")
        sid = t.get("skill_id", "?")
        try:
            rep = templates.check_faithfulness(
                t, solve=solve_fn, config=cfg, n=args.n, samples=args.samples,
                threshold=args.threshold,
            )
        except Exception as exc:  # a solver/setup failure must fail loud, never pass
            print(f"ERROR [{sid} / {tid}]: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        checked += 1
        ok = rep["faithful"]
        print(f"{'PASS' if ok else 'FAIL'} [{sid} / {tid}]: "
              f"agreed={rep['agreed']}/{rep['total']} (threshold {rep['threshold']})")
        if not ok:
            failures.append(f"{name}: {sid}/{tid} agreed {rep['agreed']}/{rep['total']}")
            for d in rep["details"]:
                if not d["agreed"]:
                    print(f"    seed {d['seed']}: {d['reason']}")

    print("=" * 60)
    print(f"checked {checked} template(s); {len(failures)} FAILED faithfulness")
    for f in failures:
        print(f"  {f}")
    print("ALL FAITHFUL" if not failures else "SOME UNFAITHFUL")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
