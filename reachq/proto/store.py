"""Store Protocol for graph persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from reachq.proto.graph import Graph


@runtime_checkable
class Store(Protocol):
    """Protocol for graph serialisation stores."""

    def dump(self, graph: Graph, path: str) -> None: ...

    def load(self, path: str) -> Graph: ...
