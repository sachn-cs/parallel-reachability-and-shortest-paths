"""Shortest path algorithms for weighted directed graphs.

Implements Dijkstra's algorithm, A* search, truncated SSSP, and d-ball
computations as used in the hopset construction (Section 6).
"""

import heapq
from collections.abc import Callable

from reachq.core.graph import WeightedDigraph


def dijkstra(graph: WeightedDigraph, source: object) -> dict[object, float]:
    """Compute exact shortest-path distances from source.

    Time: O(m log n). Space: O(n).
    """
    distances: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    distances[source] = 0
    heap: list[tuple[float, object]] = [(0, source)]
    visited: set[object] = set()
    out = graph.out_edges

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < distances[v]:
                distances[v] = nd
                heapq.heappush(heap, (nd, v))
    return distances


def astar(
    graph: WeightedDigraph,
    source: object,
    target: object,
    heuristic: Callable[[object], int],
) -> int | None:
    """A* search from source to target with an admissible heuristic.

    Returns the shortest distance from source to target, or None if unreachable.
    The heuristic h(v) must be admissible: 0 ≤ h(v) ≤ dist(v, target) for all v.

    Time: O(m log n) worst case, but typically much faster than Dijkstra
    when the heuristic is informative.
    """
    if source == target:
        return 0

    g_score: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    g_score[source] = 0
    f_score: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    f_score[source] = heuristic(source)

    heap: list[tuple[float, int, object]] = [(f_score[source], 0, source)]
    visited: set[object] = set()
    out = graph.out_edges

    while heap:
        _, d, u = heapq.heappop(heap)
        if u in visited:
            continue
        if u == target:
            return d
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < g_score[v]:
                g_score[v] = nd
                f_score[v] = nd + heuristic(v)
                heapq.heappush(heap, (f_score[v], nd, v))
    return None


def truncated_dijkstra(
    graph: WeightedDigraph, source: object, max_distance: int
) -> dict[object, float]:
    """Compute distances from source, truncated at max_distance.

    Returns vertices v with dist(source, v) ≤ max_distance.
    """
    distances: dict[object, float] = {source: 0}
    heap: list[tuple[float, object]] = [(0, source)]
    visited: set[object] = set()
    out = graph.out_edges

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd <= max_distance and nd < distances.get(v, float("inf")):
                distances[v] = nd
                heapq.heappush(heap, (nd, v))
    return distances


def compute_d_descendants(
    graph: WeightedDigraph, vertex: object, distance: int
) -> set[object]:
    """Compute R^+_d(G, v) = {t : v ⪯_d t}."""
    return set(truncated_dijkstra(graph, vertex, distance).keys())


def compute_d_ancestors(
    graph: WeightedDigraph, vertex: object, distance: int
) -> set[object]:
    """Compute R^-_d(G, v) = {s : s ⪯_d v}."""
    rev = graph.reversed()
    return set(truncated_dijkstra(rev, vertex, distance).keys())


def compute_d_ball(
    graph: WeightedDigraph, vertex: object, distance: int
) -> set[object]:
    """Compute R_d(G, v) = R^+_d(G, v) ∪ R^-_d(G, v)."""
    return compute_d_descendants(graph, vertex, distance) | compute_d_ancestors(
        graph, vertex, distance
    )


def shortest_path_hopbound(
    graph: WeightedDigraph,
    hopset_edges: dict[tuple[object, object], float],
    source: object,
    max_hops: int,
) -> dict[object, float]:
    """Compute shortest paths using at most max_hops hops in G ∪ H.

    Sequential simulation; span bounds are NOT DETERMINED.
    """
    distances: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    distances[source] = 0
    heap: list[tuple[float, int, object]] = [(0, 0, source)]
    out = graph.out_edges
    # Index hopset by source vertex for O(1) lookup per hop instead of O(|H|).
    hopset_index: dict[object, dict[object, float]] = {}
    for (a, b), weight in hopset_edges.items():
        hopset_index.setdefault(a, {})[b] = weight

    while heap:
        d, h, u = heapq.heappop(heap)
        if h > max_hops or d > distances[u]:
            continue
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            nh = h + 1
            if nh <= max_hops and nd < distances[v]:
                distances[v] = nd
                heapq.heappush(heap, (nd, nh, v))
        for b, weight in hopset_index.get(u, {}).items():
            nd = d + weight
            nh = h + 1
            if nh <= max_hops and nd < distances.get(b, float("inf")):
                distances[b] = nd
                heapq.heappush(heap, (nd, nh, b))

    return {v: d for v, d in distances.items() if d < float("inf")}


def shortest_path_tree(
    graph: WeightedDigraph, source: object
) -> dict[object, object | None]:
    """Compute a shortest path tree from source using Dijkstra.

    Returns a parent map where parent[v] is the predecessor of v, or None
    for the source itself.
    """
    distances: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    parent: dict[object, object | None] = dict.fromkeys(graph.vertices())
    distances[source] = 0
    heap: list[tuple[float, object]] = [(0, source)]
    visited: set[object] = set()
    out = graph.out_edges

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, weight in out.get(u, {}).items():
            nd = d + weight
            if nd < distances[v]:
                distances[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, v))
    return parent


def shortest_path(graph: WeightedDigraph, source: object, target: object) -> float:
    """Return the shortest distance from source to target.

    Returns ``float("inf")`` if target is unreachable from source.
    Equivalent to ``dijkstra(graph, source).get(target, float("inf"))``
    but avoids the full SSSP when only one target is needed.
    """
    distances = dijkstra(graph, source)
    return distances.get(target, float("inf"))
