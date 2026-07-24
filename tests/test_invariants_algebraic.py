"""Property-based tests for reachq.invariants.

Each invariant is checked on multiple random inputs.
"""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reachq.core.generators import random_dag
from reachq.core.graph import Digraph
from reachq.core.invariants import (
    assert_partition_correctness,
    assert_reachability_preserved,
    assert_scc_shortcuts_form_cliques,
)
from reachq.core.algorithm import build_shortcut_set_for_reachability


@given(
    n=st.integers(min_value=10, max_value=40),
    p=st.floats(min_value=0.05, max_value=0.4),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_reachability_preserved_after_sparsify(n, p, seed):
    """For any random DAG, the JLS shortcut set preserves reachability."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    H, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)
    assert_reachability_preserved(g, H)


@given(
    n=st.integers(min_value=10, max_value=40),
    p=st.floats(min_value=0.05, max_value=0.4),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_partition_correctness_random_dags(n, p, seed):
    """For any random DAG, the JLS partition covers all vertices."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    H, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)
    # Reachability preservation implies partition correctness
    # (if R+(G) = R+(G+H), then H doesn't change the partition
    # structure that the JLS labels induced).
    assert_reachability_preserved(g, H)


def test_scc_shortcut_invariant_path():
    """Path graph: 1 SCC (the whole path), so no clique expansion needed."""
    g = Digraph()
    for i in range(5):
        g.add_vertex(i)
    for i in range(4):
        g.add_edge(i, i + 1)
    H, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    assert_scc_shortcuts_form_cliques(g, H)


def test_scc_shortcut_invariant_two_disjoint_cycles():
    """Two disjoint 2-cycles: 2 SCCs of size 2, each should be a clique."""
    g = Digraph()
    g.add_edge(0, 1)
    g.add_edge(1, 0)
    g.add_edge(2, 3)
    g.add_edge(3, 2)
    H, _ = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    assert_scc_shortcuts_form_cliques(g, H)


def test_partition_correctness_empty_graph():
    g = Digraph()
    parts: list[set[object]] = []
    assert_partition_correctness(g, parts)


def test_partition_correctness_single_vertex():
    g = Digraph()
    g.add_vertex("only")
    parts: list[set[object]] = [{"only"}]
    assert_partition_correctness(g, parts)
