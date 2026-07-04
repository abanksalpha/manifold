# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for hint.py — the on-demand problem-hint assistant.

LLM-free: they exercise the pure request/validation/abstain logic and the fixtures
test double only (the model call is injected or replaced). No network, no key, no
heavy deps (hint.py is stdlib only). pytest puts this file's directory on
``sys.path`` (no ``__init__.py`` here), so ``hint`` imports directly.

Run with the generation venv (see ``verify.py`` header for how it was created)::

    manifold/content/generation/.venv/bin/python -m pytest \
        manifold/content/generation/test_hint.py -q
"""

from __future__ import annotations

import os

import hint
import pytest


def _request(**overrides: object) -> dict:
    req: dict = {
        "stem": "Two fair dice are rolled. What is P(sum = 5)?",
        "choices": ["1/9", "1/12", "1/6", "2/9", "5/36"],
        "question": "Where do I start?",
        "skill_id": "dice_sum",
        "skill_name": "Dice sum probability",
        "topic_title": "Probability",
    }
    req.update(overrides)
    return req


# --- request normalization ------------------------------------------------------


def test_normalize_requires_stem() -> None:
    with pytest.raises(hint.ConfigError):
        hint._normalize_request(_request(stem="   "))


def test_normalize_requires_question() -> None:
    with pytest.raises(hint.ConfigError):
        hint._normalize_request(_request(question=""))


def test_normalize_rejects_non_object() -> None:
    with pytest.raises(hint.ConfigError):
        hint._normalize_request(["not", "a", "dict"])


def test_normalize_clamps_question_and_history() -> None:
    long_q = "x" * (hint.MAX_QUESTION_CHARS + 500)
    history = [
        {"question": f"q{i}", "hint": f"h{i}"}
        for i in range(hint.MAX_HISTORY_TURNS + 5)
    ]
    req = hint._normalize_request(_request(question=long_q, history=history))
    assert len(req["question"]) <= hint.MAX_QUESTION_CHARS + len(" ...")
    # Only the most recent turns are kept, in order.
    assert len(req["history"]) == hint.MAX_HISTORY_TURNS
    assert req["history"][-1]["question"] == f"q{hint.MAX_HISTORY_TURNS + 4}"


def test_normalize_drops_bad_choices_and_history_turns() -> None:
    req = hint._normalize_request(
        _request(
            choices=["1/9", "", 5, "1/6"],
            history=[
                {"question": "q", "hint": ""},  # incomplete: dropped
                "nope",  # not an object: dropped
                {"question": "keep", "hint": "kept"},
            ],
        )
    )
    assert req["choices"] == ["1/9", "1/6"]
    assert req["history"] == [{"question": "keep", "hint": "kept"}]


# --- prompts never carry the answer ---------------------------------------------


def test_user_prompt_carries_context_but_no_answer_key() -> None:
    req = hint._normalize_request(_request())
    prompt = hint._user_prompt(req)
    assert "P(sum = 5)" in prompt
    assert "Where do I start?" in prompt
    # The correct index / worked solution are never sent to the hinter.
    assert "correct_index" not in prompt
    assert "solution" not in prompt.lower()


def test_system_prompt_forbids_revealing_the_answer() -> None:
    sp = hint._system_prompt()
    assert "Never state the final answer" in sp
    assert "\\(" in sp  # instructs the delimited-LaTeX display contract


# --- coerce_hint ----------------------------------------------------------------


def test_coerce_hint_accepts_string_and_object() -> None:
    assert hint._coerce_hint("a nudge") == "a nudge"
    assert hint._coerce_hint({"hint": "  spaced  "}) == "spaced"


def test_coerce_hint_rejects_empty() -> None:
    with pytest.raises(hint.HintError):
        hint._coerce_hint("   ")
    with pytest.raises(hint.HintError):
        hint._coerce_hint({"hint": ""})


def test_coerce_hint_truncates_overlong() -> None:
    out = hint._coerce_hint("y" * (hint.MAX_HINT_CHARS + 100))
    assert len(out) <= hint.MAX_HINT_CHARS + len(" ...")


# --- get_hint end to end (injected generator / config) --------------------------


def _cfg(**kw: object) -> hint.HintConfig:
    base: dict = dict(
        api_key=None, model="m", base_url="u", fixtures_path=None, request_timeout=1.0
    )
    base.update(kw)
    return hint.HintConfig(**base)


def test_get_hint_ok_with_injected_generator() -> None:
    result = hint.get_hint(
        _request(),
        generate=lambda req: "Recall the definition, then set up \\(a+b=5\\).",
    )
    assert result["status"] == "ok"
    assert "\\(" in result["hint"]


def test_get_hint_abstains_without_key_or_fixtures() -> None:
    result = hint.get_hint(_request(), config=_cfg())
    assert result["status"] == "abstain"
    assert result["reason"] == hint.ABSTAIN_NO_KEY


def test_get_hint_raises_on_malformed_request() -> None:
    with pytest.raises(hint.ConfigError):
        hint.get_hint({"question": "hi"})  # missing stem


def test_get_hint_retries_then_abstains_on_transient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hint.time, "sleep", lambda _s: None)
    calls = {"n": 0}

    def flaky(_req: dict) -> str:
        calls["n"] += 1
        raise hint.TransientError("boom")

    result = hint.get_hint(_request(), generate=flaky, attempts=2)
    assert result["status"] == "abstain"
    assert result["reason"] == hint.ABSTAIN_OFFLINE
    assert calls["n"] == 2


def test_get_hint_abstains_on_unusable_output() -> None:
    def empty(_req: dict) -> str:
        raise hint.HintError("empty reply")

    result = hint.get_hint(_request(), generate=empty, attempts=2)
    assert result["status"] == "abstain"
    assert result["reason"] == hint.ABSTAIN_HINT_ERROR


def test_get_hint_abstains_on_auth_rejection() -> None:
    def rejected(_req: dict) -> str:
        raise hint.AuthError("HTTP 401")

    result = hint.get_hint(_request(), generate=rejected)
    assert result["status"] == "abstain"
    assert result["reason"] == hint.ABSTAIN_NO_KEY


# --- fixtures double ------------------------------------------------------------


def test_fixture_hinter_default_and_by_skill() -> None:
    gen = hint._make_fixture_hinter(
        {"default": "default nudge", "by_skill": {"dice_sum": "skill nudge"}}
    )
    assert gen(hint._normalize_request(_request(skill_id="dice_sum"))) == "skill nudge"
    assert gen(hint._normalize_request(_request(skill_id="other"))) == "default nudge"


def test_fixture_hinter_miss_raises() -> None:
    gen = hint._make_fixture_hinter({"by_skill": {}})
    with pytest.raises(hint.FixtureMiss):
        gen(hint._normalize_request(_request(skill_id="x")))


# --- .env loading ---------------------------------------------------------------


def test_apply_dotenv_fills_unset_but_never_overrides(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# a comment",
                "OPENAI_API_KEY=sk-from-dotenv",
                'OPENAI_MODEL="gpt-4o"',
                "export MANIFOLD_HINT_MODEL=gpt-4o-mini",
                "IGNORED_VAR=should-not-load",  # outside the OPENAI_/MANIFOLD_ prefixes
                "malformed line with no equals",
            ]
        ),
        encoding="utf-8",
    )
    # A key already in the environment must win over .env.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-env")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("MANIFOLD_HINT_MODEL", raising=False)
    monkeypatch.delenv("IGNORED_VAR", raising=False)

    hint._apply_dotenv(env_file)

    assert os.environ["OPENAI_API_KEY"] == "sk-real-env"  # not overridden
    assert os.environ["OPENAI_MODEL"] == "gpt-4o"  # quotes stripped
    assert os.environ["MANIFOLD_HINT_MODEL"] == "gpt-4o-mini"  # export prefix handled
    assert "IGNORED_VAR" not in os.environ  # non-whitelisted key left alone


def test_from_env_reads_key_from_dotenv(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-dotenv-only\n", encoding="utf-8")
    monkeypatch.setattr(hint, "SCRIPT_DIR", tmp_path)
    monkeypatch.setattr(hint, "_dotenv_loaded", False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MANIFOLD_HINT_FIXTURES", raising=False)

    cfg = hint.HintConfig.from_env()
    assert cfg.api_key == "sk-dotenv-only"
