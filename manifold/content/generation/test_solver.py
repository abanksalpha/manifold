# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for solver.py — the deterministic answer engine.

Includes REGRESSION cases: the exact items the LLM-generate+LLM-verify pipeline
banked with WRONG answers. Code must compute the true answer for each."""

import sympy as sp
import pytest

import solver


def _val(spec):
    return sp.simplify(solver.solve_spec(spec)["value"])


# --- regression: items the old pipeline got wrong -------------------------------


def test_regression_iterate_fixed_point():
    # f(x)=2x-1, x0=1, x3.  Old bank claimed 5; truth is the fixed point 1.
    assert _val({"op": "iterate", "f": "2*x - 1", "x0": 1, "n": 3, "var": "x"}) == 1


def test_regression_compose_solve():
    # f(f(x))=5 with f(x)=2x-1  ->  4x-3=5  ->  x=2.  Old bank claimed 3.
    out = solver.solve_spec({"op": "solve", "equation": "2*(2*x - 1) - 1 = 5", "var": "x"})
    assert out["solutions"] == [sp.Integer(2)]


def test_regression_log_equation():
    # log2(x+3) - log2(x) = 1  ->  x=3.  Old bank claimed 5.
    out = solver.solve_spec({"op": "solve", "equation": "log(x + 3, 2) - log(x, 2) = 1", "var": "x"})
    assert out["solutions"] == [sp.Integer(3)]


def test_regression_evaluate_order_of_ops():
    # 3^2 + 2*4/2 - sqrt(16) = 9 + 4 - 4 = 9.
    assert _val({"op": "evaluate", "expr": "3**2 + 2*4/2 - sqrt(16)"}) == 9


# --- core ops -------------------------------------------------------------------


def test_solve_multiple_roots_returns_full_set():
    out = solver.solve_spec({"op": "solve", "equation": "x**2 - 5*x + 6 = 0", "var": "x"})
    assert out["solutions"] == [sp.Integer(2), sp.Integer(3)]


def test_diff_at_point():
    assert _val({"op": "diff", "expr": "x**3", "var": "x", "at": 2}) == 12


def test_definite_integral():
    assert _val({"op": "integrate", "expr": "2*x", "var": "x", "bounds": [0, 3]}) == 9


def test_limit():
    assert _val({"op": "limit", "expr": "sin(x)/x", "var": "x", "point": 0}) == 1


def test_vieta():
    poly = "x**3 - 6*x**2 + 11*x - 6"  # roots 1,2,3
    assert _val({"op": "vieta", "poly": poly, "var": "x", "which": "sum"}) == 6
    assert _val({"op": "vieta", "poly": poly, "var": "x", "which": "sum_pairs"}) == 11
    assert _val({"op": "vieta", "poly": poly, "var": "x", "which": "prod"}) == 6


def test_system_unique():
    out = solver.solve_spec({"op": "system", "equations": ["x + y = 5", "x - y = 1"], "vars": ["x", "y"], "want": "x"})
    assert out["value"] == 3
    assert out["solution"] == {"x": "3", "y": "2"}


def test_system_want_expression():
    out = solver.solve_spec({"op": "system", "equations": ["x + y = 5", "x - y = 1"], "vars": ["x", "y"], "want": "x + y"})
    assert out["value"] == 5


def test_sum_arithmetic():
    assert _val({"op": "sum", "expr": "k", "var": "k", "lo": 1, "hi": 10}) == 55


def test_sum_geometric():
    assert _val({"op": "sum", "expr": "2**k", "var": "k", "lo": 0, "hi": 5}) == 63


# --- matrix ops -----------------------------------------------------------------


def test_det_2x2():
    assert _val({"op": "det", "matrix": [["1", "2"], ["3", "4"]]}) == -2


def test_det_3x3():
    assert _val({"op": "det", "matrix": [["2", "0", "1"], ["3", "0", "0"], ["5", "1", "1"]]}) == 3


def test_trace():
    assert _val({"op": "trace", "matrix": [["1", "2"], ["3", "4"]]}) == 5


def test_rank_full_and_deficient():
    assert _val({"op": "rank", "matrix": [["1", "2"], ["3", "4"]]}) == 2
    assert _val({"op": "rank", "matrix": [["1", "2"], ["2", "4"]]}) == 1


def test_eig_symmetric_max_min():
    m = [["2", "0"], ["0", "3"]]
    assert _val({"op": "eig", "matrix": m, "which": "max"}) == 3
    assert _val({"op": "eig", "matrix": m, "which": "min"}) == 2


def test_eig_sum_is_trace_prod_is_det():
    m = [["4", "1"], ["2", "3"]]  # eigenvalues 5, 2
    assert _val({"op": "eig", "matrix": m, "which": "sum"}) == 7
    assert _val({"op": "eig", "matrix": m, "which": "prod"}) == 10


def test_eig_upper_triangular_diagonal_eigenvalues():
    m = [["5", "9", "-2"], ["0", "2", "7"], ["0", "0", "4"]]
    assert _val({"op": "eig", "matrix": m, "which": "max"}) == 5
    assert _val({"op": "eig", "matrix": m, "which": "min"}) == 2


def test_eig_complex_max_raises_but_sum_ok():
    m = [["0", "-1"], ["1", "0"]]  # eigenvalues ±i (not real)
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "eig", "matrix": m, "which": "max"})
    assert _val({"op": "eig", "matrix": m, "which": "sum"}) == 0


def test_dblintegrate_rectangle():
    # integral over [0,2]x[0,3] of x*y = (2^2/2)(3^2/2) = 2*4.5 = 9
    assert _val({"op": "dblintegrate", "expr": "x*y", "vars": ["x", "y"], "bounds": [["0", "2"], ["0", "3"]]}) == 9


def test_dblintegrate_type_i_region():
    # inner x from 0 to y, outer y from 0 to 2, integrand 1 -> area of triangle = 2
    assert _val({"op": "dblintegrate", "expr": "1", "vars": ["x", "y"], "bounds": [["0", "y"], ["0", "2"]]}) == 2


def test_triple_integrate_box():
    assert _val({"op": "dblintegrate", "expr": "1", "vars": ["x", "y", "z"],
                 "bounds": [["0", "2"], ["0", "3"], ["0", "4"]]}) == 24


def test_dblintegrate_bad_vars_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "dblintegrate", "expr": "x", "vars": ["x"], "bounds": [["0", "1"]]})


def test_det_non_square_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "det", "matrix": [["1", "2", "3"], ["4", "5", "6"]]})


def test_matrix_with_free_symbol_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "det", "matrix": [["a", "2"], ["3", "4"]]})


# --- fail loud ------------------------------------------------------------------


def test_unknown_op_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "teleport", "expr": "1"})


def test_no_real_solution_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "solve", "equation": "x**2 + 1 = 0", "var": "x"})


def test_evaluate_with_free_symbol_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "evaluate", "expr": "x + 1"})


def test_system_infinite_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "system", "equations": ["x + y = 2", "2*x + 2*y = 4"], "vars": ["x", "y"], "want": "x"})


def test_system_inconsistent_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "system", "equations": ["x + y = 2", "x + y = 5"], "vars": ["x", "y"], "want": "x"})


def test_malformed_spec_raises():
    with pytest.raises(solver.SolveError):
        solver.solve_spec("not a dict")
    with pytest.raises(solver.SolveError):
        solver.solve_spec({"op": "iterate", "f": "2*x", "x0": 1, "n": -2, "var": "x"})
