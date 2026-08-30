"""Parallel work/depth accounting and span profiling.

The paper analyses algorithms in the PRAM work/depth model: work
counts total operations, depth measures the longest critical
path. Python does not provide PRAM, so we simulate work and depth
explicitly via :class:`WorkDepthAccountant` and observe empirical
span via :class:`SpanProfiler`.

Recorded wall-clock time is never conflated with theoretical
bounds; the two are exposed side-by-side in the
:func:`Accountant.summary` and :func:`Profiler.summary` dicts.

Four theoretical-bound functions round out the module:
:func:`theoretical_shortcut_work`,
:func:`theoretical_shortcut_depth`,
:func:`theoretical_hopset_work`, and
:func:`theoretical_hopset_depth`.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field


@dataclass
class OperationRecord:
    """A single recorded algorithmic primitive."""

    name: str
    work: float
    depth: float
    details: str | None = None


@dataclass
class WorkDepthAccountant:
    """Tracks simulated work, depth, and observed runtime.

    Work and depth are accumulated as floating-point asymptotic
    estimates, not exact operation counts.
    """

    work: float = 0.0
    depth: float = 0.0
    elapsed_seconds: float = 0.0
    records: list[OperationRecord] = field(default_factory=list)
    start_time: float | None = field(default=None, repr=False)

    def start_timer(self) -> None:
        """Begin measuring wall-clock time."""
        self.start_time = time.perf_counter()

    def stop_timer(self) -> None:
        """End wall-clock measurement."""
        if self.start_time is not None:
            self.elapsed_seconds += time.perf_counter() - self.start_time
            self.start_time = None

    def record(
        self,
        name: str,
        work: float,
        depth: float,
        details: str | None = None,
    ) -> None:
        """Record a single primitive operation."""
        self.work += work
        self.depth = max(self.depth, depth)
        self.records.append(OperationRecord(name, work, depth, details))

    def sequential_composition(self, other: WorkDepthAccountant) -> None:
        """Combine another accountant sequentially (work + depth add)."""
        self.work += other.work
        self.depth += other.depth
        self.records.extend(other.records)

    def parallel_composition(self, others: list[WorkDepthAccountant]) -> None:
        """Combine several accountants in parallel.

        Work sums across branches; depth is the max (bounded by
        the slowest branch).
        """
        for o in others:
            self.work += o.work
        max_depth = max((o.depth for o in others), default=0.0)
        self.depth += max_depth
        for o in others:
            self.records.extend(o.records)

    def summary(self) -> dict[str, float]:
        """Return ``work``, ``depth``, and ``elapsed_seconds``."""
        return {
            "work": self.work,
            "depth": self.depth,
            "elapsed_seconds": self.elapsed_seconds,
        }

    def operations(self) -> list[OperationRecord]:
        """Return a copy of recorded operations."""
        return list(self.records)

    def __repr__(self) -> str:
        return (
            f"WorkDepthAccountant(work={self.work:.2e}, "
            f"depth={self.depth:.2e}, elapsed={self.elapsed_seconds:.3f}s)"
        )


@dataclass
class PhaseRecord:
    """Wall-clock measurement of a single sequential phase."""

    name: str
    seconds: float


@dataclass
class SpanProfiler:
    """Measures empirical parallel span by timing sequential phases.

    Each phase is timed in isolation; the sum of phase times is a
    lower bound on true PRAM span. Recorded wall-clock time is in
    ``phases``; the ``SpanProfiler.summary()`` dict exposes it
    alongside the registered theoretical bounds.
    """

    phases: list[PhaseRecord] = field(default_factory=list)
    start_time: float | None = field(default=None, repr=False)
    current_name: str | None = field(default=None, repr=False)
    current_start: float | None = field(default=None, repr=False)
    theoretical_work: float = 0.0
    theoretical_depth: float = 0.0

    def begin_phase(self, name: str) -> None:
        """Start timing ``name``."""
        self._close_current()
        self.current_name = name
        self.current_start = time.perf_counter()

    def end_phase(self) -> None:
        """Close the current phase and record its wall-clock time."""
        self._close_current()

    def _close_current(self) -> None:
        if self.current_name is None or self.current_start is None:
            return
        elapsed = time.perf_counter() - self.current_start
        self.phases.append(PhaseRecord(self.current_name, elapsed))
        self.current_name = None
        self.current_start = None

    def total_span_seconds(self) -> float:
        """Sum of phase wall-clock times. Lower bound on true PRAM span."""
        self._close_current()
        return sum(p.seconds for p in self.phases)

    def summary(self) -> dict[str, float]:
        """Return ``span_seconds``, ``theoretical_work``,
        ``theoretical_depth``, and one ``phase_<name>_seconds``
        entry per recorded phase.
        """
        self._close_current()
        result: dict[str, float] = {
            "span_seconds": self.total_span_seconds(),
            "theoretical_work": self.theoretical_work,
            "theoretical_depth": self.theoretical_depth,
        }
        for p in self.phases:
            result[f"phase_{p.name}_seconds"] = p.seconds
        return result

    def __repr__(self) -> str:
        span = self.total_span_seconds()
        return f"SpanProfiler(span={span:.3f}s, phases={len(self.phases)})"


def theoretical_shortcut_work(
    n: int, m: int, rho: float, omega: float = 3.0
) -> float:
    """Theoretical work bound for the JLS shortcut-set construction.

    Returns ``log(n) * (m + n * ρ^(2ω-2))``. Theorem 2.
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * (m + n * math.pow(rho, 2 * omega - 2))


def theoretical_shortcut_depth(n: int, rho: float) -> float:
    """Theoretical parallel depth bound for the JLS construction.

    Returns ``log(n) * sqrt(n) / ρ``.
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * (math.sqrt(n) / rho)


def theoretical_hopset_work(
    n: int, m: int, rho: float, epsilon: float
) -> float:
    """Theoretical work bound for the CFR hopset construction.

    Returns ``log(n) * (m / ε^2 + n * ρ^4)``. Theorem 4.
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * ((m / (epsilon**2)) + n * (rho**4))


def theoretical_hopset_depth(n: int, m: int, rho: float) -> float:
    """Theoretical parallel depth bound for the CFR hopset construction.

    Returns ``log(n) * (n^3 / m)^(1/4) / ρ``.
    """
    log_n = max(1.0, math.log2(n + 2))
    depth = math.pow((n**3) / max(1, m), 0.25) / rho
    return log_n * depth


__all__ = [
    "OperationRecord",
    "PhaseRecord",
    "SpanProfiler",
    "WorkDepthAccountant",
    "theoretical_hopset_depth",
    "theoretical_hopset_work",
    "theoretical_shortcut_depth",
    "theoretical_shortcut_work",
]
