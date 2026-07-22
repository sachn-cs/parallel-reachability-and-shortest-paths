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

    __slots__ = ("vertex_set", "out_edges", "in_edges", "edge_count")

    def __init__(self) -> None:
        """Initialize an empty digraph."""
        self.vertex_set: set[object] = set()
        self.out_edges: dict[object, set[object]] = {}
        self.in_edges: dict[object, set[object]] = {}
        self.edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex to the graph if not already present."""
        if v not in self.vertex_set:
            self.vertex_set.add(v)
            self.out_edges[v] = set()
            self.in_edges[v] = set()

    def add_edge(self, u: object, v: object) -> None:
        """Add a directed edge from u to v."""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.out_edges[u]:
            self.out_edges[u].add(v)
            self.in_edges[v].add(u)
            self.edge_count += 1

    def has_edge(self, u: object, v: object) -> bool:
        """Check if edge (u, v) exists in O(1) time."""
        return v in self.out_edges.get(u, set())

    def vertices(self) -> set[object]:
        """Return the set of vertices V."""
        return set(self.vertex_set)

    def edges(self) -> list[tuple[object, object]]:
        """Return the list of edges E as ordered pairs (u, v)."""
        return [
            (u, v)
            for u in self.vertex_set
            for v in self.out_edges[u]
        ]

    def out_neighbors(self, v: object) -> set[object]:
        """Return the out-neighbors of v as a set."""
        return set(self.out_edges.get(v, set()))

    def in_neighbors(self, v: object) -> set[object]:
        """Return the in-neighbors of v as a set."""
        return set(self.in_edges.get(v, set()))

    def num_vertices(self) -> int:
        """Return n = |V|."""
        return len(self.vertex_set)

    def num_edges(self) -> int:
        """Return m = |E|."""
        return self.edge_count

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self.out_edges.get(v, set()))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self.in_edges.get(v, set()))

    def induced_subgraph(self, vertex_subset: set[object]) -> Digraph:
        """Return the induced subgraph G[vertex_subset].

        As defined in Section 2.
        """
        subgraph = Digraph()
        valid = vertex_subset & self.vertex_set
        for v in valid:
            subgraph.vertex_set.add(v)
            subgraph.out_edges[v] = set()
            subgraph.in_edges[v] = set()
        for u in valid:
            for v in self.out_edges[u] & valid:
                subgraph.out_edges[u].add(v)
                subgraph.in_edges[v].add(u)
                subgraph.edge_count += 1
        return subgraph

    def reversed(self) -> Digraph:
        """Return the reversed graph G^R where all edges are flipped."""
        g = Digraph()
        g.vertex_set = set(self.vertex_set)
        g.out_edges = {v: set() for v in self.vertex_set}
        g.in_edges = {v: set() for v in self.vertex_set}
        for u, v in self.edges():
            g.out_edges[v].add(u)
            g.in_edges[u].add(v)
            g.edge_count += 1
        return g

    def copy(self) -> Digraph:
        """Return a deep copy of this digraph."""
        g = Digraph()
        g.vertex_set = set(self.vertex_set)
        for v in self.vertex_set:
            g.out_edges[v] = set(self.out_edges[v])
            g.in_edges[v] = set(self.in_edges[v])
        g.edge_count = self.edge_count
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

    __slots__ = ("vertex_set", "out_edges", "in_edges", "edge_count")

    def __init__(self) -> None:
        """Initialize an empty weighted digraph."""
        self.vertex_set: set[object] = set()
        self.out_edges: dict[object, dict[object, int]] = {}
        self.in_edges: dict[object, dict[object, int]] = {}
        self.edge_count: int = 0

    def add_vertex(self, v: object) -> None:
        """Add a vertex to the graph if not already present."""
        if v not in self.vertex_set:
            self.vertex_set.add(v)
            self.out_edges[v] = {}
            self.in_edges[v] = {}

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

    def vertices(self) -> set[object]:
        """Return the set of vertices V."""
        return set(self.vertex_set)

    def edges(self) -> list[tuple[object, object, int]]:
        """Return the list of edges as triples (u, v, weight)."""
        return [
            (u, v, w)
            for u in self.vertex_set
            for v, w in self.out_edges[u].items()
        ]

    def out_neighbors(self, v: object) -> dict[object, int]:
        """Return the out-neighbors of v with weights as a dict."""
        return dict(self.out_edges.get(v, {}))

    def in_neighbors(self, v: object) -> dict[object, int]:
        """Return the in-neighbors of v with weights as a dict."""
        return dict(self.in_edges.get(v, {}))

    def num_vertices(self) -> int:
        """Return n = |V|."""
        return len(self.vertex_set)

    def num_edges(self) -> int:
        """Return m = |E|."""
        return self.edge_count

    def degree_out(self, v: object) -> int:
        """Return out-degree of v."""
        return len(self.out_edges.get(v, {}))

    def degree_in(self, v: object) -> int:
        """Return in-degree of v."""
        return len(self.in_edges.get(v, {}))

    def induced_subgraph(self, vertex_subset: set[object]) -> WeightedDigraph:
        """Return the induced subgraph G[vertex_subset]."""
        subgraph = WeightedDigraph()
        valid = vertex_subset & self.vertex_set
        for v in valid:
            subgraph.vertex_set.add(v)
            subgraph.out_edges[v] = {}
            subgraph.in_edges[v] = {}
        for u in valid:
            for v, w in self.out_edges[u].items():
                if v in valid:
                    subgraph.out_edges[u][v] = w
                    subgraph.in_edges[v][u] = w
                    subgraph.edge_count += 1
        return subgraph

    def reversed(self) -> WeightedDigraph:
        """Return the reversed graph where all edges are flipped."""
        g = WeightedDigraph()
        g.vertex_set = set(self.vertex_set)
        for v in self.vertex_set:
            g.out_edges[v] = {}
            g.in_edges[v] = {}
        for u, v, w in self.edges():
            g.out_edges[v][u] = w
            g.in_edges[u][v] = w
            g.edge_count += 1
        return g

    def copy(self) -> WeightedDigraph:
        """Return a deep copy of this weighted digraph."""
        g = WeightedDigraph()
        g.vertex_set = set(self.vertex_set)
        for v in self.vertex_set:
            g.out_edges[v] = dict(self.out_edges[v])
            g.in_edges[v] = dict(self.in_edges[v])
        g.edge_count = self.edge_count
        return g

    def to_unweighted(self) -> Digraph:
        """Return the underlying unweighted digraph."""
        g = Digraph()
        for v in self.vertex_set:
            g.vertex_set.add(v)
            g.out_edges[v] = set()
            g.in_edges[v] = set()
        for u in self.vertex_set:
            for v in self.out_edges.get(u, set()):
                g.out_edges[u].add(v)
                g.in_edges[v].add(u)
                g.edge_count += 1
        return g

    def __repr__(self) -> str:
        return f"WeightedDigraph(n={self.num_vertices()}, m={self.num_edges()})"


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
    from prspnsd.reachability import strongly_connected_components

    sccs = strongly_connected_components(graph)
    scc_map: dict[object, int] = {}
    for idx, scc in enumerate(sccs):
        for v in scc:
            scc_map[v] = idx
    return sccs, scc_map
