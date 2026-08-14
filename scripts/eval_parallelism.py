"""Empirical comparison of sequential / threads / processes parallelism.

Runs the JLS shortcut-set construction under different ParallelContext
modes and reports wall-clock + speedup vs sequential baseline.

Honest framing: this is an *empirical* speedup measurement, not a
theoretical PRAM bound. Speedup depends on:
  * Whether the bottleneck is numpy (GIL released, threads help)
    or Python (GIL held, threads don't help).
  * Whether CSR arrays or Python sets dominate the work.

Output: results/parallelism.csv + per-row log lines.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.config import get_logger
from reachq.core.generators import random_dag

log = get_logger("reachq.parallelism")


def measure(n: int, density: float, seed: int, workers: int) -> dict[str, float]:
    g = random_dag(n=n, edge_probability=density, random_seed=seed)
    t0 = time.perf_counter()
    shortcuts, beta = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
        parallel_workers=workers,
    )
    elapsed = time.perf_counter() - t0
    return {
        "n": n,
        "density": density,
        "seed": seed,
        "workers": workers,
        "elapsed_sec": round(elapsed, 3),
        "|H|": len(shortcuts),
        "beta": round(beta, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/parallelism.csv")
    parser.add_argument("--sizes", type=int, nargs="+", default=[200, 500, 1000])
    parser.add_argument("--densities", type=float, nargs="+", default=[0.1, 0.3])
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    args = parser.parse_args()

    rows: list[dict[str, float]] = []
    log.info("parallelism comparison starting")
    for n in args.sizes:
        for density in args.densities:
            for seed in args.seeds:
                # Sequential baseline first so we can compute speedup.
                seq_row = measure(n, density, seed, workers=1)
                seq_time = seq_row["elapsed_sec"]
                rows.append(seq_row)
                for w in args.workers:
                    if w == 1:
                        continue
                    r = measure(n, density, seed, workers=w)
                    r["speedup_vs_seq"] = round(
                        seq_time / max(1e-9, r["elapsed_sec"]), 2
                    )
                    rows.append(r)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "n",
        "density",
        "seed",
        "workers",
        "elapsed_sec",
        "|H|",
        "beta",
        "speedup_vs_seq",
    ]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)

    log.info("Speedup summary (vs sequential=1):")
    by_cfg: dict[tuple[int, float, int, int], dict[str, float]] = {}
    for r in rows:
        key = (r["n"], r["density"], r["seed"], r["workers"])
        by_cfg[key] = r
    for (n, d, seed, w), r in sorted(by_cfg.items()):
        speedup = r.get("speedup_vs_seq", 1.0)
        log.info(
            "n=%d d=%s seed=%d workers=%d: %.3fs |H|=%d speedup=%.2fx",
            n,
            d,
            seed,
            w,
            r["elapsed_sec"],
            r["|H|"],
            speedup,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
