"""Tests for attributed graph reachability."""

from __future__ import annotations

from reachq.core.generators import path_graph
from reachq.research.attributed import (
    attributed_bfs,
    attributed_reachable_pairs,
    vertex_attribute_index,
)


def test_attributed_bfs_no_predicates():
    """With no predicates, behaves like ordinary BFS."""
    g = path_graph(5)
    reachable = attributed_bfs(g, 0)
    assert reachable == {0, 1, 2, 3, 4}


def test_attributed_bfs_vertex_predicate():
    """A vertex predicate can block specific vertices."""
    g = path_graph(5)
    # Block odd-indexed vertices, but we can still reach 0 from itself.
    # From 0, the only outgoing edge is to 1 (blocked), so we don't
    # reach any further vertices.
    reachable = attributed_bfs(g, 0, vertex_pred=lambda v: v % 2 == 0)
    assert reachable == {0}


def test_attributed_bfs_vertex_predicate_reachable():
    """A vertex predicate that allows traversal."""
    g = path_graph(5)
    # Block vertex 1, but allow everything else. From 0 we can't pass
    # through 1, so 0 can only reach itself.
    reachable = attributed_bfs(g, 0, vertex_pred=lambda v: v != 1)
    assert reachable == {0}
    # From 2, we can reach 3 and 4 (skipping the blocked vertex 1).
    reachable2 = attributed_bfs(g, 2, vertex_pred=lambda v: v != 1)
    assert reachable2 == {2, 3, 4}


def test_attributed_bfs_edge_predicate():
    """An edge predicate can block specific edges."""
    g = path_graph(5)
    # Block the edge (2, 3) but allow all others.
    reachable = attributed_bfs(g, 0, edge_pred=lambda u, v: not (u == 2 and v == 3))
    assert 3 not in reachable
    assert 4 not in reachable
    assert 0 in reachable
    assert 1 in reachable
    assert 2 in reachable


def test_attributed_bfs_combined():
    """Both predicates are applied."""
    g = path_graph(5)
    reachable = attributed_bfs(
        g,
        0,
        vertex_pred=lambda v: v < 4,
        edge_pred=lambda u, v: v - u == 1,
    )
    assert reachable == {0, 1, 2, 3}


def test_attributed_bfs_source_not_in_graph():
    """Source not in graph raises KeyError."""
    g = path_graph(3)
    try:
        attributed_bfs(g, 99)
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_attributed_bfs_vertex_pred_excludes_source():
    """If the vertex predicate rejects the source, result is empty."""
    g = path_graph(5)
    reachable = attributed_bfs(g, 0, vertex_pred=lambda v: v > 0)
    assert reachable == set()


def test_attributed_reachable_pairs():
    """attributed_reachable_pairs returns the (s, t) cross-product within reach."""
    g = path_graph(5)
    pairs = attributed_reachable_pairs(g, sources={0, 4}, targets={2, 3, 4})
    # From 0: reaches 2, 3, 4 -> (0, 2), (0, 3), (0, 4)
    # From 4: reaches nothing among the targets (4 reaches 4 if reflexive)
    # Note: BFS does not include the source's reachability-to-itself
    # unless explicit. Since 4 has no outgoing edges, only (4, 4) if
    # we include reflexive closure -- we don't, so just (0, 2..4).
    assert (0, 2) in pairs
    assert (0, 3) in pairs
    assert (0, 4) in pairs
    # 4 reaches only itself; we don't include (source, source).
    assert (4, 2) not in pairs


def test_vertex_attribute_index():
    """vertex_attribute_index partitions vertices by attribute value."""
    g = path_graph(5)
    idx = vertex_attribute_index(g, lambda v: v % 2)
    assert idx[0] == [0, 2, 4]
    assert idx[1] == [1, 3]
