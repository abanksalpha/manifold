# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""template_author.py — the LLM "formulate" stage, behind a hard code gate.

An LLM proposes a parametric TEMPLATE for a skill (params, stem with [[slots]], a
machine-solvable answer-spec, distractor recipes). It NEVER supplies an answer.
Before a proposed template is accepted it must pass, deterministically:

  1. :func:`templates.validate` — instantiates N variants and checks each has 5
     distinct choices, no leftover slots, and the shown answer equals a fresh
     SymPy computation of the spec (answer-faithfulness), with enough clean
     instances; and
  2. :func:`templates.check_faithfulness` — an INDEPENDENT solver reads the
     rendered stems and must land on the code answer, catching a stem whose prose
     drifts from the spec.

Only a template that clears both gates is returned; otherwise :class:`AuthorRejected`
with the reasons (no silent acceptance; standing no-fabrication rule). Correctness
of served items is therefore code-computed, never LLM-asserted.

The model call is injectable: pass ``propose`` (skill -> raw template dict) in
tests; in production it is a structured-output OpenAI call. The faithfulness
solver is likewise injectable / configured to a strong reasoning model.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Callable

SCRIPT_DIR = __import__("pathlib").Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import templates as tmpl_engine  # noqa: E402


class AuthorError(Exception):
    """Malformed proposal / setup bug. Fail loud."""


class AuthorRejected(Exception):
    """A proposed template did not clear the correctness gates; not accepted."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


_REQUIRED = ("params", "stem", "answer_spec", "distractors")


def parse_template(raw: Any, skill: dict[str, Any]) -> dict[str, Any]:
    """Coerce an LLM proposal into a template, OWNING provenance from the skill
    (the model never sets skill_id/topic/tier). Structure-only; correctness is the
    gates' job."""
    if not isinstance(raw, dict):
        raise AuthorError(f"template proposal must be a JSON object, got {type(raw).__name__}")
    for k in _REQUIRED:
        if k not in raw:
            raise AuthorError(f"template proposal missing required key {k!r}")
    if not isinstance(raw["distractors"], list) or len(raw["distractors"]) < tmpl_engine.CHOICE_COUNT - 1:
        raise AuthorError(f"template needs >= {tmpl_engine.CHOICE_COUNT - 1} distractor recipes")
    return {
        "template_id": str(raw.get("template_id") or f"{skill['skill_id']}_auto"),
        "skill_id": skill["skill_id"],
        "topic_id": skill.get("topic_id", ""),
        "tier": skill.get("tier", "relearn"),
        "params": raw["params"],
        "constraints": raw.get("constraints", []),
        "derived": raw.get("derived", {}),
        "stem": raw["stem"],
        "answer_spec": raw["answer_spec"],
        "distractors": raw["distractors"],
        "solution": raw.get("solution", ""),
        "distractor_rationales": raw.get("distractor_rationales", []),
        "require_rational": raw.get("require_rational", True),
    }


def author_template(
    skill: dict[str, Any],
    *,
    propose: Callable[[dict[str, Any]], Any] | None = None,
    faithfulness_solve: Callable[[dict[str, Any]], Any] | None = None,
    faithfulness_config: Any = None,
    n: int = 30,
    min_ok: int = 15,
    min_distinct_stems: int = 5,
    faithfulness_n: int = 5,
    faithfulness_threshold: float = 0.8,
) -> dict[str, Any]:
    """Author ONE validated template for ``skill``, or raise :class:`AuthorRejected`.

    ``propose`` (or the real model) returns a raw template; both gates must pass.
    ``faithfulness_solve``/``faithfulness_config`` enable the independent stem check
    (skip only when neither is provided — then answer-faithfulness via validate()
    still holds)."""
    if propose is None:
        raise AuthorError("no 'propose' callable and no live author configured")
    raw = propose(skill)
    template = parse_template(raw, skill)

    reasons: list[str] = []
    try:
        rep = tmpl_engine.validate(template, n=n)
    except Exception as exc:  # a template that blows up validate() is not acceptable
        raise AuthorRejected([f"validate() raised: {type(exc).__name__}: {exc}"]) from exc
    if rep["errors"]:
        reasons.append(f"validate errors: {rep['errors'][:3]}")
    if rep["ok"] < min_ok:
        reasons.append(f"only {rep['ok']}/{n} clean instances (need >= {min_ok})")
    if rep["distinct_stems"] < min_distinct_stems:
        reasons.append(f"only {rep['distinct_stems']} distinct stems (need >= {min_distinct_stems})")

    if faithfulness_solve is not None or faithfulness_config is not None:
        frep = tmpl_engine.check_faithfulness(
            template, solve=faithfulness_solve, config=faithfulness_config,
            n=faithfulness_n, threshold=faithfulness_threshold,
        )
        if not frep["faithful"]:
            reasons.append(f"stem-faithfulness failed: {frep['agreed']}/{frep['total']} agreed")

    if reasons:
        raise AuthorRejected(reasons)
    return template


# --- real OpenAI proposer (structured template JSON) ----------------------------

_SCHEMA_HINT = """Return ONE JSON object describing a PARAMETRIC TEMPLATE. Do NOT include the answer.
Keys:
- "params": object mapping name -> {"type":"int","lo":<int>,"hi":<int>} or {"type":"choice","values":[...]}
- "constraints": array of predicate strings over params using [[name]] slots and
  Ne/Eq/Gt/Lt/Ge/Le/Mod, e.g. "Ne([[b]], 0)" (keeps numbers clean); may be []
- "derived": object name -> expression over params ([[slots]]) computed by code and
  shown in the stem (e.g. a right-hand side); may be {}
- "stem": the question text; write ALL math as LaTeX in \\( ... \\); put every number
  as a [[slot]] (params or derived). No answer in the stem.
- "answer_spec": a machine-solvable op-spec whose string fields use [[slots]]; op is one of
  solve/iterate/evaluate/diff/integrate/limit/vieta/system/sum (SymPy computes the answer)
- "distractors": >= 4 recipe strings over [[slots]] and [[answer]] (wrong-but-plausible values)
- "solution": optional worked-solution text with [[slots]] and [[answer]]
The stem MUST describe exactly what answer_spec computes."""


def _make_openai_proposer(model: str, api_key: str, base_url: str, timeout: float = 60.0):
    url = f"{base_url.rstrip('/')}/chat/completions"

    def propose(skill: dict[str, Any]) -> Any:
        prompt = (
            f"Author a GRE Mathematics practice-item TEMPLATE for the skill "
            f"'{skill.get('skill_name') or skill['skill_id']}' (topic {skill.get('topic_id')}).\n\n"
            + _SCHEMA_HINT
        )
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You author rigorous, machine-checkable math item templates. Output only JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise AuthorError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}") from exc
        content = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise AuthorError("author model returned no content")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AuthorError(f"author model output was not valid JSON: {exc}") from exc

    return propose


def make_live_proposer() -> Callable[[dict[str, Any]], Any]:
    """Build the real proposer from env (OPENAI_API_KEY, MANIFOLD_AUTHOR_MODEL)."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        raise AuthorError("OPENAI_API_KEY not set; cannot author live")
    model = os.environ.get("MANIFOLD_AUTHOR_MODEL") or "gpt-4o"
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    return _make_openai_proposer(model, key, base_url)
