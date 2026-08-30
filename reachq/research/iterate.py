"""Shortcut set iterative refinement (Innovation #2).

After the JLS construction produces H_0, iteratively refine:

    H_{k+1} = jls_with_tc_pruning(G ∪ H_k, ...)

Each iteration re-runs the JLS construction on the augmented graph
G ∪ H_k. The intuition: shortcuts in H_k expand reachability, so the
construction on G ∪ H_k produces *fewer* needed shortcuts (since some
queries are now satisfied by H_k rather than requiring a new pivot).

Robust core: we return H_1 ∩ H_2 ∩ ... (the intersection of all
iterations), which is the set of shortcuts that *every* iteration of
the construction agrees is needed. Shortcuts that appear in H_1 but
not H_2 are "self-redundant" (JLS added them, but JLS wouldn't
re-add them given H_1 already in the graph).

Soundness: the intersection of sound shortcut sets is sound. Each H_k
satisfies R+(G, s) ⊆ R+(G ∪ H_k, s), so the intersection does too.

Empirical finding:

  On random DAGs (n=60, p=0.1) with parameters matched to
  build_shortcut_set_for_reachability, the construction is IDEMPOTENT:
  |H_2| = |H_1| (the second pass over G ∪ H_1 re-derives the same set).
  The strict reduction reported in earlier versions (|H_1|=670,
  |H_2|=608) came from a hand-rolled second call that used different
  k/rho parameters than the wrapper and relied on a module-global
  sampling constant; it is not reproducible with consistent parameters
  and should not be relied on.

The robust-core semantics still hold: the intersection of sound
shortcut sets is sound, so even when the iteration is idempotent the
returned set is a valid shortcut set. When the intersection becomes
empty, the function returns the empty set rather than the last
iteration's H, matching the contract that the result is the *robust
core* (shortcuts present in every iteration).
"""




from __future__ import annotations

__experimental__ = True



from reachq.core.config import get_logger
from reachq.core.graph import Digraph
from reachq.core.shortcut import jls_with_tc_pruning

log = get_logger("reachq.iterate")


def iterative_shortcut_set(
    graph: Digraph,
    *,
    omega: float = 3.0,
    max_iterations: int = 5,
    random_seed: int | None = None,
) -> set[tuple[object, object]]:
    r"""Iteratively refine the shortcut set.

    Each iteration: H_{k+1} = jls_with_tc_pruning(G ∪ H_k, ...).
    Uses the same parameter selection as
    ``build_shortcut_set_for_reachability`` so iterations are
    comparable.

    Returns the ROBUST CORE: H_1 ∩ H_2 ∩ ... ∩ H_n, the intersection
    of all iterations. Shortcuts in the intersection are those that
    every iteration of the construction agrees are needed. Shortcuts
    in H_1 \ H_2 are "self-redundant" -- JLS added them but wouldn't
    re-add them given H_1 already in the graph.

    Args:
        graph: The input digraph G.
        omega: Fast-matrix-multiplication exponent (default 3.0).
        max_iterations: Hard cap on iterations.
        random_seed: Optional seed for reproducibility.

    Returns:
        The robust core shortcut set (intersection of all iterations),
        or the empty set if the intersection becomes empty.
    """
    import math
    import time

    if random_seed is not None:
        from reachq.core.config import configure_logging

        configure_logging()

    # Match the parameter selection of build_shortcut_set_for_reachability.
    n = graph.num_vertices()
    m = graph.num_edges()
    beta = (n**omega / m) ** (1.0 / (2.0 * omega - 2.0)) if m > 0 else float("inf")
    k = max(2.0, math.log2(n))
    rho = max(1.0, math.sqrt(n) / beta) if beta > 0 else 1.0
    rho = min(rho, math.sqrt(n))
    max_level = max(1, int(math.log(n) / math.log(k)) + 1) if k > 1 else 1
    from reachq.core.shortcut import density_aware_constant

    sampling_constant = density_aware_constant(rho, k)

    log.info(
        "iterative: starting (max_iterations=%d, k=%.2f, rho=%.2f, max_level=%d)",
        max_iterations,
        k,
        rho,
        max_level,
    )
    if max_iterations == 0:
        return set()

    def build(H: set[tuple[object, object]]) -> set[tuple[object, object]]:
        augmented = Digraph()
        for v in graph.vertices():
            augmented.add_vertex(v)
        for u, v in graph.edges():
            augmented.add_edge(u, v)
        for u, v in H:
            augmented.add_edge(u, v)
        return jls_with_tc_pruning(
            augmented,
            k=k,
            rho=rho,
            max_level=max_level,
            n_global=n,
            random_seed=random_seed,
            sampling_constant=sampling_constant,
        )

    history: list[set[tuple[object, object]]] = []
    H: set[tuple[object, object]] = set()
    core: set[tuple[object, object]] = set()
    for k_iter in range(max_iterations):
        t0 = time.perf_counter()
        H_new = build(H)
        elapsed = time.perf_counter() - t0
        history.append(H_new)
        log.info(
            "iterative: iter=%d |H_{k+1}|=%d (%.2fs)",
            k_iter,
            len(H_new),
            elapsed,
        )
        if k_iter == 0:
            core = set(H_new)
        else:
            core &= H_new
        if not core:
            log.warning(
                "iterative: robust core is empty at iter=%d (no shortcut "
                "appears in every iteration); returning the empty set",
                k_iter,
            )
            return set()
        H = H_new
        if k_iter > 0 and H_new == history[0]:
            log.info("iterative: converged at iter=%d (H stable)", k_iter)
            break
    log.info(
        "iterative: returning robust core |core|=%d (history |H|=%s)",
        len(core),
        [len(h) for h in history],
    )
    return core
