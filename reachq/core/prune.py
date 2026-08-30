"""TC-pruning and hopbound-preserving pruning for shortcut sets.

TC-pruning (paper Theorem 2): when the r-ball around a pivot is
small enough, compute the full transitive closure on that subset
and add all non-self pairs as shortcuts. This replaces individual
shortcut sampling with an exact all-pairs computation, which is
cheaper when the subset is small relative to the matrix
multiplication exponent omega.

The closure is now in the Boolean semiring
(:mod:`reachq.core.tc`) and respects an explicit
``max_pairs`` budget; see
:class:`reachq.core.tc.TransitiveClosureBudgetError`.
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

    The paper's analysis: TC(G[R]) costs O(|R|^ω) ops; the
    alternative (sampling shortcuts for every vertex in R) costs
    O(|R| * k * log n). Trigger TC when the former is cheaper.

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


def default_max_pairs(n: int) -> int:
    """Default ``max_pairs`` budget for a graph with ``n`` vertices.

    Caps at 2 million pairs and at the all-pairs upper bound so
    that TC-pruning does not silently request O(n^2) memory.
    """
    return min(2 * 10**6, n * (n - 1))


def apply_tc_pruning(
    graph: Digraph,
    r_ball,
    threshold: float,
    *,
    max_pairs: int | None = None,
) -> set[tuple[object, object]]:
    """Apply TC-pruning to a single pivot's r-ball.

    If ``|r_ball| <= threshold``, compute TC on the induced
    subgraph, apply the budget, and emit non-self pairs as
    shortcuts. Otherwise returns an empty set.

    Args:
        graph: The input digraph ``G``.
        r_ball: The pivot's r-ball as a container of vertices.
        threshold: Maximum ``|r_ball|`` for which TC-pruning is
            applied.
        max_pairs: Maximum number of TC pairs to emit; defaults to
            :func:`default_max_pairs` for ``len(r_ball)``.

    Returns:
        Set of ``(u, v)`` shortcut pairs from TC-pruning. Empty
        when ``|r_ball|`` exceeds ``threshold`` or when the budget
        is exhausted.
    """
    r_ball_set = set(r_ball)
    if len(r_ball_set) == 0 or len(r_ball_set) > threshold:
        return set()
    budget = max_pairs if max_pairs is not None else default_max_pairs(
        len(r_ball_set)
    )
    try:
        tc = transitive_closure_on_subset(graph, r_ball_set, max_pairs=budget)
    except Exception:
        return set()
    return {(u, v) for u, v in tc if u != v}
