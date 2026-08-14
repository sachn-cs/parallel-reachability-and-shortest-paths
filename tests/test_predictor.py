"""Tests for the heuristics in reachq.core.predictor."""

from __future__ import annotations

import math

from reachq.core.generators import dense_graph, path_graph
from reachq.core.graph import Digraph
from reachq.core.predictor import predict_epsilon, predict_omega, predict_rho


def test_predict_omega_returns_float_in_range():
    """predict_omega returns a runtime-detected omega in [2.0, 3.0]."""
    g = path_graph(10)
    omega = predict_omega(g)
    assert isinstance(omega, float)
    assert 2.0 <= omega <= 3.0


def test_predict_epsilon_decreases_with_n():
    """predict_epsilon follows 1/sqrt(n) heuristic, so it decreases with n."""
    g_small = path_graph(10)
    g_large = path_graph(1000)
    eps_small = predict_epsilon(g_small)
    eps_large = predict_epsilon(g_large)
    assert eps_small > eps_large
    assert eps_large < 0.05  # for n=1000


def test_predict_epsilon_clamped():
    """predict_epsilon is clamped to [0.01, 0.5]."""
    g_tiny = path_graph(2)
    g_huge = path_graph(100_000)
    assert predict_epsilon(g_tiny) <= 0.5
    assert predict_epsilon(g_huge) >= 0.01


def test_predict_rho_zero_for_empty_graph():
    """Empty graph has rho=0."""
    g = Digraph()
    assert predict_rho(g) == 0.0


def test_predict_rho_density_aware():
    """Dense graphs have larger rho than sparse ones."""
    g_sparse = path_graph(20)  # m = 19
    g_dense = dense_graph(20, 380, random_seed=42)  # m = 380 (near-complete)
    rho_sparse = predict_rho(g_sparse)
    rho_dense = predict_rho(g_dense)
    # rho = sqrt(n) / beta, where beta decreases with m. So rho grows
    # with density.
    assert rho_dense > rho_sparse


def test_predict_rho_handles_disconnected():
    """Graph with isolated vertices: rho is finite, not inf."""
    g = Digraph()
    for v in range(10):
        g.add_vertex(v)
    g.add_edge(0, 1)
    rho = predict_rho(g)
    assert math.isfinite(rho)
    assert rho > 0
