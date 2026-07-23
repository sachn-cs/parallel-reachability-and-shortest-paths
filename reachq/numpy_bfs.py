"""Numpy-based BFS for large graphs.

Uses CSR adjacency representation for ~10-100x speedup over Python BFS
on sparse graphs. Falls back to Python BFS for small graphs where the
CSR conversion overhead dominates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from prspnsd.graph import Digraph

_MIN_CSR_SIZE = 500


def csr_reachable_forward(
    indptr: np.ndarray, indices: np.ndarray, source: int, n: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """BFS forward on CSR adjacency. Returns array of reachable vertex indices.

    If `max_depth` is set, stop the frontier expansion once depth reaches it
    (vertices beyond are not reachable within the hopbound).
    """
    visited = np.zeros(n, dtype=bool)
    visited[source] = True
    frontier = np.array([source], dtype=np.int64)
    depth = 0
    while frontier.size > 0:
        if max_depth is not None and depth >= max_depth:
            break
        starts = indptr[frontier]
        ends = indptr[frontier + 1]
        counts = ends - starts
        total = int(counts.sum())
        if total == 0:
            break
        # Vectorised gather of neighbor positions. For each frontier
        # vertex i we want positions in [starts[i], starts[i] + counts[i]).
        # Build it with cumsum + per-vertex index, no Python loop.
        within = np.arange(total, dtype=np.int64)
        # Per-vertex start offset within the flattened positions array.
        pos_offsets = np.empty(frontier.size + 1, dtype=np.int64)
        pos_offsets[0] = 0
        np.cumsum(counts, out=pos_offsets[1:])
        # For each within-index, which frontier vertex it belongs to.
        vert_idx = np.repeat(np.arange(frontier.size), counts)
        positions = starts[vert_idx] + (within - pos_offsets[vert_idx])
        neighbors = indices[positions]
        new_neighbors = neighbors[~visited[neighbors]]
        if new_neighbors.size == 0:
            break
        visited[new_neighbors] = True
        frontier = np.unique(new_neighbors)
        depth += 1
    return np.where(visited)[0]


def csr_reachable_backward(
    indptr_rev: np.ndarray, indices_rev: np.ndarray, source: int, n: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """BFS backward on reversed CSR adjacency. Returns array of vertex indices that reach source."""
    return csr_reachable_forward(indptr_rev, indices_rev, source, n, max_depth=max_depth)


def csr_bfs_layered(
    indptr: np.ndarray, indices: np.ndarray, source: int, n: int,
    max_depth: int,
) -> tuple[set[int], list[set[int]]]:
    """BFS up to `max_depth` hops, returning (all_visited, per_layer_sets).

    Per-layer sets are the vertex *indices* (not original labels) at each
    BFS depth 0..max_depth-1, inclusive of the source at depth 0.
    Useful when a caller wants to bound reachability per hop budget.
    """
    visited = np.zeros(n, dtype=bool)
    visited[source] = True
    layers: list[set[int]] = [{source}]
    frontier = np.array([source], dtype=np.int64)
    for _ in range(max_depth):
        if frontier.size == 0:
            break
        starts = indptr[frontier]
        ends = indptr[frontier + 1]
        counts = ends - starts
        total = int(counts.sum())
        if total == 0:
            break
        positions = np.repeat(starts, counts) + np.arange(total, dtype=np.int64)
        neighbors = indices[positions]
        new_neighbors = neighbors[~visited[neighbors]]
        if new_neighbors.size == 0:
            break
        visited[new_neighbors] = True
        frontier = np.unique(new_neighbors)
        layers.append(set(new_neighbors.tolist()))
    return set(np.where(visited)[0].tolist()), layers


def csr_to_index_map(graph_vertex_set: set[object]) -> tuple[dict[object, int], list[object]]:
    """Build bijection from vertex objects to int indices."""
    vertices = list(graph_vertex_set)
    index_map = {v: i for i, v in enumerate(vertices)}
    return index_map, vertices


def build_csr_pair(
    graph: Digraph,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, list[object]]:
    """Build forward and reversed CSR arrays from a Digraph.

    Returns:
        (indptr_fwd, indices_fwd, indptr_rev, indices_rev, n, index_to_vertex)
    """
    index_map, vertices = csr_to_index_map(graph.vertex_set)
    n = len(vertices)

    out_counts = np.zeros(n, dtype=np.int64)
    for v, neighbors in graph.out_edges.items():
        out_counts[index_map[v]] = len(neighbors)
    in_counts = np.zeros(n, dtype=np.int64)
    for v, neighbors in graph.in_edges.items():
        in_counts[index_map[v]] = len(neighbors)

    indptr_fwd = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(out_counts, out=indptr_fwd[1:])
    indptr_rev = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(in_counts, out=indptr_rev[1:])

    indices_fwd = np.empty(int(out_counts.sum()), dtype=np.int64)
    indices_rev = np.empty(int(in_counts.sum()), dtype=np.int64)

    cursor_fwd = indptr_fwd[:-1].copy()
    cursor_rev = indptr_rev[:-1].copy()
    for u, neighbors in graph.out_edges.items():
        i = index_map[u]
        for w in neighbors:
            indices_fwd[cursor_fwd[i]] = index_map[w]
            cursor_fwd[i] += 1
    for v, neighbors in graph.in_edges.items():
        j = index_map[v]
        for u in neighbors:
            indices_rev[cursor_rev[j]] = index_map[u]
            cursor_rev[j] += 1

    return indptr_fwd, indices_fwd, indptr_rev, indices_rev, n, vertices


def should_use_csr(graph: Digraph) -> bool:
    """Decide whether CSR numpy BFS is worth the conversion overhead."""
    return graph.num_vertices() >= _MIN_CSR_SIZE
