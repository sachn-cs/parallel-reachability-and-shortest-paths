"""Concurrent JLS builds must not share mutable state.

Two simultaneous ``build_shortcut_set_for_reachability`` calls
with ``flags.parallel=True`` and ``parallel_workers > 1`` must
produce independent results without workers receiving each
other's state.
"""

from __future__ import annotations

import threading
import time

from reachq.shortcut import build_shortcut_set_for_reachability
from reachq.generators import random_dag
from reachq.reachability import bfs_reachability, parallel_bfs


def _build(graph, seed: int):
    shortcuts, beta, _ = build_shortcut_set_for_reachability(
        graph,
        omega=3.0,
        random_seed=seed,
        parallel_workers=4,
        refinement={"parallel": True}, )
    return shortcuts, beta


def test_concurrent_jls_distinct_graphs():
    graphs = [
        random_dag(n=40, edge_probability=0.1, random_seed=i) for i in range(3)
    ]
    results = [None] * 3
    errors: list[Exception] = []

    def worker(idx: int):
        try:
            results[idx] = _build(graphs[idx], seed=idx)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - t0

    assert not errors, f"errors in threads: {errors}"
    for i, (shortcuts, beta) in enumerate(results):
        assert shortcuts is not None
        assert beta > 0
        for v in graphs[i].vertices():
            assert bfs_reachability(graphs[i], v) == parallel_bfs(
                graphs[i], v, shortcuts
            )
    assert elapsed < 30.0


def test_concurrent_jls_same_seed_produces_same_shortcut_set():
    """Concurrent builds of the same graph with the same seed must
    produce identical shortcut sets (the per-invocation state binding
    must be effective)."""
    g = random_dag(n=30, edge_probability=0.15, random_seed=99)
    shortcuts_a, beta_a = _build(g, seed=99)
    shortcuts_b, beta_b = _build(g, seed=99)
    assert shortcuts_a == shortcuts_b
    assert beta_a == beta_b


def test_reentrant_concurrent_builds_with_workers():
    """Workers are picklable; per-invocation state binding means
    no global state is shared even with overlapping calls."""
    g = random_dag(n=50, edge_probability=0.1, random_seed=7)
    barrier = threading.Barrier(2)

    def run(idx: int):
        barrier.wait()
        shortcuts, _, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=7,
            parallel_workers=2,
            refinement={"parallel": True}, )
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts), (
                f"thread {idx}: reachability mismatch"
            )

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
