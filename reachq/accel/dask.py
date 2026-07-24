"""Dask distributed backend.

Requires dask. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations


class DaskBackend:
    """Distributed backend using Dask."""

    mode = "dask"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        try:
            import dask  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "dask is required for distributed execution. "
                "Install with: pip install dask"
            ) from e
        self.n_workers = n_workers

    def imap_unordered(self, func, items):  # type: ignore[no-untyped-def]
        """Dispatch items via Dask delayed."""
        import dask

        futures = [dask.delayed(func)(item) for item in items]
        return dask.compute(*futures)
