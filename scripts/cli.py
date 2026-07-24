"""Command-line interface for reachq.

Provides subcommands:
- reachability: build shortcut set and query reachability
- shortest-paths: build hopset and query shortest paths
- benchmark-reachability: run reachability benchmarks
- benchmark-shortest-paths: run shortest-path benchmarks
- generate-graph: create and serialize a test graph
"""

from __future__ import annotations

import argparse
import math
import sys
import time

from reachq.generators import (
    SNAP_DATASETS,
    complete_dag,
    cycle_graph,
    dense_graph,
    erdos_renyi_digraph,
    graph_with_sccs,
    path_graph,
    random_dag,
    weighted_dense_graph,
    weighted_path_graph,
    weighted_random_dag,
)
from reachq.graph import Digraph, WeightedDigraph
from reachq.hopset import build_hopset_for_sssp
from reachq.reachability import bfs_reachability, parallel_bfs
from reachq.serialization import (
    digraph_from_json,
    digraph_to_json,
    weighted_digraph_from_json,
    weighted_digraph_to_json,
)
from reachq.shortcut_set import build_shortcut_set_for_reachability
from reachq.shortest_paths import dijkstra, shortest_path_hopbound
from reachq.logging_config import get_logger
from reachq.work_depth import (
    WorkDepthAccountant,
    theoretical_hopset_depth,
    theoretical_hopset_work,
    theoretical_shortcut_depth,
    theoretical_shortcut_work,
)

log = get_logger("reachq.cli")


def load_digraph(path: str) -> Digraph:
    with open(path) as f:
        return digraph_from_json(f.read())


def load_weighted_digraph(path: str) -> WeightedDigraph:
    with open(path) as f:
        return weighted_digraph_from_json(f.read())


def cmd_reachability(args: argparse.Namespace) -> None:
    if args.graph:
        graph = load_digraph(args.graph)
    else:
        graph = dense_graph(args.n, args.m, random_seed=args.seed)

    accountant = WorkDepthAccountant()
    accountant.start_timer()
    start = time.perf_counter()
    shortcuts, beta = build_shortcut_set_for_reachability(
        graph, omega=args.omega, random_seed=args.seed
    )
    elapsed = time.perf_counter() - start
    accountant.stop_timer()

    source = args.source if args.source is not None else 0
    original = bfs_reachability(graph, source)
    augmented = parallel_bfs(graph, source, shortcuts)

    log.info("graph: n=%d m=%d", graph.num_vertices(), graph.num_edges())
    log.info("shortcut set size: %d", len(shortcuts))
    log.info("target hopbound beta: %.2f", beta)
    log.info("construction time: %.3fs", elapsed)
    log.info("reachable from %s: %d vertices", source, len(original))
    log.info("reachability preserved: %s", original == augmented)
    if args.verbose:
        n = graph.num_vertices()
        m = graph.num_edges()
        rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
        tw = theoretical_shortcut_work(n, m, rho, omega=args.omega)
        td = theoretical_shortcut_depth(n, rho)
        log.info("theoretical shortcut work: %.2e", tw)
        log.info("theoretical shortcut depth: %.2e", td)
        log.info("simulated work: %.2e", accountant.work)
        log.info("simulated depth: %.2e", accountant.depth)


def cmd_shortest_paths(args: argparse.Namespace) -> None:
    if args.graph:
        graph = load_weighted_digraph(args.graph)
    else:
        graph = weighted_dense_graph(
            args.n, args.m, weight_range=(1, 5), random_seed=args.seed
        )

    accountant = WorkDepthAccountant()
    accountant.start_timer()
    start = time.perf_counter()
    hopset, beta = build_hopset_for_sssp(
        graph, epsilon=args.epsilon, random_seed=args.seed
    )
    elapsed = time.perf_counter() - start
    accountant.stop_timer()

    source = args.source if args.source is not None else 0
    original = dijkstra(graph, source)
    approx = shortest_path_hopbound(graph, hopset, source, max_hops=args.max_hops)

    max_ratio = 0.0
    mismatches = 0
    for v in graph.vertices():
        orig_d = original.get(v, float("inf"))
        if orig_d == float("inf"):
            continue
        hop_d = approx.get(v, float("inf"))
        if hop_d == float("inf"):
            mismatches += 1
            continue
        if hop_d > (1 + args.epsilon) * orig_d + 1e-9:
            mismatches += 1
        ratio = hop_d / orig_d if orig_d > 0 else 0.0
        max_ratio = max(max_ratio, ratio)

    log.info("graph: n=%d m=%d", graph.num_vertices(), graph.num_edges())
    log.info("hopset size: %d", len(hopset))
    log.info("target hopbound beta: %.2f", beta)
    log.info("epsilon: %.4f", args.epsilon)
    log.info("construction time: %.3fs", elapsed)
    log.info("distance mismatches: %d", mismatches)
    log.info("max approximation ratio: %.4f", max_ratio)
    if args.verbose:
        n = graph.num_vertices()
        m = graph.num_edges()
        rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
        tw = theoretical_hopset_work(n, m, rho, epsilon=args.epsilon)
        td = theoretical_hopset_depth(n, m, rho)
        log.info("theoretical hopset work: %.2e", tw)
        log.info("theoretical hopset depth: %.2e", td)
        log.info("simulated work: %.2e", accountant.work)
        log.info("simulated depth: %.2e", accountant.depth)


def cmd_benchmark_reachability(args: argparse.Namespace) -> None:
    from scripts.benchmark_reachability import benchmark_suite

    benchmark_suite(
        sizes=args.sizes,
        densities=args.densities,
        omega=args.omega,
        seed=args.seed,
        output_csv=args.output,
    )


def cmd_benchmark_shortest_paths(args: argparse.Namespace) -> None:
    from scripts.benchmark_shortest_paths import benchmark_suite

    benchmark_suite(
        sizes=args.sizes,
        epsilons=args.epsilons,
        seed=args.seed,
        output_csv=args.output,
    )


def cmd_benchmark_large(args: argparse.Namespace) -> None:
    from scripts.benchmark_large import run_snap_benchmarks, run_synthetic_scaling

    if not args.synthetic_only:
        run_snap_benchmarks(args.datasets, args.omega, args.seed, args.output)
    if not args.snap_only:
        run_synthetic_scaling(
            args.synthetic_sizes,
            args.edge_density,
            args.omega,
            args.epsilon,
            args.seed,
            args.output,
        )


def cmd_generate_graph(args: argparse.Namespace) -> None:
    if args.weighted:
        if args.generator == "path":
            graph = weighted_path_graph(args.n, random_seed=args.seed)
        elif args.generator == "random_dag":
            graph = weighted_random_dag(
                args.n, edge_probability=args.p, random_seed=args.seed
            )
        elif args.generator == "dense":
            edge_count = min(args.n * (args.n - 1), args.m)
            graph = weighted_dense_graph(args.n, edge_count, random_seed=args.seed)
        else:
            log.error("unknown weighted generator: %s", args.generator)
            sys.exit(1)
        text = weighted_digraph_to_json(graph)
    else:
        if args.generator == "path":
            graph = path_graph(args.n)
        elif args.generator == "cycle":
            graph = cycle_graph(args.n)
        elif args.generator == "complete_dag":
            graph = complete_dag(args.n)
        elif args.generator == "random_dag":
            graph = random_dag(args.n, edge_probability=args.p, random_seed=args.seed)
        elif args.generator == "erdos_renyi":
            graph = erdos_renyi_digraph(
                args.n, edge_probability=args.p, random_seed=args.seed
            )
        elif args.generator == "dense":
            edge_count = min(args.n * (args.n - 1), args.m)
            graph = dense_graph(args.n, edge_count, random_seed=args.seed)
        elif args.generator == "scc":
            scc_sizes = args.scc_sizes or [3, 3, 3]
            graph = graph_with_sccs(
                scc_sizes,
                inter_edge_probability=args.p,
                random_seed=args.seed,
            )
        else:
            log.error("unknown generator: %s", args.generator)
            sys.exit(1)
        text = digraph_to_json(graph)

    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
        log.info("graph written to %s", args.output)
    else:
        sys.stdout.write(text + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reachq",
        description="Parallel Reachability and Shortest Paths on Non-Sparse Digraphs",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # reachability
    p_reach = subparsers.add_parser(
        "reachability", help="Build shortcut set and query reachability"
    )
    p_reach.add_argument("--graph", type=str, default=None, help="Input graph JSON")
    p_reach.add_argument(
        "--n", type=int, default=100, help="Vertices (if --graph omitted)"
    )
    p_reach.add_argument(
        "--m", type=int, default=1000, help="Edges (if --graph omitted)"
    )
    p_reach.add_argument("--omega", type=float, default=3.0)
    p_reach.add_argument("--source", type=int, default=None)
    p_reach.add_argument("--seed", type=int, default=42)
    p_reach.set_defaults(func=cmd_reachability)

    # shortest-paths
    p_sp = subparsers.add_parser(
        "shortest-paths", help="Build hopset and query shortest paths"
    )
    p_sp.add_argument(
        "--graph", type=str, default=None, help="Input weighted graph JSON"
    )
    p_sp.add_argument("--n", type=int, default=80, help="Vertices (if --graph omitted)")
    p_sp.add_argument("--m", type=int, default=800, help="Edges (if --graph omitted)")
    p_sp.add_argument("--epsilon", type=float, default=0.1)
    p_sp.add_argument("--max-hops", type=int, default=1000)
    p_sp.add_argument("--source", type=int, default=None)
    p_sp.add_argument("--seed", type=int, default=42)
    p_sp.set_defaults(func=cmd_shortest_paths)

    # benchmark-reachability
    p_br = subparsers.add_parser(
        "benchmark-reachability", help="Run reachability benchmarks"
    )
    p_br.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 100, 200])
    p_br.add_argument(
        "--densities", type=float, nargs="+", default=[0.1, 0.3, 0.5, 0.8]
    )
    p_br.add_argument("--omega", type=float, default=3.0)
    p_br.add_argument("--seed", type=int, default=42)
    p_br.add_argument("--output", type=str, default=None)
    p_br.set_defaults(func=cmd_benchmark_reachability)

    # benchmark-shortest-paths
    p_bs = subparsers.add_parser(
        "benchmark-shortest-paths", help="Run shortest-path benchmarks"
    )
    p_bs.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 100])
    p_bs.add_argument(
        "--epsilons", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.5]
    )
    p_bs.add_argument("--seed", type=int, default=42)
    p_bs.add_argument("--output", type=str, default=None)
    p_bs.set_defaults(func=cmd_benchmark_shortest_paths)

    # benchmark-large
    p_bl = subparsers.add_parser(
        "benchmark-large",
        help="Run large-graph benchmarks (SNAP + synthetic)",
    )
    p_bl.add_argument(
        "--datasets",
        nargs="+",
        default=list(SNAP_DATASETS.keys()),
        help="SNAP datasets (default: all)",
    )
    p_bl.add_argument(
        "--synthetic-sizes",
        type=int,
        nargs="*",
        default=[1000, 5000, 10000, 50000, 100000],
    )
    p_bl.add_argument("--edge-density", type=float, default=0.1)
    p_bl.add_argument("--omega", type=float, default=3.0)
    p_bl.add_argument("--epsilon", type=float, default=0.1)
    p_bl.add_argument("--seed", type=int, default=42)
    p_bl.add_argument("--output", type=str, default=None)
    p_bl.add_argument("--snap-only", action="store_true")
    p_bl.add_argument("--synthetic-only", action="store_true")
    p_bl.set_defaults(func=cmd_benchmark_large)

    # generate-graph
    p_gen = subparsers.add_parser(
        "generate-graph", help="Generate and serialize a graph"
    )
    p_gen.add_argument(
        "generator",
        choices=[
            "path",
            "cycle",
            "complete_dag",
            "random_dag",
            "erdos_renyi",
            "dense",
            "scc",
        ],
        help="Graph generator type",
    )
    p_gen.add_argument("--n", type=int, default=100, help="Number of vertices")
    p_gen.add_argument(
        "--m", type=int, default=1000, help="Number of edges (for dense)"
    )
    p_gen.add_argument("--p", type=float, default=0.3, help="Edge probability")
    p_gen.add_argument(
        "--scc-sizes",
        type=int,
        nargs="+",
        default=None,
        help="SCC sizes (for scc generator)",
    )
    p_gen.add_argument(
        "--weighted", action="store_true", help="Generate weighted graph"
    )
    p_gen.add_argument("--seed", type=int, default=42)
    p_gen.add_argument("--output", type=str, default=None, help="Output JSON file")
    p_gen.set_defaults(func=cmd_generate_graph)

    args = parser.parse_args()
    args.func(args)


def cli_main() -> None:
    main()


if __name__ == "__main__":
    cli_main()
