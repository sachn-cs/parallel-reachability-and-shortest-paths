"""Tests for graph data structures."""

import pytest

from reachq.graph import Digraph, WeightedDigraph, contract_sccs, partition_by_labels


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


class TestPartitionByLabels:
    """Tests for the partition_by_labels utility."""

    def test_single_group(self):
        labels = {0: {"A"}, 1: {"A"}, 2: {"A"}}
        parts = partition_by_labels({0, 1, 2}, labels)
        assert len(parts) == 1
        assert parts[0] == {0, 1, 2}

    def test_multiple_groups(self):
        labels = {0: {"A"}, 1: {"A"}, 2: {"B"}}
        parts = partition_by_labels({0, 1, 2}, labels)
        assert len(parts) == 2
        by_size = sorted(parts, key=len, reverse=True)
        assert by_size[0] == {0, 1}
        assert by_size[1] == {2}

    def test_empty_vertices(self):
        parts = partition_by_labels(set(), {})
        assert parts == []

    def test_all_unique_labels(self):
        labels = {0: {"A"}, 1: {"B"}, 2: {"C"}}
        parts = partition_by_labels({0, 1, 2}, labels)
        assert len(parts) == 3

    def test_empty_label_sets(self):
        labels = {0: set(), 1: set()}
        parts = partition_by_labels({0, 1}, labels)
        assert len(parts) == 1
        assert parts[0] == {0, 1}

    def test_missing_vertex_defaults_to_empty_labels(self):
        labels = {0: {"A"}}
        parts = partition_by_labels({0, 1}, labels)
        assert len(parts) == 2


class TestContractSccs:
    """Tests for the contract_sccs utility."""

    def test_dag_no_sccs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        sccs, scc_map = contract_sccs(g)
        assert len(sccs) == 3
        assert scc_map[0] != scc_map[1] != scc_map[2]

    def test_single_scc(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        sccs, scc_map = contract_sccs(g)
        assert len(sccs) == 1
        assert sccs[0] == {0, 1, 2}
        assert scc_map[0] == scc_map[1] == scc_map[2]

    def test_mixed_sccs_and_dag(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)  # SCC {0,1,2}
        g.add_edge(2, 3)
        g.add_edge(3, 4)
        sccs, scc_map = contract_sccs(g)
        assert len(sccs) == 3
        # Vertices 0,1,2 share an SCC
        assert scc_map[0] == scc_map[1] == scc_map[2]
        # Vertices 3 and 4 are singletons
        assert scc_map[3] != scc_map[4]
        assert scc_map[3] != scc_map[0]

    def test_empty_graph(self):
        g = Digraph()
        sccs, scc_map = contract_sccs(g)
        assert sccs == []
        assert scc_map == {}

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        sccs, scc_map = contract_sccs(g)
        assert len(sccs) == 1
        assert scc_map[0] == 0

    def test_disconnected_sccs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 0)
        g.add_edge(2, 3)
        g.add_edge(3, 2)
        sccs, scc_map = contract_sccs(g)
        assert len(sccs) == 2
        assert scc_map[0] == scc_map[1]
        assert scc_map[2] == scc_map[3]
        assert scc_map[0] != scc_map[2]
