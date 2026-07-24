"""Tests for reachq.lower_bound (Innovation #4: bound gap analysis)."""

from __future__ import annotations

from reachq.research.lower_bound import (
    barbell_graph,
    cycle_graph_dag,
    layered_dag,
    long_path_dag,
)


class TestConstructions:
    def test_barbell_n_and_m(self):
        g = barbell_graph(10)
        n = g.num_vertices()
        m = g.num_edges()
        # Two cliques of size 10 (each: 10*9 = 90 edges) + 1 bridge = 181.
        assert n == 20
        assert m == 181

    def test_layered_dag_n_and_m(self):
        g = layered_dag(5, 10)
        assert g.num_vertices() == 50
        # 4 inter-layer layers of 10*10 = 100 edges each = 400.
        assert g.num_edges() == 400

    def test_path_dag_n_and_m(self):
        g = long_path_dag(20)
        assert g.num_vertices() == 20
        assert g.num_edges() == 19

    def test_cycle_dag_n_and_m(self):
        g = cycle_graph_dag(10)
        assert g.num_vertices() == 10
        assert g.num_edges() == 10  # one edge per vertex in a directed cycle


class TestBoundGap:
    """The JLS construction can produce |H| far exceeding the bound on
    these constructions. Sparsify (Innovation #1) reduces the practical
    |H| to 0 in most cases. This is documented as a finding for
    Innovation #4: the paper's bound is loose on standard constructions.
    """

    def test_jls_overshoots_bound_on_long_path(self):
        from reachq.core.algorithm import build_shortcut_set_for_reachability

        g = long_path_dag(20)
        H, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        n = g.num_vertices()
        m = g.num_edges()
        omega = 3.0
        beta = (n**omega / m) ** (1.0 / (2.0 * omega - 2.0))
        rho = (n**0.5) / beta
        bound = m * rho + n * rho * rho
        # The JLS construction on a long path adds O(n^2) shortcuts to
        # compress the path, exceeding the bound.
        assert len(H) >= bound, (
            f"expected JLS to overshoot bound on long path; "
            f"got |H|={len(H)} bound={bound:.1f}"
        )

    def test_sparsify_closes_bound_gap_on_path(self):
        """Sparsify (Innovation #1) reduces the practical |H| below the
        paper's bound, since the JLS-added shortcuts are mostly redundant.
        """
        from reachq.core.algorithm import build_shortcut_set_for_reachability

        g = long_path_dag(20)
        H, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,  # sparsify_shortcuts=True (default)
        )
        # On a path graph, the JLS adds O(n^2) shortcuts but they all
        # compress the same path, so sparsify removes them all.
        assert len(H) == 0, (
            f"expected sparsify to remove all shortcuts on long path; "
            f"got |H|={len(H)}"
        )
