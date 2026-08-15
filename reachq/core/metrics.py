"""Metrics collection for reachq algorithms.

Provides lightweight counter and histogram interfaces that can be
optionally wired into algorithm hot paths. No-ops by default; call
``enable_metrics()`` to activate.
"""

from __future__ import annotations

import threading

enabled = False
lock = threading.Lock()
counters: dict[str, int] = {}
histograms: dict[str, list[float]] = {}


def enable_metrics() -> None:
    """Enable metrics collection.

    After this call, ``inc_counter`` and ``record_histogram`` are
    active. The flag is global; metrics are per-process.
    """
    global enabled
    with lock:
        enabled = True


def disable_metrics() -> None:
    """Disable metrics collection and reset all counters.

    After this call, ``inc_counter`` and ``record_histogram`` are
    no-ops. The collected counters and histograms are cleared.
    """
    global enabled
    with lock:
        enabled = False
        counters.clear()
        histograms.clear()


def inc_counter(name: str, value: int = 1) -> None:
    """Increment a named counter.

    Args:
        name: Counter name.
        value: Amount to add (default 1).
    """
    if not enabled:
        return
    with lock:
        counters[name] = counters.get(name, 0) + value


def record_histogram(name: str, value: float) -> None:
    """Record a value in a named histogram.

    Args:
        name: Histogram name.
        value: Value to record.
    """
    if not enabled:
        return
    with lock:
        histograms.setdefault(name, []).append(value)


def snapshot() -> dict[str, object]:
    """Return current metrics as a dict.

    Returns:
        Mapping with keys ``"counters"`` (``{name: value}``) and
        ``"histograms"`` (``{name: {min, max, mean, count}}``).
    """
    with lock:
        counters_snap = dict(counters)
        histograms_snap = {}
        for name, values in histograms.items():
            if values:
                histograms_snap[name] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "count": len(values),
                }
    return {"counters": counters_snap, "histograms": histograms_snap}
