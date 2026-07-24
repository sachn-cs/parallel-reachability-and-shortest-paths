"""Tests for hypergraph reachability."""

from __future__ import annotations

from reachq.core.graph import Digraph
from reachq.research.hyper import (
    DirectedHypergraph,
    hyper_reachable,
    hyper_to_digraph,
    hypergraph_from_digraph,
)


def test_empty_hypergraph():
    """An empty hypergraph has no reachable vertices from any source."""
    hg = DirectedHypergraph()
    assert hg.num_vertices == 0
    assert hg.num_edges == 0
    assert hyper_reachable(hg, 0) == set()


def test_single_hyperedge():
    """A hyperedge ({a}, {b, c}) makes b and c reachable from a."""
    hg = DirectedHypergraph()
    hg.add_edge(["a"], ["b", "c"])
    assert hyper_reachable(hg, "a") == {"a", "b", "c"}


def test_chained_hyperedges():
    """Two hyperedges linked through a shared vertex form a chain."""
    hg = DirectedHypergraph()
    hg.add_edge(["a"], ["b", "c"])
    hg.add_edge(["b"], ["d"])  # link via b
    assert hyper_reachable(hg, "a") == {"a", "b", "c", "d"}


def test_hyperedge_too_big_tail():
    """A hyperedge with multiple tail vertices requires any one to fire it."""
    hg = DirectedHypergraph()
    hg.add_edge(["a", "b"], ["c"])
    # Either a or b alone can fire the hyperedge, reaching c.
    # b is in the hyperedge's tail but not reachable from a (no edge
    # leads to b).
    assert hyper_reachable(hg, "a") == {"a", "c"}
    assert hyper_reachable(hg, "b") == {"b", "c"}


def test_empty_tail_raises():
    """Adding a hyperedge with empty tail raises ValueError."""
    hg = DirectedHypergraph()
    try:
        hg.add_edge([], ["a"])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_empty_head_raises():
    """Adding a hyperedge with empty head raises ValueError."""
    hg = DirectedHypergraph()
    try:
        hg.add_edge(["a"], [])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_hypergraph_from_digraph_roundtrip():
    """Lifting a Digraph into a hypergraph and back yields the same reachability."""
    g = Digraph()
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    hg = hypergraph_from_digraph(g)
    assert hyper_reachable(hg, 0) == {0, 1, 2, 3}


def test_hyper_to_digraph():
    """Materialising a hypergraph back into a digraph preserves reachability."""
    hg = DirectedHypergraph()
    hg.add_edge([0], [1, 2])
    hg.add_edge([1], [3])
    dg = hyper_to_digraph(hg)
    # Each (s, t) for s in tail, t in head becomes a directed edge.
    assert dg.has_edge(0, 1)
    assert dg.has_edge(0, 2)
    assert dg.has_edge(1, 3)
    # Self-loops are excluded.
    assert not dg.has_edge(0, 0)


def test_unreachable_source():
    """Asking for reachability from a non-vertex returns the empty set."""
    hg = DirectedHypergraph()
    hg.add_edge(["a"], ["b"])
    assert hyper_reachable(hg, "z") == set()