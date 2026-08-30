"""Per-invocation parallel executor.

A :class:`ParallelExecutor` instance is created at the start of
each JLS construction call. State is bound into every task via
the task tuple ``(graph, state, pivot)``; workers never read
module state. Process-pool mode uses ``mp_context="spawn"`` so
numpy and scipy are re-imported cleanly per worker without
inheriting dangling thread state from the main process.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor
from typing import Any

from reachq.core.algorithm.pivots import _pivot_worker_body


def pivot_worker(args: tuple[Any, Any, Any]) -> dict[str, Any]:
    """Worker function: ``pivot_worker((graph, state, pivot))``."""
    graph, state, pivot = args
    return _pivot_worker_body(graph, state, pivot)


class ParallelExecutor:
    """Per-call dispatcher for the per-pivot loop.

    Modes:
        * ``"sequential"`` (default): ``map`` over the input list.
        * ``"processes"``: ``ProcessPoolExecutor`` with
          ``mp_context="spawn"``.
    """

    def __init__(self, mode: str = "sequential", n_workers: int = 1) -> None:
        if mode not in {"sequential", "processes"}:
            raise ValueError(f"unknown parallel mode: {mode!r}")
        if mode == "processes" and n_workers < 1:
            raise ValueError("n_workers must be >= 1 for processes mode")
        self.mode = mode
        self.n_workers = n_workers

    def imap(
        self,
        func: Callable[[tuple[Any, Any, Any]], dict[str, Any]],
        graph: Any,
        state: Any,
        items: Iterable[Any],
    ) -> list[dict[str, Any]]:
        """Dispatch ``items`` through ``func((graph, state, item))``."""
        tasks = [(graph, state, item) for item in items]
        if self.mode == "sequential" or self.n_workers <= 1:
            return [func(t) for t in tasks]
        if self.mode == "processes":
            import multiprocessing

            ctx = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(
                max_workers=self.n_workers, mp_context=ctx
            ) as pool:
                return list(pool.map(func, tasks))
        raise ValueError(f"unknown parallel mode: {self.mode!r}")

    def __repr__(self) -> str:
        return f"ParallelExecutor(mode={self.mode!r}, n_workers={self.n_workers})"
