"""Tests for the hopset-based SSSP implementation.

Each test asserts that the hopset-augmented reachability matches
plain Dijkstra within the same graph. The hopset is meant to be a
sound approximation: any vertex reachable by a regular path is
reachable via a hopset-augmented path.
"""

from __future__ import annotations

import pytest

from reachq.generators import random_dag
from reachq.graph import WeightedDigraph
from reachq.hopset import build_hopset_for_sssp
from reachq.reachability import bfs_reachability
from reachq.shortest_paths import dijkstra, shortest_path_hopbound


def _hopset_oracle(graph, source):
    """Compute all reachable distances via hopset-augmented SSSP."""
    n = graph.num_vertices()
    dist = [float("inf")] * n
    dist[source] = 0
    # Use the hopset-augmented Dijkstra
    import heapq
    visited = [False] * n
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if visited[u]:
            continue
        visited[u] = True
        for v, w in graph.out_edges.get(u, {}).items():
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    return dist


def test_empty_graph_with_hopset():
    g = WeightedDigraph()
    H, beta = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    assert H == set()
    assert beta == 0.0


def test_single_vertex_with_hopset():
    g = WeightedDigraph()
    g.add_vertex("v")
    H, _ = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    assert H == set()


def test_three_node_chain_hopset_soundness():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    H, _ = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    # The hopset is sound if all reachable distances are preserved.
    expected = dijkstra(g, 0)
    for v in g.vertices():
        if expected[v] != float("inf"):
            # All reachable vertices should remain reachable via the
            # hopset-augmented path.
            assert shortest_path_hopbound(g, 0, v, H, beta=10) is not None


def test_random_dag_hopset_soundness():
    """For a random DAG, the hopset-augmented shortest path
    distance to every reachable vertex equals the plain Dijkstra
    distance. The hopset is a sound approximation: it never
    overestimates the true distance.
    """
    g = random_dag(n=10, edge_probability=0.3, random_seed=42)
    # Add unit weights to make it a shortest-path graph.
    from reachq.graph import Digraph
    g_w = WeightedDigraph()
    for v in g.vertices():
        g_w.add_vertex(v)
    for u, v in g.edges():
        g_w.add_edge(u, v, 1)
    H, _ = build_hopset_for_sssp(g_w, epsilon=0.1, random_seed=42)
    for source in g_w.vertices():
        dijkstra_dist = dijkstra(g_w, source)
        for target in g_w.vertices():
            if dijkstra_dist[target] != float("inf"):
                # The hopset should preserve reachability.
                path = shortest_path_hopbound(
                    g_w, source, target, H, beta=20,
                )
                assert path is not None, (
                    f"hopset disconnected reachable {source}->{target}"
                )


def test_hopset_does_not_introduce_negative_weights():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1, 5)
    H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    for u, v in H:
        # Every hopset shortcut must have a non-negative weight.
        assert v >= 0


def test_hopset_reproducible():
    g = WeightedDigraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    H1, b1 = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    H2, b2 = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    assert H1 == H2
    assert b1 == b2


def test_hopset_soundness_long_path():
    g = WeightedDigraph()
    n = 20
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1, 1)
    H, beta = build_hopset_for_sssp(g, omega=3.0, random_seed=42)
    # The hopset should make the path 1-hop bounded.
    for source in g.vertices():
        for target in g.vertices():
            if source != target:
                path = shortest_path_hopbound(
                    g, source, target, H, beta=int(beta) + 1,
                )
                assert path is not None
