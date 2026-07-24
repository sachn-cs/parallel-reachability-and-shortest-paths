"""Benchmark script for shortcut set construction and reachability queries.

Produces tabular output comparing construction time, shortcut set size,
and observed hop counts across varying graph sizes and densities.
"""

from __future__ import annotations

import argparse
import csv
import time

from reachq.core.generators import (
    dense_graph,
)
from reachq.core.graph import Digraph
from reachq.core.config import get_logger
from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.work_depth import WorkDepthAccountant

log = get_logger("reachq.benchmark_reachability")


def measure_shortcut_construction(
    graph: Digraph, omega: float, seed: int
) -> tuple[set[tuple[object, object]], float, float, float, float]:
    """Build shortcut set and return metrics.

    Returns: (shortcuts, beta, elapsed_seconds, max_hops, work_estimate)
    """
    accountant = WorkDepthAccountant()
    accountant.start_timer()
    start = time.perf_counter()
    shortcuts, beta = build_shortcut_set_for_reachability(
        graph, omega=omega, random_seed=seed
    )
    elapsed = time.perf_counter() - start
    accountant.stop_timer()

    # Measure max hops from a random source in the largest weak component
    # For simplicity, use vertex 0 if present
    source = 0 if graph.has_edge(0, 1) or graph.num_vertices() > 0 else None
    if source is not None:
        hop_dists = hop_count_bfs(graph, source, shortcuts)
        reachable = {v for v, d in hop_dists.items() if d < float("inf")}
        max_hops = max((hop_dists[v] for v in reachable), default=0)
    else:
        max_hops = 0

    return shortcuts, beta, elapsed, max_hops, accountant.work


def hop_count_bfs(graph: Digraph, source: object, shortcuts: set) -> dict[object, int]:
    """BFS returning hop counts."""
    from collections import deque

    dist: dict[object, int] = {v: float("inf") for v in graph.vertices()}  # type: ignore[dict-item]
    dist[source] = 0
    q: deque = deque([source])
    out = graph.out_edges
    s_list = list(shortcuts)
    while q:
        u = q.popleft()
        for v in out.get(u, set()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
        for a, b in s_list:
            if a == u and dist[b] == float("inf"):
                dist[b] = dist[u] + 1
                q.append(b)
    return dist


def benchmark_suite(
    sizes: list[int],
    densities: list[float],
    omega: float,
    seed: int,
    output_csv: str | None,
) -> None:
    """Run benchmarks across sizes and densities."""
    rows: list[dict[str, object]] = []
    for n in sizes:
        for density in densities:
            # Approximate edge count from density
            max_edges = n * (n - 1)
            edge_count = int(density * max_edges)
            if edge_count < n - 1 and density > 0:
                # Ensure enough edges for a non-trivial graph
                edge_count = min(max_edges, n)

            graph = dense_graph(n, edge_count, random_seed=seed)
            shortcuts, beta, elapsed, max_hops, work = measure_shortcut_construction(
                graph, omega, seed
            )
            row = {
                "n": n,
                "m": graph.num_edges(),
                "density": density,
                "omega": omega,
                "beta_target": beta,
                "shortcut_size": len(shortcuts),
                "elapsed_sec": elapsed,
                "max_hops_observed": max_hops,
                "simulated_work": work,
            }
            rows.append(row)
            log.info(
                "n=%d m=%d density=%.3f beta=%.2f |H|=%d time=%.3fs max_hops=%d",
                n, graph.num_edges(), density, beta,
                len(shortcuts), elapsed, max_hops,
            )

    if output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info("results written to %s", output_csv)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark shortcut set construction for reachability"
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[20, 50, 100, 200],
        help="Graph sizes (number of vertices) to benchmark",
    )
    parser.add_argument(
        "--densities",
        type=float,
        nargs="+",
        default=[0.1, 0.3, 0.5, 0.8],
        help="Edge density fractions relative to complete digraph",
    )
    parser.add_argument(
        "--omega", type=float, default=3.0, help="Matrix multiplication exponent"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output", type=str, default=None, help="Optional CSV output path"
    )
    args = parser.parse_args()
    benchmark_suite(args.sizes, args.densities, args.omega, args.seed, args.output)


if __name__ == "__main__":
    main()
