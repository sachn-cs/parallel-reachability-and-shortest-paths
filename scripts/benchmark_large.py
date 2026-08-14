"""Large-graph benchmarks for shortcut set and hopset construction.

Runs on SNAP datasets (auto-downloaded) and large synthetic graphs.
Reports construction time, set size, target hopbound, and correctness.

Each benchmark row is printed and flushed to the CSV immediately, so
interrupting with Ctrl+C preserves completed results. Datasets are
benchmark concurrently across --workers processes.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import multiprocessing
import signal
import time
from collections.abc import Iterator

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.config import get_logger
from reachq.core.generators import (
    SNAP_DATASETS,
    load_dataset,
    random_dag,
    weighted_random_dag,
)
from reachq.core.graph import Digraph, WeightedDigraph
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound

log = get_logger("reachq.benchmark_large")


class TimeoutExceeded(Exception):
    """Raised when construction exceeds the configured timeout."""


@contextlib.contextmanager
def time_limit(seconds: int) -> Iterator[None]:
    """Raise TimeoutExceeded after *seconds* seconds."""

    def handler(signum: int, frame: object) -> None:
        raise TimeoutExceeded(f"Construction exceeded {seconds}s timeout")

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def benchmark_reachability(
    graph: Digraph,
    omega: float,
    seed: int,
    check_correctness: bool = True,
    timeout: int | None = None,
) -> dict[str, object]:
    """Build shortcut set and measure metrics."""
    n = graph.num_vertices()
    m = graph.num_edges()

    result: dict[str, object] = {"n": n, "m": m}

    try:
        with time_limit(timeout) if timeout else contextlib.nullcontext():
            start = time.perf_counter()
            shortcuts, beta = build_shortcut_set_for_reachability(
                graph,
                omega=omega,
                random_seed=seed,
            )
            elapsed = time.perf_counter() - start
        result.update(
            {
                "beta": round(beta, 2),
                "shortcut_size": len(shortcuts),
                "elapsed_sec": round(elapsed, 3),
            }
        )
        if check_correctness and n <= 10000:
            source = next(iter(graph.vertices()))
            original = bfs_reachability(graph, source)
            augmented = parallel_bfs(graph, source, shortcuts)
            result["correct"] = original == augmented
    except TimeoutExceeded as e:
        result["error"] = str(e)

    return result


def benchmark_shortest_paths(
    graph: WeightedDigraph,
    epsilon: float,
    seed: int,
    check_correctness: bool = True,
    timeout: int | None = None,
) -> dict[str, object]:
    """Build hopset and measure metrics."""
    n = graph.num_vertices()
    m = graph.num_edges()

    result: dict[str, object] = {"n": n, "m": m, "epsilon": epsilon}

    try:
        with time_limit(timeout) if timeout else contextlib.nullcontext():
            start = time.perf_counter()
            hopset, beta = build_hopset_for_sssp(
                graph,
                epsilon=epsilon,
                random_seed=seed,
            )
            elapsed = time.perf_counter() - start
        result.update(
            {
                "beta": round(beta, 2),
                "hopset_size": len(hopset),
                "elapsed_sec": round(elapsed, 3),
            }
        )
        if check_correctness and n <= 10000:
            source = next(iter(graph.vertices()))
            original = dijkstra(graph, source)
            approx = shortest_path_hopbound(graph, hopset, source, max_hops=1000)
            mismatches = sum(
                1
                for v in graph.vertices()
                if original.get(v, float("inf")) < float("inf")
                and approx.get(v, float("inf")) > (1 + epsilon) * original[v] + 1e-9
            )
            result["mismatches"] = mismatches
    except TimeoutExceeded as e:
        result["error"] = str(e)

    return result


def format_row(row: dict[str, object]) -> str:
    """Format a result row for stdout."""
    if "error" in row:
        return f"  TIMEOUT: {row['error']}"
    parts = [f"n={row['n']}", f"m={row['m']}", f"beta={row['beta']}"]
    if "shortcut_size" in row:
        parts.append(f"|H|={row['shortcut_size']}")
    if "hopset_size" in row:
        parts.append(f"|H|={row['hopset_size']}")
    parts.append(f"time={row['elapsed_sec']}s")
    if "correct" in row:
        parts.append(f"correct={row['correct']}")
    if "mismatches" in row:
        parts.append(f"mismatches={row['mismatches']}")
    return "  " + " ".join(parts)


class CsvWriter:
    """Append rows to a CSV file with a stable header, flushing after each row."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.header: list[str] | None = None
        self._stack = contextlib.ExitStack()
        self.fh = self._stack.enter_context(
            open(path, "a", newline="", buffering=1)  # noqa: SIM115 - held by ExitStack, closed in close()
        )

    def write(self, row: dict[str, object]) -> None:
        """Append a row to the CSV, writing the header on first use."""
        if self.header is None:
            self.header = list(row.keys())
            writer = csv.DictWriter(self.fh, fieldnames=self.header)
            writer.writeheader()
            self.fh.flush()
        assert self.header is not None
        writer = csv.DictWriter(self.fh, fieldnames=self.header, extrasaction="ignore")
        writer.writerow(row)
        self.fh.flush()

    def close(self) -> None:
        """Close the underlying file handle."""
        self._stack.close()


def run_one_snap(
    name: str, omega: float, seed: int, check_correctness: bool
) -> dict[str, object]:
    """Worker entry point: load and benchmark a single SNAP dataset."""
    graph = load_dataset(name)
    row = benchmark_reachability(
        graph,
        omega=omega,
        seed=seed,
        check_correctness=check_correctness,
        timeout=None,
    )
    row["source"] = name
    row["kind"] = "snap-reachability"
    return row


def run_snap_benchmarks(
    datasets: list[str],
    omega: float,
    seed: int,
    output_csv: str | None,
    check_correctness: bool,
    timeout: int | None,
    workers: int,
) -> None:
    """Benchmark reachability on SNAP datasets, concurrently across workers."""
    writer = CsvWriter(output_csv) if output_csv else None
    try:
        if workers <= 1 or len(datasets) <= 1:
            for name in datasets:
                log.info("--- %s (%s) ---", name, SNAP_DATASETS[name]["type"])
                try:
                    row = run_one_snap(name, omega, seed, check_correctness)
                except Exception as e:  # noqa: BLE001 - harness records the failure and continues
                    row = {
                        "source": name,
                        "kind": "snap-reachability",
                        "error": f"load failed: {e}",
                    }
                    log.warning("  load failed: %s", e)
                else:
                    log.info("%s", format_row(row))
                if writer:
                    writer.write(row)
            return

        ctx = multiprocessing.get_context("spawn")
        pool = ctx.Pool(processes=min(workers, len(datasets)))
        async_results: dict[multiprocessing.pool.AsyncResult, str] = {}
        pool_alive = True
        try:
            async_results = {
                pool.apply_async(
                    run_one_snap,
                    (name, omega, seed, check_correctness),
                ): name
                for name in datasets
            }
            while async_results:
                async_result, name = next(iter(async_results.items()))
                log.info("--- %s (%s) ---", name, SNAP_DATASETS[name]["type"])
                try:
                    row = async_result.get(timeout=timeout)
                except multiprocessing.TimeoutError:
                    pool.terminate()
                    pool.join()
                    pool_alive = False
                    for pending_name in async_results.values():
                        row = {
                            "source": pending_name,
                            "kind": "snap-reachability",
                            "error": f"exceeded {timeout}s timeout",
                        }
                        log.info(
                            "--- %s (%s) ---",
                            pending_name,
                            SNAP_DATASETS[pending_name]["type"],
                        )
                        log.warning("  timeout after %ds", timeout)
                        if writer:
                            writer.write(row)
                    async_results.clear()
                    break
                except Exception as e:  # noqa: BLE001 - harness records the failure and continues
                    row = {
                        "source": name,
                        "kind": "snap-reachability",
                        "error": f"worker failed: {e}",
                    }
                    log.warning("  failed: %s", e)
                else:
                    log.info("%s", format_row(row))
                if writer:
                    writer.write(row)
                del async_results[async_result]
        finally:
            if pool_alive:
                pool.close()
                pool.join()
    finally:
        if writer:
            writer.close()


def run_synthetic_scaling(
    sizes: list[int],
    edge_density: float,
    omega: float,
    epsilon: float,
    seed: int,
    output_csv: str | None,
    check_correctness: bool,
    timeout: int | None,
) -> None:
    """Benchmark on large synthetic random DAGs."""
    writer = CsvWriter(output_csv) if output_csv else None
    try:
        for n in sizes:
            m = int(edge_density * n * (n - 1) // 2)
            log.info("--- synthetic n=%d m=%d ---", n, m)

            graph = random_dag(n, edge_probability=edge_density, random_seed=seed)
            row = benchmark_reachability(
                graph,
                omega=omega,
                seed=seed,
                check_correctness=check_correctness,
                timeout=timeout,
            )
            row["source"] = f"random_dag_{n}"
            row["kind"] = "synthetic-reachability"
            log.info("%s", format_row(row))
            if writer:
                writer.write(row)

            wgraph = weighted_random_dag(
                n,
                edge_probability=edge_density,
                weight_range=(1, 5),
                random_seed=seed,
            )
            wrow = benchmark_shortest_paths(
                wgraph,
                epsilon=epsilon,
                seed=seed,
                check_correctness=check_correctness,
                timeout=timeout,
            )
            wrow["source"] = f"random_dag_{n}"
            wrow["kind"] = "synthetic-shortest-paths"
            log.info("%s", format_row(wrow))
            if writer:
                writer.write(wrow)
    finally:
        if writer:
            writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Large-graph benchmarks")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=list(SNAP_DATASETS.keys()),
        help="SNAP datasets to benchmark (default: all)",
    )
    parser.add_argument(
        "--synthetic-sizes",
        type=int,
        nargs="*",
        default=[1000, 5000, 10000, 50000, 100000],
        help="Synthetic graph sizes",
    )
    parser.add_argument(
        "--edge-density",
        type=float,
        default=0.1,
        help="Edge density for synthetic DAGs",
    )
    parser.add_argument("--omega", type=float, default=3.0)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None, help="CSV output path")
    parser.add_argument("--snap-only", action="store_true")
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument(
        "--skip-correctness", action="store_true", help="Skip correctness checks"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-graph construction timeout in seconds",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker processes for SNAP benchmarks",
    )
    args = parser.parse_args()

    check_correctness = not args.skip_correctness

    if not args.synthetic_only:
        log.info("=== SNAP Datasets (workers=%d) ===", args.workers)
        try:
            run_snap_benchmarks(
                args.datasets,
                args.omega,
                args.seed,
                args.output,
                check_correctness,
                args.timeout,
                args.workers,
            )
        except KeyboardInterrupt:
            log.warning("interrupted; partial results preserved in CSV")
            return

    if not args.snap_only:
        log.info("=== Synthetic Scaling ===")
        try:
            run_synthetic_scaling(
                args.synthetic_sizes,
                args.edge_density,
                args.omega,
                args.epsilon,
                args.seed,
                args.output,
                check_correctness,
                args.timeout,
            )
        except KeyboardInterrupt:
            log.warning("interrupted; partial results preserved in CSV")
            return


if __name__ == "__main__":
    main()
