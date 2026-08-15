"""Dask distributed backend.

This is a stub: it dispatches items via ``dask.delayed`` /
``dask.compute`` but is not wired into the JLS shortcut-set
construction. Requires the optional ``dask`` dependency; install
with ``pip install reachq[accel]``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class DaskBackend:
    """Distributed backend using Dask.

    Implements the ``Backend`` Protocol. Dispatches items via
    ``dask.delayed`` / ``dask.compute``. Not wired into the JLS
    shortcut-set construction.

    Attributes:
        mode: ``"dask"``.
        n_workers: Number of Dask workers (0 means "use Dask's default").
    """

    mode = "dask"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        """Initialise the Dask backend.

        Args:
            n_workers: Number of Dask workers (0 means "use Dask's
                default").

        Raises:
            ImportError: If ``dask`` is not installed.
        """
        from importlib.util import find_spec

        if find_spec("dask") is None:
            raise ImportError(
                "dask is required for distributed execution. "
                "Install with: pip install dask"
            )
        self.n_workers = n_workers

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Dispatch items via Dask delayed.

        Args:
            func: Callable to apply to each item.
            items: Iterable of inputs.

        Returns:
            List of results (order is not preserved).
        """
        import dask

        futures = [dask.delayed(func)(item) for item in items]
        results = dask.compute(*futures)
        return list(results)
