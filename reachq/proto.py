"""Structural Protocols describing the shape of reachq graphs and RNGs.

The Protocols here describe the contract that
:class:`reachq.graph.Digraph`, :class:`reachq.graph.WeightedDigraph`,
and ``random.Random`` already satisfy. They are intentionally
minimal -- they expose only the surface that the algorithms
actually consume, so a third-party implementation that satisfies
the Protocol can be substituted for the concrete class without
subclassing.

These Protocols are *not* used as the runtime type annotations of
the public algorithms (those still take the concrete
:class:`Digraph` / :class:`WeightedDigraph`). They exist so
external code that wants to declare "any object that looks like a
reachq graph" can use :class:`Graph` as an annotation or an
``isinstance`` check.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Graph(Protocol):
    """Directed graph.

    The concrete :class:`reachq.graph.Digraph` conforms.
    """

    insertion_order: list[object]
    index_of_map: dict[object, int]
    edge_count: int
    out_edges: dict[object, set[object]]
    in_edges: dict[object, set[object]]

    def add_vertex(self, v: object) -> None: ...
    def add_edge(self, u: object, v: object) -> None: ...
    def has_vertex(self, v: object) -> bool: ...
    def has_edge(self, u: object, v: object) -> bool: ...
    def vertices(self) -> tuple[object, ...]: ...
    def iter_vertices(self): ...
    def num_vertices(self) -> int: ...
    def num_edges(self) -> int: ...
    def edges(self) -> list[tuple[object, object]]: ...
    def index_of(self, v: object) -> int: ...
    def vertex_at(self, i: int) -> object: ...
    def out_neighbors(self, v: object) -> set[object]: ...
    def in_neighbors(self, v: object) -> set[object]: ...
    def degree_out(self, v: object) -> int: ...
    def degree_in(self, v: object) -> int: ...
    def reversed(self) -> Graph: ...
    def copy(self) -> Graph: ...
    def induced_subgraph(self, vertex_subset) -> Graph: ...


@runtime_checkable
class WeightedGraph(Graph, Protocol):
    """Weighted directed graph.

    The concrete :class:`reachq.graph.WeightedDigraph` conforms.
    """

    def add_edge(self, u: object, v: object, weight: int) -> None: ...
    def get_weight(self, u: object, v: object) -> int | None: ...
    def edges(self) -> list[tuple[object, object, int]]: ...


@runtime_checkable
class RNG(Protocol):
    """Reproducible random number source used by reachq algorithms.

    The standard library ``random.Random`` conforms.
    """

    def random(self) -> float: ...
    def randint(self, a: int, b: int) -> int: ...
    def shuffle(self, seq: list) -> None: ...


__all__ = ["RNG", "Graph", "WeightedGraph"]
