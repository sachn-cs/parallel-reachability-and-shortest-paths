"""Edge-case tests for the parallel reachability algorithm.

Each test exercises a single edge case: empty graph, single vertex,
disconnected components, no shortcuts, only shortcuts, no original
edges, etc. The tests verify that parallel_bfs agrees with the
unaccelerated bfs_reachability.
"""

from __future__ import annotations

from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs


def test_empty_graph():
    g = Digraph()
    import pytest

    with pytest.raises(KeyError):
        parallel_bfs(g, 0, set())
    with pytest.raises(KeyError):
        parallel_bfs(g, 0, {(0, 1)})


def test_single_vertex_no_shortcuts():
    g = Digraph()
    g.add_vertex("alone")
    assert parallel_bfs(g, "alone", set()) == {"alone"}


def test_single_vertex_with_self_loop_attempt():
    """A self-loop is rejected at edge-add time; the vertex still has
    itself reachable via parallel_bfs."""
    g = Digraph()
    g.add_vertex("v")
    assert parallel_bfs(g, "v", set()) == {"v"}


def test_two_disconnected_vertices():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    assert parallel_bfs(g, 0, set()) == {0}
    assert parallel_bfs(g, 1, set()) == {1}


def test_two_connected_vertices():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1)
    # Directed reachability: from 0 we can reach 1, but not vice versa.
    assert parallel_bfs(g, 0, set()) == {0, 1}
    assert parallel_bfs(g, 1, set()) == {1}


def test_two_connected_vertices_with_back_edge():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_edge(0, 1)
    g.add_edge(1, 0)
    # Now both directions exist; mutual reachability.
    assert parallel_bfs(g, 0, set()) == {0, 1}
    assert parallel_bfs(g, 1, set()) == {0, 1}


def test_only_shortcuts_no_edges():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(2)
    shortcuts = {(0, 1), (1, 2), (0, 2)}
    # Directed: shortcuts flow forward from each source.
    assert parallel_bfs(g, 0, shortcuts) == {0, 1, 2}
    assert parallel_bfs(g, 2, shortcuts) == {2}


def test_shortcut_to_nonexistent_target():
    g = Digraph()
    g.add_vertex(0)
    shortcuts = {(0, 99)}
    assert parallel_bfs(g, 0, shortcuts) == {0}


def test_shortcut_replacing_long_path():
    g = Digraph()
    n = 20
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    shortcuts = {(0, n - 1)}
    assert parallel_bfs(g, 0, shortcuts) == set(range(n))


def test_parallel_bfs_does_not_follow_unrelated_shortcuts():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    g.add_vertex(99)
    shortcuts = {(0, 99)}  # shortcut to an unrelated vertex
    assert parallel_bfs(g, 0, shortcuts) == {0, 99}


def test_three_component_chain():
    g = Digraph()
    g.add_vertex("a")
    g.add_vertex("b")
    g.add_vertex("c")
    shortcuts = {("a", "b"), ("b", "c"), ("a", "c")}
    assert parallel_bfs(g, "a", shortcuts) == {"a", "b", "c"}


def test_parallel_bfs_matches_bfs_on_random_dag():
    """Sanity: parallel_bfs and bfs_reachability should agree on a
    random DAG with random shortcuts."""
    from reachq.core.generators import random_dag

    g = random_dag(n=20, edge_probability=0.3, random_seed=42)
    shortcuts = {(0, 5), (5, 10), (10, 15), (0, 19)}
    for s in g.vertices():
        assert parallel_bfs(g, s, shortcuts) == bfs_reachability(g, s)
