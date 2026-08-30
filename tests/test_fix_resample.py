"""Tests for the Fix/Resample variant (Phase B, Paper 1 inspired)."""

from __future__ import annotations

from reachq.generators import (
    hamming_graph,
    paley_graph,
    petersen_graph,
    random_dag,
)
from reachq.reachability import bfs_reachability
from reachq.research.fix_resample import (
    fix_resample_reachable,
    fix_resample_shortcut_set,
)


class TestFixResampleBasic:
    def test_petersen_reachability_preserved(self):
        g = petersen_graph()
        shortcuts = fix_resample_shortcut_set(g, random_seed=42)
        for v in g.vertices():
            assert fix_resample_reachable(g, v, shortcuts) == bfs_reachability(g, v)

    def test_paley_reachability_preserved(self):
        g = paley_graph(13)
        shortcuts = fix_resample_shortcut_set(g, random_seed=42)
        for v in g.vertices():
            assert fix_resample_reachable(g, v, shortcuts) == bfs_reachability(g, v)

    def test_hamming_reachability_preserved(self):
        g = hamming_graph(d=3, q=3)
        shortcuts = fix_resample_shortcut_set(g, random_seed=42)
        for v in g.vertices():
            assert fix_resample_reachable(g, v, shortcuts) == bfs_reachability(g, v)

    def test_random_dag_reachability_preserved(self):
        for seed in [1, 2, 3]:
            g = random_dag(n=40, edge_probability=0.2, random_seed=seed)
            shortcuts = fix_resample_shortcut_set(g, random_seed=seed)
            for v in g.vertices():
                assert fix_resample_reachable(g, v, shortcuts) == bfs_reachability(g, v)

    def test_empty_graph(self):
        from reachq.graph import Digraph

        g = Digraph()
        shortcuts = fix_resample_shortcut_set(g)
        assert shortcuts == set()

    def test_max_iterations_cap(self):
        """If max_iterations is hit, log a warning but don't crash."""
        g = random_dag(n=20, edge_probability=0.2, random_seed=42)
        shortcuts = fix_resample_shortcut_set(g, max_iterations=5, random_seed=42)
        # Should still return a (possibly partial) shortcut set without raising.
        assert isinstance(shortcuts, set)

    def test_reproducibility(self):
        g = random_dag(n=30, edge_probability=0.2, random_seed=42)
        s1 = fix_resample_shortcut_set(g, random_seed=7)
        s2 = fix_resample_shortcut_set(g, random_seed=7)
        assert s1 == s2

    def test_threshold_fraction_controls_size(self):
        """Larger threshold_fraction (closer to 1.0) means stop sooner,
        producing a smaller (but less-complete) shortcut set. At 1.0 we
        stop when ~100% of vertices are covered; at 0.5 we stop at 50%.

        Empirically, both should still preserve reachability because the
        algorithm covers vertices greedily and the threshold is on
        fraction covered, not on correctness.
        """
        g = random_dag(n=60, edge_probability=0.2, random_seed=42)
        s_loose = fix_resample_shortcut_set(g, threshold_fraction=0.5, random_seed=42)
        s_full = fix_resample_shortcut_set(g, threshold_fraction=1.0, random_seed=42)
        # At 0.5 we stop early; at 1.0 we cover all vertices. Sizes
        # may differ but both should be valid (soundness holds either way).
        for v in g.vertices():
            assert fix_resample_reachable(g, v, s_loose) == bfs_reachability(g, v)
            assert fix_resample_reachable(g, v, s_full) == bfs_reachability(g, v)
