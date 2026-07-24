"""Process-pool backend."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from reachq.core.backends import ParallelContext


def processes(
    n: int,
    initializer: Callable[..., None] | None = None,
    initargs: tuple[Any, ...] = (),
) -> ParallelContext:
    """Shorthand for a process pool of *n* workers."""
    return ParallelContext("processes", n, initializer=initializer, initargs=initargs)
