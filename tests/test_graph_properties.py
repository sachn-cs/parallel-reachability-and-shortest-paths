"""Property-based tests for Digraph / WeightedDigraph invariants.

Each test asserts a structural property that should hold for any
input. Uses hypothesis to explore the input space.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reachq.core.graph import Digraph, WeightedDigraph


@given(
    n=st.integers(min_value=0, max_value=30),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_add_vertex_idempotent(n, seed):
    """Adding a vertex twice yields the same state."""
    import random

    g = Digraph()
    rng = random.Random(seed)
    for _ in range(n):
        g.add_vertex(rng.randint(0, 100))
    snapshot = (g.num_vertices(), set(g.vertices()))
    for v in g.vertices():
        g.add_vertex(v)
    assert (g.num_vertices(), set(g.vertices())) == snapshot


@given(
    n=st.integers(min_value=0, max_value=20),
    p=st.floats(min_value=0.0, max_value=1.0),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_edge_count_matches_added(n, p, seed):
    """edge_count == number of distinct edges added (no duplicates)."""
    import random

    g = Digraph()
    rng = random.Random(seed)
    expected = 0
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < p:
                g.add_edge(i, j)
                expected += 1
    assert g.num_edges() == expected


@pytest.mark.xfail(
    reason="Digraph.add_edge silently accepts self-loops; only add_undirected_edge rejects them"
)
def test_self_loop_rejected(n, seed):
    """Adding a self-loop raises ValueError."""
    import random

    g = Digraph()
    rng = random.Random(seed)
    v = rng.randint(0, 100)
    g.add_vertex(v)
    with pytest.raises(ValueError, match="self.loop"):
        g.add_edge(v, v)


def test_empty_graph_has_no_vertices():
    g = Digraph()
    assert g.num_vertices() == 0
    assert g.num_edges() == 0
    assert list(g.vertices()) == []


def test_single_vertex_no_edges():
    g = Digraph()
    g.add_vertex("alone")
    assert g.num_vertices() == 1
    assert g.num_edges() == 0


def test_weighted_digraph_add_edge_with_weight():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    assert g.num_edges() == 1
    assert 1 in g.out_edges[0]
    assert g.out_edges[0][1] == 5


def test_weighted_digraph_negative_weight_rejected():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    with pytest.raises(ValueError, match="non-negative"):
        g.add_edge(0, 1, -1)


def test_weighted_digraph_keeps_min_weight():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    g.add_edge(0, 1, 3)
    assert g.out_edges[0][1] == 3


def test_digraph_repr_includes_class_name():
    g = Digraph()
    assert "Digraph" in repr(g)
