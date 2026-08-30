"""Top-level wrapper for the JLS shortcut-set construction.

Composes SCC condensation, intra-SCC reachability, CSR build,
parallel executor, parameter selection, and the recursion body.
"""

from __future__ import annotations

import math
import random
from typing import Any

from reachq.core.algorithm.parallel import ParallelExecutor
from reachq.core.algorithm.recursion import jls_recursive
from reachq.core.algorithm.scc_lift import (
    contract_sccs_for_reachability,
    intra_scc_shortcuts,
)
from reachq.core.algorithm.state import AlgorithmState
from reachq.core.config import RefinementConfig
from reachq.core.csr import build_csr_pair
from reachq.core.graph import Digraph
from reachq.core.prune import compute_tc_pruning_threshold
from reachq.core.trace import trace


def density_aware_constant(rho: float, k: float) -> float:
    """Sampling constant C chosen by graph density."""
    if rho <= 0 or k <= 1:
        return 10.0
    scale = min(1.0, max(0.1, rho / max(1.0, k)))
    return 10.0 * scale


def build_shortcut_set_for_reachability(
    graph: Digraph,
    omega: float = 3.0,
    random_seed: int | None = None,
    flags: dict[str, bool] | None = None,
    parallel_workers: int = 1,
) -> tuple[set[tuple[object, object]], float]:
    """Construct a beta-shortcut set matching Theorem 2.

    Args:
        graph: Input digraph (cycles handled by SCC condensation).
        omega: Fast matrix multiplication exponent.
        random_seed: Optional seed for reproducibility.
        flags: Optional dict of algorithmic refinement toggles.
        parallel_workers: When >1 and ``flags.parallel`` is True,
            the per-pivot BFS dispatches across a process pool.

    Returns:
        ``(shortcuts, beta)`` where ``beta`` is the target hopbound.
    """
    with trace("build_shortcut_set", n=graph.num_vertices(), m=graph.num_edges()):
        f = RefinementConfig.from_dict(flags) if flags is not None else RefinementConfig()
        n = graph.num_vertices()
        m = graph.num_edges()

        if n == 0:
            return set(), 0.0

        sccs, scc_map, representatives = contract_sccs_for_reachability(graph)
        trivial = (
            f.skip_condense and all(len(scc) == 1 for scc in sccs)
        ) or n == len(sccs)
        if trivial:
            dag = graph
        else:
            dag = Digraph()
            for idx in range(len(sccs)):
                dag.add_vertex(idx)
            for u, v in graph.edges():
                if scc_map[u] != scc_map[v]:
                    dag.add_edge(scc_map[u], scc_map[v])

        beta = (
            (n**omega / m) ** (1.0 / (2.0 * omega - 2.0))
            if m > 0
            else float("inf")
        )

        k = max(2.0, math.log2(n))
        rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
        rho = min(rho, math.sqrt(n))
        max_level = (
            max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1
        )

        if f.adaptive_sampling:
            sampling_constant = density_aware_constant(rho, k)
        else:
            sampling_constant = 10.0

        csr_data = build_csr_pair(dag) if dag.num_vertices() >= 500 else None
        if csr_data is not None:
            (
                indptr_fwd,
                indices_fwd,
                indptr_rev,
                indices_rev,
                csr_n,
                idx_to_vertex,
            ) = csr_data
            state = AlgorithmState(
                indptr_fwd=indptr_fwd,
                indices_fwd=indices_fwd,
                indptr_rev=indptr_rev,
                indices_rev=indices_rev,
                idx_to_vertex=tuple(idx_to_vertex),
                n=csr_n,
                max_hops=None,
            )
        else:
            state = AlgorithmState(
                indptr_fwd=None,  # type: ignore[arg-type]
                indices_fwd=None,  # type: ignore[arg-type]
                indptr_rev=None,  # type: ignore[arg-type]
                indices_rev=None,  # type: ignore[arg-type]
                idx_to_vertex=(),
                n=dag.num_vertices(),
                max_hops=None,
            )

        log_n = math.log2(n) if n > 1 else 0.0
        if f.enable_tc_pruning:
            tc_threshold = compute_tc_pruning_threshold(
                k, log_n, rho, n, omega
            )
        else:
            tc_threshold = None

        executor_mode = "processes" if (f.parallel and parallel_workers > 1) else "sequential"
        executor = ParallelExecutor(mode=executor_mode, n_workers=parallel_workers)

        rng = random.Random(random_seed)

        dag_shortcuts = jls_recursive(
            dag,
            state,
            k,
            rho,
            max_level,
            n,
            level=0,
            rng=rng,
            flags=f,
            sampling_constant=sampling_constant,
            executor=executor,
            tc_threshold=tc_threshold,
        )

        shortcuts: set[tuple[object, object]] = set()

        if not trivial:
            intra = intra_scc_shortcuts(graph, sccs)
            shortcuts |= intra

        for u_idx, v_idx in dag_shortcuts:
            if trivial:
                shortcuts.add((u_idx, v_idx))
            else:
                shortcuts.add(
                    (representatives[u_idx], representatives[v_idx])
                )

        return shortcuts, beta


def jls_with_tc_pruning(
    graph: Digraph,
    k: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: int | None = None,
    flags=None,
    *,
    parallel_workers: int = 1,
    sampling_constant: float | None = None,
) -> set[tuple[object, object]]:
    """Direct JLS-with-TC entry point kept for advanced callers."""
    f = RefinementConfig.from_dict(flags) if flags is not None else RefinementConfig()
    if k <= 1:
        raise ValueError("k must be > 1")
    if rho <= 0:
        raise ValueError("rho must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    if sampling_constant is None:
        sampling_constant = 10.0

    csr_data = build_csr_pair(graph) if graph.num_vertices() >= 500 else None
    if csr_data is not None:
        (
            indptr_fwd,
            indices_fwd,
            indptr_rev,
            indices_rev,
            csr_n,
            idx_to_vertex,
        ) = csr_data
        state = AlgorithmState(
            indptr_fwd=indptr_fwd,
            indices_fwd=indices_fwd,
            indptr_rev=indptr_rev,
            indices_rev=indices_rev,
            idx_to_vertex=tuple(idx_to_vertex),
            n=csr_n,
            max_hops=None,
        )
    else:
        state = AlgorithmState(
            indptr_fwd=None,  # type: ignore[arg-type]
            indices_fwd=None,  # type: ignore[arg-type]
            indptr_rev=None,  # type: ignore[arg-type]
            indices_rev=None,  # type: ignore[arg-type]
            idx_to_vertex=(),
            n=graph.num_vertices(),
            max_hops=None,
        )

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    if f.enable_tc_pruning:
        tc_threshold = compute_tc_pruning_threshold(
            k, log_n, rho, graph.num_vertices(), omega=2.5
        )
    else:
        tc_threshold = None

    executor = ParallelExecutor(
        mode="processes" if (f.parallel and parallel_workers > 1) else "sequential",
        n_workers=parallel_workers,
    )
    rng = random.Random(random_seed)
    return jls_recursive(
        graph,
        state,
        k,
        rho,
        max_level,
        n_global,
        level,
        rng,
        f,
        sampling_constant,
        executor=executor,
        tc_threshold=tc_threshold,
    )
