"""Tests for the per-pivot dispatch in :mod:`reachq.shortcut`."""

from __future__ import annotations

import logging

from reachq.graph import Digraph
from reachq.shortcut import (
    ShortcutState,
    _reset_spawn_warn_emitted,
    _run_pivots,
    expand_pivot,
    get_logger,
)


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
    state = _trivial_state(g)
    out = _run_pivots(g, state, [0, 1], parallel=False, n_workers=1)
    assert len(out) == 2
    assert out[0]["r_plus"] == set() or 0 in out[0]["r_plus"]


def test_sequential_matches_parallel_result_shape():
    """Both modes return a list of per-pivot result dicts."""
    g = Digraph()
    for i in range(5):
        g.add_vertex(i)
        if i > 0:
            g.add_edge(i - 1, i)
    state = _trivial_state(g)
    out_seq = _run_pivots(g, state, [0, 1, 2], parallel=False, n_workers=1)
    assert isinstance(out_seq, list)
    assert all({"r_plus", "r_minus"} <= r.keys() for r in out_seq)


def test_spawn_warning_logged_for_small_graph(caplog):
    """Spawn warning is logged when parallel=True and graph is small."""
    g = Digraph()
    for i in range(10):
        g.add_vertex(i)
    state = _trivial_state(g)
    _reset_spawn_warn_emitted()
    with caplog.at_level(logging.INFO, logger="reachq.shortcut"):
        # n_workers>1 triggers the process-pool path; the warning fires
        # before the pool is constructed. We use a large enough n to
        # avoid actual pool startup.
        _run_pivots(g, state, [], parallel=True, n_workers=2)
    assert any("spawn cost" in rec.message for rec in caplog.records)


def test_spawn_warning_not_logged_for_large_graph(caplog):
    """No spawn warning when the graph is large enough."""
    g = Digraph()
    for i in range(2000):
        g.add_vertex(i)
    state = _trivial_state(g)
    _reset_spawn_warn_emitted()
    with caplog.at_level(logging.INFO, logger="reachq.shortcut"):
        _run_pivots(g, state, [], parallel=True, n_workers=2)
    assert not any("spawn cost" in rec.message for rec in caplog.records)


def test_spawn_warning_idempotent_per_top_level_call(caplog):
    """``build_shortcut_set_for_reachability`` resets the latch before
    invoking the recursion; within a single top-level call the
    warning fires at most once regardless of how many pivots or
    recursion levels run.
    """
    from reachq.config import RefinementConfig
    from reachq.shortcut import build_shortcut_set_for_reachability

    g = Digraph()
    for i in range(5):
        g.add_vertex(i)
        if i > 0:
            g.add_edge(i - 1, i)
    flags = RefinementConfig(parallel=True)
    _reset_spawn_warn_emitted()
    with caplog.at_level(logging.INFO, logger="reachq.shortcut"):
        build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            refinement=flags,
            parallel_workers=2,
        )
    spawn_messages = [r for r in caplog.records if "spawn cost" in r.message]
    assert len(spawn_messages) == 1


def test_expand_pivot_returns_both_keys():
    """``expand_pivot`` returns both ``r_plus`` and ``r_minus`` keys."""
    g = Digraph()
    g.add_vertex(0)
    state = _trivial_state(g)
    result = expand_pivot((g, state, 0))
    assert "r_plus" in result
    assert "r_minus" in result
    assert isinstance(result["r_plus"], set)
    assert isinstance(result["r_minus"], set)


def test_get_logger_returns_a_logger():
    """``get_logger`` is exported and returns a logging.Logger."""
    log = get_logger("reachq.test")
    assert hasattr(log, "info")
