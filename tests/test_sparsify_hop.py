"""Tests for reachq.research.sparsify_hop (beta-hopbound-preserving
sparsification).

Regression: the earlier greedy removed a shortcut whenever the local
u -> v hop check passed, which could break OTHER pairs' beta-hopbound
(e.g. on a path n=30 the old output left 207 pairs above beta). The
correct greedy only removes a shortcut when the GLOBAL hopbound is
still preserved after removal.
"""

from __future__ import annotations

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.generators import random_dag
from reachq.core.graph import Digraph
from reachq.research.sparsify_hop import (
    sparsify_hop_bounded,
    verify_hopbound_preserved,
)


def path_graph(n: int) -> Digraph:
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


class TestSparsifyHopBounded:
    def test_global_hopbound_preserved_on_paths(self):
        for n in (20, 30, 50):
            g = path_graph(n)
            H, beta = build_shortcut_set_for_reachability(
                g,
                omega=3.0,
                random_seed=42,
                sparsify_shortcuts=False,
            )
            H2 = sparsify_hop_bounded(g, H, int(beta), max_iterations=200)
            assert H2 <= H
            assert verify_hopbound_preserved(g, H2, int(beta)), (
                f"beta-hopbound violated after sparsify (n={n})"
            )

    def test_global_hopbound_preserved_on_dag(self):
        g = random_dag(40, edge_probability=0.2, random_seed=42)
        H, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H2 = sparsify_hop_bounded(g, H, int(beta), max_iterations=200)
        assert verify_hopbound_preserved(g, H2, int(beta))

    def test_soundness_preserved(self):
        from reachq.core.reachability import bfs_reachability, parallel_bfs

        g = random_dag(30, edge_probability=0.3, random_seed=42)
        H, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H2 = sparsify_hop_bounded(g, H, int(beta))
        for s in g.vertices():
            assert bfs_reachability(g, s) == parallel_bfs(g, s, H2)

    def test_size_guard_returns_input_unchanged(self):
        g = path_graph(30)
        H, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H2 = sparsify_hop_bounded(g, H, int(beta), max_vertices=10)
        assert H2 == H

    def test_non_hopbound_input_refused(self):
        """If the input already violates the hopbound, sparsify is a no-op
        rather than making a false guarantee."""
        g = path_graph(20)
        # A clearly non-hopbound set: no shortcuts at all.
        H2 = sparsify_hop_bounded(g, set(), beta=2)
        assert H2 == set()

    def test_empty_input_is_noop(self):
        g = path_graph(10)
        H2 = sparsify_hop_bounded(g, set(), beta=3)
        assert H2 == set()


class TestVerifyHopboundPreserved:
    def test_returns_true_without_shortcuts_only_for_diameter(self):
        g = path_graph(10)
        # Diameter of the path is 9 > beta=3, so hopbound fails.
        assert not verify_hopbound_preserved(g, set(), beta=3)
        # With beta >= diameter it holds.
        assert verify_hopbound_preserved(g, set(), beta=9)

    def test_shortcuts_shrink_effective_diameter(self):
        g = path_graph(20)
        H, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        assert verify_hopbound_preserved(g, H, int(beta))
        assert not verify_hopbound_preserved(g, set(), int(beta))
