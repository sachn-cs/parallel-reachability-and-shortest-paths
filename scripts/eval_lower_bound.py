"""Empirical evaluation of the shortcut-set size bound.

For each construction in lower_bound.py, run the JLS construction
and compare |H| to the paper's bound. The result is a CSV with
|H|, bound, and ratio.

The expected empirical finding: the bound is LOOSE on all tested
constructions. The JLS adds O(n*k*log n) shortcuts; sparsify removes
most of them. The bound's m*rho + n*rho^2 hides the actual factor
n*k*log n via the choice of rho.

Output: results/lower_bound.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.logging_config import get_logger
from reachq.lower_bound import (
    barbell_graph,
    cycle_graph_dag,
    layered_dag,
    long_path_dag,
)
from reachq.shortcut_set import build_shortcut_set_for_reachability

log = get_logger("reachq.lower_bound_eval")


def measure(name, g, omega: float = 3.0, seed: int = 42) -> dict[str, object]:
    n = g.num_vertices()
    m = g.num_edges()
    H_with, beta = build_shortcut_set_for_reachability(
        g,
        omega=omega,
        random_seed=seed,
        sparsify_shortcuts=True,
    )
    H_without, _ = build_shortcut_set_for_reachability(
        g,
        omega=omega,
        random_seed=seed,
        sparsify_shortcuts=False,
    )
    rho = (n**0.5) / max(1e-9, beta)
    bound = m * rho + n * rho * rho
    return {
        "construction": name,
        "n": n,
        "m": m,
        "beta": round(beta, 3),
        "rho": round(rho, 3),
        "|H|_with_sparsify": len(H_with),
        "|H|_without_sparsify": len(H_without),
        "paper_bound": round(bound, 3),
        "ratio_with_to_bound": round(len(H_with) / max(1, bound), 4),
        "ratio_without_to_bound": round(len(H_without) / max(1, bound), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/lower_bound.csv")
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    log.info("running lower-bound evaluation")

    rows.append(measure("barbell_k=10", barbell_graph(10)))
    rows.append(measure("barbell_k=20", barbell_graph(20)))
    rows.append(measure("barbell_k=50", barbell_graph(50)))

    rows.append(measure("layered_5x10", layered_dag(5, 10)))
    rows.append(measure("layered_10x10", layered_dag(10, 10)))
    rows.append(measure("layered_20x10", layered_dag(20, 10)))

    rows.append(measure("path_n=20", long_path_dag(20)))
    rows.append(measure("path_n=50", long_path_dag(50)))
    rows.append(measure("path_n=100", long_path_dag(100)))

    rows.append(measure("cycle_n=10", cycle_graph_dag(10)))
    rows.append(measure("cycle_n=20", cycle_graph_dag(20)))
    rows.append(measure("cycle_n=50", cycle_graph_dag(50)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "construction",
        "n",
        "m",
        "beta",
        "rho",
        "|H|_with_sparsify",
        "|H|_without_sparsify",
        "paper_bound",
        "ratio_with_to_bound",
        "ratio_without_to_bound",
    ]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)

    log.info("summary:")
    for r in rows:
        log.info(
            "  %s: with=%d without=%d bound=%.0f " "ratio_with=%.4f ratio_without=%.4f",
            r["construction"],
            r["|H|_with_sparsify"],
            r["|H|_without_sparsify"],
            r["paper_bound"],
            r["ratio_with_to_bound"],
            r["ratio_without_to_bound"],
        )
    avg_with = sum(r["ratio_with_to_bound"] for r in rows) / len(rows)
    avg_without = sum(r["ratio_without_to_bound"] for r in rows) / len(rows)
    log.info("average ratio with_sparsify/bound = %.4f", avg_with)
    log.info("average ratio without_sparsify/bound = %.4f", avg_without)
    log.info(
        "INTERPRETATION: ratio < 1 means the bound is loose. "
        "The 'without_sparsify' column shows what the JLS construction "
        "produces by itself; the 'with_sparsify' column shows what the "
        "practical algorithm delivers after Innovation #1 (sparsify)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
