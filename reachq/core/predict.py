"""Predictors for shortcut-set and hopset parameters.

* :func:`predict_omega` -- conservative runtime omega based on
  graph density.
* :func:`predict_epsilon` -- ``(1+eps)`` approximation factor for
  hopsets.
* :func:`predict_rho` -- shortcut-set density/hopbound tradeoff.

All predictors in this module are heuristic defaults calibrated
against the test suite. They are NOT learned models; they exist
to give reasonable starting values for the explicit parameters
accepted by :func:`reachq.core.shortcut.build_shortcut_set_for_reachability`
and :func:`reachq.core.hopset.build_hopset_for_sssp`. Callers
should override when the heuristic is wrong.

The signatures accept a graph (or its vertex/edge counts) so that
the heuristic can vary with the input. The previous version
ignored the argument; this module exists to make the heuristic
real.
"""

from __future__ import annotations

import math

from reachq.core.graph import Digraph


def _runtime_omega() -> float:
    """Conservative runtime omega for the running BLAS."""
    from reachq.research.blas_omega import runtime_omega

    return runtime_omega()


def predict_omega(graph: Digraph) -> float:
    """Predict the matrix-multiplication exponent omega for this graph.

    Uses graph density to choose between Strassen-class (``2.5``)
    and schoolbook (``3.0``) bounds:

    * Small (``n < 100``) or dense (``m / n^2 > 0.3``): return
      ``2.5`` -- Strassen-class upper bound.
    * Otherwise: return :func:`_runtime_omega` (BLAS-dependent).

    Args:
        graph: The digraph whose density determines omega.

    Returns:
        Conservative runtime omega, in the interval [2.0, 3.0].
    """
    n = graph.num_vertices()
    if n < 100:
        return 2.5
    m = graph.num_edges()
    density = m / max(1, n * n)
    if density > 0.3:
        return 2.5
    return _runtime_omega()


def predict_epsilon(n_vertices: int) -> float:
    """Predict the ``(1+eps)`` approximation parameter for the hopset.

    Heuristic: ``eps = 1 / sqrt(n)`` clamped to ``[0.01, 0.5]``.
    """
    if n_vertices <= 1:
        return 0.5
    eps = 1.0 / math.sqrt(max(2, n_vertices))
    return float(max(0.01, min(0.5, eps)))


def predict_rho(n_vertices: int, n_edges: int) -> float:
    """Predict rho for the shortcut-set construction.

    Returns ``min(sqrt(n) / beta, sqrt(n))`` where ``beta`` is the
    paper's worst-case hopbound for these ``(n, m)``.
    """
    if n_vertices == 0:
        return 0.0
    if n_edges == 0:
        return float(math.sqrt(n_vertices))
    beta = (n_vertices**3.0 / n_edges) ** (1.0 / 4.0)
    if beta <= 0:
        return float(math.sqrt(n_vertices))
    return min(math.sqrt(n_vertices) / beta, math.sqrt(n_vertices))


__all__ = [
    "predict_epsilon",
    "predict_omega",
    "predict_rho",
]
