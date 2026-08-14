"""Shared fixtures for the reachq test suite."""

from __future__ import annotations

import pytest

from reachq.core.generators import cycle_graph, path_graph, random_dag
from reachq.core.graph import Digraph, WeightedDigraph


@pytest.fixture
def small_dag() -> Digraph:
    """A small 10-vertex DAG for fast unit tests."""
    return random_dag(10, edge_probability=0.2, random_seed=42)


@pytest.fixture
def path_5() -> Digraph:
    """A directed path 0->1->2->3->4."""
    return path_graph(5)


@pytest.fixture
def cycle_5() -> Digraph:
    """A directed cycle on 5 vertices."""
    return cycle_graph(5)


@pytest.fixture
def weighted_path_5() -> WeightedDigraph:
    """A weighted directed path 0->1->2->3->4."""
    g = WeightedDigraph()
    for i in range(5):
        g.add_vertex(i)
    for i in range(4):
        g.add_edge(i, i + 1, i + 1)
    return g
