"""Measure empirical parallel span of the construction.

Runs the JLS shortcut-set construction under a SpanProfiler and prints
the per-phase wall-clock times, total span, and parallelism factor
(theoretical work / measured span).

The construction is single-process. The reported parallelism factor
is therefore an UPPER BOUND on the speedup achievable with infinite
cores; anything faster than this on one process would imply we are
already well-parallelised.

Honest framing in docs/span_measurement.md.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.core.generators import random_dag
from reachq.core.config import get_logger
from reachq.core.work_depth import (
    SpanProfiler,
    theoretical_shortcut_depth,
    theoretical_shortcut_work,
)

log = get_logger("reachq.span")


def measure_one(n: int, density: float, seed: int) -> dict[str, float]:
    from reachq.core.algorithm import build_shortcut_set_for_reachability

    g = random_dag(n=n, edge_probability=density, random_seed=seed)
    n_vertices = g.num_vertices()
    m_edges = g.num_edges()

    # Cheap pre-pass: estimate rho from edge density.
    rho = max(1.0, (n_vertices**3 / max(1, m_edges)) ** 0.25)

    profiler = SpanProfiler()
    profiler.theoretical_work = theoretical_shortcut_work(n_vertices, m_edges, rho)
    profiler.theoretical_depth = theoretical_shortcut_depth(n_vertices, rho)

    profiler.begin_phase("construction")
    t0 = time.perf_counter()
    shortcuts, beta = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
    )
    wall = time.perf_counter() - t0
    profiler.end_phase()

    summary = profiler.summary()
    summary["n"] = n_vertices
    summary["m"] = m_edges
    summary["density"] = density
    summary["seed"] = seed
    summary["|H|"] = len(shortcuts)
    summary["beta"] = beta
    summary["wall_clock_total_seconds"] = wall
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure empirical parallel span")
    parser.add_argument("--sizes", nargs="+", type=int, default=[500, 1000])
    parser.add_argument("--densities", nargs="+", type=float, default=[0.05, 0.1])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    parser.add_argument("--out", default="results/span.csv")
    args = parser.parse_args()

    rows: list[dict[str, float]] = []
    for n in args.sizes:
        for density in args.densities:
            for seed in args.seeds:
                log.info("measuring span: n=%d density=%s seed=%d", n, density, seed)
                summary = measure_one(n, density, seed)
                rows.append(summary)

    import csv

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for r in rows for k in r.keys()})
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out_path)
    for r in rows:
        log.info(
            "n=%d d=%s seed=%d span=%.3fs wall=%.3fs "
            "theoretical_work=%.2e theoretical_depth=%.2f",
            int(r["n"]),
            r["density"],
            int(r["seed"]),
            r["span_seconds"],
            r["wall_clock_total_seconds"],
            r["theoretical_work"],
            r["theoretical_depth"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
