"""GraphBLAS backend.

Requires pygraphblas. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations


class GraphBLASBackend:
    """Backend using GraphBLAS sparse matrix operations."""

    mode = "graphblas"
    n_workers = 1

    def __init__(self) -> None:
        try:
            import pygraphblas  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "pygraphblas is required for GraphBLAS backend. "
                "Install with: pip install pygraphblas"
            ) from e

    def imap_unordered(self, func, items):  # type: ignore[no-untyped-def]
        """Sequential dispatch (GraphBLAS operates on matrices, not items)."""
        return [func(item) for item in items]
