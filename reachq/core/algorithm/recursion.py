"""JLS recursion body.

The recursion drives pivot sampling, BFS expansion (sequential or
process), label construction, partitioning, and adaptive scaling.
State is constructed once by the wrapper (:mod:`wrap`) and passed
through every recursive call. No module-level globals.
"""

from __future__ import annotations

import math
import random
from typing import Any

from reachq.core.algorithm.adaptive import compute_adaptive_scale
from reachq.core.algorithm.partition import build_labels, partition_vertices
from reachq.core.algorithm.parallel import ParallelExecutor
from reachq.core.algorithm.pivots import sample_pivots
from reachq.core.algorithm.state import AlgorithmState
from reachq.core.config import RefinementConfig
from reachq.core.graph import Digraph
from reachq.core.prune import apply_tc_pruning, compute_tc_pruning_threshold


def _base_prob(k: float, level: int, n_global: int, sampling_constant: float) -> float:
    """Compute the per-level pivot probability."""
    log_n = math.log2(n_global) if n_global > 1 else 0.0
    return min(
        1.0, sampling_constant * (k ** (level + 1)) * log_n / n_global
    )


def jls_recursive(
    graph: Digraph,
    state: AlgorithmState,
    k: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int,
    rng: random.Random,
    flags: RefinementConfig,
    sampling_constant: float,
    *,
    executor: ParallelExecutor,
    tc_threshold: float | None = None,
) -> set[tuple[object, object]]:
    """JLS recursion body.

    Args:
        graph: Current (possibly induced) subgraph.
        state: Picklable CSR payload. ``state.n`` matches the
            subgraph's vertex count.
        k: Recursion widening factor (>1).
        rho: Hop-parameter.
        max_level: Maximum recursion depth.
        n_global: Original graph size (for k^(level) probability).
        level: Current recursion depth.
        rng: Random source.
        flags: Refinement toggles.
        sampling_constant: Multiplier on the pivot probability.
        executor: Per-call executor.
        tc_threshold: Pre-computed TC-pruning threshold (``None`` to
            compute or disable per flags).

    Returns:
        Set of shortcut edges for this level.
    """
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return set()

    base_prob = _base_prob(k, level, n_global, sampling_constant)

    vertices = list(graph.vertices())

    if flags.degree_ordered_pivots:
        out_degrees = {v: graph.degree_out(v) for v in vertices}
    else:
        out_degrees = {}

    pivots = sample_pivots(
        vertices, base_prob, rng,
        degree_aware=flags.degree_ordered_pivots,
        out_degrees=out_degrees,
    )

    pivots.sort(key=lambda v: graph.index_of(v))

    if not pivots:
        return set()

    shortcuts: set[tuple[object, object]] = set()

    pivot_results = executor.imap(pivot_worker_unwrap, graph, state, pivots)

    r_minus_per_pivot: dict[object, set[object]] = {}
    r_plus_per_pivot: dict[object, set[object]] = {}

    for pivot, result in zip(pivots, pivot_results):
        r_minus: set[object] = result.get("r_minus", set())
        r_plus: set[object] = result.get("r_plus", set())
        r_minus_per_pivot[pivot] = r_minus
        r_plus_per_pivot[pivot] = r_plus
        for v in r_minus:
            shortcuts.add((v, pivot))
        for v in r_plus:
            shortcuts.add((pivot, v))

        if flags.enable_tc_pruning and tc_threshold is not None:
            r_ball = (r_minus | r_plus | {pivot})
            shortcuts |= apply_tc_pruning(graph, r_ball, tc_threshold)

    labels = build_labels(vertices, pivots, r_plus_per_pivot, r_minus_per_pivot)
    parts = partition_vertices(vertices, labels)

    if len(parts) <= 1 and flags.skip_trivial_part:
        return shortcuts

    next_sampling = sampling_constant
    if flags.adaptive_sampling:
        scale = compute_adaptive_scale(parts, n_global, level, k)
        next_sampling = sampling_constant * scale

    for part in parts:
        if len(part) <= 1:
            continue
        sub = graph.induced_subgraph(part)
        sub_state = state
        sub_seed = (
            rng.randint(0, 2**31 - 1) if True else None
        )
        sub_rng = random.Random(sub_seed) if sub_seed is not None else rng
        sub_shortcuts = jls_recursive(
            sub,
            sub_state,
            k,
            rho,
            max_level,
            n_global,
            level + 1,
            sub_rng,
            flags,
            next_sampling,
            executor=executor,
            tc_threshold=tc_threshold,
        )
        shortcuts |= sub_shortcuts

    return shortcuts


def pivot_worker_unwrap(args: tuple[Any, Any, Any]) -> dict[str, Any]:
    """Adapter: unwrap ``(graph, state, pivot)`` and dispatch."""
    from reachq.core.algorithm.parallel import pivot_worker

    return pivot_worker(args)
