"""Thread-pool backend.

Provides a single helper, ``threads(n)``, that returns a
``ParallelContext`` configured for a thread pool of `n` workers.
Use for I/O-bound workloads; reachq's hot loops are CPU-bound and
do not benefit from threading because of the GIL.
"""

from __future__ import annotations

from reachq.core.backends import ParallelContext


def threads(n: int) -> ParallelContext:
    """Shorthand for a thread pool of *n* workers."""
    return ParallelContext("threads", n)
