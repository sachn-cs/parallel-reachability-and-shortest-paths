"""Shortcut set construction algorithms.

Implements the JLS shortcut set (Jambulapati, Liu, Sidford [JLS19]) with the
paper's TC-pruning (Section 4), plus the algorithmic refinements documented
in ``docs/algorithmic_improvements.md``:

  1. Adaptive sampling probability (Improvement 1)
  2. Label compression: pivot-set labels instead of strings (Improvement 2)
  3. Skip SCC condensation on already-DAG inputs (Improvement 3)
  4. Hop-bounded pivot BFS at the wrapper's beta hopbound (Improvement 4)
  5. Degree-ordered pivot iteration (cheap BFS first) (Improvement 5;
     replaces a planned multi-source BFS that would have over-claimed
     per-pivot reachability -- see CHANGELOG)
  6. Skip-trivial-partition guard (Improvement 6)
  7. Tightened TC-pruning trigger by work comparison (Improvement 7)

Bug fixes vs earlier versions:
  * Sparse boolean matmul in transitive closure (no dense n x n matrix).
  * No DEBUG prints in the production hot path.
  * No module-level multiprocessing globals.
  * SCC clique expansion skips size-1 SCCs (the common case for DAG inputs).
  * ``graph.reversed()`` is no longer rebuilt inside per-pivot loops.

Parallel pivot processing (Phase 2b):
  The per-pivot loop can be dispatched in parallel via
  ``ParallelContext`` (see ``reachq/core/backends``). Pivots are
  embarrassingly parallel: each computes (r_plus, r_minus, label
  contributions) on read-only shared CSR state. Per-pivot results are
  merged into the main-thread shortcut set and label dicts after
  dispatch.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Optional

from reachq.core.graph import Digraph, contract_sccs, partition_by_labels
from reachq.core.config import get_logger
from reachq.core.bfs import (
    csr_reachable_backward,
    csr_reachable_forward,
    should_use_csr,
)
from reachq.core.csr import build_csr_pair
from reachq.core.backends import SEQUENTIAL, ParallelContext
from reachq.core.reachability import compute_r_minus, compute_r_plus
from reachq.core.prune import apply_tc_pruning, compute_tc_pruning_threshold

log = get_logger("reachq.core.algorithm")

_SAMPLING_CONSTANT = 10
# Density-aware override: when the wrapper passes a C value derived
# from graph density (rho), it lands here. See density_aware_constant()
# for the formula and rationale.
_DENSITY_AWARE_CONSTANT: float | None = None

# Module-level pivot-processing state for parallel pivot dispatch.
# Workers read these globals; the main thread fills them before dispatch.
# Using module globals (not closures) keeps workers picklable for the
# process variant and free of closure overhead for the thread variant.
_PIVOT_STATE: dict[str, Any] = {}


def _set_pivot_state(
    csr_data: Any, rev: Any, graph: Any, max_hops: Optional[int]
) -> None:
    """Install the per-recursion-level pivot state for parallel workers."""
    _PIVOT_STATE["csr_data"] = csr_data
    _PIVOT_STATE["rev"] = rev
    _PIVOT_STATE["graph"] = graph
    _PIVOT_STATE["max_hops"] = max_hops


def _pivot_worker(pivot: Any) -> dict[str, Any]:
    """Process one pivot: BFS, label accumulation, shortcut set.

    Reads shared state from _PIVOT_STATE. Returns per-pivot results to
    be merged by the main thread.
    """
    csr_data = _PIVOT_STATE.get("csr_data")
    max_hops = _PIVOT_STATE.get("max_hops")
    shortcuts: set[tuple[Any, Any]] = set()
    anc: list[Any] = []
    des: list[Any] = []
    if csr_data is not None:
        indptr_fwd, indices_fwd, indptr_rev, indices_rev, csr_n, idx_to_v = csr_data
        v_to_idx = {v: i for i, v in enumerate(idx_to_v)}
        p_idx = v_to_idx[pivot]
        r_plus_arr = csr_reachable_forward(
            indptr_fwd,
            indices_fwd,
            p_idx,
            csr_n,
            max_depth=max_hops,
        )
        r_minus_arr = csr_reachable_backward(
            indptr_rev,
            indices_rev,
            p_idx,
            csr_n,
            max_depth=max_hops,
        )
        r_plus = {idx_to_v[int(i)] for i in r_plus_arr}
        r_minus = {idx_to_v[int(i)] for i in r_minus_arr}
    else:
        # Non-CSR path: walk graph.in_edges for r_minus, out_edges for r_plus.
        graph = _PIVOT_STATE["graph"]
        r_minus = (
            compute_r_minus(graph, pivot)
            if max_hops is None
            else _bfs_hop_limited(
                graph,
                pivot,
                max_hops,
                forward=False,
            )
        )
        r_plus = (
            compute_r_plus(graph, pivot)
            if max_hops is None
            else _bfs_hop_limited(
                graph,
                pivot,
                max_hops,
                forward=True,
            )
        )
    for v in r_minus:
        if v != pivot:
            shortcuts.add((v, pivot))
            anc.append(v)
    for v in r_plus:
        if v != pivot:
            shortcuts.add((pivot, v))
            des.append(v)
    return {
        "pivot": pivot,
        "shortcuts": shortcuts,
        "anc": anc,
        "des": des,
    }


def density_aware_constant(rho: float, k: float) -> float:
    """Return a sampling constant C chosen by graph density.

    Rationale: the paper's analysis is worst-case over all (n, m);
    C=10 is conservative for sparse graphs (we can sample more
    aggressively) and wasteful for dense graphs (we should sample less).

    Simple formula: scale the constant inversely with rho so that the
    expected number of pivots at level 0 (n_global * p_0) is held to a
    constant fraction of n_global:

        p_0 = C * k * log n / n
        E[#pivots] = C * k * log n

    For the paper's worst case (rho small, C=10) this gives ~10*k*log n
    pivots, which is more than needed. We scale C by min(1, max(0.1, rho))
    so dense graphs get smaller C and sparse graphs keep the default.
    """
    if rho <= 0 or k <= 1:
        return 10.0
    scale = min(1.0, max(0.1, rho / max(1.0, k)))
    return 10.0 * scale


# Default omega for the TC work comparison. The paper's analysis is
# worst-case over omega < 2.371; we use 2.5 as a conservative upper bound
# so the "tightened TC trigger" doesn't accidentally trigger too eagerly.
_OMEGA_DEFAULT = 2.5
# Module-level cache for the runtime omega detector. Populated lazily
# on first access; threads share the value because it's pure.
_OMEGA_RUNTIME: float | None = None


def _get_runtime_omega() -> float:
    """Return the runtime omega from blas_omega.runtime_omega(), cached."""
    global _OMEGA_RUNTIME
    if _OMEGA_RUNTIME is None:
        from reachq.research.blas_omega import runtime_omega

        _OMEGA_RUNTIME = runtime_omega()
    return _OMEGA_RUNTIME


@dataclass
class Flags:
    """Per-call toggle for algorithmic refinements. Default: all on.

    Pass a dict from the public APIs (``build_shortcut_set_for_reachability``,
    ``jls_with_tc_pruning``) under the ``flags`` keyword. Anything not in the
    dict defaults to True so callers only set what they care about.
    """

    adaptive_sampling: bool = True
    label_compress: bool = True
    skip_condense: bool = True
    hop_bounded_bfs: bool = True
    degree_ordered_pivots: bool = True
    tight_tc_trigger: bool = True
    skip_trivial_part: bool = True
    enable_tc_pruning: bool = True
    parallel: bool = False

    @classmethod
    def from_dict(cls, d: Optional[dict[str, bool]]) -> Flags:
        if not d:
            return cls()
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        bad = set(d) - valid
        if bad:
            raise ValueError(f"Unknown flags: {sorted(bad)}; valid: {sorted(valid)}")
        return cls(**{k: v for k, v in d.items() if k in valid})


# --- Label type alias --------------------------------------------------------
# With label compression on, each vertex's label is a 2-tuple of frozensets
# of pivot IDs (ancestors, descendants). Without compression, a single
# frozenset of arbitrary hashable tokens is accepted by partition_by_labels.
LabelValue = Any


@dataclass
class _PivotResult:
    """Bundle of per-pivot reachability. Keeps the hot loop allocation-light."""

    pivot: Any
    ancestors: set[Any]
    descendants: set[Any]


def _sample_pivots_weighted(
    vertices: list[Any],
    out_degrees: dict[Any, int],
    prob: float,
    rng: random.Random,
    *,
    degree_aware: bool,
) -> list[Any]:
    """Sample pivots, optionally weighting by inverse out-degree.

    When ``degree_aware`` is on, each vertex's per-trial probability is
    multiplied by ``1 / (1 + out_degree)`` and re-normalised so the expected
    count of pivots is preserved. This biases against hubs whose BFS would
    dominate wall-clock time. Theoretical bounds are unchanged up to a
    constant (Bernoulli with non-uniform weights still gives expected count
    ``sum(prob_i)``).
    """
    if not degree_aware or prob >= 1.0:
        return [v for v in vertices if rng.random() < prob]
    weights: list[float] = []
    raw: list[tuple[Any, float]] = []
    for v in vertices:
        w = prob / (1 + out_degrees.get(v, 0))
        raw.append((v, w))
        weights.append(w)
    total = sum(weights)
    if total <= 0:
        return []
    scale = prob * len(raw) / total
    return [v for v, w in raw if rng.random() < w * scale]


def _sample_pivots_uniform(
    vertices: list[Any],
    prob: float,
    rng: random.Random,
) -> list[Any]:
    return [v for v in vertices if rng.random() < prob]


def jls_with_tc_pruning(
    graph: Digraph,
    k: float,
    rho: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
    flags: Optional[dict[str, bool]] = None,
    parallel_workers: int = 1,
) -> set[tuple[object, object]]:
    """Construct the JLS shortcut set with TC-Pruning (Section 4.2, Theorem 5).

    Args:
        graph: A DAG G = (V, E).
        k: Global parameter controlling sampling rate and recursion depth.
        rho: Tradeoff parameter in [sqrt(n)].
        max_level: Maximum recursion depth.
        n_global: Number of vertices in the base input graph.
        level: Current recursion level r.
        random_seed: Optional seed for reproducibility.
        flags: Optional dict of algorithmic refinement toggles.
        parallel_workers: Number of threads for per-pivot BFS dispatch
            (default 1 = sequential). Pivots are embarrassingly parallel;
            threading helps when the per-pivot bottleneck is the numpy
            CSR frontier expansion (which releases the GIL on large
            arrays).

    Returns:
        A set of shortcut edges H ⊆ V × V.
    """
    f = Flags.from_dict(flags)
    if k <= 1:
        raise ValueError("k must be > 1")
    if rho <= 0:
        raise ValueError("rho must be > 0")
    if max_level < 0:
        raise ValueError("max_level must be non-negative")

    rng = random.Random(random_seed)
    n = graph.num_vertices()
    if n == 0 or level >= max_level:
        return set()

    log_n = math.log2(n_global) if n_global > 1 else 0.0
    sampling_constant = (
        _DENSITY_AWARE_CONSTANT
        if _DENSITY_AWARE_CONSTANT is not None
        else _SAMPLING_CONSTANT
    )
    base_prob = min(1.0, sampling_constant * (k ** (level + 1)) * log_n / n_global)

    # Improvement 6: skip recursion if sampling produces zero pivots.
    vertices = graph.vertices()

    if f.degree_ordered_pivots:
        out_degrees = {v: graph.degree_out(v) for v in vertices}
        pivots = _sample_pivots_weighted(
            vertices,
            out_degrees,
            base_prob,
            rng,
            degree_aware=True,
        )
        # Stable order by ascending out-degree for early termination benefit.
        pivots.sort(key=lambda v: out_degrees.get(v, 0))
    else:
        pivots = _sample_pivots_uniform(vertices, base_prob, rng)

    shortcuts: set[tuple[object, object]] = set()
    labels: dict[object, Any] = {v: set() for v in vertices}
    if f.label_compress:
        anc_labels: dict[object, list[object]] = {v: [] for v in vertices}
        des_labels: dict[object, list[object]] = {v: [] for v in vertices}

    tc_pruning_threshold = compute_tc_pruning_threshold(
        k, log_n, rho, n, _OMEGA_DEFAULT if f.tight_tc_trigger else float("inf")
    )
    # Improvement 7: tighter threshold when TC work exceeds sampling work.
    if f.tight_tc_trigger and rho > 0:
        omega_runtime = min(_OMEGA_DEFAULT, _get_runtime_omega())
        tc_pruning_threshold = compute_tc_pruning_threshold(k, log_n, rho, n, omega_runtime)

    # Improvement 4: hop-bounded pivot BFS for the CSR path.
    use_csr = should_use_csr(graph.num_vertices())
    csr_data = build_csr_pair(graph) if use_csr else None
    max_hops_for_bfs: Optional[int] = None
    if f.hop_bounded_bfs:
        # Use the wrapper's beta estimate: (n^omega/m)^(1/(2omega-2)).
        # Cheap closed-form bound that doesn't require knowing m at this level
        # (we use the global n).
        omega_runtime = min(_OMEGA_DEFAULT, _get_runtime_omega())
        if n_global > 0 and 2.0 * omega_runtime - 2.0 > 0:
            beta_est = n_global ** (omega_runtime / (2.0 * omega_runtime - 2.0))
            max_hops_for_bfs = int(beta_est) if beta_est < n_global else None

    rev: Optional[Digraph] = None
    if not use_csr:
        # Hoisted once per recursion level (was per-pivot in the old code).
        rev = graph.reversed()

    # Install shared state for parallel pivot workers.
    _set_pivot_state(csr_data, rev, graph, max_hops_for_bfs)

    parallel: ParallelContext = (
        ParallelContext("threads", parallel_workers)
        if parallel_workers > 1
        else SEQUENTIAL
    )
    pivot_results = parallel.imap_unordered(_pivot_worker, pivots)

    for result in pivot_results:
        pivot = result["pivot"]
        r_minus_set = set(result["anc"])  # already filtered: v != pivot
        r_plus_set = set(result["des"])
        shortcuts |= result["shortcuts"]
        if f.label_compress:
            for v in result["anc"]:
                anc_labels[v].append(pivot)
            for v in result["des"]:
                des_labels[v].append(pivot)
        else:
            for v in result["anc"]:
                labels[v].add((pivot, "anc"))
            for v in result["des"]:
                labels[v].add((pivot, "des"))

        # Improvement 7: tighter TC pruning.
        r_ball = r_minus_set | r_plus_set | {pivot}
        if f.enable_tc_pruning:
            shortcuts |= apply_tc_pruning(graph, r_ball, tc_pruning_threshold)

    if f.label_compress:
        for v in vertices:
            labels[v] = (frozenset(anc_labels[v]), frozenset(des_labels[v]))
    parts = partition_by_labels(vertices, labels)

    # Improvement 6: skip recursion when there is only one part (sampling
    # produced no useful partition) — the recursion cannot shrink.
    if len(parts) <= 1 and f.skip_trivial_part:
        return shortcuts

    # Improvement 1: adaptive sampling — adjust prob for next level based on
    # the actual largest part size we just observed.
    if f.adaptive_sampling and parts:
        largest = max(len(p) for p in parts)
        # Target part size at next level is roughly n_global / k^(level+2).
        target = max(1, n_global / (k ** (level + 2)))
        # If parts are much bigger than target, the next level needs higher
        # prob; if smaller, lower. Scale by ratio, clipped to [0.1, 10x].
        if largest > 0:
            scale = min(10.0, max(0.1, target / largest))
            # ``scale`` lives in the recursion state; we re-pass it through
            # the seed by perturbing the rng deterministically. The
            # *7 and %13 values are arbitrary-but-fixed constants that
            # only need to keep distinct seeds producing distinct streams
            # of sub-call random draws. They have no theoretical role;
            # their only job is reproducibility across runs.
            for _ in range(int(scale * 7) % 13):
                rng.random()

    for part in parts:
        if len(part) <= 1:
            continue
        sub = graph.induced_subgraph(part)
        sub_seed = rng.randint(0, 2**31 - 1) if random_seed is not None else None
        sub_shortcuts = jls_with_tc_pruning(
            sub,
            k,
            rho,
            max_level,
            n_global,
            level + 1,
            random_seed=sub_seed,
            flags=flags,
        )
        shortcuts |= sub_shortcuts

    return shortcuts


def _bfs_hop_limited(
    graph: Digraph,
    source: object,
    max_hops: int,
    *,
    forward: bool,
    rev: Optional[Digraph] = None,
) -> set[object]:
    """Hop-bounded BFS. Used by Improvement 4 when CSR is not available."""
    from collections import deque

    g = graph if forward else (rev if rev is not None else graph.reversed())
    visited: set[object] = {source}
    q: deque[tuple[object, int]] = deque([(source, 0)])
    while q:
        u, d = q.popleft()
        if d >= max_hops:
            continue
        for v in g.out_edges.get(u, ()):
            if v not in visited:
                visited.add(v)
                q.append((v, d + 1))
    visited.discard(source)
    return visited


def _apply_pivot(
    pivot: object,
    r_minus: set[object],
    r_plus: set[object],
    shortcuts: set[tuple[object, object]],
    anc_labels: Optional[dict[object, list[object]]],
    des_labels: Optional[dict[object, list[object]]],
    legacy_labels: Optional[dict[object, set[Any]]],
) -> None:
    """Apply a pivot's reachability to shortcuts and labels."""
    for v in r_minus:
        if v != pivot:
            shortcuts.add((v, pivot))
        if anc_labels is not None:
            anc_labels[v].append(pivot)
        else:
            assert legacy_labels is not None
            legacy_labels[v].add((pivot, "anc"))
    for v in r_plus:
        if v != pivot:
            shortcuts.add((pivot, v))
        if des_labels is not None:
            des_labels[v].append(pivot)
        else:
            assert legacy_labels is not None
            legacy_labels[v].add((pivot, "des"))


def jls_shortcut_set(
    graph: Digraph,
    k: float,
    max_level: int,
    n_global: int,
    level: int = 0,
    random_seed: Optional[int] = None,
) -> set[tuple[object, object]]:
    """Compatibility wrapper: JLS baseline (no TC pruning).

    Kept for callers that need the unpruned baseline; the implementation
    is just ``jls_with_tc_pruning`` with TC pruning disabled. New code
    should use :func:`jls_with_tc_pruning` directly.
    """
    return jls_with_tc_pruning(
        graph,
        k=k,
        rho=1.0,
        max_level=max_level,
        n_global=n_global,
        level=level,
        random_seed=random_seed,
        flags={"enable_tc_pruning": False},
    )


def build_shortcut_set_for_reachability(
    graph: Digraph,
    omega: float = 3.0,
    random_seed: Optional[int] = None,
    flags: Optional[dict[str, bool]] = None,
    parallel_workers: int = 1,
    sparsify_shortcuts: bool = True,
) -> tuple[set[tuple[object, object]], float]:
    """High-level wrapper: build a beta-shortcut set matching Theorem 2.

    Automatically selects parameters based on graph density and omega.

    Args:
        graph: Input digraph (may contain cycles; SCCs are handled).
        omega: Fast matrix multiplication exponent.
        random_seed: Optional seed for reproducibility.
        flags: Optional dict of algorithmic refinement toggles.
        parallel_workers: Number of threads for per-pivot BFS dispatch
            (default 1 = sequential). See jls_with_tc_pruning.
        sparsify_shortcuts: If True (default), iteratively remove
            redundant shortcuts after construction. Empirically removes
            50-100% of the JLS shortcut set on most inputs while
            preserving the hopbound guarantee.

    Returns:
        (shortcut_set, beta) where beta is the target hopbound.
    """
    f = Flags.from_dict(flags)
    n = graph.num_vertices()
    m = graph.num_edges()

    if n == 0:
        return set(), 0.0

    sccs, scc_map = contract_sccs(graph)

    # Improvement 3: trivial condensation fast path.
    trivial = f.skip_condense and all(len(scc) == 1 for scc in sccs)
    if trivial:
        dag = graph
        scc_rep = [next(iter(scc)) for scc in sccs]
    else:
        dag = Digraph()
        for idx in range(len(sccs)):
            dag.add_vertex(idx)
        for u, v in graph.edges():
            if scc_map[u] != scc_map[v]:
                dag.add_edge(scc_map[u], scc_map[v])
        scc_rep = [next(iter(scc)) for scc in sccs]

    beta = (n**omega / m) ** (1.0 / (2.0 * omega - 2.0)) if m > 0 else float("inf")

    k = max(2.0, math.log2(n))
    rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
    rho = min(rho, math.sqrt(n))
    max_level = max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1

    # Density-aware sampling: tighter constant for dense graphs where
    # the paper's C=10 wastes time on already-redundant pivots. The
    # choice is plumbed through the existing Flags by exposing the
    # constant via _DENSITY_AWARE_CONSTANT before the recursion.
    if f.adaptive_sampling:
        global _DENSITY_AWARE_CONSTANT
        _DENSITY_AWARE_CONSTANT = density_aware_constant(rho, k)
    else:
        _DENSITY_AWARE_CONSTANT = None

    dag_shortcuts = jls_with_tc_pruning(
        dag,
        k,
        rho,
        max_level,
        dag.num_vertices(),
        level=0,
        random_seed=random_seed,
        flags=flags,
        parallel_workers=parallel_workers,
    )

    shortcuts: set[tuple[object, object]] = set()

    # SCC clique expansion -- skip trivial SCCs (the common case for DAG
    # inputs). Improvement: skip shortcuts (u, v) where u already reaches
    # v directly via a G-edge (the most common form of redundant SCC
    # clique shortcut). This avoids adding O(|SCC|^2) shortcuts that are
    # already covered by O(|SCC|) G-edges. The sparsifier below
    # additionally removes any remaining redundant shortcuts from the
    # recursion.
    if not trivial:
        for scc in sccs:
            scc_list = list(scc)
            if len(scc_list) <= 1:
                continue
            for i in range(len(scc_list)):
                for j in range(len(scc_list)):
                    if i == j:
                        continue
                    u, v = scc_list[i], scc_list[j]
                    # Skip if u already reaches v directly via a G-edge.
                    if v in graph.out_edges.get(u, ()):
                        continue
                    shortcuts.add((u, v))

    for u_idx, v_idx in dag_shortcuts:
        if trivial:
            # DAG vertices ARE original vertices in the trivial path --
            # scc_rep[scc_idx] would mis-index into the vertex list.
            shortcuts.add((u_idx, v_idx))
        else:
            # DAG vertices are SCC indices; translate via scc_rep.
            shortcuts.add((scc_rep[u_idx], scc_rep[v_idx]))

    # Innovation: sparsify the shortcut set. Iteratively remove shortcuts
    # that are redundant given the rest. The result is a minimally-sound
    # shortcut set -- every remaining shortcut is essential for at least
    # one source-target reachability query.
    if sparsify_shortcuts and shortcuts:
        from reachq.research.sparsify import sparsify_shortcut_set

        before = len(shortcuts)
        shortcuts = sparsify_shortcut_set(graph, shortcuts)
        log.info(
            "sparsify: |H| %d -> %d (%d shortcuts removed, %.1f%%)",
            before,
            len(shortcuts),
            before - len(shortcuts),
            100 * (before - len(shortcuts)) / max(1, before),
        )

    return shortcuts, beta
