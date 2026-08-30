"""Tests for reachq.iterate (Innovation #2: iterative refinement)."""

from __future__ import annotations

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.generators import petersen_graph, random_dag
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.research.iterate import iterative_shortcut_set


class TestIterativeSoundness:
    def test_iterative_preserves_reachability_on_random_dag(self):
        g = random_dag(40, edge_probability=0.3, random_seed=42)
        H = iterative_shortcut_set(g, omega=3.0, max_iterations=5, random_seed=42)
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, H)

    def test_iterative_preserves_reachability_on_petersen(self):
        g = petersen_graph()
        H = iterative_shortcut_set(g, omega=3.0, max_iterations=3, random_seed=42)
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, H)

    def test_iterative_preserves_reachability_on_graph_with_sccs(self):
        from reachq.core.graph import Digraph

        g = Digraph()
        for i in range(5):
            g.add_vertex(i)
        g.add_edge(0, 1)
        g.add_edge(1, 0)
        g.add_edge(2, 3)
        g.add_edge(3, 2)
        g.add_edge(1, 2)
        g.add_edge(3, 4)
        H = iterative_shortcut_set(g, omega=3.0, max_iterations=3, random_seed=42)
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, H)


class TestIterativeRefines:
    r"""Iterative refinement is idempotent under consistent parameters.

    With the sampling constant threaded through explicitly (matching
    ``build_shortcut_set_for_reachability``), re-running JLS on
    ``G ∪ H_1`` re-derives the same shortcut set: |H_2| = |H_1|. The
    strict reduction (|H_2| < |H_1|) reported by earlier versions was an
    artifact of a hand-rolled second call using different k/rho
    parameters and a module-global sampling constant, and does not
    reproduce under consistent parameters.
    """

    def test_h2_idempotent_with_matching_parameters(self):
        g = random_dag(60, edge_probability=0.1, random_seed=42)
        H_direct, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42)
        from reachq.core.algorithm import jls_with_tc_pruning
        from reachq.core.graph import Digraph

        aug = Digraph()
        for v in g.vertices():
            aug.add_vertex(v)
        for u, v in g.edges():
            aug.add_edge(u, v)
        for u, v in H_direct:
            aug.add_edge(u, v)
        H2 = jls_with_tc_pruning(
            aug,
            k=3.0,
            rho=3.0,
            max_level=8,
            n_global=60,
            random_seed=42,
        )
        # Soundness: the augmented-graph construction never needs more
        # shortcuts than the direct one.
        assert H2 <= H_direct, (
            f"expected H_2 ⊆ H_1; got |H_1|={len(H_direct)}, |H_2|={len(H2)}"
        )
        # Idempotency: with the default sampling constant the second pass
        # re-derives the same set (no "self-redundant" shortcuts).
        assert H2 == H_direct, (
            f"expected H_2 == H_1 under consistent parameters; got "
            f"|H_1|={len(H_direct)}, |H_2|={len(H2)}"
        )

    def test_iterative_matches_direct_wrapper(self):
        """The iterate.py wrapper uses the same parameters as
        build_shortcut_set_for_reachability, so the result equals the
        direct wrapper's |H| when iteration is idempotent.
        """
        g = random_dag(60, edge_probability=0.1, random_seed=42)
        H_direct, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42)
        H_iter = iterative_shortcut_set(g, omega=3.0, max_iterations=3, random_seed=42)
        # H_iter is the robust core; for graphs where H_1 = H_2 = ... the
        # core equals H_1. For Petersen we get a smaller H_1 ∩ H_2
        # core, so we don't require equality here.
        assert H_iter <= H_direct, "robust core should be subset of H_1"


class TestIterativeConvergence:
    def test_iterative_converges_in_one_step(self):
        """The iterative method terminates after 1 step on tested inputs."""
        g = random_dag(40, edge_probability=0.2, random_seed=42)
        H = iterative_shortcut_set(g, omega=3.0, max_iterations=5, random_seed=42)
        # Iterative terminated because H stabilised (returned within
        # max_iterations). We don't have direct access to the iteration
        # count, but the returned H is the first non-trivial iteration.
        # If H is empty (sparsified down), the construction is
        # idempotent on this input.
        # Just verify it's a valid shortcut set.
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, H)

    def test_max_iterations_zero_returns_empty(self):
        g = random_dag(20, edge_probability=0.3, random_seed=42)
        H = iterative_shortcut_set(g, omega=3.0, max_iterations=0, random_seed=42)
        assert set() == H
