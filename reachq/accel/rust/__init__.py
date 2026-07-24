"""Rust-accelerated kernels via PyO3.

Requires ``maturin`` and a Rust toolchain. Build with::

    cd reachq/accel/rust
    maturin develop --release

After a successful build, the compiled extension ``_reachq_rust``
appears in the Python path. The wrapper functions in this module
attempt to import it at runtime; if the import fails (because the
extension has not been compiled), they fall back to the equivalent
pure-Python implementations in :mod:`reachq.core`.

Public API (identical to the Cython wrappers):

- :func:`rust_bfs_forward` — forward BFS over a CSR adjacency.
- :func:`rust_dijkstra` — Dijkstra from a single source.

The :file:`Cargo.toml`, :file:`pyproject.toml`, and
:file:`src/lib.rs` files in this directory constitute the build
configuration and Rust source. They are kept here so the entire
acceleration layer ships with the Python package.

For users who do not have Rust installed, the Python fallbacks
in :mod:`reachq.core` provide the same API with somewhat lower
performance.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from reachq.core.bfs import csr_reachable_forward
from reachq.core.shortest_paths import dijkstra


_ext_available = False
_rust_bfs_forward_ext: Any = None
_rust_dijkstra_ext: Any = None
try:
    from reachq.accel.rust._reachq_rust import (  # type: ignore[import-not-found]
        rust_bfs_forward as _bfs_impl,
        rust_dijkstra as _dijkstra_impl,
    )
    _rust_bfs_forward_ext = _bfs_impl
    _rust_dijkstra_ext = _dijkstra_impl
    _ext_available = True
except ImportError:
    # Maturin may install the .so at a different path. Try the
    # top-level module installed via maturin develop.
    try:
        from _reachq_rust._reachq_rust import (  # type: ignore[import-not-found]
            rust_bfs_forward as _bfs_impl,
            rust_dijkstra as _dijkstra_impl,
        )
        _rust_bfs_forward_ext = _bfs_impl
        _rust_dijkstra_ext = _dijkstra_impl
        _ext_available = True
    except ImportError:
        _ext_available = False


def rust_bfs_forward(
    indptr: np.ndarray,
    indices: np.ndarray,
    source: int,
    n: int,
    *,
    max_depth: int = 1 << 30,
) -> np.ndarray:
    """Forward BFS over a CSR adjacency (Rust-backed).

    Identical API to :func:`reachq.accel.cython.bfs.cy_bfs_forward`.
    Falls back to the pure-Python CSR BFS when the Rust extension
    is unavailable.
    """
    if _ext_available:
        result_ext = _rust_bfs_forward_ext(indptr, indices, source, n, max_depth)
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


def rust_dijkstra(
    indptr: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
    source: int,
    n: int,
) -> np.ndarray:
    """Dijkstra from ``source`` over a weighted CSR adjacency (Rust-backed).

    Identical API to :func:`reachq.accel.cython.dijkstra.cy_dijkstra`.
    Falls back to pure-Python Dijkstra when the Rust extension is
    unavailable.
    """
    if _ext_available:
        result = _rust_dijkstra_ext(indptr, indices, weights, source, n)
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


def is_rust_available() -> bool:
    """Return True if the compiled Rust extension is loaded."""
    return _ext_available


__all__ = ["rust_bfs_forward", "rust_dijkstra", "is_rust_available"]