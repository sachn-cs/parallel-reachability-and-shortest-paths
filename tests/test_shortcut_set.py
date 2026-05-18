"""Tests for shortcut set construction (JLS and JLS with TC-Pruning)."""

import pytest

from prspnsd.graph import Digraph
from prspnsd.reachability import bfs_reachability, parallel_bfs
from prspnsd.shortcut_set import (
    build_shortcut_set_for_reachability,
    jls_shortcut_set,
    jls_with_tc_pruning,
)


class TestJlsShortcutSet:
    """Tests for the baseline JLS shortcut set."""

    def test_preserves_reachability_on_dag(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(0, 3)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=3, n_global=g.num_vertices(), random_seed=42)

        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts, f"Reachability mismatch from {v}"

    def test_shortcuts_reduce_hops(self):
        g = Digraph()
        n = 10
        for i in range(n - 1):
            g.add_edge(i, i + 1)

        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=4, n_global=n, random_seed=42)
        reached = parallel_bfs(g, 0, shortcuts)
        assert 9 in reached

    def test_empty_graph(self):
        g = Digraph()
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=1, n_global=0, random_seed=42)
        assert shortcuts == set()

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=1, n_global=1, random_seed=42)
        assert shortcuts == set()

    def test_two_vertices(self):
        g = Digraph()
        g.add_edge(0, 1)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=2, n_global=2, random_seed=42)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_disconnected_graph(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=3, n_global=4, random_seed=42)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_star_graph(self):
        g = Digraph()
        n = 20
        for i in range(1, n):
            g.add_edge(0, i)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=3, n_global=n, random_seed=42)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_binary_tree(self):
        g = Digraph()
        n = 31
        for i in range(1, n):
            parent = (i - 1) // 2
            g.add_edge(parent, i)
        shortcuts = jls_shortcut_set(
            g, k=2.0, max_level=4, n_global=n, random_seed=42)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_reproducibility(self):
        g = Digraph()
        for i in range(20):
            g.add_edge(i, i + 1)
        s1 = jls_shortcut_set(g, k=2.0, max_level=3, n_global=21, random_seed=123)
        s2 = jls_shortcut_set(g, k=2.0, max_level=3, n_global=21, random_seed=123)
        assert s1 == s2


class TestJlsWithTcPruning:
    """Tests for JLS with TC-Pruning."""

    def test_preserves_reachability_on_dag(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(0, 3)
        shortcuts = jls_with_tc_pruning(
            g, k=2.0, rho=1.0, max_level=3,
            n_global=g.num_vertices(), random_seed=42)

        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts, f"Reachability mismatch from {v}"

    def test_tc_pruning_adds_extra_edges(self):
        g = Digraph()
        n = 20
        for i in range(n - 1):
            g.add_edge(i, i + 1)

        shortcuts_base = jls_shortcut_set(
            g, k=2.0, max_level=4, n_global=n, random_seed=42)
        shortcuts_tc = jls_with_tc_pruning(
            g, k=2.0, rho=2.0, max_level=4, n_global=n, random_seed=42)

        assert len(shortcuts_tc) >= len(shortcuts_base)

    def test_empty_graph(self):
        g = Digraph()
        shortcuts = jls_with_tc_pruning(
            g, k=2.0, rho=1.0, max_level=1, n_global=0, random_seed=42)
        assert shortcuts == set()

    def test_invalid_k_raises(self):
        g = Digraph()
        with pytest.raises(ValueError):
            jls_with_tc_pruning(g, k=1.0, rho=1.0, max_level=1, n_global=1)

    def test_invalid_rho_raises(self):
        g = Digraph()
        with pytest.raises(ValueError):
            jls_with_tc_pruning(g, k=2.0, rho=0.0, max_level=1, n_global=1)

    def test_invalid_max_level_raises(self):
        g = Digraph()
        with pytest.raises(ValueError):
            jls_with_tc_pruning(g, k=2.0, rho=1.0, max_level=-1, n_global=1)

    def test_reproducibility(self):
        g = Digraph()
        for i in range(20):
            g.add_edge(i, i + 1)
        s1 = jls_with_tc_pruning(g, k=2.0, rho=1.0, max_level=3, n_global=21, random_seed=123)
        s2 = jls_with_tc_pruning(g, k=2.0, rho=1.0, max_level=3, n_global=21, random_seed=123)
        assert s1 == s2

    def test_dense_graph(self):
        g = Digraph()
        n = 15
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        shortcuts = jls_with_tc_pruning(
            g, k=2.0, rho=1.0, max_level=3, n_global=n, random_seed=42)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts


class TestBuildShortcutSetForReachability:
    """Tests for the high-level shortcut set wrapper."""

    def test_end_to_end_on_dag(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(0, 3)
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert beta > 0

        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_end_to_end_on_graph_with_scc(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)  # SCC
        g.add_edge(2, 3)
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert beta > 0

        for v in g.vertices():
            original = bfs_reachability(g, v)
            with_shortcuts = parallel_bfs(g, v, shortcuts)
            assert original == with_shortcuts

    def test_long_path(self):
        g = Digraph()
        n = 50
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert beta > 0
        reached = parallel_bfs(g, 0, shortcuts)
        assert (n - 1) in reached

    def test_empty_graph(self):
        g = Digraph()
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert shortcuts == set()
        assert beta == 0.0

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert shortcuts == set()

    def test_reproducibility(self):
        g = Digraph()
        for i in range(20):
            g.add_edge(i, i + 1)
        s1, b1 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=123)
        s2, b2 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=123)
        assert s1 == s2
        assert b1 == b2

    @pytest.mark.slow
    def test_stress_large_path(self):
        g = Digraph()
        n = 200
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert beta > 0
        reached = parallel_bfs(g, 0, shortcuts)
        assert (n - 1) in reached
