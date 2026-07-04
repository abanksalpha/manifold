# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Z3-based correctness checker for the decidable "must be true" / counterexample
middle of Manifold's content pipeline (WS1, decision D32).

This is the path :mod:`verify` delegates to when an item's ``check.type == "smt"``.
Z3 does the two things a symbolic CAS is bad at for MCQ correctness:

* **prove a universal** — "which of I/II/III *must* be true for every model?" is
  answered by asserting the negation and getting ``unsat`` (proven) or a concrete
  ``sat`` **counterexample** (disproven);
* **find a model** — "which listed value satisfies these constraints?" is answered
  by a satisfying assignment.

Per D32 (Lean rejected) and the cross-cutting rules, correctness is *computed*,
never assumed: if Z3 returns ``unknown`` we raise :class:`SmtUndecidable` so the
caller rejects-and-logs the item rather than banking an unverified one. Malformed
check blocks raise :class:`SmtConfigError` (a loud pipeline bug, not a bad item).

Interpreter (deps: z3-solver): ``manifold/content/generation/.venv/bin/python``
(created with ``out/pyenv/bin/python -m venv manifold/content/generation/.venv``
then ``pip install z3-solver``; the .venv is gitignored). See ``verify.py`` header.
"""

from __future__ import annotations

import functools
import threading
from typing import Any

import z3

# Z3's context and AST/solver objects are NOT thread-safe: two threads inside the
# C library at once segfaults the whole process (observed as SIGSEGV in
# Z3_solver_check_assumptions when the bank builder verifies items across worker
# threads). Serialize every z3 interaction in this module behind one re-entrant
# lock (re-entrant so the nested correct_choices -> prove_universal path does not
# deadlock). Only `smt` checks pay this cost — a minority of items, and z3 solves
# are fast — so build throughput is essentially unchanged; correctness is identical.
_Z3_LOCK = threading.RLock()


def _serialized(fn):
    """Run ``fn`` holding the process-wide z3 lock (thread-safety, not logic)."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with _Z3_LOCK:
            return fn(*args, **kwargs)

    return wrapper

# Sorts a check block may declare for its free variables. Kept deliberately small
# (the decidable arithmetic/boolean middle); anything else is a config error.
_SORTS = {
    "Int": z3.Int,
    "Real": z3.Real,
    "Bool": z3.Bool,
}

# The only names a formula string may reference besides its declared variables and
# integer/real literals. No Python builtins are exposed to the parser.
_ALLOWED: dict[str, Any] = {
    "And": z3.And,
    "Or": z3.Or,
    "Not": z3.Not,
    "Implies": z3.Implies,
    "Xor": z3.Xor,
    "If": z3.If,
    "Distinct": z3.Distinct,
    "Abs": lambda x: z3.If(x >= 0, x, -x),
    "True": True,
    "False": False,
}


class SmtConfigError(Exception):
    """The check block is malformed (a pipeline bug). Fail loudly — never swallow."""


class SmtUndecidable(Exception):
    """Z3 could not decide (returned ``unknown``). The caller must reject + log."""


def _make_vars(var_decls: dict[str, str]) -> dict[str, Any]:
    if not isinstance(var_decls, dict) or not var_decls:
        raise SmtConfigError(f"smt check needs a non-empty 'vars' map, got {var_decls!r}")
    env: dict[str, Any] = {}
    for name, sort in var_decls.items():
        if not isinstance(name, str) or not name.isidentifier():
            raise SmtConfigError(f"invalid smt variable name {name!r}")
        maker = _SORTS.get(sort)
        if maker is None:
            raise SmtConfigError(
                f"unsupported sort {sort!r} for {name!r}; use one of {sorted(_SORTS)}"
            )
        env[name] = maker(name)
    return env


def _parse(text: str, env: dict[str, Any]) -> Any:
    """Parse one formula string into a Z3 expression in a restricted namespace."""
    if not isinstance(text, str) or not text.strip():
        raise SmtConfigError(f"empty smt formula: {text!r}")
    namespace: dict[str, Any] = {"__builtins__": {}}
    namespace.update(_ALLOWED)
    namespace.update(env)
    try:
        return eval(text, namespace)  # noqa: S307 - restricted namespace, offline authoring input
    except SmtConfigError:
        raise
    except Exception as exc:  # loud: a formula that won't parse is a pipeline bug
        raise SmtConfigError(f"could not parse smt formula {text!r}: {exc}") from exc


def _model_to_dict(model: z3.ModelRef, env: dict[str, Any]) -> dict[str, str]:
    return {name: str(model.eval(var, model_completion=True)) for name, var in env.items()}


@_serialized
def prove_universal(
    var_decls: dict[str, str],
    hypotheses: list[str],
    claim: str,
) -> dict[str, Any]:
    """Prove ``claim`` holds for *every* assignment satisfying ``hypotheses``.

    Returns ``{"proven": bool, "counterexample": dict | None}``. Proven means the
    negation is unsatisfiable; otherwise the returned model is a concrete
    counterexample. Raises :class:`SmtUndecidable` if Z3 returns ``unknown``.
    """
    env = _make_vars(var_decls)
    solver = z3.Solver()
    for hyp in hypotheses or []:
        solver.add(_parse(hyp, env))
    solver.add(z3.Not(_parse(claim, env)))
    result = solver.check()
    if result == z3.unsat:
        return {"proven": True, "counterexample": None}
    if result == z3.sat:
        return {"proven": False, "counterexample": _model_to_dict(solver.model(), env)}
    raise SmtUndecidable(f"z3 returned 'unknown' proving universal claim {claim!r}")


@_serialized
def find_model(
    var_decls: dict[str, str],
    constraints: list[str],
) -> dict[str, Any]:
    """Find an assignment satisfying every constraint.

    Returns ``{"sat": bool, "model": dict | None}``. Raises
    :class:`SmtUndecidable` if Z3 returns ``unknown``.
    """
    env = _make_vars(var_decls)
    solver = z3.Solver()
    for constraint in constraints or []:
        solver.add(_parse(constraint, env))
    result = solver.check()
    if result == z3.sat:
        return {"sat": True, "model": _model_to_dict(solver.model(), env)}
    if result == z3.unsat:
        return {"sat": False, "model": None}
    raise SmtUndecidable("z3 returned 'unknown' searching for a model")


@_serialized
def correct_choices(check: dict[str, Any], choices: list[str]) -> tuple[set[int], dict[str, Any]]:
    """Entry point used by :mod:`verify`: return the set of correct choice indices.

    Dispatches on ``check['logic']``:

    * ``"universal_subset"`` — each statement is proven/disproven universally; the
      correct choice is the one whose claimed-true set equals the actually-true set
      (the classic GRE "which of I, II, III must be true?").
    * ``"satisfies"`` — the correct choice is the listed value that makes the
      constraints hold (find-a-model / evaluate a candidate).
    """
    logic = check.get("logic")
    if logic == "universal_subset":
        return _universal_subset(check, choices)
    if logic == "satisfies":
        return _satisfies(check, choices)
    raise SmtConfigError(
        f"unsupported smt logic {logic!r}; use 'universal_subset' or 'satisfies'"
    )


def _universal_subset(
    check: dict[str, Any], choices: list[str]
) -> tuple[set[int], dict[str, Any]]:
    var_decls = check.get("vars")
    statements = check.get("statements")
    choice_sets = check.get("choice_sets")
    hypotheses = check.get("hypotheses", [])
    if not isinstance(statements, dict) or not statements:
        raise SmtConfigError("universal_subset needs a non-empty 'statements' map")
    if not isinstance(choice_sets, list) or len(choice_sets) != len(choices):
        raise SmtConfigError(
            f"'choice_sets' must be a list of {len(choices)} entries, got {choice_sets!r}"
        )

    true_set: set[str] = set()
    detail: dict[str, Any] = {}
    for name, formula in statements.items():
        outcome = prove_universal(var_decls, hypotheses, formula)
        detail[name] = outcome
        if outcome["proven"]:
            true_set.add(name)

    correct: set[int] = set()
    for i, names in enumerate(choice_sets):
        if not isinstance(names, list):
            raise SmtConfigError(f"choice_sets[{i}] must be a list of statement names")
        claimed = set(names)
        unknown = claimed - set(statements)
        if unknown:
            raise SmtConfigError(f"choice_sets[{i}] names unknown statements {sorted(unknown)}")
        if claimed == true_set:
            correct.add(i)

    return correct, {
        "logic": "universal_subset",
        "true_statements": sorted(true_set),
        "statements": detail,
    }


def _satisfies(check: dict[str, Any], choices: list[str]) -> tuple[set[int], dict[str, Any]]:
    var_decls = check.get("vars")
    constraints = check.get("constraints", [])
    choice_values = check.get("choice_values")
    if not isinstance(choice_values, dict) or not choice_values:
        raise SmtConfigError("satisfies needs a non-empty 'choice_values' map")
    for var, values in choice_values.items():
        if not isinstance(values, list) or len(values) != len(choices):
            raise SmtConfigError(
                f"choice_values[{var!r}] must list {len(choices)} values, got {values!r}"
            )

    correct: set[int] = set()
    detail: dict[str, Any] = {"logic": "satisfies", "results": []}
    for i in range(len(choices)):
        env = _make_vars(var_decls)
        solver = z3.Solver()
        for constraint in constraints:
            solver.add(_parse(constraint, env))
        for var, values in choice_values.items():
            if var not in env:
                raise SmtConfigError(f"choice_values names undeclared variable {var!r}")
            solver.add(env[var] == _parse(str(values[i]), env))
        result = solver.check()
        if result == z3.sat:
            correct.add(i)
        elif result == z3.unknown:
            raise SmtUndecidable(f"z3 returned 'unknown' evaluating choice {i}")
        detail["results"].append(str(result))

    return correct, detail
