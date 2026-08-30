"""Picklable algorithm state passed to process workers.

The state carries everything a worker needs to expand one pivot:
CSR arrays for forward and reverse reachability, the vertex
tuple in insertion order, the insertion-order index map, and
the per-call ``max_hops`` for hop-bounded BFS. Workers never
share module-level state and never mutate the payload.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AlgorithmState:
    """Immutable worker payload.

    All fields are picklable. Workers receive a copy of this
    object as part of every task; they may not mutate the fields
    even though the dataclass is not literally frozen at the
    Python level.
    """

    indptr_fwd: np.ndarray
    indices_fwd: np.ndarray
    indptr_rev: np.ndarray
    indices_rev: np.ndarray
    idx_to_vertex: tuple[object, ...]
    n: int
    max_hops: int | None = None
