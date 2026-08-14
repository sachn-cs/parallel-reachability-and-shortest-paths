"""Tests for hopset construction (CFR with TruncSSSP-Pruning)."""

import pytest

from reachq.core.graph import WeightedDigraph
from reachq.core.hopset import (
    build_hopset_for_sssp,
    cfr_hopset,
    cfr_with_truncsssp_pruning,
)
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound


class TestCfrHopset:
    """Tests for the baseline CFR hopset."""

    def test_preserves_distances_on_dag(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 3)
        g.add_edge(0, 3, 10)
        hopset = cfr_hopset(
            g,
            k=2.0,
            epsilon=0.1,
            max_level=3,
            n_global=g.num_vertices(),
            random_seed=42,
        )

        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=100)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d, f"Distance mismatch from {v} to {w}"

    def test_empty_graph(self):
        g = WeightedDigraph()
        hopset = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=1, n_global=0, random_seed=42
        )
        assert hopset == {}

    def test_single_vertex(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        hopset = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=1, n_global=1, random_seed=42
        )
        assert hopset == {}

    def test_two_vertices(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        hopset = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=2, n_global=2, random_seed=42
        )
        assert hopset == {}

    def test_invalid_k_raises(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ValueError):
            cfr_hopset(g, k=1.0, epsilon=0.1, max_level=1, n_global=1)

    def test_invalid_epsilon_raises(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ValueError):
            cfr_hopset(g, k=2.0, epsilon=0.0, max_level=1, n_global=1)

    def test_invalid_max_level_raises(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ValueError):
            cfr_hopset(g, k=2.0, epsilon=0.1, max_level=-1, n_global=1)

    def test_recursive_subparts(self):
        """Larger graph to trigger recursive partition into sub-parts."""
        g = WeightedDigraph()
        n = 40
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        hopset = cfr_hopset(
            g, k=2.0, epsilon=0.5, max_level=4, n_global=n, random_seed=42
        )
        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=n)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d

    def test_reproducibility(self):
        g = WeightedDigraph()
        for i in range(20):
            g.add_edge(i, i + 1, 1)
        h1 = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=3, n_global=21, random_seed=123
        )
        h2 = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=3, n_global=21, random_seed=123
        )
        assert h1 == h2


class TestCfrWithTruncssspPruning:
    """Tests for CFR with TruncSSSP-Pruning."""

    def test_preserves_distances_on_dag(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 3)
        g.add_edge(0, 3, 10)
        hopset = cfr_with_truncsssp_pruning(
            g,
            k=2.0,
            epsilon=0.1,
            rho=1.0,
            max_level=3,
            n_global=g.num_vertices(),
            random_seed=42,
        )

        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=100)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d

    def test_truncsssp_adds_edges(self):
        g = WeightedDigraph()
        n = 20
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)

        hopset_base = cfr_hopset(
            g, k=2.0, epsilon=0.1, max_level=4, n_global=n, random_seed=42
        )
        hopset_trunc = cfr_with_truncsssp_pruning(
            g, k=2.0, epsilon=0.1, rho=2.0, max_level=4, n_global=n, random_seed=42
        )

        assert len(hopset_trunc) >= len(hopset_base)

    def test_invalid_k_raises(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            cfr_with_truncsssp_pruning(
                g, k=1.0, epsilon=0.1, rho=1.0, max_level=1, n_global=1
            )

    def test_invalid_epsilon_raises(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            cfr_with_truncsssp_pruning(
                g, k=2.0, epsilon=0.0, rho=1.0, max_level=1, n_global=1
            )

    def test_invalid_rho_raises(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            cfr_with_truncsssp_pruning(
                g, k=2.0, epsilon=0.1, rho=0.0, max_level=1, n_global=1
            )

    def test_invalid_max_level_raises(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            cfr_with_truncsssp_pruning(
                g, k=2.0, epsilon=0.1, rho=1.0, max_level=-1, n_global=1
            )

    def test_recursive_subparts_with_truncsssp(self):
        """Larger graph to trigger recursive sub-parts and truncsssp pruning."""
        g = WeightedDigraph()
        n = 40
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        hopset = cfr_with_truncsssp_pruning(
            g, k=2.0, epsilon=0.5, rho=2.0, max_level=4, n_global=n, random_seed=42
        )
        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=n)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d

    def test_reproducibility(self):
        g = WeightedDigraph()
        for i in range(20):
            g.add_edge(i, i + 1, 1)
        h1 = cfr_with_truncsssp_pruning(
            g, k=2.0, epsilon=0.1, rho=1.0, max_level=3, n_global=21, random_seed=123
        )
        h2 = cfr_with_truncsssp_pruning(
            g, k=2.0, epsilon=0.1, rho=1.0, max_level=3, n_global=21, random_seed=123
        )
        assert h1 == h2


class TestBuildHopsetForSssp:
    """Tests for the high-level hopset wrapper."""

    def test_end_to_end_on_dag(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 3)
        g.add_edge(0, 3, 10)
        hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert beta > 0

        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=100)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d

    def test_end_to_end_on_graph_with_scc(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 1)
        g.add_edge(2, 0, 1)  # SCC
        g.add_edge(2, 3, 5)
        hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert beta > 0

        for v in g.vertices():
            original = dijkstra(g, v)
            with_hopset = shortest_path_hopbound(g, hopset, v, max_hops=100)
            for w in g.vertices():
                orig_d = original.get(w, float("inf"))
                hop_d = with_hopset.get(w, float("inf"))
                assert orig_d == hop_d

    def test_long_path(self):
        g = WeightedDigraph()
        n = 50
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert beta > 0
        with_hopset = shortest_path_hopbound(g, hopset, 0, max_hops=100)
        assert (n - 1) in with_hopset

    def test_empty_graph(self):
        g = WeightedDigraph()
        hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert hopset == {}
        assert beta == 0.0

    def test_single_vertex(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        hopset, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert hopset == {}

    def test_reproducibility(self):
        g = WeightedDigraph()
        for i in range(20):
            g.add_edge(i, i + 1, 1)
        h1, b1 = build_hopset_for_sssp(g, epsilon=0.1, random_seed=123)
        h2, b2 = build_hopset_for_sssp(g, epsilon=0.1, random_seed=123)
        assert h1 == h2
        assert b1 == b2

    @pytest.mark.slow
    def test_stress_large_path(self):
        g = WeightedDigraph()
        n = 200
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        assert beta > 0
        with_hopset = shortest_path_hopbound(g, hopset, 0, max_hops=1000)
        assert (n - 1) in with_hopset
        assert with_hopset[n - 1] == n - 1
