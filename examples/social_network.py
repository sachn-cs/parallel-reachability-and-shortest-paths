"""Social network reachability example.

Use reachq to compute the reachability structure of a SNAP social
network (e.g., cit-HepPh or p2p-Gnutella31) and report statistics
on the shortcut-set size and the beta-hopbound.

This example is a sketch, not a full social network analyzer.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.core.shortcut import build_shortcut_set_for_reachability


def main():
    try:
        from reachq.core.generators import load_dataset
    except ImportError:
        print("SNAP loader not available; skipping")
        return
    g = load_dataset("cit-HepPh")
    print(f"SNAP cit-HepPh: {g.num_vertices()} nodes, {g.num_edges()} edges")
    H, beta, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"shortcut set: {len(H)} shortcuts (beta={beta:.2f})")
    print(f"|H|/|E| ratio: {len(H) / max(1, g.num_edges()):.2f}")


if __name__ == "__main__":
    main()
