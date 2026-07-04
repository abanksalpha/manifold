# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for structure.py — the advisory structural-shape signature."""

import structure


def test_same_shape_different_numbers_collapses():
    a = {"answer_spec": {"op": "evaluate"}, "stem": "What is \\( [[a]]+[[b]] \\)?"}
    b = {"answer_spec": {"op": "evaluate"}, "stem": "What is \\( [[x]]+[[y]] \\)?"}
    assert structure.structure_signature(a) == structure.structure_signature(b)


def test_different_op_differs():
    a = {"answer_spec": {"op": "evaluate"}, "stem": "Compute \\( [[a]] \\)."}
    b = {"answer_spec": {"op": "solve"}, "stem": "Compute \\( [[a]] \\)."}
    assert structure.structure_signature(a) != structure.structure_signature(b)


def test_different_wording_differs():
    a = {"answer_spec": {"op": "diff"}, "stem": "Find the slope of the tangent line at \\( [[x0]] \\)."}
    b = {"answer_spec": {"op": "diff"}, "stem": "Find the second derivative at \\( [[x0]] \\)."}
    assert structure.structure_signature(a) != structure.structure_signature(b)


def test_distinct_structures_report_and_duplicate_flag():
    same_a = {"template_id": "t1", "answer_spec": {"op": "evaluate"}, "stem": "Find \\( [[a]] \\)."}
    same_b = {"template_id": "t2", "answer_spec": {"op": "evaluate"}, "stem": "Find \\( [[x]] \\)."}
    different = {"template_id": "t3", "answer_spec": {"op": "solve"}, "stem": "Solve for \\( x \\)."}
    rep = structure.distinct_structures([same_a, same_b, different])
    assert rep["count"] == 3
    assert rep["distinct_structures"] == 2
    assert len(rep["duplicate_shapes"]) == 1
    dup_ids = next(iter(rep["duplicate_shapes"].values()))
    assert set(dup_ids) == {"t1", "t2"}
