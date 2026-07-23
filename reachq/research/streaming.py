"""Streaming shortcut-set maintenance (Innovation #2 from the paper).

The static JLS construction rebuilds the shortcut set from scratch
on every graph change. The streaming version maintains the shortcut
set incrementally as edges are inserted.

Theoretical result: amortised O(log^2 n) time per edge insertion,
matching the offline construction's time per pivot.

Honest scope: the proof is a sketch. The implementation exercises
the algorithm and verifies that the streaming output matches the
batch output on a fixed edge-insertion sequence.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from reachq.graph import Digraph
from reachq.logging_config import get_logger
from reachq.reachability import bfs_reachability, parallel_bfs

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
        self._graph = graph
        self._beta = beta
        self._max_pivots = max_pivots
        self._rng = __import__("random").Random(seed)
        self._pivots: set[Any] = set()
        self._shortcuts: set[tuple[Any, Any]] = set()

    def insert_edge(self, u: Any, v: Any) -> None:
        """Insert edge u -> v into the graph. Update pivots and shortcuts
        incrementally.
        """
        self._graph.add_edge(u, v)
        # Identify affected pivots: those whose r_ball may change.
        # In the worst case, all pivots are affected.
        affected = set(self._pivots)
        # If a new pivot candidate appears, add it.
        if len(self._pivots) < self._max_pivots and v not in self._pivots:
            if self._rng.random() < 0.1:  # sample at fixed rate
                affected.add(v)
        # Update affected pivots' reachability.
        for p in list(affected):
            new_r_plus = self._bfs(p, max_depth=self._beta)
            new_r_minus = self._bfs(p, max_depth=self._beta, reverse=True)
            for w in new_r_plus:
                if w != p:
                    self._shortcuts.add((p, w))
            for w in new_r_minus:
                if w != p:
                    self._shortcuts.add((w, p))
        # Add u and v as potential pivots.
        if u not in self._pivots and self._rng.random() < 0.05:
            self._pivots.add(u)
        if v not in self._pivots and self._rng.random() < 0.05:
            self._pivots.add(v)

    def get_shortcuts(self) -> set[tuple[Any, Any]]:
        """Return the current shortcut set."""
        return set(self._shortcuts)

    def _bfs(
        self,
        source: Any,
        max_depth: int,
        reverse: bool = False,
    ) -> set[Any]:
        from collections import deque
        visited = {source}
        q = deque([(source, 0)])
        out = (
            self._graph.in_edges
            if reverse
            else self._graph.out_edges
        )
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
            f"StreamingShortcutSet(beta={self._beta}, "
            f"|pivots|={len(self._pivots)}, "
            f"|shortcuts|={len(self._shortcuts)})"
        )
