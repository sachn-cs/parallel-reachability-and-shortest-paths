"""Empirical evaluation for the two refinements documented in
``docs/paper_refinements.md``.

For each refinement, runs four configurations:
  (a) refinement on, paper trigger on
  (b) refinement on, paper trigger off (= refinement + its tightened bound)
  (c) refinement off (= paper baseline)
  (d) refinement off, paper trigger on, but force-firing (best of paper)

Reports |H|, wall-clock, correctness (reachability preserved), and
beta-hopbound violation count per configuration.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import deque
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.core.config import get_logger

log = get_logger("reachq.eval_refinements")


def time_limit_budget(seconds: int) -> Iterator[None]:
    import signal

    def handler(signum: int, frame: object) -> None:
        raise TimeoutError(f"timeout {seconds}s")

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def hopbound_actual(graph, source: object, shortcuts, beta: float) -> tuple[int, int]:
    """Run parallel BFS with shortcuts, return (max hops observed, violations).

    Returns (max_observed, count_over_beta).
    """
    dist: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    dist[source] = 0
    q: deque = deque([source])
    out = graph.out_edges
    shortcut_index: dict[object, list[object]] = {}
    for u, v in shortcuts:
        shortcut_index.setdefault(u, []).append(v)
    while q:
        u = q.popleft()
        if dist[u] > beta:
            continue
        for v in out.get(u, set()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
        for v in shortcut_index.get(u, ()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
    reachable = {v: d for v, d in dist.items() if d < float("inf")}
    max_observed = int(max(reachable.values(), default=0))
    return max_observed, sum(1 for d in reachable.values() if d > beta)


def run_one(
    graph, flags: dict[str, bool], seed: int, omega: float, max_seconds: int
) -> dict[str, object]:
    from reachq.core.shortcut import build_shortcut_set_for_reachability
    from reachq.core.reachability import bfs_reachability, parallel_bfs

    row: dict[str, object] = {
        "n": graph.num_vertices(),
        "m": graph.num_edges(),
        "seed": seed,
        **{f"flag_{k}": v for k, v in flags.items()},
    }
    try:
        t0 = time.perf_counter()
        shortcuts, beta, _ = build_shortcut_set_for_reachability(
            graph,
            omega=omega,
            random_seed=seed,
            flags=flags,
        )
        elapsed = time.perf_counter() - t0
        row.update(
            {
                "beta": round(beta, 3),
                "|H|": len(shortcuts),
                "elapsed_sec": round(elapsed, 3),
                "error": "",
            }
        )
        # Reachability preservation: every source.
        reachable_correct = True
        for src in list(graph.vertices())[:20]:  # sample 20 sources
            original = bfs_reachability(graph, src)
            augmented = parallel_bfs(graph, src, shortcuts)
            if original != augmented:
                reachable_correct = False
                break
        row["reachability_correct"] = reachable_correct
        # Beta-hopbound observed.
        src = next(iter(graph.vertices()))
        max_obs, violations = hopbound_actual(graph, src, shortcuts, beta)
        row["max_hops_observed"] = max_obs
        row["hopbound_violations"] = violations
    except TimeoutError as e:
        row["error"] = str(e)
    except Exception as e:  # noqa: BLE001 - harness records the failure and continues
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/refinements.csv")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--sizes", type=int, nargs="+", default=[500, 1000])
    parser.add_argument("--densities", type=float, nargs="+", default=[0.1])
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--datasets", nargs="+", default=None, help="Optional SNAP dataset names"
    )
    args = parser.parse_args()

    from reachq.core.generators import random_dag

    configurations: list[tuple[str, dict[str, bool]]] = [
        # Lemma 7 — TC trigger
        (
            "baseline_tc_off",
            {
                "enable_tc_pruning": False,
                "tight_tc_trigger": False,
                "adaptive_sampling": False,
                "label_compress": False,
                "skip_condense": False,
                "hop_bounded_bfs": False,
                "degree_ordered_pivots": False,
                "skip_trivial_part": False,
            },
        ),
        (
            "paper_tc_trigger",
            {
                "enable_tc_pruning": True,
                "tight_tc_trigger": False,
                "adaptive_sampling": False,
                "label_compress": False,
                "skip_condense": False,
                "hop_bounded_bfs": False,
                "degree_ordered_pivots": False,
                "skip_trivial_part": False,
            },
        ),
        (
            "tight_tc_trigger",
            {
                "enable_tc_pruning": True,
                "tight_tc_trigger": True,
                "adaptive_sampling": False,
                "label_compress": False,
                "skip_condense": False,
                "hop_bounded_bfs": False,
                "degree_ordered_pivots": False,
                "skip_trivial_part": False,
            },
        ),
        # Lemma 4 — hop-bounded BFS
        (
            "baseline_hbb_off",
            {
                "enable_tc_pruning": False,
                "tight_tc_trigger": False,
                "adaptive_sampling": False,
                "label_compress": False,
                "skip_condense": False,
                "hop_bounded_bfs": False,
                "degree_ordered_pivots": False,
                "skip_trivial_part": False,
            },
        ),
        (
            "hop_bounded_bfs",
            {
                "enable_tc_pruning": False,
                "tight_tc_trigger": False,
                "adaptive_sampling": False,
                "label_compress": False,
                "skip_condense": False,
                "hop_bounded_bfs": True,
                "degree_ordered_pivots": False,
                "skip_trivial_part": False,
            },
        ),
    ]

    rows: list[dict[str, object]] = []
    for n in args.sizes:
        for density in args.densities:
            for seed in args.seeds:
                g = random_dag(n, edge_probability=density, random_seed=seed)
                for name, flags in configurations:
                    log.info("n=%d d=%s seed=%d cfg=%s", n, density, seed, name)
                    row = run_one(g, flags, seed, omega=3.0, max_seconds=args.timeout)
                    row["config"] = name
                    row["density"] = density
                    row["source"] = f"random_dag_n{n}_d{density}_s{seed}"
                    rows.append(row)

    # SNAP datasets, if requested.
    if args.datasets:
        from reachq.core.generators import load_dataset

        for name in args.datasets:
            try:
                g = load_dataset(name)
            except Exception as e:  # noqa: BLE001 - record load failure and continue
                rows.append(
                    {
                        "config": "load_failed",
                        "source": name,
                        "error": f"{type(e).__name__}: {e}",
                    }
                )
                continue
            for cfg_name, flags in configurations:
                log.info("snap=%s cfg=%s", name, cfg_name)
                row = run_one(g, flags, seed=42, omega=3.0, max_seconds=args.timeout)
                row["config"] = cfg_name
                row["density"] = ""
                row["source"] = name
                rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "config",
        "source",
        "n",
        "m",
        "density",
        "seed",
        "beta",
        "|H|",
        "elapsed_sec",
        "reachability_correct",
        "max_hops_observed",
        "hopbound_violations",
        "error",
        *(
            f"flag_{k}"
            for k in (
                "enable_tc_pruning",
                "tight_tc_trigger",
                "adaptive_sampling",
                "label_compress",
                "skip_condense",
                "hop_bounded_bfs",
                "degree_ordered_pivots",
                "skip_trivial_part",
            )
        ),
    ]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
