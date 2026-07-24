"""GraphBLAS backend.

Requires pygraphblas. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations

from typing import Any, Iterable


class GraphBLASBackend:
    """Backend using GraphBLAS sparse matrix operations."""

    mode = "graphblas"
    n_workers = 1

    def __init__(self) -> None:
        from importlib.util import find_spec

        if find_spec("pygraphblas") is None:
            raise ImportError(
                "pygraphblas is required for GraphBLAS backend. "
                "Install with: pip install pygraphblas"
            )

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Sequential dispatch (GraphBLAS operates on matrices, not items)."""
        return [func(item) for item in items]
