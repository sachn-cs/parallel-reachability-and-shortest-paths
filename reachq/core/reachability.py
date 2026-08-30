"""Reachability algorithms for directed graphs.

Implements BFS (forward and reverse), SCC decomposition, topological
ordering, and the ``r_plus`` / ``r_minus`` / ``r_ball`` claim-style
sets used by the JLS shortcut-set construction. All algorithms are
deterministic.

Note: the BFS implementations here are the pure-Python fallback
``deque``-based variants. For large graphs (n >= 500 vertices),
``reachq.core.bfs.csr_reachable_forward`` (CSR numpy) is faster;
the JLS construction switches between them via
``reachq.core.bfs.should_use_csr``.
"""

from collections import deque
from collections.abc import Iterator

from reachq.core.graph import Digraph


def bfs_reachability(graph: Digraph, source: object) -> set[object]:
    """Compute ``R^+(G, source)``: all vertices reachable from ``source``.

    Args:
        graph: The input digraph.
        source: Source vertex. Must be in the graph.

    Returns:
        Set of vertices reachable from ``source`` (including ``source``).

    Raises:
        KeyError: If ``source`` is not in the graph.

    Complexity: O(m) time, O(n) space.
    """
    if source not in graph:
        raise KeyError(f"source vertex {source!r} is not in the graph")
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
        target: Target vertex. Must be in the graph.

    Returns:
        Set of vertices that can reach ``target`` (including ``target``).

    Raises:
        KeyError: If ``target`` is not in the graph.
    """
    if target not in graph:
        raise KeyError(f"target vertex {target!r} is not in the graph")
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


def compute_r_plus(graph: Digraph, vertex: object) -> set[object]:
    """Compute ``R^+(G, vertex)``: descendants of ``vertex``.

    Args:
        graph: The input digraph.
        vertex: Pivot vertex.

    Returns:
        Set of vertices reachable from ``vertex`` (inclusive).
    """
    return bfs_reachability(graph, vertex)


def compute_r_minus(graph: Digraph, vertex: object) -> set[object]:
    """Compute ``R^-(G, vertex)``: ancestors of ``vertex``.

    Args:
        graph: The input digraph.
        vertex: Pivot vertex.

    Returns:
        Set of vertices that can reach ``vertex`` (inclusive).
    """
    return reverse_bfs_reachability(graph, vertex)


def compute_r_ball(graph: Digraph, vertex: object) -> set[object]:
    """Compute ``R(G, vertex) = R^+(G, vertex) ∪ R^-(G, vertex)``.

    Args:
        graph: The input digraph.
        vertex: Pivot vertex.

    Returns:
        Union of descendants and ancestors of ``vertex`` (inclusive).
    """
    return compute_r_plus(graph, vertex) | compute_r_minus(graph, vertex)


def compute_r_sets_for_vertices(
    graph: Digraph, vertices: list[object]
) -> tuple[set[object], set[object]]:
    """Compute union of ``R^-`` and ``R^+`` for a set of vertices.

    Args:
        graph: The input digraph.
        vertices: List of pivot vertices.

    Returns:
        Tuple ``(union_of_r_minus, union_of_r_plus)``. Each is the
        union of the corresponding set across all ``vertices``.
    """
    r_minus: set[object] = set()
    r_plus: set[object] = set()
    for v in vertices:
        r_minus |= compute_r_minus(graph, v)
        r_plus |= compute_r_plus(graph, v)
    return r_minus, r_plus


def compute_ancestors(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute ``R^-(G, P) \\ R^+(G, P)``: ancestors of path ``P``."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus - r_plus


def compute_descendants(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute ``R^+(G, P) \\ R^-(G, P)``: descendants of path ``P``."""
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

    Simulates the parallel reachability primitive from Section 1.1.
    **Sequential simulation; span bounds are NOT DETERMINED.**

    Shortcuts whose target vertex is not present in the graph are
    silently ignored.

    Args:
        graph: The input digraph.
        source: Source vertex. Must be in the graph.
        shortcut_edges: Optional shortcut set ``H`` to merge with
            the graph before the BFS.

    Returns:
        Set of vertices reachable from ``source`` in ``G ∪ H``.

    Raises:
        KeyError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise KeyError(f"source vertex {source!r} is not in the graph")
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

    Args:
        graph: The input digraph.

    Returns:
        List of SCCs, each as a list of vertices. The order of the
        outer list is not specified by the algorithm. Vertices
        inside each SCC are returned in insertion order.

    Complexity: O(n + m) time and space.
    """
    visited: set[object] = set()
    finish_order: list[object] = []
    out = graph.out_edges

    for v in graph.vertices():
        if v in visited:
            continue
        stack: list[tuple[object, Iterator[object]]] = [
            (v, iter(out.get(v, set())))
        ]
        visited.add(v)
        while stack:
            node, children = stack[-1]
            for child in children:
                if child not in visited:
                    visited.add(child)
                    stack.append((child, iter(out.get(child, set()))))
                    break
            else:
                stack.pop()
                finish_order.append(node)

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
        ValueError: If ``graph`` contains a cycle.

    Complexity: O(n + m) time and space.
    """
    in_degree: dict[object, int] = {v: graph.degree_in(v) for v in graph.vertices()}
    queue: deque[object] = deque(
        [v for v, d in in_degree.items() if d == 0]
    )
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
        raise ValueError("Graph contains a cycle; topological sort not possible.")
    return result
