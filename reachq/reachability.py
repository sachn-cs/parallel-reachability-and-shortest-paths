"""Reachability algorithms for directed graphs.

Implements BFS (forward and reverse), SCC decomposition, and
topological ordering. All algorithms are deterministic given the
same input and the same insertion-ordered vertex iteration.

Direct functions:

* :func:`bfs_reachability` -- ``R^+(G, source)``
* :func:`reverse_bfs_reachability` -- ``R^-(G, target)``
* :func:`parallel_bfs` -- BFS over ``G ∪ H`` (H = shortcut set)
* :func:`strongly_connected_components` -- Kosaraju SCC
* :func:`topological_sort` -- Kahn's algorithm
* :func:`compute_ancestors`, :func:`compute_descendants`,
  :func:`compute_bridges`, :func:`compute_r_sets_for_vertices` -- set
  operations on reachability sets.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from reachq.errors import ReachqGraphError

if TYPE_CHECKING:
    from reachq.graph import Digraph


def bfs_reachability(graph: Digraph, source: object) -> set[object]:
    """Compute ``R^+(G, source)``: all vertices reachable from ``source``.

    Args:
        graph: The input digraph.
        source: Source vertex.

    Returns:
        Set of vertices reachable from ``source`` (including
        ``source``).

    Raises:
        ReachqGraphError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    visited: set[object] = {source}
    queue: deque[object] = deque([source])
    out = graph.out_edges
    while queue:
        u = queue.popleft()
        for v in out.get(u, ()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return visited


def reverse_bfs_reachability(graph: Digraph, target: object) -> set[object]:
    """Compute ``R^-(G, target)``: all vertices that can reach ``target``.

    Runs BFS on the reversed graph.

    Args:
        graph: The input digraph.
        target: Target vertex.

    Returns:
        Set of vertices that can reach ``target`` (including
        ``target``).

    Raises:
        ReachqGraphError: If ``target`` is not in the graph.
    """
    if target not in graph:
        raise ReachqGraphError(f"target {target!r} not in graph")
    visited: set[object] = {target}
    queue: deque[object] = deque([target])
    inn = graph.in_edges
    while queue:
        u = queue.popleft()
        for v in inn.get(u, set()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return visited


def compute_r_sets_for_vertices(
    graph: Digraph, vertices: list[object]
) -> tuple[set[object], set[object]]:
    """Compute the union of ``R^-`` and ``R^+`` for a set of vertices.

    Args:
        graph: The input digraph.
        vertices: List of pivot vertices.

    Returns:
        Tuple ``(union_of_r_minus, union_of_r_plus)``.
    """
    r_minus: set[object] = set()
    r_plus: set[object] = set()
    for v in vertices:
        r_minus |= reverse_bfs_reachability(graph, v)
        r_plus |= bfs_reachability(graph, v)
    return r_minus, r_plus


def compute_ancestors(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute ``R^-(G, P) \ R^+(G, P)``: ancestors of path ``P``."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus - r_plus


def compute_descendants(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute ``R^+(G, P) \ R^-(G, P)``: descendants of path ``P``."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_plus - r_minus


def compute_bridges(graph: Digraph, path_vertices: list[object]) -> set[object]:
    """Compute ``R^-(G, P) ∩ R^+(G, P)``: bridges of path ``P``."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus & r_plus


def parallel_bfs(
    graph: Digraph,
    source: object,
    shortcut_edges: set[tuple[object, object]] | None = None,
) -> set[object]:
    """BFS on ``G ∪ H`` where ``H`` is a shortcut set.

    Sequentially simulates the parallel reachability primitive from
    Section 1.1. Span bounds are NOT DETERMINED.

    Shortcuts whose target vertex is not present in the graph are
    silently ignored.

    Args:
        graph: The input digraph.
        source: Source vertex.
        shortcut_edges: Optional shortcut set ``H``.

    Returns:
        Set of vertices reachable from ``source`` in ``G ∪ H``.

    Raises:
        ReachqGraphError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise ReachqGraphError(f"source {source!r} not in graph")
    visited: set[object] = {source}
    queue: deque[object] = deque([source])
    out = graph.out_edges
    shortcut_index: dict[object, list[object]] = {}
    if shortcut_edges:
        for a, b in shortcut_edges:
            if b in graph:
                shortcut_index.setdefault(a, []).append(b)
    while queue:
        u = queue.popleft()
        for v in out.get(u, ()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
        for b in shortcut_index.get(u, ()):
            if b not in visited:
                visited.add(b)
                queue.append(b)
    return visited


def strongly_connected_components(graph: Digraph) -> list[list[object]]:
    """Compute SCCs using Kosaraju's algorithm.

    Uses iterative DFS to avoid stack overflow on large graphs.
    Vertices inside each SCC are returned in insertion order.

    Args:
        graph: The input digraph.

    Returns:
        List of SCCs, each as a list of vertices.

    Complexity: O(n + m) time and space.
    """
    visited: set[object] = set()
    finish_order: list[object] = []
    out = graph.out_edges

    for v in graph.iter_vertices():
        if v in visited:
            continue
        stack: list[tuple[object, object]] = [(v, iter(out.get(v, set())))]
        visited.add(v)
        while stack:
            node, children = stack[-1]
            try:
                child = next(children)
            except StopIteration:
                stack.pop()
                finish_order.append(node)
                continue
            if child not in visited:
                visited.add(child)
                stack.append((child, iter(out.get(child, set()))))

    rev = graph.reversed()
    rev_out = rev.out_edges
    visited.clear()
    sccs: list[list[object]] = []

    for v in reversed(finish_order):
        if v in visited:
            continue
        component: list[object] = []
        component_stack: list[object] = [v]
        visited.add(v)
        while component_stack:
            node = component_stack.pop()
            component.append(node)
            for w in rev_out.get(node, set()):
                if w not in visited:
                    visited.add(w)
                    component_stack.append(w)
        sccs.append(component)

    return sccs


def topological_sort(graph: Digraph) -> list[object]:
    """Return a topological ordering of a DAG.

    Uses Kahn's algorithm.

    Args:
        graph: The input digraph (must be a DAG).

    Returns:
        A list of vertices in topological order.

    Raises:
        ReachqGraphError: If ``graph`` contains a cycle.
    """
    in_degree: dict[object, int] = {
        v: graph.degree_in(v) for v in graph.iter_vertices()
    }
    queue: deque[object] = deque([v for v, d in in_degree.items() if d == 0])
    result: list[object] = []
    out = graph.out_edges

    while queue:
        u = queue.popleft()
        result.append(u)
        for v in out.get(u, set()):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(result) != graph.num_vertices():
        raise ReachqGraphError("Graph contains a cycle; topological sort not possible.")
    return result


__all__ = [
    "bfs_reachability",
    "compute_ancestors",
    "compute_bridges",
    "compute_descendants",
    "compute_r_sets_for_vertices",
    "parallel_bfs",
    "reverse_bfs_reachability",
    "strongly_connected_components",
    "topological_sort",
]
