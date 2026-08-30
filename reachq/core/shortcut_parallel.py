"""Per-call process-pool dispatcher for the JLS shortcut construction.

Workers receive a single ``state`` argument carrying CSR arrays,
the insertion-order vertex tuple, and the per-call ``max_hops``.
The state is built once by :func:`reachq.core.shortcut.build_state`,
copied (by pickling) into each worker, and never mutated.

Sequential mode is the default. When ``mode="processes"`` and
``n_workers > 1``, work is dispatched via
:func:`concurrent.futures.ProcessPoolExecutor` with
``mp_context="spawn"`` so numpy/scipy re-import cleanly per worker
without inheriting lingering thread state from the parent process.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reachq.core.graph import Digraph
    from reachq.core.shortcut import ShortcutState


def expand_pivot(
    args: tuple[Digraph, ShortcutState, object],
) -> dict[str, Any]:
    """Worker function: ``expand_pivot((graph, state, pivot))``."""
    graph, state, pivot = args
    return _expand_one_pivot(graph, state, pivot)


def _expand_one_pivot(
    graph: Digraph,
    state: ShortcutState,
    pivot: object,
) -> dict[str, Any]:
    """Expand one pivot via CSR numpy BFS or deque fallback.

    Returns a dict ``{"r_plus": set, "r_minus": set}``. The pivot
    itself is removed from both sets.
    """
    from reachq.core.reachability import (
        bfs_reachability,
        reverse_bfs_reachability,
    )

    if state.csr_indptr is None or state.csr_indices is None:
        if state.max_hops is not None:
            r_plus = deque_hop_limited_bfs(
                graph, pivot, state.max_hops, forward=True
            )
            r_minus = deque_hop_limited_bfs(
                graph, pivot, state.max_hops, forward=False
            )
        else:
            r_plus = bfs_reachability(graph, pivot)
            r_minus = reverse_bfs_reachability(graph, pivot)
        r_plus.discard(pivot)
        r_minus.discard(pivot)
        return {"r_plus": r_plus, "r_minus": r_minus}

    from reachq.core.bfs import (
        csr_reachable_backward,
        csr_reachable_forward,
    )

    p_idx: int | None = None
    for i, v in enumerate(state.idx_to_vertex):
        if v == pivot:
            p_idx = i
            break
    if p_idx is None:
        return {"r_plus": set(), "r_minus": set()}
    r_plus_arr = csr_reachable_forward(
        state.csr_indptr,
        state.csr_indices,
        p_idx,
        state.n,
        max_depth=state.max_hops,
    )
    rev_indptr = state.csr_rev_indptr
    rev_indices = state.csr_rev_indices
    if rev_indptr is None or rev_indices is None:
        return {'r_plus': r_plus, 'r_minus': set()}
    r_minus_arr = csr_reachable_backward(
        rev_indptr,
        rev_indices,
        p_idx,
        state.n,
        max_depth=state.max_hops,
    )
    r_plus = {state.idx_to_vertex[int(i)] for i in r_plus_arr}
    r_minus = {state.idx_to_vertex[int(i)] for i in r_minus_arr}
    r_plus.discard(pivot)
    r_minus.discard(pivot)
    return {"r_plus": r_plus, "r_minus": r_minus}


def deque_hop_limited_bfs(
    graph: Digraph,
    source: object,
    max_hops: int,
    *,
    forward: bool,
) -> set[object]:
    """Hop-bounded deque BFS used when CSR arrays are unavailable."""
    from collections import deque

    visited: set[object] = {source}
    queue: deque[tuple[object, int]] = deque([(source, 0)])
    g = graph if forward else graph.reversed()
    while queue:
        u, d = queue.popleft()
        if d >= max_hops:
            continue
        for v in g.out_edges.get(u, ()):
            if v not in visited:
                visited.add(v)
                queue.append((v, d + 1))
    visited.discard(source)
    return visited


class ParallelExecutor:
    """Per-call dispatcher for the per-pivot loop.

    Modes:
        * ``"sequential"`` (default): ``map`` over the input list.
        * ``"processes"``: ``ProcessPoolExecutor`` with
          ``mp_context="spawn"``.

    Workers run :func:`expand_pivot` with the ``(graph, state, pivot)``
    tuple; state is never read from any module global.
    """

    def __init__(self, mode: str = "sequential", n_workers: int = 1) -> None:
        if mode not in {"sequential", "processes"}:
            raise ValueError(f"unknown parallel mode: {mode!r}")
        if mode == "processes" and n_workers < 1:
            raise ValueError("n_workers must be >= 1 for processes mode")
        self.mode = mode
        self.n_workers = n_workers

    def run(
        self,
        func: Callable[..., dict[str, Any]],
        graph: Digraph,
        state: ShortcutState,
        items: Iterable[object],
    ) -> list[dict[str, Any]]:
        """Dispatch ``items`` through ``func((graph, state, item))``."""
        tasks = [(graph, state, item) for item in items]
        if self.mode == "sequential" or self.n_workers <= 1:
            return [func(t) for t in tasks]
        if self.mode == "processes":
            import multiprocessing

            ctx = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(
                max_workers=self.n_workers, mp_context=ctx
            ) as pool:
                return list(pool.map(func, tasks))
        raise ValueError(f"unknown parallel mode: {self.mode!r}")

    def __repr__(self) -> str:
        return f"ParallelExecutor(mode={self.mode!r}, n_workers={self.n_workers})"


__all__ = ["ParallelExecutor", "deque_hop_limited_bfs", "expand_pivot"]
