"""Metrics collection for reachq algorithms.

Provides lightweight counter and histogram interfaces that can be
optionally wired into algorithm hot paths. No-ops by default; call
``enable_metrics()`` to activate.
"""

from __future__ import annotations

import threading

_enabled = False
_lock = threading.Lock()
_counters: dict[str, int] = {}
_histograms: dict[str, list[float]] = {}


def enable_metrics() -> None:
    """Enable metrics collection."""
    global _enabled
    with _lock:
        _enabled = True


def disable_metrics() -> None:
    """Disable and reset metrics collection."""
    global _enabled
    with _lock:
        _enabled = False
        _counters.clear()
        _histograms.clear()


def inc_counter(name: str, value: int = 1) -> None:
    """Increment a named counter."""
    if not _enabled:
        return
    with _lock:
        _counters[name] = _counters.get(name, 0) + value


def record_histogram(name: str, value: float) -> None:
    """Record a value in a named histogram."""
    if not _enabled:
        return
    with _lock:
        _histograms.setdefault(name, []).append(value)


def snapshot() -> dict[str, object]:
    """Return current metrics as a dict.

    Returns:
        {"counters": {name: value}, "histograms": {name: {min, max, mean, count}}}
    """
    with _lock:
        counters = dict(_counters)
        histograms = {}
        for name, values in _histograms.items():
            if values:
                histograms[name] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "count": len(values),
                }
    return {"counters": counters, "histograms": histograms}
