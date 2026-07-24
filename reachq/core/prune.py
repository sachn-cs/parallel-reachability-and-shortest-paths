"""TC-pruning and hopbound-preserving pruning for shortcut sets.

TC-pruning (Improvement 7 in the paper): when the r-ball around a pivot
is small enough, compute the full transitive closure on that subset and
add all non-self pairs as shortcuts. This replaces individual shortcut
sampling with an exact all-pairs computation, which is cheaper when the
subset is small relative to the matrix multiplication exponent omega.
"""

from __future__ import annotations


from reachq.core.graph import Digraph
from reachq.core.tc import transitive_closure_on_subset


def compute_tc_pruning_threshold(
    k: float,
    log_n: float,
    rho: float,
    n: int,
    omega: float,
) -> float:
    """Compute the threshold below which TC-pruning is cost-effective.

    TC(G[R]) takes O(|R|^omega) ops; the alternative (sampling shortcuts
    for every vertex in R) costs O(|R| * k * log n). Trigger TC only when
    the former is cheaper.
    """
    threshold = (k**2) * (log_n**2) * (rho**2)
    if rho > 0 and log_n > 0:
        tight_cap = (rho * n * k * log_n) ** (1.0 / omega)
        threshold = min(threshold, tight_cap)
    return threshold


def apply_tc_pruning(
    graph: Digraph,
    r_ball: set[object],
    threshold: float,
) -> set[tuple[object, object]]:
    """Apply TC-pruning to a single pivot's r-ball.

    If |r_ball| <= threshold, compute the transitive closure on the
    induced subgraph and return all non-self pairs as shortcuts.
    Otherwise returns an empty set.

    Returns:
        Set of (u, v) shortcut pairs from the TC step.
    """
    if len(r_ball) == 0 or len(r_ball) > threshold:
        return set()
    tc = transitive_closure_on_subset(graph, r_ball)
    return {(u, v) for u, v in tc if u != v}
