"""Graph Protocol for reachq extension points.

Defines the minimum interface that a graph must satisfy to be used
with reachq algorithms. The concrete ``Digraph`` class in
``reachq.core.graph`` implements this protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Graph(Protocol):
    """Protocol for directed graphs usable with reachq algorithms."""

    @property
    def vertex_set(self) -> set[object]: ...

    def add_vertex(self, v: object) -> None: ...

    def add_edge(self, u: object, v: object) -> None: ...

    def num_vertices(self) -> int: ...

    def num_edges(self) -> int: ...

    def vertices(self) -> list[object]: ...

    def edges(self) -> list[tuple[object, object]]: ...

    def reversed(self) -> Graph: ...
