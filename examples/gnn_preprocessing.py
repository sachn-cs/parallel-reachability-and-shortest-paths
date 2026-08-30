"""GNN preprocessing example.

Use reachq to augment a citation graph with JLS shortcuts, then
save the result as a torch_geometric-compatible file.

This example is intentionally short: it's a sketch, not a
production pipeline.
"""

import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.core.shortcut import build_shortcut_set_for_reachability
from reachq.core.graph import Digraph
from reachq.core.reachability import parallel_bfs


def build_citation_graph(n_papers, density, seed):
    """Build a synthetic citation graph as a Digraph."""
    rng = random.Random(seed)
    g = Digraph()
    for i in range(n_papers):
        g.add_vertex(i)
    for i in range(n_papers):
        for j in range(i + 1, n_papers):
            if rng.random() < density:
                # Citations are directional: i cites j (i -> j)
                g.add_edge(i, j)
    return g


def to_pyg_data(g, H, beta):
    """Convert a Digraph + shortcut set to a torch_geometric Data
    object. Saves to disk for downstream GNN training.
    """
    try:
        import torch
    except ImportError:
        print("torch not installed; skipping")
        return
    try:
        from torch_geometric.data import Data
    except ImportError:
        print("torch_geometric not installed; skipping")
        return
    import numpy as np

    n = g.num_vertices()
    # Edges
    if H:
        edge_set = {(u, v) for u, v in g.edges()} | {(u, v) for u, v in H}
    else:
        edge_set = {(u, v) for u, v in g.edges()}
    edge_index = np.array(sorted(edge_set), dtype=np.int64).T

    data = Data(
        x=torch.eye(n, dtype=torch.float32),
        edge_index=torch.tensor(edge_index, dtype=torch.long),
        num_nodes=n,
    )
    data.beta = beta
    out_path = "examples/_gnn_citation_data.pt"
    torch.save(data, out_path)
    print(f"saved PyG-compatible data to {out_path}")
    return out_path


def main():
    n = 200
    density = 0.02
    g = build_citation_graph(n, density, seed=42)
    print(f"citation graph: {g.num_vertices()} papers, {g.num_edges()} citations")
    H, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"shortcut set: {len(H)} shortcuts (beta={beta:.2f})")
    # Verify soundness
    for s in range(0, n, 50):
        from reachq.core.reachability import bfs_reachability

        if bfs_reachability(g, s) != parallel_bfs(g, s, H):
            print(f"soundness VIOLATED at {s}")
            return
    print("reachability preserved for all sampled sources")
    to_pyg_data(g, H, beta)


if __name__ == "__main__":
    main()
