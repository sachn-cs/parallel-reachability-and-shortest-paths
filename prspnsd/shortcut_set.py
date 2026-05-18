"""Shortcut set construction algorithms.

Implements the JLS shortcut set (Jambulapati, Liu, Sidford [JLS19]) and
our main contribution: JLS with TC-Pruning (Section 4).

Key references:
- Section 4.1: The JLS Shortcut Set
- Section 4.2: Bounding the Diameter Achieved From Using TC-Pruning on JLS
"""

import math
import random
from typing import Optional

from prspnsd.graph import Digraph
from prspnsd.reachability import compute_r_minus, compute_r_plus
from prspnsd.transitive_closure import transitive_closure_on_subset


def _partition_by_labels(
    vertices: set[object], labels: dict[object, set[str]]
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality.

    Corresponds to Step 3 of JLS (Section 4.1).
    """
    groups: dict[frozenset, set[object]] = {}
    for v in vertices:
        key = frozenset(labels.get(v, set()))
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


def _sample_pivots(
    vertices: set[object],
    prob: float,
    rng: random.Random,
) -> list[object]:
    """Sample each vertex independently with probability prob."""
    return [v for v in vertices if rng.random() < prob]


def jls_shortcut_set(
    graph: Digraph,
    k: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
) -> set[tuple[object, object]]:
    """Construct the JLS shortcut set (Section 4.1, Proposition 4.1).

    This is the baseline algorithm from [JLS19] without any pruning.

    Args:
        graph: A DAG G = (V, E).
        k: Global parameter controlling sampling rate and recursion depth.
        max_level: Maximum recursion depth.
        n_global: Number of vertices in the base input graph.
        level: Current recursion level r.
        random_seed: Optional seed for reproducibility.

    Returns:
        A set of shortcut edges H ⊆ V × V.

    Raises:
        ValueError: If k <= 1 or max_level < 0.
    """
    if k <= 1:
        raise ValueError("k must be > 1")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    rng = random.Random(random_seed)
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return set()

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    prob = min(1.0, 100.0 * (k ** (level + 1)) * log_n / n_global)

    pivots = _sample_pivots(graph.vertices(), prob, rng)
    shortcuts: set[tuple[object, object]] = set()
    labels: dict[object, set[str]] = {v: set() for v in graph.vertices()}

    for p in pivots:
        r_minus = compute_r_minus(graph, p)
        r_plus = compute_r_plus(graph, p)

        for v in r_minus:
            if v != p:
                shortcuts.add((v, p))
            labels[v].add(f"{p} reaches me")
        for v in r_plus:
            if v != p:
                shortcuts.add((p, v))
            labels[v].add(f"I reach {p}")
        for v in r_minus:
            labels[v].add(f"{p}Anc")
        for v in r_plus:
            labels[v].add(f"{p}Des")

    parts = _partition_by_labels(graph.vertices(), labels)
    for part in parts:
        if len(part) > 1:
            sub = graph.induced_subgraph(part)
            sub_shortcuts = jls_shortcut_set(
                sub,
                k,
                max_level,
                n_global,
                level + 1,
                random_seed=rng.randint(0, 2**31 - 1)
                if random_seed is not None
                else None,
            )
            shortcuts |= sub_shortcuts

    return shortcuts


def jls_with_tc_pruning(
    graph: Digraph,
    k: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
) -> set[tuple[object, object]]:
    """Construct the JLS shortcut set with TC-Pruning (Section 4.2, Theorem 5).

    This is the main sequential construction from Theorem 2.

    Args:
        graph: A DAG G = (V, E).
        k: Global parameter.
        rho: Tradeoff parameter in [sqrt(n)].
        max_level: Maximum recursion depth.
        n_global: Number of vertices in the base input graph.
        level: Current recursion level r.
        random_seed: Optional seed for reproducibility.

    Returns:
        A set of shortcut edges H ⊆ V × V.
    """
    if k <= 1:
        raise ValueError("k must be > 1")
    if rho <= 0:
        raise ValueError("rho must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    rng = random.Random(random_seed)
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return set()

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    prob = min(1.0, 100.0 * (k ** (level + 1)) * log_n / n_global)

    pivots = _sample_pivots(graph.vertices(), prob, rng)
    shortcuts: set[tuple[object, object]] = set()
    labels: dict[object, set[str]] = {v: set() for v in graph.vertices()}

    tc_pruning_threshold = (k ** 2) * (log_n ** 2) * (rho ** 2)

    for p in pivots:
        r_minus = compute_r_minus(graph, p)
        r_plus = compute_r_plus(graph, p)
        r_ball = r_minus | r_plus

        for v in r_minus:
            if v != p:
                shortcuts.add((v, p))
            labels[v].add(f"{p} reaches me")
            labels[v].add(f"{p}Anc")
        for v in r_plus:
            if v != p:
                shortcuts.add((p, v))
            labels[v].add(f"I reach {p}")
            labels[v].add(f"{p}Des")

        if len(r_ball) <= tc_pruning_threshold:
            shortcuts |= transitive_closure_on_subset(graph, r_ball)

    parts = _partition_by_labels(graph.vertices(), labels)
    for part in parts:
        if len(part) > 1:
            sub = graph.induced_subgraph(part)
            sub_shortcuts = jls_with_tc_pruning(
                sub,
                k,
                rho,
                max_level,
                n_global,
                level + 1,
                random_seed=rng.randint(0, 2**31 - 1)
                if random_seed is not None
                else None,
            )
            shortcuts |= sub_shortcuts

    return shortcuts


def build_shortcut_set_for_reachability(
    graph: Digraph,
    omega: float = 3.0,
    random_seed: Optional[int] = None,
) -> tuple[set[tuple[object, object]], float]:
    """High-level wrapper to build a beta-shortcut set matching Theorem 2.

    Automatically selects parameters based on graph density and omega.

    Args:
        graph: Input digraph (may contain cycles; SCCs are handled).
        omega: Fast matrix multiplication exponent.
        random_seed: Optional seed for reproducibility.

    Returns:
        (shortcut_set, beta) where beta is the target hopbound.
    """
    n = graph.num_vertices()
    m = graph.num_edges()

    if n == 0:
        return set(), 0.0

    from prspnsd.reachability import strongly_connected_components

    sccs = strongly_connected_components(graph)

    dag = Digraph()
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        dag.add_vertex(idx)
        for v in scc:
            scc_map[v] = idx

    for u, v in graph.edges():
        if scc_map[u] != scc_map[v]:
            dag.add_edge(scc_map[u], scc_map[v])

    beta = (n ** omega / m) ** (1.0 / (2.0 * omega - 2.0)) if m > 0 else float("inf")

    k = max(2.0, math.log2(n))
    rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
    rho = min(rho, math.sqrt(n))
    max_level = max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1

    dag_shortcuts = jls_with_tc_pruning(
        dag, k, rho, max_level, dag.num_vertices(), level=0, random_seed=random_seed
    )

    shortcuts: set[tuple[object, object]] = set()

    for scc in sccs:
        scc_list = list(scc)
        for i in range(len(scc_list)):
            for j in range(len(scc_list)):
                if i != j:
                    shortcuts.add((scc_list[i], scc_list[j]))

    for u_idx, v_idx in dag_shortcuts:
        u_rep = list(sccs[u_idx])[0]
        v_rep = list(sccs[v_idx])[0]
        shortcuts.add((u_rep, v_rep))

    return shortcuts, beta
