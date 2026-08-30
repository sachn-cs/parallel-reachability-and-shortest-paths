"""Differential test against NetworkX for shortest paths.

For every reachable (source, target) pair, the hopset-augmented
shortest-path distance equals the exact ``dijkstra`` distance.
Includes zero-weight edges, multi-SCC graphs, and bounded-hop
state-space verification.
"""

from __future__ import annotations

from importlib.util import find_spec

import pytest

from reachq.generators import random_dag, weighted_random_dag
from reachq.graph import WeightedDigraph
from reachq.hopset import build_hopset_for_sssp
from reachq.shortest_paths import (
    UNREACHABLE,
    dijkstra,
    shortest_path,
    shortest_path_hopbound,
)


pytestmark = pytest.mark.skipif(
    find_spec("networkx") is None,
    reason="networkx not installed",
)


def _nx_reference(g: WeightedDigraph) -> dict[tuple[object, object], int]:
    """NetworkX-based all-pairs shortest paths.

    Returns a flat ``(source, target) -> distance`` mapping.
    """
    import networkx as nx

    nxg = nx.DiGraph()
    for v in g.vertices():
        nxg.add_node(v)
    for u, v, w in g.edges():
        nxg.add_edge(u, v, weight=w)
    out: dict[tuple[object, object], int] = {}
    pairs = nx.all_pairs_dijkstra_path_length(nxg)
    for a, targets in pairs:
        for b, d in targets.items():
            out[(a, b)] = int(d)
    return out


class TestNetworkXDifferentialShortestPaths:
    def test_random_dag_5(self):
        g = random_dag(n=20, edge_probability=0.3, random_seed=1)
        gw = _to_weighted(g)
        reference = _nx_reference(gw)
        for u in gw.vertices():
            ours = dijkstra(gw, u)
            for v in gw.vertices():
                if v in ours:
                    assert ours[v] == reference.get((u, v), UNREACHABLE), (
                        f"disagree on {u}->{v}: ours={ours[v]} nx={reference.get((u, v), UNREACHABLE)}"
                    )

    def test_zero_weight_dag(self):
        g = WeightedDigraph()
        for i in range(5):
            g.add_vertex(i)
            for j in range(i):
                g.add_edge(j, i, 0)
        reference = _nx_reference(g)
        for u in g.vertices():
            ours = dijkstra(g, u)
            for v in g.vertices():
                if v in ours:
                    assert ours[v] == reference.get((u, v), UNREACHABLE)

    def test_weighted_random_dag(self):
        g = weighted_random_dag(n=15, edge_probability=0.3, random_seed=42)
        reference = _nx_reference(g)
        for u in g.vertices():
            ours = dijkstra(g, u)
            for v in g.vertices():
                if v in ours:
                    assert ours[v] == reference.get((u, v), UNREACHABLE)

    def test_shortest_path_returns_unreachable_sentinel(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        g.add_vertex(1)
        assert shortest_path(g, 0, 1) == UNREACHABLE

    def test_hopset_does_not_overestimate(self):
        """For every reachable (u, v), ``shortest_path_hopbound``
        returns the exact distance — never more, never less.
        """
        g = weighted_random_dag(n=10, edge_probability=0.4, random_seed=7)
        H, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=7)
        for u in g.vertices():
            exact = dijkstra(g, u)
            approx = shortest_path_hopbound(g, H, u, max_hops=int(beta) + 10)
            for v, d in exact.items():
                if v != u:
                    assert approx[v] == d, (
                        f"hopset over/underestimates {u}->{v}: "
                        f"exact={d} hopset={approx[v]}"
                    )


def _to_weighted(g):
    gw = WeightedDigraph()
    for v in g.vertices():
        gw.add_vertex(v)
    for u, v in g.edges():
        gw.add_edge(u, v, 1)
    return gw
