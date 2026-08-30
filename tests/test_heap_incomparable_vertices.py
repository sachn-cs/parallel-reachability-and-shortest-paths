"""Heap-tie tests on arbitrarily-hashable vertex types.

Heap entries must never compare vertex objects. ``object()``
instances are incomparable (``object().__lt__`` raises
``TypeError``); previously the heap fell through to vertex
comparison and raised.
"""

from reachq.graph import WeightedDigraph
from reachq.shortest_paths import (
    astar,
    dijkstra,
    shortest_path_hopbound,
    shortest_path_tree,
    truncated_dijkstra,
)


def _build_object_graph():
    g = WeightedDigraph()
    a, b, c, d = object(), object(), object(), object()
    g.add_edge(a, b, 1)
    g.add_edge(b, c, 1)
    g.add_edge(c, d, 1)
    return g, a, b, c, d


def test_dijkstra_handles_object_vertices():
    g, a, b, c, d = _build_object_graph()
    dists = dijkstra(g, a)
    assert dists[a] == 0
    assert dists[b] == 1
    assert dists[c] == 2
    assert dists[d] == 3


def test_truncated_dijkstra_handles_object_vertices():
    g, a, b, c, d = _build_object_graph()
    truncated = truncated_dijkstra(g, a, 2)
    assert a in truncated
    assert b in truncated
    assert c in truncated
    assert d not in truncated


def test_hopbound_handles_object_vertices():
    g, a, b, c, d = _build_object_graph()
    dists = shortest_path_hopbound(g, {}, a, max_hops=2)
    assert a in dists
    assert b in dists
    assert c in dists
    assert d not in dists


def test_shortest_path_tree_handles_object_vertices():
    g, a, b, c, d = _build_object_graph()
    parent = shortest_path_tree(g, a)
    assert parent[a] is None
    assert parent[b] == a
    assert parent[c] == b
    assert parent[d] == c


def test_mixed_comparable_and_incomparable_vertices():
    """A graph mixing ints (sortable) and tuples (sortable) with
    incomparables like ``object()`` must not raise.
    """
    g = WeightedDigraph()
    v_int = 1
    v_str = "alpha"
    v_obj = object()
    v_tup = (1, 2)
    g.add_edge(v_int, v_str, 1)
    g.add_edge(v_str, v_obj, 1)
    g.add_edge(v_obj, v_tup, 1)
    dists = dijkstra(g, v_int)
    assert dists[v_int] == 0
    assert dists[v_str] == 1
    assert dists[v_obj] == 2
    assert dists[v_tup] == 3


def test_astar_incomparable_target():
    """A* heap must accept incomparables between the source and target."""
    g = WeightedDigraph()
    a, b, c = object(), object(), object()
    g.add_edge(a, b, 3)
    g.add_edge(b, c, 2)

    def h(v):
        if v == a:
            return 5
        if v == b:
            return 2
        return 0

    assert astar(g, a, c, h) == 5


def test_unreachable_object_target_returns_sentinel():
    import pytest

    from reachq.errors import ReachqGraphError

    g, a, _b, _c, _d = _build_object_graph()
    target = object()
    # target not in graph
    assert target not in g
    with pytest.raises(ReachqGraphError):
        astar(g, a, target, lambda _v: 0)
