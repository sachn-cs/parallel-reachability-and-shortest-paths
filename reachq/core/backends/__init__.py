"""Parallel-execution backends for reachq.

Defines the ``Backend`` Protocol (a minimal ``imap_unordered`` shape)
and the concrete ``ParallelContext`` selector. The default is
``SEQUENTIAL`` (single-threaded). Thread and process pools are
available via ``reachq.core.backends.threads.threads(n)`` and
``reachq.core.backends.processes.processes(n)``.

The experimental distributed backends (Ray, Dask, GraphBLAS) live
in ``reachq/accel/`` and are not part of the default build.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
R = TypeVar("R")


@runtime_checkable
class Backend(Protocol):
    """Protocol for parallel-execution backends."""

    mode: str
    n_workers: int

    def imap_unordered(
        self, func: Callable[[T], R], items: Iterable[T]
    ) -> Iterable[R]: ...


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
        """Dispatch *items* through *func*. Order is not preserved."""
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
        return f"ParallelContext(mode={self.mode!r}, n_workers={self.n_workers})"


SEQUENTIAL = ParallelContext("sequential", 1)
