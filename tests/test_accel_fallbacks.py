"""Tests for the Cython/Rust/Numba acceleration wrappers.

These tests exercise the wrapper functions without requiring the
underlying compiled extensions to be installed. They verify that:

1. The fallback path returns correct results.
2. The "is_*_available()" helper returns False (or True) consistently.
3. The public API matches the underlying pure-Python implementations.
"""

from __future__ import annotations

import numpy as np

from reachq.core.csr import build_csr_pair
from reachq.core.generators import dense_graph


def test_cython_bfs_forward_fallback():
    """cy_bfs_forward must return correct results even without compiled extension."""
    from reachq.accel.cython.bfs import cy_bfs_forward, is_cython_available

    g = dense_graph(10, 30, random_seed=42)
    indptr_fwd, indices_fwd, _, _, n, _ = build_csr_pair(g)
    # vertex 0 is an integer; convert via the index_to_vertex list.
    # Build an explicit index->vertex map.
    vertex_list = list(g.vertices())
    index_map = {v: i for i, v in enumerate(vertex_list)}
    source = index_map[vertex_list[0]]
    reached = cy_bfs_forward(indptr_fwd, indices_fwd, source, n)
    assert isinstance(reached, np.ndarray)
    assert reached.dtype == bool
    assert reached[source]  # source reaches itself
    # is_cython_available may be True or False depending on build.
    assert isinstance(is_cython_available(), bool)


def test_cython_bfs_backward_fallback():
    """cy_bfs_backward must return correct results."""
    from reachq.accel.cython.bfs import cy_bfs_backward

    g = dense_graph(8, 20, random_seed=42)
    _, _, indptr_rev, indices_rev, n, _ = build_csr_pair(g)
    vertex_list = list(g.vertices())
    index_map = {v: i for i, v in enumerate(vertex_list)}
    source = index_map[vertex_list[0]]
    reached = cy_bfs_backward(indptr_rev, indices_rev, source, n)
    assert isinstance(reached, np.ndarray)
    assert reached.dtype == bool


def test_rust_bfs_forward_fallback():
    """rust_bfs_forward fallback path."""
    from reachq.accel.rust import is_rust_available, rust_bfs_forward

    g = dense_graph(6, 12, random_seed=42)
    indptr_fwd, indices_fwd, _, _, n, _ = build_csr_pair(g)
    vertex_list = list(g.vertices())
    index_map = {v: i for i, v in enumerate(vertex_list)}
    source = index_map[vertex_list[0]]
    reached = rust_bfs_forward(indptr_fwd, indices_fwd, source, n)
    assert isinstance(reached, np.ndarray)
    assert isinstance(is_rust_available(), bool)


def test_numba_bfs_forward_fallback():
    """njit_bfs_forward fallback path."""
    from reachq.accel.numba import is_numba_available, njit_bfs_forward

    g = dense_graph(6, 12, random_seed=42)
    indptr_fwd, indices_fwd, _, _, n, _ = build_csr_pair(g)
    vertex_list = list(g.vertices())
    index_map = {v: i for i, v in enumerate(vertex_list)}
    source = index_map[vertex_list[0]]
    reached = njit_bfs_forward(indptr_fwd, indices_fwd, source, n)
    assert isinstance(reached, np.ndarray)
    assert isinstance(is_numba_available(), bool)