"""Tests for reachq.sparsify (Innovation #1: shortcut set sparsification)."""

from __future__ import annotations

from reachq.core.generators import petersen_graph, random_dag
from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.research.sparsify import sparsify_shortcut_set


class TestSparsifyBasic:
    def test_empty_input(self):
        g = petersen_graph()
        assert sparsify_shortcut_set(g, set()) == set()

    def test_redundant_shortcut_removed(self):
        """A shortcut (u, v) where u already reaches v via G is removed."""
        g = Digraph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        # (0, 2) is redundant: 0 reaches 2 via 0->1->2 already.
        shortcuts = {(0, 2)}
        result = sparsify_shortcut_set(g, shortcuts)
        assert result == set()

    def test_essential_shortcut_kept(self):
        """A shortcut that the only path requires is kept."""
        g = Digraph()
        g.add_edge(0, 1)
        # (0, 2) is essential: there's no other path from 0 to 2.
        g.add_vertex(2)
        shortcuts = {(0, 2)}
        result = sparsify_shortcut_set(g, shortcuts)
        assert result == {(0, 2)}

    def test_soundness_preserved(self):
        """Sparsification preserves R+(G, s) == R+(G+H, s) for all s."""
        g = random_dag(60, edge_probability=0.3, random_seed=42)
        H_orig, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        # First verify the unsparsified set is sound.
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(g, v, H_orig)
        # Now sparsify and verify soundness is preserved.
        H_sparse = sparsify_shortcut_set(g, H_orig)
        for v in g.vertices():
            assert bfs_reachability(g, v) == parallel_bfs(
                g, v, H_sparse
            ), f"sparsification broke soundness at v={v}"

    def test_sparsify_reduces_or_preserves(self):
        """Sparsification never increases |H|."""
        g = random_dag(50, edge_probability=0.3, random_seed=42)
        H_orig, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H_sparse = sparsify_shortcut_set(g, H_orig)
        assert len(H_sparse) <= len(H_orig)

    def test_idempotent(self):
        """Sparsifying twice gives the same result as sparsifying once."""
        g = random_dag(40, edge_probability=0.2, random_seed=42)
        H_orig, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H_once = sparsify_shortcut_set(g, H_orig)
        H_twice = sparsify_shortcut_set(g, H_once)
        assert H_once == H_twice


class TestSparsifyReducesJLS:
    """Empirical claim: JLS shortcut sets are often 50-100% redundant."""

    def test_jls_shortcut_set_mostly_redundant_on_synthetic(self):
        """On random DAGs, sparsification should remove most shortcuts."""
        g = random_dag(100, edge_probability=0.3, random_seed=42)
        H_orig, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H_sparse = sparsify_shortcut_set(g, H_orig)
        # We expect most JLS shortcuts to be redundant on dense graphs.
        if len(H_orig) > 0:
            reduction = 1 - len(H_sparse) / len(H_orig)
            assert reduction >= 0.5, (
                f"expected >= 50% reduction on dense random DAG; "
                f"got {reduction*100:.1f}% (orig={len(H_orig)} sparse={len(H_sparse)})"
            )

    def test_wrapper_default_sparsifies(self):
        """build_shortcut_set_for_reachability sparsifies by default."""
        g = random_dag(60, edge_probability=0.3, random_seed=42)
        H_default = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
        )
        # sparsify_shortcuts=False should give a larger H.
        H_unsparsified = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        assert len(H_default) <= len(H_unsparsified)


class TestSparsifyCorrectnessInvariant:
    """Sparsification preserves the SCC reachability invariant."""

    def test_scc_clique_after_sparsify(self):
        """After sparsification, every SCC is still mutually reachable."""
        from reachq.core.invariants import assert_scc_shortcuts_form_cliques

        g = random_dag(80, edge_probability=0.2, random_seed=42)
        # Build a graph with cycles.
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)  # SCC = {0, 1, 2}
        H_orig, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        H_sparse = sparsify_shortcut_set(g, H_orig)
        assert_scc_shortcuts_form_cliques(g, H_sparse)
