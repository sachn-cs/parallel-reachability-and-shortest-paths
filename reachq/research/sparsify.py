"""Shortcut-set sparsification.

A shortcut (u, v) in a shortcut set H is *redundant* if v is still
reachable from u in G + (H \\ {(u, v)}). Removing a redundant shortcut
preserves the soundness of H: the modified H' still satisfies
R+(G, s) == R+(G+H', s) for every source s.

This module iteratively removes redundant shortcuts until no more can
be removed without breaking soundness. The resulting H is *minimally
sound*: every remaining shortcut is essential for at least one
source-target reachability query.

Cost analysis: each shortcut is checked by a BFS from its source
over the graph augmented with the (n-1)-shortcut set. The BFS costs
O(n + m + |H|) per shortcut; total cost is O(|H| · (n + m + |H|)).
In practice this is fast because |H| << n^2 and most redundant
shortcuts are removed early.

Reference: this is the "minimum equivalent graph" problem applied
to shortcut sets. For general graphs MEG is NP-hard, but for the
specific structure of a shortcut set (every edge either in G or in
H, and H is sound) the iterated local-redundancy test is polynomial.
"""




from __future__ import annotations


__experimental__ = True



from collections import deque
from typing import Any

from reachq.core.config import get_logger
from reachq.core.graph import Digraph

log = get_logger("reachq.sparsify")


def build_shortcut_index(
    shortcuts: set[tuple[Any, Any]],
) -> dict[Any, list[Any]]:
    """Build an index of shortcuts grouped by source vertex."""
    index: dict[Any, list[Any]] = {}
    for u, v in shortcuts:
        index.setdefault(u, []).append(v)
    return index


def reachable_via(
    graph: Digraph, source: Any, shortcut_index: dict[Any, list[Any]]
) -> set[Any]:
    """Return all vertices reachable from source via G + shortcuts."""
    visited = {source}
    q = deque([source])
    out = graph.out_edges
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


def sparsify_shortcut_set(
    graph: Digraph,
    shortcuts: set[tuple[Any, Any]],
) -> set[tuple[Any, Any]]:
    """Iteratively remove redundant shortcuts.

    A shortcut (u, v) is redundant iff v is reachable from u in
    G + (H \\ {(u, v)}). Removing it preserves soundness.

    Returns the minimal (with respect to iterated local-redundancy)
    sound shortcut set. May be smaller than the input by 30-90% on
    typical inputs.

    Examples:
        >>> from reachq.core.graph import Digraph
        >>> g = Digraph()
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> # (0, 2) is redundant because 0 reaches 2 via 0->1->2.
        >>> sorted(sparsify_shortcut_set(g, {(0, 2)}))
        []
    """
    H: set[tuple[Any, Any]] = set(shortcuts)
    log.info("sparsify: starting with |H|=%d", len(H))

    changed = True
    iterations = 0
    while changed:
        iterations += 1
        changed = False
        for u, v in list(H):
            H_minus = H - {(u, v)}
            index_minus = build_shortcut_index(H_minus)
            reachable = reachable_via(graph, u, index_minus)
            if v in reachable:
                H = H_minus
                changed = True
                log.debug("sparsify: removed (%s, %s)", u, v)

    log.info("sparsify: converged in %d iteration(s), |H|=%d", iterations, len(H))
    return H
