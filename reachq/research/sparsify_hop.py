"""beta-hopbound-preserving sparsification (research prototype).

The reachability-only sparsifier in ``reachq.research.sparsify``
removes a shortcut (u, v) whenever v is still reachable from u via
``G + (H \\ {(u, v)})`` without a hop limit. That preserves
reachability but can destroy the beta-hopbound guarantee of the JLS
construction: on a path of n=50 vertices the JLS shortcut set compresses
the diameter from 49 to 2 hops, and the reachability-only sparsifier
removes every shortcut, restoring the long path.

This module provides a sparsifier that only removes a shortcut when the
GLOBAL beta-hopbound is preserved, i.e. every pair (s, t) that is
reachable in G must remain reachable in ``G + (H \\ {(u, v)})`` within
beta hops. The greedy is correct by construction: it never removes a
shortcut whose removal would push any reachable pair above beta.

Honest scope:

* The correctness guarantee holds for every graph, but the per-removal
  check is an all-pairs hop-BFS, so the total cost is
  O(|H| * n * (n + m + |H|)). This is only practical for small graphs;
  the ``max_vertices`` guard refuses to run above a size threshold.
* "Minimality" is NOT claimed. Computing a minimum-size hop-bound
  shortcut set is NP-hard in general; the greedy output is simply a
  sound set with no locally-redundant shortcut (each remaining shortcut
  is essential for the beta-hopbound of at least one pair).
"""




from __future__ import annotations

__experimental__ = True



from collections import deque
from typing import Any

from reachq.config import get_logger
from reachq.graph import Digraph
from reachq.reachability import bfs_reachability

log = get_logger("reachq.sparsify_hop")


def bfs_limited(
    graph: Digraph,
    source: Any,
    max_depth: int,
    shortcuts: set[tuple[Any, Any]],
) -> dict[Any, int]:
    """BFS from source, limited to max_depth hops. Returns distance map.

    Returns dict[v] = d for v reached in d <= max_depth hops. If v
    is not reached in <= max_depth hops, it is absent from the dict.
    """
    dist: dict[Any, int] = {source: 0}
    q: deque = deque([source])
    out = graph.out_edges
    index: dict[Any, list[Any]] = {}
    for u, v in shortcuts:
        index.setdefault(u, []).append(v)
    while q:
        u = q.popleft()
        if dist[u] >= max_depth:
            continue
        for v in out.get(u, set()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
        for v in index.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def verify_hopbound_preserved(
    graph: Digraph,
    shortcuts: set[tuple[Any, Any]],
    beta: int,
) -> bool:
    """True iff every vertex pair reachable in G is also reachable in
    G + shortcuts within beta hops.

    Runs one unbounded BFS per source to determine the reachable set
    (which depends only on G) and one beta-limited BFS per source over
    G + shortcuts. Cost: O(n * (n + m + |H|)).
    """
    for s in graph.vertices():
        R = bfs_reachability(graph, s)
        dist = bfs_limited(graph, s, beta, shortcuts)
        for v in R:
            if v != s and v not in dist:
                return False
    return True


def _beta_for(graph: Digraph, omega: float) -> float:
    """Compute the realised hop bound for sparsify_hop_bounded.

    Mirrors :func:`reachq.core.shortcut._params_from_omega`.
    """
    from reachq.shortcut import _params_from_omega

    n = graph.num_vertices()
    m = graph.num_edges()
    _, _, _, beta, _ = _params_from_omega(n, m, omega)
    return beta


def sparsify_hop_bounded(
    graph: Digraph,
    shortcuts: set[tuple[Any, Any]],
    beta: int,
    *,
    max_iterations: int = 100,
    max_vertices: int = 200,
) -> set[tuple[Any, Any]]:
    """Beta-hopbound-preserving sparsification.

    Iteratively remove a shortcut (u, v) only when removing it leaves
    EVERY reachable pair connected within beta hops in
    G + (H \\ {(u, v)}). Each remaining shortcut is essential for the
    beta-hopbound of at least one pair, and the returned set satisfies
    the same beta-hopbound as the input.

    The all-pairs per-removal check is O(n * (n + m + |H|)), so the
    total cost is O(|H| * n * (n + m + |H|)). To stay practical, the
    function refuses to run on graphs above ``max_vertices`` (returning
    the input unchanged) and always verifies that the input already
    satisfies the beta-hopbound before touching it.

    Args:
        graph: The original digraph.
        shortcuts: A sound shortcut set (beta-hopbound guaranteed).
        beta: The hopbound that must be preserved.
        max_iterations: Cap on greedy passes over H.
        max_vertices: Refuse to run on larger graphs (all-pairs check
            is too expensive).

    Returns:
        A subset of ``shortcuts`` that preserves the beta-hopbound.
    """
    H: set[tuple[Any, Any]] = set(shortcuts)
    n = graph.num_vertices()
    if n > max_vertices:
        log.info(
            "sparsify_hop_bounded: skipping (n=%d > max_vertices=%d)",
            n,
            max_vertices,
        )
        return H
    if not verify_hopbound_preserved(graph, H, beta):
        log.warning(
            "sparsify_hop_bounded: input does not satisfy the beta-hopbound "
            "(beta=%d); returning input unchanged",
            beta,
        )
        return H
    log.info("sparsify_hop_bounded: starting with |H|=%d, beta=%d", len(H), beta)

    for iteration in range(max_iterations):
        changed = False
        for u, v in list(H):
            H_minus = H - {(u, v)}
            if verify_hopbound_preserved(graph, H_minus, beta):
                H = H_minus
                changed = True
        if not changed:
            log.info(
                "sparsify_hop_bounded: converged at iter=%d, |H|=%d",
                iteration,
                len(H),
            )
            return H
    log.info(
        "sparsify_hop_bounded: hit max_iterations=%d, |H|=%d",
        max_iterations,
        len(H),
    )
    return H
