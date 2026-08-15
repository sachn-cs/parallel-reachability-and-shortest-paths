"""Ray distributed backend.

This is a stub: it dispatches items via Ray remote calls but is
not wired into the JLS shortcut-set construction. Requires the
optional ``ray`` dependency; install with ``pip install
reachq[accel]``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class RayBackend:
    """Distributed backend using Ray.

    Implements the ``Backend`` Protocol. Dispatches items via Ray
    remote calls. Not wired into the JLS shortcut-set construction.

    Attributes:
        mode: ``"ray"``.
        n_workers: Number of Ray workers (0 means "use Ray's default").
    """

    mode = "ray"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        """Initialise the Ray backend.

        Args:
            n_workers: Number of Ray workers (0 means "use Ray's
                default").

        Raises:
            ImportError: If ``ray`` is not installed.
        """
        from importlib.util import find_spec

        if find_spec("ray") is None:
            raise ImportError(
                "ray is required for distributed execution. "
                "Install with: pip install ray"
            )
        self.n_workers = n_workers

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Dispatch items via Ray remote calls.

        Args:
            func: Callable to apply to each item.
            items: Iterable of inputs.

        Returns:
            List of results (order is not preserved).
        """
        import ray

        remote_func = ray.remote(func)
        refs = [remote_func.remote(item) for item in items]
        return list(ray.get(refs))
