"""Tests for the per-call ParallelExecutor dispatcher."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest

from reachq.graph import Digraph
from reachq.shortcut import ShortcutState
from reachq.shortcut_parallel import ParallelExecutor, expand_pivot


def _trivial_state(graph: Digraph) -> ShortcutState:
    return ShortcutState(
        csr_indptr=None,
        csr_indices=None,
        csr_rev_indptr=None,
        csr_rev_indices=None,
        idx_to_vertex=graph.vertices(),
        n=graph.num_vertices(),
        max_hops=None,
    )


def test_run_sequential_works():
    """Sequential mode dispatches per-item through func."""
    g = Digraph()
    g.add_vertex(0)
    g.add_vertex(1)
    executor = ParallelExecutor(mode="sequential", n_workers=1)
    state = _trivial_state(g)
    out = executor.run(expand_pivot, g, state, [0, 1])
    assert len(out) == 2
    assert out[0]["r_plus"] == set() or 0 in out[0]["r_plus"]


def test_run_process_emits_spawn_warning_for_small_graph(caplog):
    """Spawn warning is logged when n_workers>1 and graph is small."""
    g = Digraph()
    for i in range(10):
        g.add_vertex(i)
    executor = ParallelExecutor(mode="processes", n_workers=2)
    state = _trivial_state(g)
    with caplog.at_level(logging.INFO, logger="reachq.core.shortcut_parallel"):
        # We don't actually start the pool; just trigger the warning
        # path by calling _warn_if_small_graph directly.
        executor._warn_if_small_graph(g)
    assert any("spawn cost" in rec.message for rec in caplog.records)


def test_run_process_no_warning_for_large_graph(caplog):
    """No spawn warning when the graph is large enough."""
    g = Digraph()
    for i in range(2000):
        g.add_vertex(i)
    executor = ParallelExecutor(mode="processes", n_workers=2)
    with caplog.at_level(logging.INFO, logger="reachq.core.shortcut_parallel"):
        executor._warn_if_small_graph(g)
    assert not any("spawn cost" in rec.message for rec in caplog.records)


def test_spawn_warning_idempotent(caplog):
    """Spawn warning is fired at most once per executor."""
    g = Digraph()
    for _ in range(5):
        g.add_vertex(_)
    executor = ParallelExecutor(mode="processes", n_workers=2)
    with caplog.at_level(logging.INFO, logger="reachq.core.shortcut_parallel"):
        executor._warn_if_small_graph(g)
        executor._warn_if_small_graph(g)
    spawn_messages = [r for r in caplog.records if "spawn cost" in r.message]
    assert len(spawn_messages) == 1
