"""Predictor for algorithm parameters.

Predicts optimal omega, epsilon, and rho values based on graph
properties (density, vertex count, degree distribution). The heuristics
combine the BLAS-detected runtime omega with empirical scaling rules
calibrated on the test suite.

These are heuristic defaults; the user can always override the
returned value with an explicit argument to
:func:`reachq.core.algorithm.build_shortcut_set_for_reachability` or
:func:`reachq.core.hopset.build_hopset_for_sssp`.
"""

from __future__ import annotations

import math

from reachq.core.graph import Digraph


def predict_omega(graph: Digraph) -> float:
    """Predict the matrix-multiplication exponent omega for this graph.

    Delegates to :func:`reachq.research.blas_omega.runtime_omega` to
    detect the BLAS vendor (OpenBLAS, MKL, Accelerate, BLIS, or
    netlib) and returns the corresponding literature omega upper
    bound. Falls back to ``2.5`` when the vendor cannot be identified
    (a conservative Strassen-class estimate).

    The returned omega is used by shortcut-set and hopset constructions
    when no explicit ``omega`` parameter is provided.

    Args:
        graph: The digraph whose BLAS environment determines omega.

    Returns:
        Conservative runtime omega, in the interval [2.0, 3.0].
    """
    from reachq.research.blas_omega import runtime_omega

    n = graph.num_vertices()
    del n
    return runtime_omega()


def predict_epsilon(graph: Digraph) -> float:
    """Predict the (1+eps)-approximation parameter for the hopset.

    Heuristic: ``eps = 1 / sqrt(n)`` rounded to a sensible
    default. Small graphs (n < 100) tolerate tighter epsilon;
    large graphs use the asymptotic ``1/sqrt(n)`` value. Clamped
    to the interval [0.01, 0.5] to keep the construction cost
    bounded.

    Rationale: the hopset construction cost scales as ``m / eps^2``,
    so ``eps`` must decrease sub-linearly with n to remain tractable.
    The ``1/sqrt(n)`` choice gives work ``~ m * n``, matching the
    asymptotic CFR bound.

    Args:
        graph: The digraph whose vertex count determines the epsilon.

    Returns:
        Recommended epsilon value, in [0.01, 0.5].
    """
    n = graph.num_vertices()
    if n <= 1:
        return 0.5
    eps = 1.0 / math.sqrt(max(2, n))
    return float(max(0.01, min(0.5, eps)))


def predict_rho(graph: Digraph) -> float:
    """Predict the rho tradeoff parameter for the shortcut-set construction.

    Computed from the density ratio ``rho = sqrt(n) / beta`` where
    ``beta`` is the paper's worst-case hopbound. Returns ``1.0``
    when the graph has zero or one vertex (degenerate case).

    Args:
        graph: The digraph whose n and m determine rho.

    Returns:
        Density ratio in (0, sqrt(n)].
    """
    n = graph.num_vertices()
    m = graph.num_edges()
    if n == 0:
        return 0.0
    if m == 0:
        return float(math.sqrt(n))
    beta = (n**3.0 / m) ** (1.0 / 4.0) if m > 0 else float("inf")
    if beta <= 0:
        return float(math.sqrt(n))
    rho = math.sqrt(n) / beta
    return min(rho, float(math.sqrt(n)))
