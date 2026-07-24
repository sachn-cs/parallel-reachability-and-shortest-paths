"""Predictor for algorithm parameters.

Predicts optimal omega, epsilon, and rho values based on graph
properties and historical benchmark data. Future work: ML-based
prediction.
"""

from __future__ import annotations

from reachq.core.graph import Digraph


def predict_omega(graph: Digraph) -> float:
    """Predict optimal omega for a graph."""
    return 2.5


def predict_epsilon(graph: Digraph) -> float:
    """Predict optimal epsilon for a graph."""
    return 0.1


def predict_rho(graph: Digraph) -> float:
    """Predict optimal rho for a graph."""
    n = graph.num_vertices()
    m = graph.num_edges()
    return m / (n * n) if n > 0 else 0.0
