"""Numpy-based BFS for large graphs.

Uses CSR adjacency representation for ~10-100x speedup over Python BFS
on sparse graphs.
"""

from __future__ import annotations

import numpy as np

MIN_CSR_SIZE = 500


def csr_reachable_forward(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """BFS forward on CSR adjacency. Returns array of reachable vertex indices."""
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
        within = np.arange(total, dtype=np.int64)
        pos_offsets = np.empty(frontier.size + 1, dtype=np.int64)
        pos_offsets[0] = 0
        np.cumsum(counts, out=pos_offsets[1:])
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
    indptr_rev: np.ndarray,
    indices_rev: np.ndarray,
    source: int,
    n: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """BFS backward on reversed CSR adjacency."""
    return csr_reachable_forward(
        indptr_rev, indices_rev, source, n, max_depth=max_depth
    )


def csr_bfs_layered(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    max_depth: int,
) -> tuple[set[int], list[set[int]]]:
    """BFS up to `max_depth` hops, returning (all_visited, per_layer_sets)."""
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


def should_use_csr(graph_num_vertices: int) -> bool:
    """Decide whether CSR numpy BFS is worth the conversion overhead."""
    return graph_num_vertices >= MIN_CSR_SIZE
