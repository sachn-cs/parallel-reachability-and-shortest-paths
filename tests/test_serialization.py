"""Tests for serialization and deserialization."""

import pytest

from prspnsd.generators import path_graph, weighted_path_graph
from prspnsd.graph import Digraph, WeightedDigraph
from prspnsd.serialization import (
    digraph_from_dict,
    digraph_from_json,
    digraph_to_dict,
    digraph_to_json,
    weighted_digraph_from_dict,
    weighted_digraph_from_json,
    weighted_digraph_to_dict,
    weighted_digraph_to_json,
)


class TestDigraphSerialization:
    def test_roundtrip(self):
        g = path_graph(5)
        text = digraph_to_json(g)
        h = digraph_from_json(text)
        assert g.num_vertices() == h.num_vertices()
        assert g.num_edges() == h.num_edges()
        assert set(g.edges()) == set(h.edges())

    def test_dict_roundtrip(self):
        g = path_graph(4)
        d = digraph_to_dict(g)
        h = digraph_from_dict(d)
        assert set(g.vertices()) == set(h.vertices())
        assert set(g.edges()) == set(h.edges())

    def test_empty_graph(self):
        g = Digraph()
        text = digraph_to_json(g)
        h = digraph_from_json(text)
        assert h.num_vertices() == 0
        assert h.num_edges() == 0

    def test_tuple_vertices(self):
        g = Digraph()
        g.add_edge((0, 0), (0, 1))
        text = digraph_to_json(g)
        h = digraph_from_json(text)
        assert h.has_edge((0, 0), (0, 1))

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            digraph_from_dict({"type": "WeightedDigraph"})


class TestWeightedDigraphSerialization:
    def test_roundtrip(self):
        g = weighted_path_graph(5, weight_range=(1, 3), random_seed=1)
        text = weighted_digraph_to_json(g)
        h = weighted_digraph_from_json(text)
        assert g.num_vertices() == h.num_vertices()
        assert g.num_edges() == h.num_edges()
        for u, v, w in g.edges():
            assert h.get_weight(u, v) == w

    def test_dict_roundtrip(self):
        g = weighted_path_graph(4, weight_range=(1, 2), random_seed=1)
        d = weighted_digraph_to_dict(g)
        h = weighted_digraph_from_dict(d)
        assert set(g.vertices()) == set(h.vertices())
        for u, v, w in g.edges():
            assert h.get_weight(u, v) == w

    def test_empty_graph(self):
        g = WeightedDigraph()
        text = weighted_digraph_to_json(g)
        h = weighted_digraph_from_json(text)
        assert h.num_vertices() == 0
        assert h.num_edges() == 0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            weighted_digraph_from_dict({"type": "Digraph"})
