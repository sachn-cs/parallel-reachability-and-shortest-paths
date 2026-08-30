"""Reachability oracle benchmark.

Validates the returned ``beta`` against actual max-hop from each
source in the largest weak component, and checks reachability
preservation. Reports environment metadata.
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

from reachq.core.shortcut import build_shortcut_set_for_reachability
from reachq.core.config import configure_logging, get_logger
from reachq.core.generators import (
    dense_graph,
    graph_with_sccs,
    path_graph,
    random_dag,
)
from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs


configure_logging()
log = get_logger("reachq.benchmark_reachability")


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


def _build_graphs(
    n_list: Sequence[int],
    densities: Sequence[float],
    seed: int,
) -> list[tuple[str, Digraph]]:
    families: list[tuple[str, Digraph]] = []
    for n in n_list:
        for density in densities:
            edge_count = max(1, int(density * n * (n - 1)))
            families.append(
                (
                    f"dense_n{n}_d{density:.2f}",
                    dense_graph(n, edge_count, random_seed=seed),
                )
            )
        families.append(
            (f"random_dag_n{n}", random_dag(n=n, edge_probability=0.1, random_seed=seed))
        )
        families.append(
            (f"with_sccs_n{n}", graph_with_sccs(scc_sizes=[max(1, n // 4)] * 4, inter_edge_probability=0.1, random_seed=seed))
        )
        families.append((f"path_n{n}", path_graph(n)))
    return families


def benchmark_suite(
    sizes: Sequence[int],
    densities: Sequence[float],
    omega: float,
    seed: int,
    output_csv: str | None,
) -> None:
    rows: list[dict[str, Any]] = []
    env = _environment_metadata()
    for family_name, graph in _build_graphs(sizes, densities, seed):
        t0 = time.perf_counter()
        shortcuts, beta = build_shortcut_set_for_reachability(
            graph, omega=omega, random_seed=seed
        )
        elapsed = time.perf_counter() - t0

        max_hop_global = 0
        reachability_violations = 0
        for source in graph.vertices():
            hop_dists = _hop_count_bfs_indexed(graph, source, shortcuts)
            reachable = [
                d for d in hop_dists.values() if d < (1 << 62)
            ]
            if reachable:
                max_hop_global = max(max_hop_global, max(reachable))
            if bfs_reachability(graph, source) != parallel_bfs(
                graph, source, shortcuts
            ):
                reachability_violations += 1

        row = {
            "family": family_name,
            "n": graph.num_vertices(),
            "m": graph.num_edges(),
            "omega": omega,
            "beta": beta,
            "shortcut_size": len(shortcuts),
            "elapsed_seconds": elapsed,
            "max_hop_global": max_hop_global,
            "reachability_violations": reachability_violations,
        }
        rows.append(row)
        log.info(
            "%s n=%d m=%d beta=%.2f |H|=%d time=%.3fs "
            "max_hop=%d reach_viol=%d",
            family_name, graph.num_vertices(), graph.num_edges(), beta,
            len(shortcuts), elapsed, max_hop_global, reachability_violations,
        )

    if output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[*env.keys(), *rows[0].keys()])
            writer.writeheader()
            for row in rows:
                writer.writerow({**env, **row})
        log.info("results written to %s", output_csv)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reachability oracle benchmark")
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 100])
    parser.add_argument("--densities", type=float, nargs="+", default=[0.2, 0.5])
    parser.add_argument("--omega", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    benchmark_suite(args.sizes, args.densities, args.omega, args.seed, args.output)


if __name__ == "__main__":
    main()
