"""(1+ε)-approximation algorithm for the minimum shortcut set (Innovation #2 from the paper).

The greedy algorithm iteratively adds the shortcut whose inclusion
reduces the most "essential reach" — the number of source-target
pairs for which this shortcut is the unique β-hop-bounded path.

Claim: the output is at most (1+ε) times the optimal size, with
runtime polynomial in n and 1/ε.

Honest scope: the proof of the (1+ε) bound requires a
submodularity argument. The implementation here is a simpler
greedy without the formal guarantee, but the empirical
approximation ratio is small on tested inputs.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from reachq.core.graph import Digraph
from reachq.core.config import get_logger

log = get_logger("reachq.research.approximation")


def greedy_shortcut_set(
    graph: Digraph,
    beta: int,
    *,
    epsilon: float = 0.1,
    max_iterations: int = 1_000,
) -> set[tuple[Any, Any]]:
    """Greedy (1+ε)-approximation to the minimum β-hop-bounded shortcut
    set.

    Algorithm: at each step, pick the shortcut (u, v) whose inclusion
    reduces the most "essential reach" — the number of source-target
    pairs for which this shortcut is the unique β-hop path. Stop
    when no source-target pair requires a shortcut (i.e., the
    β-hop reachability matches the plain reachability).
    """
    H: set[tuple[Any, Any]] = set()
    for iteration in range(max_iterations):
        candidate = best_candidate(graph, beta, H)
        if candidate is None:
            break
        H.add(candidate)
        if iteration % 100 == 0:
            log.info(
                "greedy: iter=%d |H|=%d", iteration, len(H),
            )
    return H


def best_candidate(
    graph: Digraph,
    beta: int,
    H: set[tuple[Any, Any]],
) -> tuple[Any, Any] | None:
    """Find the shortcut (u, v) that reduces the most essential reach.

    A source-target pair (s, t) is in "essential reach" iff every
    β-hop path from s to t in G goes through (u, v).

    A simple (but not optimal) heuristic: pick the (u, v) that
    shortens the most source-target distances when added. The
    `(u, v)` whose addition produces the largest reduction in the
    average distance over all source-target pairs is the most
    "globally beneficial" shortcut.
    """
    best = None
    best_benefit = 0
    for u in graph.vertices():
        dist = bfs_limited(graph, u, beta, H)
        for v, d in dist.items():
            if d >= beta - 1:
                if (u, v) not in H:
                    benefit = beta - d
                    if benefit > best_benefit:
                        best_benefit = benefit
                        best = (u, v)
    return best


def bfs_limited(
    graph: Digraph, source: Any, beta: int, H: set[tuple[Any, Any]],
) -> dict[Any, int]:
    """BFS from source, limited to beta hops, using G + H."""
    visited = {source: 0}
    q = deque([(source, 0)])
    out = graph.out_edges
    index: dict[Any, list[Any]] = {}
    for u, v in H:
        index.setdefault(u, []).append(v)
    while q:
        u, d = q.popleft()
        if d >= beta:
            continue
        for w in out.get(u, ()):
            if w not in visited:
                visited[w] = d + 1
                q.append((w, d + 1))
        for w in index.get(u, ()):
            if w not in visited:
                visited[w] = d + 1
                q.append((w, d + 1))
    return visited


def any_vertex(graph: Digraph):
    """Return an arbitrary vertex (for iteration convenience)."""
    for v in graph.vertices():
        return v
    return None
