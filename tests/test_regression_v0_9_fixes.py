"""Regression tests for the v0.9.0 correctness fixes.

These tests pin each fix listed in ``docs/migration_0_9.md`` as
a regression test. A future refactor that re-introduces any of
these bugs will fail the corresponding test.
"""

from __future__ import annotations

import pytest

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.graph import Digraph, WeightedDigraph
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.shortest_paths import (
    dijkstra,
    shortest_path_hopbound,
    truncated_dijkstra,
)
from reachq.core.tc import (
    TransitiveClosureBudgetError,
    transitive_closure_boolean,
)


class TestGraphInsertionOrder:
    """Insertion order is preserved across all vertex iteration."""

    def test_vertices_returns_insertion_order(self):
        g = Digraph()
        for v in ["z", "a", "m", "b"]:
            g.add_vertex(v)
        assert g.vertices() == ("z", "a", "m", "b")


class TestWeightedDigraphValidation:
    """Weight validation rejects non-int, bool, NaN, inf."""

    def test_bool_rejected(self):
        g = WeightedDigraph()
        with pytest.raises(TypeError):
            g.add_edge(0, 1, True)

    def test_float_rejected(self):
        g = WeightedDigraph()
        with pytest.raises(TypeError):
            g.add_edge(0, 1, 1.5)

    def test_nan_rejected(self):
        g = WeightedDigraph()
        with pytest.raises(TypeError):
            g.add_edge(0, 1, float("nan"))

    def test_negative_rejected(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            g.add_edge(0, 1, -1)


class TestSspInputValidation:
    """Source membership and bound validation."""

    def test_dijkstra_unknown_source_raises(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(KeyError):
            dijkstra(g, 1)

    def test_truncated_dijkstra_negative_bound(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ValueError):
            truncated_dijkstra(g, 0, -1)

    def test_shortest_path_hopbound_max_hops_zero(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        dists = shortest_path_hopbound(g, {}, 0, max_hops=0)
        assert dists == {0: 0}


class TestLayeredHopbound:
    """Hop-bounded SSSP keeps per-(vertex, hops) state."""

    def test_cheaper_2_hop_arrival_not_suppressed(self):
        g = WeightedDigraph()
        g.add_edge("p", "q", 5)
        g.add_edge("p", "r", 0)
        g.add_edge("r", "q", 1)
        dists = shortest_path_hopbound(g, {}, "p", max_hops=2)
        assert dists["q"] == 1


class TestHopsetWeightAccuracy:
    """Every emitted hopset edge weight is the original distance."""

    def test_asymmetric_scc_no_underweight(self):
        g = WeightedDigraph()
        g.add_edge("a", "b", 100)
        g.add_edge("b", "a", 100)
        g.add_edge("b", "c", 1)
        H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        for (u, v), w in H.items():
            actual = dijkstra(g, u).get(v, 1 << 62)
            assert actual == w


class TestTransitiveClosureBoolean:
    """TC is in the Boolean semiring with explicit budget."""

    def test_path_closure_under_budget(self):
        g = Digraph()
        for i in range(20):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        tc = transitive_closure_boolean(g, max_pairs=10_000)
        assert (0, 19) in tc

    def test_budget_strict_raises(self):
        g = Digraph()
        for i in range(20):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        with pytest.raises(TransitiveClosureBudgetError):
            transitive_closure_boolean(g, max_pairs=10, budget_strict=True)


class TestShortcutSetReproducibility:
    """Shortcut sets are byte-stable across runs and processes."""

    def test_repeatability_in_process(self):
        g = Digraph()
        for i in range(15):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        s1, b1 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        s2, b2 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert s1 == s2
        assert b1 == b2


class TestRemovedModulesAndShims:
    """The migration to v0.9 removed thin wrappers and shims."""

    def test_jls_shortcut_set_not_present(self):
        """The legacy wrapper has been removed."""
        from reachq.core.algorithm import jls_with_tc_pruning

        assert callable(jls_with_tc_pruning)
        import reachq.core.algorithm as algo

        assert not hasattr(algo, "jls_shortcut_set"), (
            "thinned wrapper jls_shortcut_set should be removed"
        )

    def test_transitive_closure_matrix_not_present(self):
        import reachq.core.tc as tc

        assert not hasattr(tc, "transitive_closure_matrix"), (
            "old int32-typed TC should be replaced by transitive_closure_boolean"
        )
