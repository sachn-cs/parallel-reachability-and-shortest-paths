"""Parallel-execution context for the JLS and CFR constructions.

Different parallel strategies are appropriate for different bottlenecks.
The bottleneck on dense graphs is the numpy CSR frontier expansion (which
releases the GIL on large arrays), so threading helps. On Python-heavy
workloads the bottleneck is per-op overhead, so threading does not help
and processes would (with high startup cost).

Public surface:

  ParallelContext -- selects a strategy; imap_unordered() dispatches items.
  SEQUENTIAL       -- single-threaded (default).
  THREADS(n)       -- concurrent.futures.ThreadPoolExecutor with n workers.
  PROCESSES(n, initializer, initargs) -- ProcessPoolExecutor.

Each worker receives one item and returns its result. Workers must be
top-level or otherwise picklable for the process-pool variant.

Design note: pivot processing is embarrassingly parallel; per-pivot
work (BFS + label update) is independent of other pivots at the same
recursion level. So imap_unordered is the natural shape -- no barrier
between pivots, just collect results and merge.
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ParallelContext:
    """Selectable parallel-execution strategy."""

    def __init__(
        self,
        mode: str = "sequential",
        n_workers: int = 1,
        *,
        initializer: Callable[..., None] | None = None,
        initargs: tuple[Any, ...] = (),
    ) -> None:
        if mode not in {"sequential", "threads", "processes"}:
            raise ValueError(f"unknown parallel mode: {mode!r}")
        if mode in {"threads", "processes"} and n_workers < 1:
            raise ValueError(f"n_workers must be >= 1 for mode={mode!r}")
        self.mode = mode
        self.n_workers = n_workers
        self.initializer = initializer
        self.initargs = initargs

    def imap_unordered(
        self,
        func: Callable[[T], R],
        items: Iterable[T],
    ) -> Iterable[R]:
        """Dispatch *items* through *func*. Order is not preserved.

        For 'sequential': returns items mapped by func, in input order.
        For 'threads'/'processes': uses the matching executor.
        """
        items_list = list(items)
        if self.mode == "sequential" or self.n_workers <= 1:
            return [func(item) for item in items_list]
        if self.mode == "threads":
            with ThreadPoolExecutor(max_workers=self.n_workers) as pool:
                return list(pool.map(func, items_list))
        if self.mode == "processes":
            with ProcessPoolExecutor(
                max_workers=self.n_workers,
                initializer=self.initializer,
                initargs=self.initargs,
            ) as pool:
                return list(pool.map(func, items_list))
        raise ValueError(f"unknown parallel mode: {self.mode!r}")

    def __repr__(self) -> str:
        return f"ParallelContext(mode={self.mode!r}, " f"n_workers={self.n_workers})"


SEQUENTIAL = ParallelContext("sequential", 1)


def threads(n: int) -> ParallelContext:
    """Shorthand for a thread pool of *n* workers."""
    return ParallelContext("threads", n)


def processes(
    n: int,
    initializer: Callable[..., None] | None = None,
    initargs: tuple[Any, ...] = (),
) -> ParallelContext:
    """Shorthand for a process pool of *n* workers."""
    return ParallelContext("processes", n, initializer=initializer, initargs=initargs)
