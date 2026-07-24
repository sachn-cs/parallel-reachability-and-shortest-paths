"""Transitive closure computation for directed graphs.

The paper uses fast matrix multiplication for transitive closure:
"TC(G) can be computed in eO(|V(G)|^omega) time using repeated squaring
of the adjacency matrix of G" (Section 4.2).

Uses scipy.sparse Boolean matmul so the algorithm runs on graphs where
dense O(n^2) memory would OOM (e.g. web-Google, n ~= 875k).
"""

from __future__ import annotations

from typing import Any

from reachq.core.graph import Digraph


def transitive_closure_brute_force(graph: Digraph) -> set[tuple[object, object]]:
    """Compute TC(G) using BFS from every vertex.

    Returns all pairs (u, v) such that there is a path from u to v in G.
    Time complexity: O(n * m) which is O(n^3) in the worst case.
    """
    from reachq.core.reachability import compute_r_plus

    result: set[tuple[object, object]] = set()
    for u in graph.vertices():
        reachable = compute_r_plus(graph, u)
        for v in reachable:
            result.add((u, v))
    return result


def vertex_to_index(graph: Digraph) -> tuple[dict[object, int], list[object]]:
    """Create a bijection between vertices and indices [0, n-1]."""
    vertices = list(graph.vertices())
    index_map = {v: i for i, v in enumerate(vertices)}
    return index_map, vertices


def transitive_closure_matrix(graph: Digraph) -> set[tuple[object, object]]:
    """Compute TC(G) using Boolean matrix multiplication (repeated squaring).

    Sparse memory: O(n + m) for the CSR adjacency; repeated squaring does
    O(log n) sparse matmuls whose intermediate sizes stay bounded by |TC|.
    Previously this allocated a dense n x n int32 matrix, which OOMs for
    graphs above ~50k vertices on a laptop.

    Implementation note: scipy.sparse ``@`` between two CSR matrices returns
    integer counts (path multiplicities) stored at every (i, j) reached,
    but the set of *reached* positions is exactly what we want. We extract
    the COO pairs from each iteration and accumulate them in a Python set.
    This sidesteps the buggy ``maximum`` behaviour for sparse matrices with
    different sparsity patterns.
    """
    import numpy as np

    try:
        from scipy.sparse import csr_matrix
    except ImportError:  # pragma: no cover - scipy is in declared deps
        return transitive_closure_brute_force(graph)

    n = graph.num_vertices()
    if n == 0:
        return set()

    index_map, vertices = vertex_to_index(graph)

    row_list: list[int] = []
    col_list: list[int] = []
    for u, v in graph.edges():
        row_list.append(index_map[u])
        col_list.append(index_map[v])
    diag_idx = np.arange(n)
    row_list.extend(diag_idx.tolist())
    col_list.extend(diag_idx.tolist())
    data = np.ones(len(row_list), dtype=np.int8)
    adj: Any = csr_matrix(
        (
            data,
            (
                np.asarray(row_list, dtype=np.int32),
                np.asarray(col_list, dtype=np.int32),
            ),
        ),
        shape=(n, n),
    )

    # Reachability as a Python set of (row, col) pairs in [0, n).
    reach: set[tuple[int, int]] = {
        (int(i), int(j)) for i, j in zip(adj.tocoo().row, adj.tocoo().col)
    }

    # Repeated squaring. The dtype of the CSR data must be wide enough to
    # hold the maximum path count between any pair, which grows as
    # O(n!) in dense graphs; int32 is enough for n up to a few thousand.
    # We pre-build a 0/1 boolean CSR per iteration from the current
    # ``reach`` set so squaring stays in the Boolean semiring.
    max_iterations = max(1, (n - 1).bit_length())
    for _ in range(max_iterations):
        rows_arr = np.fromiter((r for r, _ in reach), dtype=np.int32, count=len(reach))
        cols_arr = np.fromiter((c for _, c in reach), dtype=np.int32, count=len(reach))
        tc_csr = csr_matrix(
            (np.ones(len(reach), dtype=np.int32), (rows_arr, cols_arr)),
            shape=(n, n),
        )
        # Boolean matmul: clip to bool AFTER squaring so any positive
        # entry (regardless of path count) becomes 1. Using a wide dtype
        # (int32) avoids overflow for graphs up to n ~= a few thousand.
        squared = tc_csr @ tc_csr
        # Threshold via COO: gather (row, col) where data > 0 directly.
        sq_coo = squared.tocoo()
        new_pairs: set[tuple[int, int]] = {
            (int(i), int(j))
            for i, j, v in zip(sq_coo.row, sq_coo.col, sq_coo.data)
            if v > 0
        }
        new_pairs -= reach
        if not new_pairs:
            break
        reach |= new_pairs

    return {(vertices[i], vertices[j]) for i, j in reach}


def transitive_closure_on_subset(
    graph: Digraph, subset: set[object]
) -> set[tuple[object, object]]:
    """Compute TC(G[subset]): transitive closure of the induced subgraph.

    Used by TC-Pruning (Section 4.2): "add all edges in TC(G[R(G, p)]) to H."
    """
    subgraph = graph.induced_subgraph(subset)
    return transitive_closure_matrix(subgraph)
