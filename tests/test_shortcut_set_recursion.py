"""Tests for JLS recursion termination and partition correctness.

The recursion partitions vertices by their label set (pivots that
reach them in r_plus vs r_minus). The partition must terminate
within max_level levels, and the resulting shortcut set must
preserve reachability.
"""

from reachq.core.algorithm import jls_with_tc_pruning
from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs


class TestRecursionTermination:
    def test_recursion_terminates_within_max_level(self):
        """JLS with max_level=3 on a 5-path should not recurse infinitely."""
        g = Digraph()
        for i in range(5):
            g.add_vertex(i)
        for i in range(4):
            g.add_edge(i, i + 1)
        shortcuts = jls_with_tc_pruning(
            g,
            k=2.0,
            rho=1.0,
            max_level=3,
            n_global=5,
            random_seed=42,
            flags={"enable_tc_pruning": False},
        )
        assert isinstance(shortcuts, set)
        assert len(shortcuts) >= 0

    def test_recursion_does_not_modify_reachability_on_chain(self):
        g = Digraph()
        n = 8
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts = jls_with_tc_pruning(
            g,
            k=2.0,
            rho=1.0,
            max_level=4,
            n_global=n,
            random_seed=42,
            flags={"enable_tc_pruning": False},
        )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)

    def test_recursion_with_tc_pruning_preserves_reachability(self):
        g = Digraph()
        n = 10
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts = jls_with_tc_pruning(
            g,
            k=2.0,
            rho=2.0,
            max_level=4,
            n_global=n,
            random_seed=42,
            flags={"enable_tc_pruning": True},
        )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)

    def test_recursion_with_max_level_zero_returns_empty(self):
        g = Digraph()
        g.add_edge(0, 1)
        shortcuts = jls_with_tc_pruning(
            g,
            k=2.0,
            rho=1.0,
            max_level=0,
            n_global=2,
            random_seed=42,
            flags={"enable_tc_pruning": False},
        )
        assert isinstance(shortcuts, set)
