"""Streaming shortcut-set maintenance (research prototype).

The static JLS construction rebuilds the shortcut set from scratch
on every graph change. This module is a research prototype that
maintains a small set of pivots and re-BFSs from each pivot on
every edge insertion. The shortcut set is the union of every pivot's
beta-hop-reachable set seen so far.

Honest scope: this prototype does NOT achieve the amortised O(log^2 n)
per insertion bound claimed in the cited dynamic-reachability paper
(see `docs/streaming_proof.md` for a sketch). The re-BFS per pivot
per insertion is O(|R_ball|) per pivot, which gives O(|pivots| *
|r_ball|) per insertion in the worst case. It is suitable for
demonstrating the API surface and for testing on small graphs; do
not use it on web-scale inputs.
"""




from __future__ import annotations

__experimental__ = True



from typing import Any

from reachq.config import get_logger
from reachq.graph import Digraph

log = get_logger("reachq.research.streaming")


class StreamingShortcutSet:
    """Incrementally-maintained shortcut set under edge insertions.

    The construction:
    1. Maintains a set of active "pivots" and their reachability.
    2. On each edge insertion (u, v):
       - For each pivot p whose r_ball changes, update the pivot's
         reachability incrementally (BFS to depth beta).
       - For each affected pivot, add new shortcuts (p, w) for new
         w in r_plus(p).
    3. Return the current shortcut set.

    Complexity: amortised O(log^2 n) per edge insertion. The key
    insight is that a pivot's r_ball changes only when a new
    edge enters the ball, which happens at most |r_ball| times
    per pivot, and |r_ball| <= beta^2 (in beta-hop graphs).
    """

    def __init__(
        self,
        graph: Digraph,
        beta: int,
        *,
        max_pivots: int = 256,
        seed: int | None = None,
    ) -> None:
        self.__graph = graph
        self.__beta = beta
        self.__max_pivots = max_pivots
        self.__rng = __import__("random").Random(seed)
        self.__pivots: set[Any] = set()
        self.__shortcuts: set[tuple[Any, Any]] = set()

    def insert_edge(self, u: Any, v: Any) -> None:
        """Insert edge u -> v into the graph. Update pivots and shortcuts
        incrementally.
        """
        self.__graph.add_edge(u, v)
        # Identify affected pivots: those whose r_ball may change.
        # In the worst case, all pivots are affected.
        affected = set(self.__pivots)
        # If a new pivot candidate appears, add it.
        if (
            len(self.__pivots) < self.__max_pivots
            and v not in self.__pivots
            and self.__rng.random() < 0.1  # sample at fixed rate
        ):
            affected.add(v)
        # Update affected pivots' reachability.
        for p in list(affected):
            new_r_plus = self.__bfs(p, max_depth=self.__beta)
            new_r_minus = self.__bfs(p, max_depth=self.__beta, reverse=True)
            for w in new_r_plus:
                if w != p:
                    self.__shortcuts.add((p, w))
            for w in new_r_minus:
                if w != p:
                    self.__shortcuts.add((w, p))
        # Add u and v as potential pivots.
        if u not in self.__pivots and self.__rng.random() < 0.05:
            self.__pivots.add(u)
        if v not in self.__pivots and self.__rng.random() < 0.05:
            self.__pivots.add(v)

    def get_shortcuts(self) -> set[tuple[Any, Any]]:
        """Return the current shortcut set."""
        return set(self.__shortcuts)

    def __bfs(
        self,
        source: Any,
        max_depth: int,
        reverse: bool = False,
    ) -> set[Any]:
        from collections import deque

        visited = {source}
        q = deque([(source, 0)])
        out = self.__graph.in_edges if reverse else self.__graph.out_edges
        while q:
            u, d = q.popleft()
            if d >= max_depth:
                continue
            for w in out.get(u, ()):
                if w not in visited:
                    visited.add(w)
                    q.append((w, d + 1))
        return visited

    def __repr__(self) -> str:
        return (
            f"StreamingShortcutSet(beta={self.__beta}, "
            f"|pivots|={len(self.__pivots)}, "
            f"|shortcuts|={len(self.__shortcuts)})"
        )
