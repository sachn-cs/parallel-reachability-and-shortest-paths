"""SCC condensation for the reachability shortcut construction.

Each SCC is collapsed to a single vertex chosen from the
insertion-order ``Digraph``. Intra-SCC distances are computed
once per SCC and emitted as exact shortcuts in the final
shortcut set so that the condensation does not lose path
information.
"""

from __future__ import annotations

from reachq.core.graph import Digraph, WeightedDigraph
from reachq.core.reachability import strongly_connected_components
from reachq.core.shortest_paths import dijkstra


def contract_sccs_for_reachability(graph: Digraph) -> tuple[
    list[list[object]], dict[object, int], list[object]
]:
    """Compute SCC decomposition with deterministic ordering.

    Returns:
        ``(sccs, scc_map, representatives)``. Each entry of
        ``sccs`` is a list in insertion order; the representative
        is the first vertex of each SCC list.
    """
    components = strongly_connected_components(graph)
    sccs = [sorted(c, key=lambda v: graph.index_of(v)) for c in components]
    scc_map: dict[object, int] = {}
    representatives: list[object] = []
    for idx, scc in enumerate(sccs):
        for v in scc:
            scc_map[v] = idx
        representatives.append(scc[0])
    return sccs, scc_map, representatives


def intra_scc_shortcuts(
    graph: Digraph,
    sccs: list[list[object]],
) -> set[tuple[object, object]]:
    """All intra-SCC exact reachability edges (for reachability, unweighted)."""
    shortcuts: set[tuple[object, object]] = set()
    for scc in sccs:
        if len(scc) <= 1:
            continue
        sub = graph.induced_subgraph(set(scc))
        for u in scc:
            if u not in sub:
                continue
            r_plus = _bfs_plus(sub, u)
            r_plus.discard(u)
            for v in r_plus:
                if v in sub:
                    shortcuts.add((u, v))
        for u in scc:
            for v in scc:
                if u != v and (u, v) not in shortcuts:
                    shortcuts.add((u, v))
    return shortcuts


def intra_scc_shortcuts_weighted(
    graph: WeightedDigraph,
    sccs: list[list[object]],
) -> set[tuple[object, object]]:
    """All intra-SCC exact reachability edges."""
    shortcuts: set[tuple[object, object]] = set()
    for scc in sccs:
        if len(scc) <= 1:
            continue
        sub = graph.induced_subgraph(set(scc))
        sub_w: WeightedDigraph = WeightedDigraph()
        for v in sub.vertices():
            sub_w.add_vertex(v)
        for u in sub.vertices():
            for v, w in sub.out_edges.get(u, {}).items():
                sub_w.add_edge(u, v, w)
        for u in scc:
            if u not in sub_w:
                continue
            d = dijkstra(sub_w, u)
            for v in d:
                if v != u:
                    shortcuts.add((u, v))
    return shortcuts


def _bfs_plus(graph: Digraph, source: object) -> set[object]:
    """BFS forward; convenience wrapper."""
    visited: set[object] = {source}
    from collections import deque

    q: deque[object] = deque([source])
    while q:
        u = q.popleft()
        for v in graph.out_edges.get(u, ()):
            if v not in visited:
                visited.add(v)
                q.append(v)
    return visited
