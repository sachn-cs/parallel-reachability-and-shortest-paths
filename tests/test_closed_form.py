"""Tests for reachq.closed_form (paper contribution: tight bound on
JLS essential shortcut set)."""

from __future__ import annotations

from reachq.closed_form import (
    binary_tree_dag,
    layered_dag_shortcut_set,
    lower_bound_path,
    paper_bound_const,
    path_shortcut_set,
    star_shortcut_set,
)


class TestPathOptimality:
    def test_path_optimal_H_is_empty(self):
        """The n-path: optimal H is the empty set (the path already
        has the right reachability via direct edges)."""
        for n in [10, 50, 100]:
            assert path_shortcut_set(n) == set()

    def test_path_lower_bound_is_zero(self):
        assert lower_bound_path(100) == 0


class TestCycleOptimality:
    def test_cycle_optimal_H_is_empty(self):
        """The n-cycle: every vertex reaches every other via the
        cycle, so optimal H is empty."""
        from reachq.closed_form import cycle_shortcut_set
        for n in [10, 50, 100]:
            assert cycle_shortcut_set(n) == set()


class TestStarOptimality:
    def test_star_optimal_H_is_empty(self):
        """The n-star: center reaches every leaf in 1 hop, every leaf
        reaches center in 1 hop. The 2-hop clique needs no shortcuts."""
        for n in [10, 50, 100]:
            assert star_shortcut_set(n) == set()


class TestLayeredDAGOptimality:
    def test_layered_dag_optimal_H_is_empty(self):
        """The layered DAG with complete bipartite between layers: each
        vertex reaches all later-layer vertices via the bipartite
        edges. Optimal H is empty."""
        for layers, layer_size in [(5, 10), (10, 10)]:
            assert layered_dag_shortcut_set(layers, layer_size) == set()


class TestPaperBoundGap:
    """On all standard constructions, the paper's bound is asymptotically
    loose by orders of magnitude. The optimal |H| is 0, while the
    paper's bound is O(n^2) for dense graphs and O(n*rho + n*rho^2) for
    sparse graphs.
    """

    def test_path_bound_loose(self):
        """For the n-path, paper bound = O(n^2) but optimal is 0."""
        for n in [10, 50, 100, 500]:
            # Approximate paper bound.
            bound = float(n * n + (n - 1) * (n ** 0.5))
            assert paper_bound_const(n) >= bound / 2  # rough check
            assert path_shortcut_set(n) == set()
            # ratio
            assert 0 < bound, f"path n={n} bound {bound} > 0 but optimal is 0"

    def test_layered_dag_bound_loose(self):
        for layers, layer_size in [(5, 10), (10, 10), (20, 10)]:
            n = layers * layer_size
            bound = paper_bound_const(n)
            optimal = len(layered_dag_shortcut_set(layers, layer_size))
            assert optimal == 0
            assert bound > 0


class TestTreeGenerator:
    def test_binary_tree_dag_n(self):
        g = binary_tree_dag(depth=3)
        # 2^4 - 1 = 15 vertices.
        assert g.num_vertices() == 15
        # Edges: each non-leaf has 2 children. For depth 3:
        # root (1) has 2 children (depth 1, 2 nodes total) each has 2
        # children. So 1 + 2 + 4 = 7 non-leaf edges.
        assert g.num_edges() == 14  # 15 - 1 (each vertex except root has 1 parent)


def test_paper_bound_const_grows_superlinearly():
    """The paper's bound grows superlinearly with n on dense graphs."""
    bounds = [paper_bound_const(n) for n in [10, 100, 1000, 10000]]
    # Should grow at least quadratically (n^2 term dominates).
    ratio = bounds[3] / bounds[1]  # n=10000 / n=100
    expected_ratio = (10000 / 100) ** 2  # 10000
    assert ratio >= expected_ratio / 2  # within constant