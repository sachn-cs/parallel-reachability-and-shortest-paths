"""Tests for numpy-based BFS and CSR conversion."""

from __future__ import annotations

import numpy as np

from prspnsd.generators import (
    cycle_graph,
    path_graph,
    random_dag,
)
from prspnsd.graph import Digraph
from prspnsd.numpy_bfs import (
    build_csr_pair,
    csr_reachable_backward,
    csr_reachable_forward,
    should_use_csr,
)
from prspnsd.reachability import bfs_reachability, reverse_bfs_reachability


def test_to_csr_returns_arrays() -> None:  # noqa: D103
    g = path_graph(5)
    indptr, indices, n = g.to_csr()
    assert isinstance(indptr, np.ndarray)
    assert isinstance(indices, np.ndarray)
    assert n == 5
    assert indptr.dtype == np.int64
    assert indices.dtype == np.int64
    assert indptr.shape == (6,)
    assert indices.shape == (4,)
    assert indptr[0] == 0
    assert indptr[-1] == 4


def test_to_csr_neighbors_match_out_edges() -> None:  # noqa: D103
    g = path_graph(5)
    indptr, indices, _ = g.to_csr()
    index_map = {v: i for i, v in enumerate(sorted(g.vertex_set))}  # type: ignore[type-var]
    for v, i in index_map.items():
        neighbors = {int(indices[j]) for j in range(indptr[i], indptr[i + 1])}
        expected = {index_map[w] for w in g.out_edges[v]}
        assert neighbors == expected


def test_csr_reachable_forward_matches_python_bfs() -> None:  # noqa: D103
    g = random_dag(20, edge_probability=0.3, random_seed=42)
    indptr_fwd, indices_fwd, _, _, n, vertices = build_csr_pair(g)
    index_map = {v: i for i, v in enumerate(vertices)}
    for source in vertices:
        src_idx = index_map[source]
        expected = bfs_reachability(g, source)
        result = {vertices[int(i)] for i in csr_reachable_forward(
            indptr_fwd, indices_fwd, src_idx, n,
        )}
        assert result == expected


def test_csr_reachable_backward_matches_python_reverse_bfs() -> None:  # noqa: D103
    g = random_dag(20, edge_probability=0.3, random_seed=42)
    _, _, indptr_rev, indices_rev, n, vertices = build_csr_pair(g)
    index_map = {v: i for i, v in enumerate(vertices)}
    for target in vertices:
        tgt_idx = index_map[target]
        expected = reverse_bfs_reachability(g, target)
        result = {vertices[int(i)] for i in csr_reachable_backward(
            indptr_rev, indices_rev, tgt_idx, n,
        )}
        assert result == expected


def test_csr_reachable_forward_on_cycle() -> None:  # noqa: D103
    g = cycle_graph(10)
    indptr_fwd, indices_fwd, _, _, n, vertices = build_csr_pair(g)
    index_map = {v: i for i, v in enumerate(vertices)}
    source_idx = index_map[0]
    result = csr_reachable_forward(indptr_fwd, indices_fwd, source_idx, n)
    assert len(result) == 10


def test_should_use_csr_threshold() -> None:  # noqa: D103
    g_small = path_graph(10)
    g_large = path_graph(1000)
    assert not should_use_csr(g_small)
    assert should_use_csr(g_large)


def test_build_csr_pair_empty_graph() -> None:  # noqa: D103
    g = Digraph()
    g.add_vertex(0)
    indptr_fwd, indices_fwd, indptr_rev, indices_rev, n, vertices = build_csr_pair(g)
    assert n == 1
    assert len(indices_fwd) == 0
    assert len(indices_rev) == 0
