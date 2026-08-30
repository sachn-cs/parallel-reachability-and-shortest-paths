"""Tests for reachq.adaptive_beta (Innovation #3)."""

from __future__ import annotations

from reachq.generators import (
    hamming_graph,
    paley_graph,
    petersen_graph,
    random_dag,
)
from reachq.research.adaptive_beta import adaptive_beta, paper_beta


class TestAdaptiveBeta:
    def test_returns_positive_on_nonempty_graph(self):
        g = random_dag(20, edge_probability=0.2, random_seed=42)
        beta = adaptive_beta(g, n_samples=5, random_seed=42)
        assert beta >= 1.0

    def test_returns_zero_on_empty_graph(self):
        from reachq.graph import Digraph

        beta = adaptive_beta(Digraph(), n_samples=5)
        assert beta == 0.0

    def test_seed_reproducibility(self):
        g = random_dag(40, edge_probability=0.2, random_seed=42)
        b1 = adaptive_beta(g, n_samples=10, random_seed=42)
        b2 = adaptive_beta(g, n_samples=10, random_seed=42)
        assert b1 == b2

    def test_higher_density_gives_smaller_beta(self):
        """Dense graphs have smaller reachability per step -> smaller beta."""
        sparse = random_dag(60, edge_probability=0.05, random_seed=42)
        dense = random_dag(60, edge_probability=0.3, random_seed=42)
        b_sparse = adaptive_beta(sparse, n_samples=20, random_seed=42)
        b_dense = adaptive_beta(dense, n_samples=20, random_seed=42)
        assert b_dense < b_sparse, (
            f"denser graph should have smaller beta: "
            f"b_sparse={b_sparse}, b_dense={b_dense}"
        )

    def test_safety_factor_increases_beta(self):
        g = random_dag(40, edge_probability=0.2, random_seed=42)
        b_low = adaptive_beta(g, n_samples=10, safety_factor=1.0, random_seed=42)
        b_high = adaptive_beta(g, n_samples=10, safety_factor=2.0, random_seed=42)
        assert b_high > b_low

    def test_petersen_bounded(self):
        g = petersen_graph()
        beta = adaptive_beta(g, n_samples=10, random_seed=42)
        assert beta >= 1.0
        assert beta <= 10  # Petersen diameter = 2, so beta ~ 3

    def test_paley_bounded(self):
        g = paley_graph(17)
        beta = adaptive_beta(g, n_samples=10, random_seed=42)
        assert beta >= 1.0
        assert beta <= 10  # Paley(17) diameter = 2

    def test_hamming_bounded(self):
        g = hamming_graph(2, 4)
        beta = adaptive_beta(g, n_samples=10, random_seed=42)
        assert beta >= 1.0
        assert beta <= 5  # H(2,4) diameter = 2


class TestPaperBeta:
    def test_paper_beta_formula(self):
        g = random_dag(60, edge_probability=0.3, random_seed=42)
        n = g.num_vertices()
        m = g.num_edges()
        omega = 3.0
        expected = (n**omega / m) ** (1.0 / (2.0 * omega - 2.0))
        assert paper_beta(g, omega=omega) == expected

    def test_paper_beta_infinity_on_empty_graph(self):
        g = random_dag(10, edge_probability=0.0, random_seed=42)
        # Edge_probability=0 gives m=0 -> beta = inf
        assert paper_beta(g) == float("inf")


class TestBetaComparison:
    """Compare adaptive_beta with paper_beta on tested fixtures.

    Documents the weak correlation: they measure different things
    (worst-case density bound vs. empirical eccentricity). The
    user should pick the appropriate one for their use case.
    """

    def test_both_positive_on_dense_random_dag(self):
        g = random_dag(60, edge_probability=0.3, random_seed=42)
        b_adapt = adaptive_beta(g, n_samples=20, random_seed=42)
        b_paper = paper_beta(g, omega=3.0)
        assert b_adapt > 0
        assert b_paper > 0

    def test_paper_beta_smaller_on_dense(self):
        """The paper's density-based bound is tighter on dense graphs."""
        g = random_dag(60, edge_probability=0.3, random_seed=42)
        b_adapt = adaptive_beta(g, n_samples=20, random_seed=42)
        b_paper = paper_beta(g, omega=3.0)
        # The paper's bound is smaller on dense graphs where density-based
        # reasoning is tight.
        assert b_paper < b_adapt, (
            f"on dense graph, paper_beta ({b_paper:.2f}) should be smaller "
            f"than adaptive_beta ({b_adapt:.2f})"
        )
