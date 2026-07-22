"""Graph data structures for directed graphs.

Follows the notation and definitions from Section 2 (Preliminaries).
Optimized with __slots__ for memory efficiency.
"""

from __future__ import annotations


class Digraph:
    """A directed graph G = (V, E) with unweighted edges.

    Vertices are arbitrary hashable objects. Edges are stored as adjacency sets
    for O(1) membership testing. The graph may contain parallel edges.
    """

    __slots__ = ("_vertices", "_out_edges", "_in_edges", "_edge_count")

    def __init__(self) -> None:
        """Initialize an empty digraph."""
        self._vertices: set[object] = set()
        self._out_edges: dict[object, set[object]] = {}
        self._in_edges: dict[object, set[object]] = {}
        self._edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex to the graph if not already present."""
        if v not in self._vertices:
            self._vertices.add(v)
            self._out_edges[v] = set()
            self._in_edges[v] = set()

    def add_edge(self, u: object, v: object) -> None:
        """Add a directed edge from u to v."""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self._out_edges[u]:
            self._out_edges[u].add(v)
            self._in_edges[v].add(u)
            self._edge_count += 1

    def has_edge(self, u: object, v: object) -> bool:
        """Check if edge (u, v) exists in O(1) time."""
        return v in self._out_edges.get(u, set())

    def vertices(self) -> set[object]:
        """Return the set of vertices V."""
        return set(self._vertices)

    def edges(self) -> list[tuple[object, object]]:
        """Return the list of edges E as ordered pairs (u, v)."""
        return [
            (u, v)
            for u in self._vertices
            for v in self._out_edges[u]
        ]

    def out_neighbors(self, v: object) -> set[object]:
        """Return the out-neighbors of v as a set."""
        return set(self._out_edges.get(v, set()))

    def in_neighbors(self, v: object) -> set[object]:
        """Return the in-neighbors of v as a set."""
        return set(self._in_edges.get(v, set()))

    def num_vertices(self) -> int:
        """Return n = |V|."""
        return len(self._vertices)

    def num_edges(self) -> int:
        """Return m = |E|."""
        return self._edge_count

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self._out_edges.get(v, set()))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self._in_edges.get(v, set()))

    def induced_subgraph(self, vertex_subset: set[object]) -> Digraph:
        """Return the induced subgraph G[vertex_subset].

        As defined in Section 2.
        """
        subgraph = Digraph()
        valid = vertex_subset & self._vertices
        for v in valid:
            subgraph._vertices.add(v)
            subgraph._out_edges[v] = set()
            subgraph._in_edges[v] = set()
        for u in valid:
            for v in self._out_edges[u] & valid:
                subgraph._out_edges[u].add(v)
                subgraph._in_edges[v].add(u)
                subgraph._edge_count += 1
        return subgraph

    def reversed(self) -> Digraph:
        """Return the reversed graph G^R where all edges are flipped."""
        g = Digraph()
        g._vertices = set(self._vertices)
        g._out_edges = {v: set() for v in self._vertices}
        g._in_edges = {v: set() for v in self._vertices}
        for u, v in self.edges():
            g._out_edges[v].add(u)
            g._in_edges[u].add(v)
            g._edge_count += 1
        return g

    def copy(self) -> Digraph:
        """Return a deep copy of this digraph."""
        g = Digraph()
        g._vertices = set(self._vertices)
        for v in self._vertices:
            g._out_edges[v] = set(self._out_edges[v])
            g._in_edges[v] = set(self._in_edges[v])
        g._edge_count = self._edge_count
        return g

    def __repr__(self) -> str:
        return f"Digraph(n={self.num_vertices()}, m={self.num_edges()})"


def partition_by_labels(
    vertices: set[object], labels: dict[object, set[str]]
) -> list[set[object]]:
    """Partition vertices into equivalence classes by exact label equality.

    Corresponds to Step 3 of the JLS shortcut set construction (Section 4.1).
    Two vertices are in the same class if and only if their label sets are
    identical.

    Args:
        vertices: The vertex set to partition.
        labels: A mapping from each vertex to its label set.

    Returns:
        A list of disjoint sets whose union equals *vertices*.
    """
    groups: dict[frozenset, set[object]] = {}
    for v in vertices:
        key = frozenset(labels.get(v, set()))
        groups.setdefault(key, set()).add(v)
    return list(groups.values())


class WeightedDigraph:
    """A weighted directed graph G = (V, E, w) with non-negative integer weights.

    The paper assumes polynomially bounded non-negative integer weights.
    """

    __slots__ = ("_vertices", "_out_edges", "_in_edges", "_edge_count")

    def __init__(self) -> None:
        """Initialize an empty weighted digraph."""
        self._vertices: set[object] = set()
        self._out_edges: dict[object, dict[object, int]] = {}
        self._in_edges: dict[object, dict[object, int]] = {}
        self._edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex to the graph if not already present."""
        if v not in self._vertices:
            self._vertices.add(v)
            self._out_edges[v] = {}
            self._in_edges[v] = {}

    def add_edge(self, u: object, v: object, weight: int) -> None:
        """Add a directed edge from u to v with given weight.

        If the edge already exists, keeps the minimum weight.

        Raises:
            ValueError: If weight is negative.
        """
        if weight < 0:
            raise ValueError("Weights must be non-negative.")
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self._out_edges[u] or weight < self._out_edges[u][v]:
            if v not in self._out_edges[u]:
                self._edge_count += 1
            self._out_edges[u][v] = weight
            self._in_edges[v][u] = weight

    def has_edge(self, u: object, v: object) -> bool:
        """Check if edge (u, v) exists."""
        return v in self._out_edges.get(u, {})

    def get_weight(self, u: object, v: object) -> int | None:
        """Return weight of edge (u, v) or None if not present."""
        return self._out_edges.get(u, {}).get(v)

    def vertices(self) -> set[object]:
        """Return the set of vertices V."""
        return set(self._vertices)

    def edges(self) -> list[tuple[object, object, int]]:
        """Return the list of edges as triples (u, v, weight)."""
        return [
            (u, v, w)
            for u in self._vertices
            for v, w in self._out_edges[u].items()
        ]

    def out_neighbors(self, v: object) -> dict[object, int]:
        """Return the out-neighbors of v with weights as a dict."""
        return dict(self._out_edges.get(v, {}))

    def in_neighbors(self, v: object) -> dict[object, int]:
        """Return the in-neighbors of v with weights as a dict."""
        return dict(self._in_edges.get(v, {}))

    def num_vertices(self) -> int:
        """Return n = |V|."""
        return len(self._vertices)

    def num_edges(self) -> int:
        """Return m = |E|."""
        return self._edge_count

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self._out_edges.get(v, {}))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self._in_edges.get(v, {}))

    def induced_subgraph(self, vertex_subset: set[object]) -> WeightedDigraph:
        """Return the induced subgraph G[vertex_subset]."""
        subgraph = WeightedDigraph()
        valid = vertex_subset & self._vertices
        for v in valid:
            subgraph._vertices.add(v)
            subgraph._out_edges[v] = {}
            subgraph._in_edges[v] = {}
        for u in valid:
            for v, w in self._out_edges[u].items():
                if v in valid:
                    subgraph._out_edges[u][v] = w
                    subgraph._in_edges[v][u] = w
                    subgraph._edge_count += 1
        return subgraph

    def reversed(self) -> WeightedDigraph:
        """Return the reversed graph where all edges are flipped."""
        g = WeightedDigraph()
        g._vertices = set(self._vertices)
        for v in self._vertices:
            g._out_edges[v] = {}
            g._in_edges[v] = {}
        for u, v, w in self.edges():
            g._out_edges[v][u] = w
            g._in_edges[u][v] = w
            g._edge_count += 1
        return g

    def copy(self) -> WeightedDigraph:
        """Return a deep copy of this weighted digraph."""
        g = WeightedDigraph()
        g._vertices = set(self._vertices)
        for v in self._vertices:
            g._out_edges[v] = dict(self._out_edges[v])
            g._in_edges[v] = dict(self._in_edges[v])
        g._edge_count = self._edge_count
        return g

    def to_unweighted(self) -> Digraph:
        """Return the underlying unweighted digraph."""
        g = Digraph()
        for v in self._vertices:
            g._vertices.add(v)
            g._out_edges[v] = set()
            g._in_edges[v] = set()
        for u, v, _ in self.edges():
            g._out_edges[u].add(v)
            g._in_edges[v].add(u)
            g._edge_count += 1
        return g

    def __repr__(self) -> str:
        return f"WeightedDigraph(n={self.num_vertices()}, m={self.num_edges()})"
