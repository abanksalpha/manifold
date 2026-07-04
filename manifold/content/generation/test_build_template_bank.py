# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for build_template_bank.py's near-duplicate rejection gate: within one
skill's authored list, a template whose structural shape repeats an earlier one is
dropped and never reaches template_bank.json — a REAL gate, not just advisory
reporting, so the served bank can never carry two "very similar" problems for the
same skill."""

import json

import build_template_bank as btb


def _write(dir_, name, data):
    (dir_ / name).write_text(json.dumps(data), encoding="utf-8")


def _tmpl(skill_id, tid, stem, a=2, b=3):
    return {
        "template_id": tid,
        "skill_id": skill_id,
        "topic_id": "t",
        "tier": "relearn",
        "params": {"a": {"type": "int", "lo": a, "hi": a + 30}, "b": {"type": "int", "lo": b, "hi": b + 30}},
        "constraints": [],
        "stem": stem,
        "answer_spec": {"op": "evaluate", "expr": "[[a]] + [[b]]"},
        "distractors": ["[[answer]]+1", "[[answer]]-1", "[[answer]]+2", "[[answer]]-2", "[[answer]]+3"],
    }


def test_dedup_drops_reskinned_duplicate_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(btb, "AUTHORED", tmp_path)
    monkeypatch.setattr(btb, "BANK_PATH", tmp_path / "template_bank.json")
    dup1 = _tmpl("skill_x", "t1", "What is \\( [[a]] + [[b]] \\)?")
    # Same op, same normalized stem skeleton, just different slot NAMES/ranges: a reskin.
    dup2 = _tmpl("skill_x", "t2", "What is \\( [[a]] + [[b]] \\)?", a=5, b=9)
    different = _tmpl("skill_x", "t3", "Compute the sum of \\( [[a]] \\) and \\( [[b]] \\).", a=1, b=2)
    _write(tmp_path, "skill_x.json", [dup1, dup2, different])

    rc = btb.main()

    bank = json.loads((tmp_path / "template_bank.json").read_text())
    ids = {t["template_id"] for t in bank["templates"]}
    assert "t1" in ids  # first occurrence of the shape kept
    assert "t2" not in ids  # dropped: duplicates t1's shape
    assert "t3" in ids  # genuinely different shape kept
    assert rc == 0  # a dropped duplicate is not a file failure


def test_dedup_keeps_all_distinct_shapes(tmp_path, monkeypatch):
    monkeypatch.setattr(btb, "AUTHORED", tmp_path)
    monkeypatch.setattr(btb, "BANK_PATH", tmp_path / "template_bank.json")
    a = _tmpl("skill_y", "a1", "What is \\( [[a]] + [[b]] \\)?")
    b = _tmpl("skill_y", "a2", "Find the total when you combine \\( [[a]] \\) and \\( [[b]] \\).", a=4, b=6)
    _write(tmp_path, "skill_y.json", [a, b])

    btb.main()

    bank = json.loads((tmp_path / "template_bank.json").read_text())
    ids = {t["template_id"] for t in bank["templates"]}
    assert ids == {"a1", "a2"}
