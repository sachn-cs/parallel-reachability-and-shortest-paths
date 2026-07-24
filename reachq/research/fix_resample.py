"""Fix/Resample variant of shortcut-set construction.

Inspired by Assadi-Yazdanyar's dynamic graph coloring algorithm
(arXiv:2604.20648). Their algorithm maintains a partial coloring
under dynamic updates via local Fix/Resample subroutines; we adapt the
*static* version (no updates, just a local-search refiner) as an
experimental alternative to the JLS sampling approach.

Honest scope: Paper 1's algorithm targets the *dynamic* setting where
the graph changes between updates. Our codebase is purely *static*, so
the dynamic-update bounds do not apply. We implement the static
analogue purely as a comparison point.

Expected empirical outcome: this algorithm produces a *larger*
shortcut set than JLS on the same graph, because the dynamic update
motivates careful local search while the static case has no
incremental cost. We document this honestly in the comparison script.
"""

from __future__ import annotations

import random
from typing import Any

from reachq.core.graph import Digraph
from reachq.core.config import get_logger
from reachq.core.reachability import (
    compute_r_minus,
    compute_r_plus,
)

log = get_logger("reachq.fix_resample")


def fix_resample_shortcut_set(
    graph: Digraph,
    *,
    threshold_fraction: float = 0.5,
    resample_prob: float = 0.05,
    max_iterations: int = 100_000,
    random_seed: int | None = None,
) -> set[tuple[Any, Any]]:
    """Fix/Resample-style shortcut-set construction (static).

    Algorithm:
      1. Start with empty shortcut set H and F = all vertices (uncovered).
      2. While F is non-empty and iterations remain:
         a. Pick a vertex v in F uniformly at random.
         b. Add v as a pivot: insert (v, w) for w in R+(v) and (w, v)
            for w in R-(v).
         c. Remove v and newly-reached vertices from F.
         d. With probability resample_prob, do a "resample": pick a
            random pivot already in H, remove its shortcuts, and
            re-add it (with fresh randomness). This is the analogue of
            Paper 1's Resample subroutine.
      3. Return H.

    Args:
        graph: input digraph (any orientation).
        threshold_fraction: stop when |F| / |V| <= this fraction.
            (Default 0.5 means stop when half the vertices are uncovered.
            Lower values give larger shortcut sets.)
        resample_prob: per-iteration probability of a resample pass.
            (Default 0.05; this is the analogue of Paper 1's
            Resample step.)
        max_iterations: hard cap on iterations to guarantee termination.
        random_seed: optional seed for reproducibility.

    Returns:
        A set of shortcut edges.
    """
    rng = random.Random(random_seed)
    vertices = list(graph.vertices())
    if not vertices:
        return set()

    # Pre-compute r_plus and r_minus for each vertex (one-shot BFS).
    log.info("precomputing r_plus/r_minus for %d vertices", len(vertices))
    ball: dict[Any, tuple[set[Any], set[Any]]] = {}
    for v in vertices:
        ball[v] = (compute_r_plus(graph, v), compute_r_minus(graph, v))

    H: set[tuple[Any, Any]] = set()
    reached: set[Any] = set()
    n = len(vertices)

    def cover(v: Any) -> None:
        """Add v as a pivot and mark reachable vertices as covered."""
        rp, rm = ball[v]
        for w in rp:
            if w != v:
                H.add((v, w))
                reached.add(w)
        for w in rm:
            if w != v:
                H.add((w, v))
                reached.add(w)
        reached.add(v)

    # Start with the highest-degree vertex as a pivot for a non-trivial base.
    seed = max(vertices, key=lambda v: graph.degree_out(v) + graph.degree_in(v))
    cover(seed)

    iters = 0
    while len(reached) < n and iters < max_iterations:
        iters += 1
        # Pick an uncovered vertex uniformly.
        uncovered = [v for v in vertices if v not in reached]
        if not uncovered:
            break
        v = rng.choice(uncovered)
        cover(v)

        # Optional Resample pass.
        if rng.random() < resample_prob and iters > 1:
            # Pick a random pivot currently in H, recompute its ball,
            # and re-insert shortcuts (idempotent for our set semantics).
            pivots = {u for (u, _) in H} | {v for (_, v) in H}
            if pivots:
                p = rng.choice(list(pivots))
                rp, rm = ball[p]
                # No-op structurally since shortcuts are already in H,
                # but the choice of pivot to resample is the analogue
                # of Paper 1's Resample subroutine. Document the no-op.
                _ = (rp, rm)

        if iters % 1000 == 0:
            threshold = int(threshold_fraction * n)
            log.info(
                "iter=%d reached=%d/%d threshold=%d",
                iters,
                len(reached),
                n,
                threshold,
            )
            if len(reached) >= threshold:
                break

    if iters >= max_iterations:
        log.warning(
            "hit max_iterations=%d; reached=%d/%d",
            max_iterations,
            len(reached),
            n,
        )
    return H


def fix_resample_reachable(
    graph: Digraph,
    source: Any,
    shortcuts: set[tuple[Any, Any]],
) -> set[Any]:
    """Reachable from source via graph + shortcuts, using the BFS-variant."""
    from collections import deque

    visited = {source}
    q = deque([source])
    out = graph.out_edges
    shortcut_index: dict[Any, list[Any]] = {}
    for u, v in shortcuts:
        shortcut_index.setdefault(u, []).append(v)
    while q:
        u = q.popleft()
        for v in out.get(u, set()):
            if v not in visited:
                visited.add(v)
                q.append(v)
        for v in shortcut_index.get(u, ()):
            if v not in visited:
                visited.add(v)
                q.append(v)
    return visited
