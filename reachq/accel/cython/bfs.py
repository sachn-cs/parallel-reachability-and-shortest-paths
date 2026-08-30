"""Cython-accelerated BFS kernel.

This module is the public Python entry point for the CSR-based BFS
kernels in :file:`bfs.pyx`. When the Cython extension has been
compiled (via ``python setup.py build_ext --inplace`` from this
directory, or installed via the ``reachq[accel]`` wheel), the
functions dispatch to the compiled code with the GIL released for
parallel execution. When the extension is unavailable, they fall
back to a pure-Python implementation that yields identical results.

The fallback uses :func:`reachq.core.bfs.csr_reachable_forward` /
:func:`csr_reachable_backward` internally.

Public API:

- :func:`cy_bfs_forward` — forward BFS over a CSR adjacency.
- :func:`cy_bfs_backward` — backward BFS over the reversed CSR.

Both functions accept numpy int64 arrays for ``indptr`` and
``indices`` and return a numpy boolean array of reached vertices.
"""

from __future__ import annotations

import numpy as np

from reachq.bfs import csr_reachable_backward, csr_reachable_forward

_ext_available = False
try:
    from reachq.accel.cython._cy_bfs import (  # type: ignore[import-not-found]
        cy_bfs_backward as _cy_bfs_backward_ext,
    )
    from reachq.accel.cython._cy_bfs import (
        cy_bfs_forward as _cy_bfs_forward_ext,
    )

    _ext_available = True
except ImportError:
    _ext_available = False


def cy_bfs_forward(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    *,
    max_depth: int = 1 << 30,
) -> np.ndarray:
    """Forward BFS from ``source`` over a CSR adjacency.

    Returns a numpy boolean array of length ``n`` where
    ``out[v]`` is True iff v is reachable from ``source`` in at
    most ``max_depth`` hops.

    Args:
        indptr: CSR indptr array, dtype int64, length n + 1.
        indices: CSR indices array, dtype int64, length m.
        source: Source vertex index.
        n: Number of vertices.
        max_depth: Maximum hop count. Default is effectively
            unbounded (``1 << 30``).

    Returns:
        Boolean numpy array of length n.
    """
    if _ext_available:
        result_ext = _cy_bfs_forward_ext(indptr, indices, source, n, max_depth)
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


def cy_bfs_backward(
    indptr_rev: np.ndarray,
    indices_rev: np.ndarray,
    source: int,
    n: int,
    *,
    max_depth: int = 1 << 30,
) -> np.ndarray:
    """Backward BFS from ``source`` over the reversed CSR.

    Returns a numpy boolean array of length ``n`` where ``out[v]``
    is True iff ``source`` is reachable from v in at most
    ``max_depth`` forward hops (i.e., v can reach ``source``).

    Args:
        indptr_rev: Reversed-CSR indptr array.
        indices_rev: Reversed-CSR indices array.
        source: Source vertex index.
        n: Number of vertices.
        max_depth: Maximum hop count.

    Returns:
        Boolean numpy array of length n.
    """
    if _ext_available:
        result_ext = _cy_bfs_backward_ext(indptr_rev, indices_rev, source, n, max_depth)
        if isinstance(result_ext, np.ndarray):
            return result_ext
    # Fallback: pure-Python returns the indices of reached vertices;
    # convert to a boolean mask of length n.
    reached_indices = csr_reachable_backward(
        indptr_rev, indices_rev, source, n, max_depth=max_depth
    )
    out = np.zeros(n, dtype=bool)
    out[reached_indices] = True
    return out


def is_cython_available() -> bool:
    """Return True if the compiled Cython extension is loaded."""
    return _ext_available


__all__ = ["cy_bfs_backward", "cy_bfs_forward", "is_cython_available"]
