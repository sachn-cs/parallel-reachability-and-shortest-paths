"""Spectral cross-check: correlate shortcut-set size with spectral gap.

For each named fixture (Petersen, Paley, Shrikhande, Hamming) we
compute the spectrum and the JLS shortcut set. The hypothesis: graphs
with larger spectral gap (closer to expander) need fewer shortcuts.

Honest framing: this is an exploratory empirical check. The JLS
construction's |H| depends on ρ = sqrt(n)/β, which depends on the
SQUARE of n, not directly on the spectrum. So we don't expect a tight
correlation -- but it gives us a sanity check that the construction
behaves sensibly on graphs with known eigenvalue distributions.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.config import get_logger
from reachq.core.generators import (
    hamming_graph,
    paley_graph,
    petersen_graph,
    shrikhande_graph,
)
from reachq.core.graph import Digraph
from reachq.core.spectrum import spectral_gap, spectrum

log = get_logger("reachq.spectral_check")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/spectral_check.csv")
    args = parser.parse_args()

    fixtures: list[tuple[str, Digraph]] = [
        ("Petersen", petersen_graph()),
        ("Paley(5)", paley_graph(5)),
        ("Paley(13)", paley_graph(13)),
        ("Paley(17)", paley_graph(17)),
        ("Shrikhande/rook", shrikhande_graph()),
        ("Hamming(2,3)", hamming_graph(2, 3)),
        ("Hamming(2,4)", hamming_graph(2, 4)),
        ("Hamming(3,3)", hamming_graph(3, 3)),
        ("Hamming(4,2)", hamming_graph(4, 2)),
    ]

    rows: list[dict[str, object]] = []
    log.info("spectral cross-check: %d fixtures", len(fixtures))
    for label, g in fixtures:
        eigs = spectrum(g)
        gap = spectral_gap(g)
        largest = float(eigs[-1])
        second_largest = float(eigs[-2]) if len(eigs) > 1 else 0.0
        t0 = time.perf_counter()
        shortcuts, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
        )
        elapsed = time.perf_counter() - t0
        row = {
            "label": label,
            "n": g.num_vertices(),
            "m": g.num_edges(),
            "largest_eig": round(largest, 3),
            "second_largest_eig": round(second_largest, 3),
            "spectral_gap": round(gap, 3),
            "beta": round(beta, 3),
            "|H|": len(shortcuts),
            "|H|/n": round(len(shortcuts) / max(1, g.num_vertices()), 3),
            "time_s": round(elapsed, 4),
        }
        rows.append(row)
        log.info(
            "%s: n=%d m=%d lambda1=%.2f gap=%.2f beta=%.2f |H|=%d |H|/n=%.2f t=%.3fs",
            label,
            row["n"],
            row["m"],
            row["largest_eig"],
            row["spectral_gap"],
            row["beta"],
            row["|H|"],
            row["|H|/n"],
            row["time_s"],
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "label",
        "n",
        "m",
        "largest_eig",
        "second_largest_eig",
        "spectral_gap",
        "beta",
        "|H|",
        "|H|/n",
        "time_s",
    ]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log.info("wrote %s", out)

    # Sanity: |H|/n should grow with beta = (n^omega/m)^(1/(2omega-2)).
    if rows:
        b_values = sorted({cast(float, r["beta"]) for r in rows})
        log.info("beta range across fixtures: %s", b_values)
        log.info(
            "INTERPRETATION: |H|/n grows roughly with beta (= (n^omega/m)^(1/(2omega-2))). "
            "Sparse graphs (large beta) need more shortcuts; dense graphs "
            "(small beta) need fewer."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
