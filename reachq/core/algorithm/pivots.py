"""Pivot sampling and per-pivot BFS expansion.

Sampling supports two modes:

* uniform Bernoulli on ``vertices`` with probability ``base_prob``.
* degree-aware: per-vertex probability scaled by
  ``1 / (1 + out_degree)`` and renormalised so the expected
  count of pivots matches ``base_prob * |vertices|``.

The BFS expansion dispatches to CSR numpy kernels when the
payload includes precomputed arrays; otherwise it falls back to
deque BFS over the graph passed alongside the state. Workers are
configured to always take ``(graph, state, pivot)`` so the
serialization cost is uniform.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Any

from reachq.core.algorithm.state import AlgorithmState
from reachq.core.bfs import csr_reachable_backward, csr_reachable_forward
from reachq.core.graph import Digraph
from reachq.core.reachability import (
    bfs_reachability,
    reverse_bfs_reachability,
)


def sample_pivots(
    vertices,
    base_prob: float,
    rng: random.Random,
    *,
    degree_aware: bool,
    out_degrees: dict[object, int] | None = None,
) -> list[object]:
    """Return the list of pivots selected for this level."""
    if not degree_aware or base_prob >= 1.0:
        return [v for v in vertices if rng.random() < base_prob]

    if out_degrees is None:
        out_degrees = {}

    raw: list[tuple[object, float]] = []
    weights: list[float] = []
    for v in vertices:
        w = base_prob / (1 + out_degrees.get(v, 0))
        raw.append((v, w))
        weights.append(w)

    total = sum(weights)
    if total <= 0:
        return []
    scale = base_prob * len(raw) / total
    return [v for v, w in raw if rng.random() < w * scale]


def _vertex_index(state: AlgorithmState, pivot: object) -> int | None:
    for i, v in enumerate(state.idx_to_vertex):
        if v == pivot:
            return i
    return None


def _pivot_worker_body(
    graph: Digraph,
    state: AlgorithmState,
    pivot: object,
) -> dict[str, Any]:
    """Expand one pivot via CSR (if available) or deque BFS."""
    if state.indptr_fwd is not None:
        p_idx = _vertex_index(state, pivot)
        if p_idx is None:
            return {"r_plus": set(), "r_minus": set()}
        r_plus_arr = csr_reachable_forward(
            state.indptr_fwd,
            state.indices_fwd,
            p_idx,
            state.n,
            max_depth=state.max_hops,
        )
        r_minus_arr = csr_reachable_backward(
            state.indptr_rev,
            state.indices_rev,
            p_idx,
            state.n,
            max_depth=state.max_hops,
        )
        r_plus = {state.idx_to_vertex[int(i)] for i in r_plus_arr}
        r_minus = {state.idx_to_vertex[int(i)] for i in r_minus_arr}
    else:
        if state.max_hops is not None:
            r_plus = bfs_hop_limited_deque(graph, pivot, state.max_hops, forward=True)
            r_minus = bfs_hop_limited_deque(
                graph, pivot, state.max_hops, forward=False
            )
        else:
            r_plus = bfs_reachability(graph, pivot)
            r_minus = reverse_bfs_reachability(graph, pivot)
    r_plus.discard(pivot)
    r_minus.discard(pivot)
    return {"r_plus": r_plus, "r_minus": r_minus}


def bfs_hop_limited_deque(
    graph: Digraph,
    source: object,
    max_hops: int,
    *,
    forward: bool,
) -> set[object]:
    """Hop-bounded BFS using a deque."""
    visited: set[object] = {source}
    q: deque[tuple[object, int]] = deque([(source, 0)])
    g = graph if forward else graph.reversed()
    while q:
        u, d = q.popleft()
        if d >= max_hops:
            continue
        for v in g.out_edges.get(u, ()):
            if v not in visited:
                visited.add(v)
                q.append((v, d + 1))
    visited.discard(source)
    return visited
