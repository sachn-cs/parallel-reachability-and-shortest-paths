"""Tests for the naive dynamic transitive closure."""

from __future__ import annotations

from reachq.graph import Digraph
from reachq.research.dynamic_tc import DynamicTransitiveClosure, incremental_tc


def test_dynamic_tc_empty_graph():
    """An empty graph has only the reflexive closure (empty set of pairs)."""
    g = Digraph()
    dtc = DynamicTransitiveClosure(g)
    # Reflexive closure on empty graph: no pairs.
    assert len(dtc) == 0


def test_dynamic_tc_single_edge():
    """Inserting (0, 1) adds (0, 1) to the closure."""
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    dtc = DynamicTransitiveClosure(g)
    dtc.insert_edge(0, 1)
    assert dtc.reaches(0, 1)
    assert not dtc.reaches(1, 0)


def test_dynamic_tc_chained_edges():
    """Inserting 0->1 and 1->2 makes 0 reach 2."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    dtc = DynamicTransitiveClosure(g)
    dtc.insert_edge(0, 1)
    dtc.insert_edge(1, 2)
    assert dtc.reaches(0, 2)
    assert dtc.reaches(1, 2)
    assert not dtc.reaches(2, 0)


def test_dynamic_tc_reachable_from():
    """reachable_from returns all reachable vertices."""
    g = Digraph()
    for v in range(4):
        g.add_vertex(v)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    dtc = DynamicTransitiveClosure(g)
    assert dtc.reachable_from(0) == {0, 1, 2}
    assert dtc.reachable_from(3) == {3}


def test_dynamic_tc_delete_edge():
    """Deleting (0, 1) removes reachability 0 -> 1 and 0 -> 2."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    dtc = DynamicTransitiveClosure(g)
    assert dtc.reaches(0, 2)
    dtc.delete_edge(0, 1)
    assert not dtc.reaches(0, 1)
    assert not dtc.reaches(0, 2)


def test_dynamic_tc_delete_nonexistent_edge_noop():
    """Deleting an edge that doesn't exist is a no-op."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    g.add_edge(0, 1)
    dtc = DynamicTransitiveClosure(g)
    before = dtc.reach_set()
    dtc.delete_edge(1, 0)
    after = dtc.reach_set()
    assert before == after


def test_incremental_tc_helper():
    """incremental_tc builds a closure from a sequence of insertions."""
    g = Digraph()
    for v in range(3):
        g.add_vertex(v)
    dtc = incremental_tc(g, [(0, 1), (1, 2)])
    assert dtc.reaches(0, 2)


def test_dynamic_tc_invalid_vertex_raises():
    """Inserting an edge with an unknown vertex raises KeyError."""
    g = Digraph()
    g.add_vertex(0)
    dtc = DynamicTransitiveClosure(g)
    try:
        dtc.insert_edge(0, 99)
        assert False, "expected KeyError"
    except KeyError:
        pass
