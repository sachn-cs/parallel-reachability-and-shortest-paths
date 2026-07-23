"""Tests for reachability algorithms."""

import pytest

from reachq.graph import Digraph
from reachq.reachability import (
    bfs_reachability,
    compute_ancestors,
    compute_bridges,
    compute_descendants,
    compute_r_ball,
    parallel_bfs,
    reverse_bfs_reachability,
    strongly_connected_components,
    topological_sort,
)


class TestBfsReachability:
    """Tests for BFS-based reachability."""

    def test_simple_path(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        assert bfs_reachability(g, 0) == {0, 1, 2, 3}
        assert bfs_reachability(g, 1) == {1, 2, 3}
        assert bfs_reachability(g, 3) == {3}

    def test_disconnected(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        assert bfs_reachability(g, 0) == {0, 1}
        assert bfs_reachability(g, 2) == {2, 3}

    def test_cycle(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        assert bfs_reachability(g, 0) == {0, 1, 2}

    def test_self_loop(self):
        g = Digraph()
        g.add_edge(0, 0)
        g.add_edge(0, 1)
        assert bfs_reachability(g, 0) == {0, 1}

    def test_empty_graph(self):
        g = Digraph()
        assert bfs_reachability(g, 0) == {0}

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        assert bfs_reachability(g, 0) == {0}

    def test_reverse_bfs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        assert reverse_bfs_reachability(g, 3) == {0, 1, 2, 3}
        assert reverse_bfs_reachability(g, 1) == {0, 1}

    def test_r_ball(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        assert compute_r_ball(g, 0) == {0, 1, 2}

    def test_ancestors_descendants_bridges(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(0, 3)
        path = [0, 1, 2, 3]
        bri = compute_bridges(g, path)
        assert bri == {0, 1, 2, 3}
        anc = compute_ancestors(g, path)
        des = compute_descendants(g, path)
        assert anc == set()
        assert des == set()

    def test_parallel_bfs_with_shortcuts(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        shortcuts = {(0, 3)}
        reached = parallel_bfs(g, 0, shortcuts)
        assert reached == {0, 1, 2, 3}

    def test_parallel_bfs_no_shortcuts(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        reached = parallel_bfs(g, 0)
        assert reached == {0, 1, 2}


class TestTopologicalSort:
    """Tests for topological sort."""

    def test_dag(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(0, 2)
        order = topological_sort(g)
        assert order.index(0) < order.index(1)
        assert order.index(1) < order.index(2)
        assert order.index(0) < order.index(2)

    def test_cycle_raises(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        with pytest.raises(ValueError):
            topological_sort(g)

    def test_empty(self):
        g = Digraph()
        assert topological_sort(g) == []

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        assert topological_sort(g) == [0]


class TestStronglyConnectedComponents:
    """Tests for SCC computation."""

    def test_single_scc(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 1
        assert sccs[0] == {0, 1, 2}

    def test_dag_has_singleton_sccs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 3
        assert all(len(scc) == 1 for scc in sccs)

    def test_two_sccs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 0)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 2)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 2
        scc_sets = [set(scc) for scc in sccs]
        assert {0, 1} in scc_sets
        assert {2, 3} in scc_sets

    def test_empty_graph(self):
        g = Digraph()
        sccs = strongly_connected_components(g)
        assert sccs == []

    def test_single_vertex(self):
        g = Digraph()
        g.add_vertex(0)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 1
        assert sccs[0] == {0}

    def test_self_loop(self):
        g = Digraph()
        g.add_edge(0, 0)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 1
        assert sccs[0] == {0}

    def test_disconnected_sccs(self):
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 0)
        g.add_edge(2, 3)
        g.add_edge(3, 2)
        sccs = strongly_connected_components(g)
        assert len(sccs) == 2
        scc_sets = [set(scc) for scc in sccs]
        assert {0, 1} in scc_sets
        assert {2, 3} in scc_sets


class TestDeterminism:
    """Tests that algorithms produce deterministic output for deterministic input."""

    def test_bfs_deterministic(self):
        g = Digraph()
        for i in range(50):
            g.add_edge(i, i + 1)
        r1 = bfs_reachability(g, 0)
        r2 = bfs_reachability(g, 0)
        assert r1 == r2

    def test_scc_deterministic(self):
        g = Digraph()
        for i in range(20):
            g.add_edge(i, (i + 1) % 20)
        s1 = strongly_connected_components(g)
        s2 = strongly_connected_components(g)
        assert len(s1) == len(s2)
        for a, b in zip(s1, s2):
            assert a == b
