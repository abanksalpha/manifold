# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for the deterministic correctness verifier (WS1, D32).

Run with the generation venv (see ``verify.py`` header for how it was created)::

    manifold/content/generation/.venv/bin/python -m pytest \
        manifold/content/generation/test_verify.py -q

Every fixture exercises the gate it names; correctness is recomputed by SymPy/NumPy
and Z3, never assumed. pytest puts this file's directory on ``sys.path`` (no
``__init__.py`` here), so ``verify``/``smt_check`` import directly.
"""

from __future__ import annotations

import pytest

import smt_check
import verify


def _base_item(**overrides) -> dict:
    """A structurally valid item; override fields per test."""
    item = {
        "stem": "Placeholder stem.",
        "choices": ["a", "b", "c", "d", "e"],
        "correct_index": 0,
        "solution": "Placeholder worked solution.",
        "source_ref": "docs/manifold/problem-types/eigen.md#1",
        "tier_tag": "mf::tier::teach",
        "check": {"type": "numeric", "expr": "0"},
    }
    item.update(overrides)
    return item


# --- Gate 2/3: a correct antiderivative item is accepted ------------------------


def test_correct_antiderivative_accepts():
    item = _base_item(
        stem="An antiderivative of cos(x) is:",
        choices=["sin(x)", "-sin(x)", "cos(x)", "x", "tan(x)"],
        correct_index=0,
        solution="d/dx sin(x) = cos(x).",
        source_ref="docs/manifold/problem-types/integral_calc.md#3",
        tier_tag="mf::tier::relearn",
        check={"type": "antiderivative", "integrand": "cos(x)", "var": "x"},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["reason"] == "ok"
    assert report["correct_choices"] == [0]
    assert all(gate["passed"] for gate in report["gates"].values())


# --- Gate 3: a wrong-answer item is rejected (single correct, wrong index) -------


def test_wrong_answer_rejects():
    item = _base_item(
        stem="An antiderivative of cos(x) is:",
        # correct_index points at cos(x) (index 0), but the real answer is sin(x).
        choices=["cos(x)", "-sin(x)", "sin(x)", "x", "1"],
        correct_index=0,
        solution="d/dx sin(x) = cos(x); cos(x) is not an antiderivative of itself.",
        source_ref="docs/manifold/problem-types/integral_calc.md#3",
        check={"type": "antiderivative", "integrand": "cos(x)", "var": "x"},
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "wrong_answer"
    assert report["gates"]["ground_truth"]["passed"] is True
    assert report["gates"]["single_answer"]["passed"] is False
    assert report["correct_choices"] == [2]


# --- Gate 3: a two-correct-answers item is rejected by single-answer -------------


def test_two_correct_answers_rejects():
    # x**2 and x**2 + 3 are both antiderivatives of 2x (they differ only by +C).
    item = _base_item(
        stem="An antiderivative of 2x is:",
        choices=["x**2", "x**2 + 3", "x**2 + x", "2*x", "x**3"],
        correct_index=0,
        solution="Both x^2 and x^2 + 3 differentiate to 2x, so this item is ambiguous.",
        source_ref="docs/manifold/problem-types/integral_calc.md#1",
        check={"type": "antiderivative", "integrand": "2*x", "var": "x"},
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "multiple_correct"
    assert report["gates"]["single_answer"]["passed"] is False
    assert report["correct_choices"] == [0, 1]


# --- Gate 2: an eigenvalue item is accepted -------------------------------------


def test_eigenvalue_accepts():
    item = _base_item(
        stem="Find the eigenvalues of [[2, 1], [1, 2]].",
        choices=["1, 3", "2, 2", "0, 4", "1, 2", "-1, 3"],
        correct_index=0,
        solution="det(A - lambda I) = (2 - lambda)^2 - 1 = 0 gives lambda = 1, 3.",
        source_ref="docs/manifold/problem-types/eigen.md#1",
        tier_tag="mf::tier::teach",
        check={"type": "eigen", "matrix": [[2, 1], [1, 2]]},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["reason"] == "ok"
    assert report["correct_choices"] == [0]


# --- Gate 2: a determinant item is accepted -------------------------------------


def test_determinant_accepts():
    item = _base_item(
        stem="Compute det([[2, 1], [1, 2]]).",
        choices=["3", "0", "4", "-3", "1"],
        correct_index=0,
        solution="2*2 - 1*1 = 3.",
        source_ref="docs/manifold/problem-types/eigen.md#11",
        check={"type": "det", "matrix": [[2, 1], [1, 2]]},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["reason"] == "ok"
    assert report["correct_choices"] == [0]


# --- Gate 2: an undecidable item is rejected with reason 'undecidable' -----------


def test_undecidable_rejects():
    # g is an arbitrary (undefined) function: no numeric grounding is possible, so
    # the verifier must refuse to assume correctness rather than bank it.
    item = _base_item(
        stem="Let g be an arbitrary differentiable function. Which equals g(x)?",
        choices=["g(x)", "2*g(x)", "g(x) + 1", "x", "0"],
        correct_index=0,
        solution="g is arbitrary, so equality cannot be mechanically decided.",
        source_ref="docs/manifold/problem-types/real_analysis_sequences.md#1",
        check={"type": "equiv", "expr": "g(x)"},
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "undecidable"
    assert report["gates"]["structural"]["passed"] is True
    assert report["gates"]["ground_truth"]["passed"] is False


# --- Gate 1: a malformed item is rejected structurally --------------------------


def test_malformed_structural_rejects():
    item = _base_item(
        stem="This item has only four choices.",
        choices=["1", "2", "3", "4"],
        correct_index=0,
        check={"type": "numeric", "expr": "1"},
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "structural"
    assert report["gates"]["structural"]["passed"] is False
    # Ground truth was never reached.
    assert report["gates"]["ground_truth"]["passed"] is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"choices": ["1", "1", "2", "3", "4"]},  # not distinct
        {"choices": ["1", "2", "3", "4", "  "]},  # empty choice
        {"correct_index": 5},  # out of range
        {"correct_index": True},  # bool is not a valid index
        {"stem": "  "},  # empty stem
        {"source_ref": ""},  # missing source
    ],
)
def test_structural_variants_reject(overrides):
    item = _base_item(check={"type": "numeric", "expr": "1"}, **overrides)
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "structural"


# --- extra check types (breadth) ------------------------------------------------


def test_numeric_accepts():
    item = _base_item(
        stem="Evaluate sin(pi/6).",
        choices=["1/2", "sqrt(3)/2", "1", "0", "-1/2"],
        correct_index=0,
        solution="sin(pi/6) = 1/2.",
        source_ref="docs/manifold/problem-types/trigonometry.md#1",
        check={"type": "numeric", "expr": "sin(pi/6)"},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]


def test_no_correct_choice_rejects():
    item = _base_item(
        stem="Evaluate sin(pi/6).",
        choices=["1", "2", "3", "4", "5"],
        correct_index=0,
        solution="sin(pi/6) = 1/2, which is not listed.",
        source_ref="docs/manifold/problem-types/trigonometry.md#1",
        check={"type": "numeric", "expr": "sin(pi/6)"},
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "no_correct"
    assert report["correct_choices"] == []


def test_equiv_accepts():
    item = _base_item(
        stem="Factor x**2 - 1.",
        choices=["(x-1)*(x+1)", "x**2 + 1", "(x-1)**2", "x**2 - x", "1 - x**2"],
        correct_index=0,
        solution="Difference of squares.",
        source_ref="docs/manifold/problem-types/elementary_algebra.md#1",
        check={"type": "equiv", "expr": "x**2 - 1"},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]


def test_rank_accepts():
    item = _base_item(
        stem="Rank of [[1,2,3],[2,4,6],[1,0,1]].",
        choices=["2", "3", "1", "0", "4"],
        correct_index=0,
        solution="Row 2 = 2*Row 1; two independent rows remain.",
        source_ref="docs/manifold/problem-types/linear_algebra_core.md#1",
        check={"type": "rank", "matrix": [[1, 2, 3], [2, 4, 6], [1, 0, 1]]},
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]


def test_count_accepts_with_agreeing_bruteforce():
    item = _base_item(
        stem="How many 2-element subsets does a 6-element set have?",
        choices=["15", "30", "21", "36", "12"],
        correct_index=0,
        solution="C(6,2) = 15.",
        source_ref="docs/manifold/problem-types/combinatorics.md#1",
        check={
            "type": "count",
            "expr": "binomial(6,2)",
            "brute": {"vars": {"i": [1, 6], "j": [1, 6]}, "predicate": "i < j"},
        },
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]
    assert report["gates"]["ground_truth"]["detail"]["closed_form"] == 15
    assert report["gates"]["ground_truth"]["detail"]["brute_force"] == 15


def test_prob_exact_accepts_with_agreeing_bruteforce():
    item = _base_item(
        stem="Two fair dice are rolled. P(sum = 7)?",
        choices=["1/6", "5/36", "1/12", "7/36", "1/9"],
        correct_index=0,
        solution="6 of 36 outcomes sum to 7.",
        source_ref="docs/manifold/problem-types/probability.md#1",
        check={
            "type": "prob_exact",
            "expr": "Rational(1,6)",
            "brute": {"vars": {"a": [1, 6], "b": [1, 6]}, "event": "Eq(a+b,7)"},
        },
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]


def test_count_methods_disagree_is_undecidable():
    # Closed form (15) and brute force (a wrong predicate giving 21) disagree.
    item = _base_item(
        stem="Deliberately inconsistent count check.",
        choices=["15", "30", "21", "36", "12"],
        correct_index=0,
        solution="The two recompute paths disagree, so the item is undecidable.",
        source_ref="docs/manifold/problem-types/combinatorics.md#1",
        check={
            "type": "count",
            "expr": "binomial(6,2)",
            "brute": {"vars": {"i": [1, 6], "j": [1, 6]}, "predicate": "i <= j"},
        },
    )
    verified, report = verify.verify(item)
    assert verified is False
    assert report["reason"] == "undecidable"


# --- smt path (Z3) via verify.verify --------------------------------------------


def test_smt_universal_must_be_true_accepts():
    item = _base_item(
        stem="For every integer n, which must be true? "
        "I: n^2 >= 0.  II: n >= 0.  III: n^2 >= n.",
        choices=["I and III", "I, II, III", "I only", "II only", "none"],
        correct_index=0,
        solution="II fails at n = -1; I and III hold for all integers.",
        source_ref="docs/manifold/problem-types/number_theory.md#1",
        check={
            "type": "smt",
            "logic": "universal_subset",
            "vars": {"n": "Int"},
            "statements": {"I": "n*n >= 0", "II": "n >= 0", "III": "n*n >= n"},
            "choice_sets": [["I", "III"], ["I", "II", "III"], ["I"], ["II"], []],
        },
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [0]
    assert report["gates"]["ground_truth"]["detail"]["true_statements"] == ["I", "III"]


def test_smt_satisfies_accepts():
    item = _base_item(
        stem="Which positive integer x satisfies x^2 = 2x?",
        choices=["0", "2", "1", "-2", "4"],
        correct_index=1,
        solution="x^2 = 2x and x > 0 give x = 2.",
        source_ref="docs/manifold/problem-types/elementary_algebra.md#2",
        check={
            "type": "smt",
            "logic": "satisfies",
            "vars": {"x": "Int"},
            "constraints": ["x*x == 2*x", "x > 0"],
            "choice_values": {"x": ["0", "2", "1", "-2", "4"]},
        },
    )
    verified, report = verify.verify(item)
    assert verified is True
    assert report["correct_choices"] == [1]


# --- unsupported / malformed check blocks fail loudly (pipeline bug) -------------


def test_unsupported_check_type_raises():
    item = _base_item(check={"type": "handwave"})
    with pytest.raises(ValueError):
        verify.verify(item)


def test_missing_check_block_raises():
    item = _base_item()
    del item["check"]
    with pytest.raises(ValueError):
        verify.verify(item)


# --- smt_check core API (direct) ------------------------------------------------


def test_prove_universal_true():
    result = smt_check.prove_universal({"n": "Int"}, [], "n*n >= 0")
    assert result["proven"] is True
    assert result["counterexample"] is None


def test_prove_universal_false_with_counterexample():
    result = smt_check.prove_universal({"n": "Int"}, [], "n >= 0")
    assert result["proven"] is False
    assert result["counterexample"] is not None


def test_find_model_sat_and_unsat():
    sat = smt_check.find_model({"x": "Int"}, ["x*x == 4", "x > 0"])
    assert sat["sat"] is True
    assert sat["model"]["x"] == "2"
    unsat = smt_check.find_model({"x": "Int"}, ["x > 0", "x < 0"])
    assert unsat["sat"] is False
    assert unsat["model"] is None


def test_smt_config_error_on_bad_logic():
    with pytest.raises(smt_check.SmtConfigError):
        smt_check.correct_choices({"type": "smt", "logic": "bogus"}, ["a"] * 5)
