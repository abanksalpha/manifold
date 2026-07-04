# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""seed_templates.py — a first set of parametric templates for real computational
skills, to prove the number-replacement engine end to end.

Each is authored ONCE; :mod:`templates` instantiates unlimited correct variants by
replacing numbers and computing the answer with :mod:`solver`. These four cover the
regression skills the old LLM pipeline got wrong (iteration, log equations) and
show variety across skills. The full per-skill set is authored later by the
subagent swarm against this same schema.

Slots are ``[[name]]`` everywhere (stem, answer_spec, CONSTRAINTS, distractor
recipes). Distractors here are simple numeric offsets so the engine is robust; the
LLM "dress" stage can later replace them with misconception-specific ones.
"""

from __future__ import annotations

from typing import Any

# Robust default distractors: five distinct offsets from the true answer. The
# engine guards them (drops any that equal the answer or another valid solution),
# then keeps the first four distinct ones.
_OFFSETS = ["[[answer]] + 1", "[[answer]] - 1", "[[answer]] + 2", "[[answer]] - 2", "[[answer]] + 3"]

TEMPLATES: list[dict[str, Any]] = [
    {
        "template_id": "iterate_affine_v1",
        "skill_id": "self_composition_iteration_fixed_points",
        "topic_id": "precalc_functions",
        "tier": "relearn",
        "params": {
            "a": {"type": "int", "lo": 2, "hi": 3},
            "b": {"type": "int", "lo": -3, "hi": 3},
            "x0": {"type": "int", "lo": 1, "hi": 4},
            "n": {"type": "choice", "values": [2, 3]},
        },
        "constraints": ["Ne([[b]], 0)"],
        "stem": (
            "Let \\( f(x) = [[a]]x + ([[b]]) \\). Define \\( x_0 = [[x0]] \\) and "
            "\\( x_{n+1} = f(x_n) \\). What is \\( x_{[[n]]} \\)?"
        ),
        "answer_spec": {"op": "iterate", "f": "[[a]]*x + [[b]]", "x0": "[[x0]]", "n": "[[n]]", "var": "x"},
        "distractors": _OFFSETS,
        "solution": "Apply \\( f \\) repeatedly from \\( x_0 = [[x0]] \\); after [[n]] steps the value is \\([[answer]]\\).",
    },
    {
        "template_id": "remainder_theorem_v1",
        "skill_id": "remainder_and_factor_theorems",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {
            "a": {"type": "int", "lo": -4, "hi": 4},
            "b": {"type": "int", "lo": -4, "hi": 4},
            "c": {"type": "int", "lo": -6, "hi": 6},
            "r": {"type": "int", "lo": -3, "hi": 3},
        },
        "constraints": ["Ne([[r]], 0)"],
        "stem": (
            "Let \\( p(x) = x^3 + ([[a]])x^2 + ([[b]])x + ([[c]]) \\). What is the remainder "
            "when \\( p(x) \\) is divided by \\( x - ([[r]]) \\)?"
        ),
        "answer_spec": {"op": "evaluate", "expr": "([[r]])**3 + ([[a]])*([[r]])**2 + ([[b]])*([[r]]) + ([[c]])"},
        "distractors": _OFFSETS,
        "solution": "By the Remainder Theorem the remainder is \\( p([[r]]) = [[answer]] \\).",
    },
    {
        "template_id": "log_diff_equation_v1",
        "skill_id": "solving_logarithmic_equations",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {"c": {"type": "int", "lo": 1, "hi": 8}},
        "constraints": ["Gt([[c]], 0)"],
        "stem": "Solve \\( \\log_2(x + [[c]]) - \\log_2(x) = 1 \\). Which of the following is a solution?",
        "answer_spec": {"op": "solve", "equation": "log(x + [[c]], 2) - log(x, 2) = 1", "var": "x"},
        "distractors": _OFFSETS,
        "solution": "\\( \\log_2\\frac{x+[[c]]}{x}=1 \\Rightarrow \\frac{x+[[c]]}{x}=2 \\Rightarrow x=[[answer]] \\).",
    },
    {
        "template_id": "abs_value_equation_v1",
        "skill_id": "absolute_value_equations_and_inequalities",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {
            "a": {"type": "choice", "values": [1, 2]},
            "b": {"type": "int", "lo": 0, "hi": 8},
            "c": {"type": "int", "lo": 1, "hi": 8},
        },
        "constraints": ["Eq(Mod([[b]] + [[c]], [[a]]), 0)", "Eq(Mod([[b]] - [[c]], [[a]]), 0)"],
        "stem": "Solve \\( |[[a]]x - [[b]]| = [[c]] \\). Which of the following is a solution?",
        "answer_spec": {"op": "solve", "equation": "Abs([[a]]*x - [[b]]) = [[c]]", "var": "x"},
        "distractors": _OFFSETS,
        "solution": "\\( [[a]]x - [[b]] = \\pm[[c]] \\); one solution is \\( x = [[answer]] \\).",
    },
    {
        # Right-hand sides are DERIVED from a chosen integer solution (p, q), so the
        # system is guaranteed to have that clean solution and the stem shows it.
        "template_id": "linear_system_v1",
        "skill_id": "solving_a_small_linear_system",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {
            "p": {"type": "int", "lo": -4, "hi": 4},
            "q": {"type": "int", "lo": -4, "hi": 4},
            "a1": {"type": "int", "lo": 1, "hi": 4},
            "b1": {"type": "int", "lo": -4, "hi": 4},
            "a2": {"type": "int", "lo": 1, "hi": 4},
            "b2": {"type": "int", "lo": -4, "hi": 4},
        },
        "constraints": ["Ne([[a1]]*[[b2]] - [[a2]]*[[b1]], 0)"],
        "derived": {"c1": "[[a1]]*[[p]] + [[b1]]*[[q]]", "c2": "[[a2]]*[[p]] + [[b2]]*[[q]]"},
        "stem": (
            "Consider the system \\( [[a1]]x + ([[b1]])y = [[c1]] \\) and "
            "\\( [[a2]]x + ([[b2]])y = [[c2]] \\). What is the value of \\( x \\)?"
        ),
        "answer_spec": {
            "op": "system",
            "equations": ["[[a1]]*x + [[b1]]*y = [[c1]]", "[[a2]]*x + [[b2]]*y = [[c2]]"],
            "vars": ["x", "y"], "want": "x",
        },
        "distractors": _OFFSETS,
        "solution": "Solving the system gives \\( x = [[answer]] \\).",
    },
    {
        "template_id": "exponential_equation_v1",
        "skill_id": "solving_exponential_equations",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {
            "base": {"type": "choice", "values": [2, 3, 5]},
            "c": {"type": "int", "lo": 0, "hi": 3},
            "k": {"type": "int", "lo": 1, "hi": 4},
        },
        "constraints": ["Gt([[k]], [[c]])"],
        "derived": {"rhs": "[[base]]**[[k]]"},
        "stem": "Solve \\( [[base]]^{x + [[c]]} = [[rhs]] \\). Which of the following is a solution?",
        "answer_spec": {"op": "solve", "equation": "[[base]]**(x + [[c]]) = [[rhs]]", "var": "x"},
        "distractors": _OFFSETS,
        "solution": "\\( x + [[c]] = [[k]] \\Rightarrow x = [[answer]] \\).",
    },
    {
        "template_id": "sum_of_coefficients_v1",
        "skill_id": "sums_of_coefficients_and_binomial_theorem",
        "topic_id": "elementary_algebra",
        "tier": "relearn",
        "params": {
            "a": {"type": "int", "lo": 1, "hi": 3},
            "b": {"type": "int", "lo": 1, "hi": 4},
            "n": {"type": "choice", "values": [2, 3, 4]},
        },
        "constraints": [],
        "stem": "For \\( P(x) = ([[a]]x + [[b]])^{[[n]]} \\), what is the sum of the coefficients of \\( P(x) \\)?",
        "answer_spec": {"op": "evaluate", "expr": "([[a]] + [[b]])**[[n]]"},
        "distractors": _OFFSETS,
        "solution": "The sum of coefficients is \\( P(1) = ([[a]] + [[b]])^{[[n]]} = [[answer]] \\).",
    },
]
