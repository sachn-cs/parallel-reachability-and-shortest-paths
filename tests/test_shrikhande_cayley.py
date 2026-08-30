"""Tests for the shrikhande_cayley() generator (after stub removal)."""

from __future__ import annotations

from reachq.generators import shrikhande_cayley


def test_shrikhande_cayley_returns_graph():
    """The function must return a Digraph, not raise NotImplementedError."""
    g = shrikhande_cayley()
    assert g.num_vertices() == 16


def test_shrikhande_cayley_is_3_regular():
    """Each vertex in the Shrikhande graph has degree 6 (3 incoming + 3 outgoing)."""
    g = shrikhande_cayley()
    for v in g.vertices():
        # 6 undirected neighbours = 6 outgoing + 6 incoming directed edges
        assert g.degree_out(v) == 6
        assert g.degree_in(v) == 6


def test_shrikhande_cayley_edge_count():
    """6-regular undirected graph on 16 vertices: 48 undirected = 96 directed edges."""
    g = shrikhande_cayley()
    assert g.num_edges() == 96


def test_shrikhande_cayley_undirected():
    """For every (u, v), there is also (v, u)."""
    g = shrikhande_cayley()
    for u, v in g.edges():
        assert g.has_edge(v, u), f"missing reverse edge ({v}, {u})"
