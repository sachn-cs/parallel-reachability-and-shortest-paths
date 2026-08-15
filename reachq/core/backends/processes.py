"""Process-pool backend.

Provides a single helper, ``processes(n)``, that returns a
``ParallelContext`` configured for a process pool of `n` workers.
Use as the ``ParallelContext`` argument when the workload is
CPU-bound and the GIL is the bottleneck.

Note: process workers cannot share module globals (the JLS
construction uses a module-global ``_PIVOT_STATE`` dict that is
not picklable). The CFR path exposes a ``parallel_workers``
parameter, but it is currently logged-and-ignored on the process
path; the sequential path is the only fully-tested mode.
"""

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
