"""Tests for transitive closure computation."""


from prspnsd.graph import Digraph
from prspnsd.transitive_closure import (
    transitive_closure_brute_force,
    transitive_closure_matrix,
    transitive_closure_on_subset,
)


class TestTransitiveClosureBruteForce:
    """Tests for brute-force transitive closure."""

    def test_empty_graph(self):
        g = Digraph()
        tc = transitive_closure_brute_force(g)
        assert tc == set()

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        tc = transitive_closure_brute_force(g)
        assert tc == {(0, 0)}

    def test_simple_path(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        tc = transitive_closure_brute_force(g)
        assert tc == {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}

    def test_cycle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        tc = transitive_closure_brute_force(g)
        vertices = {0, 1, 2}
        expected = {(u, v) for u in vertices for v in vertices}
        assert tc == expected

    def test_disconnected(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        tc = transitive_closure_brute_force(g)
        assert tc == {(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3)}

    def test_triangle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(0, 2)
        tc = transitive_closure_brute_force(g)
        assert tc == {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}


class TestTransitiveClosureMatrix:
    """Tests for matrix-based transitive closure."""

    def test_empty_graph(self):
        g = Digraph()
        tc = transitive_closure_matrix(g)
        assert tc == set()

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        tc = transitive_closure_matrix(g)
        assert tc == {(0, 0)}

    def test_simple_path(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        tc = transitive_closure_matrix(g)
        assert tc == {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}

    def test_cycle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        tc = transitive_closure_matrix(g)
        vertices = {0, 1, 2}
        expected = {(u, v) for u in vertices for v in vertices}
        assert tc == expected

    def test_disconnected(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        tc = transitive_closure_matrix(g)
        assert tc == {(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3)}

    def test_agrees_with_brute_force(self):
        g = Digraph()
        n = 15
        for i in range(n):
            for j in range(i + 1, n):
                if (i + j) % 3 == 0:
                    g.add_edge(i, j)
        tc_matrix = transitive_closure_matrix(g)
        tc_brute = transitive_closure_brute_force(g)
        assert tc_matrix == tc_brute

    def test_large_agrees_with_brute_force(self):
        g = Digraph()
        n = 30
        for i in range(n - 1):
            g.add_edge(i, i + 1)
            if i % 2 == 0 and i + 2 < n:
                g.add_edge(i, i + 2)
        tc_matrix = transitive_closure_matrix(g)
        tc_brute = transitive_closure_brute_force(g)
        assert tc_matrix == tc_brute


class TestTransitiveClosureOnSubset:
    """Tests for transitive closure on a subset."""

    def test_basic(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        tc = transitive_closure_on_subset(g, {0, 1, 2})
        assert tc == {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}

    def test_empty_subset(self):
        g = Digraph()
        g.add_edge(0, 1)
        tc = transitive_closure_on_subset(g, set())
        assert tc == set()

    def test_single_element_subset(self):
        g = Digraph()
        g.add_edge(0, 1)
        tc = transitive_closure_on_subset(g, {0})
        assert tc == {(0, 0)}
