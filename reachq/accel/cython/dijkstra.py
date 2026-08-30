"""Cython-accelerated Dijkstra kernel.

This module is the public Python entry point for the binary-heap
Dijkstra kernel in :file:`dijkstra.pyx`. When the Cython extension
has been compiled (via ``python setup.py build_ext --inplace`` from
this directory, or installed via the ``reachq[accel]`` wheel), the
function dispatches to the compiled code with the GIL released for
parallel execution. When the extension is unavailable, it falls
back to a pure-Python implementation that yields identical results.

Public API:

- :func:`cy_dijkstra` — Dijkstra from a single source over a
  weighted CSR adjacency.

The function accepts numpy int64 arrays for ``indptr`` and
``indices`` and a numpy float64 array for ``weights`` parallel to
``indices``.
"""

from __future__ import annotations

import numpy as np

from reachq.core.shortest_paths import dijkstra

_ext_available = False
try:
    from reachq.accel.cython._cy_dijkstra import (  # type: ignore[import-not-found]
        cy_dijkstra as _cy_dijkstra_ext,
    )

    _ext_available = True
except ImportError:
    _ext_available = False


def _numpy_fallback(
    indptr: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
    source: int,
    n: int,
) -> np.ndarray:
    """Pure-Python Dijkstra fallback using the WeightedDigraph wrapper."""
    from reachq.core.graph import WeightedDigraph

    g = WeightedDigraph()
    for u in range(n):
        start = int(indptr[u])
        end = int(indptr[u + 1])
        g.add_vertex(u)
        for j in range(start, end):
            v = int(indices[j])
            w = float(weights[j])
            g.add_vertex(v)
            g.add_edge(u, v, int(w))
    result = dijkstra(g, source)
    out = np.full(n, np.inf, dtype=np.float64)
    if source in g:
        out[source] = 0.0
    for v_obj, d in result.items():
        if isinstance(v_obj, int) and 0 <= v_obj < n:
            out[v_obj] = d
    return out


def cy_dijkstra(
    indptr: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
    source: int,
    n: int,
) -> np.ndarray:
    """Dijkstra from ``source`` over a weighted CSR adjacency.

    Returns a numpy float64 array of length n where ``dist[v]`` is
    the shortest-path distance from ``source`` to ``v`` (or
    ``inf`` if unreachable).

    Args:
        indptr: CSR indptr array, dtype int64, length n + 1.
        indices: CSR indices array, dtype int64, length m.
        weights: Edge weights array, dtype float64, length m.
        source: Source vertex index.
        n: Number of vertices.

    Returns:
        Float64 numpy array of length n.
    """
    if _ext_available:
        result = _cy_dijkstra_ext(indptr, indices, weights, source, n)
        if isinstance(result, np.ndarray):
            return result
    return _numpy_fallback(indptr, indices, weights, source, n)


def is_cython_available() -> bool:
    """Return True if the compiled Cython extension is loaded."""
    return _ext_available


__all__ = ["cy_dijkstra", "is_cython_available"]
