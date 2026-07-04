# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for the independent cross-solve gate (independent_solve.py) and its wiring
into serve_live.py. No network: the model call is always an injected/fixture double,
so these are hermetic and free. What they prove is the *gate logic*: a verified item
whose stem an independent solver does not resolve to the claimed choice is NOT served.

Run: manifold/content/generation/.venv/bin/python -m pytest \
        manifold/content/generation/test_independent_solve.py -q
"""

from __future__ import annotations

import pytest

import independent_solve as isolve
import serve_live

# A genuinely-correct prob_exact draft (P(sum of two dice = 5) = 4/36 = 1/9). verify.py
# recomputes this by exact brute force, so it truly verifies; the cross-solve gate is
# then what decides whether it also gets served.
GOOD_DRAFT = {
    "stem": "Two fair six-sided dice are rolled. What is the probability that the sum equals 5?",
    "correct_choice": "1/9",
    "distractors": ["1/12", "1/6", "2/9", "5/36"],
    "distractor_rationales": ["off by one", "sum of 7", "double count", "sum of 6"],
    "solution": "Four of 36 ordered outcomes sum to 5, so 4/36 = 1/9.",
    "check": {
        "type": "prob_exact",
        "expr": "Rational(1, 9)",
        "brute": {"vars": {"a": [1, 6], "b": [1, 6]}, "event": "Eq(a + b, 5)"},
    },
}

SKILL = {
    "skill_id": "dice_sum_probability",
    "topic_id": "probability",
    "tier": "teach",
    "skill_name": "Probability of a dice sum",
}


def _item(correct_index: int = 2) -> dict:
    """A minimal assembled item with a known correct_index for gate-only tests."""
    choices = ["1/12", "1/6", "1/9", "2/9", "5/36"]
    return {
        "stem": "Two fair dice are rolled; P(sum = 5)?",
        "choices": choices,
        "correct_index": correct_index,
        "check": {"type": "numeric", "expr": "1/9"},
    }


# --- gate logic -----------------------------------------------------------------


def test_agreement_when_solver_matches_label():
    verdict = isolve.check_agreement(_item(2), solve=lambda item: 2, samples=2)
    assert verdict["agreed"] is True
    assert verdict["chosen_index"] == 2
    assert verdict["claimed_index"] == 2


def test_disagreement_when_solver_picks_another_choice():
    verdict = isolve.check_agreement(_item(2), solve=lambda item: 0, samples=2)
    assert verdict["agreed"] is False
    assert verdict["chosen_index"] == 0
    assert "!= claimed 2" in verdict["reason"]


def test_split_votes_are_not_enough_agreement():
    calls = {"n": 0}

    def flaky(item):
        calls["n"] += 1
        return 2 if calls["n"] == 1 else 3  # one vote each -> no 2-way consensus

    verdict = isolve.check_agreement(_item(2), solve=flaky, samples=2)
    assert verdict["agreed"] is False
    assert verdict["chosen_index"] is None
    assert "no 2-way agreement" in verdict["reason"]


def test_single_sample_matching_label_agrees():
    verdict = isolve.check_agreement(_item(4), solve=lambda item: 4, samples=1)
    assert verdict["agreed"] is True


def test_none_index_when_true_answer_not_among_choices_disagrees():
    # The solver computed an answer that equals no listed choice (broken item, e.g. the
    # order-of-operations bug where the true answer 20 isn't an option): decisive reject.
    verdict = isolve.check_agreement(_item(2), solve=lambda item: isolve.NONE_INDEX, samples=2)
    assert verdict["agreed"] is False
    assert "NONE of the listed choices" in verdict["reason"]


def test_vote_derived_from_computed_value_agrees():
    # Real-solver shape: {computed_answer, chosen_index}. claimed=2 -> choice "1/9".
    solve = lambda item: {"computed_answer": "1/9", "chosen_index": 2}
    verdict = isolve.check_agreement(_item(2), solve=solve, samples=2)
    assert verdict["agreed"] is True


def test_computed_value_overrides_a_lazy_matching_index():
    # THE 20-not-in-choices bug: the model force-picks index 0 (== claimed 0), but its
    # COMPUTED answer (20) equals no choice. Value-matching must reject despite the index.
    solve = lambda item: {"computed_answer": "20", "chosen_index": 0}
    verdict = isolve.check_agreement(_item(0), solve=solve, samples=2)
    assert verdict["agreed"] is False
    assert "NONE of the listed choices" in verdict["reason"]


def test_computed_value_matching_a_different_choice_disagrees():
    # Solver computes "1/6" (choice 1) but claim is 0: value-match routes the vote to 1,
    # so it correctly disagrees with the claimed index.
    solve = lambda item: {"computed_answer": "1/6", "chosen_index": 0}
    verdict = isolve.check_agreement(_item(0), solve=solve, samples=2)
    assert verdict["agreed"] is False


# --- fixtures double (used by the offline e2e) ----------------------------------


def test_trust_label_oracle_agrees():
    solve = isolve._make_fixture_solver({"oracle": "trust_label"})
    verdict = isolve.check_agreement(_item(1), solve=solve, samples=2)
    assert verdict["agreed"] is True


def test_always_wrong_oracle_disagrees():
    solve = isolve._make_fixture_solver({"oracle": "always_wrong"})
    verdict = isolve.check_agreement(_item(1), solve=solve, samples=2)
    assert verdict["agreed"] is False


# --- no silent pass: unavailable solver fails loudly ----------------------------


def test_no_key_and_no_fixtures_raises_not_passes():
    cfg = isolve.SolveConfig(
        api_key=None, model="gpt-4o", base_url="x", fixtures_path=None,
        samples=2, request_timeout=1.0,
    )
    with pytest.raises(isolve.SolverAuthError):
        isolve.check_agreement(_item(2), config=cfg)


# --- which check types require a cross-solve -------------------------------------


@pytest.mark.parametrize("check_type", ["numeric", "equiv"])
def test_stated_value_checks_need_cross_solve(check_type):
    assert isolve.needs_cross_solve({"check": {"type": check_type}}) is True


@pytest.mark.parametrize("check_type", ["det", "rank", "eigen", "count", "prob_exact", "smt"])
def test_recompute_checks_are_self_grounding(check_type):
    assert isolve.needs_cross_solve({"check": {"type": check_type}}) is False


# --- serve_live integration: the actual runtime behavior ------------------------


def _good_gen(skill, difficulty):
    return serve_live._validate_draft(dict(GOOD_DRAFT))


def test_serve_live_serves_when_verified_and_cross_solved():
    result = serve_live.next_problem(
        SKILL, generate=_good_gen, solve=lambda item: item["correct_index"], attempts=3, seed=7
    )
    assert result["status"] == "ok"
    assert result["verifier_report"]["independent_solve"]["agreed"] is True


def test_serve_live_abstains_when_solver_disagrees_even_though_verified():
    # The draft genuinely verifies (prob_exact 1/9 is real), but the independent solver
    # always picks a different choice -> the item is never served (no fabrication).
    result = serve_live.next_problem(
        SKILL,
        generate=_good_gen,
        solve=lambda item: (item["correct_index"] + 1) % 5,
        attempts=3,
        seed=7,
    )
    assert result["status"] == "abstain"
    assert result["reason"] == serve_live.ABSTAIN_UNVERIFIED
    assert "independent_solver_disagreed" in result["detail"]
