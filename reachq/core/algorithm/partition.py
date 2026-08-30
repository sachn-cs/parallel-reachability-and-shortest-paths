"""Label compression + partition by label equality.

Each vertex's label is a pair of frozensets: pivots whose
d-ancestor set contains the vertex, and pivots whose
d-descendant set contains it. Vertices with identical labels are
in the same partition; the construction recurses on each part.
"""

from __future__ import annotations

from reachq.core.graph import Digraph, partition_by_labels


def build_labels(
    vertices,
    pivots,
    r_plus_per_pivot: dict[object, set[object]],
    r_minus_per_pivot: dict[object, set[object]],
) -> dict[object, tuple[frozenset[object], frozenset[object]]]:
    """Build the per-vertex label tuple from accumulated r+/r-."""
    anc: dict[object, list[object]] = {v: [] for v in vertices}
    des: dict[object, list[object]] = {v: [] for v in vertices}
    for pivot in pivots:
        for v in r_minus_per_pivot.get(pivot, set()):
            anc.setdefault(v, []).append(pivot)
        for v in r_plus_per_pivot.get(pivot, set()):
            des.setdefault(v, []).append(pivot)
    return {
        v: (frozenset(anc.get(v, [])), frozenset(des.get(v, [])))
        for v in vertices
    }


def partition_vertices(
    vertices,
    labels: dict[object, tuple[frozenset, frozenset]],
) -> list[set[object]]:
    """Partition ``vertices`` by label equality via
    :func:`reachq.core.graph.partition_by_labels`."""
    return partition_by_labels(vertices, labels)
