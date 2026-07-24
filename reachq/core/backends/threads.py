"""Thread-pool backend."""

from __future__ import annotations

from reachq.core.backends import ParallelContext


def threads(n: int) -> ParallelContext:
    """Shorthand for a thread pool of *n* workers."""
    return ParallelContext("threads", n)
