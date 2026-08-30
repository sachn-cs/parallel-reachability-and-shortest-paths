"""Adaptive sampling scaling.

When ``flags.adaptive_sampling`` is on, the sampling probability
for the next recursion level is scaled by ``target / largest``,
clipped to ``[0.1, 10]``. The scale is returned as a multiplier
on the current level's ``sampling_constant`` and threaded through
the recursive call. The legacy "RNG perturbation" workaround has
been removed — it didn't actually adjust the probability.
"""

from __future__ import annotations


def target_size(n_global: int, level: int, k: float) -> int:
    """Target part size at recursion ``level + 1``."""
    return max(1, int(n_global / (k ** (level + 2))))


def compute_adaptive_scale(
    parts: list[set[object]],
    n_global: int,
    level: int,
    k: float,
) -> float:
    """Return a multiplier on the sampling constant for the next level."""
    if not parts:
        return 1.0
    largest = max(len(p) for p in parts)
    target = target_size(n_global, level, k)
    if largest <= 0 or target <= 0:
        return 1.0
    return min(10.0, max(0.1, target / largest))
