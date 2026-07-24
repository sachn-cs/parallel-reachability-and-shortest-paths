"""Reachability algorithms for directed graphs.

Implements BFS, SCC decomposition, and bridge/ancestor/descendant
computations from Section 2. All algorithms are deterministic.
"""

from collections import deque
from collections.abc import Iterator
from typing import Optional

from reachq.core.graph import Digraph


def bfs_reachability(graph: Digraph, source: object) -> set[object]:
    """Compute R^+(G, source): all vertices reachable from source via BFS.

    Time: O(m). Space: O(n).
    """
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
    """Compute R^-(G, target): all vertices that can reach target.

    Runs BFS on the reversed graph. Time: O(m). Space: O(n).
    """
    visited: set[object] = set()
    queue: deque[object] = deque()
    queue.append(target)
    visited.add(target)
    inn = graph.in_edges
    while queue:
        u = queue.popleft()
        for v in inn.get(u, set()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return visited


def compute_r_plus(graph: Digraph, vertex: object) -> set[object]:
    """Compute R^+(G, v)."""
    return bfs_reachability(graph, vertex)


def compute_r_minus(graph: Digraph, vertex: object) -> set[object]:
    """Compute R^-(G, v)."""
    return reverse_bfs_reachability(graph, vertex)


def compute_r_ball(graph: Digraph, vertex: object) -> set[object]:
    """Compute R(G, v) = R^+(G, v) ∪ R^-(G, v)."""
    return compute_r_plus(graph, vertex) | compute_r_minus(graph, vertex)


def compute_r_sets_for_vertices(
    graph: Digraph, vertices: list[object]
) -> tuple[set[object], set[object]]:
    """Compute union of R^+ and R^- for a set of vertices efficiently."""
    r_minus: set[object] = set()
    r_plus: set[object] = set()
    for v in vertices:
        r_minus |= compute_r_minus(graph, v)
        r_plus |= compute_r_plus(graph, v)
    return r_minus, r_plus


def compute_ancestors(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute R^-(G, P) \\ R^+(G, P): ancestors of path P."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus - r_plus


def compute_descendants(graph: Digraph, path_vertices: list[object]) -> set[object]:
    r"""Compute R^+(G, P) \\ R^-(G, P): descendants of path P."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_plus - r_minus


def compute_bridges(graph: Digraph, path_vertices: list[object]) -> set[object]:
    """Compute R^-(G, P) ∩ R^+(G, P): bridges of path P."""
    r_minus, r_plus = compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus & r_plus


def parallel_bfs(
    graph: Digraph,
    source: object,
    shortcut_edges: Optional[set[tuple[object, object]]] = None,
) -> set[object]:
    """BFS on G ∪ H where H is a shortcut set.

    This simulates the parallel reachability primitive from Section 1.1.
    Sequential simulation; span bounds are NOT DETERMINED.

    Shortcuts whose target vertex is not present in the graph are
    silently ignored.
    """
    visited: set[object] = {source}
    queue: deque[object] = deque([source])
    out = graph.out_edges
    shortcut_index: dict[object, list[object]] = {}
    if shortcut_edges:
        for a, b in shortcut_edges:
            if b not in graph.vertex_set:
                continue
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


def strongly_connected_components(graph: Digraph) -> list[set[object]]:
    """Compute SCCs using Kosaraju's algorithm. O(n + m) time.

    Uses iterative DFS to avoid stack overflow on large graphs.
    Returns a list of sets, each being an SCC.
    """
    visited: set[object] = set()
    finish_order: list[object] = []
    out = graph.out_edges

    for v in graph.vertices():
        if v in visited:
            continue
        stack: list[tuple[object, Iterator[object]]] = [(v, iter(out.get(v, set())))]
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
    sccs: list[set[object]] = []

    for v in reversed(finish_order):
        if v in visited:
            continue
        component: set[object] = set()
        component_stack: list[object] = [v]
        visited.add(v)
        while component_stack:
            node = component_stack.pop()
            component.add(node)
            for w in rev_out.get(node, set()):
                if w not in visited:
                    visited.add(w)
                    component_stack.append(w)
        sccs.append(component)

    return sccs


def topological_sort(graph: Digraph) -> list[object]:
    """Return a topological ordering of a DAG. Raises ValueError if cycles exist.

    Uses Kahn's algorithm. Time: O(n + m).
    """
    in_degree: dict[object, int] = {v: graph.degree_in(v) for v in graph.vertices()}
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
        raise ValueError("Graph contains a cycle; topological sort not possible.")
    return result
