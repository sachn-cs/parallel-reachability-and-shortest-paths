"""Compressed-sparse-row (CSR) adjacency representation for digraphs.

A CSR pair is two numpy arrays per direction: ``indptr`` (length
``n+1``) and ``indices`` (length ``m``). Reading the outgoing
neighbours of vertex ``i`` is a constant-time slice:

    neighbours_i = indices[indptr[i]:indptr[i+1]]

CSR is the format used by the BFS kernels in ``reachq/core/bfs.py``
and the experimental Cython/Numba/Rust wrappers in
``reachq/accel/``.

Vertex indices follow the graph's insertion order (see
:mod:`reachq.core.graph`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from reachq.core.graph import Digraph


def build_csr_pair(
    graph: Digraph,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, tuple[object, ...]]:
    """Build forward and reversed CSR arrays from a Digraph.

    Returns:
        ``(indptr_fwd, indices_fwd, indptr_rev, indices_rev, n, idx_to_vertex)``
        where ``idx_to_vertex`` is the graph's insertion-order vertex
        tuple, used to decode computed indices back to vertices.
    """
    n = graph.num_vertices()
    idx_to_vertex: tuple[object, ...] = graph.vertices()
    v_to_idx = graph._index_of  # noqa: SLF001 — internal but stable

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
