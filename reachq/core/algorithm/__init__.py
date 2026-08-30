"""JLS shortcut-set construction.

Public entry points:

* :func:`build_shortcut_set_for_reachability` — high-level
  Theorem-2 wrapper.
* :func:`jls_with_tc_pruning` — direct JLS-with-TC entry point.
* :class:`RefinementConfig` and related are re-exported from
  :mod:`reachq.core.config`.
"""

from reachq.core.algorithm.wrap import (
    build_shortcut_set_for_reachability,
    density_aware_constant,
    jls_with_tc_pruning,
)
from reachq.core.config import RefinementConfig

__all__ = [
    "RefinementConfig",
    "build_shortcut_set_for_reachability",
    "density_aware_constant",
    "jls_with_tc_pruning",
]
