"""Dask distributed backend.

Requires dask. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class DaskBackend:
    """Distributed backend using Dask."""

    mode = "dask"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        from importlib.util import find_spec

        if find_spec("dask") is None:
            raise ImportError(
                "dask is required for distributed execution. "
                "Install with: pip install dask"
            )
        self.n_workers = n_workers

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Dispatch items via Dask delayed."""
        import dask

        futures = [dask.delayed(func)(item) for item in items]
        results = dask.compute(*futures)
        return list(results)
