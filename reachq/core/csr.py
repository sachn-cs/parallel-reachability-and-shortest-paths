"""Compressed-sparse-row (CSR) adjacency representation for digraphs.

A CSR pair is two numpy arrays per direction: ``indptr`` (length
``n+1``) and ``indices`` (length ``m``). Reading the outgoing
neighbours of vertex ``i`` is a constant-time slice:

    neighbours_i = indices[indptr[i]:indptr[i+1]]

CSR is the format used by the BFS kernels in ``reachq/core/bfs.py``
and the experimental Cython/Numba/Rust wrappers in
``reachq/accel/``. The conversion from a Digraph allocates
``indptr_fwd``/``indices_fwd`` (forward edges) and the
indptr_rev/indices_rev (reverse edges) in one pass so the BFS
also has the backward view at hand.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from reachq.core.graph import Digraph


def csr_to_index_map(
    graph_vertex_set: set[object],
) -> tuple[dict[object, int], list[object]]:
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
