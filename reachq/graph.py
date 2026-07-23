"""Graph data structures for directed graphs.

Follows the notation and definitions from Section 2 (Preliminaries).
Optimized with __slots__ for memory efficiency.

Hierarchy:
    Graph (base) -- vertex storage, shared operations
      Digraph (inherits Graph) -- unweighted directed graph
        WeightedDigraph (inherits Digraph) -- weighted directed graph
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class Graph:
    """Base class for directed graphs.

    Provides vertex management, shared operations (induced_subgraph,
    reversed, copy), and template hooks that subclasses implement
    for type-specific edge storage.

    Attributes:
        vertex_set: The set of vertices V.
        edge_count: Total number of edges |E|.
    """

    __slots__ = ("vertex_set", "out_edges", "in_edges", "edge_count")

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self.vertex_set: set[object] = set()
        self.out_edges: dict[object, Any] = {}
        self.in_edges: dict[object, Any] = {}
        self.edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex to the graph if not already present."""
        if v not in self.vertex_set:
            self.vertex_set.add(v)
            self.initialize_vertex(v)

    def has_vertex(self, v: object) -> bool:
        """Check if vertex v exists in O(1)."""
        return v in self.vertex_set

    def vertices(self) -> set[object]:
        """Return a copy of the vertex set."""
        return set(self.vertex_set)

    def num_vertices(self) -> int:
        """Return n = |V|."""
        return len(self.vertex_set)

    def num_edges(self) -> int:
        """Return m = |E|."""
        return self.edge_count

    def __repr__(self) -> str:
        return f"{type(self).__name__}(n={self.num_vertices()}, m={self.num_edges()})"

    # --- Template hooks (subclasses override) ---

    def initialize_vertex(self, v: object) -> None:
        """Set up adjacency storage for a newly added vertex."""
        raise NotImplementedError

    def iterate_edges_from(self, u: object) -> Iterator[tuple[object, Any]]:
        """Yield (v, data) for each outgoing edge from u."""
        raise NotImplementedError

    def iterate_all_edges(self) -> Iterator[tuple[object, object, Any]]:
        """Yield (u, v, data) for every edge in the graph."""
        for u in self.vertex_set:
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

    # --- Shared operations (use template hooks) ---

    def induced_subgraph(self, vertex_subset: set[object]) -> Graph:
        """Return G[vertex_subset].

        As defined in Section 2.
        """
        subgraph = self.create_empty()
        valid = vertex_subset & self.vertex_set
        for v in valid:
            subgraph.add_vertex(v)
        for u in valid:
            for v, data in self.iterate_edges_from(u):
                if v in valid:
                    subgraph.store_edge(u, v, data)
                    subgraph.edge_count += 1
        return subgraph

    def reversed(self) -> Graph:
        """Return G^R where all edges are flipped."""
        g = self.create_empty()
        g.vertex_set = set(self.vertex_set)
        for v in self.vertex_set:
            g.initialize_vertex(v)
        for u, v, data in self.iterate_all_edges():
            g.store_edge(v, u, data)
            g.edge_count += 1
        return g

    def copy(self) -> Graph:
        """Return a deep copy."""
        g = self.create_empty()
        g.vertex_set = set(self.vertex_set)
        for v in self.vertex_set:
            g.initialize_vertex(v)
        for u in self.vertex_set:
            for v2, data in self.iterate_edges_from(u):
                g.store_edge(u, v2, data)
        g.edge_count = self.edge_count
        return g


class Digraph(Graph):
    """A directed graph G = (V, E) with unweighted edges.

    Vertices are arbitrary hashable objects. Edges are stored as adjacency sets
    for O(1) membership testing. The graph may contain parallel edges.
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
        """Add edge u -> v to the adjacency sets."""
        self.out_edges[u].add(v)
        self.in_edges[v].add(u)

    def create_empty(self) -> Digraph:
        """Create an empty unweighted digraph."""
        return Digraph()

    # --- Covariant return overrides ---

    def induced_subgraph(self, vertex_subset: set[object]) -> Digraph:  # type: ignore[override]
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
        """Add an undirected edge {u, v}: both directions, counted once.

        Useful for symmetric graph generators (Petersen, SRGs, Hamming).
        Increments ``edge_count`` once per pair, regardless of which
        direction is added first.
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
        self.edge_count += 1

    def has_edge(self, u: object, v: object) -> bool:
        """Check if edge (u, v) exists in O(1) time."""
        return v in self.out_edges.get(u, set())

    def edges(self) -> list[tuple[object, object]]:
        """Return the list of edges as ordered pairs (u, v)."""
        return [(u, v) for u in self.vertex_set for v in self.out_edges[u]]

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
            (indptr, indices, n) where indptr and indices are numpy int64
            arrays of shape (n+1,) and (m,) respectively, and n = |V|.
            Neighbors of vertex i are indices[indptr[i]:indptr[i+1]].
        """
        import numpy as np

        index_map, n = _csr_index_map(self)
        indptr = np.zeros(n + 1, dtype=np.int64)
        for v in self.vertex_set:
            i = index_map[v]
            indptr[i + 1] = len(self.out_edges.get(v, set()))
        np.cumsum(indptr, out=indptr)
        indices = np.empty(indptr[-1], dtype=np.int64)
        for v in self.vertex_set:
            i = index_map[v]
            start = indptr[i]
            for j, w in enumerate(self.out_edges.get(v, set())):
                indices[start + j] = index_map[w]
        return indptr, indices, n


def _csr_index_map(graph: Digraph) -> tuple[dict[object, int], int]:
    """Build vertex→index bijection for CSR conversion."""
    index_map: dict[object, int] = {}
    for i, v in enumerate(graph.vertex_set):
        index_map[v] = i
    return index_map, graph.num_vertices()


def partition_by_labels(
    vertices: set[object],
    labels: dict[object, Any],
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality.

    Corresponds to Step 3 of the JLS shortcut set construction (Section 4.1).
    Two vertices are in the same class if and only if their label sets are
    identical.

    Accepts the historical ``set[hashable]`` labels or the compressed
    ``tuple[frozenset[int], frozenset[int]]`` form used by the algorithmic
    refinements. Anything hashable is allowed; mutable inputs are normalised
    via ``frozenset`` so the partition key is always hashable.

    Args:
        vertices: The vertex set to partition.
        labels: A mapping from each vertex to its label value.

    Returns:
        A list of disjoint sets whose union equals *vertices*.
    """
    groups: dict[tuple, set[object]] = {}
    for v in vertices:
        key = labels.get(v)
        if key is None:
            groups.setdefault((), set()).add(v)
            continue
        if not isinstance(key, tuple):
            key = (frozenset(key) if hasattr(key, "__iter__") else key,)
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


class WeightedDigraph(Digraph):
    """A weighted directed graph G = (V, E, w) with non-negative integer weights.

    The paper assumes polynomially bounded non-negative integer weights.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize an empty weighted digraph."""
        Graph.__init__(self)
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
        """Store a weighted edge u -> v with weight data."""
        self.out_edges[u][v] = data
        self.in_edges[v][u] = data

    def create_empty(self) -> WeightedDigraph:
        """Create an empty weighted digraph."""
        return WeightedDigraph()

    # --- Covariant return overrides ---

    def induced_subgraph(self, vertex_subset: set[object]) -> WeightedDigraph:  # type: ignore[override]
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
        """Add a directed edge from u to v with given weight.

        If the edge already exists, keeps the minimum weight.

        Raises:
            ValueError: If weight is negative.
        """
        if weight < 0:
            raise ValueError("Weights must be non-negative.")
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u] or weight < self.out_edges[u][v]:
            if v not in self.out_edges[u]:
                self.edge_count += 1
            self.out_edges[u][v] = weight
            self.in_edges[v][u] = weight

    def has_edge(self, u: object, v: object) -> bool:
        """Check if edge (u, v) exists."""
        return v in self.out_edges.get(u, {})

    def get_weight(self, u: object, v: object) -> int | None:
        """Return weight of edge (u, v) or None if not present."""
        return self.out_edges.get(u, {}).get(v)

    def edges(self) -> list[tuple[object, object, int]]:  # type: ignore[override]
        """Return the list of edges as triples (u, v, weight)."""
        return [(u, v, w) for u in self.vertex_set for v, w in self.out_edges[u].items()]

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
        for v in self.vertex_set:
            g.vertex_set.add(v)
            g.out_edges[v] = set()
            g.in_edges[v] = set()
        for u in self.vertex_set:
            for v in self.out_edges.get(u, {}):
                g.out_edges[u].add(v)
                g.in_edges[v].add(u)
                g.edge_count += 1
        return g


def contract_sccs(graph: Digraph) -> tuple[list[set[object]], dict[object, int]]:
    """Compute the SCC decomposition and vertex-to-component mapping.

    Contracts a directed graph into its strongly connected components.
    Used by shortcut set and hopset construction to reduce cyclic graphs
    to an acyclic condensation DAG.

    Args:
        graph: A directed graph.  Pass ``graph.to_unweighted()`` when the
            input is a :class:`WeightedDigraph`.

    Returns:
        A tuple ``(sccs, scc_map)`` where *sccs* is a list of vertex sets
        (one per SCC) and *scc_map* maps each vertex to its SCC index.
    """
    from reachq.reachability import strongly_connected_components

    sccs = strongly_connected_components(graph)
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        for v in scc:
            scc_map[v] = idx
    return sccs, scc_map
