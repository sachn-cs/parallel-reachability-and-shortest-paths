"""Transitive closure computation for directed graphs.

The paper uses fast matrix multiplication for transitive closure::

    TC(G) can be computed in e`O(|V(G)`|^omega) time using repeated
    squaring of the adjacency matrix of G (Section 4.2).

This implementation uses the Boolean semiring: the sparse datatype is
`int8` and squaring is `(A @ A) > 0` followed by a coalesce.
Overflow is impossible by construction. Output size is inherently
quadratic in the worst case and is bounded by `max_pairs`; graphs
whose projected closure exceeds the budget raise
:class:`TransitiveClosureBudgetError`.

Memory characteristics:

* adjacency / closure CSR: `O(|TC|)` entries.
* Python set of (i, j) pairs: `O(|TC|)`.

There is no dense n x n backup; exact TC is honestly `O(|TC|)` memory.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from reachq.errors import ReachqValueError
from reachq.graph import Digraph
from reachq.reachability import bfs_reachability


class TransitiveClosureBudgetError(Exception):
    """Raised when the projected TC exceeds the configured `max_pairs`.

    The Boolean semiring makes TC scale-free w.r.t. edge weights, but
    worst-case |TC| is `O(n^2)`. Carries `partial_pairs` so callers
    can recover progress.
    """

    def __init__(self, message: str, *, partial_pairs: int | None = None) -> None:
        super().__init__(message)
        self.partial_pairs = partial_pairs


def transitive_closure_brute_force(graph: Digraph) -> set[tuple[object, object]]:
    """Compute `TC(G)` using BFS from every vertex.

    This is the ground-truth oracle; it does not enforce a budget
    and will gladly consume `O(n^2)` memory on dense inputs.

    Args:
        graph: The input digraph.

    Returns:
        Set of all pairs `(u, v)` such that there is a path from
        `u` to `v` in `G` (including `u == v`).

    Complexity: `O(n * m)` time, `O(n^2)` space in the worst case.
    """
    result: set[tuple[object, object]] = set()
    for u in graph.iter_vertices():
        result.add((u, u))
        for v in bfs_reachability(graph, u):
            if v != u:
                result.add((u, v))
    return result


def transitive_closure(
    graph: Digraph,
    *,
    max_pairs: int | None = None,
    budget_strict: bool = True,
) -> set[tuple[object, object]]:
    """Compute `TC(G)` in the Boolean semiring with sparse repeated squaring.

    Args:
        graph: The input digraph.
        max_pairs: Maximum number of `(u, v)` pairs to emit.
            `None` disables the budget.
        budget_strict: When `True` (default), exceed the budget
            exactly by raising
            :class:`TransitiveClosureBudgetError`. When `False`,
            return whatever pairs fit under the budget without
            raising.

    Returns:
        Set of all pairs `(u, v)` such that there is a path from
        `u` to `v` in `G` (including `u == v`).

    Raises:
        TransitiveClosureBudgetError: when `budget_strict=True`
            and the budget is exceeded. Carries `partial_pairs`
            so callers can recover progress.
    """
    if max_pairs is not None and max_pairs < 0:
        raise ReachqValueError(f"max_pairs must be non-negative (got {max_pairs})")

    vertices = list(graph.iter_vertices())
    n = len(vertices)
    if n == 0:
        return set()

    index_map = graph.index_of_map

    rows: list[int] = []
    cols: list[int] = []
    for u in vertices:
        i = index_map[u]
        for v in graph.out_edges.get(u, ()):
            rows.append(i)
            cols.append(index_map[v])
    diag = np.arange(n, dtype=np.int32)
    rows_arr = np.concatenate([np.asarray(rows, dtype=np.int32), diag])
    cols_arr = np.concatenate([np.asarray(cols, dtype=np.int32), diag])

    from scipy.sparse import csr_matrix

    tc = csr_matrix(
        (np.ones(len(rows_arr), dtype=np.int8), (rows_arr, cols_arr)),
        shape=(n, n),
        dtype=np.int8,
    )
    tc.sum_duplicates()

    coo = tc.tocoo()
    reach: set[tuple[int, int]] = {(int(r), int(c)) for r, c in zip(coo.row, coo.col)}
    if max_pairs is not None and len(reach) > max_pairs:
        if budget_strict:
            raise TransitiveClosureBudgetError(
                f"max_pairs={max_pairs} exceeded by initial adjacency "
                f"(|adj|={len(reach)})",
                partial_pairs=len(reach),
            )
        return decode_pairs(reach, vertices, max_pairs)

    if n <= 1:
        return decode_pairs(reach, vertices, max_pairs)

    max_iterations = max(1, (n - 1).bit_length())
    for _ in range(max_iterations):
        rows_arr = np.fromiter((r for r, _ in reach), dtype=np.int32, count=len(reach))
        cols_arr = np.fromiter((c for _, c in reach), dtype=np.int32, count=len(reach))
        step = csr_matrix(
            (np.ones(len(reach), dtype=np.int8), (rows_arr, cols_arr)),
            shape=(n, n),
            dtype=np.int8,
        )
        squared = (step @ step).astype(bool, copy=False)
        coo = squared.tocoo()
        new_pairs: set[tuple[int, int]] = {
            (int(r), int(c)) for r, c in zip(coo.row, coo.col)
        }
        new_pairs -= reach
        if not new_pairs:
            break
        if max_pairs is not None and len(reach) + len(new_pairs) > max_pairs:
            if budget_strict:
                raise TransitiveClosureBudgetError(
                    f"max_pairs={max_pairs} exceeded "
                    f"(|reach|={len(reach)}, pending={len(new_pairs)})",
                    partial_pairs=len(reach),
                )
            for p in new_pairs:
                reach.add(p)
                if len(reach) >= max_pairs:
                    return decode_pairs(reach, vertices, max_pairs)
            break
        reach |= new_pairs

    return decode_pairs(reach, vertices, max_pairs)


def decode_pairs(
    reach: set[tuple[int, int]],
    vertices: list[object],
    budget: int | None,
) -> set[tuple[object, object]]:
    """Translate integer pairs back to vertex objects."""
    out: set[tuple[object, object]] = set()
    for i, j in reach:
        if budget is not None and len(out) >= budget:
            return out
        out.add((vertices[i], vertices[j]))
    return out


def transitive_closure_on_subset(
    graph: Digraph,
    subset: Iterable[object],
    *,
    max_pairs: int | None = None,
) -> set[tuple[object, object]]:
    """Compute `TC(G[subset])`: closure on the induced subgraph.

    Args:
        graph: The input digraph `G`.
        subset: Iterable of vertices already in `graph`.
        max_pairs: Forwarded to :func:`transitive_closure`.

    Returns:
        Set of reachable pairs in `graph.induced_subgraph(subset)`.
    """
    subgraph = graph.induced_subgraph(set(subset))
    return transitive_closure(subgraph, max_pairs=max_pairs)


__all__ = [
    "TransitiveClosureBudgetError",
    "transitive_closure",
    "transitive_closure_brute_force",
    "transitive_closure_on_subset",
]
