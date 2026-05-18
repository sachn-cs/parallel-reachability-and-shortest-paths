"""Tests for graph generators."""

import pytest

from prspnsd.generators import (
    complete_dag,
    cycle_graph,
    dense_graph,
    erdos_renyi_digraph,
    graph_stats,
    graph_with_sccs,
    grid_graph,
    layered_dag,
    path_graph,
    random_dag,
    weighted_dense_graph,
    weighted_path_graph,
    weighted_random_dag,
)
from prspnsd.graph import Digraph, WeightedDigraph
from prspnsd.reachability import strongly_connected_components


class TestPathGraph:
    def test_basic(self):
        g = path_graph(5)
        assert g.num_vertices() == 5
        assert g.num_edges() == 4
        assert g.has_edge(0, 1)
        assert g.has_edge(3, 4)
        assert not g.has_edge(4, 3)

    def test_n1(self):
        g = path_graph(1)
        assert g.num_vertices() == 1
        assert g.num_edges() == 0


class TestCycleGraph:
    def test_basic(self):
        g = cycle_graph(5)
        assert g.num_vertices() == 5
        assert g.num_edges() == 5
        assert g.has_edge(4, 0)

    def test_scc(self):
        g = cycle_graph(5)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 1


class TestCompleteDag:
    def test_basic(self):
        n = 5
        g = complete_dag(n)
        expected = n * (n - 1) // 2
        assert g.num_edges() == expected

    def test_acyclic(self):
        g = complete_dag(4)
        for i in range(4):
            for j in range(i + 1, 4):
                assert g.has_edge(i, j)
            for j in range(i):
                assert not g.has_edge(i, j)


class TestRandomDag:
    def test_deterministic(self):
        g1 = random_dag(10, edge_probability=0.3, random_seed=123)
        g2 = random_dag(10, edge_probability=0.3, random_seed=123)
        assert g1.num_edges() == g2.num_edges()
        assert set(g1.edges()) == set(g2.edges())

    def test_no_backward_edges(self):
        g = random_dag(20, edge_probability=0.5, random_seed=42)
        for u, v in g.edges():
            assert u < v


class TestErdosRenyi:
    def test_deterministic(self):
        g1 = erdos_renyi_digraph(10, 0.3, random_seed=7)
        g2 = erdos_renyi_digraph(10, 0.3, random_seed=7)
        assert set(g1.edges()) == set(g2.edges())

    def test_no_self_loops(self):
        g = erdos_renyi_digraph(10, 1.0, random_seed=1)
        for u, v in g.edges():
            assert u != v


class TestDenseGraph:
    def test_exact_edge_count(self):
        g = dense_graph(10, 50, random_seed=1)
        assert g.num_edges() == 50

    def test_raises_when_too_many(self):
        with pytest.raises(ValueError):
            dense_graph(5, 100)


class TestGraphWithSccs:
    def test_scc_sizes(self):
        sizes = [3, 4, 2]
        g = graph_with_sccs(sizes, random_seed=1)
        sccs = strongly_connected_components(g)
        assert len(sccs) == len(sizes)
        actual_sizes = sorted(len(s) for s in sccs)
        assert actual_sizes == sorted(sizes)

    def test_inter_edges_respect_order(self):
        sizes = [2, 2]
        g = graph_with_sccs(sizes, inter_edge_probability=1.0, random_seed=1)
        # SCC 0 should be {0,1}, SCC 1 should be {2,3}
        sccs = strongly_connected_components(g)
        scc_sets = [set(s) for s in sccs]
        # Find the SCC containing 0
        scc_0 = next(s for s in scc_sets if 0 in s)
        scc_1 = next(s for s in scc_sets if 2 in s)
        for u in scc_0:
            for v in scc_1:
                assert g.has_edge(u, v)


class TestLayeredDag:
    def test_structure(self):
        g = layered_dag([2, 3, 2], edge_probability=1.0, random_seed=1)
        assert g.num_vertices() == 7
        # All possible layer edges present
        for u in [(0, 0), (0, 1)]:
            for v in [(1, 0), (1, 1), (1, 2)]:
                assert g.has_edge(u, v)

    def test_no_edges_within_layer(self):
        g = layered_dag([3, 3], edge_probability=1.0, random_seed=1)
        for u, v in g.edges():
            assert u[0] != v[0]


class TestGridGraph:
    def test_basic(self):
        g = grid_graph(3, 3)
        assert g.num_vertices() == 9
        assert isinstance(g, WeightedDigraph)
        assert g.get_weight((0, 0), (1, 0)) == 1
        assert g.get_weight((0, 0), (0, 1)) == 1


class TestWeightedPathGraph:
    def test_weights(self):
        g = weighted_path_graph(5, weight_range=(1, 1), random_seed=1)
        assert g.num_edges() == 4
        for i in range(4):
            assert g.get_weight(i, i + 1) == 1


class TestWeightedRandomDag:
    def test_deterministic(self):
        g1 = weighted_random_dag(10, 0.3, weight_range=(1, 5), random_seed=7)
        g2 = weighted_random_dag(10, 0.3, weight_range=(1, 5), random_seed=7)
        assert set(g1.edges()) == set(g2.edges())
        for u, v, w in g1.edges():
            assert 1 <= w <= 5


class TestWeightedDenseGraph:
    def test_exact_edge_count(self):
        g = weighted_dense_graph(10, 50, random_seed=1)
        assert g.num_edges() == 50

    def test_raises_when_too_many(self):
        with pytest.raises(ValueError):
            weighted_dense_graph(5, 100)


class TestGraphStats:
    def test_stats(self):
        g = path_graph(10)
        stats = graph_stats(g)
        assert stats["n"] == 10
        assert stats["m"] == 9
        assert stats["max_out_degree"] == 1
        assert stats["max_in_degree"] == 1
