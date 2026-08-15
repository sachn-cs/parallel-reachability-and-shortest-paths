"""GraphBLAS backend.

This is a stub: the backend exposes the ``Backend`` Protocol
shape but the underlying implementation defers to a sequential
list comprehension. Real GraphBLAS operations would operate on
sparse matrices, not on per-item callables. Requires the optional
``pygraphblas`` dependency; install with ``pip install
reachq[accel]``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


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
