"""Benchmark script for hopset construction and approximate shortest paths.

Produces tabular output comparing construction time, hopset size,
and approximation quality across varying graph sizes and epsilon values.
"""

from __future__ import annotations

import argparse
import csv
import time
from typing import Any

from reachq.core.generators import weighted_dense_graph
from reachq.core.graph import WeightedDigraph
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.config import get_logger
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound
from reachq.core.work_depth import WorkDepthAccountant

log = get_logger("reachq.benchmark_shortest_paths")


def measure_hopset_construction(
    graph: WeightedDigraph, epsilon: float, seed: int
) -> tuple[dict[tuple[object, object], float], float, float, float, int, float]:
    """Build hopset and return metrics.

    Returns: (hopset, beta, elapsed_seconds, max_ratio, mismatches, work_estimate)
    """
    accountant = WorkDepthAccountant()
    accountant.start_timer()
    start = time.perf_counter()
    hopset, beta = build_hopset_for_sssp(graph, epsilon=epsilon, random_seed=seed)
    elapsed = time.perf_counter() - start
    accountant.stop_timer()

    max_ratio = 0.0
    mismatches = 0
    for source in list(graph.vertices())[:10]:  # sample 10 sources
        original = dijkstra(graph, source)
        approx = shortest_path_hopbound(graph, hopset, source, max_hops=1000)
        for v in graph.vertices():
            orig_d = original.get(v, float("inf"))
            if orig_d == float("inf"):
                continue
            hop_d = approx.get(v, float("inf"))
            if hop_d == float("inf"):
                mismatches += 1
                continue
            if hop_d > (1 + epsilon) * orig_d + 1e-9:
                mismatches += 1
            ratio = hop_d / orig_d if orig_d > 0 else 0.0
            max_ratio = max(max_ratio, ratio)

    return hopset, beta, elapsed, max_ratio, mismatches, accountant.work


def benchmark_suite(
    sizes: list[int],
    epsilons: list[float],
    seed: int,
    output_csv: str | None,
) -> None:
    """Run benchmarks across sizes and epsilon values."""
    rows: list[dict[str, Any]] = []
    for n in sizes:
        for epsilon in epsilons:
            # Use a moderately dense weighted graph
            edge_count = min(n * (n - 1), int(0.3 * n * n))
            graph = weighted_dense_graph(
                n, edge_count, weight_range=(1, 5), random_seed=seed
            )
            hopset, beta, elapsed, max_ratio, mismatches, work = (
                measure_hopset_construction(graph, epsilon, seed)
            )
            row = {
                "n": n,
                "m": graph.num_edges(),
                "epsilon": epsilon,
                "beta_target": beta,
                "hopset_size": len(hopset),
                "elapsed_sec": elapsed,
                "max_ratio_observed": max_ratio,
                "mismatches": mismatches,
                "simulated_work": work,
            }
            rows.append(row)
            log.info(
                "n=%d m=%d eps=%.3f beta=%.2f |H|=%d time=%.3fs max_ratio=%.4f mismatches=%d",
                n, graph.num_edges(), epsilon, beta,
                len(hopset), elapsed, max_ratio, mismatches,
            )

    if output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info("results written to %s", output_csv)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark hopset construction for shortest paths"
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[20, 50, 100],
        help="Graph sizes (number of vertices) to benchmark",
    )
    parser.add_argument(
        "--epsilons",
        type=float,
        nargs="+",
        default=[0.05, 0.1, 0.2, 0.5],
        help="Approximation factors epsilon",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output", type=str, default=None, help="Optional CSV output path"
    )
    args = parser.parse_args()
    benchmark_suite(args.sizes, args.epsilons, args.seed, args.output)


if __name__ == "__main__":
    main()
