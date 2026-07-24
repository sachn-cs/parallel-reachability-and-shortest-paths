"""Edge-case tests for reachq.shortest_paths.

Each test exercises a single edge case: empty graph, single vertex,
negative weights (rejected), unreachable target, zero-weight edges,
self-loops, etc.
"""

from __future__ import annotations

import pytest

from reachq.core.graph import WeightedDigraph
from reachq.core.shortest_paths import dijkstra, shortest_path


def test_dijkstra_empty_graph():
    g = WeightedDigraph()
    assert dijkstra(g, 0) == {0: 0.0}


def test_dijkstra_single_vertex():
    g = WeightedDigraph()
    g.add_vertex("only")
    assert dijkstra(g, "only") == {"only": 0.0}


def test_dijkstra_unreachable_target():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    # No edge between 0 and 1.
    distances = dijkstra(g, 0)
    assert distances[0] == 0
    assert distances[1] == float("inf")


def test_dijkstra_zero_weight_edges():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 0)
    g.add_edge(1, 2, 0)
    d = dijkstra(g, 0)
    assert d[0] == 0.0
    assert d[1] == 0.0
    assert d[2] == 0.0


def test_dijkstra_self_loop_no_effect():
    """Self-loops are accepted by add_edge but contribute 0 to the
    shortest-path distance from a vertex to itself.
    """
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_edge(0, 0, 5)  # silently accepted
    distances = dijkstra(g, 0)
    assert distances[0] == 0


def test_dijkstra_negative_weight_rejected():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    with pytest.raises(ValueError, match="non-negative"):
        g.add_edge(0, 1, -1)


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
    assert shortest_path(g, 0, 0) == 0.0
    assert shortest_path(g, 1, 1) == 0.0


def test_shortest_path_unreachable():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    assert shortest_path(g, 0, 1) == float("inf")


def test_shortest_path_zero_weight():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 0)
    assert shortest_path(g, 0, 1) == 0.0


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
    # A->B->D = 1+3 = 4; A->C->D = 2+1 = 3. Pick the smaller.
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
    assert d[0] == 0.0
    assert d[1] == 1.0
    assert d[2] == float("inf")
    assert d[3] == float("inf")
