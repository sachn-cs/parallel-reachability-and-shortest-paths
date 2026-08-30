"""Tests for the predictors in reachq.core.predict."""

from __future__ import annotations

import math

from reachq.generators import dense_graph, path_graph
from reachq.graph import Digraph
from reachq.core.predict import predict_epsilon, predict_omega, predict_rho


def test_predict_omega_returns_float_in_range():
    """predict_omega returns a value in [2.0, 3.0]."""
    omega = predict_omega(path_graph(20))
    assert isinstance(omega, float)
    assert 2.0 <= omega <= 3.0


def test_predict_omega_small_graph_uses_strassen_bound():
    """predict_omega returns 2.5 for small graphs."""
    assert predict_omega(path_graph(50)) == 2.5


def test_predict_omega_dense_graph_uses_strassen_bound():
    """predict_omega returns 2.5 for dense graphs."""
    g = dense_graph(200, 36000, random_seed=42)
    assert predict_omega(g) == 2.5


def test_predict_epsilon_decreases_with_n():
    """predict_epsilon follows 1/sqrt(n) heuristic."""
    eps_small = predict_epsilon(10)
    eps_large = predict_epsilon(1000)
    assert eps_small > eps_large
    assert eps_large < 0.05


def test_predict_epsilon_clamped():
    """predict_epsilon is clamped to [0.01, 0.5]."""
    assert predict_epsilon(2) <= 0.5
    assert predict_epsilon(100_000) >= 0.01


def test_predict_rho_zero_for_empty_graph():
    """Empty graph has rho=0."""
    assert predict_rho(0, 0) == 0.0


def test_predict_rho_density_aware():
    """Dense graphs have larger rho than sparse ones."""
    n = 20
    rho_sparse = predict_rho(n, 19)
    rho_dense = predict_rho(n, 380)
    assert rho_dense > rho_sparse


def test_predict_rho_handles_disconnected():
    """Graph with isolated vertices: rho is finite, not inf."""
    rho = predict_rho(10, 1)
    assert math.isfinite(rho)
    assert rho > 0
