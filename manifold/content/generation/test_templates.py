# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for templates.py — the number-replacement engine.

Proves: (1) one template yields many DISTINCT variants (numbers change),
(2) every variant's shown answer IS the code-computed answer (faithfulness),
(3) the correct answer is never among the distractors, (4) determinism, and
(5) the regression case (iterate f=2x-1 from x0=1, x3) computes to 1."""

import pytest

import solver
import templates
from seed_templates import TEMPLATES

BY_ID = {t["template_id"]: t for t in TEMPLATES}


@pytest.mark.parametrize("tmpl", TEMPLATES, ids=lambda t: t["template_id"])
def test_template_validates(tmpl):
    rep = templates.validate(tmpl, n=40)
    assert rep["errors"] == [], rep["errors"]
    assert rep["ok"] >= 20, f"too few clean instances: {rep}"
    # number replacement really happens: many distinct stems produced.
    assert rep["distinct_stems"] >= 5, rep


@pytest.mark.parametrize("tmpl", TEMPLATES, ids=lambda t: t["template_id"])
def test_faithfulness_and_distractors(tmpl):
    made = 0
    for seed in range(60):
        try:
            item = templates.instantiate(tmpl, seed)
        except templates.InstanceRejected:
            continue
        made += 1
        ch = item["choices"]
        assert len(ch) == 5 and len(set(ch)) == 5
        correct_val = solver._parse(ch[item["correct_index"]])
        # the shown correct answer equals a fresh code computation of the spec
        recomputed = solver.solve_spec(item["provenance"]["answer_spec"])["value"]
        assert solver.values_equal(correct_val, recomputed)
        # no distractor equals the correct answer
        for i, c in enumerate(ch):
            if i != item["correct_index"]:
                assert not solver.values_equal(solver._parse(c), correct_val)
    assert made >= 10


@pytest.mark.parametrize("raw,clean", [
    # the reported artifacts
    (r"\( f(x) = 4x + (1) \)", r"\( f(x) = 4x + 1 \)"),
    (r"\( g(x) = 4x + (-2) \)", r"\( g(x) = 4x - 2 \)"),
    (r"\( \log_{2}(x - (-3)) = 2 \)", r"\( \log_{2}(x + 3) = 2 \)"),
    (r"\( \log_{2}(x - (4)) = 1 \)", r"\( \log_{2}(x - 4) = 1 \)"),
    (r"x^{3} + (-2)x^{2} + (-4)x + (8)", r"x^{3} - 2x^{2} - 4x + 8"),
    # opener-strip: parenthesized leading coefficient after \left( / = 
    (r"\left( (-2)x^{3} + (1)x^{2} \right)", r"\left( -2x^{3} + x^{2} \right)"),
    (r"x = (-3)", r"x = -3"),
    # coefficient 1 collapses only when multiplying a variable
    (r"\( 1x^{2} + 5 \)", r"\( x^{2} + 5 \)"),
    (r"\( -1x + 4 \)", r"\( -x + 4 \)"),
])
def test_tidy_math_cleans_artifacts(raw, clean):
    assert templates._tidy_math(raw) == clean


@pytest.mark.parametrize("text", [
    r"\( f(g(1)) \)",              # function-call parens are untouched
    r"\( r_1 r_2 r_3 \)",         # subscripts kept
    r"\( 41x + 10x \)",           # multi-digit numbers kept
    r"\( x^{1} \)",               # exponent 1 kept
    r"\( 1 \cdot 5 = 5 \)",       # standalone 1 and \cdot kept
    r"\( \frac{1}{2} \)",         # fraction 1 kept
    r"\( f(x) = 2x - 3 \)",       # already clean stays clean (idempotent)
])
def test_tidy_math_preserves_valid_latex(text):
    assert templates._tidy_math(text) == text


def test_tidy_math_is_idempotent():
    once = templates._tidy_math(r"\( 4x + (-2) + (1)y \)")
    assert templates._tidy_math(once) == once


@pytest.mark.parametrize("raw,clean", [
    # an added/subtracted zero renders as an ugly artifact -> drop the whole term
    ("3x + 0", "3x"),
    ("x - 0", "x"),
    ("3x + 0 = 0", "3x = 0"),           # only the additive 0 goes; the "= 0" side stays
    ("2x + (0)", "2x"),                 # _TIDY_OP first makes "+ (0)" -> "+ 0", then dropped
    ("x^2 - 0", "x^2"),
    (r"x^{2} - 0", r"x^{2}"),           # closing brace counts as a real term char
    (r"\( f(x) = 3x + 0 \)", r"\( f(x) = 3x \)"),
])
def test_tidy_math_drops_additive_zero(raw, clean):
    assert templates._tidy_math(raw) == clean


@pytest.mark.parametrize("text", [
    "x = 0",        # equation side: 0 not preceded by a +/- operator -> keep
    "= 0",          # bare equation side -> keep
    "10",           # 0 is part of a longer number -> keep
    "0.5x",         # 0 followed by a decimal point -> keep
    "x_0",          # subscript -> keep
    "(0, 3)",       # 0 not preceded by a +/- operator -> keep
    "3x + 0y",      # coefficient-zero-times-variable is out of scope -> keep unchanged
])
def test_tidy_math_keeps_non_additive_zero(text):
    assert templates._tidy_math(text) == text


@pytest.mark.parametrize("raw,clean", [
    # a bare negative substitution leaves two adjacent signs -> collapse to one
    ("y = 5x + -6", "y = 5x - 6"),
    ("y = 5x - -6", "y = 5x + 6"),
    ("3 + +2", "3 + 2"),
    ("3 - +2", "3 - 2"),
    (r"\( a = 2x + -3 \)", r"\( a = 2x - 3 \)"),
])
def test_tidy_math_collapses_double_signs(raw, clean):
    assert templates._tidy_math(raw) == clean


@pytest.mark.parametrize("text", [
    "x^-2",         # a single sign after an exponent, not a double sign -> keep
    "x - 2",        # a normal single subtraction -> keep
    "3 - 2",        # a normal single subtraction -> keep
])
def test_tidy_math_leaves_single_signs(text):
    assert templates._tidy_math(text) == text


@pytest.mark.parametrize("raw", [
    "3x + 0",
    "x - 0",
    "3x + 0 = 0",
    "2x + (0)",
    "x^2 - 0",
    "x = 0",
    "3x + 0y",
])
def test_tidy_math_zero_term_is_idempotent(raw):
    once = templates._tidy_math(raw)
    assert templates._tidy_math(once) == once


def test_instantiate_stem_has_no_paren_number_artifacts():
    # every seed of a paren-heavy template renders clean (no "+ (n)"/"- (n)")
    import re
    tmpl = BY_ID["remainder_theorem_v1"]
    art = re.compile(r"[+\-]\s*\(\s*[+-]?\d+\s*\)")
    for seed in range(30):
        try:
            item = templates.instantiate(tmpl, seed)
        except templates.InstanceRejected:
            continue
        assert not art.search(item["stem"]), item["stem"]


def test_numeric_slot_fusion_guard():
    # Author bug: a display field that glues a literal digit to a numeric slot
    # (`2[[n]]`, meaning 2*n) renders "21" for n=1 while the answer is computed
    # from 2*n=2 -> the shown question no longer matches its own answer. This must
    # fail LOUDLY (TemplateError), not silently ship glued math.
    base = {
        "template_id": "fuse_probe",
        "skill_id": "s",
        "topic_id": "t",
        "params": {"n": {"type": "int", "lo": 1, "hi": 3}},
        "answer_spec": {"op": "evaluate", "expr": "sqrt(3**(2*[[n]]))"},
        "distractors": ["[[answer]] + 1", "[[answer]] + 2", "[[answer]] - 1", "[[answer]] + 3", "[[answer]] + 4"],
        "solution": "The value is \\( [[answer]] \\).",
    }
    bad = dict(base, stem="Evaluate \\( \\sqrt{3^{2[[n]]}} \\).")
    with pytest.raises(templates.TemplateError):
        templates.instantiate(bad, seed=0)
    # Two adjacent numeric slots fuse too.
    bad2 = dict(base, stem="Evaluate \\( [[n]][[n]] \\).")
    with pytest.raises(templates.TemplateError):
        templates.instantiate(bad2, seed=0)
    # Making the product explicit with \cdot renders fine.
    good = dict(base, stem="Evaluate \\( \\sqrt{3^{2\\cdot[[n]]}} \\).")
    item = templates.instantiate(good, seed=0)
    assert "\\cdot" in item["stem"] and not templates._leftover_slots(item["stem"])


def test_determinism():
    tmpl = TEMPLATES[0]
    a = templates.instantiate(tmpl, 123)
    b = templates.instantiate(tmpl, 123)
    assert a == b


def test_regression_iterate_exact_numbers():
    # The exact item the old bank got wrong: f(x)=2x-1, x0=1, x3.  Truth = 1.
    item = templates.instantiate(
        BY_ID["iterate_affine_v1"], seed=0, params_override={"a": 2, "b": -1, "x0": 1, "n": 3}
    )
    assert item["choices"][item["correct_index"]] == "1"
    # and 1 must NOT appear as a distractor
    assert item["choices"].count("1") == 1


def test_faithfulness_gate_accepts_when_solver_agrees():
    # Injected "solver" that always lands on the code-correct choice -> faithful.
    def solve_ok(item):
        return item["correct_index"]
    rep = templates.check_faithfulness(BY_ID["iterate_affine_v1"], solve=solve_ok, n=5, samples=2)
    assert rep["faithful"] is True
    assert rep["agreed"] == rep["total"] > 0


def test_faithfulness_gate_rejects_when_solver_disagrees():
    # Injected "solver" that always lands on the WRONG choice -> template rejected.
    def solve_wrong(item):
        return (item["correct_index"] + 1) % templates.CHOICE_COUNT
    rep = templates.check_faithfulness(BY_ID["iterate_affine_v1"], solve=solve_wrong, n=5, samples=2)
    assert rep["faithful"] is False
    assert rep["agreed"] == 0


def test_regression_log_varies_and_correct():
    # log2(x+c)-log2(x)=1 -> x=c.  Check a couple concrete c values.
    for c in (3, 5, 7):
        item = templates.instantiate(
            BY_ID["log_diff_equation_v1"], seed=0, params_override={"c": c}
        )
        assert item["choices"][item["correct_index"]] == str(c)


def test_linear_system_derived_rhs_correct():
    # chosen solution (p,q)=(3,2); the RHS is derived so x must come out to 3.
    item = templates.instantiate(
        BY_ID["linear_system_v1"], seed=0,
        params_override={"p": 3, "q": 2, "a1": 1, "b1": 1, "a2": 1, "b2": -1},
    )
    assert "5" in item["stem"] and "1" in item["stem"]  # c1=5, c2=1
    assert item["choices"][item["correct_index"]] == "3"


def test_exponential_equation_correct():
    # 3^(x+1)=27 -> x=2.
    item = templates.instantiate(
        BY_ID["exponential_equation_v1"], seed=0, params_override={"base": 3, "c": 1, "k": 3}
    )
    assert "27" in item["stem"]
    assert item["choices"][item["correct_index"]] == "2"


def test_tidy_math_cleans_parenthesis_artifacts():
    # Display tidy-up: defensive parens around signed slots become clean math in the
    # rendered stem, WITHOUT ever altering function-call parens or multi-term groups.
    T = templates._tidy_math
    assert T("4x + (1)") == "4x + 1"
    assert T("4x + (-2)") == "4x - 2"          # + (-n) merges to - n
    assert T("3 + (-1)") == "3 - 1"            # the exact case the owner reported
    assert T("x - (-3)") == "x + 3"            # - (-n) merges to + n
    assert T("x - (5)") == "x - 5"
    assert T("= (-3)") == "= -3"               # redundant parens after "=" dropped
    assert T("1x + 2") == "x + 2"              # unit coefficient collapses
    # MUST preserve: function-call parens, LaTeX groups, multi-term parens, exponents.
    assert T("f(g(1))") == "f(g(1))"
    assert T("\\sin(-1)") == "\\sin(-1)"
    assert T("(15 - x)^{3}") == "(15 - x)^{3}"
    assert T("41x") == "41x"                   # not a unit coefficient
    assert T("x^1y") == "x^1y"                 # unbraced exponent, not a coefficient


def test_tidy_math_does_not_touch_choices_or_answer():
    # The tidy pass is display-only: choices stay sympy-ASCII (verify parses them) and
    # the code-computed answer is unchanged. Instantiate a template whose stem wraps a
    # negative slot and confirm the shown answer still equals a fresh SymPy computation.
    from seed_templates import TEMPLATES as SEED
    by = {t["template_id"]: t for t in SEED}
    item = templates.instantiate(by["iterate_affine_v1"], seed=5)
    recomputed = solver.solve_spec(item["provenance"]["answer_spec"])["value"]
    shown = solver._parse(item["choices"][item["correct_index"]])
    assert solver.values_equal(recomputed, shown)
    # no leftover "+ (" / "- (" bare-number artifact in the rendered stem
    import re as _re
    assert not _re.search(r"[+\-]\s*\(\s*[+-]?\d+\s*\)", item["stem"])


def test_sum_of_coefficients_correct():
    # (2x+3)^4 -> sum of coefficients = 5^4 = 625.
    item = templates.instantiate(
        BY_ID["sum_of_coefficients_v1"], seed=0, params_override={"a": 2, "b": 3, "n": 4}
    )
    assert item["choices"][item["correct_index"]] == "625"
