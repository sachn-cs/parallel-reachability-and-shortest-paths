"""Digraph models.

Two concrete classes:

* :class:`Digraph` -- directed graph with unweighted edges.
* :class:`WeightedDigraph` -- directed graph with non-negative integer
  edge weights.

Both classes share insertion-order vertex indexing so that SCC,
sampling, partition, recursion, and CSR all consume a stable
sequence of vertices regardless of hash randomization. ``vertices()``
returns that sequence as a tuple.

The classes conform to :class:`reachq.proto.graph.Graph` (and
:class:`WeightedGraph`), so any third-party graph implementation that
satisfies the protocol can be substituted into reachq algorithms.
"""

from __future__ import annotations

from collections.abc import Iterator

from reachq.core.errors import ReachqTypeError, ReachqValueError


class Digraph:
    """Directed graph ``G = (V, E)``.

    Vertices are arbitrary hashable objects. Edges are stored as
    adjacency sets for O(1) membership testing. The graph may contain
    parallel edges at the multiplicity of the call to ``add_edge``.
    """

    __slots__ = (
        "edge_count",
        "in_edges",
        "index_of_map",
        "insertion_order",
        "out_edges",
    )

    def __init__(self) -> None:
        self.insertion_order: list[object] = []
        self.index_of_map: dict[object, int] = {}
        self.out_edges: dict[object, set[object]] = {}
        self.in_edges: dict[object, set[object]] = {}
        self.edge_count: int = 0

    @property
    def vertex_set(self) -> set[object]:
        """Set view of vertices (preserves insertion-order membership)."""
        return set(self.insertion_order)

    def add_vertex(self, v: object) -> None:
        """Add a vertex, assigning it the next insertion-order index."""
        if v not in self.index_of_map:
            self.index_of_map[v] = len(self.insertion_order)
            self.insertion_order.append(v)
            self.out_edges.setdefault(v, self._empty_adjacency())
            self.in_edges.setdefault(v, self._empty_adjacency())

    def _empty_adjacency(self):
        """Subclass hook for the empty adjacency type (set or dict-of-int)."""
        return set()

    def has_vertex(self, v: object) -> bool:
        """Check whether ``v`` is in the vertex set."""
        return v in self.index_of_map

    def vertices(self) -> tuple[object, ...]:
        """Return all vertices in insertion order as a tuple."""
        return tuple(self.insertion_order)

    def iter_vertices(self) -> Iterator[object]:
        """Iterate vertices in insertion order without copying."""
        return iter(self.insertion_order)

    def num_vertices(self) -> int:
        """Return ``n = |V|``."""
        return len(self.insertion_order)

    def num_edges(self) -> int:
        """Return ``m = |E|``."""
        return self.edge_count

    def index_of(self, v: object) -> int:
        """Return the insertion-order index of ``v``."""
        return self.index_of_map[v]

    def vertex_at(self, i: int) -> object:
        """Return the vertex at insertion-order index ``i``."""
        return self.insertion_order[i]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(n={self.num_vertices()}, m={self.num_edges()})"

    def __contains__(self, v: object) -> bool:
        return v in self.index_of_map

    def __iter__(self) -> Iterator[object]:
        return iter(self.insertion_order)

    def __len__(self) -> int:
        return len(self.insertion_order)

    def add_edge(self, u: object, v: object) -> None:
        """Add a directed edge from u to v."""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u]:
            self.out_edges[u].add(v)
            self.in_edges[v].add(u)
            self.edge_count += 1

    def add_undirected_edge(self, u: object, v: object) -> None:
        """Add an undirected edge ``{u, v}``: both directions, two directed edges."""
        if u == v:
            raise ReachqValueError("self-loops not supported on add_undirected_edge")
        self.add_vertex(u)
        self.add_vertex(v)
        if v in self.out_edges[u]:
            return
        self.out_edges[u].add(v)
        self.in_edges[v].add(u)
        self.out_edges[v].add(u)
        self.in_edges[u].add(v)
        self.edge_count += 2

    def has_edge(self, u: object, v: object) -> bool:
        """Check whether edge (u, v) exists in O(1) time."""
        return v in self.out_edges.get(u, set())

    def edges(self) -> list[tuple[object, object]]:
        """Return the list of edges as ordered pairs in insertion order."""
        return [
            (u, v)
            for u in self.insertion_order
            for v in self.out_edges[u]
        ]

    def out_neighbors(self, v: object) -> set[object]:
        """Return the out-neighbors of v as a set."""
        return set(self.out_edges.get(v, set()))

    def in_neighbors(self, v: object) -> set[object]:
        """Return the in-neighbors of v as a set."""
        return set(self.in_edges.get(v, set()))

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self.out_edges.get(v, set()))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self.in_edges.get(v, set()))

    def reversed(self) -> Digraph:
        """Return ``G^R`` where all edges are flipped."""
        g = self.__class__()
        g.restore_indices(self.index_of_map, self.insertion_order)
        for v in self.insertion_order:
            g.out_edges.setdefault(v, self._empty_adjacency())
            g.in_edges.setdefault(v, self._empty_adjacency())
        for u, v in self.edges():
            g.out_edges[v].add(u)
            g.in_edges[u].add(v)
            g.edge_count += 1
        return g

    def copy(self) -> Digraph:
        """Return a deep copy."""
        g = self.__class__()
        g.restore_indices(self.index_of_map, self.insertion_order)
        for v in self.insertion_order:
            g.out_edges.setdefault(v, self._empty_adjacency())
            g.in_edges.setdefault(v, self._empty_adjacency())
        for u in self.insertion_order:
            for v in self.out_edges[u]:
                g.out_edges[u].add(v)
                g.in_edges[v].add(u)
                g.edge_count += 1
        return g

    def induced_subgraph(self, vertex_subset) -> Digraph:
        """Return ``G[vertex_subset]``.

        ``vertex_subset`` is any iterable of vertices already in the
        graph. Vertices outside the original graph are silently
        ignored.
        """
        valid = {v for v in vertex_subset if v in self.index_of_map}
        order = [v for v in self.insertion_order if v in valid]
        idx = {v: i for i, v in enumerate(order)}
        g = self.__class__()
        g.restore_indices(idx, order)
        for v in order:
            g.out_edges.setdefault(v, self._empty_adjacency())
            g.in_edges.setdefault(v, self._empty_adjacency())
        for u in order:
            for v in self.out_edges[u]:
                if v in idx:
                    g.out_edges[u].add(v)
                    g.in_edges[v].add(u)
                    g.edge_count += 1
        return g

    def restore_indices(
        self, index_map: dict[object, int], order: list[object]
    ) -> None:
        """Restore ``insertion_order`` and ``index_of_map`` from another graph."""
        self.index_of_map = dict(index_map)
        self.insertion_order = list(order)


def partition_by_labels(
    vertices,
    labels: dict[object, object] | dict[object, tuple[frozenset[object], frozenset[object]]],
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality.

    Args:
        vertices: The vertex container to partition.
        labels: A mapping from each vertex to its label value.
            Vertices missing from the mapping group under the empty
            label.

    Returns:
        A list of disjoint sets whose union covers the input vertices.
    """
    seen: set[object] = set()
    groups: dict[object, set[object]] = {}
    for v in vertices:
        if v in seen:
            continue
        seen.add(v)
        key = labels.get(v)
        if not isinstance(key, tuple):
            key = (frozenset(key) if hasattr(key, "__iter__") else key,)
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


class WeightedDigraph(Digraph):
    """A weighted directed graph ``G = (V, E, w)`` with non-negative integer weights.

    The paper assumes polynomially bounded non-negative integer weights.
    Weights are strictly ``int`` (excluding ``bool``, non-finite
    floats); passing anything else raises :class:`ReachqTypeError`.
    Negative integers raise :class:`ReachqValueError`.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()
        self.out_edges: dict[object, dict[object, int]] = {}
        self.in_edges: dict[object, dict[object, int]] = {}

    def _empty_adjacency(self) -> dict[object, int]:
        """Subclass hook for the empty adjacency type."""
        return {}

    def add_edge(self, u: object, v: object, weight: int) -> None:  # type: ignore[override]
        """Add a directed edge with weight.

        Args:
            u: Source vertex; added if not present.
            v: Target vertex; added if not present.
            weight: Non-negative integer weight.

        Raises:
            ReachqTypeError: If ``weight`` is not an ``int`` (excluding
                ``bool``).
            ReachqValueError: If ``weight`` is negative.
        """
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise ReachqTypeError(
                f"weight must be a non-negative int (got "
                f"{type(weight).__name__}: {weight!r})"
            )
        if weight < 0:
            raise ReachqValueError(
                f"weight must be non-negative (got {weight!r})"
            )

        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u] or weight < self.out_edges[u][v]:
            if v not in self.out_edges[u]:
                self.edge_count += 1
            self.out_edges[u][v] = weight
            self.in_edges[v][u] = weight

    def has_edge(self, u: object, v: object) -> bool:  # type: ignore[override]
        return v in self.out_edges.get(u, {})

    def get_weight(self, u: object, v: object) -> int | None:
        """Return weight of edge (u, v) or None if not present."""
        return self.out_edges.get(u, {}).get(v)

    def edges(self) -> list[tuple[object, object, int]]:  # type: ignore[override]
        """Return the list of edges as triples in insertion order."""
        return [
            (u, v, w)
            for u in self.insertion_order
            for v, w in self.out_edges[u].items()
        ]

    def out_neighbors(self, v: object) -> dict[object, int]:  # type: ignore[override]
        return dict(self.out_edges.get(v, {}))

    def in_neighbors(self, v: object) -> dict[object, int]:  # type: ignore[override]
        return dict(self.in_edges.get(v, {}))

    def degree_out(self, v: object) -> int:
        return len(self.out_edges.get(v, {}))

    def degree_in(self, v: object) -> int:
        return len(self.in_edges.get(v, {}))

    def reversed(self) -> WeightedDigraph:  # type: ignore[override]
        g = self.__class__()
        g.restore_indices(self.index_of_map, self.insertion_order)
        for v in self.insertion_order:
            g.out_edges.setdefault(v, {})
            g.in_edges.setdefault(v, {})
        for u, v, w in self.edges():
            g.out_edges[v][u] = w
            g.in_edges[u][v] = w
            g.edge_count += 1
        return g

    def copy(self) -> WeightedDigraph:  # type: ignore[override]
        g = self.__class__()
        g.restore_indices(self.index_of_map, self.insertion_order)
        for v in self.insertion_order:
            g.out_edges[v] = dict(self.out_edges[v])
            g.in_edges[v] = dict(self.in_edges[v])
        g.edge_count = self.edge_count
        return g

    def induced_subgraph(self, vertex_subset) -> WeightedDigraph:  # type: ignore[override]
        valid = {v for v in vertex_subset if v in self.index_of_map}
        order = [v for v in self.insertion_order if v in valid]
        idx = {v: i for i, v in enumerate(order)}
        g = self.__class__()
        g.restore_indices(idx, order)
        for v in order:
            g.out_edges.setdefault(v, {})
            g.in_edges.setdefault(v, {})
        for u in order:
            for v, w in self.out_edges[u].items():
                if v in idx:
                    g.out_edges[u][v] = w
                    g.in_edges[v][u] = w
                    g.edge_count += 1
        return g


def contract_sccs(graph: Digraph) -> tuple[list[list[object]], dict[object, int]]:
    """Compute the SCC decomposition and vertex-to-component mapping.

    Args:
        graph: A directed graph.

    Returns:
        A tuple ``(sccs, scc_map)`` where *sccs* is a list of vertex
        lists in insertion order, and *scc_map* maps each vertex to
        its SCC index.

    The SCC list order is determined by Kosaraju's algorithm
    operating on ``graph.iter_vertices()``; vertices inside each SCC
    follow the original insertion order.
    """
    from reachq.core.reachability import strongly_connected_components

    components = strongly_connected_components(graph)
    sccs = [
        sorted(c, key=lambda v: graph.index_of(v)) for c in components
    ]
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        for v in scc:
            scc_map[v] = idx
    return sccs, scc_map


__all__ = [
    "Digraph",
    "WeightedDigraph",
    "contract_sccs",
    "partition_by_labels",
]
