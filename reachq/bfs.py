"""Numpy-based BFS for large graphs.

Uses CSR adjacency representation for ~10-100x speedup over Python
BFS on sparse graphs. The forward-reachability and layered
variants are the workhorses of the JLS shortcut-set construction;
the backward variant is used by the r-ball helper.

These helpers are also the pure-Python fallback kernels that the
Cython / Numba / Rust wrappers in ``reachq/accel/`` import and
fall back to when the compiled extension is unavailable.
"""

from __future__ import annotations

import numpy as np

MIN_CSR_SIZE = 500
"""Vertex count threshold above which the CSR numpy BFS is faster
than the deque-based Python BFS despite the conversion overhead."""


def csr_reachable_forward(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """BFS forward on a CSR adjacency, returning reachable vertex indices.

    Args:
        indptr: Forward CSR indptr array of length ``n + 1``.
        indices: Forward CSR indices array of length ``m``.
        source: Source vertex index (0 <= source < n).
        n: Number of vertices.
        max_depth: If set, stop the BFS after this many hops.

    Returns:
        Sorted 1-D int64 array of vertex indices reachable from
        ``source`` (inclusive).
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
    """BFS backward on a reversed CSR adjacency.

    Equivalent to ``csr_reachable_forward`` applied to the reversed
    edges: the result is the set of vertices that can reach
    ``source`` (i.e. the reverse-reachable set).

    Args:
        indptr_rev: Reverse CSR indptr array of length ``n + 1``.
        indices_rev: Reverse CSR indices array of length ``m``.
        source: Source vertex index (0 <= source < n).
        n: Number of vertices.
        max_depth: If set, stop the BFS after this many hops.

    Returns:
        Sorted 1-D int64 array of vertex indices that can reach
        ``source`` (inclusive).
    """
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
    """BFS up to ``max_depth`` hops, returning the visited set and per-layer sets.

    Args:
        indptr: Forward CSR indptr array of length ``n + 1``.
        indices: Forward CSR indices array of length ``m``.
        source: Source vertex index (0 <= source < n).
        n: Number of vertices.
        max_depth: Maximum number of hops to expand.

    Returns:
        A tuple ``(all_visited, layers)`` where ``all_visited`` is
        the set of reachable vertices and ``layers[i]`` is the set
        of vertices discovered at hop ``i`` (negative vertices are
        placed in the first layer ``layers[0] = {source}``).
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


def should_use_csr(graph_num_vertices: int) -> bool:
    """Return True iff CSR numpy BFS is worth the conversion overhead.

    Below ``MIN_CSR_SIZE`` the conversion overhead dominates the
    BFS cost; the deque-based Python BFS is faster.

    Args:
        graph_num_vertices: Number of vertices in the graph.

    Returns:
        True if ``graph_num_vertices >= MIN_CSR_SIZE``.
    """
    return graph_num_vertices >= MIN_CSR_SIZE
