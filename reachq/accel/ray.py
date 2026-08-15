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
    """Distributed backend using Ray."""

    mode = "ray"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        from importlib.util import find_spec

        if find_spec("ray") is None:
            raise ImportError(
                "ray is required for distributed execution. "
                "Install with: pip install ray"
            )
        self.n_workers = n_workers

    def imap_unordered(self, func: Any, items: Iterable[Any]) -> list[Any]:
        """Dispatch items via Ray remote calls."""
        import ray

        remote_func = ray.remote(func)
        refs = [remote_func.remote(item) for item in items]
        return list(ray.get(refs))
