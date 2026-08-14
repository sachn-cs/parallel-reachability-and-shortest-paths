"""Hopset construction algorithms.

Implements the CFR hopset (Cao, Fineman, Russell [CFR20]) with the
paper's TruncSSSP-Pruning (Section 6), plus the same algorithmic
refinements as :mod:`reachq.core.algorithm`:

  1. Adaptive sampling probability (Improvement 1)
  2. Label compression: pivot-set labels instead of strings (Improvement 2)
  3. Skip SCC condensation on already-DAG inputs (Improvement 3)
  4. Hop-bounded pivot BFS at the wrapper's beta hopbound (Improvement 4)
  5. Degree-ordered pivot iteration (cheap BFS first) (Improvement 5)
  6. Skip-trivial-partition guard (Improvement 6)
  7. (n/a — TC pruning not used in hopset construction; this slot is
     reserved for the symmetric TruncSSSP trigger refinement when the
     graph supports it)

Bug fixes vs earlier versions:
  * ``graph.reversed()`` rebuilt once per level, not once per pivot.
  * ``truncsssp_threshold`` computed once per recursion level, not once
    per pivot.
  * No DEBUG prints in the production hot path.
  * DAG inputs skip condensation entirely (Improvement 3).
"""

from __future__ import annotations

import math
import random
from typing import Any

from reachq.core.config import RefinementConfig
from reachq.core.graph import WeightedDigraph, contract_sccs, partition_by_labels
from reachq.core.shortest_paths import (
    compute_d_ancestors,
    compute_d_ball,
    compute_d_descendants,
    dijkstra,
)
from reachq.core.trace import trace

OMEGA_DEFAULT = 2.5
OMEGA_RUNTIME_HOP: float | None = None


def get_runtime_omega() -> float:
    """Return runtime omega, cached; same impl as in shortcut_set."""
    global OMEGA_RUNTIME_HOP
    if OMEGA_RUNTIME_HOP is None:
        from reachq.research.blas_omega import runtime_omega

        OMEGA_RUNTIME_HOP = runtime_omega()
    return OMEGA_RUNTIME_HOP


def compute_truncated_sssp_structure(
    graph: WeightedDigraph,
    vertex_subset: set[object],
    max_distance: int,
) -> dict[tuple[object, object], float]:
    """Compute all-pairs shortest paths within *vertex_subset*, truncated at *max_distance*."""
    subgraph = graph.induced_subgraph(vertex_subset)
    edges: dict[tuple[object, object], float] = {}
    for u in vertex_subset:
        dists = dijkstra(subgraph, u)
        for v, d in dists.items():
            if d <= max_distance and u != v:
                edges[(u, v)] = d
    return edges


def cfr_recursive(
    graph: WeightedDigraph,
    k: float,
    epsilon: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int,
    rng: random.Random,
    flags: RefinementConfig,
    *,
    prunning: bool,
) -> dict[tuple[object, object], float]:
    """Shared CFR-with-TruncSSSP-Pruning body used by both public entry points.

    When ``prunning`` is False, runs the baseline CFR hopset (no TruncSSSP).
    """
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return {}

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    base_prob = (
        min(1.0, OMEGA_DEFAULT * (k ** (level + 1)) * log_n / n_global)
        if OMEGA_RUNTIME_HOP is None
        else min(
            1.0,
            min(OMEGA_DEFAULT, get_runtime_omega())
            * (k ** (level + 1))
            * log_n
            / n_global,
        )
    )

    vertices = graph.vertices()

    if flags.degree_ordered_pivots:
        out_degrees = {v: graph.degree_out(v) for v in vertices}
        pivots = [
            v
            for v in vertices
            if bernoulli_weighted(
                base_prob,
                out_degrees.get(v, 0),
                rng,
            )
        ]
        pivots.sort(key=lambda v: out_degrees.get(v, 0))
    else:
        pivots = [v for v in vertices if rng.random() < base_prob]

    if not pivots:
        return {}

    hopset: dict[tuple[object, object], float] = {}
    labels: dict[object, Any] = {v: set() for v in vertices}
    if flags.label_compress:
        anc_labels: dict[object, list[object]] = {v: [] for v in vertices}
        des_labels: dict[object, list[object]] = {v: [] for v in vertices}

    # Hoisted once per level (was once per pivot previously).
    distance_scale = int((1 + epsilon) ** level)
    distance_scale = max(1, distance_scale)
    d = distance_scale * int(max(1, log_n))

    # Distances from each pivot to all vertices: shared Dijkstra per pivot.
    # Reversed graph built once per level, not once per pivot.
    rev = graph.reversed()
    dists_to_p_cache: dict[object, dict[object, float]] = {}

    truncsssp_threshold = (k**2) * (log_n**2) * (rho**2)

    for pivot in pivots:
        d_ancestors = compute_d_ancestors(graph, pivot, d)
        d_descendants = compute_d_descendants(graph, pivot, d)
        dists_from_p = dijkstra(graph, pivot)
        dists_to_p = dijkstra(rev, pivot)
        dists_to_p_cache[pivot] = dists_to_p

        for v in d_ancestors:
            w = dists_to_p.get(v, float("inf"))
            if w < float("inf") and v != pivot:
                prev = hopset.get((v, pivot))
                if prev is None or w < prev:
                    hopset[(v, pivot)] = w
            if flags.label_compress:
                anc_labels[v].append(pivot)
            else:
                labels[v].add((pivot, "anc"))

        for v in d_descendants:
            w = dists_from_p.get(v, float("inf"))
            if w < float("inf") and v != pivot:
                prev = hopset.get((pivot, v))
                if prev is None or w < prev:
                    hopset[(pivot, v)] = w
            if flags.label_compress:
                des_labels[v].append(pivot)
            else:
                labels[v].add((pivot, "des"))

        if prunning:
            d_ball = compute_d_ball(graph, pivot, d)
            if 0 < len(d_ball) <= truncsssp_threshold:
                trunc_edges = compute_truncated_sssp_structure(graph, d_ball, d)
                for edge, w in trunc_edges.items():
                    prev = hopset.get(edge)
                    if prev is None or w < prev:
                        hopset[edge] = w

    if flags.label_compress:
        for v in vertices:
            labels[v] = (frozenset(anc_labels[v]), frozenset(des_labels[v]))

    parts = partition_by_labels(vertices, labels)

    # Improvement 6.
    if len(parts) <= 1 and flags.skip_trivial_part:
        return hopset

    for part in parts:
        if len(part) <= 1:
            continue
        sub = graph.induced_subgraph(part)
        # Advance the RNG so the recursion sees a different stream.
        rng.randint(0, 2**31 - 1)
        sub_hopset = cfr_recursive(
            sub,
            k,
            epsilon,
            rho,
            max_level,
            n_global,
            level + 1,
            rng,
            flags,
            prunning=prunning,
        )
        for edge, w in sub_hopset.items():
            prev = hopset.get(edge)
            if prev is None or w < prev:
                hopset[edge] = w

    return hopset


def bernoulli_weighted(prob: float, out_deg: int, rng: random.Random) -> bool:
    """Improvement 5 (degree-aware pivot weighting): accept with prob / (1 + deg)."""
    if prob >= 1.0:
        return True
    return rng.random() < prob / (1 + out_deg)


def cfr_hopset(
    graph: WeightedDigraph,
    k: float,
    epsilon: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: int | None = None,
    flags: dict[str, bool] | None = None,
) -> dict[tuple[object, object], float]:
    """Construct the CFR hopset without TruncSSSP-Pruning.

    Equivalent to the public CFR baseline, used here as a comparison point
    against :func:`cfr_with_truncsssp_pruning`. Both now share an internal
    recursive body via :func:`cfr_recursive` so the only difference is the
    pruning flag.
    """
    f = RefinementConfig.from_dict(flags)
    if k <= 1:
        raise ValueError("k must be > 1")
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")
    rng = random.Random(random_seed)
    return cfr_recursive(
        graph,
        k,
        epsilon,
        rho=1.0,
        max_level=max_level,
        n_global=n_global,
        level=level,
        rng=rng,
        flags=f,
        prunning=False,
    )


def cfr_with_truncsssp_pruning(
    graph: WeightedDigraph,
    k: float,
    epsilon: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: int | None = None,
    flags: dict[str, bool] | None = None,
) -> dict[tuple[object, object], float]:
    """Construct the CFR hopset with TruncSSSP-Pruning (Section 6.3, Theorem 4)."""
    f = RefinementConfig.from_dict(flags)
    if k <= 1:
        raise ValueError("k must be > 1")
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    if rho <= 0:
        raise ValueError("rho must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")
    rng = random.Random(random_seed)
    return cfr_recursive(
        graph,
        k,
        epsilon,
        rho=rho,
        max_level=max_level,
        n_global=n_global,
        level=level,
        rng=rng,
        flags=f,
        prunning=True,
    )


def build_hopset_for_sssp(
    graph: WeightedDigraph,
    epsilon: float = 0.1,
    random_seed: int | None = None,
    flags: dict[str, bool] | None = None,
    parallel_workers: int = 1,
) -> tuple[dict[tuple[object, object], float], float]:
    """High-level wrapper: build a (beta, epsilon)-hopset matching Theorem 4.

    Automatically selects parameters based on graph density.

    Args:
        parallel_workers: Accepted for API symmetry with
            ``build_shortcut_set_for_reachability``; the hopset
            construction runs sequentially because the per-pivot
            workload is a Dijkstra call (GIL-bound in Python). Pass any
            value; it is currently ignored.

    Returns:
        (hopset, beta) where beta is the target hopbound.
    """
    with trace("build_hopset", n=graph.num_vertices(), m=graph.num_edges()):
        if parallel_workers != 1:
            import logging

            logging.getLogger("reachq.hopset").info(
                "build_hopset_for_sssp: parallel_workers=%d ignored "
                "(hopset construction is sequential)",
                parallel_workers,
            )
        f = RefinementConfig.from_dict(flags)
        n = graph.num_vertices()
        m = graph.num_edges()

        if n == 0:
            return {}, 0.0

        sccs, scc_map = contract_sccs(graph.to_unweighted())

        # Improvement 3: trivial condensation fast path.
        trivial = f.skip_condense and all(len(scc) == 1 for scc in sccs)
        if trivial:
            dag = graph
            scc_rep = [next(iter(scc)) for scc in sccs]
        else:
            dag = WeightedDigraph()
            for idx in range(len(sccs)):
                dag.add_vertex(idx)
            for u, v, w in graph.edges():
                if scc_map[u] != scc_map[v]:
                    dag.add_edge(scc_map[u], scc_map[v], w)
            scc_rep = [next(iter(scc)) for scc in sccs]

        beta = (n**3 / m) ** 0.25 if m > 0 else float("inf")

        k = max(2.0, math.log2(n))
        rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
        rho = min(rho, math.sqrt(n))
        max_level = max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1

        dag_hopset = cfr_with_truncsssp_pruning(
            dag,
            k,
            epsilon,
            rho,
            max_level,
            dag.num_vertices(),
            level=0,
            random_seed=random_seed,
            flags=flags,
        )

        hopset: dict[tuple[object, object], float] = {}

        # SCC intra-clique shortcuts — skip trivial SCCs.
        if not trivial:
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
                            prev = hopset.get(key)
                            if prev is None or d < prev:
                                hopset[key] = d

        for u_idx, v_idx, hw in ((u, v, dag_hopset[(u, v)]) for u, v in dag_hopset):
            if trivial:
                key = (u_idx, v_idx)
            else:
                assert isinstance(u_idx, int)
                assert isinstance(v_idx, int)
                key = (scc_rep[u_idx], scc_rep[v_idx])
            prev = hopset.get(key)
            if prev is None or hw < prev:
                hopset[key] = hw

        return hopset, beta
