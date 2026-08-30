"""Graph data structures for directed graphs.

Follows the notation and definitions from Section 2 (Preliminaries).

Hierarchy:

    Graph (base) -- vertex storage, shared operations
      Digraph (inherits Graph) -- unweighted directed graph
        WeightedDigraph (inherits Digraph) -- weighted directed graph

Vertex storage guarantees:

    * Insertion order is preserved as the canonical vertex index. SCC,
      sampling, partitioning, recursion, and CSR all index by
      insertion order so that algorithms are deterministic across
      processes regardless of ``PYTHONHASHSEED``.
    * ``vertices()`` returns a tuple in insertion order.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any


class Graph:
    """Base class for directed graphs.

    Vertices are arbitrary hashable objects. Edges are stored as
    adjacency maps for O(1) membership testing. Insertion order is
    preserved as a stable internal index.

    Attributes:
        edge_count: Total number of edges |E|.
        out_edges: Per-source adjacency storage (type decided by subclass).
        in_edges: Per-target adjacency storage (type decided by subclass).
    """

    __slots__ = (
        "_index_of",
        "_insertion_order",
        "edge_count",
        "in_edges",
        "out_edges",
    )

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._insertion_order: list[object] = []
        self._index_of: dict[object, int] = {}
        self.out_edges: dict[object, Any] = {}
        self.in_edges: dict[object, Any] = {}
        self.edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex, assigning it the next insertion-order index."""
        if v not in self._index_of:
            self._index_of[v] = len(self._insertion_order)
            self._insertion_order.append(v)
            self.initialize_vertex(v)

    def has_vertex(self, v: object) -> bool:
        """Check whether ``v`` is in the vertex set."""
        return v in self._index_of

    def vertices(self) -> tuple[object, ...]:
        """Return all vertices in insertion order as a tuple."""
        return tuple(self._insertion_order)

    def iter_vertices(self) -> Iterator[object]:
        """Iterate vertices in insertion order without copying."""
        return iter(self._insertion_order)

    def num_vertices(self) -> int:
        """Return ``n = |V|``."""
        return len(self._insertion_order)

    def num_edges(self) -> int:
        """Return ``m = |E|``."""
        return self.edge_count

    def index_of(self, v: object) -> int:
        """Return the insertion-order index of ``v``."""
        return self._index_of[v]

    def vertex_at(self, i: int) -> object:
        """Return the vertex at insertion-order index ``i``."""
        return self._insertion_order[i]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(n={self.num_vertices()}, m={self.num_edges()})"

    def __contains__(self, v: object) -> bool:
        return v in self._index_of

    def __iter__(self) -> Iterator[object]:
        return iter(self._insertion_order)

    def __len__(self) -> int:
        return len(self._insertion_order)

    # --- Template hooks (subclasses override) ---

    def initialize_vertex(self, v: object) -> None:
        """Set up adjacency storage for a newly added vertex."""
        raise NotImplementedError

    def iterate_edges_from(self, u: object) -> Iterator[tuple[object, Any]]:
        """Yield (v, data) for each outgoing edge from u."""
        raise NotImplementedError

    def iterate_all_edges(self) -> Iterator[tuple[object, object, Any]]:
        """Yield (u, v, data) for every edge in the graph."""
        for u in self._insertion_order:
            for v, data in self.iterate_edges_from(u):
                yield u, v, data

    def store_edge(self, u: object, v: object, data: Any) -> None:
        """Store an edge in the adjacency structure.

        Does NOT increment edge_count -- callers manage that.
        """
        raise NotImplementedError

    def create_empty(self) -> Graph:
        """Create an empty graph of the same concrete type."""
        raise NotImplementedError

    def _restore_indices_from(self, mapping: dict[object, int], order: list[object]) -> None:
        """Restore ``_index_of`` / ``_insertion_order`` from another graph.

        Used by copy/reversed/induced_subgraph when rebasing adjacency
        to a new instance. The mapping is the source graph's
        ``_index_of`` and ``order`` is its ``_insertion_order``; both
        must describe the same vertex set.
        """
        self._index_of = dict(mapping)
        self._insertion_order = list(order)

    # --- Shared operations (use template hooks) ---

    def induced_subgraph(self, vertex_subset) -> Graph:
        """Return ``G[vertex_subset]``.

        ``vertex_subset`` is any iterable of vertices already in the
        graph. Vertices outside the original graph are silently
        ignored.
        """
        valid = {v for v in vertex_subset if v in self._index_of}
        subgraph = self.create_empty()
        order = [v for v in self._insertion_order if v in valid]
        idx = {v: i for i, v in enumerate(order)}
        subgraph._restore_indices_from(idx, order)
        for v in order:
            subgraph.initialize_vertex(v)
        for u in order:
            for v, data in self.iterate_edges_from(u):
                if v in idx:
                    subgraph.store_edge(u, v, data)
                    subgraph.edge_count += 1
        return subgraph

    def reversed(self) -> Graph:
        """Return ``G^R`` where all edges are flipped."""
        g = self.create_empty()
        g._restore_indices_from(self._index_of, self._insertion_order)
        for v in self._insertion_order:
            g.initialize_vertex(v)
        for u, v, data in self.iterate_all_edges():
            g.store_edge(v, u, data)
            g.edge_count += 1
        return g

    def copy(self) -> Graph:
        """Return a deep copy."""
        g = self.create_empty()
        g._restore_indices_from(self._index_of, self._insertion_order)
        for v in self._insertion_order:
            g.initialize_vertex(v)
        for u in self._insertion_order:
            for v2, data in self.iterate_edges_from(u):
                g.store_edge(u, v2, data)
        g.edge_count = self.edge_count
        return g


class Digraph(Graph):
    """A directed graph ``G = (V, E)`` with unweighted edges.

    Vertices are arbitrary hashable objects. Edges are stored as
    adjacency sets for O(1) membership testing. The graph may contain
    parallel edges (inserted via ``add_edge``; equivalent to the
    single edge at the multiplicity of the call).
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize an empty digraph."""
        super().__init__()
        self.out_edges: dict[object, set[object]] = {}
        self.in_edges: dict[object, set[object]] = {}

    # --- Template hook implementations ---

    def initialize_vertex(self, v: object) -> None:
        """Initialize adjacency sets for vertex v."""
        self.out_edges[v] = set()
        self.in_edges[v] = set()

    def iterate_edges_from(self, u: object) -> Iterator[tuple[object, None]]:
        """Yield (v, None) for each outgoing edge from u."""
        for v in self.out_edges.get(u, set()):
            yield v, None

    def store_edge(self, u: object, v: object, data: None) -> None:  # type: ignore[override]
        """Add edge ``u -> v`` to the adjacency sets."""
        self.out_edges[u].add(v)
        self.in_edges[v].add(u)

    def create_empty(self) -> Digraph:
        """Create an empty unweighted digraph."""
        return Digraph()

    # --- Covariant return overrides ---

    def induced_subgraph(self, vertex_subset) -> Digraph:  # type: ignore[override]
        """Return the induced subgraph as a Digraph."""
        return super().induced_subgraph(vertex_subset)  # type: ignore[return-value]

    def reversed(self) -> Digraph:  # type: ignore[override]
        """Return the reversed graph as a Digraph."""
        return super().reversed()  # type: ignore[return-value]

    def copy(self) -> Digraph:  # type: ignore[override]
        """Return a deep copy as a Digraph."""
        return super().copy()  # type: ignore[return-value]

    # --- Concrete API ---

    def add_edge(self, u: object, v: object) -> None:
        """Add a directed edge from u to v."""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u]:
            self.out_edges[u].add(v)
            self.in_edges[v].add(u)
            self.edge_count += 1

    def add_undirected_edge(self, u: object, v: object) -> None:
        """Add an undirected edge ``{u, v}``: both directions, two directed edges.

        Useful for symmetric graph generators (Petersen, SRGs, Hamming).
        Increments ``edge_count`` twice (one per directed edge), matching
        ``num_edges()``'s contract of counting directed edges.
        """
        if u == v:
            raise ValueError("self-loops not supported")
        self.add_vertex(u)
        self.add_vertex(v)
        if v in self.out_edges[u]:
            return  # already added
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
        return [(u, v) for u in self._insertion_order for v in self.out_edges[u]]

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

    def to_csr(self) -> tuple[Any, Any, int]:
        """Convert adjacency to CSR arrays for numpy-based algorithms.

        Returns:
            (indptr, indices, n) where ``indptr`` and ``indices`` are
            int64 numpy arrays of shapes ``(n+1,)`` and ``(m,)``
            respectively. The vertex index used is the insertion-order
            index from ``index_of``.
        """
        import numpy as np

        n = self.num_vertices()
        indptr = np.zeros(n + 1, dtype=np.int64)
        for i, v in enumerate(self._insertion_order):
            indptr[i + 1] = len(self.out_edges.get(v, set()))
        np.cumsum(indptr, out=indptr)
        indices = np.empty(indptr[-1], dtype=np.int64)
        for i, v in enumerate(self._insertion_order):
            start = indptr[i]
            for j, w in enumerate(self.out_edges.get(v, set())):
                indices[start + j] = self._index_of[w]
        return indptr, indices, n


def partition_by_labels(
    vertices,
    labels: dict[object, Any],
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality.

    Accepts any hashable label value. Tuples of frozensets and bare
    frozensets both work without normalisation.

    Args:
        vertices: The vertex container to partition.
        labels: A mapping from each vertex to its label value.
            Vertices missing from the mapping group under the empty
            label.

    Returns:
        A list of disjoint sets whose union covers the input vertices.
    """
    groups: dict[tuple, set[object]] = {}
    seen: set[object] = set()
    for v in vertices:
        if v in seen:
            continue
        seen.add(v)
        key = labels.get(v)
        if key is None:
            groups.setdefault((), set()).add(v)
            continue
        if not isinstance(key, tuple):
            key = (frozenset(key) if hasattr(key, "__iter__") else key,)
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


class WeightedDigraph(Digraph):
    """A weighted directed graph ``G = (V, E, w)`` with non-negative integer weights.

    The paper assumes polynomially bounded non-negative integer
    weights. Weights are strictly ``int`` (excluding ``bool`` and
    non-finite floats); passing anything else raises ``TypeError``.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize an empty weighted digraph."""
        super().__init__()
        self.out_edges: dict[object, dict[object, int]] = {}  # type: ignore[assignment]
        self.in_edges: dict[object, dict[object, int]] = {}  # type: ignore[assignment]

    # --- Override template hooks for weighted storage ---

    def initialize_vertex(self, v: object) -> None:
        """Initialize weighted adjacency dicts for vertex v."""
        self.out_edges[v] = {}
        self.in_edges[v] = {}

    def iterate_edges_from(self, u: object) -> Iterator[tuple[object, int]]:  # type: ignore[override]
        """Yield (v, weight) for each outgoing edge from u."""
        yield from self.out_edges.get(u, {}).items()

    def store_edge(self, u: object, v: object, data: int) -> None:  # type: ignore[override]
        """Store a weighted edge ``u -> v`` with weight ``data``."""
        self.out_edges[u][v] = data
        self.in_edges[v][u] = data

    def create_empty(self) -> WeightedDigraph:
        """Create an empty weighted digraph."""
        return WeightedDigraph()

    # --- Covariant return overrides ---

    def induced_subgraph(self, vertex_subset) -> WeightedDigraph:  # type: ignore[override]
        """Return the induced subgraph as a WeightedDigraph."""
        return super().induced_subgraph(vertex_subset)  # type: ignore[return-value]

    def reversed(self) -> WeightedDigraph:  # type: ignore[override]
        """Return the reversed graph as a WeightedDigraph."""
        return super().reversed()  # type: ignore[return-value]

    def copy(self) -> WeightedDigraph:  # type: ignore[override]
        """Return a deep copy as a WeightedDigraph."""
        return super().copy()  # type: ignore[return-value]

    # --- Overridden API ---

    def add_edge(self, u: object, v: object, weight: int) -> None:  # type: ignore[override]
        """Add a directed edge with weight.

        Args:
            u: Source vertex; added if not present.
            v: Target vertex; added if not present.
            weight: Non-negative integer weight.

        Raises:
            TypeError: If ``weight`` is not an ``int`` (excluding
                ``bool``), is not finite, or is non-integral.
            ValueError: If ``weight`` is negative.
        """
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise TypeError(
                f"weight must be a non-negative int (got {type(weight).__name__}: "
                f"{weight!r})"
            )
        if weight < 0:
            raise ValueError(f"weight must be non-negative (got {weight!r})")

        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u] or weight < self.out_edges[u][v]:
            if v not in self.out_edges[u]:
                self.edge_count += 1
            self.out_edges[u][v] = weight
            self.in_edges[v][u] = weight

    def has_edge(self, u: object, v: object) -> bool:
        """Check whether edge (u, v) exists."""
        return v in self.out_edges.get(u, {})

    def get_weight(self, u: object, v: object) -> int | None:
        """Return weight of edge (u, v) or None if not present."""
        return self.out_edges.get(u, {}).get(v)

    def edges(self) -> list[tuple[object, object, int]]:  # type: ignore[override]
        """Return the list of edges as triples in insertion order."""
        return [
            (u, v, w)
            for u in self._insertion_order
            for v, w in self.out_edges[u].items()
        ]

    def out_neighbors(self, v: object) -> dict[object, int]:  # type: ignore[override]
        """Return the out-neighbors of v with weights as a dict."""
        return dict(self.out_edges.get(v, {}))

    def in_neighbors(self, v: object) -> dict[object, int]:  # type: ignore[override]
        """Return the in-neighbors of v with weights as a dict."""
        return dict(self.in_edges.get(v, {}))

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self.out_edges.get(v, {}))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self.in_edges.get(v, {}))

    def to_unweighted(self) -> Digraph:
        """Return the underlying unweighted digraph."""
        g = Digraph()
        g._restore_indices_from(self._index_of, self._insertion_order)
        for v in self._insertion_order:
            g.initialize_vertex(v)
        for u in self._insertion_order:
            for v in self.out_edges.get(u, {}):
                g.out_edges[u].add(v)
                g.in_edges[v].add(u)
                g.edge_count += 1
        return g


def contract_sccs(graph: Digraph) -> tuple[list[list[object]], dict[object, int]]:
    """Compute the SCC decomposition and vertex-to-component mapping.

    Args:
        graph: A directed graph. Pass ``graph.to_unweighted()`` when
            the input is a :class:`WeightedDigraph`.

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
    sccs = [sorted(c, key=lambda v: graph.index_of(v)) for c in components]
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        for v in scc:
            scc_map[v] = idx
    return sccs, scc_map
