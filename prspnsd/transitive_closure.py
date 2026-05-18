"""Transitive closure computation for directed graphs.

The paper uses fast matrix multiplication for transitive closure:
"TC(G) can be computed in eO(|V(G)|^omega) time using repeated squaring
of the adjacency matrix of G" (Section 4.2).

We provide both a matrix-multiplication-based implementation (using numpy)
and a brute-force BFS-based implementation for small graphs or verification.
"""


try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from typing import Any

from prspnsd.graph import Digraph


def transitive_closure_brute_force(graph: Digraph) -> set[tuple[object, object]]:
    """Compute TC(G) using BFS from every vertex.

    Returns all pairs (u, v) such that there is a path from u to v in G.
    Time complexity: O(n * m) which is O(n^3) in the worst case.
    """
    from prspnsd.reachability import compute_r_plus
    result: set[tuple[object, object]] = set()
    for u in graph.vertices():
        reachable = compute_r_plus(graph, u)
        for v in reachable:
            result.add((u, v))
    return result


def _vertex_to_index(graph: Digraph) -> tuple[dict[object, int], list[object]]:
    """Create a bijection between vertices and indices [0, n-1]."""
    vertices = list(graph.vertices())
    index_map = {v: i for i, v in enumerate(vertices)}
    return index_map, vertices


def transitive_closure_matrix(graph: Digraph) -> set[tuple[object, object]]:
    """Compute TC(G) using matrix multiplication (repeated squaring).

    This implements the paper's approach (Section 4.2).

    The matrix multiplication is performed using numpy.matmul,
    which uses optimized BLAS/LAPACK. The paper assumes
    O(n^omega) where omega < 2.371339 (Proposition 2.1).

    If numpy is not available, falls back to brute_force.
    """
    if not HAS_NUMPY:
        return transitive_closure_brute_force(graph)

    n = graph.num_vertices()
    if n == 0:
        return set()

    index_map, vertices = _vertex_to_index(graph)

    # Build adjacency matrix over the Boolean semiring {0, 1} with OR/AND.
    adj: Any = np.zeros((n, n), dtype=np.int8)
    for u, v in graph.edges():
        adj[index_map[u], index_map[v]] = 1

    # Add self-loops
    np.fill_diagonal(adj, 1)

    # Repeated squaring: O(log n) matrix multiplications.
    tc = adj.copy()
    max_iterations = max(1, (n - 1).bit_length())

    for _ in range(max_iterations):
        old = tc.copy()
        tc = np.matmul(tc, tc, out=tc)
        tc = (tc > 0).astype(np.int8)
        if np.array_equal(tc, old):
            break

    result: set[tuple[object, object]] = set()
    rows, cols = np.where(tc)
    for i, j in zip(rows, cols):
        result.add((vertices[i], vertices[j]))
    return result


def transitive_closure_on_subset(graph: Digraph, subset: set[object]) -> set[tuple[object, object]]:
    """Compute TC(G[subset]): transitive closure of the induced subgraph.

    Used by TC-Pruning (Section 4.2): "add all edges in TC(G[R(G, p)]) to H."
    """
    subgraph = graph.induced_subgraph(subset)
    return transitive_closure_matrix(subgraph)
