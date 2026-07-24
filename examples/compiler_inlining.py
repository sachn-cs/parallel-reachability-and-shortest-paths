"""Compiler inlining example.

Use reachq to identify which basic blocks should be inlined based
on their reachability within the IR. Blocks that many pivots reach
in a small hop count are good inlining candidates (they are
"upstream" of many code paths).

This example is a sketch, not a production compiler.
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.core.graph import Digraph
from reachq.core.algorithm import build_shortcut_set_for_reachability


def build_ir_graph(seed):
    """Build a synthetic IR graph: basic blocks + control flow edges."""
    rng = random.Random(seed)
    g = Digraph()
    # 20 basic blocks, edges from control flow
    n_blocks = 20
    for i in range(n_blocks):
        g.add_vertex(f"block_{i}")
    for i in range(n_blocks):
        for j in range(n_blocks):
            if i != j and rng.random() < 0.15:
                g.add_edge(f"block_{i}", f"block_{j}")
    return g


def recommend_inlining(g, H, beta, max_inlines=3):
    """Recommend up to max_inlines basic blocks for inlining.

    A block is a good inlining candidate if many other blocks reach
    it in <= beta hops. The JLS shortcut set encodes the
    reachability structure of the graph, and pivots in H that reach
    the block are proxies for "incoming edges from many places".
    """
    # Count how many distinct sources reach each block.
    reach_count = {v: 0 for v in g.vertices()}
    for u, v in H:
        reach_count[v] += 1
    # Rank by reach count descending.
    return sorted(g.vertices(), key=lambda v: -reach_count[v])[:max_inlines]


def main():
    g = build_ir_graph(seed=42)
    print(f"IR graph: {g.num_vertices()} blocks, {g.num_edges()} edges")
    H, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"shortcut set: {len(H)} pivots (beta={beta:.2f})")
    inlines = recommend_inlining(g, H, beta)
    print(f"recommended inlining order: {inlines}")


if __name__ == "__main__":
    main()
