"""Reachability algorithms for directed graphs.

Implements BFS, SCC decomposition, and bridge/ancestor/descendant
computations from Section 2. All algorithms are deterministic.
"""

from typing import Dict, List, Set, Tuple, Optional, Deque
from collections import deque

from prspnsd.graph import Digraph


def bfs_reachability(graph: Digraph, source: object) -> Set[object]:
    """Compute R^+(G, source): all vertices reachable from source via BFS.

    Time: O(m). Space: O(n).
    """
    visited: Set[object] = set()
    queue: Deque[object] = deque()
    queue.append(source)
    visited.add(source)
    out = graph._out_edges
    while queue:
        u = queue.popleft()
        for v in out.get(u, set()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return visited


def reverse_bfs_reachability(graph: Digraph, target: object) -> Set[object]:
    """Compute R^-(G, target): all vertices that can reach target.

    Runs BFS on the reversed graph. Time: O(m). Space: O(n).
    """
    visited: Set[object] = set()
    queue: Deque[object] = deque()
    queue.append(target)
    visited.add(target)
    inn = graph._in_edges
    while queue:
        u = queue.popleft()
        for v in inn.get(u, set()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return visited


def compute_r_plus(graph: Digraph, vertex: object) -> Set[object]:
    """Compute R^+(G, v)."""
    return bfs_reachability(graph, vertex)


def compute_r_minus(graph: Digraph, vertex: object) -> Set[object]:
    """Compute R^-(G, v)."""
    return reverse_bfs_reachability(graph, vertex)


def compute_r_ball(graph: Digraph, vertex: object) -> Set[object]:
    """Compute R(G, v) = R^+(G, v) ∪ R^-(G, v)."""
    return compute_r_plus(graph, vertex) | compute_r_minus(graph, vertex)


def _compute_r_sets_for_vertices(
    graph: Digraph, vertices: List[object]
) -> Tuple[Set[object], Set[object]]:
    """Compute union of R^+ and R^- for a set of vertices efficiently."""
    r_minus: Set[object] = set()
    r_plus: Set[object] = set()
    for v in vertices:
        r_minus |= compute_r_minus(graph, v)
        r_plus |= compute_r_plus(graph, v)
    return r_minus, r_plus


def compute_ancestors(graph: Digraph, path_vertices: List[object]) -> Set[object]:
    """Compute R^-(G, P) \ R^+(G, P): ancestors of path P."""
    r_minus, r_plus = _compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus - r_plus


def compute_descendants(graph: Digraph, path_vertices: List[object]) -> Set[object]:
    """Compute R^+(G, P) \ R^-(G, P): descendants of path P."""
    r_minus, r_plus = _compute_r_sets_for_vertices(graph, path_vertices)
    return r_plus - r_minus


def compute_bridges(graph: Digraph, path_vertices: List[object]) -> Set[object]:
    """Compute R^-(G, P) ∩ R^+(G, P): bridges of path P."""
    r_minus, r_plus = _compute_r_sets_for_vertices(graph, path_vertices)
    return r_minus & r_plus


def parallel_bfs(
    graph: Digraph,
    source: object,
    shortcut_edges: Optional[Set[Tuple[object, object]]] = None,
) -> Set[object]:
    """BFS on G ∪ H where H is a shortcut set.

    This simulates the parallel reachability primitive from Section 1.1.
    Sequential simulation; span bounds are NOT DETERMINED.
    """
    visited: Set[object] = set()
    queue: Deque[object] = deque()
    queue.append(source)
    visited.add(source)
    out = graph._out_edges
    while queue:
        u = queue.popleft()
        for v in out.get(u, set()):
            if v not in visited:
                visited.add(v)
                queue.append(v)
        if shortcut_edges:
            for a, b in shortcut_edges:
                if a == u and b not in visited:
                    visited.add(b)
                    queue.append(b)
    return visited


def strongly_connected_components(graph: Digraph) -> List[Set[object]]:
    """Compute SCCs using Kosaraju's algorithm. O(n + m) time.

    Returns a list of sets, each being an SCC.
    """
    visited: Set[object] = set()
    finish_order: List[object] = []
    out = graph._out_edges

    def dfs1(v: object) -> None:
        visited.add(v)
        for w in out.get(v, set()):
            if w not in visited:
                dfs1(w)
        finish_order.append(v)

    for v in graph.vertices():
        if v not in visited:
            dfs1(v)

    rev = graph.reversed()
    rev_out = rev._out_edges
    visited.clear()
    sccs: List[Set[object]] = []

    def dfs2(v: object, component: Set[object]) -> None:
        visited.add(v)
        component.add(v)
        for w in rev_out.get(v, set()):
            if w not in visited:
                dfs2(w, component)

    for v in reversed(finish_order):
        if v not in visited:
            component: Set[object] = set()
            dfs2(v, component)
            sccs.append(component)

    return sccs


def topological_sort(graph: Digraph) -> List[object]:
    """Return a topological ordering of a DAG. Raises ValueError if cycles exist.

    Uses Kahn's algorithm. Time: O(n + m).
    """
    in_degree: Dict[object, int] = {v: graph.degree_in(v) for v in graph.vertices()}
    queue: Deque[object] = deque([v for v, d in in_degree.items() if d == 0])
    result: List[object] = []
    out = graph._out_edges

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
