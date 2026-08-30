"""Edge-case tests for reachq.shortest_paths.

Each test exercises a single edge case: empty graph, single vertex,
negative weights (rejected), unreachable target, zero-weight edges,
self-loops, etc.

The contract here is the v0.9 contract: unreachable vertices are
absent from the distance map; ``shortest_path`` reports a sentinel
larger than any polynomial weight for unreachable targets;
``dijkstra`` raises ``KeyError`` for sources not in the graph.
"""

from __future__ import annotations

import math

import pytest

from reachq.core.graph import WeightedDigraph
from reachq.core.shortest_paths import UNREACHABLE, dijkstra, shortest_path


def test_dijkstra_empty_graph():
    g = WeightedDigraph()
    with pytest.raises(KeyError):
        dijkstra(g, 0)


def test_dijkstra_single_vertex():
    g = WeightedDigraph()
    g.add_vertex("only")
    assert dijkstra(g, "only") == {"only": 0}


def test_dijkstra_unreachable_target():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    distances = dijkstra(g, 0)
    assert distances[0] == 0
    assert 1 not in distances


def test_dijkstra_zero_weight_edges():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 0)
    g.add_edge(1, 2, 0)
    d = dijkstra(g, 0)
    assert d[0] == 0
    assert d[1] == 0
    assert d[2] == 0


def test_dijkstra_self_loop_no_effect():
    """Self-loops are accepted by add_edge but contribute 0 to the
    shortest-path distance from a vertex to itself.
    """
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_edge(0, 0, 5)
    distances = dijkstra(g, 0)
    assert distances[0] == 0


def test_dijkstra_negative_weight_rejected():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    with pytest.raises(ValueError, match="non-negative"):
        g.add_edge(0, 1, -1)


def test_dijkstra_non_integer_weight_rejected():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    with pytest.raises(TypeError):
        g.add_edge(0, 1, 1.5)
    with pytest.raises(TypeError):
        g.add_edge(0, 1, math.inf)


def test_dijkstra_keeps_minimum_weight():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 10)
    g.add_edge(0, 1, 5)
    g.add_edge(0, 1, 7)
    assert dijkstra(g, 0)[1] == 5


def test_shortest_path_source_equals_target():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    assert shortest_path(g, 0, 0) == 0
    assert shortest_path(g, 1, 1) == 0


def test_shortest_path_unreachable():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    assert shortest_path(g, 0, 1) == UNREACHABLE


def test_shortest_path_zero_weight():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 0)
    assert shortest_path(g, 0, 1) == 0


def test_shortest_path_long_path():
    g = WeightedDigraph()
    n = 10
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1, 1)
    assert shortest_path(g, 0, n - 1) == n - 1


def test_dijkstra_multiple_paths():
    g = WeightedDigraph()
    g.add_vertex("A")
    g.add_vertex("B")
    g.add_vertex("C")
    g.add_vertex("D")
    g.add_edge("A", "B", 1)
    g.add_edge("A", "C", 2)
    g.add_edge("B", "D", 3)
    g.add_edge("C", "D", 1)
    d = dijkstra(g, "A")
    assert d["D"] == 3


def test_dijkstra_disconnected_components():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_vertex(3)
    g.add_edge(0, 1, 1)
    g.add_edge(2, 3, 1)
    d = dijkstra(g, 0)
    assert d[0] == 0
    assert d[1] == 1
    assert 2 not in d
    assert 3 not in d
