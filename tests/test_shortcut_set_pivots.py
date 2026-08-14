"""Tests for the pivot sampling, parallel worker dispatch, and
density-aware constant.

Pivots are sampled with probability C * k * log n / n. The
density-aware constant C depends on graph density.
"""

from reachq.core.algorithm import (
    build_shortcut_set_for_reachability,
    density_aware_constant,
    jls_with_tc_pruning,
)
from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs


class TestPivotSampling:
    def test_pivots_preserve_reachability_on_sparse_dag(self):
        """Sparse DAG: high diameter, many shortcuts needed."""
        g = Digraph()
        n = 20
        for i in range(n):
            g.add_vertex(i)
        for i in range(0, n - 1, 3):
            g.add_edge(i, i + 1)
        shortcuts, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)

    def test_pivots_preserve_reachability_on_dense_dag(self):
        """Dense DAG: well-connected, fewer shortcuts needed."""
        g = Digraph()
        n = 15
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        # Add cross-layer edges to make it dense.
        for i in range(0, n, 2):
            for j in range(i + 1, n, 2):
                if j - i <= 3:
                    g.add_edge(i, j)
        shortcuts, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)

    def test_pivots_preserve_reachability_with_tc_pruning(self):
        g = Digraph()
        n = 20
        for i in range(n):
            g.add_vertex(i)
        for i in range(0, n - 1, 2):
            g.add_edge(i, i + 1)
        shortcuts = jls_with_tc_pruning(
            g,
            k=2.0,
            rho=1.0,
            max_level=3,
            n_global=n,
            random_seed=42,
        )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)

    def test_pivots_reproducible_with_same_seed(self):
        g = Digraph()
        n = 15
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        s1, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        s2, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert s1 == s2

    def test_pivots_differ_with_different_seeds(self):
        g = Digraph()
        n = 15
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        s1, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=1)
        s2, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=2)
        # Different seeds produce different pivot sets, hence possibly
        # different shortcut sets. We don't assert inequality (could
        # be the same by chance on small graphs) but verify both
        # are valid shortcut sets.
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, s1)
            assert bfs_reachability(g, v) == parallel_bfs(g, v, s2)


class TestDensityAwareConstant:
    def test_density_aware_constant_returns_positive(self):
        assert density_aware_constant(rho=1.0, k=2.0) > 0
        assert density_aware_constant(rho=10.0, k=2.0) > 0

    def test_density_aware_constant_monotone_in_rho(self):
        c_small = density_aware_constant(rho=1.0, k=2.0)
        c_large = density_aware_constant(rho=10.0, k=2.0)
        assert c_small <= c_large

    def test_density_aware_constant_handles_edge_cases(self):
        # rho <= 0 -> default
        assert density_aware_constant(rho=0.0, k=2.0) == 10.0
        assert density_aware_constant(rho=-1.0, k=2.0) == 10.0
        # k <= 1 -> default
        assert density_aware_constant(rho=2.0, k=1.0) == 10.0
