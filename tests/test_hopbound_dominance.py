"""Counterexample: layered DP for hop-bounded SSSP.

The reviewer's counterexample:

    s -> a (0), a -> x (0), s -> x (5), x -> t (0), max_hops=2.

The naive single-distance-per-vertex algorithm can suppress a
shorter-hop arrival that is also cheaper, leaving ``t`` as
``inf``. Layered DP / frontier tuple keeping a per-(vertex, hops)
state must return ``t == 0``.
"""

from reachq.core.generators import path_graph
from reachq.core.graph import WeightedDigraph
from reachq.core.shortest_paths import (
    dijkstra,
    shortest_path_hopbound,
    truncated_dijkstra,
    shortest_path_tree,
    astar,
)


def _build_counterexample():
    g = WeightedDigraph()
    g.add_edge("s", "a", 0)
    g.add_edge("a", "x", 0)
    g.add_edge("s", "x", 5)
    g.add_edge("x", "t", 0)
    return g


def test_counterexample_t_reaches_with_correct_distance():
    """Reviewer's counterexample: the buggy implementation omitted
    ``t`` because a cheaper 3-hop arrival suppressed a costlier
    2-hop arrival. The fix returns ``t`` at distance 5.
    """
    g = _build_counterexample()
    dists = shortest_path_hopbound(g, {}, "s", max_hops=2)
    assert "t" in dists, (
        "t must be reachable at cost 5 via s->x->t within max_hops=2"
    )
    assert dists["t"] == 5


def test_counterexample_three_hop_unbounded():
    g = _build_counterexample()
    dists = shortest_path_hopbound(g, {}, "s", max_hops=3)
    assert dists["t"] == 0


def test_counterexample_with_longer_path():
    g = WeightedDigraph()
    for label in ["s", "a", "b", "c", "x", "t"]:
        g.add_vertex(label)
    g.add_edge("s", "a", 0)
    g.add_edge("a", "b", 0)
    g.add_edge("b", "c", 0)
    g.add_edge("c", "x", 0)
    g.add_edge("s", "x", 8)
    g.add_edge("x", "t", 0)
    dists = shortest_path_hopbound(g, {}, "s", max_hops=5)
    assert dists["t"] == 0


def test_short_hop_cheaper_path_preserved():
    """A cheaper 2-hop arrival must not be discarded in favor of a
    costlier 1-hop arrival. With max_hops=2, both p->q (1 hop, weight 5)
    and p->r->q (2 hops, weight 1) are reachable; the cheapest wins.
    """
    g = WeightedDigraph()
    g.add_edge("p", "q", 5)
    g.add_edge("p", "r", 0)
    g.add_edge("r", "q", 1)
    dists = shortest_path_hopbound(g, {}, "p", max_hops=2)
    assert dists["q"] == 1


def test_hopbound_matches_dijkstra_when_max_hops_unbounded():
    g = path_graph(10)
    gw = WeightedDigraph()
    for v in g.vertices():
        gw.add_vertex(v)
        for w in g.out_edges.get(v, ()):
            gw.add_edge(v, w, 1)
    for src in gw.vertices():
        exact = dijkstra(gw, src)
        approx = shortest_path_hopbound(gw, {}, src, max_hops=100)
        for tgt, d in exact.items():
            assert approx.get(tgt) == d


def test_truncated_dijkstra_does_not_break_on_object_vertices():
    """Truncated Dijkstra must accept arbitrary hashable vertices."""
    g = WeightedDigraph()
    a, b, c = object(), object(), object()
    g.add_edge(a, b, 5)
    g.add_edge(b, c, 5)
    truncated = truncated_dijkstra(g, a, 8)
    assert a in truncated
    assert b in truncated
    assert c not in truncated


def test_dijkstra_does_not_compare_vertices():
    """Two ``object()`` instances at the same distance must not raise."""
    g = WeightedDigraph()
    a, b = object(), object()
    g.add_edge(a, b, 1)
    dists = dijkstra(g, a)
    assert dists[a] == 0
    assert dists[b] == 1


def test_shortest_path_tree_handles_object_vertices():
    a, b, c = object(), object(), object()
    g = WeightedDigraph()
    g.add_edge(a, b, 2)
    g.add_edge(b, c, 3)
    parent = shortest_path_tree(g, a)
    assert parent[a] is None
    assert parent[b] == a
    assert parent[c] == b


def test_astar_consistent_heuristic_finds_optimal():
    g = WeightedDigraph()
    for i in range(5):
        g.add_vertex(i)
    for i, j, w in [(0, 1, 1), (1, 2, 1), (2, 4, 1), (0, 3, 2), (3, 4, 1)]:
        g.add_edge(i, j, w)

    def h(v):
        return {0: 3, 1: 2, 2: 1, 3: 1, 4: 0}.get(v, 0)

    path_cost = astar(g, 0, 4, h)
    assert path_cost == 3


def test_astar_zero_heuristic_matches_dijkstra():
    g = WeightedDigraph()
    for i in range(10):
        g.add_vertex(i)
        if i > 0:
            g.add_edge(i - 1, i, 1)
    astar_dist = astar(g, 0, 9, lambda v: 0)
    dijkstra_dist = dijkstra(g, 0)[9]
    assert astar_dist == dijkstra_dist
