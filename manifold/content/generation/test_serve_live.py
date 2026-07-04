# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for serve_live's draft gate — specifically the display-field LaTeX
contract added in Task 2 (delimited \\(...\\) / \\[...\\] math in the stem, worked
solution and distractor_rationales; sympy-ASCII choices left for verify.py).

Run with the generation venv (see ``verify.py`` header for how it was created)::

    manifold/content/generation/.venv/bin/python -m pytest \
        manifold/content/generation/test_serve_live.py -q

These tests are LLM-free: they exercise the pure, deterministic validators only.
pytest puts this file's directory on ``sys.path`` (no ``__init__.py`` here), so
``serve_live`` imports directly.
"""

from __future__ import annotations

import json

import pytest

import serve_live


# --- _validate_display_latex: the delimited-LaTeX contract ----------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Plain prose with no mathematics at all.",
        "The derivative is \\(2x + 3\\) at the point.",
        "By the chain rule, \\[\\frac{dz}{dx} = -\\frac{x}{z}.\\]",
        "Compare \\(\\sqrt{2}\\) with \\(\\frac{1}{2}\\) and \\(\\pi\\).",
        "The matrix \\(\\begin{bmatrix} 1 & 2 \\\\ 0 & 3 \\end{bmatrix}\\) is upper triangular.",
        "It costs \\$5 to enter.",  # an escaped literal dollar is fine
    ],
)
def test_display_latex_accepts_well_formed(text: str) -> None:
    assert serve_live._validate_display_latex("field", text) is None


@pytest.mark.parametrize(
    "text",
    [
        "The value is \\(2x + 3 at the point.",  # unclosed \(
        "The value is 2x + 3\\) at the point.",  # closing with no open
        "Mixed \\(2x + 3\\] here.",  # \( closed by \]
        "Nested \\(2x \\(y\\)\\) run.",  # a run opened inside a run
        "Unbalanced \\(\\frac{1}{2\\) braces.",  # missing }
        "Dollar math $2x + 3$ is banned.",  # $...$ math mode
        "A raw times glyph: \\(2 \u00d7 3\\).",  # Unicode math glyph
        "A raw radical: \u221a2 outside macros.",  # Unicode radical
        "Greek glyph \u03c0 instead of a macro.",  # Unicode pi
    ],
)
def test_display_latex_rejects_malformed(text: str) -> None:
    assert serve_live._validate_display_latex("field", text) is not None


# --- _validate_draft: display fields are LaTeX, choices stay ASCII ---------------


def _draft(**overrides) -> dict:
    """A structurally valid draft with LaTeX display fields and ASCII choices."""
    draft = {
        "stem": "What is the value of \\(2 \\cdot 3 + 4\\)?",
        "correct_choice": "10",
        "distractors": ["9", "11", "12", "13"],
        "distractor_rationales": [
            "Adding \\(2 + 3 + 4\\) instead of multiplying first gives \\(9\\).",
            "Off by one from a mis-added \\(6 + 4\\).",
            "Using \\(2 \\cdot 4\\) then \\(+ 4\\) gives \\(12\\).",
            "A doubled term gives \\(13\\).",
        ],
        "solution": "First \\(2 \\cdot 3 = 6\\), then \\(6 + 4 = 10\\).",
        "check": {"type": "numeric", "expr": "2*3 + 4"},
    }
    draft.update(overrides)
    return draft


def test_validate_draft_accepts_latex_display_and_ascii_choices() -> None:
    cleaned = serve_live._validate_draft(_draft())
    # Choices are returned verbatim as ASCII (verify.py parses these).
    assert cleaned["correct_choice"] == "10"
    assert cleaned["distractors"] == ["9", "11", "12", "13"]
    # Display fields keep their LaTeX delimiters untouched.
    assert "\\(" in cleaned["stem"]
    assert "\\(" in cleaned["solution"]


def test_validate_draft_rejects_unicode_glyph_in_stem() -> None:
    with pytest.raises(serve_live.GenerationError, match="display LaTeX in stem"):
        serve_live._validate_draft(_draft(stem="Compute \\(2 \u00d7 3\\)."))


def test_validate_draft_rejects_dollar_math_in_solution() -> None:
    with pytest.raises(serve_live.GenerationError, match="display LaTeX in solution"):
        serve_live._validate_draft(_draft(solution="We get $2 \\cdot 3 = 6$."))


def test_validate_draft_rejects_unclosed_delimiter_in_rationale() -> None:
    bad = _draft()
    bad["distractor_rationales"] = [
        "An unclosed \\(2 + 2 run.",
        "fine",
        "fine",
        "fine",
    ]
    with pytest.raises(serve_live.GenerationError, match="distractor_rationales"):
        serve_live._validate_draft(bad)


def test_validate_draft_does_not_constrain_choices_to_latex() -> None:
    # A choice that would be "malformed LaTeX" (a bare backslash-paren) is still
    # accepted, because choices are ASCII for the verifier, not display LaTeX.
    cleaned = serve_live._validate_draft(_draft(correct_choice="Rational(1, 3)"))
    assert cleaned["correct_choice"] == "Rational(1, 3)"


# --- _repair_math_escapes: heal LaTeX commands the model single-escaped -----------


def test_validate_draft_repairs_single_escaped_latex_command() -> None:
    """A model that double-escapes \\( \\) but single-escapes \\times: json.loads eats
    the ``\\t`` as a tab, so the stem parses as ``\\(3 <TAB>imes 2\\)``. The gate heals
    it back to \\times inside the math span rather than serving the tab or rejecting."""
    mangled = json.loads(r'"\\(3 \times 2^{x} = 48\\)"')
    assert "\t" in mangled  # precondition: the wound is present pre-repair
    cleaned = serve_live._validate_draft(_draft(stem=mangled))
    assert cleaned["stem"] == "\\(3 \\times 2^{x} = 48\\)"


def test_repair_math_escapes_preserves_prose_newlines() -> None:
    # \neq inside math is healed (NL+"eq" -> \neq); a real newline in prose is kept.
    src = json.loads(r'"See \\(a \neq b\\).\nThen continue."')
    assert serve_live._repair_math_escapes(src) == "See \\(a \\neq b\\).\nThen continue."
