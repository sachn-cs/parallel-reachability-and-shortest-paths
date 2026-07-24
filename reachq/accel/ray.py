"""Ray distributed backend.

Requires ray. Install with ``pip install reachq[accel]``.
"""

from __future__ import annotations


class RayBackend:
    """Distributed backend using Ray."""

    mode = "ray"
    n_workers = 0

    def __init__(self, n_workers: int = 0) -> None:
        try:
            import ray  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "ray is required for distributed execution. "
                "Install with: pip install ray"
            ) from e
        self.n_workers = n_workers

    def imap_unordered(self, func, items):  # type: ignore[no-untyped-def]
        """Dispatch items via Ray remote calls."""
        import ray

        remote_func = ray.remote(func)
        refs = [remote_func.remote(item) for item in items]
        return ray.get(refs)
