"""Shortest path algorithms for weighted directed graphs.

Implements Dijkstra's algorithm, A* search with optional reopening,
truncated SSSP, and the hop-bounded SSSP primitive used by the
hopset construction. Heap entries always include a per-call
monotonic counter so that ties do not fall through to a vertex
comparison — this allows arbitrarily-hashable vertex keys
(including ``object()`` instances) without ``TypeError``.

The hop-bounded query is the layered DP required by Theorem 4:
each (vertex, hops_used) pair carries its own best distance.

All algorithms in this module are deterministic given the same
input and same insertion-ordered vertex iteration. Unreachable
vertices are *absent* from the returned mapping.
"""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Callable

from reachq.core.graph import WeightedDigraph


UNREACHABLE: int = 1 << 62
"""Sentinel larger than any polynomial weight. Returned by
:func:`shortest_path` when the target is unreachable from the source."""


def _require_source(graph: WeightedDigraph, source: object) -> None:
    if source not in graph:
        raise KeyError(f"source vertex {source!r} is not in the graph")


def dijkstra(graph: WeightedDigraph, source: object) -> dict[object, int]:
    """Compute exact shortest-path distances from ``source``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.

    Returns:
        Mapping ``vertex -> distance`` for every vertex reachable
        from ``source`` within integer arithmetic. Unreachable
        vertices are absent from the result.

    Raises:
        KeyError: If ``source`` is not in the graph.

    Complexity: O(m log n) time, O(n) space.
    """
    _require_source(graph, source)
    out = graph.out_edges
    distances: dict[object, int] = {source: 0}
    counter = itertools.count()
    heap: list[tuple[int, int, object]] = [(0, next(counter), source)]
    visited: set[object] = set()

    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < distances.get(v, 1 << 62):
                distances[v] = nd
                heapq.heappush(heap, (nd, next(counter), v))
    return distances


def astar(
    graph: WeightedDigraph,
    source: object,
    target: object,
    heuristic: Callable[[object], int],
    *,
    require_consistent: bool = False,
    reopen: bool = False,
) -> int | None:
    """A* search from ``source`` to ``target``.

    With ``require_consistent=True`` the heuristic is verified on
    every vertex reachable from the source: an inconsistent
    ``h(v) > dist(v, target) + h(target)`` pairing raises
    ``ValueError``. The verification runs an exact BFS bounded by
    ``dist(source, target) + h(source)`` so its cost is no worse
    than a single Dijkstra call.

    With ``reopen=True`` the closed set is removed: when a better
    ``g_score[v]`` arrives, the heap entry is updated and the
    frontier re-expands ``v``. Without reopening the closed set,
    A* on an inconsistent heuristic can return a suboptimal path.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.
        target: Target vertex.
        heuristic: Callable mapping a vertex to a non-negative
            lower bound on its distance to ``target``. Non-negative
            on every reachable vertex; consistent when the
            ``require_consistent=True`` flag is used.
        require_consistent: Validate the heuristic before search.
        reopen: Allow re-expansion of closed nodes.

    Returns:
        The shortest distance, or ``None`` if ``target`` is
        unreachable.

    Complexity: O(m log n) worst case.
    """
    _require_source(graph, source)
    if target not in graph:
        raise KeyError(f"target vertex {target!r} is not in the graph")
    if source == target:
        return 0
    if heuristic(target) != 0:
        raise ValueError("heuristic(target) must be 0")

    if require_consistent:
        h_source = heuristic(source)
        if h_source < 0:
            raise ValueError("heuristic must be non-negative")
        bound = h_source
        dijkstra_dist = dijkstra(graph, source)
        for v, d in dijkstra_dist.items():
            hv = heuristic(v)
            if hv < 0:
                raise ValueError(
                    f"heuristic({v!r}) must be non-negative (got {hv})"
                )
            if v == target:
                continue
            for w, wgt in graph.out_edges.get(v, {}).items():
                if d + wgt + heuristic(w) < hv:
                    raise ValueError(
                        f"heuristic is inconsistent on edge {v!r} -> {w!r}: "
                        f"h({v!r})={hv} > d+wg+h({w!r})"
                    )

    g_score: dict[object, int] = {source: 0}
    f_score: dict[object, int] = {source: heuristic(source)}
    counter = itertools.count()
    heap: list[tuple[int, int, int, object]] = [
        (f_score[source], 0, next(counter), source)
    ]
    closed: set[object] = set()
    out = graph.out_edges

    while heap:
        _, d, _, u = heapq.heappop(heap)
        if not reopen and u in closed:
            continue
        if d > g_score.get(u, 1 << 62):
            continue
        if u == target:
            return d
        closed.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < g_score.get(v, 1 << 62):
                g_score[v] = nd
                f_score[v] = nd + heuristic(v)
                heapq.heappush(
                    heap, (f_score[v], nd, next(counter), v)
                )
    return None


def truncated_dijkstra(
    graph: WeightedDigraph, source: object, max_distance: int
) -> dict[object, int]:
    """Compute distances from ``source``, truncated at ``max_distance``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.
        max_distance: Maximum distance to expand. Vertices with
            distance ``> max_distance`` are not returned.

    Returns:
        Mapping ``vertex -> distance`` for vertices ``v`` with
        ``dist(source, v) <= max_distance``.

    Raises:
        KeyError: If ``source`` is not in the graph.
        ValueError: If ``max_distance`` is negative.

    Complexity: O(m log n) worst case.
    """
    _require_source(graph, source)
    if max_distance < 0:
        raise ValueError(f"max_distance must be non-negative (got {max_distance})")
    out = graph.out_edges
    distances: dict[object, int] = {source: 0}
    counter = itertools.count()
    heap: list[tuple[int, int, object]] = [(0, next(counter), source)]
    visited: set[object] = set()

    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd <= max_distance and nd < distances.get(v, 1 << 62):
                distances[v] = nd
                heapq.heappush(heap, (nd, next(counter), v))
    return distances


def compute_d_descendants(
    graph: WeightedDigraph, vertex: object, distance: int
) -> set[object]:
    """Compute ``R^+_d(G, v) = {{t : v ⪯_d t}}``."""
    return set(truncated_dijkstra(graph, vertex, distance).keys())


def compute_d_ancestors(
    graph: WeightedDigraph,
    vertex: object,
    distance: int,
    *,
    rev: WeightedDigraph | None = None,
) -> set[object]:
    """Compute ``R^-_d(G, v) = {{s : s ⪯_d v}}``.

    If ``rev`` is supplied it is used as the reversed graph
    directly; otherwise the reversed graph is constructed once
    per call. Callers that perform many ancestor computations
    should hoist ``rev`` and pass it.
    """
    source_rev = rev if rev is not None else graph.reversed()
    return set(truncated_dijkstra(source_rev, vertex, distance).keys())


def compute_d_ball(
    graph: WeightedDigraph,
    vertex: object,
    distance: int,
    *,
    rev: WeightedDigraph | None = None,
) -> set[object]:
    """Compute ``R_d(G, v) = R^+_d(G, v) ∪ R^-_d(G, v)``."""
    return compute_d_descendants(graph, vertex, distance) | compute_d_ancestors(
        graph, vertex, distance, rev=rev
    )


def shortest_path_hopbound(
    graph: WeightedDigraph,
    hopset_edges,
    source: object,
    max_hops: int,
) -> dict[object, int]:
    """Compute shortest paths in ``G ∪ H`` using at most ``max_hops`` hops.

    This is the layered dynamic programming required by Theorem 4:
    distinct (vertex, hops_used) pairs carry independent distance
    records. A costlier arrival at vertex ``v`` that *uses fewer
    hops* than a known arrival is preserved when the unused hops
    may still be needed to reach a target within ``max_hops``.
    Heap ties on equal ``distance`` are broken by ``hops`` (lower
    wins) then by insertion counter, so the algorithm never
    compares vertex objects.

    Args:
        graph: The input weighted digraph.
        hopset_edges: Hopset ``H`` as a ``(u, v) -> weight`` mapping
            or a 2-iterable of ``(u, v, weight)`` triples.
        source: Source vertex.
        max_hops: Maximum number of hops allowed (non-negative).

    Returns:
        Mapping ``vertex -> distance`` for every vertex reachable
        from ``source`` within ``max_hops`` hops in ``G ∪ H``.
        Unreachable vertices are absent.

    Raises:
        KeyError: If ``source`` is not in the graph.
        ValueError: If ``max_hops`` is negative.
    """
    _require_source(graph, source)
    if max_hops < 0:
        raise ValueError(f"max_hops must be non-negative (got {max_hops})")

    out = graph.out_edges

    if hasattr(hopset_edges, "items"):
        hopset_pairs = ((a, b, weight) for (a, b), weight in hopset_edges.items())
    else:
        hopset_pairs = (
            (item[0], item[1], item[2])
            for item in hopset_edges
            if len(item) >= 3
        )
    hopset_index: dict[object, dict[object, int]] = {}
    for a, b, weight in hopset_pairs:
        hopset_index.setdefault(a, {})[b] = weight

    INF = 1 << 62
    best: dict[tuple[object, int], int] = {(source, 0): 0}
    result: dict[object, int] = {source: 0}
    counter = itertools.count()
    heap: list[tuple[int, int, int, object, int]] = [
        (0, 0, next(counter), source, 0)
    ]

    while heap:
        d, h, _, u, hops = heapq.heappop(heap)
        key = (u, hops)
        if d > best.get(key, INF):
            continue
        if h >= max_hops:
            continue

        for v, weight in out.get(u, {}).items():
            nd = d + weight
            nh = hops + 1
            nkey = (v, nh)
            if nh <= max_hops and nd < best.get(nkey, INF):
                best[nkey] = nd
                if nd < result.get(v, INF):
                    result[v] = nd
                heapq.heappush(
                    heap, (nd, nh, next(counter), v, nh)
                )

        for b, weight in hopset_index.get(u, {}).items():
            nd = d + weight
            nh = hops + 1
            nkey = (b, nh)
            if nh <= max_hops and nd < best.get(nkey, INF):
                best[nkey] = nd
                if nd < result.get(b, INF):
                    result[b] = nd
                heapq.heappush(
                    heap, (nd, nh, next(counter), b, nh)
                )

    return result


def shortest_path_tree(
    graph: WeightedDigraph, source: object
) -> dict[object, object | None]:
    """Compute a shortest-path tree from ``source``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.

    Returns:
        Mapping ``vertex -> parent`` where ``parent[v]`` is the
        predecessor of ``v`` on a shortest path from ``source``,
        or ``None`` for unreachable vertices.

    Raises:
        KeyError: If ``source`` is not in the graph.

    Complexity: O(m log n) time, O(n) space.
    """
    _require_source(graph, source)
    out = graph.out_edges
    distances: dict[object, int] = {source: 0}
    parent: dict[object, object | None] = {v: None for v in graph.vertices()}
    counter = itertools.count()
    heap: list[tuple[int, int, object]] = [(0, next(counter), source)]
    visited: set[object] = set()
    INF = 1 << 62

    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < distances.get(v, INF):
                distances[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, next(counter), v))
    return parent


def shortest_path(graph: WeightedDigraph, source: object, target: object) -> int:
    """Return the shortest distance from ``source`` to ``target``.

    Returns :data:`UNREACHABLE` (an integer sentinel larger than any
    polynomial weight) if ``target`` is unreachable from ``source``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.
        target: Target vertex.

    Returns:
        Shortest distance, or :data:`UNREACHABLE` for unreachable
        targets.

    Raises:
        KeyError: If ``source`` is not in the graph.
    """
    _require_source(graph, source)
    distances = dijkstra(graph, source)
    return distances.get(target, UNREACHABLE)
