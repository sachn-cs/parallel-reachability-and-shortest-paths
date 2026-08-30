"""Reachability over hypergraphs.

A hypergraph generalises a directed graph: instead of edges
connecting exactly two vertices, a *hyperedge* connects an arbitrary
non-empty subset of vertices. Formally, a directed hypergraph is a
pair ``(V, E)`` where ``E`` is a set of pairs ``(S, T)`` with
``S, T ⊆ V``, ``S ≠ ∅``, and ``T ≠ ∅``.

A vertex ``v`` is reachable from a source ``s`` iff there is a
sequence of hyperedges ``(S_1, T_1), ..., (S_k, T_k)`` such that:

- ``s ∈ S_1`` (or ``s = s`` trivially)
- for each step, ``T_i ∩ S_{i+1} ≠ ∅`` (a "link" vertex)
- ``v ∈ T_k`` (or any downstream vertex)

Hypergraph reachability generalises standard graph reachability
because ordinary directed edges are exactly the case where
``|S| = |T| = 1``.

**Complexity:** BFS over a directed hypergraph with n vertices and
m hyperedges, each of average size k, costs O(m * k) per source.
For arbitrary k, this is O(m * n) in the worst case.

Reference: Ausiello, Franciosa, Italiano, "Dynamic transitive
closure for directed hypergraphs." (2004). Our implementation is a
straightforward BFS; the dynamic update problem is much harder and
is not addressed here.
"""

from __future__ import annotations

__experimental__ = True


from collections import deque
from collections.abc import Callable, Iterable

from reachq.graph import Digraph

Hyperedge = tuple[frozenset[object], frozenset[object]]
"""A directed hyperedge: (tail set, head set). Both non-empty."""


class DirectedHypergraph:
    """A directed hypergraph with vertex and edge sets.

    Attributes:
        vertices: The vertex set V.
        edges: Tuple of :data:`Hyperedge` records. Immutable view;
            use ``add_edge`` / ``remove_edge`` to mutate.
    """

    __slots__ = ("_edges", "_head_index", "_tail_index", "_vertices")

    def __init__(self) -> None:
        self._vertices: set[object] = set()
        self._edges: list[Hyperedge] = []
        # Inverted index: vertex -> list of edge indices whose tail
        # contains the vertex.
        self._tail_index: dict[object, list[int]] = {}
        # Inverted index: vertex -> list of edge indices whose head
        # contains the vertex.
        self._head_index: dict[object, list[int]] = {}

    @property
    def num_vertices(self) -> int:
        """Number of vertices |V|."""
        return len(self._vertices)

    @property
    def num_edges(self) -> int:
        """Number of hyperedges |E|."""
        return len(self._edges)

    def add_vertex(self, v: object) -> None:
        """Add a vertex. Idempotent."""
        self._vertices.add(v)

    def add_edge(self, tail: Iterable[object], head: Iterable[object]) -> int:
        """Add a hyperedge (tail, head).

        Both ``tail`` and ``head`` must be non-empty. The edge's
        index is returned.

        Raises:
            ValueError: If tail or head is empty.
        """
        tail_set = frozenset(tail)
        head_set = frozenset(head)
        if not tail_set:
            raise ValueError("hyperedge tail must be non-empty")
        if not head_set:
            raise ValueError("hyperedge head must be non-empty")
        for v in tail_set | head_set:
            self._vertices.add(v)
        idx = len(self._edges)
        self._edges.append((tail_set, head_set))
        for v in tail_set:
            self._tail_index.setdefault(v, []).append(idx)
        for v in head_set:
            self._head_index.setdefault(v, []).append(idx)
        return idx

    def edges(self) -> list[Hyperedge]:
        """Return a list of all hyperedges."""
        return list(self._edges)

    def vertices(self) -> set[object]:
        """Return the vertex set."""
        return set(self._vertices)

    def __repr__(self) -> str:
        return f"DirectedHypergraph(V={self.num_vertices}, |E|={self.num_edges})"


def hyper_reachable(hg: DirectedHypergraph, source: object) -> set[object]:
    """Return all vertices reachable from ``source`` in the hypergraph.

    Implements the BFS-style reachability algorithm for directed
    hypergraphs: a vertex is reachable iff it can be reached via a
    sequence of hyperedges where consecutive edges share a "link"
    vertex in (head of previous, tail of next).

    The source vertex itself is included in the result (reflexive
    closure). If ``source`` is not a vertex of the hypergraph, the
    empty set is returned.

    Args:
        hg: The input directed hypergraph.
        source: Starting vertex.

    Returns:
        Set of reachable vertices including ``source``.
    """
    if source not in hg._vertices:
        return set()
    visited: set[object] = {source}
    # Each queue entry is a "frontier vertex" that has just been
    # reached; we fire every hyperedge whose tail contains it.
    q: deque[object] = deque([source])
    while q:
        u = q.popleft()
        for edge_idx in hg._tail_index.get(u, ()):
            tail, head = hg._edges[edge_idx]
            del tail
            for v in head:
                if v not in visited:
                    visited.add(v)
                    q.append(v)
    return visited


def hypergraph_from_digraph(graph: Digraph) -> DirectedHypergraph:
    """Lift a :class:`~reachq.core.graph.Digraph` into a directed
    hypergraph by treating each directed edge (u, v) as a hyperedge
    (S={u}, T={v}).

    This is the canonical embedding of ordinary directed graphs into
    directed hypergraphs.

    Args:
        graph: The input digraph.

    Returns:
        A :class:`DirectedHypergraph` representing the same graph.
    """
    hg = DirectedHypergraph()
    for v in graph.vertices():
        hg.add_vertex(v)
    for u, v in graph.edges():
        hg.add_edge((u,), (v,))
    return hg


def hyper_to_digraph(
    hg: DirectedHypergraph,
    *,
    vertex_pred: Callable[[object], bool] | None = None,
) -> Digraph:
    """Convert a hypergraph into an equivalent Digraph by materialising
    every (tail_member, head_member) edge pair.

    The result is a standard directed graph where each hyperedge
    ``(S, T)`` becomes ``|S| * |T|`` ordinary edges. Useful for
    interop with the rest of :mod:`reachq` (which operates on
    :class:`Digraph`).

    Args:
        hg: The input directed hypergraph.
        vertex_pred: Optional callable ``f(v) -> bool`` to include
            only matching vertices in the resulting Digraph.

    Returns:
        A :class:`Digraph` with one edge per (s, t) where s ∈ S and
        t ∈ T for some hyperedge (S, T).
    """
    g = Digraph()
    for v in hg._vertices:
        if vertex_pred is not None and not vertex_pred(v):
            continue
        g.add_vertex(v)
    for tail, head in hg._edges:
        for s in tail:
            for t in head:
                if s == t:
                    continue
                g.add_edge(s, t)
    return g
