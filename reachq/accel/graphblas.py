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
    """Backend using GraphBLAS sparse matrix operations.

    Implements the ``Backend`` Protocol. The current implementation
    defers to a sequential list comprehension; real GraphBLAS
    operations would operate on sparse matrices, not on per-item
    callables.

    Attributes:
        mode: ``"graphblas"``.
        n_workers: Number of concurrent workers (always 1; the
            underlying GraphBLAS operation is matrix-level).
    """

    mode = "graphblas"
    n_workers = 1

    def __init__(self) -> None:
        """Initialise the GraphBLAS backend.

        Raises:
            ImportError: If ``pygraphblas`` is not installed.
        """
        from importlib.util import find_spec

        if find_spec("pygraphblas") is None:
            raise ImportError(
                "pygraphblas is required for GraphBLAS backend. "
                "Install with: pip install pygraphblas"
            )

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Sequential dispatch (GraphBLAS operates on matrices, not items).

        Args:
            func: Callable to apply to each item.
            items: Iterable of inputs.

        Returns:
            List of results in input order.
        """
        return [func(item) for item in items]
