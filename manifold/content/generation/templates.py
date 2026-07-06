# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""templates.py — parametric templates: infinite, deterministically-correct items
by REPLACING NUMBERS.

A template is authored ONCE (parameters + a stem with slots + an answer *op-spec*
with the same slots + distractor recipes). To make an item, code:

  1. samples the parameters (seeded, subject to "nice-number" constraints),
  2. renders the stem AND the answer op-spec from the SAME parameters,
  3. computes the answer with :mod:`solver` (SymPy) — never an LLM,
  4. builds distractors from recipes and guards them (distinct, != answer, and
     for equations NOT another valid solution),
  5. assembles a 5-choice item with the correct answer at a seeded index.

Because the stem and the answer are rendered from the *same* parameters, they
cannot disagree (the stem-faithfulness hole that let LLM word-problems bank wrong
answers is closed by construction). Changing the seed changes the numbers, so one
template yields unlimited correct variants.

Slots use ``[[name]]`` (not ``{name}``) so they never collide with LaTeX braces
like ``\\frac{a}{b}``.

Interpreter: the generation venv (sympy). See verify.py header.
"""

from __future__ import annotations

import random
import re
from typing import Any

import solver

SLOT = re.compile(r"\[\[(\w+)\]\]")
CHOICE_COUNT = 5


class TemplateError(Exception):
    """The template itself is malformed (author bug). Fail loud."""


class InstanceRejected(Exception):
    """This seed did not yield a clean item (constraints/distractors); try another."""


# --- substitution ---------------------------------------------------------------


def _subst(text: str, params: dict[str, Any], *, expr: bool) -> str:
    """Replace ``[[name]]`` slots. In ``expr`` mode each value is parenthesized so
    a negative like ``-1`` composes safely inside a larger expression."""
    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in params:
            raise TemplateError(f"reference to unknown parameter [[{name}]]")
        return f"({params[name]})" if expr else f"{params[name]}"
    return SLOT.sub(repl, text)


def _subst_value(v: Any, params: dict[str, Any]) -> Any:
    """Slot-substitute a spec value, recursing into nested lists/dicts so a matrix
    (a nested list of expression strings) has its [[slots]] filled too."""
    if isinstance(v, str):
        return _subst(v, params, expr=True)
    if isinstance(v, list):
        return [_subst_value(x, params) for x in v]
    if isinstance(v, dict):
        return {k: _subst_value(x, params) for k, x in v.items()}
    return v


def _subst_spec(spec: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    return {k: _subst_value(v, params) for k, v in spec.items()}


def _leftover_slots(text: str) -> bool:
    return bool(SLOT.search(text))


# Guard against the "implicit-multiplication concatenation" author bug. Slot
# substitution is pure string replacement, so a DISPLAY field written ``2[[n]]``
# (meaning 2*n) renders the digits glued: n=1 -> "21", not "2". The answer is
# computed from the answer-spec (where ``2*[[n]]`` really is arithmetic), so a
# glued stem silently stops matching its own code-computed answer. Authors must
# make the product explicit (``2\cdot[[n]]``). This detects a numeric slot whose
# rendered value would fuse with an adjacent literal digit, or with another
# numeric slot — a non-numeric slot (a noun, "\sin x") cannot form a bigger
# number, so "3 [[noun]]" and the like are never flagged.
_FUSE = re.compile("[0-9]\x01|\x02[0-9]|\x02\x01")


def _fuses_numerically(text: str, params: dict[str, Any]) -> bool:
    def mark(m: re.Match[str]) -> str:
        v = params.get(m.group(1))
        return f"\x01{v}\x02" if v is not None and re.match(r"-?\d", str(v)) else "\x00"

    return bool(_FUSE.search(SLOT.sub(mark, text)))


# --- display tidy-up ------------------------------------------------------------
# Templates wrap every numeric slot in defensive parens (e.g. "[[a]]x + ([[b]])")
# so a negative value composes safely inside a bigger expression. That is correct
# for the answer-spec/distractor EXPR path, but in the rendered STEM prose it leaves
# ugly artifacts: "4x + (1)", "4x + (-2)", "x - (-3)". This pass runs ONLY on the
# human-facing display fields (stem, solution, rationales) — never on choices or the
# answer-spec — and rewrites those artifacts into clean math ("4x + 1", "4x - 2",
# "x + 3"). It only ever touches ORDINARY parens around a bare signed integer; it
# never alters LaTeX delimiters (\( \[ \left( \right)) or function-call parens like
# f(g(1)), so the math meaning is unchanged.

# + or - immediately followed by a parenthesized signed integer -> merge the signs.
_TIDY_OP = re.compile(r"([+\-])\s*\(\s*([+-]?\d+)\s*\)")
# a group opener (\left(, \(, =) immediately followed by a parenthesized signed
# integer -> drop the redundant inner parens but keep the sign, e.g. "\left( (-2)x"
# -> "\left( -2x" and "= (-3)" -> "= -3".
_TIDY_OPEN = re.compile(r"(\\left\(|\\\(|=)\s*\(\s*([+-]?\d+)\s*\)")
# a coefficient of 1 directly multiplying a variable letter -> drop the 1 ("1x" ->
# "x", "-1x" -> "-x"). Guarded so it never touches a multi-digit number (41x), a
# subscript/exponent (x_1y, x^{1}, an unbraced x^1y), a standalone constant ("+ 1"),
# a decimal (2.1x), or a LaTeX command (1\cdot stays).
_TIDY_ONE_COEF = re.compile(r"(?<![0-9.A-Za-z\\_{^])1(?=[A-Za-z])")
# two adjacent signs from a bare negative substitution ("4x + -6", "4x - -6") ->
# one sign ("4x - 6", "4x + 6"). Fires only when a number follows, so it never
# touches an exponent ("x^-2"), scientific notation, or a lone operator.
_TIDY_DOUBLE_SIGN = re.compile(r"([+\-])\s*([+\-])\s*(?=[\d.])")
# an ADDITIVE zero term -> drop it entirely ("3x + 0" -> "3x", "x^2 - 0" -> "x^2").
# The lookbehind requires a real term char (digit/letter/closing bracket) right
# before the +/- operator, so an equation side like "x = 0" or a tuple "(0, 3)" is
# NOT touched (0 there is not preceded by a + or -). The lookahead requires the 0 to
# be a standalone integer, so it never fires on "10" (0 inside a number), "0.5"
# (decimal), "0y" (zero coefficient — left alone by design) or "x_0" (subscript).
# Runs AFTER _TIDY_OP so an already-merged "+ (0)" (now "+ 0") is dropped too.
_TIDY_ZERO_TERM = re.compile(r"(?<=[0-9A-Za-z)\]}])\s*[+\-]\s*0(?![0-9.A-Za-z_])")


def _tidy_math(text: str) -> str:
    """Clean sign/parenthesis artifacts in a rendered DISPLAY field. Idempotent."""
    def _op(m: re.Match[str]) -> str:
        op, num = m.group(1), int(m.group(2))
        val = num if op == "+" else -num
        return f"+ {val}" if val >= 0 else f"- {-val}"

    text = _TIDY_DOUBLE_SIGN.sub(lambda m: "+ " if m.group(1) == m.group(2) else "- ", text)
    text = _TIDY_OP.sub(_op, text)
    text = _TIDY_OPEN.sub(lambda m: f"{m.group(1)} {m.group(2)}", text)
    text = _TIDY_ONE_COEF.sub("", text)
    text = _TIDY_ZERO_TERM.sub("", text)  # drop additive-zero terms ("3x + 0" -> "3x")
    text = re.sub(r"  +", " ", text)  # collapse any double spaces the edits created
    return text


# --- parameter sampling ---------------------------------------------------------


def _sample_one(ps: dict[str, Any], rng: random.Random) -> Any:
    t = ps.get("type")
    if t == "int":
        return rng.randint(int(ps["lo"]), int(ps["hi"]))
    if t == "choice":
        return rng.choice(list(ps["values"]))
    raise TemplateError(f"unknown parameter type {t!r} (use 'int' or 'choice')")


def _truthy(constraint_expr: str) -> bool:
    val = solver._parse(constraint_expr)
    import sympy as sp
    val = sp.simplify(val)
    if val in (sp.true, True):
        return True
    if val in (sp.false, False):
        return False
    raise TemplateError(f"constraint did not reduce to a boolean: {constraint_expr!r} -> {val}")


def _sample_params(template: dict[str, Any], rng: random.Random, tries: int = 300) -> dict[str, Any]:
    specs = template.get("params") or {}
    constraints = template.get("constraints") or []
    for _ in range(tries):
        params = {name: _sample_one(ps, rng) for name, ps in specs.items()}
        if all(_truthy(_subst(c, params, expr=True)) for c in constraints):
            return params
    raise InstanceRejected("could not satisfy constraints within try budget")


# --- distractors ----------------------------------------------------------------


def _eval_recipe(recipe: str, params: dict[str, Any], answer: Any) -> Any:
    """A distractor recipe is an expression over the params and ``answer``."""
    import sympy as sp
    ctx = dict(params)
    ctx["answer"] = sp.sstr(answer)
    val = solver._parse(_subst(recipe, ctx, expr=True))
    val = sp.simplify(val)
    if val.free_symbols:
        raise TemplateError(f"distractor recipe {recipe!r} did not reduce to a number: {val}")
    return val


# --- instantiation --------------------------------------------------------------


def instantiate(
    template: dict[str, Any], seed: int, params_override: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build one concrete item from ``template`` at ``seed``.

    Raises :class:`InstanceRejected` if this seed can't yield a clean item (bad
    numbers / colliding distractors); the caller should try another seed. Raises
    :class:`TemplateError` / :class:`solver.SolveError` for author/spec bugs.
    """
    import sympy as sp

    rng = random.Random(seed)
    params = params_override if params_override is not None else _sample_params(template, rng)

    # Derived params: values COMPUTED from the sampled ones (e.g. a system's RHS, or
    # an expanded polynomial's coefficients) so the stem can display them while the
    # answer stays code-computed. Computed once, then usable in stem/spec/distractors.
    for name, expr in (template.get("derived") or {}).items():
        if name in params:
            raise TemplateError(f"derived name {name!r} shadows a sampled parameter")
        v = sp.simplify(solver._parse(_subst(expr, params, expr=True)))
        if v.free_symbols:
            raise TemplateError(f"derived {name!r} did not reduce to a number: {v}")
        params[name] = solver.display(v)

    answer_spec = _subst_spec(template["answer_spec"], params)
    result = solver.solve_spec(answer_spec)
    answer = result["value"]
    forbidden = list(result.get("solutions", [answer]))  # equations: keep distractors off ALL roots

    # Optional niceness gate so MCQ answers stay clean (default: rational).
    if template.get("require_rational", True) and answer.is_rational is not True:
        raise InstanceRejected(f"answer {answer} is not a clean rational for these params")

    recipes = template.get("distractors") or []
    if len(recipes) < CHOICE_COUNT - 1:
        raise TemplateError(f"template needs >= {CHOICE_COUNT - 1} distractor recipes, has {len(recipes)}")
    distractors: list[Any] = []
    for recipe in recipes:
        val = _eval_recipe(recipe, params, answer)
        if any(solver.values_equal(val, f) for f in forbidden):
            continue  # coincides with the answer or another valid solution -> skip
        if any(solver.values_equal(val, d) for d in distractors):
            continue  # duplicate distractor -> skip
        distractors.append(val)
        if len(distractors) == CHOICE_COUNT - 1:
            break
    if len(distractors) < CHOICE_COUNT - 1:
        raise InstanceRejected("not enough distinct, non-colliding distractors for these params")

    # Author-bug guard: no display field may fuse a numeric slot into a larger
    # number with an adjacent digit/slot (see _fuses_numerically). This is a
    # TemplateError (not InstanceRejected): it is wrong for EVERY seed, so it must
    # fail loudly at the acceptance gate rather than silently ship glued math.
    disp_params = {**params, "answer": solver.display(answer)}
    for _field in (template["stem"], template.get("solution") or "", *(template.get("distractor_rationales") or [])):
        if isinstance(_field, str) and _fuses_numerically(_field, disp_params):
            raise TemplateError(
                f"display field fuses a numeric slot with an adjacent number; "
                f"write an explicit \\cdot: {_field!r}"
            )

    stem = _tidy_math(_subst(template["stem"], params, expr=False))
    if _leftover_slots(stem):
        raise TemplateError("stem still has unfilled [[slots]] after substitution")

    correct_index = rng.randrange(CHOICE_COUNT)
    choices_vals: list[Any] = []
    di = 0
    for i in range(CHOICE_COUNT):
        if i == correct_index:
            choices_vals.append(answer)
        else:
            choices_vals.append(distractors[di]); di += 1
    choices = [solver.display(v) for v in choices_vals]

    solution = _tidy_math(_subst(template.get("solution", ""), {**params, "answer": solver.display(answer)}, expr=False))
    rationales = [
        _tidy_math(_subst(r, {**params, "answer": solver.display(answer)}, expr=False))
        for r in (template.get("distractor_rationales") or [])
    ][: CHOICE_COUNT - 1]
    while len(rationales) < CHOICE_COUNT - 1:
        rationales.append("This value comes from a common mistake, not the correct computation.")

    topic = template.get("topic_id", "")
    return {
        "stem": stem,
        "choices": choices,
        "correct_index": correct_index,
        "solution": solution or f"The computed answer is \\({solver.display(answer)}\\).",
        "distractor_rationales": rationales,
        "source_ref": f"manifold-template://{topic}/{template['skill_id']}#{template['template_id']}",
        "topic_id": topic,
        "skill_id": template["skill_id"],
        "tier_tag": f"mf::tier::{template.get('tier', 'relearn')}",
        "provenance": {
            "template_id": template["template_id"],
            "params": params,
            "answer_spec": answer_spec,
            "answer": solver.display(answer),
            "seed": seed,
            "solver_computed": True,
        },
    }


# --- validation -----------------------------------------------------------------


def check_faithfulness(
    template: dict[str, Any],
    *,
    solve: Any = None,
    config: Any = None,
    n: int = 5,
    samples: int = 2,
    base_seed: int = 0,
    threshold: float = 0.8,
) -> dict[str, Any]:
    """Guard the ONE risk code can't catch alone: the stem PROSE drifting from the
    answer-spec (a template that reads "x_3" but computes "x_2").

    The answer is code-correct by construction, so an *independent* solver reading
    only the rendered STEM+choices should land on it. We instantiate ``n`` variants
    and blind-solve each via :mod:`independent_solve` (a strong/reasoning model in
    production; an injected double in tests). If the stem faithfully describes the
    spec, agreement is high; a drifted stem makes the solver disagree, so the
    template is rejected. This runs ONCE per template (acceptance gate), never on
    the serving path — served correctness stays purely code-computed.
    """
    import independent_solve as isolve

    agreed = 0
    total = 0
    details: list[dict[str, Any]] = []
    for s in range(base_seed, base_seed + n):
        try:
            item = instantiate(template, s)
        except InstanceRejected:
            continue
        total += 1
        verdict = isolve.check_agreement(item, config=config, solve=solve, samples=samples)
        if verdict["agreed"]:
            agreed += 1
        details.append({"seed": s, "agreed": verdict["agreed"], "reason": verdict["reason"]})
    faithful = total > 0 and (agreed / total) >= threshold
    return {"faithful": faithful, "agreed": agreed, "total": total, "threshold": threshold, "details": details}


def validate(template: dict[str, Any], n: int = 30, base_seed: int = 0) -> dict[str, Any]:
    """Instantiate ``n`` seeds and assert the invariants that make an item safe.

    Returns a report: successes, rejects (acceptable), hard errors (template bugs),
    and how many DISTINCT stems/answers were produced (proves number replacement).
    """
    ok = 0
    rejects = 0
    errors: list[str] = []
    stems: set[str] = set()
    answers: set[str] = set()
    for s in range(base_seed, base_seed + n):
        try:
            item = instantiate(template, s)
        except InstanceRejected:
            rejects += 1
            continue
        except (TemplateError, solver.SolveError) as exc:
            errors.append(f"seed {s}: {type(exc).__name__}: {exc}")
            continue
        except Exception as exc:
            # An unexpected failure (e.g. a SymPy internal limit hit while comparing
            # a pathological irrational value) is a bug in THIS seed's instance, not
            # a reason to abort every other seed's validation. Record it as an error
            # (still fails the template if too many occur) instead of crashing the
            # whole validate() call and hiding the health of every other seed.
            errors.append(f"seed {s}: {type(exc).__name__}: {exc}")
            continue
        # invariants
        ch = item["choices"]
        if len(ch) != CHOICE_COUNT or len(set(ch)) != CHOICE_COUNT:
            errors.append(f"seed {s}: choices not 5-distinct: {ch}")
            continue
        if _leftover_slots(item["stem"]) or any(_leftover_slots(c) for c in ch):
            errors.append(f"seed {s}: leftover slot in stem/choices")
            continue
        # faithfulness: re-solve the (substituted) spec and confirm it equals the
        # choice marked correct — the answer shown IS the code-computed one.
        recomputed = solver.solve_spec(item["provenance"]["answer_spec"])["value"]
        shown = solver._parse(ch[item["correct_index"]])
        if not solver.values_equal(recomputed, shown):
            errors.append(f"seed {s}: FAITHFULNESS FAIL: recomputed {recomputed} != shown {shown}")
            continue
        ok += 1
        stems.add(item["stem"])
        answers.add(ch[item["correct_index"]])
    return {
        "template_id": template.get("template_id"),
        "skill_id": template.get("skill_id"),
        "n": n,
        "ok": ok,
        "rejected": rejects,
        "errors": errors,
        "distinct_stems": len(stems),
        "distinct_answers": len(answers),
    }
