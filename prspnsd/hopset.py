"""Hopset construction algorithms.

Implements the CFR hopset (Cao, Fineman, Russell [CFR20]) and
our main contribution: CFR with TruncSSSP-Pruning (Section 6).

NOTE: The exact pseudocode for the CFR hopset with TruncSSSP-Pruning
is not fully present in the extracted paper text (Sections 6.1--6.3
were partially truncated). We reconstruct the algorithm from:
  1. The paper's statement that it "adapts the CFR hopset construction
     analogously" to the JLS shortcut set adaptation (Section 6).
  2. The high-level description in Section 3.2 (Summary of Our Main Result)
     and Section 6.3.
  3. The known structure of CFR hopsets from [CFR20].

ASSUMPTION: The precise pivot sampling probabilities, distance scales,
and TruncSSSP-Pruning thresholds for the hopset are reconstructed
from the analogy to the shortcut set. The structure follows the
paper's description but some constants may differ from the authors'
original implementation.
"""

import math
import random
from typing import Optional

from prspnsd.graph import WeightedDigraph
from prspnsd.shortest_paths import (
    compute_d_ancestors,
    compute_d_ball,
    compute_d_descendants,
    dijkstra,
)


def _partition_by_weighted_labels(
    vertices: set[object],
    labels: dict[object, set[str]],
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality."""
    groups: dict[frozenset, set[object]] = {}
    for v in vertices:
        key = frozenset(labels.get(v, set()))
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


def _compute_truncated_sssp_structure(
    graph: WeightedDigraph,
    vertex_subset: set[object],
    max_distance: int,
) -> dict[tuple[object, object], int]:
    """Compute all-pairs shortest paths within vertex_subset, truncated at max_distance.

    This is the TruncSSSP-Pruning analogue of TC(G[R(G, p)]):
    instead of the transitive closure (reachability), we compute
    truncated shortest paths (distances). The resulting edges
    form a hopset on the induced subgraph.

    Returns a dict mapping (u, v) to the shortest-path distance from u to v,
    including only pairs with finite distance <= max_distance.
    """
    subgraph = graph.induced_subgraph(vertex_subset)
    edges: dict[tuple[object, object], int] = {}
    for u in vertex_subset:
        dists = dijkstra(subgraph, u)
        for v, d in dists.items():
            if d <= max_distance and u != v:
                edges[(u, v)] = d
    return edges


def cfr_hopset(
    graph: WeightedDigraph,
    k: float,
    epsilon: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
) -> dict[tuple[object, object], int]:
    """Construct the CFR hopset (reconstructed from [CFR20], Section 6.1).

    This is the baseline hopset algorithm without TruncSSSP-Pruning.

    Args:
        graph: A weighted DAG G = (V, E, w).
        k: Global parameter controlling sampling rate.
        epsilon: Approximation factor for the hopset.
        max_level: Maximum recursion depth.
        n_global: Number of vertices in the base input graph.
        level: Current recursion level.
        random_seed: Optional seed for reproducibility.

    Returns:
        A dict mapping shortcut edges (u, v) to their weights.
    """
    if k <= 1:
        raise ValueError("k must be > 1")
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    rng = random.Random(random_seed)
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return {}

    distance_scale = int((1 + epsilon) ** level)
    distance_scale = max(1, distance_scale)

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    prob = min(1.0, 100.0 * (k ** (level + 1)) * log_n / n_global)

    pivots = [v for v in graph.vertices() if rng.random() < prob]

    hopset: dict[tuple[object, object], int] = {}
    labels: dict[object, set[str]] = {v: set() for v in graph.vertices()}

    for p in pivots:
        d = distance_scale * int(max(1, log_n))
        d_ancestors = compute_d_ancestors(graph, p, d)
        d_descendants = compute_d_descendants(graph, p, d)

        dists_from_p = dijkstra(graph, p)
        rev = graph.reversed()
        dists_to_p = dijkstra(rev, p)

        for v in d_ancestors:
            weight = dists_to_p.get(v, float("inf"))
            if weight < float("inf") and v != p:
                hopset[(v, p)] = weight
            labels[v].add(f"{p} d-reaches me")
            labels[v].add(f"{p}Anc_d")

        for v in d_descendants:
            weight = dists_from_p.get(v, float("inf"))
            if weight < float("inf") and v != p:
                hopset[(p, v)] = weight
            labels[v].add(f"I d-reach {p}")
            labels[v].add(f"{p}Des_d")

    parts = _partition_by_weighted_labels(graph.vertices(), labels)

    for part in parts:
        if len(part) > 1:
            sub = graph.induced_subgraph(part)
            sub_hopset = cfr_hopset(
                sub,
                k,
                epsilon,
                max_level,
                n_global,
                level + 1,
                random_seed=rng.randint(0, 2**31 - 1)
                if random_seed is not None
                else None,
            )
            for edge, weight in sub_hopset.items():
                hopset[edge] = min(hopset.get(edge, float("inf")), weight)

    return hopset


def cfr_with_truncsssp_pruning(
    graph: WeightedDigraph,
    k: float,
    epsilon: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
) -> dict[tuple[object, object], int]:
    """Construct the CFR hopset with TruncSSSP-Pruning (Section 6.3, Theorem 4).

    This is the main sequential hopset construction.

    Args:
        graph: A weighted DAG G = (V, E, w).
        k: Global parameter.
        epsilon: Approximation factor.
        rho: Tradeoff parameter in [sqrt(n)].
        max_level: Maximum recursion depth.
        n_global: Number of vertices in the base input graph.
        level: Current recursion level.
        random_seed: Optional seed.

    Returns:
        A dict mapping hopset edges (u, v) to their weights.
    """
    if k <= 1:
        raise ValueError("k must be > 1")
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    if rho <= 0:
        raise ValueError("rho must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    rng = random.Random(random_seed)
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return {}

    distance_scale = int((1 + epsilon) ** level)
    distance_scale = max(1, distance_scale)
    log_n = math.log2(n_global) if n_global > 1 else 0.0
    prob = min(1.0, 100.0 * (k ** (level + 1)) * log_n / n_global)

    pivots = [v for v in graph.vertices() if rng.random() < prob]

    hopset: dict[tuple[object, object], int] = {}
    labels: dict[object, set[str]] = {v: set() for v in graph.vertices()}

    truncsssp_threshold = (k ** 2) * (log_n ** 2) * (rho ** 2)

    for p in pivots:
        d = distance_scale * int(max(1, log_n))
        d_ball = compute_d_ball(graph, p, d)

        d_ancestors = compute_d_ancestors(graph, p, d)
        d_descendants = compute_d_descendants(graph, p, d)

        dists_from_p = dijkstra(graph, p)
        rev = graph.reversed()
        dists_to_p = dijkstra(rev, p)

        for v in d_ancestors:
            weight = dists_to_p.get(v, float("inf"))
            if weight < float("inf") and v != p:
                hopset[(v, p)] = weight
            labels[v].add(f"{p} d-reaches me")
            labels[v].add(f"{p}Anc_d")

        for v in d_descendants:
            weight = dists_from_p.get(v, float("inf"))
            if weight < float("inf") and v != p:
                hopset[(p, v)] = weight
            labels[v].add(f"I d-reach {p}")
            labels[v].add(f"{p}Des_d")

        if len(d_ball) <= truncsssp_threshold:
            trunc_edges = _compute_truncated_sssp_structure(graph, d_ball, d)
            for edge, weight in trunc_edges.items():
                hopset[edge] = min(hopset.get(edge, float("inf")), weight)

    parts = _partition_by_weighted_labels(graph.vertices(), labels)

    for part in parts:
        if len(part) > 1:
            sub = graph.induced_subgraph(part)
            sub_hopset = cfr_with_truncsssp_pruning(
                sub,
                k,
                epsilon,
                rho,
                max_level,
                n_global,
                level + 1,
                random_seed=rng.randint(0, 2**31 - 1)
                if random_seed is not None
                else None,
            )
            for edge, weight in sub_hopset.items():
                hopset[edge] = min(hopset.get(edge, float("inf")), weight)

    return hopset


def build_hopset_for_sssp(
    graph: WeightedDigraph,
    epsilon: float = 0.1,
    random_seed: Optional[int] = None,
) -> tuple[dict[tuple[object, object], int], float]:
    """High-level wrapper to build a (beta, epsilon)-hopset matching Theorem 4.

    Automatically selects parameters based on graph density.

    Args:
        graph: Input weighted digraph.
        epsilon: Approximation factor.
        random_seed: Optional seed for reproducibility.

    Returns:
        (hopset, beta) where beta is the target hopbound.
    """
    n = graph.num_vertices()
    m = graph.num_edges()

    if n == 0:
        return {}, 0.0

    from prspnsd.reachability import strongly_connected_components

    sccs = strongly_connected_components(graph.to_unweighted())

    dag = WeightedDigraph()
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        dag.add_vertex(idx)
        for v in scc:
            scc_map[v] = idx

    for u, v, w in graph.edges():
        if scc_map[u] != scc_map[v]:
            dag.add_edge(scc_map[u], scc_map[v], w)

    beta = (n ** 3 / m) ** 0.25 if m > 0 else float("inf")

    k = max(2.0, math.log2(n))
    rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
    rho = min(rho, math.sqrt(n))
    max_level = max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1

    dag_hopset = cfr_with_truncsssp_pruning(
        dag, k, epsilon, rho, max_level, dag.num_vertices(), level=0,
        random_seed=random_seed,
    )

    hopset: dict[tuple[object, object], int] = {}

    for scc in sccs:
        scc_list = list(scc)
        if len(scc_list) <= 1:
            continue
        sub = graph.induced_subgraph(scc)
        for u in scc_list:
            dists = dijkstra(sub, u)
            for v, d in dists.items():
                if u != v:
                    key = (u, v)
                    hopset[key] = min(hopset.get(key, float("inf")), d)

    for u_idx, v_idx in dag_hopset:
        u_rep = list(sccs[u_idx])[0]
        v_rep = list(sccs[v_idx])[0]
        weight = dag_hopset[(u_idx, v_idx)]
        if (u_rep, v_rep) in hopset:
            hopset[(u_rep, v_rep)] = min(hopset[(u_rep, v_rep)], weight)
        else:
            hopset[(u_rep, v_rep)] = weight

    return hopset, beta
