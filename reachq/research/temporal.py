"""Reachability over temporal graphs.

A temporal graph (also called a time-varying graph) is a directed
graph where each edge has an associated timestamp. Reachability is
restricted to edges whose timestamps respect a *temporal walk*:
edges must be traversed in non-decreasing order of timestamp.

Formally, a temporal walk from ``s`` to ``t`` is a sequence of
edges ``(u_0, v_0, tau_0), (u_1, v_1, tau_1), ..., (u_k, v_k, tau_k)``
with ``u_0 = s``, ``v_k = t``, ``v_i = u_{i+1}`` for ``i < k``,
and ``tau_i <= tau_{i+1}`` for all i.

This module implements:

1. :class:`TemporalDigraph` — a digraph with timestamped edges.
2. :func:`temporal_bfs` — BFS that respects temporal ordering.
3. :func:`earliest_arrival` — earliest timestamp at which a target
   becomes reachable from a source.

Temporal reachability is strictly harder than standard reachability
because the temporal walk constraint is monotone in time. For any
fixed source ``s``, the set of vertices reachable at time ``tau`` is
non-decreasing with ``tau``; the "earliest arrival" problem asks for
the minimum ``tau`` at which a target becomes reachable.

Reference: Xuan, Ferreira, Jarry, "Computing shortest, fastest, and
foremost walks in temporal graphs." *J. Comput. System Sci. 69
(2004)*. Our implementation is the classical BFS-based labelling
algorithm (Algorithm 1 in that paper).
"""




from __future__ import annotations

__experimental__ = True



from collections import deque
from collections.abc import Iterable

TemporalEdge = tuple[object, object, int]
"""A temporal edge: (source, target, timestamp)."""


class TemporalDigraph:
    """A directed graph whose edges carry timestamps.

    Each edge is a ``(u, v, tau)`` triple. Multiple edges between
    the same pair of vertices at different timestamps are allowed.

    Attributes:
        num_vertices: |V|.
        num_edges: |E| (counting all temporal edges).
    """

    __slots__ = ("_edges", "_out", "_vertices")

    def __init__(self) -> None:
        self._vertices: set[object] = set()
        self._edges: list[TemporalEdge] = []
        # Inverted index: vertex -> sorted list of (timestamp, target).
        self._out: dict[object, list[tuple[int, object]]] = {}

    @property
    def num_vertices(self) -> int:
        return len(self._vertices)

    @property
    def num_edges(self) -> int:
        return len(self._edges)

    def add_vertex(self, v: object) -> None:
        """Add a vertex. Idempotent."""
        self._vertices.add(v)

    def add_edge(self, u: object, v: object, tau: int) -> None:
        """Add a temporal edge (u, v) at time ``tau``.

        Multiple edges with the same (u, v) but different timestamps
        are all stored. Edges are kept in timestamp-sorted order
        within each adjacency list for efficient forward traversal.
        """
        self._vertices.add(u)
        self._vertices.add(v)
        self._edges.append((u, v, tau))
        self._out.setdefault(u, []).append((tau, v))
        # Keep sorted by timestamp. Insertion is O(k) where k is the
        # number of edges from u; we accept this for clarity. Use
        # bisect if hot path demands it.
        self._out[u].sort(key=lambda x: x[0])

    def vertices(self) -> set[object]:
        """Return the vertex set."""
        return set(self._vertices)

    def edges(self) -> list[TemporalEdge]:
        """Return all temporal edges."""
        return list(self._edges)

    def outgoing(self, u: object) -> list[tuple[int, object]]:
        """Return ``[(timestamp, target), ...]`` for edges from ``u``,
        sorted by timestamp.
        """
        return list(self._out.get(u, ()))

    def __repr__(self) -> str:
        return f"TemporalDigraph(V={self.num_vertices}, |E|={self.num_edges})"


def temporal_bfs(
    tg: TemporalDigraph,
    source: object,
    *,
    start_time: int = 0,
    max_time: int | None = None,
) -> set[object]:
    """Return vertices reachable from ``source`` via temporal walks.

    A temporal walk is a sequence of edges with non-decreasing
    timestamps, starting at or after ``start_time`` and (optionally)
    ending at or before ``max_time``.

    The source vertex itself is included in the result (reflexive
    closure). If ``source`` is not a vertex of the temporal graph,
    the empty set is returned.

    Args:
        tg: Input temporal digraph.
        source: Starting vertex.
        start_time: Minimum allowed timestamp for any traversed
            edge (default 0).
        max_time: Maximum allowed timestamp (inclusive). Default
            ``None`` means no upper bound.

    Returns:
        Set of reachable vertices including ``source``.
    """
    if source not in tg._vertices:
        return set()

    visited: set[object] = {source}
    # Each queue entry carries the latest timestamp seen so far on
    # the path; only outgoing edges with timestamp >= that value are
    # eligible.
    q: deque[tuple[object, int]] = deque([(source, start_time)])
    while q:
        u, latest = q.popleft()
        for tau, v in tg._out.get(u, ()):
            if tau < latest:
                continue
            if max_time is not None and tau > max_time:
                continue
            if v not in visited:
                visited.add(v)
                # The latest timestamp on the new path is tau.
                q.append((v, tau))
    return visited


def earliest_arrival(
    tg: TemporalDigraph,
    source: object,
    target: object,
) -> int | None:
    """Compute the earliest arrival time from ``source`` to ``target``.

    Returns the minimum timestamp ``tau`` of any temporal edge that
    can be the last edge of a temporal walk from ``source`` to
    ``target``. Returns ``None`` if ``target`` is unreachable from
    ``source``.

    Algorithm: classical BFS-labelling, O(|E|) work.

    Args:
        tg: Input temporal digraph.
        source: Source vertex.
        target: Target vertex.

    Returns:
        Earliest arrival timestamp, or ``None`` if unreachable.
    """
    if source not in tg._vertices or target not in tg._vertices:
        return None
    if source == target:
        return 0
    # label[v] = earliest arrival time at v.
    INF = 1 << 62
    label: dict[object, int] = {v: INF for v in tg._vertices}
    label[source] = 0
    # FIFO queue. New arrivals with smaller labels are not possible
    # (BFS order = increasing timestamp), so a vertex is enqueued at
    # most once.
    q: deque[object] = deque([source])
    while q:
        u = q.popleft()
        latest = label[u]
        for tau, v in tg._out.get(u, ()):
            if tau < latest:
                continue
            if tau < label[v]:
                label[v] = tau
                q.append(v)
    if label[target] == INF:
        return None
    return label[target]


def from_temporal_edges(
    edges: Iterable[TemporalEdge],
) -> TemporalDigraph:
    """Build a :class:`TemporalDigraph` from a flat list of temporal edges.

    Args:
        edges: Iterable of (u, v, tau) triples.

    Returns:
        A new :class:`TemporalDigraph` containing every edge.
    """
    tg = TemporalDigraph()
    for u, v, tau in edges:
        tg.add_edge(u, v, tau)
    return tg
