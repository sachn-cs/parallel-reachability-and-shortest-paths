"""RAG reranking example.

Use reachq to identify high-reachability passages (those reached by
many JLS pivots in the citation graph) and treat those as
relevance-prioritised candidates for a RAG (retrieval-augmented
generation) pipeline.

This example is a sketch, not a production RAG system.
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.graph import Digraph
from reachq.reachability import bfs_reachability
from reachq.shortcut_set import build_shortcut_set_for_reachability


def build_passage_graph(n_passages, density, seed):
    """Build a synthetic passage-citation graph as a Digraph."""
    rng = random.Random(seed)
    g = Digraph()
    for i in range(n_passages):
        g.add_vertex(i)
    for i in range(n_passages):
        for j in range(n_passages):
            if i != j and rng.random() < density:
                g.add_edge(i, j)
    return g


def rank_by_pivot_reach(g, H, query):
    """Rank passages by the number of JLS pivots that can reach them.

    Passages that many pivots reach in beta hops are more likely to
    be relevant for queries that traverse the same pivot structure.
    """
    # For each pivot, compute its reachable set in G + H.
    pivot_reach = {}
    for u, v in H:
        pivot_reach.setdefault(u, set()).add(v)
    # For each query, count how many pivots reach each target.
    reach_count = {p: 0 for p in g.vertices()}
    for pivot, target in H:
        # Naive: just count each target once per pivot.
        reach_count[target] += 1
    # Sort by reach count descending.
    return sorted(g.vertices(), key=lambda v: -reach_count[v])


def main():
    n = 100
    density = 0.05
    g = build_passage_graph(n, density, seed=42)
    print(f"passage graph: {g.num_vertices()} passages, {g.num_edges()} citations")
    H, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"shortcut set: {len(H)} shortcuts (beta={beta:.2f})")
    query = 0
    ranking = rank_by_pivot_reach(g, H, query)
    print(f"top 10 passages for query {query}: {ranking[:10]}")
    # The 'relevance' signal here is the number of JLS pivots that
    # reach each passage. This is a simple proxy for a true relevance
    # model.


if __name__ == "__main__":
    main()
