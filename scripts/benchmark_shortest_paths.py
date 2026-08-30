"""Hopset oracle benchmark.

Validates the returned ``beta`` against actual hop-counts in
``G ∪ H`` from every source. Detects both overestimates
(hopbound exceeded) and underestimates (hopset distance >
``(1 + epsilon) * exact`` distance).

Reports environment metadata so results are reproducible across
machines.
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import sys
import time
from collections.abc import Sequence
from typing import Any

from reachq.config import configure_logging, get_logger
from reachq.generators import (
    dense_graph,
    random_dag,
    weighted_dense_graph,
    weighted_random_dag,
    graph_with_sccs,
    path_graph,
)
from reachq.graph import Digraph, WeightedDigraph
from reachq.hopset import build_hopset_for_sssp
from reachq.reachability import bfs_reachability, parallel_bfs
from reachq.shortest_paths import dijkstra, shortest_path_hopbound


configure_logging()
log = get_logger("reachq.benchmark_shortest_paths")


def _hop_count_bfs_indexed(
    graph: Digraph,
    source: object,
    shortcuts: set[tuple[object, object]],
) -> dict[object, int]:
    """BFS-with-shortcuts returning hop counts."""
    from collections import deque

    shortcut_index: dict[object, list[object]] = {}
    for a, b in shortcuts:
        shortcut_index.setdefault(a, []).append(b)

    dist: dict[object, int] = {v: 1 << 62 for v in graph.vertices()}
    dist[source] = 0
    q: deque = deque([source])
    while q:
        u = q.popleft()
        for v in graph.out_edges.get(u, ()):
            if dist[v] == 1 << 62:
                dist[v] = dist[u] + 1
                q.append(v)
        for b in shortcut_index.get(u, ()):
            if b in dist and dist[b] == 1 << 62:
                dist[b] = dist[u] + 1
                q.append(b)
    return dist


def _environment_metadata() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", "default"),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "unset"),
        "numpy": __import__("numpy").__version__,
        "scipy": __import__("scipy").__version__,
    }


def _build_graphs(n_list: Sequence[int], seed: int) -> list[tuple[str, Any]]:
    families: list[tuple[str, Any]] = []
    for n in n_list:
        for family_name, factory in [
            ("random_dag", lambda n, seed: random_dag(n=n, edge_probability=0.1, random_seed=seed)),
            ("weighted_dense", lambda n, seed: weighted_dense_graph(n, int(0.3 * n * n), weight_range=(1, 5), random_seed=seed)),
            ("weighted_random_dag", lambda n, seed: weighted_random_dag(n=n, edge_probability=0.1, random_seed=seed)),
            ("graph_with_sccs", lambda n, seed: graph_with_sccs(scc_sizes=[max(1, n // 4)] * 4, inter_edge_probability=0.1, random_seed=seed)),
            ("path", lambda n, seed: path_graph(n)),
        ]:
            families.append((f"{family_name}_n{n}", factory(n, seed)))
    return families


def _validate_hopset(
    graph: WeightedDigraph,
    hopset: dict[tuple[object, object], int],
    beta: float,
    epsilon: float,
    sources: list[object],
) -> dict[str, Any]:
    max_hop = 0
    overestimates = 0
    underestimated_pairs = 0
    for source in sources:
        h_dist = _hop_count_bfs_indexed(graph, source, set(hopset.keys()))
        for v in graph.vertices():
            if v in h_dist and h_dist[v] != 1 << 62:
                max_hop = max(max_hop, h_dist[v])
                if beta > 0 and h_dist[v] > beta + 1e-9:
                    overestimates += 1
        d_exact = dijkstra(graph, source)
        approx = shortest_path_hopbound(
            graph, hopset, source, max_hops=int(beta) + 5
        )
        for v, d in d_exact.items():
            if v == source:
                continue
            if v in approx and approx[v] > (1 + epsilon) * d + 1e-9:
                underestimated_pairs += 1
    return {
        "max_hop_observed": max_hop,
        "beta_violations": overestimates,
        "approximation_violations": underestimated_pairs,
    }


def benchmark_suite(
    sizes: Sequence[int],
    epsilons: Sequence[float],
    seed: int,
    output_csv: str | None,
) -> None:
    rows: list[dict[str, Any]] = []
    env = _environment_metadata()
    for n in sizes:
        for family_name, family_graph in _build_graphs([n], seed):
            for epsilon in epsilons:
                if isinstance(family_graph, Digraph):
                    gw = WeightedDigraph()
                    for v in family_graph.vertices():
                        gw.add_vertex(v)
                    for u in family_graph.vertices():
                        for v in family_graph.out_edges.get(u, ()):
                            gw.add_edge(u, v, 1)
                else:
                    gw = family_graph

                t0 = time.perf_counter()
                hopset, beta = build_hopset_for_sssp(
                    gw, epsilon=epsilon, random_seed=seed
                )
                elapsed = time.perf_counter() - t0

                sources = list(gw.vertices())[: min(100, n)]
                validation = _validate_hopset(
                    gw, hopset, beta, epsilon, sources
                )
                row = {
                    "family": family_name,
                    "n": n,
                    "epsilon": epsilon,
                    "beta": beta,
                    "hopset_size": len(hopset),
                    "elapsed_seconds": elapsed,
                    **validation,
                    "reached_pct": (
                        sum(
                            1
                            for v in gw.vertices()
                            for s in sources
                            if v in parallel_bfs(gw, s, set(hopset.keys()))
                        )
                        / (len(sources) * n)
                        * 100
                    ),
                }
                rows.append(row)
                log.info(
                    "%s n=%d eps=%.3f |H|=%d beta=%.2f time=%.3fs "
                    "max_hop=%d beta_viol=%d approx_viol=%d reached=%.1f%%",
                    family_name, n, epsilon, len(hopset), beta, elapsed,
                    row["max_hop_observed"], row["beta_violations"],
                    row["approximation_violations"], row["reached_pct"],
                )

    if output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[*env.keys(), *rows[0].keys()])
            writer.writeheader()
            for row in rows:
                writer.writerow({**env, **row})
        log.info("results written to %s", output_csv)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hopset oracle benchmark")
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 100])
    parser.add_argument("--epsilons", type=float, nargs="+", default=[0.05, 0.1, 0.2])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    benchmark_suite(args.sizes, args.epsilons, args.seed, args.output)


if __name__ == "__main__":
    main()
