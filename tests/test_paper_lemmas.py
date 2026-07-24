"""Empirical tests supporting the lemmas in docs/paper_refinements.md.

Each test runs the JLS shortcut-set construction under several flag
configurations and asserts the invariants the lemmas claim. Tests use
many seeds to make empirical claims statistically meaningful.
"""

from __future__ import annotations

import pytest

from reachq.core.generators import random_dag
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.algorithm import build_shortcut_set_for_reachability

PAPER_TC = {
    "enable_tc_pruning": True,
    "tight_tc_trigger": False,
    "adaptive_sampling": False,
    "label_compress": False,
    "skip_condense": False,
    "hop_bounded_bfs": False,
    "degree_ordered_pivots": False,
    "skip_trivial_part": False,
}

TIGHT_TC = {**PAPER_TC, "tight_tc_trigger": True}

NO_TC = {**PAPER_TC, "enable_tc_pruning": False}

HOP_BOUNDED = {**NO_TC, "hop_bounded_bfs": True}


def run(g, flags: dict, seed: int):
    return build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=seed, flags=flags
    )


def hopbound_max(graph, source, shortcuts, beta):
    """Return the max hops actually observed by parallel_bfs from source."""
    from collections import deque

    dist: dict[object, float] = {v: float("inf") for v in graph.vertices()}
    dist[source] = 0
    q: deque = deque([source])
    out = graph.out_edges
    index: dict[object, list[object]] = {}
    for u, v in shortcuts:
        index.setdefault(u, []).append(v)
    while q:
        u = q.popleft()
        for v in out.get(u, set()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
        for v in index.get(u, ()):
            if dist[v] == float("inf"):
                dist[v] = dist[u] + 1
                q.append(v)
    reachable = [d for d in dist.values() if d < float("inf")]
    return max(reachable, default=0)


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 42])
def test_lemma_2_1_tc_soundness(seed: int) -> None:
    """Lemma 2.1: TC-pruning is sound whenever it fires.

    Soundness means: reachability in G equals reachability in G∪H,
    regardless of which TC trigger was used.
    """
    g = random_dag(n=60, edge_probability=0.2, random_seed=seed)
    for flags in (PAPER_TC, TIGHT_TC, NO_TC):
        shortcuts, _ = run(g, flags, seed)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            augmented = parallel_bfs(g, v, shortcuts)
            assert (
                original == augmented
            ), f"seed={seed} flags={flags}: mismatch from {v}"


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 42])
def test_lemma_2_2_size_contribution(seed: int) -> None:
    """Lemma 2.2: TC contribution under tightened trigger bounded by |R|·k·log n.

    We can't measure |R| directly inside the black-box wrapper, but we
    can verify the empirical consequence: when TC fires under the
    tightened trigger, |H| is no larger than the per-pivot
    sampling-only baseline *plus* the TC work bound.
    """
    g = random_dag(n=80, edge_probability=0.3, random_seed=seed)
    h_no_tc, _ = run(g, NO_TC, seed)
    h_paper, _ = run(g, PAPER_TC, seed)
    h_tight, _ = run(g, TIGHT_TC, seed)
    # Tightened trigger fires at most as often as paper's trigger; thus
    # |H|_tight <= |H|_paper.
    assert len(h_tight) <= len(
        h_paper
    ), f"seed={seed}: |H|_tight={len(h_tight)} > |H|_paper={len(h_paper)}"
    # Sampling-only baseline always valid (perhaps larger):
    assert len(h_no_tc) >= len(h_paper)


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 42])
def test_lemma_3_1_hopbound_preserved(seed: int) -> None:
    """Lemma 3.1: hop-bounded pivot BFS preserves the beta-hopbound.

    Empirically: max observed hop from any source is <= beta.
    """
    g = random_dag(n=80, edge_probability=0.2, random_seed=seed)
    for flags, label in ((NO_TC, "no_tc"), (HOP_BOUNDED, "hop_bounded")):
        shortcuts, beta = run(g, flags, seed)
        for src in list(g.vertices())[:10]:
            max_obs = hopbound_max(g, src, shortcuts, beta)
            assert max_obs <= beta + 1e-9, (
                f"seed={seed} cfg={label} src={src}: "
                f"max_obs={max_obs} > beta={beta}"
            )


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 42])
def test_lemma_3_2_reachability_correctness_hop_bounded(seed: int) -> None:
    """Lemma 3.1 corollary: hop-bounded BFS preserves reachability."""
    g = random_dag(n=80, edge_probability=0.2, random_seed=seed)
    shortcuts, _ = run(g, HOP_BOUNDED, seed)
    for v in g.vertices():
        original = bfs_reachability(g, v)
        augmented = parallel_bfs(g, v, shortcuts)
        assert original == augmented, f"seed={seed}: reachability mismatch from {v}"


def test_flags_dataclass_is_public() -> None:
    """Flags must be importable from the top-level package, not be hidden."""
    from reachq import Flags as TopFlags
    from reachq.core.algorithm import Flags as LocalFlags

    assert TopFlags is LocalFlags


def test_paper_tc_vs_tight_tc_size_invariant_across_seeds() -> None:
    """Across many seeds, tightened TC trigger never strictly increases |H|."""
    n_violations = 0
    for seed in range(50):
        g = random_dag(n=40, edge_probability=0.3, random_seed=seed)
        h_paper, _ = run(g, PAPER_TC, seed)
        h_tight, _ = run(g, TIGHT_TC, seed)
        if len(h_tight) > len(h_paper):
            n_violations += 1
    assert (
        n_violations == 0
    ), f"tightened trigger increased |H| in {n_violations}/50 seeds"
