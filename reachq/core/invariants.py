"""Theorem-oriented validation helpers and invariant checkers.

These functions verify structural and algorithmic properties required by
the paper's theorems. They are intended for testing and debugging, not
for production hot paths.
"""

from __future__ import annotations

import math

from reachq.core.graph import Digraph, WeightedDigraph
from reachq.core.reachability import (
    bfs_reachability,
    parallel_bfs,
    strongly_connected_components,
)
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound


def assert_reachability_preserved(
    graph: Digraph,
    shortcuts: set[tuple[object, object]],
    msg: str | None = None,
) -> None:
    """Verify that shortcuts do not alter reachability.

    For every vertex v, R^+(G, v) must equal R^+(G ∪ H, v).
    This corresponds to the definition of a shortcut set (Section 2).
    """
    for v in graph.vertices():
        original = bfs_reachability(graph, v)
        augmented = parallel_bfs(graph, v, shortcuts)
        if original != augmented:
            missing = original - augmented
            extra = augmented - original
            raise AssertionError(
                f"Reachability mismatch from {v}: missing={missing}, extra={extra}. {msg or ''}"
            )


def assert_hopbound(
    graph: Digraph,
    source: object,
    shortcuts: set[tuple[object, object]],
    beta: float,
    msg: str | None = None,
) -> int:
    """Compute the actual hop count from source and assert it ≤ beta.

    Returns the observed hop count. Raises AssertionError if the bound
    is violated.
    """
    from collections import deque

    dist: dict[object, int] = {v: float("inf") for v in graph.vertices()}  # type: ignore[misc]
    dist[source] = 0
    q: deque = deque([source])
    out = graph.out_edges
    shortcut_list = list(shortcuts)

    while q:
        u = q.popleft()
        for v in out.get(u, set()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
        for a, b in shortcut_list:
            if a == u and dist[b] == float("inf"):
                dist[b] = dist[u] + 1
                q.append(b)

    reachable = {v for v, d in dist.items() if d < float("inf")}
    max_hops = max((dist[v] for v in reachable), default=0)
    if max_hops > beta:
        raise AssertionError(
            f"Hopbound violated: max_hops={max_hops} > beta={beta}. {msg or ''}"
        )
    return max_hops


def assert_scc_shortcuts_form_cliques(
    graph: Digraph,
    shortcuts: set[tuple[object, object]],
    msg: str | None = None,
) -> None:
    """Verify that every SCC is a clique in G + shortcuts.

    Theorem 2 requires that within each SCC, every vertex can reach
    every other via G ∪ shortcuts. We verify this by checking that
    for each pair (u, v) in the same SCC, the augmented graph G +
    shortcuts makes u and v mutually reachable.

    This is equivalent to requiring shortcuts for every (u, v) pair
    in the SCC that is NOT already a direct G-edge -- because within
    an SCC, G itself gives reachability, so the only missing reachability
    is pairs where G has no edge in either direction. (If G has u→v
    directly, no shortcut is needed.)
    """
    from reachq.core.reachability import parallel_bfs

    sccs = strongly_connected_components(graph)
    for scc in sccs:
        if len(scc) <= 1:
            continue
        scc_list = list(scc)
        # For each u in SCC, check that parallel_bfs(g, u, shortcuts)
        # reaches every other v in the SCC. This is the "augmented
        # reachability" check, NOT the direct-edge check.
        for u in scc_list:
            reach = parallel_bfs(graph, u, shortcuts)
            for v in scc_list:
                if v == u:
                    continue
                if v not in reach:
                    raise AssertionError(
                        f"u={u} cannot reach v={v} in same SCC via G+H. " f"{msg or ''}"
                    )


def assert_partition_correctness(
    graph: Digraph,
    parts: list[set[object]],
    msg: str | None = None,
) -> None:
    """Verify that parts form a partition of V(G).

    Checks:
    1. Union of parts equals V(G).
    2. Parts are pairwise disjoint.
    """
    vertices = graph.vertices()
    union: set[object] = set()
    for part in parts:
        if not part.issubset(vertices):
            extra = part - vertices
            raise AssertionError(
                f"Partition contains extraneous vertices: {extra}. {msg or ''}"
            )
        intersection = union & part
        if intersection:
            raise AssertionError(
                f"Partition parts overlap on {intersection}. {msg or ''}"
            )
        union |= part

    if union != vertices:
        missing = vertices - union
        raise AssertionError(f"Partition missing vertices: {missing}. {msg or ''}")


def assert_distance_approximation(
    graph: WeightedDigraph,
    hopset: dict[tuple[object, object], float],
    source: object,
    epsilon: float,
    max_hops: int,
    msg: str | None = None,
) -> dict[object, float]:
    """Verify that hopset distances are within (1 + epsilon) of true distances.

    Computes exact distances with Dijkstra and approximate distances with
    shortest_path_hopbound, then asserts the (beta, epsilon)-hopset guarantee.

    Returns a dict mapping each vertex to the observed approximation ratio.
    """
    original = dijkstra(graph, source)
    approx = shortest_path_hopbound(graph, hopset, source, max_hops)
    ratios: dict[object, float] = {}
    for v in graph.vertices():
        orig_d = original.get(v, float("inf"))
        if orig_d == float("inf"):
            continue
        hop_d = approx.get(v, float("inf"))
        if hop_d == float("inf"):
            raise AssertionError(
                f"Vertex {v} reachable in G but not in G ∪ H within {max_hops} hops. {msg or ''}"
            )
        if hop_d > (1 + epsilon) * orig_d + 1e-9:
            raise AssertionError(
                f"Distance approximation violated for {v}: "
                f"hop_d={hop_d} > (1+eps)*orig={(1 + epsilon) * orig_d}. "
                f"{msg or ''}"
            )
        ratio = hop_d / orig_d if orig_d > 0 else 0.0
        ratios[v] = ratio
    return ratios


def assert_shortcut_set_size_bound(
    graph: Digraph,
    shortcuts: set[tuple[object, object]],
    rho: float,
    msg: str | None = None,
) -> None:
    """Verify that |H| is consistent with the O~(n * rho^2) bound.

    This is a coarse sanity check, not a proof.
    """
    n = graph.num_vertices()
    log_n = max(1.0, math.log2(n + 2))
    bound = log_n * n * (rho**2)
    if len(shortcuts) > bound:
        raise AssertionError(
            f"Shortcut set size {len(shortcuts)} exceeds coarse bound "
            f"{bound:.1f} (n={n}, rho={rho}). {msg or ''}"
        )


def assert_hopset_size_bound(
    graph: WeightedDigraph,
    hopset: dict[tuple[object, object], float],
    epsilon: float,
    rho: float,
    msg: str | None = None,
) -> None:
    """Verify that |H| is consistent with the O~(n/epsilon^2 + n*rho^2) bound.

    Coarse sanity check only.
    """
    n = graph.num_vertices()
    log_n = max(1.0, math.log2(n + 2))
    bound = log_n * (n / (epsilon**2) + n * (rho**2))
    if len(hopset) > bound:
        raise AssertionError(
            f"Hopset size {len(hopset)} exceeds coarse bound "
            f"{bound:.1f} (n={n}, eps={epsilon}, rho={rho}). {msg or ''}"
        )


def check_equivalence_classes(
    labels: dict[object, set[str]],
    parts: list[set[object]],
    msg: str | None = None,
) -> None:
    """Verify that label-based partitioning matches the equivalence classes.

    Every part should consist of vertices with identical label sets.
    """
    label_to_part: dict[frozenset, set[object]] = {}
    for part in parts:
        for v in part:
            key = frozenset(labels.get(v, set()))
            if key in label_to_part:
                if label_to_part[key] != part:
                    raise AssertionError(
                        f"Vertex {v} with labels {key} appears in two different parts. {msg or ''}"
                    )
            else:
                label_to_part[key] = part

    for part in parts:
        if not part:
            continue
        first = next(iter(part))
        first_labels = frozenset(labels.get(first, set()))
        for v in part:
            v_labels = frozenset(labels.get(v, set()))
            if v_labels != first_labels:
                raise AssertionError(
                    f"Part contains vertices with different labels: "
                    f"{first} has {first_labels}, {v} has {v_labels}. "
                    f"{msg or ''}"
                )
