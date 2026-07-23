"""Search for counterexamples to Corollary 2.3 of docs/paper_refinements.md.

The corollary claims that the tightened TC trigger (Lemma 2.2)
preserves Theorem 2's bound |H| <= O(m*rho + n*rho^2) in the dense
regime. We search for graphs where |H|_tight significantly exceeds
|H|_paper or where the |H|/n ratio grows superlinearly with n.

For each (n, p) we sample random DAGs and report:
  * |H|_paper  (TC trigger = paper's threshold)
  * |H|_tight  (TC trigger = Lemma 2.2's work-comparison)
  * theoretical_bound = m*rho + n*rho^2  (paper's worst-case)

The asymptotic bound is loose in absolute terms; we look for the
*RATIO* |H|/theoretical_bound to grow with n, which would indicate
the tightened trigger violates the bound asymptotically.

Output: results/counterexample_search.csv with one row per (n, p, seed).
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.generators import random_dag
from reachq.logging_config import get_logger
from reachq.shortcut_set import build_shortcut_set_for_reachability

log = get_logger("reachq.counterexample")


PAPER_TC_FLAGS = {
    "enable_tc_pruning": True, "tight_tc_trigger": False,
    "adaptive_sampling": False, "label_compress": False,
    "skip_condense": False, "hop_bounded_bfs": False,
    "degree_ordered_pivots": False, "skip_trivial_part": False,
    "parallel": False,
}
TIGHT_TC_FLAGS = {
    "enable_tc_pruning": True, "tight_tc_trigger": True,
    "adaptive_sampling": False, "label_compress": False,
    "skip_condense": False, "hop_bounded_bfs": False,
    "degree_ordered_pivots": False, "skip_trivial_part": False,
    "parallel": False,
}


def theoretical_bound(n: int, m: int, rho: float) -> float:
    """Paper's worst-case bound |H| <= O(m*rho + n*rho^2)."""
    return m * rho + n * rho * rho


def measure_one(n: int, p: float, seed: int) -> dict[str, float]:
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    m = g.num_edges()
    s_paper, beta = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=seed, flags=PAPER_TC_FLAGS,
    )
    s_tight, beta_t = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=seed, flags=TIGHT_TC_FLAGS,
    )
    # Compute rho from the wrapper's beta.
    rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
    bound = theoretical_bound(n, m, rho)
    return {
        "n": n, "p": p, "seed": seed,
        "m": m, "rho": round(rho, 3), "beta": round(beta, 3),
        "|H|_paper": len(s_paper),
        "|H|_tight": len(s_tight),
        "theoretical_bound": round(bound, 3),
        "ratio_paper": round(len(s_paper) / max(1, bound), 3),
        "ratio_tight": round(len(s_tight) / max(1, bound), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/counterexample_search.csv")
    parser.add_argument("--sizes", type=int, nargs="+", default=[10, 15, 20, 30, 50, 80])
    parser.add_argument("--densities", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.4])
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    rows: list[dict[str, float]] = []
    log.info(
        "starting counterexample search: sizes=%s densities=%s seeds=%s",
        args.sizes, args.densities, args.seeds,
    )
    for n in args.sizes:
        for p in args.densities:
            for seed in args.seeds:
                log.info("n=%d p=%s seed=%d", n, p, seed)
                rows.append(measure_one(n, p, seed))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)

    log.info("Summary:")
    by_n: dict[int, list[dict[str, float]]] = {}
    for r in rows:
        by_n.setdefault(int(r["n"]), []).append(r)
    for n in sorted(by_n):
        rs = by_n[n]
        max_ratio_tight = max(r["ratio_tight"] for r in rs)
        max_ratio_paper = max(r["ratio_paper"] for r in rs)
        log.info(
            "n=%d: max |H|_tight/bound = %.2f, max |H|_paper/bound = %.2f",
            n, max_ratio_tight, max_ratio_paper,
        )

    worst_tight = max(rows, key=lambda r: r["ratio_tight"])
    if worst_tight["ratio_tight"] > 100:
        log.warning(
            "ratio_tight > 100 found at n=%d: |H|_tight=%d, bound=%.0f",
            int(worst_tight["n"]),
            int(worst_tight["|H|_tight"]),
            worst_tight["theoretical_bound"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())