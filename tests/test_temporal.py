"""Tests for temporal graph reachability."""

from __future__ import annotations

from reachq.research.temporal import (
    TemporalDigraph,
    earliest_arrival,
    from_temporal_edges,
    temporal_bfs,
)


def test_empty_temporal_graph():
    """An empty temporal graph has no reachable vertices."""
    tg = TemporalDigraph()
    assert tg.num_vertices == 0
    assert temporal_bfs(tg, 0) == set()


def test_single_temporal_edge():
    """A single temporal edge (a, b, 5) makes b reachable from a at t=0."""
    tg = TemporalDigraph()
    tg.add_edge("a", "b", 5)
    # Default start_time=0 allows the edge.
    assert temporal_bfs(tg, "a") == {"a", "b"}


def test_temporal_bfs_respects_start_time():
    """An edge with timestamp < start_time is not traversed."""
    tg = TemporalDigraph()
    tg.add_edge("a", "b", 5)
    # start_time=10 blocks the edge (timestamp 5 < 10).
    assert temporal_bfs(tg, "a", start_time=10) == {"a"}


def test_temporal_bfs_respects_max_time():
    """An edge with timestamp > max_time is not traversed."""
    tg = TemporalDigraph()
    tg.add_edge("a", "b", 5)
    # max_time=3 blocks the edge (timestamp 5 > 3).
    assert temporal_bfs(tg, "a", max_time=3) == {"a"}


def test_temporal_chain_with_monotonic_timestamps():
    """A chain 0->1@1, 1->2@3 is a valid temporal walk from 0 to 2."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 1)
    tg.add_edge(1, 2, 3)
    assert temporal_bfs(tg, 0) == {0, 1, 2}


def test_temporal_chain_violates_monotonicity():
    """A chain 0->1@5, 1->2@3 cannot reach 2 from 0 (timestamps must be non-decreasing)."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 5)
    tg.add_edge(1, 2, 3)
    assert temporal_bfs(tg, 0) == {0, 1}  # can't reach 2


def test_earliest_arrival():
    """earliest_arrival returns the minimum arrival timestamp."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 1)
    tg.add_edge(0, 1, 5)  # duplicate edge, later timestamp
    tg.add_edge(1, 2, 3)
    # Earliest arrival at 2 is via 0->1@1, 1->2@3 = 3.
    assert earliest_arrival(tg, 0, 2) == 3


def test_earliest_arrival_unreachable():
    """earliest_arrival returns None if target is unreachable."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 1)
    assert earliest_arrival(tg, 0, 5) is None


def test_earliest_arrival_same_source_target():
    """earliest_arrival(source, source) = 0."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 1)
    assert earliest_arrival(tg, 0, 0) == 0


def test_earliest_arrival_invalid_vertex():
    """earliest_arrival with unknown vertex returns None."""
    tg = TemporalDigraph()
    tg.add_edge(0, 1, 1)
    assert earliest_arrival(tg, 99, 1) is None
    assert earliest_arrival(tg, 0, 99) is None


def test_from_temporal_edges_helper():
    """from_temporal_edges builds a TemporalDigraph from a flat list."""
    tg = from_temporal_edges([(0, 1, 1), (1, 2, 2), (2, 3, 3)])
    assert tg.num_vertices == 4
    assert tg.num_edges == 3
    assert temporal_bfs(tg, 0) == {0, 1, 2, 3}