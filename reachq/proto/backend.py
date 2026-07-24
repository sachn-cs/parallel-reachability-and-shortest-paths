"""Backend Protocol for parallel-execution backends."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Callable, Protocol, TypeVar, runtime_checkable

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
