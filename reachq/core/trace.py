"""Operation tracing for reachq algorithms.

Usage::

    with trace("build_shortcut_set", n=graph.num_vertices()):
        H, beta = build_shortcut_set_for_reachability(graph)

The ``trace()`` context manager logs entry/exit and timing. It is
designed to be low-overhead: the hot path only pays for a
``time.monotonic_ns()`` call at entry and exit.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from reachq.core.config import get_logger

log = get_logger("reachq.core.trace")


@contextmanager
def trace(operation: str, **attrs: Any) -> Any:
    """Trace an operation with entry/exit logging and timing.

    Args:
        operation: Name of the operation (e.g. "build_shortcut_set").
        **attrs: Additional attributes to log (e.g. n=1000, omega=3.0).
    """
    extra = " ".join(f"{k}={v}" for k, v in attrs.items())
    msg = f"{operation} start" + (f" ({extra})" if extra else "")
    log.info(msg)
    t0 = time.monotonic_ns()
    try:
        yield
    except Exception:
        elapsed_ms = (time.monotonic_ns() - t0) / 1e6
        log.error("%s failed after %.1fms", operation, elapsed_ms)
        raise
    else:
        elapsed_ms = (time.monotonic_ns() - t0) / 1e6
        log.info("%s done in %.1fms", operation, elapsed_ms)
