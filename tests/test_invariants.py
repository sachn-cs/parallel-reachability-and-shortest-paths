"""Tests for theorem-oriented validation helpers."""

import pytest

from prspnsd.generators import cycle_graph, path_graph, weighted_path_graph
from prspnsd.invariants import (
    assert_distance_approximation,
    assert_hopbound,
    assert_hopset_size_bound,
    assert_partition_correctness,
    assert_reachability_preserved,
    assert_scc_shortcuts_form_cliques,
    assert_shortcut_set_size_bound,
    check_equivalence_classes,
)
from prspnsd.shortcut_set import build_shortcut_set_for_reachability, jls_shortcut_set


class TestReachabilityPreserved:
    """Tests for assert_reachability_preserved."""

    def test_path_with_shortcuts(self):
        g = path_graph(10)
        shortcuts = jls_shortcut_set(g, k=2.0, max_level=3, n_global=10, random_seed=1)
        assert_reachability_preserved(g, shortcuts)

    def test_cycle_with_shortcuts(self):
        g = cycle_graph(5)
        shortcuts, _ = build_shortcut_set_for_reachability(g, random_seed=1)
        assert_reachability_preserved(g, shortcuts)

    def test_preservation_failure(self):
        g = path_graph(3)
        bad_shortcuts = {(2, 0)}  # adds backward reachability
        with pytest.raises(AssertionError):
            assert_reachability_preserved(g, bad_shortcuts)


class TestHopbound:
    """Tests for assert_hopbound."""

    def test_short_path(self):
        g = path_graph(5)
        shortcuts = {(0, 4)}
        assert_hopbound(g, 0, shortcuts, beta=4.0)

    def test_violation(self):
        g = path_graph(5)
        shortcuts = set()
        with pytest.raises(AssertionError):
            assert_hopbound(g, 0, shortcuts, beta=2.0)


class TestSccShortcuts:
    """Tests for assert_scc_shortcuts_form_cliques."""

    def test_cycle(self):
        g = cycle_graph(4)
        shortcuts, _ = build_shortcut_set_for_reachability(g, random_seed=1)
        assert_scc_shortcuts_form_cliques(g, shortcuts)

    def test_missing_clique(self):
        g = cycle_graph(3)
        shortcuts = {(0, 1), (1, 2)}  # missing (2, 0)
        with pytest.raises(AssertionError):
            assert_scc_shortcuts_form_cliques(g, shortcuts)

    def test_existing_edge_not_in_shortcuts(self):
        g = cycle_graph(3)
        # Complete the SCC clique: cycle has 0→1, 1→2, 2→0.
        # Missing reverse edges 1→0, 2→1, 0→2 for the clique.
        shortcuts = {(1, 0), (2, 1), (0, 2)}
        assert_scc_shortcuts_form_cliques(g, shortcuts)


class TestPartitionCorrectness:
    """Tests for assert_partition_correctness."""

    def test_valid_partition(self):
        g = path_graph(4)
        parts = [{0, 1}, {2, 3}]
        assert_partition_correctness(g, parts)

    def test_missing_vertex(self):
        g = path_graph(4)
        parts = [{0, 1}, {2}]
        with pytest.raises(AssertionError):
            assert_partition_correctness(g, parts)

    def test_overlapping_parts(self):
        g = path_graph(4)
        parts = [{0, 1}, {1, 2}]
        with pytest.raises(AssertionError):
            assert_partition_correctness(g, parts)

    def test_extra_vertices_in_part(self):
        g = path_graph(3)
        parts = [{0, 1, 99}]
        with pytest.raises(AssertionError):
            assert_partition_correctness(g, parts)


class TestDistanceApproximation:
    """Tests for assert_distance_approximation."""

    def test_exact_hopset(self):
        g = weighted_path_graph(5, weight_range=(1, 1), random_seed=1)
        hopset = {}
        ratios = assert_distance_approximation(g, hopset, source=0, epsilon=0.0, max_hops=100)
        # Source vertex has ratio 0.0; all others should be exactly 1.0.
        assert all(r == 1.0 for v, r in ratios.items() if v != 0)

    def test_violation(self):
        g = weighted_path_graph(3, weight_range=(1, 1), random_seed=1)
        hopset = {(0, 2): 10}
        with pytest.raises(AssertionError):
            assert_distance_approximation(g, hopset, source=0, epsilon=0.0, max_hops=1)

    def test_unreachable_vertex_in_hopset(self):
        g = weighted_path_graph(3, weight_range=(1, 1), random_seed=1)
        # Hopset only covers source, vertex 2 unreachable within hops
        hopset = {(0, 1): 1}
        with pytest.raises(AssertionError):
            assert_distance_approximation(g, hopset, source=0, epsilon=0.0, max_hops=1)


class TestShortcutSetSizeBound:
    """Tests for assert_shortcut_set_size_bound."""

    def test_within_bound(self):
        g = path_graph(10)
        shortcuts = {(0, i) for i in range(1, 10)}
        assert_shortcut_set_size_bound(g, shortcuts, rho=10.0)

    def test_violation(self):
        g = path_graph(10)
        shortcuts = {(0, i) for i in range(1, 10)}
        with pytest.raises(AssertionError):
            assert_shortcut_set_size_bound(g, shortcuts, rho=0.1)


class TestHopsetSizeBound:
    """Tests for assert_hopset_size_bound."""

    def test_within_bound(self):
        g = weighted_path_graph(10, random_seed=1)
        hopset = {(0, i): 1 for i in range(1, 10)}
        assert_hopset_size_bound(g, hopset, epsilon=0.1, rho=10.0)

    def test_violation(self):
        g = weighted_path_graph(10, random_seed=1)
        hopset = {(0, i): 1 for i in range(1, 10)}
        # Tight bound: eps=10.0 makes n/eps^2 tiny, so bound < |hopset|.
        with pytest.raises(AssertionError):
            assert_hopset_size_bound(g, hopset, epsilon=10.0, rho=0.1)


class TestEquivalenceClasses:
    """Tests for check_equivalence_classes."""

    def test_valid(self):
        labels = {0: {"A"}, 1: {"A"}, 2: {"B"}}
        parts = [{0, 1}, {2}]
        check_equivalence_classes(labels, parts)

    def test_mixed_labels_in_part(self):
        labels = {0: {"A"}, 1: {"B"}}
        parts = [{0, 1}]
        with pytest.raises(AssertionError):
            check_equivalence_classes(labels, parts)

    def test_vertex_in_wrong_part(self):
        labels = {0: {"A"}, 1: {"A"}, 2: {"B"}}
        # Vertex 1 has label A but is in the B part
        parts = [{0}, {1, 2}]
        with pytest.raises(AssertionError):
            check_equivalence_classes(labels, parts)
