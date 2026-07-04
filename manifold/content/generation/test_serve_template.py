# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Wiring tests: serve_live serves computational skills from validated parametric
templates (deterministically-correct) on the real path, and never fabricates for
an untemplated skill without a key."""

import json

import serve_live

TEMPLATED = {
    "skill_id": "self_composition_iteration_fixed_points",
    "topic_id": "precalc_functions",
    "tier": "relearn",
    "skill_name": "Self-composition / iteration",
}


def _clean_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MANIFOLD_LIVE_FIXTURES", raising=False)
    monkeypatch.delenv("MANIFOLD_TEMPLATE_BANK", raising=False)
    serve_live._TEMPLATE_INDEX = None  # reset cache so the index reloads


def test_serves_from_template_without_any_llm(monkeypatch):
    _clean_env(monkeypatch)
    res = serve_live.next_problem(dict(TEMPLATED), seed=42)
    assert res["status"] == "ok"
    assert res.get("source") == "template"
    item = res["item"]
    assert len(item["choices"]) == 5 and len(set(item["choices"])) == 5
    assert 0 <= item["correct_index"] < 5
    assert item["skill_id"] == TEMPLATED["skill_id"]


def test_template_serving_is_deterministic(monkeypatch):
    _clean_env(monkeypatch)
    a = serve_live.next_problem(dict(TEMPLATED), seed=7)
    b = serve_live.next_problem(dict(TEMPLATED), seed=7)
    assert a == b


def test_untemplated_skill_abstains_without_key(monkeypatch):
    _clean_env(monkeypatch)
    res = serve_live.next_problem(
        {"skill_id": "no_such_skill_xyz", "topic_id": "t", "tier": "relearn", "skill_name": "x"},
        seed=1,
    )
    assert res["status"] == "abstain"  # honest gap, never a fabricated item


def test_teach_skill_with_template_serves_from_template_not_bank(monkeypatch, tmp_path):
    # The routing change: a teach-tier COMPUTATIONAL skill that has a validated
    # template must serve from the template (deterministic, code-computed answer),
    # NOT fall through to the pre-vetted teach bank.
    _clean_env(monkeypatch)
    tmpl = {
        "template_id": "unit_test_teach_v1",
        "skill_id": "unit_test_teach_skill",
        "topic_id": "combinatorics",
        "tier": "teach",
        "params": {"n": {"type": "int", "lo": 4, "hi": 9}},
        "constraints": [],
        "stem": "Compute \\( [[n]]! \\).",
        "answer_spec": {"op": "evaluate", "expr": "factorial([[n]])"},
        "distractors": [
            "factorial([[n]]) + 1", "factorial([[n]]) - 1",
            "factorial([[n]]) + 2", "factorial([[n]]) - 2", "factorial([[n]]) + 6",
        ],
    }
    bank = tmp_path / "bank.json"
    bank.write_text(json.dumps({"templates": [tmpl]}), encoding="utf-8")
    monkeypatch.setenv("MANIFOLD_TEMPLATE_BANK", str(bank))
    serve_live._TEMPLATE_INDEX = None
    res = serve_live.next_problem(
        {"skill_id": "unit_test_teach_skill", "topic_id": "combinatorics",
         "tier": "teach", "skill_name": "Factorial"},
        seed=5,
    )
    serve_live._TEMPLATE_INDEX = None  # reset cache for other tests
    assert res["status"] == "ok"
    assert res.get("source") == "template"
