"""Empirical comparison: JLS shortcut set vs Fix/Resample variant.

Honest framing: this is an *experimental* comparison. The Fix/Resample
variant is a static analogue of Paper 1's dynamic coloring algorithm;
its motivation is to explore whether a local-search alternative to JLS
sampling produces smaller shortcut sets on real graphs.

Expected outcome (documented in the script output): the JLS sampling
approach produces smaller shortcut sets than Fix/Resample on most
inputs because Fix/Resample selects pivots greedily (one uncovered
vertex at a time) rather than by random sampling.

Output: results/fix_resample_comparison.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.fix_resample import fix_resample_shortcut_set, fix_resample_reachable
from reachq.generators import (
    hamming_graph,
    paley_graph,
    petersen_graph,
    random_dag,
    shrikhande_graph,
)
from reachq.logging_config import get_logger
from reachq.reachability import bfs_reachability
from reachq.shortcut_set import build_shortcut_set_for_reachability

log = get_logger("reachq.fix_resample_eval")


def jls_with_random_seed(g, seed):
    shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)
    return shortcuts, beta


def fix_resample_with_random_seed(g, seed):
    return fix_resample_shortcut_set(g, random_seed=seed), None


def measure(label, g, seed):
    t0 = time.perf_counter()
    jls_H, beta = jls_with_random_seed(g, seed)
    jls_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    fr_H, _ = fix_resample_with_random_seed(g, seed)
    fr_time = time.perf_counter() - t0

    # Sanity: both must preserve reachability.
    for v in g.vertices():
        assert bfs_reachability(g, v) == fix_resample_reachable(g, v, jls_H)
        assert bfs_reachability(g, v) == fix_resample_reachable(g, v, fr_H)

    # Empirical hopbound: max BFS depth actually observed in G + H.
    from collections import deque
    def empirical_max_hops(shortcuts):
        out = g.out_edges
        index = {}
        for u, v in shortcuts:
            index.setdefault(u, []).append(v)
        max_h = 0
        for src in g.vertices():
            dist = {v: float("inf") for v in g.vertices()}
            dist[src] = 0
            q = deque([src])
            while q:
                u = q.popleft()
                for v in out.get(u, set()):
                    if dist[v] == float("inf"):
                        dist[v] = dist[u] + 1; q.append(v)
                for v in index.get(u, ()):
                    if dist[v] == float("inf"):
                        dist[v] = dist[u] + 1; q.append(v)
            max_h = max(max_h, max((d for d in dist.values() if d < float("inf")), default=0))
        return max_h

    jls_hops = empirical_max_hops(jls_H)
    fr_hops = empirical_max_hops(fr_H)
    ratio_size = len(fr_H) / max(1, len(jls_H))
    ratio_hops = fr_hops / max(1, jls_hops)
    return {
        "label": label, "seed": seed,
        "n": g.num_vertices(), "m": g.num_edges(),
        "|H|_jls": len(jls_H), "|H|_fix_resample": len(fr_H),
        "size_ratio_fr_over_jls": round(ratio_size, 3),
        "empirical_hops_jls": jls_hops,
        "empirical_hops_fr": fr_hops,
        "hops_ratio_fr_over_jls": round(ratio_hops, 2),
        "beta": round(beta, 3) if beta else "",
        "jls_time_s": round(jls_time, 4),
        "fr_time_s": round(fr_time, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/fix_resample_comparison.csv")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--random-sizes", type=int, nargs="+", default=[50, 100, 200])
    args = parser.parse_args()

    rows: list[dict[str, object]] = []

    log.info("named fixtures (Papers 2/3)")
    for seed in args.seeds:
        for label, g in [
            ("Petersen", petersen_graph()),
            ("Paley(13)", paley_graph(13)),
            ("Shrikhande/rook", shrikhande_graph()),
            ("Hamming(2,4)", hamming_graph(2, 4)),
            ("Hamming(3,3)", hamming_graph(3, 3)),
        ]:
            row = measure(label, g, seed)
            rows.append(row)
            log.info(
                "%s seed=%d: |H|_jls=%d |H|_fr=%d size_ratio=%.2f hops_jls=%d hops_fr=%d",
                label, seed, row["|H|_jls"], row["|H|_fix_resample"],
                row["size_ratio_fr_over_jls"],
                row["empirical_hops_jls"], row["empirical_hops_fr"],
            )

    log.info("random DAGs")
    for seed in args.seeds:
        for n in args.random_sizes:
            for p in (0.1, 0.3):
                label = f"random_dag_n{n}_p{p}"
                g = random_dag(n, edge_probability=p, random_seed=seed)
                row = measure(label, g, seed)
                rows.append(row)
                log.info(
                    "%s seed=%d: |H|_jls=%d |H|_fr=%d size_ratio=%.2f jls_time=%.2fs fr_time=%.2fs",
                    label, seed, row["|H|_jls"], row["|H|_fix_resample"],
                    row["size_ratio_fr_over_jls"], row["jls_time_s"], row["fr_time_s"],
                )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "label", "seed", "n", "m",
        "|H|_jls", "|H|_fix_resample", "size_ratio_fr_over_jls",
        "empirical_hops_jls", "empirical_hops_fr", "hops_ratio_fr_over_jls",
        "beta", "jls_time_s", "fr_time_s",
    ]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)

    # Summary: aggregate ratios.
    if rows:
        avg_size = sum(r["size_ratio_fr_over_jls"] for r in rows) / len(rows)
        avg_hops = sum(r["hops_ratio_fr_over_jls"] for r in rows) / len(rows)
        log.info(
            "average |H|_fr / |H|_jls = %.2f (Fix/Resample smaller on %d / %d cases)",
            avg_size,
            sum(1 for r in rows if r["size_ratio_fr_over_jls"] < 1.0),
            len(rows),
        )
        log.info(
            "average hops_fr / hops_jls = %.2f (Fix/Resample looser on %d / %d cases)",
            avg_hops,
            sum(1 for r in rows if r["hops_ratio_fr_over_jls"] > 1.0),
            len(rows),
        )
        log.info(
            "INTERPRETATION: Fix/Resample produces smaller |H| but looser "
            "hopbound. JLS oversamples and gets a tighter hopbound. "
            "Trade-off: pick Fix/Resample if |H| matters more than query "
            "time; pick JLS if hopbound matters."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())