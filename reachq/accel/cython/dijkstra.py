"""Cython-accelerated Dijkstra kernel.

Requires Cython compilation. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations


def _cython_dijkstra_not_available() -> None:
    raise ImportError(
        "Cython Dijkstra kernel not compiled. "
        "Build with: pip install reachq[accel]"
    )


def cy_dijkstra(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Heap-based Dijkstra (Cython)."""
    _cython_dijkstra_not_available()
