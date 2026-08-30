"""Predictors for shortcut-set and hopset parameters.

* :func:`predict_omega` -- runtime BLAS omega (no ``graph`` dependency).
* :func:`predict_epsilon` -- ``(1+eps)`` approximation factor for hopsets.
* :func:`predict_rho` -- shortcut-set density/hopbound tradeoff.

These are heuristic defaults; callers may override by passing the
explicit argument to :func:`reachq.core.shortcut.build_shortcut_set_for_reachability`
or :func:`reachq.core.hopset.build_hopset_for_sssp`.
"""

from __future__ import annotations

import math


def predict_omega() -> float:
    """Return the conservative runtime omega for the running BLAS.

    Detects the BLAS vendor (OpenBLAS, MKL, Accelerate, BLIS, or
    netlib) and returns the corresponding literature omega upper
    bound. Falls back to ``3.0`` (Strassen-class) when the vendor
    cannot be identified.
    """
    from reachq.research.blas_omega import runtime_omega

    return runtime_omega()


def predict_epsilon(n_vertices: int) -> float:
    """Predict the (1+eps)-approximation parameter for the hopset.

    Heuristic: ``eps = 1 / sqrt(n)`` clamped to ``[0.01, 0.5]``.
    """
    if n_vertices <= 1:
        return 0.5
    eps = 1.0 / math.sqrt(max(2, n_vertices))
    return float(max(0.01, min(0.5, eps)))


def predict_rho(n_vertices: int, n_edges: int) -> float:
    """Predict rho for the shortcut-set construction.

    Returns ``min(sqrt(n) / beta, sqrt(n))`` where beta is the
    paper's worst-case hopbound.
    """
    if n_vertices == 0:
        return 0.0
    if n_edges == 0:
        return float(math.sqrt(n_vertices))
    beta = (n_vertices**3.0 / n_edges) ** (1.0 / 4.0)
    if beta <= 0:
        return float(math.sqrt(n_vertices))
    return min(math.sqrt(n_vertices) / beta, math.sqrt(n_vertices))


__all__ = ["predict_epsilon", "predict_omega", "predict_rho"]
