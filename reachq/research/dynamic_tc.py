"""Dynamic transitive closure maintenance.

Maintains the transitive closure of a directed graph under edge
insertions and deletions. This is a *naive* implementation suitable
for correctness verification and small-graph testing; it does not
achieve polylog amortised update time.

**Complexity (honest scope):**

- Insert: `O(n^2)` worst case. After inserting (u, v), every vertex x
  that can reach u now also reaches every vertex in v's reachable
  set (R+(v)), and every vertex y that v reaches can also reach
  every vertex that u reaches. The implementation walks these
  relations explicitly.

- Delete: `O(n^2)` worst case. After deleting (u, v), we recompute
  the affected rows and columns of the reachability matrix by BFS
  from u (for u's forward reachability) and from predecessors of u
  (for their forward reachability through u). The naive approach
  is to recompute the full matrix in O(n * (n + m)) work.

For fully-dynamic transitive closure with polylog update time, see
Demetrescu-Italiano (FOCS 2000) and subsequent work. That algorithm
is materially more complex than the naive approach and is not
included here.

This module's purpose is to give users a working, correct
implementation for small to medium graphs (n < ~10k) and to serve
as a baseline against which any future optimized implementation can
be benchmarked.
"""




from __future__ import annotations


__experimental__ = True



from collections.abc import Iterable

from reachq.core.graph import Digraph


class DynamicTransitiveClosure:
    """Incremental transitive closure with explicit edge updates.

    Internally maintains a boolean reachability matrix as a
    `set[tuple[int, int]]` of (index_a, index_b) pairs. The
    matrix is updated eagerly on every insertion and deletion.

    Attributes:
        graph: The underlying digraph (mutated by `insert_edge`
            and `delete_edge` to stay in sync with the matrix).
        vertices: Tuple of vertex objects in canonical order.
    """

    __slots__ = ("_index", "_reach", "graph", "vertices")

    def __init__(self, graph: Digraph) -> None:
        self.graph = graph
        self.vertices: tuple[object, ...] = tuple(graph.vertices())
        self._index: dict[object, int] = {v: i for i, v in enumerate(self.vertices)}
        self._reach: set[tuple[int, int]] = self.compute_full_tc()

    def compute_full_tc(self) -> set[tuple[int, int]]:
        """Recompute the full transitive closure from scratch via BFS."""
        from collections import deque

        n = len(self.vertices)
        reach: set[tuple[int, int]] = set()
        out_edges_idx: dict[int, list[int]] = {i: [] for i in range(n)}
        for u, v in self.graph.edges():
            iu = self._index[u]
            iv = self._index[v]
            out_edges_idx[iu].append(iv)
        # Each vertex reaches itself (reflexive closure).
        for i in range(n):
            reach.add((i, i))
        # BFS from each vertex.
        for source_idx in range(n):
            visited: set[int] = {source_idx}
            q: deque[int] = deque([source_idx])
            while q:
                u = q.popleft()
                for w in out_edges_idx.get(u, []):
                    if w not in visited:
                        visited.add(w)
                        q.append(w)
            for v in visited:
                reach.add((source_idx, v))
        return reach

    def insert_edge(self, u: object, v: object) -> None:
        """Insert edge (u, v) into the graph and update the closure.

        Updates the graph adjacency (which `self.graph` owns) and
        then augments the reachability matrix to reflect the new
        edge. Cost: `O(n^2)` in the worst case (a hub vertex that
        reaches or is reached by everything).

        Args:
            u: Source vertex.
            v: Target vertex.

        Raises:
            KeyError: If `u` or `v` is not in the graph's vertex
                set. Use `graph.add_vertex` first.
        """
        if u not in self._index:
            raise KeyError(f"vertex {u!r} not in graph")
        if v not in self._index:
            raise KeyError(f"vertex {v!r} not in graph")

        self.graph.add_edge(u, v)
        iu = self._index[u]
        iv = self._index[v]

        # After inserting (u, v), any vertex x that reaches u now
        # reaches v too. And any vertex y that v reaches is now
        # reached by every x that reaches u.
        #
        # Find every x such that (x, iu) is in reach, and every y
        # such that (iv, y) is in reach. Add (x, y) for every (x, y).
        preds: set[int] = {x for (x, y) in self._reach if y == iu}
        succs: set[int] = {y for (x, y) in self._reach if x == iv}
        preds.add(iu)  # u trivially reaches u
        succs.add(iv)  # v trivially reaches v
        for x in preds:
            for y in succs:
                self._reach.add((x, y))

    def delete_edge(self, u: object, v: object) -> None:
        """Delete edge (u, v) and recompute the affected reachability.

        This is the expensive operation. The naive implementation
        recomputes the *entire* transitive closure in O(n * (n + m))
        time. A more clever implementation would invalidate only the
        rows/columns reachable from predecessors of u.

        Args:
            u: Source vertex.
            v: Target vertex.

        Raises:
            KeyError: If `u` or `v` is not in the graph's vertex
                set.
        """
        if u not in self._index:
            raise KeyError(f"vertex {u!r} not in graph")
        if v not in self._index:
            raise KeyError(f"vertex {v!r} not in graph")

        if not self.graph.has_edge(u, v):
            return
        # Remove edge from graph (manually since Digraph lacks delete).
        self.remove_edge_from_graph(u, v)
        # Recompute full TC.
        self._reach = self.compute_full_tc()

    def remove_edge_from_graph(self, u: object, v: object) -> None:
        """Remove edge (u, v) from the underlying Digraph in-place."""
        out = self.graph.out_edges
        if u in out and v in out[u]:
            out[u].discard(v)
        # Update edge_count. Digraph has no public decrementer; access
        # via the slot.
        current_count = self.graph.edge_count
        self.graph.edge_count = current_count - 1
        # Also remove from in_edges for symmetry.
        in_ = self.graph.in_edges
        if v in in_ and u in in_[v]:
            in_[v].discard(u)

    def reaches(self, source: object, target: object) -> bool:
        """Test whether `target` is reachable from `source`.

        Args:
            source: Source vertex.
            target: Target vertex.

        Returns:
            True iff (source, target) is in the transitive closure.

        Raises:
            KeyError: If `source` or `target` is not a vertex.
        """
        if source not in self._index or target not in self._index:
            return False
        return (self._index[source], self._index[target]) in self._reach

    def reachable_from(self, source: object) -> set[object]:
        """Return all vertices reachable from `source`."""
        if source not in self._index:
            return set()
        i = self._index[source]
        return {self.vertices[j] for (s, j) in self._reach if s == i}

    def reach_set(self) -> set[tuple[object, object]]:
        """Return the full transitive closure as a set of vertex pairs."""
        return {(self.vertices[i], self.vertices[j]) for (i, j) in self._reach}

    def __len__(self) -> int:
        """Number of reachable pairs in the current TC."""
        return len(self._reach)

    def __repr__(self) -> str:
        return (
            f"DynamicTransitiveClosure(n={len(self.vertices)}, "
            f"|reach|={len(self._reach)})"
        )


def incremental_tc(
    initial_graph: Digraph,
    edges_to_insert: Iterable[tuple[object, object]],
) -> DynamicTransitiveClosure:
    """Build a dynamic TC from a base graph and a sequence of insertions.

    Convenience wrapper that constructs the closure, applies each
    insertion in order, and returns the result.

    Args:
        initial_graph: Starting digraph (not mutated by this function
            except via the constructed :class:`DynamicTransitiveClosure`'s
            `insert_edge`).
        edges_to_insert: Iterable of (u, v) tuples to insert.

    Returns:
        A :class:`DynamicTransitiveClosure` reflecting the initial
        graph plus all the insertions.
    """
    # The DynamicTransitiveClosure constructor mutates the graph by
    # referencing it (no copy); since we do not mutate initial_graph
    # elsewhere, sharing is safe.
    dtc = DynamicTransitiveClosure(initial_graph)
    for u, v in edges_to_insert:
        if u not in dtc.graph:
            dtc.graph.add_vertex(u)
            dtc.vertices = dtc.graph.vertices()
            dtc._index = {vtx: i for i, vtx in enumerate(dtc.vertices)}
            dtc._reach = dtc.compute_full_tc()
        if v not in dtc.graph:
            dtc.graph.add_vertex(v)
            dtc.vertices = dtc.graph.vertices()
            dtc._index = {vtx: i for i, vtx in enumerate(dtc.vertices)}
            dtc._reach = dtc.compute_full_tc()
        dtc.insert_edge(u, v)
    return dtc
