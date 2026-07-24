"""Cython-accelerated BFS kernel.

Requires Cython compilation. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations


def _cython_bfs_not_available() -> None:
    raise ImportError(
        "Cython BFS kernel not compiled. "
        "Build with: pip install reachq[accel]"
    )


# Public API stubs — raise until Cython extension is compiled.
def cy_bfs_forward(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Vectorised CSR BFS forward (Cython)."""
    _cython_bfs_not_available()
