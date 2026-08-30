"""Reachability over attributed graphs.

Extends reachability to graphs where vertices and edges carry
attributes. Reachability queries can filter on attribute values:

- **Vertex predicates** restrict which vertices can be visited
- **Edge predicates** restrict which edges can be traversed

A typical use: in a social network, only traverse edges whose
``relationship`` attribute is "friend" or "colleague" (not "blocked").

The implementation adapts the standard BFS from
:mod:`reachq.core.reachability` with two callback predicates that
gate vertex/edge acceptance. Both predicates default to "always
true" (no filtering).
"""




from __future__ import annotations

__experimental__ = True



from collections import deque
from collections.abc import Callable
from typing import Any

from reachq.graph import Digraph

VertexPredicate = Callable[[Any], bool]
"""Predicate over vertex objects. Returns True to allow visit."""

EdgePredicate = Callable[[Any, Any], bool]
"""Predicate over (source, target) edge pairs. Returns True to allow traversal."""


def attributed_bfs(
    graph: Digraph,
    source: object,
    *,
    vertex_pred: VertexPredicate | None = None,
    edge_pred: EdgePredicate | None = None,
) -> set[object]:
    """Reachability from ``source`` under attribute constraints.

    Performs a BFS from ``source``, visiting only vertices that
    satisfy ``vertex_pred`` and traversing only edges that satisfy
    ``edge_pred``. Self-loops and unreachable vertices are handled
    naturally.

    Args:
        graph: Input digraph.
        source: Starting vertex. Must be in ``graph``.
        vertex_pred: Optional predicate over vertex objects. If
            provided, vertices for which it returns False are
            excluded from the visited set (and not enqueued).
            Default: visit all vertices.
        edge_pred: Optional predicate over (u, v) pairs. If provided,
            edges for which it returns False are not traversed.
            Default: traverse all edges.

    Returns:
        Set of vertices reachable from ``source`` under the
        predicates. Always contains ``source`` itself (assuming
        ``vertex_pred(source)`` is True, otherwise the empty set).

    Raises:
        KeyError: If ``source`` is not in ``graph``.
    """
    if source not in graph:
        raise KeyError(f"source {source!r} not in graph")

    vp = vertex_pred if vertex_pred is not None else lambda _v: True
    ep = edge_pred if edge_pred is not None else lambda _u, _v: True

    if not vp(source):
        return set()

    visited: set[object] = {source}
    q: deque[object] = deque([source])
    out = graph.out_edges
    while q:
        u = q.popleft()
        for v in out.get(u, ()):
            if v in visited:
                continue
            if not vp(v):
                continue
            if not ep(u, v):
                continue
            visited.add(v)
            q.append(v)
    return visited


def attributed_reachable_pairs(
    graph: Digraph,
    sources: set[object],
    targets: set[object],
    *,
    vertex_pred: VertexPredicate | None = None,
    edge_pred: EdgePredicate | None = None,
) -> set[tuple[object, object]]:
    """Pairs (s, t) with s in ``sources`` and t in ``targets`` such that
    t is reachable from s under the given predicates.

    Computes the attributed BFS from each source and intersects the
    result with ``targets``. For small ``targets`` this is the
    standard "reachability-from-many" query.

    Args:
        graph: Input digraph.
        sources: Set of starting vertices.
        targets: Set of target vertices.
        vertex_pred: Optional vertex predicate (see :func:`attributed_bfs`).
        edge_pred: Optional edge predicate (see :func:`attributed_bfs`).

    Returns:
        Set of (source, target) pairs where the target is reachable
        from the source under the predicates.
    """
    out: set[tuple[object, object]] = set()
    for s in sources:
        if s not in graph:
            continue
        visited = attributed_bfs(graph, s, vertex_pred=vertex_pred, edge_pred=edge_pred)
        for t in targets:
            if t in visited:
                out.add((s, t))
    return out


def vertex_attribute_index(
    graph: Digraph,
    attribute_fn: Callable[[Any], Any],
) -> dict[Any, list[object]]:
    """Build an inverted index mapping attribute values to vertex lists.

    Useful for fast filtered reachability: instead of testing every
    vertex against a predicate, look up the allowed set directly.

    Args:
        graph: Input digraph.
        attribute_fn: Function mapping a vertex to its attribute value.

    Returns:
        Dict ``{attribute_value: [vertex1, vertex2, ...]}``.

    Example:
        >>> from reachq.graph import Digraph
        >>> g = Digraph()
        >>> for v in [0, 1, 2]:
        ...     g.add_vertex(v)
        >>> idx = vertex_attribute_index(g, lambda v: v % 2)
        >>> sorted(idx.keys())
        [0, 1]
        >>> sorted(idx[0])
        [0, 2]
    """
    index: dict[Any, list[object]] = {}
    for v in graph.vertices():
        attr = attribute_fn(v)
        index.setdefault(attr, []).append(v)
    return index
