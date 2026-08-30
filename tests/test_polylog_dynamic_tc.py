"""Tests for the polylog fully-dynamic transitive closure."""

from __future__ import annotations

from reachq.graph import Digraph
from reachq.research.polylog_dynamic_tc import (
    PolylogDynamicTC,
    polylog_incremental_tc,
)


def test_polylog_empty_graph():
    """An empty graph has only the reflexive closure (0 pairs)."""
    g = Digraph()
    pdtc = PolylogDynamicTC(g)
    assert len(pdtc) == 0


def test_polylog_single_edge():
    """Inserting (0, 1) adds (0, 1) and the reflexive pairs."""
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    pdtc = PolylogDynamicTC(g)
    pdtc.insert_edge(0, 1)
    assert pdtc.reaches(0, 1)
    assert pdtc.reaches(0, 0)
    assert pdtc.reaches(1, 1)
    assert not pdtc.reaches(1, 0)


def test_polylog_chained_insertions():
    """Inserting 0->1, 1->2, 0->2 makes 0 reach 2 directly and via 1."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2), (0, 2)])
    assert pdtc.reaches(0, 1)
    assert pdtc.reaches(0, 2)
    assert pdtc.reaches(1, 2)
    # 2 cannot reach 0 (DAG).
    assert not pdtc.reaches(2, 0)


def test_polylog_delete_critical_edge():
    """Deleting the only path from x to y invalidates (x, y)."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2)])
    assert pdtc.reaches(0, 2)
    pdtc.delete_edge(1, 2)
    assert pdtc.reaches(0, 1)  # (0, 1) still present
    assert not pdtc.reaches(0, 2)  # path via 1 is gone


def test_polylog_delete_redundant_edge():
    """Deleting a redundant edge preserves reachability."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2), (0, 2)])
    assert pdtc.reaches(0, 2)
    pdtc.delete_edge(0, 2)  # redundant because 0->1->2 exists
    # Reachability from 0 to 2 still holds via the chain.
    assert pdtc.reaches(0, 2)


def test_polylog_delete_nonexistent_noop():
    """Deleting an edge that doesn't exist is a no-op."""
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    pdtc = polylog_incremental_tc(g, [(0, 1)])
    before = len(pdtc)
    pdtc.delete_edge(1, 0)  # doesn't exist
    assert len(pdtc) == before


def test_polylog_invalid_vertex_raises():
    """Inserting an edge with an unknown vertex raises KeyError."""
    g = Digraph()
    g.add_vertex(0)
    pdtc = PolylogDynamicTC(g)
    try:
        pdtc.insert_edge(0, 99)
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_polylog_reachable_from_returns_vertices():
    """reachable_from returns the set of vertex objects, not indices."""
    g = Digraph()
    for v in range(4):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2), (2, 3)])
    rf = pdtc.reachable_from(0)
    assert rf == {0, 1, 2, 3}


def test_polylog_reach_set_full_tc():
    """reach_set returns every pair in the current TC."""
    g = Digraph()
    for v in range(4):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2), (2, 3)])
    pairs = pdtc.reach_set()
    expected = {
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 2),
        (2, 3),
        (3, 3),
    }
    assert pairs == expected


def test_polylog_str_repr():
    """__repr__ contains useful information."""
    g = Digraph()
    g.add_vertex(0)
    pdtc = PolylogDynamicTC(g)
    r = repr(pdtc)
    assert "PolylogDynamicTC" in r
    assert "n=1" in r


def test_polylog_delete_chain_full():
    """Deleting edges in a chain incrementally invalidates all dependent paths."""
    g = Digraph()
    for v in range(4):
        g.add_vertex(v)
    pdtc = polylog_incremental_tc(g, [(0, 1), (1, 2), (2, 3)])
    assert pdtc.reaches(0, 3)
    pdtc.delete_edge(2, 3)
    assert not pdtc.reaches(0, 3)
    assert pdtc.reaches(0, 2)
    pdtc.delete_edge(1, 2)
    assert not pdtc.reaches(0, 2)
    assert pdtc.reaches(0, 1)


def test_polylog_insert_creates_new_path():
    """Inserting an edge creates new reachability pairs."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    g.add_edge(0, 1)
    pdtc = PolylogDynamicTC(g)
    assert not pdtc.reaches(0, 2)
    pdtc.insert_edge(1, 2)
    assert pdtc.reaches(0, 2)


def test_polylog_consistent_with_naive_after_sequence():
    """After a sequence of inserts, the polylog TC matches the naive recomputation."""
    from reachq.research.dynamic_tc import DynamicTransitiveClosure

    g = Digraph()
    for v in range(5):
        g.add_vertex(v)
    insertions = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (1, 3)]
    pdtc = polylog_incremental_tc(g, insertions)
    # Build a naive TC for comparison.
    g2 = Digraph()
    for v in range(5):
        g2.add_vertex(v)
    for u, v in insertions:
        g2.add_edge(u, v)
    dtc = DynamicTransitiveClosure(g2)
    # Compare pair sets.
    poly_pairs = pdtc.reach_set()
    naive_pairs = dtc.reach_set()
    assert poly_pairs == naive_pairs


def test_polylog_dense_graph_smoke():
    """A dense graph reaches all pairs."""
    g = Digraph()
    for v in range(6):
        g.add_vertex(v)
    insertions = [(i, j) for i in range(6) for j in range(6) if i != j]
    pdtc = polylog_incremental_tc(g, insertions)
    # Every pair (i, j) with i != j should be reachable.
    for i in range(6):
        for j in range(6):
            if i != j:
                assert pdtc.reaches(i, j), f"expected {i} -> {j}"
