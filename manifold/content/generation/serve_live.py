# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""serve_live.py — Manifold's runtime problem source: on-the-fly generation (D44).

**Owner directive D44 (supersedes the bank-first D6/D14/D28 and the bank-first
part of D38).** Every runtime *problem* is generated **live** per review. There is
**no persisted item bank as the runtime source**. The loop is:

    generate a candidate MCQ  ->  verify.verify()  ->  independent_solve  ->  serve iff both agree

Verification stays in the loop, unchanged and read-only: an item is served only if
:mod:`verify` (SymPy symbolic AND numeric / Z3 / exact brute force, no LLM in the
correctness path) proves exactly one of its five choices is correct and that it is
the claimed one. But :mod:`verify` only proves *check<->choice* consistency; for the
stated-value check types (``numeric``/``equiv``) the ``check.expr`` restates the
generator's own answer, so that pass is tautological w.r.t. the *stem*. To close that
hole a second, **independent** gate (:mod:`independent_solve`, D32 gate 5) blind-solves
the assembled item with a different/stronger model and must land on the same choice
before it is served. Generated content is never trusted, only verified AND cross-solved;
an item that cannot be independently confirmed is abstained, never served.

If generation or verification fails after a few retries, or the app is offline /
has no ``OPENAI_API_KEY``, this module **abstains honestly**: it returns an explicit
ABSTAIN result with a real reason. It **never** returns a fabricated or unverified
item and **never** falls back to a bank. Lectures remain pre-authored (the sole
exception to live generation) and are not touched here.

Public API::

    next_problem(skill)  ->  {"status": "ok", "item": {...}, ...}
                          |   {"status": "abstain", "reason": "...", "detail": "..."}

The model call is **injectable**. In production it is a direct structured-output
call to an OpenAI-compatible chat API (mirroring ``generate.ts``: same schema, same
machine-checkable ``check`` DSL and local pre-verify gate). The *live* path defaults
to a stronger gpt-4o-class model for yield (override with ``OPENAI_MODEL``), while the
offline bank build keeps the cheap-model-plus-SymPy-filter recipe (D33). For tests and
offline dev, point ``MANIFOLD_LIVE_FIXTURES`` at a JSON file of pre-authored drafts
(a deterministic **test double** that replaces only the model call — verify.py still
runs in the loop, so the no-fabrication invariant is preserved), or pass a
``generate`` callable directly to :func:`next_problem`.

Provenance is owned here, never by the model (AC22): ``skill_id`` / ``topic_id`` /
``tier_tag`` / ``source_ref`` come from the requested skill, and ``correct_index``
is placed at a **seeded, logged** position (determinism-where-it-matters, D28/D44).

Run with the generation venv (deps: sympy, mpmath, numpy, z3-solver — same venv as
``verify.py``; see its header)::

    # from a JSON request on stdin (how mediasrv calls it):
    echo '{"skill_id":"eigenvalues_of_an_explicit_small_matrix","topic_id":"eigen",
           "tier":"teach","skill_name":"Eigenvalues of a small matrix"}' \
      | manifold/content/generation/.venv/bin/python \
          manifold/content/generation/serve_live.py --request-json -

    # or with convenience flags (scripted check):
    manifold/content/generation/.venv/bin/python \
        manifold/content/generation/serve_live.py \
        --skill-id eigenvalues_of_an_explicit_small_matrix --topic-id eigen --tier teach
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
# verify.py / smt_check.py live beside this file; put their dir first on sys.path so
# ``import verify`` resolves regardless of CWD (verify.py does a bare ``import smt_check``).
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import independent_solve  # noqa: E402  (import after sys.path fix-up, by design)
import verify  # noqa: E402  (import after sys.path fix-up, by design)

# --- constants (kept in lockstep with generate.ts / verify.py) ------------------

# A stronger, gpt-4o-class default for the *live* path: on-the-fly yield matters
# more than per-item spend here (offline banking still uses the cheap recipe, D33).
# Override with --model / OPENAI_MODEL for a cheaper or different model.
DEFAULT_MODEL = "gpt-4o"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_ATTEMPTS = 7  # well-formed candidates that may reach the verifier before abstaining (D44)
DEFAULT_DIFFICULTY = "med"
DEFAULT_REQUEST_TIMEOUT = 45.0  # per model call, seconds
CHOICE_COUNT = 5
DISTRACTOR_COUNT = 4
# The verifier is the single source of truth for which check types are computable.
SUPPORTED_CHECK_TYPES = tuple(verify.SUPPORTED_TYPES)
# SMT sorts/logics the smt_check backend accepts (kept in lockstep with smt_check).
_SMT_SORTS = ("Int", "Real", "Bool")
_SMT_LOGICS = ("universal_subset", "satisfies")

# ABSTAIN reason codes (stable, surfaced to the UI). Never a fabricated item.
ABSTAIN_NO_KEY = "no_key"
ABSTAIN_OFFLINE = "offline"
ABSTAIN_UNVERIFIED = "unverified_after_retries"
ABSTAIN_GENERATION_ERROR = "generation_error"
ABSTAIN_NO_FIXTURE = "no_fixture"
# The model judged the skill has no machine-checkable computation (a proof, an
# interval, an English-label / graph-reading answer): an honest DEFER, not a bug.
ABSTAIN_NEEDS_CURATION = "needs_curation"
# A teach/"new" skill that is served from the pre-vetted bank has no banked item yet
# (a conceptual skill the pipeline could not verify). Honest gap, never generated live.
ABSTAIN_CONTENT_PENDING = "content_pending"


# --- errors ---------------------------------------------------------------------


class ConfigError(Exception):
    """A setup/programming error (bad request, malformed fixtures). Fails loudly."""


class AuthError(Exception):
    """The key was rejected (401/403). Retrying will not help; abstain as no_key."""


class TransientError(Exception):
    """A retryable network/server condition (offline, timeout, 429, 5xx)."""


class GenerationError(Exception):
    """The model produced a malformed / unusable draft (regenerate, don't count)."""


class NeedsCuration(Exception):
    """The model judged this skill has no machine-checkable check (honest defer)."""


class FixtureMiss(Exception):
    """The fixtures test double has no draft for this skill (deterministic: no retry)."""


# --- skill spec -----------------------------------------------------------------


def _normalize_skill(skill: dict[str, Any]) -> dict[str, Any]:
    """Validate and fill a skill request. ``skill_id`` is required (fail loudly)."""
    if not isinstance(skill, dict):
        raise ConfigError(f"skill must be an object, got {type(skill).__name__}")
    skill_id = skill.get("skill_id")
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise ConfigError("skill request is missing a non-empty 'skill_id'")
    skill_id = skill_id.strip()
    topic_id = (skill.get("topic_id") or "").strip()
    tier = (skill.get("tier") or "").strip()
    difficulty = (skill.get("difficulty") or DEFAULT_DIFFICULTY).strip()
    return {
        "skill_id": skill_id,
        "skill_name": (skill.get("skill_name") or skill_id).strip() or skill_id,
        "topic_id": topic_id,
        "topic_title": (skill.get("topic_title") or topic_id).strip(),
        "tier": tier,
        "difficulty": difficulty,
    }


def _source_ref(skill: dict[str, Any]) -> str:
    """An honest, traceable provenance string for a live-generated item (AC22).

    The named source is the skill's own place in Manifold's curriculum; the item was
    generated live for it and independently verified. Never blank (verify requires it).
    """
    topic = skill["topic_id"] or "unknown_topic"
    return f"manifold-live://{topic}/{skill['skill_id']}"


# --- display-field LaTeX gate (Task 2) ------------------------------------------
# The stem, worked solution and distractor_rationales are DISPLAY fields: the view
# typesets them directly (verify.py never sees them). Their contract is delimited
# LaTeX — math wrapped in \(...\) (inline) or \[...\] (display) — with prose left as
# prose. A malformed block would render as raw source, so a draft that violates the
# contract is a generator bug to REGENERATE (bounded), never to serve. Choices are
# NOT checked here: they stay sympy-ASCII so verify.py can parse them.

# Unicode math glyphs the prompt forbids: each must be written as a TeX macro so the
# MathJax path can typeset it. (A minus-sign glyph and a middle dot are included.)
_BANNED_MATH_UNICODE = "×÷√⋅·−∞≤≥≠→←↔∈∉⊂⊆∪∩∀∃∑∏∫√πθλαβγµσ°²³¹⁰√"
_UNESCAPED_DOLLAR = re.compile(r"(?<!\\)\$")


def _validate_display_latex(field: str, text: str) -> str | None:
    """Reason ``text`` violates the delimited-LaTeX display contract, or None.

    Checks (all cheap, no MathJax — that lives in JS): no ``$...$`` math mode, no raw
    Unicode math glyphs, and correctly paired, non-nested ``\\(...\\)`` / ``\\[...\\]``
    runs with balanced ``{ }`` braces inside each run. Pure prose (no delimiters, no
    banned glyphs) is always valid. Returns a human-readable reason on failure so the
    regenerate log is specific."""
    if _UNESCAPED_DOLLAR.search(text):
        return "uses $...$ math mode; wrap math in \\(...\\) or \\[...\\] instead"
    for ch in text:
        if ch in _BANNED_MATH_UNICODE:
            return f"contains the raw Unicode math glyph {ch!r}; write it as a TeX macro"
    i = 0
    n = len(text)
    open_delim: str | None = None  # None, "(", or "[" — the currently open math run
    run_start = 0
    while i < n:
        if text[i] == "\\" and i + 1 < n and text[i + 1] in "()[]":
            marker = text[i + 1]
            if marker in "([":
                if open_delim is not None:
                    return "a \\( or \\[ opened before the previous math run was closed"
                open_delim = marker
                run_start = i + 2
            else:  # a closing marker: ) or ]
                if open_delim is None:
                    return f"a closing \\{marker} with no matching \\( or \\["
                if (open_delim == "(") != (marker == ")"):
                    return "mismatched math delimiters (\\( closed by \\], or \\[ by \\))"
                run = text[run_start:i]
                if run.count("{") != run.count("}"):
                    return "unbalanced { } braces inside a math run"
                open_delim = None
            i += 2
            continue
        i += 1
    if open_delim is not None:
        return f"an unclosed \\{open_delim} ... math run"
    return None


# --- model draft (mirrors generate.ts ModelDraft + parseDraft) ------------------

# LaTeX commands whose backslash+letter is ALSO a valid JSON string escape
# (\t \n \r \b \f \v) are silently eaten when a model emits them with a SINGLE
# backslash: json.loads turns "\times" into TAB+"imes", "\neq" into NL+"eq", etc.
# Inside a math span such control chars are never legitimate, so restore each to its
# backslash form. Prose outside math (\(...\), \[...\], $...$) keeps real newlines.
_MATH_SPAN = re.compile(r"\\\(.*?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|\$.*?\$", re.DOTALL)
_CTRL_TO_LATEX = {"\t": r"\t", "\n": r"\n", "\r": r"\r", "\x08": r"\b", "\x0c": r"\f", "\x0b": r"\v"}


def _repair_math_escapes(obj: Any) -> Any:
    """Restore LaTeX commands mangled by JSON escape parsing, only inside math spans."""
    if isinstance(obj, str):
        if not any(ch in obj for ch in _CTRL_TO_LATEX):
            return obj

        def _fix(m: "re.Match[str]") -> str:
            span = m.group(0)
            for ch, cmd in _CTRL_TO_LATEX.items():
                span = span.replace(ch, cmd)
            return span

        return _MATH_SPAN.sub(_fix, obj)
    if isinstance(obj, dict):
        return {k: _repair_math_escapes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_repair_math_escapes(v) for v in obj]
    return obj


def _validate_draft(raw: Any) -> dict[str, Any]:
    """Coerce a model/fixture object into a servable draft, or classify the failure.

    Three outcomes, exactly mirroring ``generate.ts`` (``parseDraft`` +
    ``validateCheckBlock``) so a live draft is gated as strictly as an offline one:

    * a **malformed / structurally-unusable** draft (missing field, wrong choice
      count, or a ``check`` block whose *shape* would raise in the verifier) raises
      :class:`GenerationError` — a generator bug to REGENERATE, never counted as a
      real verify attempt and never allowed to reach (and crash) ``verify``;
    * a draft the model marks ``needs_curation`` (a proof, an interval, a graph or
      English-label answer with no machine-checkable computation) raises
      :class:`NeedsCuration` — an honest DEFER, not a bug;
    * otherwise a cleaned, machine-checkable draft is returned for verification.
    """
    if not isinstance(raw, dict):
        raise GenerationError(f"draft is not an object: {type(raw).__name__}")
    # Heal LaTeX commands the model single-escaped (\times -> TAB+imes) before the
    # display-LaTeX gate and typesetting see them.
    raw = _repair_math_escapes(raw)
    stem = raw.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        raise GenerationError("draft missing 'stem'")
    correct = raw.get("correct_choice")
    if not isinstance(correct, str) or not correct.strip():
        raise GenerationError("draft missing 'correct_choice'")
    distractors = raw.get("distractors")
    if (
        not isinstance(distractors, list)
        or len(distractors) != DISTRACTOR_COUNT
        or not all(isinstance(d, str) and d.strip() for d in distractors)
    ):
        raise GenerationError(f"draft 'distractors' must be exactly {DISTRACTOR_COUNT} non-empty strings")
    # distractor_rationales are wrong-answer FEEDBACK text, not part of the correctness
    # proof (verify + the independent cross-solve decide that). The model often returns
    # the wrong count; discarding an otherwise-valid item over it just burns the retry
    # budget, so normalize to exactly DISTRACTOR_COUNT instead (pad honestly, trim extra).
    raw_rationales = raw.get("distractor_rationales")
    rationales = [r for r in raw_rationales if isinstance(r, str) and r.strip()] if isinstance(raw_rationales, list) else []
    if len(rationales) < DISTRACTOR_COUNT:
        rationales = rationales + ["This option does not match the verified answer."] * (DISTRACTOR_COUNT - len(rationales))
    else:
        rationales = rationales[:DISTRACTOR_COUNT]
    solution = raw.get("solution")
    if not isinstance(solution, str) or not solution.strip():
        raise GenerationError("draft missing 'solution'")
    # An honest defer: the model says no rigorous machine-checkable check exists.
    if raw.get("needs_curation") is True:
        reason = raw.get("curation_reason") or "model flagged: no machine-checkable computation"
        raise NeedsCuration(str(reason))
    check = raw.get("check")
    if not isinstance(check, dict):
        raise GenerationError("draft missing a 'check' object (and did not set needs_curation)")
    # The check must be a supported type AND structurally well-formed, so a malformed
    # block is regenerated here rather than raising deep inside verify (a crash).
    shape_reason = _validate_check_block(check)
    if shape_reason is not None:
        raise GenerationError(f"malformed check: {shape_reason}")
    # Display fields must satisfy the delimited-LaTeX contract (Task 2) so the view
    # can typeset them directly instead of showing raw source. A violation is a
    # generator bug: regenerate it (bounded), never serve it. Choices are exempt
    # (sympy-ASCII for verify.py) and are checked by the verifier, not here.
    for _fname, _fval in (("stem", stem.strip()), ("solution", solution.strip())):
        _latex_reason = _validate_display_latex(_fname, _fval)
        if _latex_reason is not None:
            raise GenerationError(f"malformed display LaTeX in {_fname}: {_latex_reason}")
    for _idx, _r in enumerate(rationales):
        _latex_reason = _validate_display_latex(f"distractor_rationales[{_idx}]", _r)
        if _latex_reason is not None:
            raise GenerationError(
                f"malformed display LaTeX in distractor_rationales[{_idx}]: {_latex_reason}"
            )
    trimmed = [correct.strip(), *[d.strip() for d in distractors]]
    if len(set(trimmed)) != CHOICE_COUNT:
        raise GenerationError("correct answer and distractors are not all distinct")
    return {
        "stem": stem.strip(),
        "correct_choice": correct.strip(),
        "distractors": [d.strip() for d in distractors],
        "distractor_rationales": [str(r) for r in rationales],
        "solution": solution.strip(),
        "check": check,
    }


# --- local check-block validation (mirrors generate.ts validateCheckBlock) -------
# Returns a human-readable reason when the check block would raise downstream
# (unsupported type, missing/misshaped fields), or None when it is structurally
# sound. Content-level rejects (undecidable, no_correct, wrong value) are NOT judged
# here; those are the trusted verifier's job. Keeping this in lockstep with
# generate.ts is what took its pipeline_error count to zero.


def _looks_like_tuple(expr: str) -> bool:
    return bool(re.match(r"^\s*\(.*,.*\)\s*$", expr))


def _require_expr(check: dict[str, Any], field: str) -> str | None:
    value = check.get(field)
    if not isinstance(value, str) or not value.strip():
        return f"{field} must be a non-empty string"
    if _looks_like_tuple(value):
        return f"{field} looks like a tuple/coordinate pair; use a scalar expression or a different check type"
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_matrix(check: dict[str, Any], square: bool) -> str | None:
    matrix = check.get("matrix")
    if not isinstance(matrix, list) or not matrix:
        return "matrix must be a non-empty list of rows"
    first = matrix[0]
    width = len(first) if isinstance(first, list) else 0
    if width == 0:
        return "matrix rows must be non-empty lists"
    for row in matrix:
        if not isinstance(row, list) or len(row) != width:
            return "matrix rows have unequal or invalid length"
        for entry in row:
            if not _is_number(entry) and not isinstance(entry, str):
                return "matrix entries must be numbers or numeric strings"
    if square and len(matrix) != width:
        return f"matrix must be square, got {len(matrix)}x{width}"
    return None


def _validate_brute_vars(vars_: Any) -> str | None:
    if not isinstance(vars_, dict) or not vars_:
        return "brute.vars must be a non-empty object of name -> [lo, hi]"
    for name, rng in vars_.items():
        if not isinstance(rng, list) or len(rng) != 2 or not all(_is_number(n) and math.isfinite(n) for n in rng):
            return f"brute.vars['{name}'] must be a [lo, hi] pair of integers (no 'step' keys)"
    return None


def _validate_count(check: dict[str, Any]) -> str | None:
    has_expr = isinstance(check.get("expr"), str) and check["expr"].strip() != ""
    has_brute = isinstance(check.get("brute"), dict)
    if not has_expr and not has_brute:
        return "count needs 'expr' and/or 'brute'"
    if has_brute:
        brute = check["brute"]
        reason = _validate_brute_vars(brute.get("vars"))
        if reason:
            return reason
        if not isinstance(brute.get("predicate"), str) or not brute["predicate"].strip():
            return "count brute needs a 'predicate' string"
    return None


def _validate_prob(check: dict[str, Any]) -> str | None:
    has_expr = isinstance(check.get("expr"), str) and check["expr"].strip() != ""
    has_brute = isinstance(check.get("brute"), dict)
    if not has_expr and not has_brute:
        return "prob_exact needs 'expr' and/or 'brute'"
    if has_brute:
        brute = check["brute"]
        reason = _validate_brute_vars(brute.get("vars"))
        if reason:
            return reason
        if not isinstance(brute.get("event"), str) or not brute["event"].strip():
            return "prob_exact brute needs an 'event' string"
    return None


def _validate_smt(check: dict[str, Any]) -> str | None:
    vars_ = check.get("vars")
    if not isinstance(vars_, dict) or not vars_:
        return "smt needs a non-empty 'vars' map"
    for name, sort in vars_.items():
        if not isinstance(sort, str) or sort not in _SMT_SORTS:
            return f"smt var '{name}' has unsupported sort {sort!r}; use {'/'.join(_SMT_SORTS)}"
    logic = check.get("logic")
    if logic == "universal_subset":
        statements = check.get("statements")
        if not isinstance(statements, dict) or not statements:
            return "universal_subset needs a non-empty 'statements' object (name -> formula)"
        for name, formula in statements.items():
            if not isinstance(formula, str) or not formula.strip():
                return f"statement '{name}' must be a non-empty formula string"
        choice_sets = check.get("choice_sets")
        if not isinstance(choice_sets, list) or len(choice_sets) != CHOICE_COUNT:
            return f"universal_subset needs 'choice_sets' with exactly {CHOICE_COUNT} entries"
        known = set(statements)
        for i, names in enumerate(choice_sets):
            if not isinstance(names, list):
                return f"choice_sets[{i}] must be a list of statement names"
            for nm in names:
                if nm not in known:
                    return f"choice_sets[{i}] names unknown statement {nm!r}"
        hyps = check.get("hypotheses")
        if hyps is not None and (not isinstance(hyps, list) or not all(isinstance(h, str) for h in hyps)):
            return "smt 'hypotheses' must be a list of strings"
        return None
    if logic == "satisfies":
        choice_values = check.get("choice_values")
        if not isinstance(choice_values, dict) or not choice_values:
            return "satisfies needs a non-empty 'choice_values' map (var -> 5 values)"
        declared = set(vars_)
        for name, values in choice_values.items():
            if name not in declared:
                return f"choice_values names undeclared variable {name!r}"
            if not isinstance(values, list) or len(values) != CHOICE_COUNT:
                return f"choice_values['{name}'] must list exactly {CHOICE_COUNT} values"
        constraints = check.get("constraints")
        if constraints is not None and (
            not isinstance(constraints, list) or not all(isinstance(c, str) for c in constraints)
        ):
            return "smt 'constraints' must be a list of strings"
        return None
    return f"unsupported smt logic {logic!r}; use {' or '.join(_SMT_LOGICS)}"


def _validate_check_block(check: Any) -> str | None:
    """Structural gate for a ``check`` block; None means well-formed enough to verify."""
    if not isinstance(check, dict):
        return "check is not an object"
    check_type = check.get("type")
    if not isinstance(check_type, str) or check_type not in SUPPORTED_CHECK_TYPES:
        return f"check.type {check_type!r} is not one of {', '.join(SUPPORTED_CHECK_TYPES)}"
    if check_type in ("equiv", "numeric"):
        return _require_expr(check, "expr")
    if check_type == "antiderivative":
        reason = _require_expr(check, "integrand")
        if reason:
            return reason
        if check.get("var") is not None and not isinstance(check.get("var"), str):
            return "antiderivative 'var' must be a string"
        return None
    if check_type in ("eigen", "det"):
        return _validate_matrix(check, True)
    if check_type == "rank":
        return _validate_matrix(check, False)
    if check_type == "count":
        return _validate_count(check)
    if check_type == "prob_exact":
        return _validate_prob(check)
    if check_type == "smt":
        return _validate_smt(check)
    return f"unsupported check.type {check_type!r}"


# --- assembly (owns provenance + a seeded, logged correct_index) ----------------


def _assemble_item(
    skill: dict[str, Any], draft: dict[str, Any], *, seed: int, attempt: int
) -> tuple[dict[str, Any], int]:
    """Place the correct answer at a seeded position and stamp provenance.

    Mirrors ``generate.ts`` assembleItem: the correct choice goes at a seeded index,
    distractors fill the other slots in order, and ``distractor_rationales`` stay in
    distractor order (so the view maps a wrong pick back by discounting the correct
    slot). Returns the item plus the concrete index seed used (logged, D28/D44).
    """
    index_seed = (seed * 1_000_003 + attempt * 97 + (hash(skill["skill_id"]) & 0xFFFF)) & 0x7FFFFFFF
    rng = random.Random(index_seed)
    correct_index = rng.randrange(CHOICE_COUNT)
    choices: list[str] = []
    d = 0
    for i in range(CHOICE_COUNT):
        if i == correct_index:
            choices.append(draft["correct_choice"])
        else:
            choices.append(draft["distractors"][d])
            d += 1
    item = {
        "stem": draft["stem"],
        "choices": choices,
        "correct_index": correct_index,
        "solution": draft["solution"],
        "distractor_rationales": draft["distractor_rationales"],
        "source_ref": _source_ref(skill),
        "topic_id": skill["topic_id"],
        "skill_id": skill["skill_id"],
        "tier_tag": f"mf::tier::{skill['tier']}" if skill["tier"] else "mf::tier::unknown",
        "check": draft["check"],
        "generator": {
            "stage": "serve_live.py",
            "seed": index_seed,
            "attempt": attempt,
            "correct_index_source": "seeded_prng(random.Random)",
        },
    }
    return item, index_seed


# --- OpenAI generator (mirrors generate.ts prompt + schema) ---------------------

# The exact DSL verify.py / smt_check.py consume (kept faithful to generate.ts so a
# live draft is as verifiable as an offline-banked one).
_CHECK_DSL = """Every item needs a machine-checkable "check" block so an external SymPy/Z3 verifier
can recompute the answer and confirm exactly one choice is correct. Pick the "type"
that matches the problem's actual computation:
- equiv: {"type":"equiv","expr":"<sympy expr>"} - exactly one choice is symbolically
  equal to expr. Use for algebraic identities and closed forms that may contain a
  symbol, e.g. "n*(n+1)/2" or "factorial(n)". Choices are sympy strings (** for powers).
- numeric: {"type":"numeric","expr":"<closed-form number>"} - one choice equals the
  number. expr and every choice must be a pure NUMBER with no free variable, e.g.
  "sin(pi/6)", "Rational(2,3)", "11". If the answer is a formula in a variable (like
  "n*(n-1)/2"), use equiv instead; if it is an asymptotic big-O class, set
  needs_curation. To keep an operation-count numeric, instantiate the variable to a
  concrete value so both expr and every choice are plain numbers.
- antiderivative: {"type":"antiderivative","integrand":"<sympy>","var":"x"} - one
  choice differentiates back to the integrand (the constant of integration is ignored).
- eigen: {"type":"eigen","matrix":[[..],[..]]} - one choice lists the eigenvalue
  multiset, e.g. "2, 3". Matrix entries are plain numbers.
- det: {"type":"det","matrix":[[..],[..]]} - one choice equals the determinant.
- rank: {"type":"rank","matrix":[[..],[..]]} - one choice equals the integer rank.
- count: {"type":"count","expr":"<sympy integer>","brute":{"vars":{"i":[lo,hi],..},
  "predicate":"<sympy bool>"}} - the closed form and an exact brute-force enumeration
  must agree, and one choice equals the count. Give BOTH expr and brute when you can.
  Every counted object must be an INTEGER inside its [lo, hi] range. To count real
  roots or critical / inflection points, engineer the function so all such points are
  integers and test them with Eq(poly, 0); if any root is irrational, set
  needs_curation rather than a brute that would miss it.
- prob_exact: {"type":"prob_exact","expr":"Rational(a,b)","brute":{"vars":{"a":[lo,hi],
  ..},"event":"<sympy bool>"}} - closed form and favorable/total brute force must agree;
  one choice equals the probability.
- smt: for "which of I/II/III must be true" or "which listed value satisfies ...". Two
  shapes only:
  * universal_subset: {"type":"smt","logic":"universal_subset","vars":{"n":"Int"},
    "statements":{"I":"n*n >= 0","II":"n >= 0"},"choice_sets":[["I"],["I","II"],[],
    ["II"],["I","II"]]}. statements is an OBJECT mapping a name to a formula.
    choice_sets has exactly 5 entries, each a list of statement names; the correct
    choice's set equals the set of statements true for every model.
  * satisfies: {"type":"smt","logic":"satisfies","vars":{"x":"Int"},
    "constraints":["x*x == 2*x","x > 0"],"choice_values":{"x":["0","2","1","-2","4"]}}.
    choice_values maps each declared variable to exactly 5 values (one per choice); the
    correct choice makes every constraint hold.

Hard rules for every expression, predicate, and formula string:
- Plain SymPy only: ** for powers, "/" for division, pi, sqrt, factorial(n),
  binomial(n,k). Rational(a,b) takes INTEGER a and b only, so write "n*(n+1)/2", never
  "Rational(n*(n+1),2)".
- Every choice for numeric/count/prob/det/rank/eigen is a number or a list of numbers:
  never a word ("eight"), never big-O like "O(n**2)", never a coordinate pair.
- In count/prob predicates and events, write equality as Eq(a, b) because a == b
  silently reduces to False; combine with And/Or/Not; reference only the declared
  integer variables. Each variable is one [lo, hi] integer range: bake any step into
  the predicate, never add "step" keys.
- Never reference an undefined function such as f(x), f'(x), or g(x) in a check, and
  never write plain-language or Python-style code (no ".subs(...)", no bare "and").
- Matrix entries are plain numbers, not symbols.
- equiv's expr is the ANSWER ITSELF, never a derivative, an intermediate quantity, or a
  condition. For "find the inflection point" the expr is the x-value "1", not "6*x - 6".
- DIRECT-COMPUTATION EXCEPTION (do this whenever it applies): when the stem literally
  gives an expression to evaluate, simplify, or compute, set expr to THAT WHOLE GIVEN
  EXPRESSION, not the final number. E.g. for "Evaluate (2*3)+(4^2)-(sqrt(16)/2)" use
  expr "(2*3)+(4**2)-(sqrt(16)/2)". The verifier then does the arithmetic itself and
  confirms exactly one choice equals the result, so it catches a wrong answer key even
  when you miscompute. Only write the final number as expr when the answer is not a
  single transcribable expression of the given quantities.
- Prefer equiv for an EXACT closed form (a radical like "sqrt(2)/2", a fraction, a
  symbolic expression): it checks symbolic AND numeric equality, so it is more robust
  than numeric for irrational exact answers. Reserve numeric for plain rational/decimal
  numbers.
- The check must recompute the SAME value that correct_choice states, and NO distractor
  may equal that value. If correct_choice is "450", use expr "450", not the
  intermediate "225". Engineer clean numbers so no calculator is needed.

If a skill has no such machine-checkable computation (a proof, a graph-reading task,
an asymptotic big-O classification, a real-root or critical-point count whose roots are
not integers, a "verify that a condition holds" task, or an answer that is an interval
or an English label), set "needs_curation": true with a short "curation_reason" instead
of forcing a check. An honestly deferred skill beats a fabricated or bogus check."""

_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "stem": {"type": "string"},
        "correct_choice": {"type": "string"},
        "distractors": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
        "distractor_rationales": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
            "maxItems": 4,
        },
        "solution": {"type": "string"},
        "check": {
            "type": "object",
            "properties": {"type": {"type": "string", "enum": list(SUPPORTED_CHECK_TYPES)}},
            "required": ["type"],
        },
        "needs_curation": {"type": "boolean"},
        "curation_reason": {"type": "string"},
    },
    "required": ["stem", "correct_choice", "distractors", "distractor_rationales", "solution"],
}


def _system_prompt() -> str:
    return "\n".join(
        [
            "You are an expert GRE Mathematics Subject Test item writer.",
            "Write ONE multiple-choice item for the given problem-type skill and difficulty.",
            "",
            "Hard requirements:",
            "- The stem is self-contained and does NOT reveal the answer.",
            "- Provide exactly ONE correct answer and FOUR distinct, plausible distractors.",
            "- Distractors encode real misconceptions (off-by-one, sign error, wrong rule), and NONE of",
            "  them may equal the correct answer's value.",
            "- SOLUTION-SET WORDING: if the equation/problem has MORE THAN ONE solution, ask 'Which of",
            "  the following is A solution of ...?' (indefinite) — never 'the solution' / 'the value',",
            "  which falsely implies a unique answer. Reserve 'the solution' for problems that truly have",
            "  a single solution. Either way EXACTLY ONE listed choice must be correct, and no distractor",
            "  may be another valid solution (even an unlisted one must not collide with a distractor).",
            "- Give a correct worked solution whose final result matches the correct answer.",
            "- Numbers are engineered to be clean and solvable with no calculator.",
            "- Where the content is mathematical, write choices as sympy-parseable strings (use ** for",
            "  powers, pi, sqrt, Rational(a,b) with integer a and b, factorial, binomial).",
            "- Do NOT number the choices or add 'A)'/'B)'. Return bare answer strings.",
            "- In the stem, the worked solution, and EVERY distractor_rationale, write ALL mathematics as",
            "  LaTeX inside delimiters: \\( ... \\) for inline math and \\[ ... \\] for a displayed equation.",
            "  Use standard TeX macros (\\frac{a}{b}, \\sqrt{x}, x^{2}, \\cdot, \\pi, \\sin, \\le, \\to,",
            "  \\begin{bmatrix}...\\end{bmatrix}); keep ordinary words as plain prose OUTSIDE the delimiters.",
            "  Do NOT use $...$ math mode, and do NOT paste raw Unicode math glyphs (no x as a times sign, no",
            "  middle dot, no radical sign, no superscript digits, no minus-sign glyph, no <=/>= glyphs, no",
            "  Greek letters as glyphs) — write each as its TeX macro. For a literal dollar sign write \\$.",
            "  Every \\( must close with \\) and every \\[ with \\], with balanced { } braces; a malformed or",
            "  unwrapped block is regenerated, so it never reaches the learner.",
            "- The CHOICES are the ONE exception: keep them as sympy-parseable ASCII (** for powers, pi, sqrt,",
            "  Rational(a,b), factorial, binomial) with NO LaTeX and NO \\( \\) delimiters, because an external",
            "  SymPy verifier parses them. The app typesets the choices for display on its own.",
            "",
            "Pick the check TYPE from the problem's real computation, not habit: use equiv for exact",
            "closed forms and radicals, the matrix/count/prob/eigen types for those computations, and",
            "smt for 'which must be true' / 'which value satisfies'. If the honest answer is an interval,",
            "a set, an English label, a proof, or a graph reading, set needs_curation instead of forcing",
            "a numeric check that the verifier will reject.",
            "",
            _CHECK_DSL,
            "",
            "Self-consistency is mandatory: the check must recompute exactly the correct answer, and an",
            "external SymPy/Z3 verifier must find that exactly one choice is correct. If you cannot express",
            "a rigorous, self-consistent check for this skill, set needs_curation rather than guessing.",
        ]
    )


def _user_prompt(skill: dict[str, Any], difficulty: str) -> str:
    return "\n".join(
        [
            f"Skill: {skill['skill_name']}",
            f"Skill id: {skill['skill_id']}   Topic: {skill['topic_id']}   Tier: {skill['tier']}",
            f"Difficulty: {difficulty}",
            "",
            "Return the item as structured JSON matching the schema. Prefer a rigorous check",
            "that matches the computation; use needs_curation only when no machine-checkable",
            "check exists.",
        ]
    )


def _make_openai_generator(cfg: "ServeConfig") -> Callable[[dict[str, Any], str], dict[str, Any]]:
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"

    def generate(skill: dict[str, Any], difficulty: str) -> dict[str, Any]:
        body = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(skill, difficulty)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "manifold_item", "schema": _RESPONSE_SCHEMA, "strict": False},
            },
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.request_timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            if exc.code in (401, 403):
                raise AuthError(f"HTTP {exc.code}: {text[:200]}") from exc
            if exc.code == 429 or exc.code >= 500:
                raise TransientError(f"HTTP {exc.code}: {text[:200]}") from exc
            raise GenerationError(f"HTTP {exc.code}: {text[:200]}") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise TransientError(f"network error: {exc}") from exc
        content = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise GenerationError("model returned no content")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"model output was not valid JSON: {exc}") from exc
        return _validate_draft(parsed)

    return generate


# --- fixtures generator (test double: replaces ONLY the model call) -------------


def _load_fixtures(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"MANIFOLD_LIVE_FIXTURES points to a missing file: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"MANIFOLD_LIVE_FIXTURES is not valid JSON ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"MANIFOLD_LIVE_FIXTURES must be a JSON object ({path})")
    return data


def _make_fixture_generator(fixtures: dict[str, Any]) -> Callable[[dict[str, Any], str], dict[str, Any]]:
    by_skill = fixtures.get("by_skill") or {}
    default = fixtures.get("default")
    if not isinstance(by_skill, dict):
        raise ConfigError("fixtures 'by_skill' must be an object")

    def generate(skill: dict[str, Any], difficulty: str) -> dict[str, Any]:
        raw = by_skill.get(skill["skill_id"], default)
        if raw is None:
            raise FixtureMiss(
                f"no fixture draft for skill {skill['skill_id']!r} and no 'default' draft"
            )
        # _validate_draft may raise GenerationError for a deliberately malformed draft;
        # that is a legitimate "unverifiable this round" outcome the test may exercise.
        return _validate_draft(raw)

    return generate


# --- config ---------------------------------------------------------------------

# serve_live runs as a mediasrv subprocess that only inherits the app's environment;
# in a packaged app there is no shell to source .env. Fill ONLY unset OPENAI_*/
# MANIFOLD_* vars from the nearest .env (a real env var always wins; a missing .env
# is a no-op and the caller then abstains honestly). Mirrors hint.py's loader.
_DOTENV_PREFIXES = ("OPENAI_", "MANIFOLD_")
_dotenv_loaded = False


def _apply_dotenv(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key.startswith(_DOTENV_PREFIXES) and key not in os.environ:
            os.environ[key] = value


def _load_dotenv_into_env() -> None:
    """Load the nearest .env (walking up from this file) once, filling unset keys."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    for parent in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            _apply_dotenv(candidate)
            return


class ServeConfig:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        fixtures_path: str | None,
        request_timeout: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.fixtures_path = fixtures_path
        self.request_timeout = request_timeout

    @classmethod
    def from_env(cls) -> "ServeConfig":
        _load_dotenv_into_env()
        key = os.environ.get("OPENAI_API_KEY")
        fixtures = os.environ.get("MANIFOLD_LIVE_FIXTURES")
        return cls(
            api_key=key.strip() if key and key.strip() else None,
            model=os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL,
            base_url=os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL,
            fixtures_path=fixtures.strip() if fixtures and fixtures.strip() else None,
            request_timeout=DEFAULT_REQUEST_TIMEOUT,
        )


def _select_generator(
    cfg: ServeConfig,
) -> tuple[Callable[[dict[str, Any], str], dict[str, Any]] | None, str | None]:
    """Choose the generation source, or return (None, abstain_reason).

    Explicit precedence, no silent fallback: fixtures (test double) if set, else the
    real model if a key is present, else abstain as ``no_key``.
    """
    if cfg.fixtures_path:
        return _make_fixture_generator(_load_fixtures(cfg.fixtures_path)), None
    if cfg.api_key:
        return _make_openai_generator(cfg), None
    return None, ABSTAIN_NO_KEY


# --- results --------------------------------------------------------------------


def _ok(item: dict[str, Any], report: dict[str, Any], attempt: int, seed: int) -> dict[str, Any]:
    served = {k: item[k] for k in (
        "stem",
        "choices",
        "correct_index",
        "solution",
        "distractor_rationales",
        "source_ref",
        "topic_id",
        "skill_id",
        "tier_tag",
    )}
    return {
        "status": "ok",
        "item": served,
        "verifier_report": report,
        "attempts": attempt,
        "seed": seed,
    }


def _abstain(reason: str, detail: str, attempts: int) -> dict[str, Any]:
    return {"status": "abstain", "reason": reason, "detail": detail, "attempts": attempts}


# --- teach ("new") bank: pre-vetted problems served instead of live generation ---
# Owner directive (2026-07-02): teach-tier skills are served from a pre-generated,
# 100%-working bank (build_teach_bank.py: verify.py AND independent cross-solve). Every
# OTHER tier is generated on the fly. A teach skill absent from the bank is an honest
# content gap (abstain content_pending), never silently generated live.

_TEACH_BANK_PATH = os.environ.get("MANIFOLD_TEACH_BANK") or str(SCRIPT_DIR / "teach_bank.json")
_TEACH_BANK_CACHE: dict[str, list[dict[str, Any]]] | None = None


def _load_teach_bank() -> dict[str, list[dict[str, Any]]]:
    """Index the teach bank as skill_id -> [records], cached. Missing file = empty."""
    global _TEACH_BANK_CACHE
    if _TEACH_BANK_CACHE is not None:
        return _TEACH_BANK_CACHE
    index: dict[str, list[dict[str, Any]]] = {}
    path = Path(_TEACH_BANK_PATH)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data.get("items") if isinstance(data, dict) else data
        for rec in records or []:
            item = rec.get("item") if isinstance(rec, dict) else None
            sid = (rec.get("skill_id") if isinstance(rec, dict) else None) or (item or {}).get("skill_id")
            if isinstance(item, dict) and sid:
                index.setdefault(sid, []).append(rec)
    _TEACH_BANK_CACHE = index
    return index


def _serve_from_teach_bank(skill: dict[str, Any], *, seed: int | None) -> dict[str, Any] | None:
    """Return an _ok-shaped result from a banked teach item, or None if none exists.

    The banked item already passed verify.py AND the independent cross-solve at build
    time, so serving it preserves the no-fabrication invariant without a live call."""
    records = _load_teach_bank().get(skill["skill_id"])
    if not records:
        return None
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    rec = rng.choice(records)
    item = rec["item"]
    served = {k: item[k] for k in (
        "stem", "choices", "correct_index", "solution", "distractor_rationales",
        "source_ref", "topic_id", "skill_id", "tier_tag",
    ) if k in item}
    return {
        "status": "ok",
        "item": served,
        "verifier_report": rec.get("verifier_report"),
        "source": "teach_bank",
        "item_id": rec.get("item_id"),
    }


# --- template serving: deterministically-correct parametric items ---------------
# Computational skills are served from validated parametric templates: the answer
# is computed by SymPy (solver.py), never asserted by an LLM, and the numbers are
# resampled every review. This is preferred over live generation wherever a
# template exists, because live generation (LLM asserts the answer, a correlated
# LLM confirms it) can serve wrong items; a template cannot.

_TEMPLATE_INDEX: dict[str, list[dict[str, Any]]] | None = None


def _load_template_index() -> dict[str, list[dict[str, Any]]]:
    """skill_id -> [templates], from seed_templates.py plus an optional authored
    template_bank.json. Cached. A load failure is logged, never fabricated away."""
    global _TEMPLATE_INDEX
    if _TEMPLATE_INDEX is not None:
        return _TEMPLATE_INDEX
    idx: dict[str, list[dict[str, Any]]] = {}
    try:
        import seed_templates
        for t in seed_templates.TEMPLATES:
            idx.setdefault(t["skill_id"], []).append(t)
    except Exception as exc:  # a bad seed module is a bug to surface, not to hide
        _log(f"template index: could not load seed_templates: {exc}")
    bank_path = Path(os.environ.get("MANIFOLD_TEMPLATE_BANK") or (SCRIPT_DIR / "template_bank.json"))
    if bank_path.is_file():
        try:
            data = json.loads(bank_path.read_text(encoding="utf-8"))
            for t in (data.get("templates") if isinstance(data, dict) else data) or []:
                idx.setdefault(t["skill_id"], []).append(t)
        except Exception as exc:
            _log(f"template bank {bank_path}: {exc}")
    _TEMPLATE_INDEX = idx
    return idx


def _serve_from_template(skill: dict[str, Any], *, seed: int | None) -> dict[str, Any] | None:
    """Return an _ok-shaped result from a parametric template, or None if this skill
    has no template. The instance is code-computed and cannot carry a wrong answer."""
    tmpls = _load_template_index().get(skill["skill_id"])
    if not tmpls:
        return None
    import templates as tmpl_engine

    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    for _ in range(8):  # a few tries to dodge an occasional rejected instance
        t = rng.choice(tmpls)
        try:
            item = tmpl_engine.instantiate(t, rng.randrange(2**31))
        except tmpl_engine.InstanceRejected:
            continue
        served = {k: item[k] for k in (
            "stem", "choices", "correct_index", "solution", "distractor_rationales",
            "source_ref", "topic_id", "skill_id", "tier_tag",
        )}
        return {"status": "ok", "item": served, "source": "template", "template_id": t["template_id"]}
    return None


# --- deterministic arithmetic re-solve (closes the correlated-LLM-error hole) ----
# verify.py is tautological for a stated-value numeric check (expr = the generator's
# own claimed answer), and the blind cross-solver is itself an LLM that can make the
# SAME arithmetic slip — so a plain "Evaluate the expression <E>" item can be served
# with a WRONG key when both models miscompute (owner-observed: 3^3 + 2*4^2 - 15/3 = 54
# served as 56). This is a DETERMINISTIC guard: when the stem literally asks to evaluate
# ONE self-contained, closed-form numeric expression, recompute it with SymPy straight
# from the stem and reject the item if it disagrees with the claimed correct choice.
# It fires ONLY when it can parse a pure number (no free variables, no unsupported
# macros, exactly one delimited run), so it never false-rejects a parametric or
# non-arithmetic item; when it cannot decide it returns None and verify + cross-solve
# remain the gate (no silent pass, no fabricated confidence).

_EVAL_TRIGGERS = ("evaluate", "compute", "simplify", "value of", "result of", "equivalent")
_MATH_RUN = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", re.DOTALL)
# Standalone i / I / e / E are ambiguous (imaginary unit / Euler's number vs a plain
# variable), so the symbolic recompute skips any expression containing one, rather than
# risk a false reject on e.g. "Evaluate i^23".
_AMBIG_CONST = re.compile(r"(?<![A-Za-z])[iIeE](?![A-Za-z])")


def _latex_to_sympy(latex: str) -> str:
    """Convert the small LaTeX grammar the generator emits into a SymPy string."""
    s = latex.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\cdot", "*").replace("\\times", "*").replace("\\div", "/")
    s = s.replace("\\pi", "pi")
    frac = re.compile(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
    while frac.search(s):
        s = frac.sub(r"((\1)/(\2))", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\sqrt\s*([0-9A-Za-z])", r"sqrt(\1)", s)
    s = re.sub(r"\^\s*\{([^{}]*)\}", r"**(\1)", s)
    s = re.sub(r"\^\s*(-?[0-9A-Za-z])", r"**\1", s)
    return s.strip()


def _arithmetic_stem_check(item: dict[str, Any]) -> str | None:
    """Reason the claimed answer contradicts a deterministically-recomputed stem, or None.

    For an evaluate/compute/simplify/"equivalent to" stem containing ONE self-contained
    expression, this recomputes the expression from the STEM with SymPy — NUMERIC *and*
    SYMBOLIC (so "simplify (2x^3)^2 * (x^4)^{1/2}" is checked, not just pure-number
    arithmetic) — and rejects the item when the claimed choice is provably NOT equivalent.
    It is the non-LLM backstop for the tautological verify + LLM cross-solve. It rejects
    ONLY when SymPy is certain they differ (``expr.equals`` returns False); any ambiguity
    (imaginary unit, unparseable, undecidable) returns None and leaves the verdict to
    verify + the blind cross-solve — never a false reject, never a fabricated pass."""
    stem = item.get("stem", "")
    if not any(t in stem.lower() for t in _EVAL_TRIGGERS):
        return None
    runs = [a or b for a, b in _MATH_RUN.findall(stem)]
    if len(runs) != 1:  # ambiguous which expression is "the answer": don't guess
        return None
    sy = _latex_to_sympy(runs[0])
    if "\\" in sy or _AMBIG_CONST.search(sy):  # unsupported macro / ambiguous constant
        return None
    choices = item.get("choices") or []
    idx = item.get("correct_index")
    if not isinstance(idx, int) or not (0 <= idx < len(choices)):
        return None
    claimed_raw = str(choices[idx])
    if _AMBIG_CONST.search(claimed_raw):
        return None
    try:
        import sympy
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )

        tx = standard_transformations + (convert_xor, implicit_multiplication_application)
        stem_expr = parse_expr(sy, transformations=tx)
        claimed = parse_expr(claimed_raw, transformations=tx)
    except Exception:
        return None  # unparseable either side -> no deterministic verdict, no-op
    try:
        equal = stem_expr.equals(claimed)  # True / False / None (symbolic + numeric)
    except Exception:
        return None
    if equal is False:
        try:
            simplified = sympy.simplify(stem_expr)
        except Exception:
            simplified = stem_expr
        return f"stem simplifies to {simplified}, but the claimed answer {claimed_raw} is not equivalent"
    return None


# --- one gated candidate (runnable concurrently) --------------------------------


def _try_candidate(
    skill: dict[str, Any],
    gen: Callable[[dict[str, Any], str], dict[str, Any]],
    solve_cfg: "independent_solve.SolveConfig",
    solve_fn: Callable[[dict[str, Any]], int],
    solve_samples: int | None,
    seed: int,
    attempt: int,
) -> dict[str, Any]:
    """Run ONE candidate through the FULL gated pipeline and return a tagged outcome.

    Gates are identical to the sequential path (generate -> assemble -> verify.py ->
    deterministic arithmetic re-check -> blind cross-solve); ``"ok"`` is returned only
    when every gate passes. The ordinary failure classes are returned as tags rather
    than raised, so this can be run concurrently and its results aggregated by the
    driver without changing any correctness guarantee."""
    try:
        draft = gen(skill, skill["difficulty"])
    except FixtureMiss as exc:
        return {"kind": "fixture_miss", "detail": str(exc)}
    except AuthError as exc:
        return {"kind": "auth", "detail": f"the API key was rejected: {exc}"}
    except NeedsCuration as exc:
        return {"kind": "needs_curation", "detail": str(exc)}
    except TransientError as exc:
        return {"kind": "transient", "detail": str(exc)}
    except GenerationError as exc:
        return {"kind": "gen_error", "detail": str(exc)}
    item, item_seed = _assemble_item(skill, draft, seed=seed, attempt=attempt)
    try:
        verified, report = verify.verify(item)
    except Exception as exc:  # a shape-valid check that still raises = generator bug
        return {"kind": "gen_error", "detail": f"verifier raised: {type(exc).__name__}: {exc}"}
    if not verified:
        return {"kind": "verify_reject", "reason": report.get("reason")}
    stem_reason = _arithmetic_stem_check(item)
    if stem_reason is not None:
        return {"kind": "verify_reject", "reason": f"arithmetic_stem_mismatch: {stem_reason}"}
    try:
        verdict = independent_solve.check_agreement(
            item, config=solve_cfg, solve=solve_fn, samples=solve_samples
        )
    except independent_solve.SolverAuthError as exc:
        return {"kind": "auth", "detail": f"independent solver unavailable: {exc}"}
    except independent_solve.SolverTransientError as exc:
        return {"kind": "transient", "detail": f"independent solver transient: {exc}"}
    except independent_solve.SolverProtocolError as exc:
        return {"kind": "transient", "detail": f"independent solver protocol error: {exc}"}
    if verdict["agreed"]:
        return {"kind": "ok", "item": item, "report": {**report, "independent_solve": verdict}, "seed": item_seed}
    return {"kind": "verify_reject", "reason": f"independent_solver_disagreed: {verdict['reason']}"}


# --- the runtime entry point ----------------------------------------------------


def next_problem(
    skill: dict[str, Any],
    *,
    generate: Callable[[dict[str, Any], str], dict[str, Any]] | None = None,
    attempts: int = DEFAULT_ATTEMPTS,
    config: ServeConfig | None = None,
    seed: int | None = None,
    solve: Callable[[dict[str, Any]], int] | None = None,
    solve_config: "independent_solve.SolveConfig | None" = None,
    solve_samples: int | None = None,
) -> dict[str, Any]:
    """Generate one candidate live, verify it, cross-solve it, and serve iff both
    the verifier and an independent blind solver agree on the answer (D44, D32).

    Returns ``{"status": "ok", "item": {...}, ...}`` with a verified + cross-solved
    item, or ``{"status": "abstain", "reason": ..., "detail": ...}`` when none could be
    produced (no key, offline, unverifiable, or the independent solver disagreed after
    ``attempts`` tries). Never returns a fabricated, unverified, or unconfirmed item;
    never falls back to a bank.
    """
    skill = _normalize_skill(skill)
    cfg = config or ServeConfig.from_env()

    # Template-FIRST for EVERY tier (D-fix 2026-07-03, extended to teach): on the real
    # runtime path, a computational skill is served from a validated parametric template
    # whose answer is computed by SymPy (solver.py) and whose numbers are resampled per
    # review. This is preferred over BOTH the teach bank and the correlated-LLM live path
    # because a template cannot carry a wrong answer, while the old LLM-writes-and-confirms
    # path banked ~15-20% wrong items. Hermetic tests inject a generator / fixtures and
    # deliberately bypass this whole block.
    if generate is None and cfg.fixtures_path is None:
        served = _serve_from_template(skill, seed=seed)
        if served is not None:
            return served

    # Owner directive: a teach/"new" skill with NO template is served from the pre-vetted
    # bank (conceptual skills the template engine cannot express), NOT generated live. A
    # teach skill absent from both the templates and the bank is an honest content gap
    # (abstain), never silently generated live.
    if generate is None and cfg.fixtures_path is None and skill.get("tier") == "teach":
        served = _serve_from_teach_bank(skill, seed=seed)
        if served is not None:
            return served
        return _abstain(
            ABSTAIN_CONTENT_PENDING,
            "this 'new' (teach) skill has no verified template or banked problem yet; teach "
            "content is pre-generated and vetted, so this is an honest gap rather than a live "
            "generation.",
            attempts=0,
        )

    gen = generate
    if gen is None:
        gen, reason = _select_generator(cfg)
        if gen is None:
            return _abstain(
                reason or ABSTAIN_NO_KEY,
                "OPENAI_API_KEY is not set and no fixtures were provided, so no problem can "
                "be generated. Set the key (see .env.example) or provide MANIFOLD_LIVE_FIXTURES.",
                attempts=0,
            )

    # Independent cross-solve gate (D32 gate 5), built once. A candidate that verifies
    # but cannot be independently confirmed must NOT be served — resolve the solver up
    # front so a missing confirmation source is an honest abstain, not a silent pass.
    solve_cfg = solve_config or independent_solve.SolveConfig.from_env()
    solve_fn = solve
    if solve_fn is None:
        solve_fn, _solve_reason = independent_solve.select_solver(solve_cfg)
        if solve_fn is None:
            return _abstain(
                ABSTAIN_NO_KEY,
                "a candidate could be generated but not independently confirmed: there is "
                "no OPENAI_API_KEY and no MANIFOLD_SOLVE_FIXTURES for the cross-solve gate. "
                "Refusing to serve an unconfirmed item (D32).",
                attempts=0,
            )

    if seed is None:
        seed = random.SystemRandom().randrange(2**31)

    # Budgets (D44). Only a well-formed, machine-checkable draft consumes the real
    # ``attempts`` retry budget by reaching the verifier. Everything else is bounded
    # separately so wasted work never eats those retries and a broken model can never
    # spin forever:
    #   - a malformed draft (or one that makes the verifier raise) is a generator bug:
    #     REGENERATE it, capped by ``max_regens`` — it is not counted as an attempt;
    #   - a transient network failure backs off, capped by ``max_transient``;
    #   - a skill the model repeatedly flags ``needs_curation`` is an honest DEFER
    #     after a small confirmation (``max_curation``), not a bogus forced check.
    max_regens = max(attempts, 4)
    max_transient = 4
    max_curation = 2

    verify_attempts = 0
    regens = 0
    transient = 0
    curation_flags = 0
    last_verify_reason: str | None = None
    last_gen_detail: str | None = None
    curation_detail: str | None = None

    # Absolute guard so no combination of failures can loop unbounded.
    safety_cap = attempts + max_regens + max_transient + max_curation + 2
    iterations = 0

    # Candidates run in bounded-parallel BATCHES (MANIFOLD_PARALLEL_CANDIDATES, default
    # 3) instead of one-at-a-time. Latency was dominated by the sequential generate ->
    # verify -> cross-solve rounds on low-yield skills; a batch overlaps those LLM calls,
    # and the FIRST candidate that passes ALL gates wins. Correctness is unchanged: every
    # candidate goes through the identical verify + deterministic arithmetic re-check +
    # blind cross-solve gates (`_try_candidate`); a wrong item can never win. Set
    # MANIFOLD_PARALLEL_CANDIDATES=1 to fall back to the strict sequential behavior.
    from concurrent.futures import ThreadPoolExecutor

    try:
        parallel = max(1, int(os.environ.get("MANIFOLD_PARALLEL_CANDIDATES") or "3"))
    except ValueError:
        parallel = 3
    attempt_no = 0

    while verify_attempts < attempts:
        iterations += 1
        if iterations > safety_cap:
            break
        batch = max(1, min(parallel, attempts - verify_attempts))
        with ThreadPoolExecutor(max_workers=batch) as pool:
            futures = [
                pool.submit(
                    _try_candidate, skill, gen, solve_cfg, solve_fn, solve_samples,
                    seed, attempt_no + i + 1,
                )
                for i in range(batch)
            ]
            outcomes = [f.result() for f in futures]
        attempt_no += batch

        # A candidate that passed ALL gates ends it immediately (first winner wins).
        winners = [o for o in outcomes if o["kind"] == "ok"]
        if winners:
            best = winners[0]
            verify_attempts += sum(1 for o in outcomes if o["kind"] in ("ok", "verify_reject"))
            _log(
                f"VERIFIED + cross-solved (parallel batch of {batch}, seed={best['seed']}, "
                f"check={best['report'].get('check_type')})"
            )
            return _ok(best["item"], best["report"], verify_attempts, best["seed"])

        # No winner in this batch: fold each outcome into the honest budgets. A hard
        # deterministic failure (bad/absent key, missing fixture) abstains at once.
        transient_before = transient
        for o in outcomes:
            kind = o["kind"]
            if kind == "auth":
                return _abstain(ABSTAIN_NO_KEY, o["detail"], verify_attempts)
            if kind == "fixture_miss":
                return _abstain(ABSTAIN_NO_FIXTURE, o["detail"], verify_attempts)
            if kind == "needs_curation":
                curation_flags += 1
                curation_detail = o["detail"]
            elif kind == "transient":
                transient += 1
                last_gen_detail = o["detail"]
            elif kind == "gen_error":
                regens += 1
                last_gen_detail = o["detail"]
            elif kind == "verify_reject":
                verify_attempts += 1
                last_verify_reason = o["reason"]
                _log(f"verify-attempt {verify_attempts} rejected: {last_verify_reason}")
        if curation_flags >= max_curation:
            return _abstain(ABSTAIN_NEEDS_CURATION, curation_detail or str(last_gen_detail), verify_attempts)
        if transient > max_transient or regens > max_regens:
            break
        if transient > transient_before:
            time.sleep(0.4 * transient)  # back off rate limits before the next batch

    # No verified item within budget: abstain with the most specific honest reason.
    if last_verify_reason is not None:
        return _abstain(
            ABSTAIN_UNVERIFIED,
            f"generated {verify_attempts} machine-checkable candidate(s); none passed "
            f"verification (last reason: {last_verify_reason})",
            verify_attempts,
        )
    if transient > 0:
        return _abstain(
            ABSTAIN_OFFLINE,
            f"could not reach the model after {transient} attempt(s): {last_gen_detail}",
            verify_attempts,
        )
    if curation_flags > 0:
        return _abstain(
            ABSTAIN_NEEDS_CURATION,
            curation_detail or "model flagged this skill as needing curated content",
            verify_attempts,
        )
    return _abstain(
        ABSTAIN_GENERATION_ERROR,
        f"could not produce a machine-checkable draft after {regens} regeneration(s): {last_gen_detail}",
        verify_attempts,
    )


def _log(message: str) -> None:
    """Diagnostics go to stderr so stdout stays a single clean JSON result."""
    print(f"serve_live: {message}", file=sys.stderr)


# --- warm daemon: keep sympy + the banks loaded across requests -----------------
# Shelling out a fresh Python per problem re-imports sympy/z3 and re-parses the
# template bank every time (~0.3s of pure cold-start), which dominates a template
# serve whose actual work is milliseconds. The daemon loads all of that ONCE, then
# serves the deterministic fast path (templates + teach bank) per request over
# stdin/stdout so a templated problem returns near-instantly. A skill that needs
# live LLM generation returns {"status":"needs_live"}; the caller runs the cold
# path for it, so live-generation correctness and concurrency are unchanged.


def serve_deterministic(skill: dict[str, Any]) -> dict[str, Any] | None:
    """The no-LLM fast path: a template instance (fresh numbers, SymPy-computed) or
    a banked teach item. Returns an _ok-shaped result, a ``content_pending`` abstain
    for a teach skill with no content, or ``None`` when the skill needs live
    generation (which the caller handles on the cold path)."""
    skill = _normalize_skill(skill)
    # In a hermetic test run the live-fixture double is the intended content
    # source; defer to the cold fixture path (which honors it) instead of serving
    # real templates from this fast path, so the e2e is deterministic. Production
    # never sets this, so the template/bank fast path is unchanged there.
    if os.environ.get("MANIFOLD_LIVE_FIXTURES"):
        return None
    served = _serve_from_template(skill, seed=None)
    if served is not None:
        return served
    if skill.get("tier") == "teach":
        served = _serve_from_teach_bank(skill, seed=None)
        if served is not None:
            return served
        return _abstain(
            ABSTAIN_CONTENT_PENDING,
            "this 'new' (teach) skill has no verified template or banked problem yet; "
            "teach content is pre-generated and vetted, so this is an honest gap.",
            attempts=0,
        )
    return None


def run_daemon() -> int:
    """Serve the deterministic fast path over stdin/stdout, one JSON request per line.

    Emits a ``{"status":"ready"}`` line once warmed, then for each request line a
    single JSON result line (``ok`` / ``abstain`` / ``needs_live`` / ``error``)."""
    import templates as _warm  # noqa: F401  (pulls in solver -> sympy, warmed once)

    _load_template_index()
    _load_teach_bank()
    sys.stdout.write(json.dumps({"status": "ready"}) + "\n")
    sys.stdout.flush()
    # readline() one at a time: iterating `for line in sys.stdin` reads ahead into a
    # buffer and would stall this request/response protocol.
    while True:
        raw = sys.stdin.readline()
        if not raw:  # EOF: the parent closed the pipe (app shutting down)
            break
        raw = raw.strip()
        if not raw:
            continue
        try:
            skill = json.loads(raw)
            result = serve_deterministic(skill)
            if result is None:
                result = {"status": "needs_live"}
        except ConfigError as exc:
            result = {"status": "error", "detail": str(exc)}
        except Exception as exc:  # a malformed template is a bug to surface, not hang
            result = {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


# --- CLI ------------------------------------------------------------------------


def _read_request(source: str) -> dict[str, Any]:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    if not raw.strip():
        raise ConfigError("empty request (expected a JSON skill object)")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"request is not valid JSON: {exc}") from exc
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Serve one live-generated, verified Manifold problem, or abstain (D44)."
    )
    parser.add_argument(
        "--request-json",
        help="path to a JSON skill request, or '-' to read it from stdin (how mediasrv calls it)",
    )
    parser.add_argument("--skill-id", help="skill id (convenience alternative to --request-json)")
    parser.add_argument("--skill-name", default=None)
    parser.add_argument("--topic-id", default=None)
    parser.add_argument("--topic-title", default=None)
    parser.add_argument("--tier", default=None)
    parser.add_argument("--difficulty", default=None)
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--serve-daemon",
        action="store_true",
        help="run as a warm daemon serving the deterministic fast path over stdin/stdout",
    )
    args = parser.parse_args(argv)

    if args.serve_daemon:
        return run_daemon()

    try:
        if args.request_json:
            skill = _read_request(args.request_json)
        elif args.skill_id:
            skill = {
                "skill_id": args.skill_id,
                "skill_name": args.skill_name,
                "topic_id": args.topic_id,
                "topic_title": args.topic_title,
                "tier": args.tier,
                "difficulty": args.difficulty,
            }
        else:
            parser.error("provide --request-json or --skill-id")
            return 2
        result = next_problem(skill, attempts=args.attempts, seed=args.seed)
    except ConfigError as exc:
        # A real setup/programming error: fail loudly (non-zero), never a fake item.
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # An ABSTAIN is a valid runtime outcome, not a CLI failure: emit it on stdout, exit 0.
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
