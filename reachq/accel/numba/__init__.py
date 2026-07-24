"""Numba-JIT accelerated kernels.

This module provides Numba-JIT-compiled kernels for the
CSR-based BFS and Dijkstra inner loops. The Numba kernels use
``@njit`` and ``fastmath=True`` for vectorised arithmetic where
applicable; the GIL is released during the JIT'd loops.

If Numba is not installed, the wrapper functions fall back to the
pure-Python implementations in :mod:`reachq.core`. Numba can be
installed with ``pip install numba``; it adds a JIT compile cost
on first call (typically a few seconds per kernel) but the
compiled kernels execute 10-50x faster than pure Python on
typical inputs.

Public API (mirrors the Cython wrappers):

- :func:`njit_bfs_forward` — forward BFS over a CSR adjacency.
- :func:`njit_dijkstra` — Dijkstra from a single source.
- :func:`is_numba_available` — True if Numba is installed.
"""

from __future__ import annotations

import numpy as np

from reachq.core.bfs import csr_reachable_forward
from reachq.core.shortest_paths import dijkstra


_numba_available = False
try:
    import numba  # type: ignore[import-not-found]

    _numba_available = True
except ImportError:
    _numba_available = False


if _numba_available:
    @numba.njit(cache=True, fastmath=True, boundscheck=False)
    def _jit_bfs_forward_kernel(
        indptr: np.ndarray,
        indices: np.ndarray,
        source: int,
        n: int,
        max_depth: int,
    ) -> np.ndarray:
        """JIT-compiled forward BFS. Releases the GIL."""
        reached = np.zeros(n, dtype=numba.boolean)
        if source < 0 or source >= n:
            return reached
        reached[source] = True
        frontier = np.empty(n, dtype=np.int64)
        next_frontier = np.empty(n, dtype=np.int64)
        frontier[0] = source
        frontier_size = 1
        for _depth in range(max_depth):
            if frontier_size == 0:
                break
            next_size = 0
            for i in range(frontier_size):
                u = frontier[i]
                start = indptr[u]
                end = indptr[u + 1]
                for j in range(start, end):
                    v = indices[j]
                    if not reached[v]:
                        reached[v] = True
                        next_frontier[next_size] = v
                        next_size += 1
            for i in range(next_size):
                frontier[i] = next_frontier[i]
            frontier_size = next_size
        return reached

    @numba.njit(cache=True, fastmath=True, boundscheck=False)
    def _jit_dijkstra_kernel(
        indptr: np.ndarray,
        indices: np.ndarray,
        weights: np.ndarray,
        source: int,
        n: int,
    ) -> np.ndarray:
        """JIT-compiled Dijkstra with inline binary heap. Releases the GIL."""
        dist = np.full(n, np.inf, dtype=np.float64)
        if source < 0 or source >= n:
            return dist
        # Inline binary min-heap.
        heap_dist = np.empty(n + 16, dtype=np.float64)
        heap_vertex = np.empty(n + 16, dtype=np.int64)
        heap_pos = np.full(n, -1, dtype=np.int64)
        heap_size = 0
        dist[source] = 0.0
        heap_dist[0] = 0.0
        heap_vertex[0] = source
        heap_pos[source] = 0
        heap_size = 1
        while heap_size > 0:
            u = heap_vertex[0]
            du = heap_dist[0]
            heap_size -= 1
            if heap_size > 0:
                heap_dist[0] = heap_dist[heap_size]
                heap_vertex[0] = heap_vertex[heap_size]
                heap_pos[heap_vertex[0]] = 0
                k = 0
                while True:
                    child = 2 * k + 1
                    if child >= heap_size:
                        break
                    if child + 1 < heap_size and heap_dist[child + 1] < heap_dist[child]:
                        child += 1
                    if heap_dist[k] <= heap_dist[child]:
                        break
                    heap_dist[k], heap_dist[child] = heap_dist[child], heap_dist[k]
                    heap_vertex[k], heap_vertex[child] = heap_vertex[child], heap_vertex[k]
                    heap_pos[heap_vertex[k]] = k
                    heap_pos[heap_vertex[child]] = child
                    k = child
            heap_pos[u] = -2
            j = indptr[u]
            while j < indptr[u + 1]:
                v = indices[j]
                alt = du + weights[j]
                if alt < dist[v]:
                    dist[v] = alt
                    pos_v = heap_pos[v]
                    if pos_v == -2:
                        heap_dist[heap_size] = alt
                        heap_vertex[heap_size] = v
                        heap_pos[v] = heap_size
                        heap_size += 1
                        k = heap_size - 1
                        while k > 0:
                            parent = (k - 1) // 2
                            if heap_dist[parent] <= heap_dist[k]:
                                break
                            heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                            heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                            heap_pos[heap_vertex[parent]] = parent
                            heap_pos[heap_vertex[k]] = k
                            k = parent
                    elif pos_v >= 0:
                        k = pos_v
                        heap_dist[k] = alt
                        while k > 0:
                            parent = (k - 1) // 2
                            if heap_dist[parent] <= heap_dist[k]:
                                break
                            heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                            heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                            heap_pos[heap_vertex[parent]] = parent
                            heap_pos[heap_vertex[k]] = k
                            k = parent
                    else:
                        heap_dist[heap_size] = alt
                        heap_vertex[heap_size] = v
                        heap_pos[v] = heap_size
                        heap_size += 1
                        k = heap_size - 1
                        while k > 0:
                            parent = (k - 1) // 2
                            if heap_dist[parent] <= heap_dist[k]:
                                break
                            heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                            heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                            heap_pos[heap_vertex[parent]] = parent
                            heap_pos[heap_vertex[k]] = k
                            k = parent
                j += 1
        return dist


def njit_bfs_forward(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    *,
    max_depth: int = 1 << 30,
) -> np.ndarray:
    """Forward BFS over a CSR adjacency (Numba-JIT).

    Identical API to :func:`reachq.accel.cython.bfs.cy_bfs_forward`.
    Falls back to :func:`reachq.core.bfs.csr_reachable_forward`
    when Numba is not installed.
    """
    if _numba_available:
        result_ext = _jit_bfs_forward_kernel(indptr, indices, source, n, max_depth)
        if isinstance(result_ext, np.ndarray):
            return result_ext
    # Fallback: pure-Python returns the indices of reached vertices;
    # convert to a boolean mask of length n.
    reached_indices = csr_reachable_forward(
        indptr, indices, source, n, max_depth=max_depth
    )
    out = np.zeros(n, dtype=bool)
    out[reached_indices] = True
    return out


def njit_dijkstra(
    indptr: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
    source: int,
    n: int,
) -> np.ndarray:
    """Dijkstra from ``source`` over a weighted CSR adjacency (Numba-JIT).

    Falls back to :func:`reachq.core.shortest_paths.dijkstra` when
    Numba is not installed.
    """
    if _numba_available:
        result = _jit_dijkstra_kernel(indptr, indices, weights, source, n)
        if isinstance(result, np.ndarray):
            return result
    from reachq.core.graph import WeightedDigraph

    g = WeightedDigraph()
    for u in range(n):
        start = int(indptr[u])
        end = int(indptr[u + 1])
        for j in range(start, end):
            v = int(indices[j])
            w = float(weights[j])
            if v not in g.vertex_set:
                g.add_vertex(v)
            if u not in g.vertex_set:
                g.add_vertex(u)
            g.add_edge(u, v, int(w))
    result = dijkstra(g, source)
    out = np.full(n, np.inf, dtype=np.float64)
    for v_obj, d in result.items():
        v = int(str(v_obj))
        if 0 <= v < n:
            out[v] = d
    return out


def is_numba_available() -> bool:
    """Return True if Numba is installed."""
    return _numba_available


__all__ = ["njit_bfs_forward", "njit_dijkstra", "is_numba_available"]