"""Shortest-path algorithms for weighted digraphs.

Implements Dijkstra, A* search (with optional reopen and consistency
validation), truncated SSSP, and the hop-bounded SSSP primitive
used by the hopset construction (Theorem 4).

Heap-tie correctness: every heap entry includes a per-call
monotonic counter, so ties never compare vertex objects. This
allows arbitrarily-hashable vertex keys (``object()``,
``frozenset``, custom classes) without ``TypeError``.

The hop-bounded query ``shortest_path_hopbound`` implements the
layered dynamic programming required by Theorem 4: each
(vertex, hops_used) pair carries its own best distance, so a
costlier arrival that uses fewer hops is preserved when the
unused hops may still be needed to reach a target within
``max_hops``.

Unreachable vertices are *absent* from the returned mapping. For
``shortest_path`` use the constant ``UNREACHABLE`` as a sentinel
for an unreachable target.
"""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Callable
from typing import TYPE_CHECKING

from reachq.errors import ReachqGraphError, ReachqValueError

if TYPE_CHECKING:
    from reachq.graph import WeightedDigraph

UNREACHABLE: int = 1 << 62
"""Sentinel larger than any polynomial weight. Returned by
:func:`shortest_path` when the target is unreachable from the source."""


def dijkstra(graph: WeightedDigraph, source: object) -> dict[object, int]:
    """Compute exact shortest-path distances from ``source``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.

    Returns:
        Mapping ``vertex -> distance`` for every vertex reachable
        from ``source``. Unreachable vertices are absent.

    Raises:
        ReachqGraphError: If ``source`` is not in the graph.

    Complexity: O(m log n) time, O(n) space.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
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
    reopen: bool = False,
) -> int | None:
    """A* search from ``source`` to ``target``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.
        target: Target vertex.
        heuristic: Callable mapping a vertex to a non-negative lower
            bound on its distance to ``target``. Must satisfy
            ``h(target) == 0``.
        reopen: When True, allow re-expansion of closed nodes. When
            False (default), the closed set is honored and an
            inconsistent heuristic may return a suboptimal path.

    Returns:
        Shortest distance, or ``None`` if ``target`` is unreachable.

    Raises:
        ReachqGraphError: If ``source`` or ``target`` is not in the
            graph, or if ``heuristic(target) != 0``.

    Complexity: O(m log n) worst case.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    if target not in graph:
        raise ReachqGraphError(f"target {target!r} not in graph")
    if source == target:
        return 0
    if heuristic(target) != 0:
        raise ReachqValueError("heuristic(target) must be 0")

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
        ReachqGraphError: If ``source`` is not in the graph.
        ReachqValueError: If ``max_distance`` is negative.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    if max_distance < 0:
        raise ReachqValueError(
            f"max_distance must be non-negative (got {max_distance})"
        )
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
    """Compute ``R^+_d(G, v) = {{t : v <=_d t}}``."""
    return set(truncated_dijkstra(graph, vertex, distance).keys())


def compute_d_ancestors(
    graph: WeightedDigraph,
    vertex: object,
    distance: int,
    *,
    rev: WeightedDigraph | None = None,
) -> set[object]:
    """Compute ``R^-_d(G, v) = {{s : s <=_d v}}``.

    If ``rev`` is supplied it is used as the reversed graph
    directly; otherwise the reversed graph is constructed once per
    call. Callers that perform many ancestor computations should
    hoist ``rev`` and pass it.
    """
    source_rev = rev if rev is not None else graph.reversed()
    return set(truncated_dijkstra(source_rev, vertex, distance).keys())


def shortest_path_hopbound(
    graph: WeightedDigraph,
    hopset_edges,
    source: object,
    max_hops: int,
) -> dict[object, int]:
    """Compute shortest paths in ``G ∪ H`` using at most ``max_hops`` hops.

    The layered dynamic programming required by Theorem 4: distinct
    (vertex, hops_used) pairs carry independent distance records. A
    costlier arrival at vertex ``v`` that uses fewer hops than a
    known arrival is preserved when the unused hops may still be
    needed to reach a target within ``max_hops``. Heap ties on
    equal ``distance`` are broken by ``hops`` (lower wins) then by
    insertion counter, so the algorithm never compares vertex
    objects.

    Args:
        graph: The input weighted digraph.
        hopset_edges: Hopset ``H`` as a ``(u, v) -> weight`` mapping
            or an iterable of ``(u, v, weight)`` triples.
        source: Source vertex.
        max_hops: Maximum number of hops allowed (non-negative).

    Returns:
        Mapping ``vertex -> distance`` for every vertex reachable
        from ``source`` within ``max_hops`` hops in ``G ∪ H``.
        Unreachable vertices are absent.

    Raises:
        ReachqGraphError: If ``source`` is not in the graph.
        ReachqValueError: If ``max_hops`` is negative.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    if max_hops < 0:
        raise ReachqValueError(f"max_hops must be non-negative (got {max_hops})")

    out = graph.out_edges

    if hasattr(hopset_edges, "items"):
        hopset_pairs = (
            (a, b, weight) for (a, b), weight in hopset_edges.items()
        )
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
    best_at_hop: dict[tuple[object, int], int] = {(source, 0): 0}
    result: dict[object, int] = {source: 0}
    counter = itertools.count()
    heap: list[tuple[int, int, int, object, int]] = [
        (0, 0, next(counter), source, 0)
    ]

    while heap:
        d, h, _, u, hops = heapq.heappop(heap)
        key = (u, hops)
        if d > best_at_hop.get(key, INF):
            continue
        if h >= max_hops:
            continue

        for v, weight in out.get(u, {}).items():
            nd = d + weight
            nh = hops + 1
            nkey = (v, nh)
            if nh <= max_hops and nd < best_at_hop.get(nkey, INF):
                best_at_hop[nkey] = nd
                if nd < result.get(v, INF):
                    result[v] = nd
                heapq.heappush(heap, (nd, nh, next(counter), v, nh))

        for b, weight in hopset_index.get(u, {}).items():
            nd = d + weight
            nh = hops + 1
            nkey = (b, nh)
            if nh <= max_hops and nd < best_at_hop.get(nkey, INF):
                best_at_hop[nkey] = nd
                if nd < result.get(b, INF):
                    result[b] = nd
                heapq.heappush(heap, (nd, nh, next(counter), b, nh))

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
        ReachqGraphError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    out = graph.out_edges
    distances: dict[object, int] = {source: 0}
    parent: dict[object, object | None] = {
        v: None for v in graph.iter_vertices()
    }
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


def shortest_path(
    graph: WeightedDigraph, source: object, target: object
) -> int:
    """Return the shortest distance from ``source`` to ``target``.

    Returns :data:`UNREACHABLE` if ``target`` is unreachable from
    ``source``.

    Args:
        graph: The input weighted digraph.
        source: Source vertex.
        target: Target vertex.

    Returns:
        Shortest distance, or :data:`UNREACHABLE` for unreachable
        targets.

    Raises:
        ReachqGraphError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    distances = dijkstra(graph, source)
    return distances.get(target, UNREACHABLE)


__all__ = [
    "UNREACHABLE",
    "astar",
    "compute_d_ancestors",
    "compute_d_descendants",
    "dijkstra",
    "shortest_path",
    "shortest_path_hopbound",
    "shortest_path_tree",
    "truncated_dijkstra",
]
