"""Tests for the hopset-based SSSP implementation.

Each test asserts that the hopset-augmented reachability matches
plain Dijkstra within the same graph. The hopset is a sound
approximation: any vertex reachable by a regular path is reachable
via a hopset-augmented path *and* the augmented distance equals
the exact Dijkstra distance for every reachable pair.
"""

from __future__ import annotations

from reachq.core.generators import random_dag
from reachq.core.graph import WeightedDigraph
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound


def test_empty_graph_with_hopset():
    g = WeightedDigraph()
    H, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    assert H == {}
    assert beta == 0.0


def test_single_vertex_with_hopset():
    g = WeightedDigraph()
    g.add_vertex("v")
    H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    assert H == {}


def test_three_node_chain_hopset_soundness():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    H, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    expected = dijkstra(g, 0)
    approx = shortest_path_hopbound(g, H, 0, max_hops=int(beta) + 5)
    for v in g.vertices():
        if v in expected:
            assert v in approx, f"hopset disconnected reachable 0->{v}"
            assert approx[v] == expected[v]


def test_random_dag_hopset_soundness():
    """For a random DAG the augmented distance equals the exact
    distance at every reachable vertex.
    """
    g = random_dag(n=10, edge_probability=0.3, random_seed=42)
    g_w = WeightedDigraph()
    for v in g.vertices():
        g_w.add_vertex(v)
    for u, v in g.edges():
        g_w.add_edge(u, v, 1)
    H, beta = build_hopset_for_sssp(g_w, epsilon=0.1, random_seed=42)
    for source in g_w.vertices():
        dijkstra_dist = dijkstra(g_w, source)
        approx = shortest_path_hopbound(g_w, H, source, max_hops=int(beta) + 5)
        for target in g_w.vertices():
            if target in dijkstra_dist:
                assert target in approx, f"hopset disconnected {source}->{target}"
                assert approx[target] == dijkstra_dist[target]


def test_hopset_weights_match_dijkstra():
    """Every hopset edge weight must equal the original-graph distance."""
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    for (u, v), w in H.items():
        assert isinstance(w, int) and w >= 0
        assert dijkstra(g, u)[v] == w


def test_hopset_reproducible():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    H1, b1 = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    H2, b2 = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    assert H1 == H2
    assert b1 == b2


def test_hopset_soundness_long_path():
    g = WeightedDigraph()
    n = 20
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1, 1)
    H, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    for source in g.vertices():
        approx = shortest_path_hopbound(
            g, H, source, max_hops=int(beta) + 1
        )
        plain = dijkstra(g, source)
        for target, d in plain.items():
            if target != source:
                assert target in approx
                assert approx[target] == d
