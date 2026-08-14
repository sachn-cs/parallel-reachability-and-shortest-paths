"""Tests for graph generators."""

import pytest

from reachq.core.generators import (
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
from reachq.core.graph import WeightedDigraph
from reachq.core.reachability import strongly_connected_components


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


class TestSpectralGraphGenerators:
    """Tests for SRG / Hamming graph generators (from Papers 2/3)."""

    def test_petersen_graph_properties(self):
        from reachq.core.generators import petersen_graph

        g = petersen_graph()
        assert g.num_vertices() == 10
        # Petersen is 3-regular, triangle-free, girth 5.
        degrees = {len(g.out_edges.get(v, set())) for v in g.vertices()}
        assert degrees == {3}
        # No triangles: for every vertex, no two neighbours share an edge.
        for v in g.vertices():
            neighbors = g.out_edges[v]
            for u in neighbors:
                for w in neighbors:
                    if u < w and w in g.out_edges.get(u, set()):
                        raise AssertionError(f"triangle {v}-{u}-{w} in Petersen")

    def test_paley_graph_properties(self):
        from reachq.core.generators import paley_graph

        # Paley(5) is the 5-cycle C5: 5 undirected edges, 10 directed.
        g5 = paley_graph(5)
        assert g5.num_vertices() == 5
        assert g5.num_edges() == 10
        # Paley(13) is srg(13, 6, 2, 3): 13*6/2 = 39 undirected pairs,
        # 78 directed edges.
        g13 = paley_graph(13)
        assert g13.num_vertices() == 13
        assert g13.num_edges() == 78

    def test_paley_invalid_inputs(self):
        from reachq.core.generators import paley_graph

        with pytest.raises(ValueError, match="1"):
            paley_graph(3)
        with pytest.raises(ValueError, match="prime"):
            paley_graph(9)  # 9 ≡ 1 mod 4 but is not prime

    def test_shrikhande_rook_graph_properties(self):
        from reachq.core.generators import shrikhande_graph

        g = shrikhande_graph()
        assert g.num_vertices() == 16
        # Rook's graph (substituted for Shrikhande): 16 * 6 / 2 = 48 undirected
        # pairs, 96 directed edges.
        assert g.num_edges() == 96
        # 6-regular.
        degrees = {len(g.out_edges.get(v, set())) for v in g.vertices()}
        assert degrees == {6}

    def test_hamming_graph_properties(self):
        from reachq.core.generators import hamming_graph

        g = hamming_graph(d=2, q=3)  # 9 vertices, degree 4 (one per axis per direction)
        assert g.num_vertices() == 9
        # H(2,3) is 4-regular: each vertex has 2 coords × 2 directions = 4 neighbours.
        degrees = {len(g.out_edges.get(v, set())) for v in g.vertices()}
        assert degrees == {4}
        # H(d, q): q^d vertices of degree d*(q-1); directed edges = n*deg = 36 for H(2,3).
        assert g.num_edges() == 36

    def test_hamming_invalid_inputs(self):
        from reachq.core.generators import hamming_graph

        with pytest.raises(ValueError, match="d must be"):
            hamming_graph(d=0, q=2)
        with pytest.raises(ValueError, match="q must be"):
            hamming_graph(d=1, q=1)

    def test_srg_lam_mu_invariant(self):
        """The feasibility condition k(k - lam - 1) = (n - k - 1) * mu
        holds for all SRGs we generate. Testable directly on Petersen
        and the rook's graph.
        """
        from reachq.core.generators import petersen_graph, shrikhande_graph

        for label, g, k, lam, mu in [
            ("Petersen", petersen_graph(), 3, 0, 1),
            ("rook's (Shrikhande SRG)", shrikhande_graph(), 6, 2, 2),
        ]:
            n = g.num_vertices()
            assert k * (k - lam - 1) == (n - k - 1) * mu, (
                f"{label}: k(k-lam-1)={k * (k - lam - 1)} != (n-k-1)mu={(n - k - 1) * mu}"
            )
