"""Tests for graph data structures."""

import pytest

from prspnsd.graph import Digraph, WeightedDigraph


class TestDigraph:
    """Tests for the unweighted Digraph class."""

    def test_empty_graph(self):
        g = Digraph()
        assert g.num_vertices() == 0
        assert g.num_edges() == 0
        assert g.vertices() == set()
        assert g.edges() == []

    def test_add_vertices_and_edges(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(0, 2)
        assert g.num_vertices() == 3
        assert g.num_edges() == 3
        assert g.vertices() == {0, 1, 2}
        assert set(g.edges()) == {(0, 1), (1, 2), (0, 2)}
        assert g.out_neighbors(0) == {1, 2}
        assert g.in_neighbors(2) == {1, 0}

    def test_has_edge(self):
        g = Digraph()
        g.add_edge(0, 1)
        assert g.has_edge(0, 1)
        assert not g.has_edge(1, 0)
        assert not g.has_edge(0, 2)

    def test_degree(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        g.add_edge(2, 1)
        assert g.degree_out(0) == 2
        assert g.degree_in(1) == 2
        assert g.degree_out(3) == 0

    def test_parallel_edges_deduped(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(0, 1)
        assert g.num_edges() == 1

    def test_induced_subgraph(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        sub = g.induced_subgraph({1, 2, 3})
        assert sub.num_vertices() == 3
        assert sub.num_edges() == 2
        assert set(sub.edges()) == {(1, 2), (2, 3)}

    def test_induced_subgraph_empty(self):
        g = Digraph()
        g.add_edge(0, 1)
        sub = g.induced_subgraph(set())
        assert sub.num_vertices() == 0
        assert sub.num_edges() == 0

    def test_copy_isolation(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        h = g.copy()
        assert h.num_vertices() == g.num_vertices()
        assert h.num_edges() == g.num_edges()
        h.add_edge(2, 0)
        assert g.num_edges() == 2
        assert h.num_edges() == 3

    def test_reversed(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        gr = g.reversed()
        assert gr.has_edge(1, 0)
        assert gr.has_edge(2, 1)
        assert not gr.has_edge(0, 1)

    def test_repr(self):
        g = Digraph()
        g.add_edge(0, 1)
        assert repr(g) == "Digraph(n=2, m=1)"

    def test_string_vertices(self):
        g = Digraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        assert g.num_vertices() == 3
        assert g.has_edge("a", "b")

    def test_tuple_vertices(self):
        g = Digraph()
        g.add_edge((0, 0), (0, 1))
        g.add_edge((0, 1), (1, 1))
        assert g.num_vertices() == 3
        assert g.has_edge((0, 0), (0, 1))


class TestWeightedDigraph:
    """Tests for the WeightedDigraph class."""

    def test_empty_graph(self):
        g = WeightedDigraph()
        assert g.num_vertices() == 0
        assert g.num_edges() == 0

    def test_add_weighted_edges(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(1, 2, 3)
        assert g.num_vertices() == 3
        assert g.num_edges() == 2
        assert g.out_neighbors(0) == {1: 5}
        assert g.in_neighbors(1) == {0: 5}

    def test_negative_weight_raises(self):
        g = WeightedDigraph()
        with pytest.raises(ValueError):
            g.add_edge(0, 1, -1)

    def test_has_edge_and_weight(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        assert g.has_edge(0, 1)
        assert g.get_weight(0, 1) == 5
        assert g.get_weight(1, 0) is None

    def test_parallel_edges_keep_min_weight(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(0, 1, 3)
        assert g.num_edges() == 1
        assert g.get_weight(0, 1) == 3

    def test_to_unweighted(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(1, 2, 3)
        u = g.to_unweighted()
        assert u.num_vertices() == 3
        assert u.num_edges() == 2
        assert set(u.edges()) == {(0, 1), (1, 2)}

    def test_reversed(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(1, 2, 3)
        gr = g.reversed()
        assert gr.has_edge(1, 0)
        assert gr.get_weight(1, 0) == 5
        assert gr.has_edge(2, 1)
        assert gr.get_weight(2, 1) == 3

    def test_copy_isolation(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        h = g.copy()
        h.add_edge(1, 2, 3)
        assert g.num_edges() == 1
        assert h.num_edges() == 2

    def test_degree(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(0, 2, 2)
        assert g.degree_out(0) == 2
        assert g.degree_in(1) == 1

    def test_induced_subgraph_weighted(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(1, 2, 3)
        g.add_edge(2, 3, 7)
        sub = g.induced_subgraph({1, 2, 3})
        assert sub.num_vertices() == 3
        assert sub.num_edges() == 2
        assert sub.get_weight(1, 2) == 3
        assert sub.get_weight(2, 3) == 7

    def test_repr(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        assert repr(g) == "WeightedDigraph(n=2, m=1)"
