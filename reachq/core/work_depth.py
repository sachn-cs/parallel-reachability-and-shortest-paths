"""Parallel work/depth simulation model.

The paper analyzes algorithms in the PRAM work/depth model:
- Work = total number of operations.
- Depth = length of the longest critical path (span).

Since Python does not provide PRAM, we simulate work and depth explicitly
by recording coarse-grained algorithmic primitives. Each recorded operation
adds to the total work and depth according to the asymptotic bounds stated
in the paper. This makes the simulation mathematically traceable.

Observed wall-clock time is tracked separately and never conflated with
theoretical work/depth bounds.

In addition to the simulated model, ``SpanProfiler`` measures *empirical*
parallel span by timing each sequential phase of the construction on one
process. This gives a lower bound on true PRAM span: anything faster than
this on a single process implies the algorithm is already well-parallelised.
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

    Work and depth are accumulated as floating-point asymptotic estimates.
    They are not exact operation counts; they reflect the paper's stated
    bounds for each primitive.
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
        """Record a single primitive operation.

        Args:
            name: Identifier for the primitive (e.g., "bfs", "matrix_multiply").
            work: Asymptotic work contributed by this call.
            depth: Asymptotic depth contributed by this call.
            details: Optional human-readable annotation.
        """
        self.work += work
        self.depth = max(self.depth, depth)  # parallel composition of sequential phases
        self.records.append(OperationRecord(name, work, depth, details))

    def sequential_composition(self, other: WorkDepthAccountant) -> None:
        """Combine another accountant sequentially.

        Work and depth add; the other’s depth extends our critical path.
        """
        self.work += other.work
        self.depth += other.depth
        self.records.extend(other.records)

    def parallel_composition(self, others: list[WorkDepthAccountant]) -> None:
        """Combine several accountants in parallel.

        Work sums; depth is the maximum across all branches.
        """
        for o in others:
            self.work += o.work
        max_depth = max((o.depth for o in others), default=0.0)
        self.depth += max_depth
        for o in others:
            self.records.extend(o.records)

    def summary(self) -> dict[str, float]:
        """Return a dict with total work, depth, and elapsed time."""
        return {
            "work": self.work,
            "depth": self.depth,
            "elapsed_seconds": self.elapsed_seconds,
        }

    def operations(self) -> list[OperationRecord]:
        """Return the list of recorded operations."""
        return list(self.records)

    def __repr__(self) -> str:
        return (
            f"WorkDepthAccountant(work={self.work:.2e}, "
            f"depth={self.depth:.2e}, elapsed={self.elapsed_seconds:.3f}s)"
        )


def record_bfs(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    details: str | None = None,
) -> None:
    """Record a BFS/DFS traversal on a digraph with n vertices and m edges.

    Paper work bound: O(m).
    Sequential depth bound: O(n) for standard BFS.
    Parallel depth bound (used in parallel_bfs with shortcuts): O(beta).
    We record the sequential bound here; callers using parallel primitives
    should adjust depth explicitly.
    """
    if accountant is None:
        return
    accountant.record("bfs", work=m, depth=n, details=details)


def record_reverse_bfs(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    details: str | None = None,
) -> None:
    """Record a reverse BFS traversal. Same bounds as BFS."""
    if accountant is None:
        return
    accountant.record("reverse_bfs", work=m, depth=n, details=details)


def record_dijkstra(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    details: str | None = None,
) -> None:
    """Record Dijkstra’s algorithm on a graph with n vertices and m edges.

    Paper work bound: O(m log n) with a binary heap.
    We approximate work as m * log2(n + 2) to avoid log(0).
    Depth is sequential: O(m log n).
    """
    if accountant is None:
        return
    log_n = max(1.0, math.log2(n + 2))
    work = m * log_n
    accountant.record("dijkstra", work=work, depth=work, details=details)


def record_truncated_dijkstra(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    details: str | None = None,
) -> None:
    """Record a truncated Dijkstra run.

    Work and depth are bounded by the full Dijkstra cost in the worst case,
    but typically smaller. We conservatively use the full bound.
    """
    record_dijkstra(accountant, n, m, details)


def record_matrix_multiply(
    accountant: WorkDepthAccountant | None,
    n: int,
    omega: float = 3.0,
    details: str | None = None,
) -> None:
    """Record an n x n matrix multiplication.

    Paper assumes fast matrix multiplication exponent omega < 2.371339.
    Our implementation uses numpy.matmul (standard BLAS), effectively
    omega = 3 for most sizes. The caller can override omega.

    Work: O(n^omega).
    Depth: O(log n) for parallel repeated squaring.
    """
    if accountant is None:
        return
    work = n**omega
    depth = max(1.0, math.log2(n + 2))
    accountant.record("matrix_multiply", work=work, depth=depth, details=details)


def record_transitive_closure(
    accountant: WorkDepthAccountant | None,
    n: int,
    omega: float = 3.0,
    details: str | None = None,
) -> None:
    """Record transitive closure via repeated squaring.

    Work: O(n^omega).
    Depth: O(log n) for the O(log n) parallel matrix multiplications.
    """
    if accountant is None:
        return
    work = n**omega
    depth = max(1.0, math.log2(n + 2))
    accountant.record("transitive_closure", work=work, depth=depth, details=details)


def record_tc_pruning(
    accountant: WorkDepthAccountant | None,
    ball_size: int,
    omega: float = 3.0,
    details: str | None = None,
) -> None:
    """Record TC-Pruning on a ball of size |R(G,p)|.

    Work: O(|R|^omega) for computing TC on the induced subgraph.
    Depth: O(log |R|) for repeated squaring.
    """
    if accountant is None:
        return
    b = ball_size
    if b <= 1:
        return
    work = b**omega
    depth = max(1.0, math.log2(b + 2))
    accountant.record("tc_pruning", work=work, depth=depth, details=details)


def record_truncsssp_pruning(
    accountant: WorkDepthAccountant | None,
    ball_size: int,
    details: str | None = None,
) -> None:
    """Record TruncSSSP-Pruning on a ball of size |R_d(G,p)|.

    Work: O(|R| * (m_R + n_R)) for running Dijkstra from every vertex in the
    ball on the induced subgraph, truncated at distance d.
    We approximate this as O(|R| * m_R) in the worst case.
    Depth: sequential, O(|R| * m_R).
    """
    if accountant is None:
        return
    b = ball_size
    if b <= 1:
        return
    # Conservative bound: |R| Dijkstra runs on subgraph with <= |R| vertices.
    # Densest possible subgraph has O(|R|^2) edges.
    work = b * (b**2)
    accountant.record("truncsssp_pruning", work=work, depth=work, details=details)


def record_scc_decomposition(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    details: str | None = None,
) -> None:
    """Record Kosaraju SCC decomposition.

    Work: O(n + m).
    Depth: O(n) sequential; parallel variants exist but are not reproduced.
    """
    if accountant is None:
        return
    accountant.record("scc_decomposition", work=n + m, depth=n, details=details)


def record_partition(
    accountant: WorkDepthAccountant | None,
    n: int,
    details: str | None = None,
) -> None:
    """Record label-based vertex partitioning.

    Work: O(n).
    Depth: O(1) in parallel; O(n) sequential.
    """
    if accountant is None:
        return
    accountant.record("partition", work=n, depth=n, details=details)


def record_shortcut_set_construction(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    rho: float,
    omega: float = 3.0,
    details: str | None = None,
) -> None:
    """Record the overall JLS + TC-Pruning shortcut set construction.

    Paper work bound (Theorem 2): O~(m + n * rho^{2*omega - 2}).
    Paper depth bound: O~(n^{1/2+o(1)} / rho) for parallel execution.
    Since we simulate sequentially, depth tracks the sequential depth
    dominated by the recursion and BFS phases.
    """
    if accountant is None:
        return
    log_n = max(1.0, math.log2(n + 2))
    work = m + n * (rho ** (2 * omega - 2))
    # Sequential depth is O~(n) in the worst case for the simulation.
    depth = n * log_n
    accountant.record(
        "shortcut_set_construction",
        work=work * log_n,
        depth=depth,
        details=details,
    )


def record_hopset_construction(
    accountant: WorkDepthAccountant | None,
    n: int,
    m: int,
    rho: float,
    epsilon: float,
    details: str | None = None,
) -> None:
    """Record the overall CFR + TruncSSSP-Pruning hopset construction.

    Paper work bound (Theorem 4): O~(m / epsilon^2 + n * rho^4).
    Paper hopbound: (n^{3+o(1)} / m)^{1/4} / rho, up to (1+epsilon) distortion.
    Sequential depth is dominated by recursive Dijkstra calls.
    """
    if accountant is None:
        return
    log_n = max(1.0, math.log2(n + 2))
    work = (m / (epsilon**2)) + n * (rho**4)
    depth = n * log_n
    accountant.record(
        "hopset_construction",
        work=work * log_n,
        depth=depth,
        details=details,
    )


@dataclass
class PhaseRecord:
    """Wall-clock measurement of a single sequential phase."""

    name: str
    seconds: float


@dataclass
class SpanProfiler:
    """Measures empirical parallel span by timing sequential phases.

    The construction is run sequentially on a single process. Each
    "phase" — a coarse unit of work like sampling, partition, or
    recursion — is timed. The *empirical span* is the sum of phase
    times (since each phase is sequential in the absence of real
    parallelism).

    This is NOT a true PRAM measurement; it is a lower bound on the
    parallel span achievable on one process. Real PRAM span can only
    be smaller if the phases are parallelisable.

    To compare against the paper's theoretical bounds, set
    ``theoretical_work`` and ``theoretical_depth`` from the formulas
    in this module; ``span_to_depth_ratio`` then gives a dimensionless
    indicator: > 1 means the implementation takes longer than the
    theoretical depth predicts (expected for Python overhead),
    < 1 would mean we beat the bound (a sign of measurement error).
    """

    phases: list[PhaseRecord] = field(default_factory=list)
    start_time: float | None = field(default=None, repr=False)
    current_name: str | None = field(default=None, repr=False)
    current_start: float | None = field(default=None, repr=False)
    theoretical_work: float = 0.0
    theoretical_depth: float = 0.0

    def begin_phase(self, name: str) -> None:
        """Start timing a new phase."""
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
        """Return a dict with measured span and theoretical bounds.

        Note: ``theoretical_work`` and ``theoretical_depth`` are in
        asymptotic-operation units, while ``span_seconds`` is wall-clock
        time. They are NOT directly comparable. Convert with an
        operations-per-second constant for your hardware if you want
        a unitless ratio.
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
        return f"SpanProfiler(span={span:.3f}s, " f"phases={len(self.phases)})"


def theoretical_shortcut_work(n: int, m: int, rho: float, omega: float = 3.0) -> float:
    """Return theoretical work bound for shortcut set construction.

    Bound from Theorem 2: O~(m + n * rho^{2*omega - 2}).
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * (m + n * math.pow(rho, 2 * omega - 2))


def theoretical_shortcut_depth(n: int, rho: float) -> float:
    """Return theoretical parallel depth bound for shortcut set construction.

    Bound from Theorem 2: O~(n^{1/2+o(1)} / rho).
    We approximate the o(1) term with a single log factor.
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * (math.sqrt(n) / rho)


def theoretical_hopset_work(n: int, m: int, rho: float, epsilon: float) -> float:
    """Return theoretical work bound for hopset construction.

    Bound from Theorem 4: O~(m / epsilon^2 + n * rho^4).
    """
    log_n = max(1.0, math.log2(n + 2))
    return log_n * ((m / (epsilon**2)) + n * (rho**4))


def theoretical_hopset_depth(n: int, m: int, rho: float) -> float:
    """Return theoretical parallel depth bound for hopset construction.

    Bound from Theorem 4: O~((n^3 / m)^{1/4} / rho).
    We approximate the o(1) term with a single log factor.
    """
    log_n = max(1.0, math.log2(n + 2))
    depth = math.pow((n**3) / max(1, m), 0.25) / rho
    return log_n * depth
