"""Property-based tests supporting the lemmas in docs/paper_refinements.md.

These use hypothesis @given to generate random DAGs across many
configurations. Property-based tests are stronger than the
seed-parameterised tests in test_paper_lemmas.py because they
explore the input space more thoroughly.
"""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reachq.generators import random_dag
from reachq.reachability import bfs_reachability, parallel_bfs
from reachq.shortcut import build_shortcut_set_for_reachability

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


def run(g, refinement: dict, seed: int):
    return build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=seed, refinement=refinement
    )


@given(
    n=st.integers(min_value=20, max_value=60),
    p=st.floats(min_value=0.05, max_value=0.4),
    seed=st.integers(min_value=0, max_value=2**20),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_lemma_2_1_tc_soundness_property(n, p, seed):
    """Lemma 2.1: TC-pruning is sound whenever it fires.

    Property: for any random DAG, soundness holds for all 3 flag
    configurations.
    """
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    for flags in (PAPER_TC, TIGHT_TC, NO_TC):
        shortcuts, _, _ = run(g, flags, seed)
        for v in g.vertices():
            original = bfs_reachability(g, v)
            augmented = parallel_bfs(g, v, shortcuts)
            assert original == augmented


@given(
    n=st.integers(min_value=40, max_value=80),
    p=st.floats(min_value=0.2, max_value=0.4),
    seed=st.integers(min_value=0, max_value=2**20),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_lemma_2_2_size_contribution_property(n, p, seed):
    """Lemma 2.2: tightened trigger never strictly increases |H|."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    _, _, _ = run(g, NO_TC, seed)
    h_paper, _, _ = run(g, PAPER_TC, seed)
    h_tight, _, _ = run(g, TIGHT_TC, seed)
    assert len(h_tight) <= len(h_paper)


@given(
    n=st.integers(min_value=20, max_value=80),
    p=st.floats(min_value=0.05, max_value=0.4),
    seed=st.integers(min_value=0, max_value=2**20),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_lemma_3_2_reachability_correctness_hop_bounded_property(n, p, seed):
    """Lemma 3.2: hop-bounded BFS preserves reachability."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    shortcuts, _, _ = run(g, HOP_BOUNDED, seed)
    for v in g.vertices():
        original = bfs_reachability(g, v)
        augmented = parallel_bfs(g, v, shortcuts)
        assert original == augmented
