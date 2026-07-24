"""RNG Protocol for reproducible random number generation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RNG(Protocol):
    """Protocol for random number generators used in reachq algorithms."""

    def random(self) -> float: ...

    def randint(self, a: int, b: int) -> int: ...

    def choice(self, seq: list[object]) -> object: ...

    def sample(self, population: list[object], k: int) -> list[object]: ...

    def seed(self, s: int) -> None: ...
