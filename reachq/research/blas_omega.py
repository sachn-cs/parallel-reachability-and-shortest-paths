"""Re-export of BLAS-detection helpers from :mod:`reachq.config`.

``runtime_omega`` is hardware introspection that lives with the
rest of the configuration layer; this module exists so existing
``from reachq.research.blas_omega import runtime_omega`` imports
keep working and so the research boundary stays explicit for
``__experimental__ = True`` callers.
"""

from __future__ import annotations

__experimental__ = True

from reachq.config import (
    BLAS_OMEGA_TABLE,
    detect_blas_vendor,
    omega_table,
    runtime_omega,
)

__all__ = [
    "BLAS_OMEGA_TABLE",
    "detect_blas_vendor",
    "omega_table",
    "runtime_omega",
]
