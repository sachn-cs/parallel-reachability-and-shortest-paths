"""Auto-tuner for RefinementConfig.

Selects optimal refinement settings based on graph properties
(density, size, structure). Future work: bandit-based online tuning.
"""

from __future__ import annotations

from reachq.core.config import RefinementConfig
from reachq.core.graph import Digraph


def auto_tune(graph: Digraph) -> RefinementConfig:
    """Select RefinementConfig based on graph properties.

    Heuristic: dense graphs benefit from label compression and
    skip_condense; sparse graphs benefit from hop-bounded BFS
    and TC pruning.
    """
    n = graph.num_vertices()
    m = graph.num_edges()
    rho = m / (n * n) if n > 0 else 0.0

    # Dense graphs: disable TC pruning (too expensive), enable label compress.
    if rho > 0.01:
        return RefinementConfig(
            enable_tc_pruning=False,
            label_compress=True,
            hop_bounded_bfs=True,
        )
    # Sparse graphs: enable everything.
    return RefinementConfig()
