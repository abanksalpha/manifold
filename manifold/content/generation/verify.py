# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Deterministic correctness gate for Manifold's content pipeline (WS1, D28, D32).

**No LLM is in this path.** Generated content is never trusted, only verified: an
item is banked only if this module proves exactly one of its five choices is
correct *and* that it is the choice the item claims. Correctness is recomputed
independently of the generator via **SymPy (symbolic) AND mpmath/NumPy (numeric)**,
and the two must agree — a disagreement means a CAS bug we don't trust, so the item
is rejected. If SymPy cannot decide or evaluate, the item is **rejected with reason
``undecidable`` — never assumed correct** (cross-cutting rule; D32).

Three gates, in order:

1. **structural** — exactly five distinct non-empty choices, ``correct_index`` in
   range, non-empty ``stem``/``solution``, ``source_ref`` present.
2. **ground_truth** — recompute the answer independently (symbolic ∧ numeric,
   agreement required) and evaluate the ``check`` against **all five** choices.
   Antiderivatives are checked by differentiating each choice back to the integrand
   (so ``+C`` never matters). Discrete counts are checked by exact brute force.
   ``check.type == "smt"`` is delegated to :mod:`smt_check` (Z3).
3. **single_answer** — exactly one choice is correct, and it equals ``correct_index``.

Public API: :func:`verify` returns ``(verified: bool, report: dict)``.

Supported ``check.type`` values: ``equiv``, ``numeric``, ``antiderivative``,
``eigen``, ``det``, ``rank``, ``count``, ``prob_exact``, ``smt``.

Interpreter (deps: sympy, mpmath, numpy, z3-solver):
``manifold/content/generation/.venv/bin/python`` — created with::

    out/pyenv/bin/python -m venv manifold/content/generation/.venv
    manifold/content/generation/.venv/bin/python -m pip install \
        sympy mpmath numpy z3-solver pytest

(the .venv is gitignored). Run the tests with::

    manifold/content/generation/.venv/bin/python -m pytest \
        manifold/content/generation/test_verify.py -q
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
from typing import Any, Callable

import numpy as np
import sympy as sp

import smt_check

# --- tolerances & sampling (any randomness is seeded + documented; D28) ---------
NUM_TOL = 1e-9  # |value| below this counts as numerically zero
NONZERO_THRESHOLD = 1e-6  # |value| above this counts as numerically nonzero
EIGEN_TOL = 1e-7  # spectra match within this (clean small GRE matrices)
NUM_SAMPLES = 20  # random probe points per numeric equivalence test
MIN_VALID_SAMPLES = 5  # fewer usable probes than this => undecidable
SAMPLE_SEED = 1729  # fixed so verification is reproducible
SAMPLE_LO, SAMPLE_HI = 0.2, 1.8  # probe interval (positive: safe for sqrt/log)
MAX_BRUTE = 2_000_000  # brute-force domain cap; larger raises (never silently skips)

SUPPORTED_TYPES = (
    "equiv",
    "numeric",
    "antiderivative",
    "eigen",
    "det",
    "rank",
    "count",
    "prob_exact",
    "smt",
)


class Undecidable(Exception):
    """SymPy/Z3 could not decide or evaluate. Reject + log; never assume correct."""


# --- parsing helpers ------------------------------------------------------------


def _sympify(value: Any) -> sp.Expr:
    """Parse a choice/expression string into a SymPy expression, or fail loudly."""
    text = value if isinstance(value, str) else str(value)
    try:
        return sp.sympify(text, convert_xor=True)
    except (sp.SympifyError, SyntaxError, TypeError, AttributeError) as exc:
        raise Undecidable(f"could not parse {text!r}: {exc}") from exc


def _to_complex(expr: sp.Expr) -> complex:
    return complex(sp.N(expr, 30))


def _require_number(expr: sp.Expr, what: str) -> sp.Expr:
    if expr.free_symbols:
        raise Undecidable(f"{what} is not a closed number: {expr!r}")
    return expr


def _parse_number(text: Any) -> sp.Expr:
    return _require_number(_sympify(text), "choice")


def _parse_int(text: Any) -> int:
    expr = _require_number(_sympify(text), "choice")
    if expr.is_integer:
        return int(expr)
    value = _to_complex(expr)
    if abs(value.imag) < NUM_TOL and abs(value.real - round(value.real)) < NUM_TOL:
        return int(round(value.real))
    raise Undecidable(f"choice {text!r} is not an integer")


def _parse_value_list(text: Any) -> list[complex]:
    """Parse a choice like ``"1, 3"`` / ``"{1, 3}"`` / ``"2 and 2"`` into numbers."""
    raw = (text if isinstance(text, str) else str(text)).strip()
    for opener, closer in (("{", "}"), ("[", "]"), ("(", ")")):
        if raw.startswith(opener) and raw.endswith(closer):
            raw = raw[1:-1]
            break
    raw = raw.replace(" and ", ",")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise Undecidable(f"choice {text!r} lists no values")
    return [_to_complex(_require_number(_sympify(p), "choice value")) for p in parts]


def _matrix_sym(raw: Any, *, square: bool) -> sp.Matrix:
    if not isinstance(raw, list) or not raw or not all(isinstance(r, list) and r for r in raw):
        raise ValueError(f"matrix must be a non-empty list of non-empty rows: {raw!r}")
    width = len(raw[0])
    if any(len(row) != width for row in raw):
        raise ValueError("matrix rows have unequal length")
    if square and len(raw) != width:
        raise ValueError(f"matrix must be square, got {len(raw)}x{width}")
    rows = []
    for row in raw:
        parsed = []
        for entry in row:
            value = _sympify(entry)
            if value.free_symbols:
                raise Undecidable(f"matrix entry {entry!r} is symbolic; no numeric cross-check")
            parsed.append(value)
        rows.append(parsed)
    return sp.Matrix(rows)


def _matrix_np(raw: Any) -> np.ndarray:
    return np.array(
        [[_to_complex(_sympify(entry)) for entry in row] for row in raw],
        dtype=complex,
    )


# --- numeric / symbolic agreement primitives ------------------------------------


def _symbolically_zero(expr: sp.Expr) -> bool:
    """True iff SymPy can simplify ``expr`` to zero. A non-simplification is treated
    as a *claim of nonzero* — the numeric probe then confirms or contradicts it."""
    simplified = sp.simplify(expr)
    return simplified.is_zero is True or simplified == 0


def _numerically_zero(expr: sp.Expr) -> bool | None:
    """True/False if random probes clearly agree; None if inconclusive/unevaluable."""
    free = sorted(expr.free_symbols, key=lambda s: s.name)
    if not free:
        try:
            value = _to_complex(expr)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(value.real) and math.isfinite(value.imag)):
            return None
        magnitude = abs(value)
        if magnitude <= NUM_TOL:
            return True
        if magnitude >= NONZERO_THRESHOLD:
            return False
        return None

    try:
        func = sp.lambdify(free, expr, modules=["mpmath"])
    except Exception:
        return None
    rng = random.Random(SAMPLE_SEED)
    magnitudes: list[float] = []
    for _ in range(NUM_SAMPLES):
        point = [rng.uniform(SAMPLE_LO, SAMPLE_HI) for _ in free]
        try:
            value = complex(func(*point))
        except Exception:
            continue
        if not (math.isfinite(value.real) and math.isfinite(value.imag)):
            continue
        magnitudes.append(abs(value))
    if len(magnitudes) < MIN_VALID_SAMPLES:
        return None
    peak = max(magnitudes)
    if peak <= NUM_TOL:
        return True
    if peak >= NONZERO_THRESHOLD:
        return False
    return None


def _equivalent(a: sp.Expr, b: sp.Expr) -> bool:
    """Decide a ≡ b requiring symbolic and numeric agreement, else Undecidable."""
    difference = sp.expand(a - b)
    symbolic = _symbolically_zero(difference)
    numeric = _numerically_zero(difference)
    if numeric is None:
        raise Undecidable(f"numeric probe inconclusive for {a!r} vs {b!r}")
    if symbolic != numeric:
        raise Undecidable(
            f"symbolic({symbolic}) and numeric({numeric}) disagree for {a!r} vs {b!r}"
        )
    return symbolic


def _numbers_equal(candidate: sp.Expr, truth: sp.Expr) -> bool:
    """Decide two numbers equal via symbolic ∧ numeric agreement, else Undecidable."""
    symbolic = _symbolically_zero(candidate - truth)
    ca, ct = _to_complex(candidate), _to_complex(truth)
    numeric = abs(ca - ct) <= NUM_TOL * (1 + abs(ct))
    if symbolic != numeric:
        raise Undecidable(
            f"symbolic({symbolic}) and numeric({numeric}) disagree: {candidate!r} vs {truth!r}"
        )
    return symbolic


def _multiset_close(a: list[complex], b: list[complex], tol: float) -> bool:
    """Greedy multiset equality within tolerance (order-independent, with mult.)."""
    if len(a) != len(b):
        return False
    remaining = list(b)
    for value in a:
        match = next((i for i, other in enumerate(remaining) if abs(value - other) <= tol), None)
        if match is None:
            return False
        remaining.pop(match)
    return not remaining


# --- check-type handlers: (check, choices) -> (correct_indices, detail) ----------
# Each recomputes ground truth independently and evaluates ALL five choices.
# Each raises Undecidable when SymPy/numeric cannot decide (never assume correct).


def _check_equiv(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    reference = _sympify(check["expr"])
    correct, per_choice = set(), []
    for i, choice in enumerate(choices):
        is_equal = _equivalent(_sympify(choice), reference)
        per_choice.append({"choice": i, "equivalent": is_equal})
        if is_equal:
            correct.add(i)
    return correct, {"reference": str(reference), "per_choice": per_choice}


def _check_antiderivative(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    var = sp.Symbol(str(check.get("var", "x")))
    integrand = _sympify(check["integrand"])
    correct, per_choice = set(), []
    for i, choice in enumerate(choices):
        derivative = sp.diff(_sympify(choice), var)
        is_equal = _equivalent(derivative, integrand)
        per_choice.append({"choice": i, "derivative_matches": is_equal})
        if is_equal:
            correct.add(i)
    return correct, {"integrand": str(integrand), "variable": str(var), "per_choice": per_choice}


def _ground_truth_number(expr_text: str) -> tuple[sp.Expr, complex]:
    """Recompute a closed-form number three ways and require agreement."""
    expr = _require_number(_sympify(expr_text), "check expression")
    simplified = sp.simplify(expr)
    raw_value = _to_complex(expr)  # numeric value of the original form
    simplified_value = _to_complex(simplified)  # numeric value after symbolic transform
    try:
        mpmath_value = complex(sp.lambdify([], expr, modules=["mpmath"])())
    except Exception as exc:
        raise Undecidable(f"mpmath could not evaluate {expr_text!r}: {exc}") from exc
    scale = 1 + abs(raw_value)
    if abs(raw_value - simplified_value) > NUM_TOL * scale:
        raise Undecidable(f"symbolic simplification changed the value of {expr_text!r}")
    if abs(raw_value - mpmath_value) > NUM_TOL * scale:
        raise Undecidable(f"mpmath and SymPy disagree on {expr_text!r}")
    return simplified, raw_value


def _check_numeric(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    truth, _ = _ground_truth_number(check["expr"])
    correct, per_choice = set(), []
    for i, choice in enumerate(choices):
        is_equal = _numbers_equal(_parse_number(choice), truth)
        per_choice.append({"choice": i, "equals_truth": is_equal})
        if is_equal:
            correct.add(i)
    return correct, {"value": str(truth), "per_choice": per_choice}


def _check_det(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    matrix = _matrix_sym(check["matrix"], square=True)
    truth = sp.simplify(matrix.det())
    numpy_det = np.linalg.det(_matrix_np(check["matrix"]))
    if abs(_to_complex(truth) - complex(numpy_det)) > EIGEN_TOL * (1 + abs(complex(numpy_det))):
        raise Undecidable(f"SymPy det {truth} and NumPy det {numpy_det} disagree")
    correct = {i for i, choice in enumerate(choices) if _numbers_equal(_parse_number(choice), truth)}
    return correct, {"determinant": str(truth)}


def _check_rank(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    matrix = _matrix_sym(check["matrix"], square=False)
    truth = int(matrix.rank())
    numpy_rank = int(np.linalg.matrix_rank(_matrix_np(check["matrix"])))
    if truth != numpy_rank:
        raise Undecidable(f"SymPy rank {truth} and NumPy rank {numpy_rank} disagree")
    correct = {i for i, choice in enumerate(choices) if _parse_int(choice) == truth}
    return correct, {"rank": truth}


def _check_eigen(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    matrix = _matrix_sym(check["matrix"], square=True)
    spectrum: list[complex] = []
    for value, multiplicity in matrix.eigenvals().items():
        spectrum.extend([_to_complex(value)] * int(multiplicity))
    numpy_spectrum = list(np.linalg.eigvals(_matrix_np(check["matrix"])))
    if not _multiset_close(spectrum, numpy_spectrum, EIGEN_TOL):
        raise Undecidable(f"SymPy spectrum {spectrum} and NumPy spectrum {numpy_spectrum} disagree")
    correct = set()
    for i, choice in enumerate(choices):
        if _multiset_close(_parse_value_list(choice), spectrum, EIGEN_TOL):
            correct.add(i)
    return correct, {"eigenvalues": [str(v) for v in matrix.eigenvals()]}


def _brute_count(spec: dict) -> int:
    """Exact enumeration count over an integer grid (discrete: number theory/combi)."""
    var_ranges = spec.get("vars")
    predicate_text = spec.get("predicate")
    if not isinstance(var_ranges, dict) or not var_ranges or not predicate_text:
        raise ValueError(f"brute spec needs 'vars' and 'predicate': {spec!r}")
    names = list(var_ranges)
    symbols = [sp.Symbol(n) for n in names]
    ranges = []
    for name in names:
        bounds = var_ranges[name]
        if not (isinstance(bounds, list) and len(bounds) == 2):
            raise ValueError(f"range for {name!r} must be [lo, hi], got {bounds!r}")
        lo, hi = int(bounds[0]), int(bounds[1])
        ranges.append(range(lo, hi + 1))
    size = math.prod(len(r) for r in ranges)
    if size > MAX_BRUTE:
        raise ValueError(f"brute-force domain too large ({size} > {MAX_BRUTE})")
    predicate = _sympify(predicate_text)
    if not isinstance(predicate, sp.Basic):  # e.g. "True"/"False" parse to Python bool
        predicate = sp.true if bool(predicate) else sp.false
    count = 0
    for combo in itertools.product(*ranges):
        result = predicate.subs(dict(zip(symbols, combo)))
        if result in (sp.true, True):
            count += 1
        elif result in (sp.false, False):
            continue
        else:
            simplified = sp.simplify(result)
            if simplified in (sp.true, True):
                count += 1
            elif simplified not in (sp.false, False):
                raise Undecidable(f"predicate did not reduce to a boolean at {combo}")
    return count


def _check_count(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    values: list[int] = []
    detail: dict[str, Any] = {}
    if "expr" in check:
        expr = _require_number(_sympify(check["expr"]), "count expression")
        simplified = sp.simplify(expr)
        if simplified.is_integer is not True:
            raise Undecidable(f"count expression {check['expr']!r} is not an integer")
        closed_form = int(simplified)
        mpmath_value = complex(sp.lambdify([], expr, modules=["mpmath"])())
        if abs(mpmath_value.imag) > NUM_TOL or abs(mpmath_value.real - closed_form) > NONZERO_THRESHOLD:
            raise Undecidable(f"closed form and numeric value disagree for {check['expr']!r}")
        values.append(closed_form)
        detail["closed_form"] = closed_form
    if "brute" in check:
        brute = _brute_count(check["brute"])
        values.append(brute)
        detail["brute_force"] = brute
    if not values:
        raise ValueError("count check needs 'expr' and/or 'brute'")
    if len(set(values)) != 1:
        raise Undecidable(f"count methods disagree: {values}")
    truth = values[0]
    correct = {i for i, choice in enumerate(choices) if _parse_int(choice) == truth}
    detail["count"] = truth
    return correct, detail


def _check_prob_exact(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    values: list[sp.Expr] = []
    detail: dict[str, Any] = {}
    if "expr" in check:
        expr = _require_number(_sympify(check["expr"]), "probability expression")
        values.append(sp.nsimplify(expr, rational=True))
        detail["closed_form"] = str(values[-1])
    if "brute" in check:
        spec = check["brute"]
        total_spec = {"vars": spec["vars"], "predicate": "True"}
        favorable = _brute_count({"vars": spec["vars"], "predicate": spec["event"]})
        total = _brute_count(total_spec)
        if total == 0:
            raise ValueError("probability brute-force sample space is empty")
        values.append(sp.Rational(favorable, total))
        detail["brute_force"] = f"{favorable}/{total}"
    if not values:
        raise ValueError("prob_exact check needs 'expr' and/or 'brute'")
    if any(not _numbers_equal(v, values[0]) for v in values[1:]):
        raise Undecidable(f"probability methods disagree: {[str(v) for v in values]}")
    truth = values[0]
    if not (0 <= truth <= 1):
        raise Undecidable(f"probability {truth} is outside [0, 1]")
    correct = {i for i, choice in enumerate(choices) if _numbers_equal(_parse_number(choice), truth)}
    detail["probability"] = str(truth)
    return correct, detail


_HANDLERS: dict[str, Callable[[dict, list[str]], tuple[set[int], dict]]] = {
    "equiv": _check_equiv,
    "numeric": _check_numeric,
    "antiderivative": _check_antiderivative,
    "eigen": _check_eigen,
    "det": _check_det,
    "rank": _check_rank,
    "count": _check_count,
    "prob_exact": _check_prob_exact,
}


def _correct_choices(check: dict, choices: list[str]) -> tuple[set[int], dict]:
    check_type = check.get("type")
    if check_type == "smt":
        try:
            return smt_check.correct_choices(check, choices)
        except smt_check.SmtUndecidable as exc:
            raise Undecidable(f"smt: {exc}") from exc
    handler = _HANDLERS.get(check_type)
    if handler is None:
        raise ValueError(f"unsupported check.type {check_type!r}; supported: {SUPPORTED_TYPES}")
    return handler(check, choices)


# --- Gate 1: structural ---------------------------------------------------------


def _structural(item: dict) -> tuple[bool, str]:
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != 5:
        got = len(choices) if isinstance(choices, list) else type(choices).__name__
        return False, f"expected exactly 5 choices, got {got}"
    cleaned = []
    for i, choice in enumerate(choices):
        if not isinstance(choice, str) or not choice.strip():
            return False, f"choice {i} is empty or not a string"
        cleaned.append(choice.strip())
    if len(set(cleaned)) != len(cleaned):
        return False, "choices are not all distinct"
    correct_index = item.get("correct_index")
    if not isinstance(correct_index, int) or isinstance(correct_index, bool):
        return False, f"correct_index must be an int, got {correct_index!r}"
    if not 0 <= correct_index < 5:
        return False, f"correct_index {correct_index} out of range [0, 5)"
    for field in ("stem", "solution", "source_ref"):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            return False, f"{field} is missing or empty"
    return True, "5 distinct choices, index in range, stem/solution/source_ref present"


# --- public API -----------------------------------------------------------------


def verify(item: dict) -> tuple[bool, dict]:
    """Verify one ``Item``. Returns ``(verified, verifier_report)``.

    ``verified`` is True only if all three gates pass. The report always carries a
    per-gate pass/fail with a reason and a top-level ``reason`` code (one of ``ok``,
    ``structural``, ``undecidable``, ``no_correct``, ``multiple_correct``,
    ``wrong_answer``). Unsupported ``check.type`` / malformed check blocks raise
    (loud pipeline bug), rather than silently rejecting.
    """
    report: dict[str, Any] = {
        "verified": False,
        "reason": None,
        "check_type": (item.get("check") or {}).get("type"),
        "source_ref": item.get("source_ref"),
        "claimed_correct_index": None,
        "correct_choices": None,
        "gates": {
            "structural": {"passed": False, "reason": None},
            "ground_truth": {"passed": False, "reason": None, "detail": None},
            "single_answer": {"passed": False, "reason": None},
        },
    }

    # Gate 1: structural.
    ok, reason = _structural(item)
    report["gates"]["structural"] = {"passed": ok, "reason": reason}
    if not ok:
        report["reason"] = "structural"
        return False, report
    report["claimed_correct_index"] = item["correct_index"]

    check = item.get("check")
    if not isinstance(check, dict) or not check.get("type"):
        raise ValueError("item is missing a 'check' block with a 'type'")

    # Gate 2: independent ground-truth recompute (symbolic ∧ numeric) over all 5.
    try:
        correct, detail = _correct_choices(check, item["choices"])
    except Undecidable as exc:
        report["gates"]["ground_truth"] = {"passed": False, "reason": str(exc), "detail": None}
        report["reason"] = "undecidable"
        return False, report
    report["gates"]["ground_truth"] = {
        "passed": True,
        "reason": "recomputed independently; symbolic and numeric agree",
        "detail": detail,
    }
    report["correct_choices"] = sorted(correct)

    # Gate 3: single-answer.
    correct_index = item["correct_index"]
    if len(correct) == 0:
        report["gates"]["single_answer"] = {
            "passed": False,
            "reason": "no choice matches the recomputed answer",
        }
        report["reason"] = "no_correct"
        return False, report
    if len(correct) > 1:
        report["gates"]["single_answer"] = {
            "passed": False,
            "reason": f"{len(correct)} choices are correct: {sorted(correct)}",
        }
        report["reason"] = "multiple_correct"
        return False, report
    only = next(iter(correct))
    if only != correct_index:
        report["gates"]["single_answer"] = {
            "passed": False,
            "reason": f"correct choice is index {only}, item claims {correct_index}",
        }
        report["reason"] = "wrong_answer"
        return False, report

    report["gates"]["single_answer"] = {
        "passed": True,
        "reason": "exactly one choice is correct and it matches correct_index",
    }
    report["verified"] = True
    report["reason"] = "ok"
    return True, report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: verify.py <item.json>")
    with open(argv[1], encoding="utf-8") as handle:
        item = json.load(handle)
    verified, report = verify(item)
    print(json.dumps(report, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
