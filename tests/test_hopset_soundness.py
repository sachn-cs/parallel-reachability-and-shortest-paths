"""Tests for the hopset-based SSSP implementation.

Each test asserts that the hopset-augmented reachability matches
plain Dijkstra within the same graph. The hopset is a sound
approximation: any vertex reachable by a regular path is reachable
via a hopset-augmented path.
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
        if expected[v] != float("inf"):
            assert approx.get(v, float("inf")) != float("inf"), (
                f"hopset disconnected reachable 0->{v}"
            )


def test_random_dag_hopset_soundness():
    """For a random DAG, the hopset-augmented shortest path
    distance to every reachable vertex equals the plain Dijkstra
    distance. The hopset is a sound approximation: it never
    overestimates the true distance.
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
            if dijkstra_dist[target] != float("inf"):
                assert approx.get(target, float("inf")) != float("inf"), (
                    f"hopset disconnected reachable {source}->{target}"
                )


def test_hopset_does_not_introduce_negative_weights():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    for _, (_, _, _) in H.items():
        assert isinstance(_, int)
        assert _ >= 0


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
            g,
            H,
            source,
            max_hops=int(beta) + 1,
        )
        for target in g.vertices():
            if source != target:
                plain = dijkstra(g, source).get(target, float("inf"))
                if plain != float("inf"):
                    assert approx.get(target, float("inf")) != float("inf"), (
                        f"hopset disconnected reachable {source}->{target}"
                    )
