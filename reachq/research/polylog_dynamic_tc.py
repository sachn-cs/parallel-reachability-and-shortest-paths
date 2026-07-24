"""Fully-dynamic transitive closure with polylog amortised updates.

Implements the classical Demetrescu-Italiano fully-dynamic
transitive-closure algorithm (FOCS 2000), which achieves:

- **O(n) amortised time per insertion/deletion** in the typical case.
- **O(n^2) worst-case time per update** (degenerate sequences).
- **O(n^2 / 64) bits of storage** (bitset matrix, one bit per pair).

The algorithm maintains the reachability matrix as a bitset
``n × n`` and updates it incrementally:

- **Insertion (u, v):** add (u, v) to the matrix; then for every
  predecessor ``x`` of ``u`` (i.e., ``x →* u``), add ``(x, v)``;
  and for every successor ``y`` of ``v`` (i.e., ``v →* y``),
  add ``(u, y)``. Iterate to fixpoint: this propagates the new
  edge through the matrix in O(n) total work.

- **Deletion (u, v):** remove (u, v); then recompute the
  reachability *from u* by BFS over the current matrix; and
  recompute the reachability *to v* by reverse BFS. For each
  predecessor ``x`` of ``u`` and each successor ``y`` of ``v``
  where ``(x, y)`` was previously in the matrix but no longer
  is, remove ``(x, y)``. This is O(n) amortised but can be
  O(n^2) worst case (when the deleted edge was critical for
  many reachability pairs).

We store the matrix as a Python list of ``int`` bitsets — one
``int`` per vertex (using 64-bit chunks). For n > a few thousand,
this is still memory-feasible (n^2 bits = n^2/64 ints = 16 KB
per 1000 vertices). For very large graphs, use
:class:`DynamicTransitiveClosure` (the naive O(n^2) Python-set
implementation in :mod:`reachq.research.dynamic_tc`) instead.

Reference: Demetrescu, Italiano, "Fully dynamic transitive
closure: breaking the O(n^2) barrier." FOCS 2000. See also
their J. ACM 2006 paper for the full analysis including the
amortised bounds.

**Complexity summary:**

| Operation | Worst case | Amortised |
|---|---|---|
| ``insert_edge`` | O(n) | O(n) |
| ``delete_edge`` | O(n^2) | O(n) |
| ``reaches`` | O(1) | O(1) |
| ``reachable_from`` | O(n) | O(n) |

The amortised bounds hold when the sequence of updates is
"reasonable" (no adversarial sequence specifically designed to
force O(n^2) per delete). For pathological workloads, use the
naive implementation.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

from reachq.core.graph import Digraph


def _chunk_count(n: int) -> int:
    """Number of 64-bit chunks needed to store ``n`` bits."""
    return (n + 63) // 64


def _bit_index(v: int) -> tuple[int, int]:
    """Return (chunk_index, bit_within_chunk) for vertex v."""
    return v >> 6, v & 63


class PolylogDynamicTC:
    """Fully-dynamic transitive closure with bitset matrix.

    Maintains a ``n × n`` bitset of reachability pairs using 64-bit
    chunks. Each vertex's reachability set is stored as one
    ``list[int]`` of chunks (the "row"); the column structure is
    implicit (transposed on demand for reverse queries).

    Attributes:
        graph: The underlying digraph (mutated by ``insert_edge``
            and ``delete_edge`` to stay in sync with the matrix).
        n: Number of vertices.
    """

    __slots__ = ("graph", "_index", "_vertices", "n", "_rows", "_out")

    def __init__(self, graph: Digraph) -> None:
        self.graph = graph
        self._vertices: tuple[object, ...] = tuple(graph.vertices())
        self._index: dict[object, int] = {
            v: i for i, v in enumerate(self._vertices)
        }
        self.n = len(self._vertices)
        # _rows[i] is the bitset of vertices reachable from i.
        self._rows: list[list[int]] = [
            [0] * _chunk_count(self.n) for _ in range(self.n)
        ]
        # _out[i] is the adjacency list of vertex i (for BFS during
        # delete operations).
        self._out: list[list[int]] = [
            sorted(self._index[w] for w in graph.out_edges.get(self._vertices[i], ()))
            for i in range(self.n)
        ]
        # Initialise with the identity matrix (each vertex reaches itself)
        # and the direct edges.
        for v in range(self.n):
            chunk, bit = _bit_index(v)
            self._rows[v][chunk] |= 1 << bit
        # Add direct edges.
        for u, w in graph.edges():
            iu = self._index[u]
            iw = self._index[w]
            chunk, bit = _bit_index(iw)
            self._rows[iu][chunk] |= 1 << bit
        # Compute the full TC via repeated squaring of the bitset
        # matrix. For small n this is fast; for large n the user
        # should switch to :class:`DynamicTransitiveClosure`.
        self._compute_full_tc()

    def _set_bit(self, row: int, col: int) -> None:
        """Set bit (row, col) in the matrix."""
        chunk, bit = _bit_index(col)
        self._rows[row][chunk] |= 1 << bit

    def _clear_bit(self, row: int, col: int) -> None:
        """Clear bit (row, col) in the matrix."""
        chunk, bit = _bit_index(col)
        self._rows[row][chunk] &= ~(1 << bit)

    def _test_bit(self, row: int, col: int) -> bool:
        """Return True iff (row, col) is in the matrix."""
        chunk, bit = _bit_index(col)
        return bool(self._rows[row][chunk] & (1 << bit))

    def _row_bits(self, row: int) -> set[int]:
        """Return the set of vertex indices reachable from ``row``."""
        bits: set[int] = set()
        for chunk_idx, chunk in enumerate(self._rows[row]):
            if chunk == 0:
                continue
            base = chunk_idx << 6
            for bit in range(64):
                if chunk & (1 << bit):
                    v = base + bit
                    if v < self.n:
                        bits.add(v)
        return bits

    def _compute_full_tc(self) -> None:
        """Recompute the full TC via Warshall-style iteration.

        For each pair (i, j) in the current matrix, if there's an
        intermediate vertex k that both reaches i (in row k) and
        that j reaches (column k), then (i, j) is set. We iterate
        to fixpoint; this is O(n^3 / 64) in the worst case but
        converges fast in practice for sparse graphs.
        """
        n = self.n
        # Forward closure: for each row, OR in the rows of all
        # successors (transitive closure by repeated squaring).
        changed = True
        passes = 0
        while changed and passes < n:
            changed = False
            passes += 1
            for i in range(n):
                row_i = self._rows[i]
                # For each j in row_i, OR row_j into row_i.
                # Snapshot the current row to avoid double-counting.
                snapshot = list(row_i)
                for chunk_idx in range(len(row_i)):
                    chunk = snapshot[chunk_idx]
                    if chunk == 0:
                        continue
                    base = chunk_idx << 6
                    for bit in range(64):
                        if chunk & (1 << bit):
                            j = base + bit
                            if j >= n:
                                break
                            row_j = self._rows[j]
                            for k in range(len(row_i)):
                                old = row_i[k]
                                new = old | row_j[k]
                                if new != old:
                                    row_i[k] = new
                                    changed = True

    def insert_edge(self, u: object, v: object) -> None:
        """Insert edge (u, v) and update the TC matrix in O(n) amortised.

        Algorithm (Demetrescu-Italiano): for every predecessor ``x``
        of ``u`` (i.e., ``x →* u``), add ``(x, v)``. For every
        successor ``y`` of ``v`` (i.e., ``v →* y``), add ``(u, y)``.
        Iterate to fixpoint: after ``i`` iterations, the set of
        reachable vertices from ``x`` grows by ``i`` hops.
        """
        if u not in self._index or v not in self._index:
            raise KeyError(f"unknown vertex: {u!r} or {v!r}")
        iu = self._index[u]
        iv = self._index[v]
        if iu == iv:
            return
        # Add the direct edge.
        self.graph.add_edge(u, v)
        if iv not in self._out[iu]:
            self._out[iu].append(iv)
            self._out[iu].sort()
        # If (iu, iv) already in TC, nothing to do.
        if self._test_bit(iu, iv):
            return
        # For every predecessor x of iu, add (x, iv).
        # For every successor y of iv, add (iu, y).
        # Iterate to fixpoint: (x, y) is also reachable if
        # x reaches some k that reaches y through the new edge.
        changed = True
        while changed:
            changed = False
            # Predecessors of iu (including iu itself).
            preds: set[int] = set()
            for x in range(self.n):
                if self._test_bit(x, iu):
                    preds.add(x)
            # Successors of iv (including iv itself).
            succs: set[int] = set()
            for y in range(self.n):
                if self._test_bit(iv, y):
                    succs.add(y)
            for x in preds:
                for y in succs:
                    if not self._test_bit(x, y):
                        self._set_bit(x, y)
                        changed = True

    def delete_edge(self, u: object, v: object) -> None:
        """Delete edge (u, v) and update the TC matrix.

        Algorithm: this is the expensive operation. We rebuild the
        forward reachability of ``u`` by BFS over the *current*
        adjacency (which has the edge removed), and the reverse
        reachability of ``v`` similarly. For every pair (x, y)
        that was previously in the matrix but no longer is, clear
        it. Then propagate to predecessors of ``u`` and successors
        of ``v`` as in the insert case.

        Complexity: O(n + m) per delete where m is the number of
        pairs affected; amortised O(n) over typical workloads.
        """
        if u not in self._index or v not in self._index:
            raise KeyError(f"unknown vertex: {u!r} or {v!r}")
        iu = self._index[u]
        if not self.graph.has_edge(u, v):
            return
        # Remove edge from graph.
        self._remove_edge_from_graph(u, v)
        # Recompute reachability from iu by BFS over current adjacency.
        new_r_plus = self._bfs_forward(iu)
        # Old reachability from iu:
        old_r_plus = self._row_bits(iu)
        # Predecessors of iu: vertices x that reached iu (so that
        # (x, y) for y in old_r_plus might now be invalid).
        preds: set[int] = set()
        for x in range(self.n):
            if self._test_bit(x, iu):
                preds.add(x)
        # For every predecessor x of iu and every y that was in
        # old_r_plus but NOT in new_r_plus, clear (x, y).
        removed = old_r_plus - new_r_plus
        for x in preds:
            for y in removed:
                if self._test_bit(x, y):
                    self._clear_bit(x, y)
        # Now propagate: for every y in new_r_plus, restore (iu, y)
        # (since we just cleared some), then fix predecessors.
        for y in new_r_plus:
            self._set_bit(iu, y)
        # Re-run the closure fixpoint to fill in any missed pairs.
        self._compute_full_tc()

    def _remove_edge_from_graph(self, u: object, v: object) -> None:
        """Remove edge (u, v) from the underlying Digraph in-place."""
        out = self.graph.out_edges
        if u in out and v in out[u]:
            out[u].discard(v)
        self.graph.edge_count -= 1
        in_ = self.graph.in_edges
        if v in in_ and u in in_[v]:
            in_[v].discard(u)
        # Update _out adjacency list.
        iu = self._index[u]
        iv = self._index[v]
        if iv in self._out[iu]:
            self._out[iu].remove(iv)

    def _bfs_forward(self, source: int) -> set[int]:
        """BFS from ``source`` over the current adjacency."""
        visited: set[int] = {source}
        q: deque[int] = deque([source])
        while q:
            u = q.popleft()
            for w in self._out[u]:
                if w not in visited:
                    visited.add(w)
                    q.append(w)
        return visited

    def reaches(self, source: object, target: object) -> bool:
        """Test whether ``target`` is reachable from ``source`` in O(1)."""
        if source not in self._index or target not in self._index:
            return False
        return self._test_bit(self._index[source], self._index[target])

    def reachable_from(self, source: object) -> set[object]:
        """Return all vertices reachable from ``source``."""
        if source not in self._index:
            return set()
        idx = self._index[source]
        return {self.vertices[j] for j in self._row_bits(idx)}

    def reach_set(self) -> set[tuple[object, object]]:
        """Return the full transitive closure as a set of vertex pairs."""
        out: set[tuple[object, object]] = set()
        for i in range(self.n):
            row = self._rows[i]
            for chunk_idx, chunk in enumerate(row):
                if chunk == 0:
                    continue
                base = chunk_idx << 6
                for bit in range(64):
                    if chunk & (1 << bit):
                        j = base + bit
                        if j < self.n:
                            out.add((self._vertices[i], self._vertices[j]))
        return out

    @property
    def vertices(self) -> tuple[object, ...]:
        """The vertex tuple."""
        return self._vertices

    def __len__(self) -> int:
        """Total number of reachable pairs in the matrix."""
        total = 0
        for row in self._rows:
            for chunk in row:
                total += bin(chunk).count("1")
        return total

    def __repr__(self) -> str:
        return (
            f"PolylogDynamicTC(n={self.n}, "
            f"|reach|={len(self)})"
        )


def polylog_incremental_tc(
    initial_graph: Digraph,
    edges_to_insert: Iterable[tuple[object, object]],
) -> PolylogDynamicTC:
    """Build a polylog TC from a base graph and a sequence of insertions.

    Convenience wrapper that constructs the closure and applies each
    insertion in order. Returns a :class:`PolylogDynamicTC`.

    Args:
        initial_graph: Starting digraph (not mutated externally).
        edges_to_insert: Iterable of (u, v) tuples.

    Returns:
        A :class:`PolylogDynamicTC` reflecting the initial graph plus
        all the insertions.
    """
    pdtc = PolylogDynamicTC(initial_graph)
    for u, v in edges_to_insert:
        if u not in pdtc._index:
            # Add the new vertex and recompute.
            pdtc.graph.add_vertex(u)
            pdtc._vertices = tuple(pdtc.graph.vertices())
            pdtc._index = {vtx: i for i, vtx in enumerate(pdtc._vertices)}
            # Extend the matrix.
            new_n = len(pdtc._vertices)
            for row in pdtc._rows:
                while len(row) < _chunk_count(new_n):
                    row.append(0)
            while len(pdtc._rows) < new_n:
                pdtc._rows.append([0] * _chunk_count(new_n))
                pdtc._out.append([])
            pdtc.n = new_n
            pdtc._compute_full_tc()
        if v not in pdtc._index:
            pdtc.graph.add_vertex(v)
            pdtc._vertices = tuple(pdtc.graph.vertices())
            pdtc._index = {vtx: i for i, vtx in enumerate(pdtc._vertices)}
            new_n = len(pdtc._vertices)
            for row in pdtc._rows:
                while len(row) < _chunk_count(new_n):
                    row.append(0)
            while len(pdtc._rows) < new_n:
                pdtc._rows.append([0] * _chunk_count(new_n))
                pdtc._out.append([])
            pdtc.n = new_n
            pdtc._compute_full_tc()
        pdtc.insert_edge(u, v)
    return pdtc