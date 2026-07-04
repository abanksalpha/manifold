# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""solver.py — the deterministic answer engine ("compile to get the answer").

Correctness comes from CODE, never from an LLM. A problem is described by a
machine-solvable *op-spec*; this module computes the TRUE answer with SymPy and
NEVER trusts a claimed value. This closes the hole that let LLM-asserted answers
(confirmed by a correlated LLM cross-solver) into the bank: e.g. f(x)=2x-1 from
x0=1 gives x3=1 (not the "5" a model asserted), and f(f(x))=5 gives x=2 (not "3").

Fail loud (standing rule): an undecidable, non-real, or non-finite result raises
:class:`SolveError`; the caller rejects the item. It never guesses.

Op-specs (all string exprs are plain SymPy: ** for powers, sqrt, log, exp, sin,
pi, Rational, factorial, binomial):

  {"op":"evaluate","expr":"3**2 + 2*4/2 - sqrt(16)"}              -> a number
  {"op":"solve","equation":"log(x+3,2)-log(x,2)=1","var":"x"}     -> {solutions:[...]}
  {"op":"iterate","f":"2*x - 1","x0":1,"n":3,"var":"x"}           -> value after n applications
  {"op":"diff","expr":"x**3","var":"x","at":2,"order":1}          -> derivative (optionally at a point)
  {"op":"integrate","expr":"2*x","var":"x","bounds":[0,3]}        -> definite (or antiderivative if no bounds)
  {"op":"limit","expr":"sin(x)/x","var":"x","point":0}            -> limit
  {"op":"vieta","poly":"x**3-6*x**2+11*x-6","var":"x","which":"sum"}  -> sum|prod|sum_pairs of roots
  {"op":"det","matrix":[["[[a]]","[[b]]"],["[[c]]","[[d]]"]]}          -> determinant (square)
  {"op":"trace","matrix":[["[[a]]","[[b]]"],["[[c]]","[[d]]"]]}        -> trace (square)
  {"op":"rank","matrix":[["[[a]]","[[b]]"],["[[c]]","[[d]]"]]}         -> integer rank
  {"op":"eig","matrix":[[...]],"which":"max"}                          -> max|min|sum|prod eigenvalue
  {"op":"dblintegrate","expr":"x*y","vars":["x","y"],"bounds":[["0","[[b]]"],["0","2"]]}
                                                                       -> iterated (double/triple) integral

Matrix entries are plain SymPy expression strings; the template engine substitutes
[[slots]] inside the nested rows before this runs. Eigenvalue ops fail loud on a
matrix with non-closed-form eigenvalues, and max/min fail loud unless every
eigenvalue is real (so an item can only serve an unambiguous scalar answer).

Interpreter: the generation venv (sympy). See verify.py header.
"""

from __future__ import annotations

from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TX = standard_transformations + (implicit_multiplication_application, convert_xor)

# The only names an op-spec expression may reference besides its variables and
# numeric literals. No Python builtins are exposed to the parser.
_ALLOWED: dict[str, Any] = {
    "sqrt": sp.sqrt, "log": sp.log, "ln": sp.log, "exp": sp.exp,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot,
    "sec": sp.sec, "csc": sp.csc, "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "pi": sp.pi, "E": sp.E, "I": sp.I, "oo": sp.oo,
    "Abs": sp.Abs, "factorial": sp.factorial, "binomial": sp.binomial,
    "Rational": sp.Rational, "floor": sp.floor, "ceiling": sp.ceiling,
    "root": sp.root, "gcd": sp.gcd, "Mod": sp.Mod,
    # Relationals so template CONSTRAINT strings (e.g. "Ne(r1,r2)", "a > 0") parse.
    "Eq": sp.Eq, "Ne": sp.Ne, "Gt": sp.Gt, "Lt": sp.Lt, "Ge": sp.Ge, "Le": sp.Le,
}


class SolveError(Exception):
    """The spec is malformed or its answer cannot be computed cleanly. Fail loud."""


class SolveUndecidable(SolveError):
    """SymPy could not decide / the answer is not a clean closed form."""


def _parse(text: Any, extra: dict[str, Any] | None = None) -> sp.Expr:
    if not isinstance(text, str) or not text.strip():
        raise SolveError(f"expected a non-empty expression string, got {text!r}")
    local = dict(_ALLOWED)
    if extra:
        local.update(extra)
    try:
        return parse_expr(text, local_dict=local, transformations=_TX, evaluate=True)
    except Exception as exc:  # a spec expression that won't parse is a bug, not a bad item
        raise SolveError(f"could not parse {text!r}: {exc}") from exc


def _sym(name: Any) -> sp.Symbol:
    if not isinstance(name, str) or not name.isidentifier():
        raise SolveError(f"invalid variable name {name!r}")
    return sp.Symbol(name)


def _require_number(value: sp.Expr, context: str) -> sp.Expr:
    """Collapse to an exact number or raise (never return a symbolic/undecidable)."""
    try:
        simplified = sp.simplify(value)
    except Exception as exc:
        raise SolveUndecidable(f"{context}: simplify failed: {exc}") from exc
    if simplified.free_symbols:
        raise SolveError(f"{context}: result {simplified} still has free symbols")
    if simplified in (sp.oo, -sp.oo, sp.zoo, sp.nan):
        raise SolveUndecidable(f"{context}: result is not finite ({simplified})")
    return simplified


def _coerce_int(raw: Any, context: str) -> int:
    """Accept an int, or a (possibly substituted) string like ``(3)`` that is an
    integer. Raises on anything non-integral (fail loud)."""
    if isinstance(raw, bool):
        raise SolveError(f"{context}: expected an integer, got a bool")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        val = _require_number(_parse(raw), context)
        if val.is_Integer:
            return int(val)
        raise SolveError(f"{context}: expected an integer, got {val}")
    raise SolveError(f"{context}: expected an integer, got {raw!r}")


def values_equal(a: sp.Expr, b: sp.Expr) -> bool:
    """True iff two SymPy values are exactly equal (symbolic then numeric)."""
    try:
        if a == b:
            return True
        d = sp.simplify(a - b)
        if d == 0:
            return True
        eq = sp.nsimplify(a) == sp.nsimplify(b)
        return bool(eq)
    except Exception:
        return False


def display(value: sp.Expr) -> str:
    """Canonical, SymPy-parseable ASCII rendering of an answer (** for powers)."""
    return sp.sstr(value)


# --- ops ------------------------------------------------------------------------


def _op_evaluate(spec: dict[str, Any]) -> dict[str, Any]:
    val = _require_number(_parse(spec.get("expr")), "evaluate")
    return {"value": val, "display": display(val)}


def _split_equation(equation: Any, extra: dict[str, Any] | None = None) -> sp.Expr:
    if not isinstance(equation, str) or not equation.strip():
        raise SolveError(f"solve needs an 'equation' string, got {equation!r}")
    if "=" in equation:
        lhs, rhs = equation.split("=", 1)
        return _parse(lhs, extra) - _parse(rhs, extra)
    return _parse(equation, extra)


def _op_solve(spec: dict[str, Any]) -> dict[str, Any]:
    name = spec.get("var", "x")
    if not isinstance(name, str) or not name.isidentifier():
        raise SolveError(f"invalid variable name {name!r}")
    # Solve over the reals (real symbol) so Abs(...) is solvable and complex roots
    # are excluded; parse the equation against this SAME symbol.
    var = sp.Symbol(name, real=True)
    expr = _split_equation(spec.get("equation"), extra={name: var})
    try:
        sols = sp.solve(expr, var, dict=False)
    except Exception as exc:
        raise SolveUndecidable(f"solve failed: {exc}") from exc
    real: list[sp.Expr] = []
    for s in sols:
        try:
            s2 = sp.simplify(s)
        except Exception:
            s2 = s
        if s2.free_symbols or not s2.is_real:
            continue
        if not any(values_equal(s2, r) for r in real):
            real.append(s2)
    if not real:
        raise SolveUndecidable(f"no real closed-form solution for {spec.get('equation')!r}")
    real_sorted = sorted(real, key=lambda e: float(e))
    return {"solutions": real_sorted, "value": real_sorted[0], "display": display(real_sorted[0])}


def _op_iterate(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "x"))
    f = _parse(spec.get("f"))
    n = _coerce_int(spec.get("n"), "iterate.n")
    if n < 0:
        raise SolveError(f"iterate needs a non-negative integer 'n', got {n}")
    cur = _parse(str(spec.get("x0")))
    for _ in range(n):
        cur = f.subs(var, cur)
    val = _require_number(cur, "iterate")
    return {"value": val, "display": display(val)}


def _op_diff(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "x"))
    order = _coerce_int(spec.get("order", 1), "diff.order")
    if order < 1:
        raise SolveError(f"diff 'order' must be a positive integer, got {order}")
    d = sp.diff(_parse(spec.get("expr")), var, order)
    if "at" in spec and spec["at"] is not None:
        val = _require_number(d.subs(var, _parse(str(spec["at"]))), "diff@point")
        return {"value": val, "display": display(val)}
    d = sp.simplify(d)
    return {"value": d, "display": display(d)}


def _op_integrate(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "x"))
    expr = _parse(spec.get("expr"))
    bounds = spec.get("bounds")
    if bounds is not None:
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise SolveError(f"integrate 'bounds' must be [a, b], got {bounds!r}")
        a, b = _parse(str(bounds[0])), _parse(str(bounds[1]))
        try:
            val = sp.integrate(expr, (var, a, b))
        except Exception as exc:
            raise SolveUndecidable(f"definite integral failed: {exc}") from exc
        val = _require_number(val, "integrate")
        return {"value": val, "display": display(val)}
    anti = sp.integrate(expr, var)
    if anti.has(sp.Integral):
        raise SolveUndecidable(f"no closed-form antiderivative for {spec.get('expr')!r}")
    anti = sp.simplify(anti)
    return {"value": anti, "display": display(anti)}


def _op_limit(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "x"))
    point = spec.get("point")
    pt = sp.oo if point in ("oo", "inf", "infinity") else _parse(str(point))
    direction = spec.get("dir", "+-")
    try:
        lim = sp.limit(_parse(spec.get("expr")), var, pt, direction if direction in ("+", "-") else "+-")
    except Exception as exc:
        raise SolveUndecidable(f"limit failed: {exc}") from exc
    if lim in (sp.zoo, sp.nan):
        raise SolveUndecidable(f"limit does not exist for {spec.get('expr')!r}")
    lim = sp.simplify(lim)
    return {"value": lim, "display": display(lim)}


def _op_vieta(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "x"))
    poly = sp.Poly(_parse(spec.get("poly")), var)
    which = spec.get("which", "sum")
    roots = sp.roots(poly)
    multiset: list[sp.Expr] = []
    for r, m in roots.items():
        multiset.extend([sp.simplify(r)] * m)
    if sum(roots.values()) != poly.degree():
        raise SolveUndecidable(f"polynomial {spec.get('poly')!r} has non-closed-form roots")
    if which == "sum":
        val = sum(multiset)
    elif which == "prod":
        val = sp.prod(multiset)
    elif which == "sum_pairs":
        val = sum(multiset[i] * multiset[j] for i in range(len(multiset)) for j in range(i + 1, len(multiset)))
    else:
        raise SolveError(f"unsupported vieta 'which' {which!r}; use sum/prod/sum_pairs")
    val = _require_number(val, "vieta")
    return {"value": val, "display": display(val)}


def _op_system(spec: dict[str, Any]) -> dict[str, Any]:
    var_names = spec.get("vars")
    if not isinstance(var_names, list) or not var_names:
        raise SolveError("system needs a non-empty 'vars' list")
    syms = {n: sp.Symbol(n, real=True) for n in var_names if isinstance(n, str) and n.isidentifier()}
    if len(syms) != len(var_names):
        raise SolveError(f"invalid variable name(s) in {var_names!r}")
    eqs_raw = spec.get("equations")
    if not isinstance(eqs_raw, list) or not eqs_raw:
        raise SolveError("system needs a non-empty 'equations' list")
    eqs = [_split_equation(e, extra=syms) for e in eqs_raw]
    try:
        sols = sp.solve(eqs, list(syms.values()), dict=True)
    except Exception as exc:
        raise SolveUndecidable(f"system solve failed: {exc}") from exc
    if not sols:
        raise SolveUndecidable("system has no solution")
    if len(sols) != 1:
        raise SolveUndecidable(f"system does not have a unique solution ({len(sols)} found)")
    solmap = sols[0]
    if any(v.free_symbols for v in solmap.values()):
        raise SolveUndecidable("system has infinitely many solutions (free parameters)")
    want = spec.get("want", var_names[0])
    val = _require_number(_parse(want, syms).subs(solmap), "system")
    return {
        "value": val, "display": display(val),
        "solution": {str(k): display(sp.simplify(v)) for k, v in solmap.items()},
    }


def _op_sum(spec: dict[str, Any]) -> dict[str, Any]:
    var = _sym(spec.get("var", "k"))
    expr = _parse(spec.get("expr"), {var.name: var})
    lo = _coerce_int(spec.get("lo"), "sum.lo")
    hi = _coerce_int(spec.get("hi"), "sum.hi")
    if hi < lo:
        raise SolveError(f"sum needs hi >= lo, got lo={lo} hi={hi}")
    val = _require_number(sp.summation(expr, (var, lo, hi)), "sum")
    return {"value": val, "display": display(val)}


def _parse_matrix(spec: dict[str, Any], key: str = "matrix") -> sp.Matrix:
    """Build a SymPy matrix from a nested list of expression strings/numbers."""
    raw = spec.get(key)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise SolveError(f"{key} must be a non-empty list of rows")
    rows: list[list[sp.Expr]] = []
    width: int | None = None
    for r in raw:
        if not isinstance(r, (list, tuple)) or not r:
            raise SolveError(f"{key} rows must be non-empty lists")
        if width is None:
            width = len(r)
        elif len(r) != width:
            raise SolveError(f"{key} rows have unequal length ({len(r)} vs {width})")
        rows.append([_parse(str(e)) for e in r])
    m = sp.Matrix(rows)
    if m.free_symbols:
        raise SolveError(f"{key} still has free symbols {m.free_symbols}; all entries must be numeric")
    return m


def _require_square(m: sp.Matrix, op: str) -> sp.Matrix:
    if m.rows != m.cols:
        raise SolveError(f"{op} needs a square matrix, got {m.rows}x{m.cols}")
    return m


def _op_det(spec: dict[str, Any]) -> dict[str, Any]:
    m = _require_square(_parse_matrix(spec), "det")
    val = _require_number(m.det(), "det")
    return {"value": val, "display": display(val)}


def _op_trace(spec: dict[str, Any]) -> dict[str, Any]:
    m = _require_square(_parse_matrix(spec), "trace")
    val = _require_number(m.trace(), "trace")
    return {"value": val, "display": display(val)}


def _op_rank(spec: dict[str, Any]) -> dict[str, Any]:
    m = _parse_matrix(spec)
    val = sp.Integer(m.rank())
    return {"value": val, "display": display(val)}


def _op_dblintegrate(spec: dict[str, Any]) -> dict[str, Any]:
    """Iterated (double/triple) definite integral. ``vars``/``bounds`` are ordered
    INNERMOST FIRST; an inner bound may reference an outer variable (Type I/II
    regions). Returns a number (fails loud if it is not finite)."""
    var_names = spec.get("vars")
    bounds = spec.get("bounds")
    if not isinstance(var_names, list) or len(var_names) not in (2, 3):
        raise SolveError("dblintegrate needs 'vars': 2 or 3 names (innermost first)")
    if not isinstance(bounds, list) or len(bounds) != len(var_names):
        raise SolveError("dblintegrate needs 'bounds' matching 'vars' (innermost first)")
    syms = {n: sp.Symbol(n, real=True) for n in var_names if isinstance(n, str) and n.isidentifier()}
    if len(syms) != len(var_names):
        raise SolveError(f"invalid variable name(s) in {var_names!r}")
    expr = _parse(spec.get("expr"), syms)
    limits = []
    for n, bpair in zip(var_names, bounds):
        if not isinstance(bpair, (list, tuple)) or len(bpair) != 2:
            raise SolveError(f"each bounds entry must be [lo, hi], got {bpair!r}")
        lo = _parse(str(bpair[0]), syms)
        hi = _parse(str(bpair[1]), syms)
        limits.append((syms[n], lo, hi))
    try:
        val = sp.integrate(expr, *limits)
    except Exception as exc:
        raise SolveUndecidable(f"iterated integral failed: {exc}") from exc
    val = _require_number(val, "dblintegrate")
    return {"value": val, "display": display(val)}


def _op_eig(spec: dict[str, Any]) -> dict[str, Any]:
    m = _require_square(_parse_matrix(spec), "eig")
    which = spec.get("which", "max")
    try:
        evals = m.eigenvals()
    except Exception as exc:
        raise SolveUndecidable(f"eigenvalue computation failed: {exc}") from exc
    if sum(int(mult) for mult in evals.values()) != m.rows:
        raise SolveUndecidable("matrix has non-closed-form eigenvalues")
    multiset: list[sp.Expr] = []
    for e, mult in evals.items():
        multiset.extend([sp.simplify(e)] * int(mult))
    if which == "sum":
        val = _require_number(sum(multiset), "eig.sum")
    elif which == "prod":
        val = _require_number(sp.prod(multiset), "eig.prod")
    elif which in ("max", "min"):
        reals: list[sp.Expr] = []
        for e in multiset:
            e2 = _require_number(e, "eig")
            if e2.is_real is not True:
                raise SolveUndecidable(f"eig {which} needs all-real eigenvalues, got {e2}")
            reals.append(e2)
        val = max(reals, key=lambda z: float(z)) if which == "max" else min(reals, key=lambda z: float(z))
    else:
        raise SolveError(f"unsupported eig 'which' {which!r}; use max/min/sum/prod")
    return {"value": val, "display": display(val)}


_OPS = {
    "evaluate": _op_evaluate, "solve": _op_solve, "iterate": _op_iterate,
    "diff": _op_diff, "integrate": _op_integrate, "limit": _op_limit, "vieta": _op_vieta,
    "system": _op_system, "sum": _op_sum,
    "det": _op_det, "trace": _op_trace, "rank": _op_rank, "eig": _op_eig,
    "dblintegrate": _op_dblintegrate,
}


def solve_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Compute the true answer for an op-spec. Raises SolveError on any failure.

    Returns a dict with at least ``value`` (a SymPy expr) and ``display`` (ASCII);
    ``solve`` also returns ``solutions`` (the full real solution set, so the caller
    can keep distractors OUT of it)."""
    if not isinstance(spec, dict):
        raise SolveError(f"op-spec must be a dict, got {type(spec).__name__}")
    op = spec.get("op")
    fn = _OPS.get(op)
    if fn is None:
        raise SolveError(f"unknown op {op!r}; supported: {', '.join(sorted(_OPS))}")
    return fn(spec)
