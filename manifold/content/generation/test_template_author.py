# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for template_author.py — the LLM 'formulate' stage behind the code gate.

Uses an injected ``propose`` (no live LLM) so the GATE logic is verified
deterministically: a sound proposal is accepted; broken proposals (validate fails,
or stem-faithfulness fails) are rejected."""

import copy

import pytest

import template_author as author
from seed_templates import TEMPLATES

SKILL = {"skill_id": "self_composition_iteration_fixed_points", "topic_id": "precalc_functions",
         "tier": "relearn", "skill_name": "Self-composition"}
GOOD_BODY = {k: copy.deepcopy(v) for k, v in TEMPLATES[0].items()}


def _propose(body):
    return lambda skill: copy.deepcopy(body)


def _agree(item):
    return item["correct_index"]


def _disagree(item):
    return (item["correct_index"] + 1) % 5


def test_accepts_sound_template():
    t = author.author_template(SKILL, propose=_propose(GOOD_BODY), faithfulness_solve=_agree)
    assert t["skill_id"] == SKILL["skill_id"]
    assert t["answer_spec"]["op"] == "iterate"


def test_owns_provenance_over_model():
    body = copy.deepcopy(GOOD_BODY)
    body["skill_id"] = "the_model_tried_to_lie"
    t = author.author_template(SKILL, propose=_propose(body), faithfulness_solve=_agree)
    assert t["skill_id"] == SKILL["skill_id"]  # forced from the request, not the model


def test_rejects_when_validate_fails():
    body = copy.deepcopy(GOOD_BODY)
    body["distractors"] = ["[[answer]]", "[[answer]]", "[[answer]]", "[[answer]]"]  # all collide -> 0 clean
    with pytest.raises(author.AuthorRejected):
        author.author_template(SKILL, propose=_propose(body), faithfulness_solve=_agree)


def test_rejects_when_stem_faithfulness_fails():
    with pytest.raises(author.AuthorRejected):
        author.author_template(SKILL, propose=_propose(GOOD_BODY), faithfulness_solve=_disagree)


def test_malformed_proposal_raises():
    with pytest.raises(author.AuthorError):
        author.author_template(SKILL, propose=lambda s: {}, faithfulness_solve=_agree)
