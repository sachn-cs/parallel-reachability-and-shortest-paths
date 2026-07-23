"""Ablation: rerun the sampling ladder with each flag disabled.

Produces ``results/ablation.csv`` so the contribution of every algorithmic
refinement is measurable on a single graph class.

Only timeouts are caught (they're an expected outcome of a benchmark).
Other exceptions propagate.
"""

from __future__ import annotations

import argparse
import csv
import signal
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.logging_config import get_logger

log = get_logger("reachq.ablation")


@contextmanager
def _time_limit(seconds: int) -> Iterator[None]:
    def handler(signum: int, frame: object) -> None:
        raise TimeoutError(f"exceeded {seconds}s")
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


FLAG_NAMES = (
    "adaptive_sampling", "label_compress", "skip_condense",
    "hop_bounded_bfs", "degree_ordered_pivots", "tight_tc_trigger",
    "skip_trivial_part", "enable_tc_pruning",
)


def _all_off_except(name: str) -> dict[str, bool]:
    return {n: (n == name) for n in FLAG_NAMES}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablation over algorithmic flags")
    parser.add_argument("--sizes", nargs="+", type=int, default=[500])
    parser.add_argument("--densities", nargs="+", type=float, default=[0.1])
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--out", default="results/ablation.csv")
    args = parser.parse_args()

    from reachq.generators import random_dag, weighted_random_dag
    from reachq.shortcut_set import build_shortcut_set_for_reachability
    from reachq.hopset import build_hopset_for_sssp

    rows: list[dict[str, object]] = []
    all_on = {n: True for n in FLAG_NAMES}
    all_off = {n: False for n in FLAG_NAMES}
    configurations: list[tuple[str, dict[str, bool]]] = [
        ("all_on", all_on),
        ("all_off", all_off),
        *((f"only_{name}", _all_off_except(name)) for name in FLAG_NAMES),
    ]

    log.info("ablation starting; sizes=%s densities=%s",
             args.sizes, args.densities)
    for n in args.sizes:
        for density in args.densities:
            g = random_dag(n, edge_probability=density, random_seed=42)
            wg = weighted_random_dag(n, edge_probability=density, random_seed=42)
            for name, flags in configurations:
                log.info("n=%d d=%s cfg=%s", n, density, name)
                row: dict[str, object] = {
                    "config": name, "n": n, "density": density,
                    "m": g.num_edges(),
                    "flag_count_on": sum(1 for v in flags.values() if v),
                    **{f"flag_{k}": v for k, v in flags.items()},
                }
                try:
                    with _time_limit(args.timeout):
                        t0 = time.perf_counter()
                        shortcuts, beta = build_shortcut_set_for_reachability(
                            g, omega=3.0, random_seed=42, flags=flags,
                        )
                        elapsed = time.perf_counter() - t0
                    row.update({
                        "reach_beta": round(beta, 3),
                        "reach_|H|": len(shortcuts),
                        "reach_time_s": round(elapsed, 3),
                    })
                except TimeoutError:
                    row["reach_error"] = "timeout"
                try:
                    with _time_limit(args.timeout):
                        t0 = time.perf_counter()
                        hopset, beta = build_hopset_for_sssp(
                            wg, epsilon=0.1, random_seed=42, flags=flags,
                        )
                        elapsed = time.perf_counter() - t0
                    row.update({
                        "hop_beta": round(beta, 3),
                        "hop_|H|": len(hopset),
                        "hop_time_s": round(elapsed, 3),
                    })
                except TimeoutError:
                    row["hop_error"] = "timeout"
                rows.append(row)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "config", "n", "density", "m", "flag_count_on",
        "reach_beta", "reach_|H|", "reach_time_s", "reach_error",
        "hop_beta", "hop_|H|", "hop_time_s", "hop_error",
        *(f"flag_{k}" for k in FLAG_NAMES),
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())