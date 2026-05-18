"""Deterministic graph generators for experiments.

All generators accept an optional random_seed and use seeded random.Random
instances for reproducibility. None of these generators rely on external
libraries.
"""

from __future__ import annotations

import random

from prspnsd.graph import Digraph, WeightedDigraph


def path_graph(n: int) -> Digraph:
    """Create a directed path on n vertices: 0 → 1 → ... → n-1."""
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


def cycle_graph(n: int) -> Digraph:
    """Create a directed cycle on n vertices: 0 → 1 → ... → n-1 → 0."""
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g


def complete_dag(n: int) -> Digraph:
    """Create a complete DAG: edges i → j for all i < j.

    This graph has m = n(n-1)/2 edges and diameter n-1.
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(i, j)
    return g


def layered_dag(
    layers: list[int],
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a layered DAG with given layer sizes.

    Args:
        layers: List where layers[i] is the number of vertices in layer i.
        edge_probability: Probability of adding an edge between consecutive
            layers. Edges always go from layer i to layer i+1.
        random_seed: Optional seed for reproducibility.

    Returns:
        A Digraph with vertices named (layer, index).
    """
    rng = random.Random(random_seed)
    g = Digraph()
    vertices: list[list[tuple[int, int]]] = []
    for layer_idx, size in enumerate(layers):
        layer_vertices = []
        for j in range(size):
            v = (layer_idx, j)
            g.add_vertex(v)
            layer_vertices.append(v)
        vertices.append(layer_vertices)

    for i in range(len(layers) - 1):
        for u in vertices[i]:
            for v in vertices[i + 1]:
                if rng.random() < edge_probability:
                    g.add_edge(u, v)
    return g


def random_dag(
    n: int,
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a random DAG by topologically ordering vertices and sampling edges.

    Args:
        n: Number of vertices.
        edge_probability: Probability of edge i → j for i < j.
        random_seed: Optional seed.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_probability:
                g.add_edge(i, j)
    return g


def erdos_renyi_digraph(
    n: int,
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a random directed graph (not necessarily acyclic).

    Each ordered pair (u, v) with u != v is included independently with
    probability edge_probability.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < edge_probability:
                g.add_edge(i, j)
    return g


def dense_graph(
    n: int,
    edge_count: int,
    random_seed: int | None = None,
) -> Digraph:
    """Create a dense digraph with exactly edge_count edges.

    The graph is not guaranteed to be acyclic.

    Args:
        n: Number of vertices.
        edge_count: Number of edges (must be ≤ n*(n-1)).
        random_seed: Optional seed.

    Raises:
        ValueError: If edge_count exceeds n*(n-1).
    """
    max_edges = n * (n - 1)
    if edge_count > max_edges:
        raise ValueError(
            f"edge_count {edge_count} exceeds max {max_edges} for n={n}"
        )
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)

    all_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(all_pairs)
    selected = all_pairs[:edge_count]
    for u, v in selected:
        g.add_edge(u, v)
    return g


def graph_with_sccs(
    scc_sizes: list[int],
    inter_edge_probability: float = 0.1,
    random_seed: int | None = None,
) -> Digraph:
    """Create a digraph with specified SCC sizes.

    Each SCC is a directed cycle of the given size. Between SCCs, edges are
    sampled with probability inter_edge_probability, respecting a topological
    ordering of SCCs to keep them distinct.

    Args:
        scc_sizes: List of SCC sizes.
        inter_edge_probability: Probability of adding an edge from SCC i to
            SCC j for i < j.
        random_seed: Optional seed.

    Returns:
        A Digraph where SCCs are guaranteed to match scc_sizes.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    sccs: list[list[int]] = []
    next_vertex = 0
    for size in scc_sizes:
        scc = list(range(next_vertex, next_vertex + size))
        next_vertex += size
        sccs.append(scc)
        for v in scc:
            g.add_vertex(v)
        for idx in range(size):
            u = scc[idx]
            v = scc[(idx + 1) % size]
            g.add_edge(u, v)

    for i in range(len(sccs)):
        for j in range(i + 1, len(sccs)):
            for u in sccs[i]:
                for v in sccs[j]:
                    if rng.random() < inter_edge_probability:
                        g.add_edge(u, v)
    return g


def grid_graph(n: int, m: int) -> WeightedDigraph:
    """Create an n × m grid graph with unit weights.

    Vertices are (i, j) for 0 ≤ i < n, 0 ≤ j < m.
    Edges go right and down with weight 1.
    """
    g = WeightedDigraph()
    for i in range(n):
        for j in range(m):
            g.add_vertex((i, j))
            if i + 1 < n:
                g.add_edge((i, j), (i + 1, j), 1)
            if j + 1 < m:
                g.add_edge((i, j), (i, j + 1), 1)
    return g


def weighted_path_graph(
    n: int,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a weighted directed path on n vertices.

    Edge i → i+1 gets a random integer weight in weight_range.
    """
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        w = rng.randint(lo, hi)
        g.add_edge(i, i + 1, w)
    return g


def weighted_random_dag(
    n: int,
    edge_probability: float = 0.3,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a weighted random DAG.

    Edges i → j for i < j are sampled with probability edge_probability.
    Weights are uniform integers in weight_range.
    """
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_probability:
                g.add_edge(i, j, rng.randint(lo, hi))
    return g


def weighted_dense_graph(
    n: int,
    edge_count: int,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a dense weighted digraph with exactly edge_count edges."""
    max_edges = n * (n - 1)
    if edge_count > max_edges:
        raise ValueError(
            f"edge_count {edge_count} exceeds max {max_edges} for n={n}"
        )
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)

    all_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(all_pairs)
    selected = all_pairs[:edge_count]
    for u, v in selected:
        g.add_edge(u, v, rng.randint(lo, hi))
    return g


def graph_stats(graph: Digraph) -> dict[str, int]:
    """Return basic statistics for a graph."""
    return {
        "n": graph.num_vertices(),
        "m": graph.num_edges(),
        "max_out_degree": max(
            (graph.degree_out(v) for v in graph.vertices()), default=0
        ),
        "max_in_degree": max(
            (graph.degree_in(v) for v in graph.vertices()), default=0
        ),
    }
