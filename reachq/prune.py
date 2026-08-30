"""TC-pruning and hopbound-preserving pruning for shortcut sets.

TC-pruning (paper Theorem 2): when the r-ball around a pivot is
small enough, compute the full transitive closure on that subset
and add all non-self pairs as shortcuts. This replaces individual
shortcut sampling with an exact all-pairs computation, which is
cheaper when the subset is small relative to the matrix
multiplication exponent omega.
"""

from __future__ import annotations

from reachq.closure import transitive_closure_on_subset
from reachq.graph import Digraph


def compute_tc_pruning_threshold(
    k: float,
    log_n: float,
    rho: float,
    n: int,
    omega: float,
) -> float:
    """Compute the threshold below which TC-pruning is cost-effective.

    TC(G[R]) costs ``O(|R|^ω)`` ops; the alternative (sampling
    shortcuts for every vertex in R) costs ``O(|R| * k * log n)``.
    Trigger TC when the former is cheaper.

    Args:
        k: Hopbound parameter.
        log_n: ``log_2(n)``.
        rho: Hop-parameter.
        n: Number of vertices.
        omega: Fast-matrix-multiplication exponent.

    Returns:
        The threshold ``|R|`` below which TC-pruning is cheaper.
    """
    threshold = (k**2) * (log_n**2) * (rho**2)
    if rho > 0 and log_n > 0:
        tight_cap = (rho * n * k * log_n) ** (1.0 / omega)
        threshold = min(threshold, tight_cap)
    return threshold


def apply_tc_pruning(
    graph: Digraph,
    r_ball,
    threshold: float,
    *,
    max_pairs: int | None = None,
) -> set[tuple[object, object]]:
    """Apply TC-pruning to a single pivot's r-ball.

    Args:
        graph: The input digraph ``G``.
        r_ball: The pivot's r-ball as a container of vertices.
        threshold: Maximum ``|r_ball|`` for which TC-pruning is
            applied.
        max_pairs: Maximum number of TC pairs to emit; defaults to
            ``min(2_000_000, n*(n-1))`` for ``n = |r_ball|``.

    Returns:
        Set of non-self ``(u, v)`` shortcut pairs from TC-pruning.
        Empty when ``|r_ball|`` exceeds ``threshold`` or when the
        budget is exhausted.
    """
    r_ball_set = set(r_ball)
    if len(r_ball_set) == 0 or len(r_ball_set) > threshold:
        return set()
    budget = (
        max_pairs
        if max_pairs is not None
        else min(
            2_000_000,
            len(r_ball_set) * (len(r_ball_set) - 1),
        )
    )
    if budget == len(r_ball_set) * (len(r_ball_set) - 1):
        budget = 2_000_000
    tc = transitive_closure_on_subset(graph, r_ball_set, max_pairs=budget)
    return {(u, v) for u, v in tc if u != v}


__all__ = [
    "apply_tc_pruning",
    "compute_tc_pruning_threshold",
]
