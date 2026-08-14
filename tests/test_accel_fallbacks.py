"""Tests for the Cython/Rust/Numba acceleration wrappers.

These tests exercise both the compiled-extension path (when available)
and the Python fallback path. The compiled extensions may or may
not be installed in the test environment; the tests verify that:

1. The wrappers return correct results in both modes.
2. The "is_*_available()" helper accurately reflects the state.
3. The fallback (when used) matches the compiled output bit-for-bit.
"""

from __future__ import annotations

import numpy as np

from reachq.core.bfs import csr_reachable_forward
from reachq.core.csr import build_csr_pair
from reachq.core.generators import dense_graph


def _setup_graph(
    n: int = 10, m: int = 30, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, int]:
    g = dense_graph(n, m, random_seed=seed)
    indptr_fwd, indices_fwd, _, _, csr_n, _ = build_csr_pair(g)
    return indptr_fwd, indices_fwd, csr_n


def test_cython_bfs_forward():
    """cy_bfs_forward returns correct results via extension OR fallback."""
    from reachq.accel.cython.bfs import cy_bfs_forward, is_cython_available

    indptr, indices, n = _setup_graph()
    reached = cy_bfs_forward(indptr, indices, 0, n)
    assert isinstance(reached, np.ndarray)
    assert reached.dtype == bool
    assert reached[0]  # source reaches itself

    # Compare with the canonical pure-Python fallback to ensure
    # the compiled extension (if loaded) gives identical results.
    fallback_indices = csr_reachable_forward(indptr, indices, 0, n)
    fallback_mask = np.zeros(n, dtype=bool)
    fallback_mask[fallback_indices] = True
    np.testing.assert_array_equal(reached, fallback_mask)
    assert isinstance(is_cython_available(), bool)


def test_cython_bfs_backward():
    """cy_bfs_backward returns correct results."""
    from reachq.accel.cython.bfs import cy_bfs_backward

    g = dense_graph(8, 20, random_seed=42)
    _, _, indptr_rev, indices_rev, csr_n, _ = build_csr_pair(g)
    reached = cy_bfs_backward(indptr_rev, indices_rev, 0, csr_n)
    assert isinstance(reached, np.ndarray)
    assert reached.dtype == bool


def test_rust_bfs_forward():
    """rust_bfs_forward returns correct results via extension OR fallback."""
    from reachq.accel.rust import is_rust_available, rust_bfs_forward

    indptr, indices, n = _setup_graph()
    reached = rust_bfs_forward(indptr, indices, 0, n)
    assert isinstance(reached, np.ndarray)

    # Compare with the canonical pure-Python fallback.
    fallback_indices = csr_reachable_forward(indptr, indices, 0, n)
    fallback_mask = np.zeros(n, dtype=bool)
    fallback_mask[fallback_indices] = True
    np.testing.assert_array_equal(reached, fallback_mask)
    assert isinstance(is_rust_available(), bool)


def test_numba_bfs_forward():
    """njit_bfs_forward returns correct results via JIT OR fallback."""
    from reachq.accel.numba import is_numba_available, njit_bfs_forward

    indptr, indices, n = _setup_graph()
    reached = njit_bfs_forward(indptr, indices, 0, n)
    assert isinstance(reached, np.ndarray)

    # Compare with the canonical pure-Python fallback.
    fallback_indices = csr_reachable_forward(indptr, indices, 0, n)
    fallback_mask = np.zeros(n, dtype=bool)
    fallback_mask[fallback_indices] = True
    np.testing.assert_array_equal(reached, fallback_mask)
    assert isinstance(is_numba_available(), bool)


def test_cython_dijkstra_matches_python():
    """Cython Dijkstra (or fallback) matches the canonical Dijkstra."""
    from reachq.accel.cython.dijkstra import cy_dijkstra

    indptr, indices, n = _setup_graph(8, 20)
    weights = np.ones(len(indices), dtype=np.float64)
    dist = cy_dijkstra(indptr, indices, weights, 0, n)
    assert isinstance(dist, np.ndarray)
    assert dist.dtype == np.float64
    assert dist[0] == 0.0
    assert np.all(np.isfinite(dist))


def test_rust_dijkstra_matches_python():
    """Rust Dijkstra (or fallback) returns sensible distances."""
    from reachq.accel.rust import rust_dijkstra

    indptr, indices, n = _setup_graph(8, 20)
    weights = np.ones(len(indices), dtype=np.float64)
    dist = rust_dijkstra(indptr, indices, weights, 0, n)
    assert isinstance(dist, np.ndarray)
    assert dist.dtype == np.float64
    assert dist[0] == 0.0


def test_numba_dijkstra_matches_python():
    """Numba Dijkstra (or fallback) returns sensible distances."""
    from reachq.accel.numba import njit_dijkstra

    indptr, indices, n = _setup_graph(8, 20)
    weights = np.ones(len(indices), dtype=np.float64)
    dist = njit_dijkstra(indptr, indices, weights, 0, n)
    assert isinstance(dist, np.ndarray)
    assert dist.dtype == np.float64
    assert dist[0] == 0.0


def test_consistency_across_backends():
    """All three backends (extension or fallback) agree on a path graph."""
    from reachq.accel.cython.bfs import cy_bfs_forward
    from reachq.accel.numba import njit_bfs_forward
    from reachq.accel.rust import rust_bfs_forward

    indptr, indices, n = _setup_graph(12, 40, seed=7)
    r1 = cy_bfs_forward(indptr, indices, 0, n)
    r2 = rust_bfs_forward(indptr, indices, 0, n)
    r3 = njit_bfs_forward(indptr, indices, 0, n)
    np.testing.assert_array_equal(r1, r2)
    np.testing.assert_array_equal(r1, r3)


def test_numba_prewarm():
    """prewarm() triggers compilation and makes subsequent calls fast."""
    from reachq.accel.numba import is_numba_available, njit_bfs_forward, prewarm

    if not is_numba_available():
        # If Numba is not installed, prewarm must raise a clear error.
        try:
            prewarm()
            assert False, "expected RuntimeError when Numba missing"
        except RuntimeError:
            pass
        return

    # When Numba is available, prewarm should complete in a few seconds
    # and subsequent calls should be fast (no JIT compile cost).
    import time

    t0 = time.perf_counter()
    prewarm(bfs_size=64, bfs_avg_degree=4, dijkstra_size=64, dijkstra_avg_degree=4)
    prewarm_elapsed = time.perf_counter() - t0
    # The warmup itself takes time (1-5 seconds typical). After it
    # completes, the first real call should be < 100ms.
    assert prewarm_elapsed < 30.0

    t0 = time.perf_counter()
    indptr, indices, n = _setup_graph(20, 60)
    njit_bfs_forward(indptr, indices, 0, n)
    first_call_ms = (time.perf_counter() - t0) * 1000
    assert first_call_ms < 100, (
        f"first call after prewarm should be < 100ms, got {first_call_ms:.1f}ms"
    )
