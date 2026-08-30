"""Compressed-sparse-row (CSR) adjacency representation.

A CSR pair is two numpy arrays per direction: ``indptr`` (length
``n+1``) and ``indices`` (length ``m``). Reading the outgoing
neighbours of vertex ``i`` is a constant-time slice::

    neighbours_i = indices[indptr[i]:indptr[i+1]]

CSR is the format used by the BFS kernels in :mod:`reachq.core.bfs`
and the experimental Cython/Numba/Rust wrappers in
:mod:`reachq.accel`.

Vertex indices follow the graph's insertion order (see
:mod:`reachq.core.graph`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from reachq.core.graph import Digraph, WeightedDigraph


def build_csr_pair(
    graph: "Digraph",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, tuple[object, ...]]:
    """Build forward and reversed CSR arrays from a :class:`Digraph`.

    Returns:
        ``(indptr_fwd, indices_fwd, indptr_rev, indices_rev, n, idx_to_vertex)``
        where ``idx_to_vertex`` is the graph's insertion-order vertex
        tuple, used to decode computed indices back to vertices.
    """
    n = graph.num_vertices()
    idx_to_vertex: tuple[object, ...] = graph.vertices()
    v_to_idx = graph.index_of_map

    out_counts = np.zeros(n, dtype=np.int64)
    for v, neighbors in graph.out_edges.items():
        out_counts[v_to_idx[v]] = len(neighbors)
    in_counts = np.zeros(n, dtype=np.int64)
    for v, neighbors in graph.in_edges.items():
        in_counts[v_to_idx[v]] = len(neighbors)

    indptr_fwd = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(out_counts, out=indptr_fwd[1:])
    indptr_rev = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(in_counts, out=indptr_rev[1:])

    indices_fwd = np.empty(int(out_counts.sum()), dtype=np.int64)
    indices_rev = np.empty(int(in_counts.sum()), dtype=np.int64)

    cursor_fwd = indptr_fwd[:-1].copy()
    cursor_rev = indptr_rev[:-1].copy()
    for u, neighbors in graph.out_edges.items():
        i = v_to_idx[u]
        for w in neighbors:
            indices_fwd[cursor_fwd[i]] = v_to_idx[w]
            cursor_fwd[i] += 1
    for v, neighbors in graph.in_edges.items():
        j = v_to_idx[v]
        for u in neighbors:
            indices_rev[cursor_rev[j]] = v_to_idx[u]
            cursor_rev[j] += 1

    return (
        indptr_fwd,
        indices_fwd,
        indptr_rev,
        indices_rev,
        n,
        idx_to_vertex,
    )


def digraph_from_csr(
    indptr: np.ndarray,
    indices: np.ndarray,
    idx_to_vertex: tuple[object, ...],
) -> "Digraph":
    """Reconstruct a :class:`Digraph` from a forward CSR pair.

    Args:
        indptr: CSR indptr array of length ``n + 1``.
        indices: CSR indices array of length ``m``.
        idx_to_vertex: Tuple of vertex labels in insertion order.

    Returns:
        A :class:`Digraph` with the same adjacency as the CSR pair.
    """
    from reachq.core.graph import Digraph

    g = Digraph()
    for v in idx_to_vertex:
        g.add_vertex(v)
    for u_idx, v_idx in enumerate(idx_to_vertex):
        start = int(indptr[u_idx])
        end = int(indptr[u_idx + 1])
        for j in range(start, end):
            g.add_edge(v_idx, idx_to_vertex[int(indices[j])])
    return g


def to_unweighted_digraph(graph: "WeightedDigraph") -> "Digraph":
    """Return the underlying unweighted :class:`Digraph`.

    Insertion order is preserved.
    """
    from reachq.core.graph import Digraph

    g = Digraph()
    g.restore_indices(graph.index_of_map, graph.insertion_order)
    for v in graph.insertion_order:
        g.out_edges.setdefault(v, set())
        g.in_edges.setdefault(v, set())
    for u in graph.insertion_order:
        for v in graph.out_edges.get(u, {}):
            if v not in g.out_edges[u]:
                g.out_edges[u].add(v)
                g.in_edges[v].add(u)
                g.edge_count += 1
    return g


def digraph_from_csr_indices(
    graph: "Digraph",
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Convert a :class:`Digraph` to a forward CSR pair.

    Returns:
        ``(indptr, indices, n, m)`` -- the standard CSR arrays plus
        the vertex and edge counts.
    """
    n = graph.num_vertices()
    indptr = np.zeros(n + 1, dtype=np.int64)
    for i, v in enumerate(graph.vertices()):
        indptr[i + 1] = len(graph.out_edges.get(v, set()))
    np.cumsum(indptr, out=indptr)
    m = int(indptr[-1])
    indices = np.empty(m, dtype=np.int64)
    for i, v in enumerate(graph.vertices()):
        start = indptr[i]
        for j, w in enumerate(graph.out_edges.get(v, set())):
            indices[start + j] = graph.index_of(w)
    return indptr, indices, n, m


__all__ = [
    "build_csr_pair",
    "digraph_from_csr",
    "digraph_from_csr_indices",
    "to_unweighted_digraph",
]
