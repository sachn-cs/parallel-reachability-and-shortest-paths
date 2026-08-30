"""Empirical comparison: streaming vs batch shortcut-set maintenance.

Streams edges one at a time through StreamingShortcutSet and compares
its final shortcut set against the batch output from
reachq.shortcut_set.build_shortcut_set_for_reachability.

Output: a single-row CSV with |H_streaming|, |H_batch|, and whether
they preserve reachability identically.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.core.shortcut import build_shortcut_set_for_reachability
from reachq.core.config import get_logger
from reachq.core.generators import random_dag
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.research.streaming import StreamingShortcutSet

log = get_logger("reachq.eval_streaming")


def evaluate(n: int, p: float, beta: int, seed: int) -> dict:
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    s = StreamingShortcutSet(g, beta=beta, seed=seed)
    # Stream all edges one at a time.
    edges = list(g.edges())
    for u, v in edges:
        s.insert_edge(u, v)
    H_streaming = s.get_shortcuts()

    # Run batch JLS on the ORIGINAL graph (not augmented). Comparing
    # against an augmented graph would trivially yield |H|_batch=0
    # because every reachability query is already satisfied by the
    # augmented shortcuts.
    H_batch, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)

    # Soundness: R+(G, s) = R+(G + H_streaming, s) for all s.
    sound_streaming = all(
        bfs_reachability(g, s) == parallel_bfs(g, s, H_streaming) for s in g.vertices()
    )
    sound_batch = all(
        bfs_reachability(g, s) == parallel_bfs(g, s, H_batch) for s in g.vertices()
    )

    return {
        "n": n,
        "p": p,
        "beta": beta,
        "seed": seed,
        "edges": g.num_edges(),
        "|H|_streaming": len(H_streaming),
        "|H|_batch": len(H_batch),
        "sound_streaming": sound_streaming,
        "sound_batch": sound_batch,
    }


def main() -> int:
    rows = []
    log.info("streaming vs batch comparison")
    for n in [20, 30, 50]:
        for p in [0.1, 0.3]:
            for beta in [2, 4]:
                row = evaluate(n=n, p=p, beta=beta, seed=42)
                rows.append(row)
                log.info(
                    "n=%d p=%.2f beta=%d: |H|_streaming=%d |H|_batch=%d sound_s=%s sound_b=%s",
                    n,
                    p,
                    beta,
                    row["|H|_streaming"],
                    row["|H|_batch"],
                    row["sound_streaming"],
                    row["sound_batch"],
                )

    out_path = Path("results/streaming_vs_batch.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out_path)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
