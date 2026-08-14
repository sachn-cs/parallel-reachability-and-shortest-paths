"""Property-based round-trip tests for serialization.

For Digraph, build, serialise to JSON, deserialise, and assert
the two are equivalent. Uses hypothesis to explore the input space.
"""

from __future__ import annotations

import random

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reachq.core.graph import Digraph
from reachq.core.io.json import dump, load


@given(
    n=st.integers(min_value=0, max_value=20),
    p=st.floats(min_value=0.0, max_value=1.0),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_digraph_round_trip(n, p, seed):
    g = Digraph()
    rng = random.Random(seed)
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < p:
                g.add_edge(i, j)
    j_str = dump(g)
    g2 = load(j_str)
    # Same vertex set
    assert set(g.vertices()) == set(g2.vertices())
    # Same edges
    assert g.out_edges == g2.out_edges
    # Same number of edges
    assert g.num_edges() == g2.num_edges()


def test_digraph_empty_round_trip():
    g = Digraph()
    g2 = load(dump(g))
    assert g.out_edges == g2.out_edges
    assert g.num_edges() == g2.num_edges() == 0


def test_digraph_single_vertex_round_trip():
    g = Digraph()
    g.add_vertex("only")
    g2 = load(dump(g))
    assert set(g.vertices()) == set(g2.vertices())
    assert g.out_edges == g2.out_edges


def test_digraph_string_vertices_round_trip():
    g = Digraph()
    g.add_vertex("alice")
    g.add_vertex("bob")
    g.add_edge("alice", "bob")
    g2 = load(dump(g))
    assert g2.out_edges == g.out_edges
    assert set(g2.vertices()) == {"alice", "bob"}
