"""Tests for transitive closure computation."""

import pytest

from reachq.closure import (
    TransitiveClosureBudgetError,
    transitive_closure,
    transitive_closure_brute_force,
    transitive_closure_on_subset,
)
from reachq.graph import Digraph


class TestTransitiveClosureBruteForce:
    """Tests for brute-force transitive closure."""

    def test_empty_graph(self):
        g = Digraph()
        assert transitive_closure_brute_force(g) == set()

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        assert transitive_closure_brute_force(g) == {(0, 0)}

    def test_simple_path(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        expected = {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}
        assert transitive_closure_brute_force(g) == expected

    def test_cycle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        vertices = {0, 1, 2}
        expected = {(u, v) for u in vertices for v in vertices}
        assert transitive_closure_brute_force(g) == expected

    def test_disconnected(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        expected = {(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3)}
        assert transitive_closure_brute_force(g) == expected

    def test_triangle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(0, 2)
        expected = {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}
        assert transitive_closure_brute_force(g) == expected


class TestTransitiveClosure:
    """Boolean-semiring tests for transitive closure."""

    def test_empty_graph(self):
        g = Digraph()
        assert transitive_closure(g) == set()

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        assert transitive_closure(g) == {(0, 0)}

    def test_simple_path(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        expected = {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}
        assert transitive_closure(g) == expected

    def test_cycle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        vertices = {0, 1, 2}
        expected = {(u, v) for u in vertices for v in vertices}
        assert transitive_closure(g) == expected

    def test_disconnected(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        expected = {(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3)}
        assert transitive_closure(g) == expected

    def test_agrees_with_brute_force(self):
        g = Digraph()
        n = 15
        for i in range(n):
            for j in range(i + 1, n):
                if (i + j) % 3 == 0:
                    g.add_edge(i, j)
        assert transitive_closure(g) == transitive_closure_brute_force(g)

    def test_large_agrees_with_brute_force(self):
        g = Digraph()
        n = 30
        for i in range(n - 1):
            g.add_edge(i, i + 1)
            if i % 2 == 0 and i + 2 < n:
                g.add_edge(i, i + 2)
        assert transitive_closure(g) == transitive_closure_brute_force(g)

    def test_budget_raises_strict(self):
        g = Digraph()
        n = 100
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        with pytest.raises(TransitiveClosureBudgetError):
            transitive_closure(g, max_pairs=10)

    def test_budget_non_strict_returns_partial(self):
        g = Digraph()
        n = 50
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        result = transitive_closure(g, max_pairs=50, budget_strict=False)
        assert len(result) <= 50
        assert (0, 0) in result


class TestTransitiveClosureOnSubset:
    """Tests for transitive closure on a subset."""

    def test_basic(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        expected = {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}
        assert transitive_closure_on_subset(g, {0, 1, 2}) == expected

    def test_empty_subset(self):
        g = Digraph()
        g.add_edge(0, 1)
        assert transitive_closure_on_subset(g, set()) == set()

    def test_single_element_subset(self):
        g = Digraph()
        g.add_edge(0, 1)
        assert transitive_closure_on_subset(g, {0}) == {(0, 0)}


class TestLargeGraphOverflow:
    """Boolean semiring: no integer overflow on dense graphs."""

    def test_large_path_no_overflow(self):
        n = 200
        g = Digraph()
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        tc = transitive_closure(g)
        assert len(tc) == n * (n + 1) // 2
        for i in range(n):
            for j in range(i, n):
                assert (i, j) in tc

    def test_dense_graph_large_n(self):
        n = 150
        g = Digraph()
        for i in range(n):
            g.add_vertex(i)
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        tc = transitive_closure(g)
        assert len(tc) == n * (n + 1) // 2
