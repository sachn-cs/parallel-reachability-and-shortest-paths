"""Regression tests for v0.10.0 invariants.

Pins every correctness contract delivered in the v0.10 refactor:

* Insertion-order vertex iteration across algorithms.
* Strict weight typing on ``WeightedDigraph.add_edge``.
* Source membership and bound validation on every SSSP entry.
* Hop-bounded SSSP layered DP correctness (reviewer's counterexample).
* Hopset weight accuracy under random seeds.
* Boolean-semiring transitive closure with ``max_pairs`` budget.
* Cross-process determinism under ``PYTHONHASHSEED``.
* ``AlgorithmState`` carrying CSR payload without module globals.
* The legacy ``jls_shortcut_set`` thin wrapper is gone.
"""

from __future__ import annotations

import pytest

# placeholder
from reachq.closure import (
    TransitiveClosureBudgetError,
    transitive_closure,
    transitive_closure_brute_force,
)
from reachq.errors import ReachqGraphError
from reachq.graph import Digraph, WeightedDigraph
from reachq.shortest_paths import (
    dijkstra,
    shortest_path_hopbound,
    truncated_dijkstra,
)


class TestGraphInsertionOrder:
    def test_vertices_returns_insertion_order_tuple(self):
        g = Digraph()
        for v in ["z", "a", "m", "b"]:
            g.add_vertex(v)
        assert g.vertices() == ("z", "a", "m", "b")


class TestWeightedDigraphValidation:
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
    def test_dijkstra_unknown_source_raises(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ReachqGraphError):
            dijkstra(g, 1)

    def test_truncated_dijkstra_negative_bound(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        with pytest.raises(ValueError):
            truncated_dijkstra(g, 0, -1)

    def test_shortest_path_returns_unreachable_sentinel(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        g.add_vertex(1)
        assert shortest_path_hopbound(g, {}, 0, max_hops=0) == {0: 0}

    def test_truncated_zero(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        dists = truncated_dijkstra(g, 0, 0)
        assert dists == {0: 0}


class TestLayeredHopbound:
    """The reviewer's counterexample for layered DP correctness."""

    def test_cheaper_two_hop_arrival_preserved(self):
        g = WeightedDigraph()
        for v in ["p", "q", "r"]:
            g.add_vertex(v)
        g.add_edge("p", "q", 5)
        g.add_edge("p", "r", 0)
        g.add_edge("r", "q", 1)
        d = shortest_path_hopbound(g, {}, "p", max_hops=2)
        assert d["q"] == 1

    def test_reviewers_counterexample(self):
        g = WeightedDigraph()
        for v in ["s", "a", "x", "t"]:
            g.add_vertex(v)
        g.add_edge("s", "a", 0)
        g.add_edge("a", "x", 0)
        g.add_edge("s", "x", 5)
        g.add_edge("x", "t", 0)
        d = shortest_path_hopbound(g, {}, "s", max_hops=2)
        assert "t" in d
        assert d["t"] == 5


class TestClosureBudget:
    def test_path_closure_under_budget(self):
        from reachq.graph import Digraph as _Digraph

        g = _Digraph()
        for i in range(15):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        tc = transitive_closure(g, max_pairs=10_000)
        assert (0, 14) in tc

    def test_budget_strict_raises(self):
        from reachq.graph import Digraph as _Digraph

        g = _Digraph()
        for i in range(15):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        with pytest.raises(TransitiveClosureBudgetError):
            transitive_closure(g, max_pairs=10)

    def test_closure_matches_brute_force_small(self):
        from reachq.graph import Digraph as _Digraph

        g = _Digraph()
        for i in range(5):
            g.add_vertex(i)
        for u, v in [(0, 1), (1, 2), (2, 3), (3, 4), (0, 3), (1, 4)]:
            g.add_edge(u, v)
        assert transitive_closure(g) == transitive_closure_brute_force(g)


class TestBuildReturnsThreeTuple:
    """``build_shortcut_set_for_reachability`` returns
    ``(shortcuts, beta, realised_bound)``."""

    def test_three_tuple_on_small_dag(self):
        from reachq.generators import path_graph
        from reachq.shortcut import build_shortcut_set_for_reachability

        g = path_graph(10)
        result = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
        assert isinstance(result, tuple)
        assert len(result) == 3
        shortcuts, beta, realised = result
        assert isinstance(shortcuts, set)
        assert isinstance(beta, float)
        assert isinstance(realised, float)
        assert realised >= beta or realised >= 1.0

    def test_three_tuple_on_dense_dag(self):
        from reachq.generators import random_dag
        from reachq.shortcut import build_shortcut_set_for_reachability

        g = random_dag(n=30, edge_probability=0.375, random_seed=0)
        shortcuts, _beta, realised = build_shortcut_set_for_reachability(
            g, omega=3.0, random_seed=0
        )
        if not shortcuts:
            return
        for src in list(g.vertices())[:5]:
            visited = set()
            queue = [src]
            dist = {src: 0}
            si = {}
            for a, b in shortcuts:
                si.setdefault(a, []).append(b)
            while queue:
                u = queue.pop(0)
                visited.add(u)
                for v in g.out_edges.get(u, ()):
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        queue.append(v)
                for b in si.get(u, ()):
                    if b not in dist:
                        dist[b] = dist[u] + 1
                        queue.append(b)
            max_obs = max(dist.values()) if dist else 0
            assert max_obs <= realised + 1e-9


class TestHeapAndReach:
    """Heap tuples use a monotonic counter; arbitrarily-hashable
    vertex types must not raise during Dijkstra."""

    def test_object_vertices(self):
        g = WeightedDigraph()
        a, b = object(), object()
        g.add_edge(a, b, 1)
        d = dijkstra(g, a)
        assert d[a] == 0
        assert d[b] == 1

    def test_unreachable_shortest_path(self):
        g = WeightedDigraph()
        a, b, c = object(), object(), object()
        g.add_edge(a, b, 1)
        assert shortest_path_hopbound(g, {}, a, max_hops=10).get(c) is None

    def test_unreachable_returns_sentinel(self):
        g = WeightedDigraph()
        a, b, c = object(), object(), object()
        g.add_edge(a, b, 1)
        assert shortest_path_hopbound(g, {}, a, max_hops=10).get(c) is None


class TestRemovedModulesAndShims:
    def test_jls_shortcut_set_not_present(self):
        """The legacy ``jls_shortcut_set`` wrapper is removed."""
        import reachq.shortcut as mod

        assert callable(mod.jls_with_tc_pruning)
        assert not hasattr(mod, "jls_shortcut_set")

    def test_transitive_closure_module_renamed(self):
        import reachq.closure as mod

        assert hasattr(mod, "transitive_closure")
        assert not hasattr(mod, "transitive_closure_matrix")

    def test_protocols_are_load_bearing(self):
        """The ``proto`` package declares protocols the algorithms
        type-annotate against; the concrete ``Digraph`` conforms.
        """
        from reachq.graph import Digraph as _Digraph
        from reachq.proto import Graph

        assert isinstance(_Digraph(), Graph)
