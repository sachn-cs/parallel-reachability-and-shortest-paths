"""Tests for reachq.closed_form."""

from __future__ import annotations

from reachq.research.closed_form import (
    binary_tree_dag,
    layered_dag_shortcut_set,
    lower_bound_path,
    path_shortcut_set,
    star_shortcut_set,
    upper_bound_paper,
)


class TestPathOptimality:
    def test_path_optimal_H_is_empty(self):
        """The n-path: optimal H is the empty set (the path already
        has the right reachability via direct edges).
        """
        for n in [10, 50, 100]:
            assert path_shortcut_set(n) == set()

    def test_path_lower_bound_is_zero(self):
        assert lower_bound_path(100) == 0


class TestCycleOptimality:
    def test_cycle_optimal_H_is_empty(self):
        """The n-cycle: every vertex reaches every other via the
        cycle, so optimal H is empty.
        """
        from reachq.research.closed_form import cycle_shortcut_set

        for n in [10, 50, 100]:
            assert cycle_shortcut_set(n) == set()


class TestStarOptimality:
    def test_star_optimal_H_is_empty(self):
        """The n-star: center reaches every leaf in 1 hop, every leaf
        reaches center in 1 hop. The 2-hop clique needs no shortcuts.
        """
        for n in [10, 50, 100]:
            assert star_shortcut_set(n) == set()


class TestLayeredDAGOptimality:
    def test_layered_dag_optimal_H_is_within_layer_cliques(self):
        """The layered DAG shortcut set adds one (j1, j2) pair per
        (j1, j2) within each layer where j1 != j2.

        For a layered DAG with ``layers`` layers of size ``layer_size``,
        the shortcut set has ``layers * layer_size * (layer_size - 1)``
        pairs, all of which connect two vertices in the same layer.
        """
        for layers, layer_size in [(5, 10), (10, 10)]:
            H = layered_dag_shortcut_set(layers, layer_size)
            assert len(H) == layers * layer_size * (layer_size - 1)
            for u, v in H:
                u_layer, _ = divmod(u, layer_size)
                v_layer, _ = divmod(v, layer_size)
                assert u_layer == v_layer


class TestTreeGenerator:
    def test_binary_tree_dag_n(self):
        g = binary_tree_dag(depth=3)
        # 2^4 - 1 = 15 vertices.
        assert g.num_vertices() == 15
        # Edges: each non-leaf has 2 children. For depth 3:
        # root (1) has 2 children (depth 1, 2 nodes total) each has 2
        # children. So 1 + 2 + 4 = 7 non-leaf edges.
        assert g.num_edges() == 14  # 15 - 1 (each vertex except root has 1 parent)


def test_upper_bound_paper_grows_superlinearly():
    """The paper's bound grows superlinearly with n on dense graphs."""
    bounds = [upper_bound_paper(n, n) for n in [10, 100, 1000, 10000]]
    ratio = bounds[3] / bounds[1]
    expected_ratio = (10000 / 100) ** 2
    assert ratio >= expected_ratio / 2
