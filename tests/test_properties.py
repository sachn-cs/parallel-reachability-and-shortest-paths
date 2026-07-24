"""Hypothesis-driven property tests for shortcut-set invariants.

These tests use random DAG generation with @given strategies to verify
the invariants in ``docs/paper_refinements.md`` across many seeds.
The number of examples is bounded by ``reachq_HYPOTHESIS`` env var
(default 20) so the suite stays under a few seconds.
"""

from __future__ import annotations

import os
from collections import deque

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reachq.core.generators import random_dag
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.algorithm import build_shortcut_set_for_reachability

EXAMPLES = int(os.environ.get("reachq_HYPOTHESIS", "20"))


def hopbound_max(graph, source, shortcuts, beta):
    """Return the max BFS depth observed from source in G + shortcuts."""
    dist = {v: float("inf") for v in graph.vertices()}
    dist[source] = 0
    q = deque([source])
    out = graph.out_edges
    index = {}
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


small_n = st.integers(min_value=10, max_value=80)
small_p = st.floats(min_value=0.05, max_value=0.4)
small_seed = st.integers(min_value=0, max_value=10**6)


@given(n=small_n, p=small_p, seed=small_seed)
@settings(
    max_examples=EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
def test_reachability_preserved(n, p, seed):
    """For every source, R+(G, s) == R+(G∪H, s)."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    shortcuts, _ = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
    )
    for v in g.vertices():
        assert bfs_reachability(g, v) == parallel_bfs(g, v, shortcuts)


@given(n=small_n, p=small_p, seed=small_seed)
@settings(
    max_examples=EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
def test_beta_hopbound_observed(n, p, seed):
    """Max BFS hops in G∪H is bounded by the beta from the construction."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    shortcuts, beta = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
    )
    if beta <= 0 or not shortcuts:
        return
    for src in list(g.vertices())[:5]:
        max_obs = hopbound_max(g, src, shortcuts, beta)
        assert (
            max_obs <= beta + 1e-9
        ), f"n={n} p={p} seed={seed}: max_obs={max_obs} > beta={beta}"


@given(n=small_n, p=small_p, seed=small_seed)
@settings(
    max_examples=EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
def test_no_self_loops_in_shortcut_set(n, p, seed):
    """Shortcut set must not contain self-loops."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    shortcuts, _ = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
    )
    for u, v in shortcuts:
        assert u != v


@given(n=small_n, p=small_p, seed=small_seed)
@settings(
    max_examples=EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
def test_shortcut_set_bounded_by_n_squared(n, p, seed):
    """Empirical sanity bound: |H| <= n*(n-1) (total possible DAG edges)."""
    g = random_dag(n=n, edge_probability=p, random_seed=seed)
    shortcuts, _ = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=seed,
    )
    n_vertices = g.num_vertices()
    assert len(shortcuts) <= n_vertices * (n_vertices - 1)


@pytest.mark.parametrize("seed", list(range(5)))
def test_reproducibility_across_seeds(seed):
    g = random_dag(n=60, edge_probability=0.2, random_seed=seed)
    s1, b1 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)
    s2, b2 = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=seed)
    assert s1 == s2
    assert b1 == b2
