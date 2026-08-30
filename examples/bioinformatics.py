"""Bioinformatics example.

Use reachq to compute reachability in a synthetic protein-protein
interaction network (PPI) and report which 'hub' proteins are
reachable from a query protein in a small hop count.

This example is a sketch, not a real bioinformatics pipeline.
"""

import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.core.shortcut import build_shortcut_set_for_reachability
from reachq.core.graph import Digraph
from reachq.core.reachability import parallel_bfs


def build_ppi_graph(n_proteins, density, seed):
    """Build a synthetic protein-protein interaction network as a
    directed graph (u -> v means u activates v)."""
    rng = random.Random(seed)
    g = Digraph()
    for i in range(n_proteins):
        g.add_vertex(f"P{i}")
    for i in range(n_proteins):
        for j in range(n_proteins):
            if i != j and rng.random() < density:
                g.add_edge(f"P{i}", f"P{j}")
    return g


def find_hubs(g, H, beta, query):
    """Find proteins reachable from `query` in <= beta hops. These
    are potential 'downstream hubs' of the query protein."""
    reach = parallel_bfs(g, query, H)
    # The query itself is reachable (always).
    return sorted(reach - {query})


def main():
    n = 100
    density = 0.05
    g = build_ppi_graph(n, density, seed=42)
    print(f"PPI: {g.num_vertices()} proteins, {g.num_edges()} interactions")
    H, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"shortcut set: {len(H)} shortcuts (beta={beta:.2f})")
    query = "P0"
    hubs = find_hubs(g, H, beta, query)
    print(f"downstream hubs from {query} (within {beta:.0f} hops): {hubs[:10]}")


if __name__ == "__main__":
    main()
