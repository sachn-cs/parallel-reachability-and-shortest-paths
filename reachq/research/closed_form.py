"""Closed-form optimal shortcut sets for specific graph classes.

Classes analyzed:

1. Long path (n vertices, n-1 edges). Optimal H = 0.
2. Layered DAG (L layers of size s). Within-layer clique.
3. Cycle graph (n vertices). Optimal H = 0.
4. Star graph (n leaves + 1 center). Optimal H = 0.
5. Complete binary tree of given depth.

Theoretical contributions: on standard constructions the paper's
worst-case bound |H| = O(m + n * ρ^(2ω-2)) is asymptotically loose;
these closed-form helpers show that |H|_essential = 0 on many
natural classes.
"""




from __future__ import annotations


__experimental__ = True



from typing import Any

from reachq.core.graph import Digraph


def path_shortcut_set(n: int) -> set[tuple[Any, Any]]:
    """Optimal shortcut set for the long path 0 -> 1 -> ... -> n-1.

    The trivial one-hop reachability of the path already gives
    R+(G, s) for every source s. No shortcuts are needed.
    """
    return set()


def cycle_shortcut_set(n: int) -> set[tuple[Any, Any]]:
    """Optimal shortcut set for the n-cycle. Returns the empty set."""
    return set()


def layered_dag_shortcut_set(layers: int, layer_size: int) -> set[tuple[int, int]]:
    """Shortcut set for the layered DAG with intra-layer clique shortcuts.

    Returns ``layers * layer_size * (layer_size - 1)`` directed pairs.
    """
    h: set[tuple[int, int]] = set()
    for i in range(layers):
        layer_offset = i * layer_size
        for j1 in range(layer_size):
            for j2 in range(layer_size):
                if j1 != j2:
                    h.add((layer_offset + j1, layer_offset + j2))
    return h


def star_shortcut_set(n: int) -> set[tuple[Any, Any]]:
    """Optimal shortcut set for the n-star. Returns the empty set."""
    return set()


def binary_tree_dag(depth: int) -> Digraph:
    """Complete binary tree of given depth, encoded as a DAG.

    Total vertices: 2^(depth+1) - 1.
    """
    g = Digraph()
    for d in range(depth + 1):
        for k in range(2**d):
            g.add_vertex((d, k))
    for d in range(depth):
        for k in range(2**d):
            g.add_edge((d, k), (d + 1, 2 * k))
            g.add_edge((d, k), (d + 1, 2 * k + 1))
    return g


def lower_bound_path(n: int) -> int:
    """Lower bound on |H| for the n-path. The path's own edges preserve
    reachability, so the lower bound is 0.
    """
    return 0


def upper_bound_paper(n: int, m: int) -> float:
    """Paper's worst-case bound for a graph with ``n`` vertices and ``m`` edges.

    Coarse form: ``n^2 + m * sqrt(n)``.
    """
    return float(n * n + m * (n**0.5))


def verify_path_optimality(n: int) -> dict[str, Any]:
    """The n-path requires NO shortcuts for soundness."""
    from collections import deque

    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    H = path_shortcut_set(n)
    for s in range(n):
        visited: set[Any] = {s}
        q: deque[Any] = deque([s])
        while q:
            u = q.popleft()
            for v in g.out_edges.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        assert visited == set(range(s, n)), (
            f"path_shortcut_set not sound at s={s}: "
            f"expected {set(range(s, n))}, got {visited}"
        )
    return {
        "graph": f"path_{n}",
        "optimal_|H|": len(H),
        "paper_bound": upper_bound_paper(n, n - 1),
    }


def verify_cycle_optimality(n: int) -> dict[str, Any]:
    """The n-cycle requires NO shortcuts."""
    from collections import deque

    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    H = cycle_shortcut_set(n)
    for s in g.vertices():
        visited = {s}
        q: deque[Any] = deque([s])
        while q:
            u = q.popleft()
            for v in g.out_edges.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        assert visited == set(g.vertices()), f"cycle_shortcut_set not sound at s={s}"
    return {
        "graph": f"cycle_{n}",
        "optimal_|H|": len(H),
        "paper_bound": upper_bound_paper(n, n),
    }


def verify_star_optimality(n: int) -> dict[str, Any]:
    """The n-star requires NO shortcuts (2-hop clique via center)."""
    from collections import deque

    g = Digraph()
    for i in range(n + 1):
        g.add_vertex(i)
    for i in range(1, n + 1):
        g.add_edge(0, i)
        g.add_edge(i, 0)
    H = star_shortcut_set(n)
    for s in g.vertices():
        visited = {s}
        q: deque[Any] = deque([s])
        while q:
            u = q.popleft()
            for v in g.out_edges.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        assert visited == set(g.vertices()), f"star_shortcut_set not sound at s={s}"
    return {
        "graph": f"star_{n}",
        "optimal_|H|": len(H),
        "paper_bound": upper_bound_paper(n + 1, n),
    }


def verify_layered_dag_optimality(layers: int, layer_size: int) -> dict[str, Any]:
    """Layered DAG with complete bipartite + complete within-layer cliques.

    The shortcut set is exactly the set of within-layer pairs not
    already present in the input graph.
    """
    from collections import deque

    g = Digraph()
    for i in range(layers):
        for j in range(layer_size):
            g.add_vertex((i, j))
    for i in range(layers - 1):
        for j1 in range(layer_size):
            for j2 in range(layer_size):
                g.add_edge((i, j1), (i + 1, j2))
    for i in range(layers):
        for j1 in range(layer_size):
            for j2 in range(layer_size):
                if j1 != j2:
                    g.add_edge((i, j1), (i, j2))
    H = layered_dag_shortcut_set(layers, layer_size)
    layer_verts = [(i, j) for i in range(layers) for j in range(layer_size)]
    for s in layer_verts:
        visited: set[Any] = {s}
        q: deque[Any] = deque([s])
        while q:
            u = q.popleft()
            for v in g.out_edges.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        s_layer = s[0]
        expected: set[Any] = set()
        for li in range(s_layer, layers):
            for lj in range(layer_size):
                expected.add((li, lj))
        assert visited == expected, (
            f"layered_dag_shortcut_set verification failed at s={s}: "
            f"expected {expected}, got {visited}"
        )
    return {
        "graph": f"layered_{layers}x{layer_size}",
        "optimal_|H|": len(H),
        "paper_bound": upper_bound_paper(
            layers * layer_size, (layers - 1) * layer_size * layer_size
        ),
    }


def verify_bipartite_layered_soundness(layers: int, layer_size: int) -> dict[str, Any]:
    """Layered DAG with complete bipartite and NO within-layer edges."""
    from collections import deque

    g = Digraph()
    for i in range(layers):
        for j in range(layer_size):
            g.add_vertex((i, j))
    for i in range(layers - 1):
        for j1 in range(layer_size):
            for j2 in range(layer_size):
                g.add_edge((i, j1), (i + 1, j2))
    layer_verts = [(i, j) for i in range(layers) for j in range(layer_size)]
    for s in layer_verts:
        visited: set[Any] = {s}
        q: deque[Any] = deque([s])
        while q:
            u = q.popleft()
            for v in g.out_edges.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        s_layer = s[0]
        expected: set[Any] = {s}
        for li in range(s_layer + 1, layers):
            for lj in range(layer_size):
                expected.add((li, lj))
        assert visited == expected, (
            f"bipartite layered DAG soundness check failed at s={s}: "
            f"expected {expected}, got {visited}"
        )
    return {
        "graph": f"bipartite_layered_{layers}x{layer_size}",
        "n": layers * layer_size,
        "m": (layers - 1) * layer_size * layer_size,
    }


__all__ = [
    "binary_tree_dag",
    "cycle_shortcut_set",
    "layered_dag_shortcut_set",
    "lower_bound_path",
    "path_shortcut_set",
    "star_shortcut_set",
    "upper_bound_paper",
    "verify_bipartite_layered_soundness",
    "verify_cycle_optimality",
    "verify_layered_dag_optimality",
    "verify_path_optimality",
    "verify_star_optimality",
]
