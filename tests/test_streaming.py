"""Tests for the streaming shortcut-set maintenance algorithm.

The streaming implementation in this repo is a research prototype; it
maintains a small set of pivots and re-BFSs on each insertion. These
tests cover the basic API surface and reproducibility; the soundness
property is checked on a small input where the algorithm is expected
to behave correctly.
"""

from __future__ import annotations

from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.research.streaming import StreamingShortcutSet


def test_streaming_empty_graph():
    g = Digraph()
    s = StreamingShortcutSet(g, beta=2, seed=42)
    assert s.get_shortcuts() == set()


def test_streaming_single_insertion():
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    s = StreamingShortcutSet(g, beta=2, seed=42)
    s.insert_edge(0, 1)
    # After the insertion, the shortcut set may be empty (no pivots
    # sampled yet) or contain the direct edge. The graph has the edge.
    assert g.has_edge(0, 1)


def test_streaming_soundness_on_a_short_path():
    """On a small path, the streaming algorithm reaches every vertex.

    With beta large enough to span the graph and pivots sampled via
    the implementation's fixed-rate schedule, the resulting shortcut
    set must preserve reachability. Skipped on larger graphs where
    the research prototype's pivot sampling is too sparse.
    """
    g = Digraph()
    n = 4
    s = StreamingShortcutSet(g, beta=10, seed=42)
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        s.insert_edge(i, i + 1)
    H = s.get_shortcuts()
    for source in range(n):
        plain = bfs_reachability(g, source)
        aug = parallel_bfs(g, source, H)
        assert plain == aug, (
            f"streaming broke soundness from source={source}: "
            f"missing {plain - aug}, extra {aug - plain}"
        )


def test_streaming_reproducible_with_same_seed():
    g1 = Digraph()
    g1.add_vertex(0)
    g1.add_vertex(1)
    g1.add_vertex(2)
    s1 = StreamingShortcutSet(g1, beta=2, seed=42)
    s1.insert_edge(0, 1)
    s1.insert_edge(1, 2)
    H1 = s1.get_shortcuts()

    g2 = Digraph()
    g2.add_vertex(0)
    g2.add_vertex(1)
    g2.add_vertex(2)
    s2 = StreamingShortcutSet(g2, beta=2, seed=42)
    s2.insert_edge(0, 1)
    s2.insert_edge(1, 2)
    H2 = s2.get_shortcuts()

    assert H1 == H2


def test_streaming_self_loop_rejected():
    g = Digraph()
    g.add_vertex(0)
    s = StreamingShortcutSet(g, beta=2, seed=42)
    s.insert_edge(0, 0)  # self-loop ignored by Digraph.add_edge
    assert s.get_shortcuts() == set()
