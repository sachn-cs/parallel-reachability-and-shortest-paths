"""reachq: graph reachability, queryable.

## How to read this code

reachq is a typed Python package. Public API lives in `__all__`
(below) and is re-exported from each submodule. Private helpers
are not in `__all__` and should not be imported from outside the
package.

The package is organised into two layers:

  - ``reachq.core.*`` (always imported): graph primitives, reachability,
    shortcut-set construction, hopset construction, work-depth
    accounting, serialisation.
  - ``reachq.research.*`` (opt-in): refinements and new algorithms that
    the paper does not include. These are imported directly; no
    runtime activation is required.

The public API is in this `__init__.py`. The algorithms module
(``reachq.core.algorithm``) is the most important; ``reachq.core.reachability``
holds the BFS implementation; ``reachq.core.graph`` is the Digraph base
class. The `flags` parameter on the public functions is a
``RefinementConfig`` dataclass of boolean toggles; the
`parallel_workers` parameter is the thread pool size; and
``reachq.core.config.get_logger(name)`` gives you a per-module
logger.

The recommended first test after install:

    >>> from reachq.core.graph import Digraph
    >>> from reachq.core.algorithm import build_shortcut_set_for_reachability
    >>> g = Digraph(); g.add_edge(0, 1); g.add_edge(1, 2)
    >>> H, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    >>> isinstance(H, set)
    True
    >>> beta > 0
    True

This package implements the algorithms from:
"Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
Near-linear Work and Sub-square-root Depth"
by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak (2026).
"""

__version__ = "7.0.0"

from reachq.core import invariants
from reachq.core.generators import (
    cycle_graph,
    dense_graph,
    erdos_renyi_digraph,
    graph_with_sccs,
    grid_graph,
    hamming_graph,
    layered_dag,
    paley_graph,
    path_graph,
    petersen_graph,
    random_dag,
    shrikhande_graph,
    weighted_dense_graph,
    weighted_path_graph,
    weighted_random_dag,
)
from reachq.core.graph import Digraph, WeightedDigraph
from reachq.core.hopset import (
    build_hopset_for_sssp,
    cfr_hopset,
    cfr_with_truncsssp_pruning,
)
from reachq.core.reachability import (
    bfs_reachability,
    compute_ancestors,
    compute_bridges,
    compute_descendants,
    compute_r_ball,
    compute_r_minus,
    compute_r_plus,
    parallel_bfs,
    reverse_bfs_reachability,
    strongly_connected_components,
    topological_sort,
)
from reachq.core.io.json import (
    load,
    dump,
    weighted_load,
    weighted_dump,
)
from reachq.core.algorithm import (
    build_shortcut_set_for_reachability,
    jls_shortcut_set,
    jls_with_tc_pruning,
)
from reachq.core.config import RefinementConfig
from reachq.core.shortest_paths import (
    astar,
    compute_d_ancestors,
    compute_d_ball,
    compute_d_descendants,
    dijkstra,
    shortest_path,
    shortest_path_hopbound,
    shortest_path_tree,
    truncated_dijkstra,
)
from reachq.core.tc import (
    transitive_closure_brute_force,
    transitive_closure_matrix,
    transitive_closure_on_subset,
)
from reachq.core.work_depth import WorkDepthAccountant

Flags = RefinementConfig

__all__ = [
    "Digraph",
    "Flags",
    "RefinementConfig",
    "WeightedDigraph",
    "WorkDepthAccountant",
    "astar",
    "bfs_reachability",
    "build_hopset_for_sssp",
    "build_shortcut_set_for_reachability",
    "cfr_hopset",
    "cfr_with_truncsssp_pruning",
    "compute_ancestors",
    "compute_bridges",
    "compute_d_ancestors",
    "compute_d_ball",
    "compute_d_descendants",
    "compute_descendants",
    "compute_r_ball",
    "compute_r_minus",
    "compute_r_plus",
    "cycle_graph",
    "dense_graph",
    "load",
    "dump",
    "dijkstra",
    "erdos_renyi_digraph",
    "graph_with_sccs",
    "grid_graph",
    "hamming_graph",
    "invariants",
    "jls_shortcut_set",
    "jls_with_tc_pruning",
    "layered_dag",
    "paley_graph",
    "parallel_bfs",
    "path_graph",
    "petersen_graph",
    "random_dag",
    "shrikhande_graph",
    "reverse_bfs_reachability",
    "shortest_path",
    "shortest_path_hopbound",
    "shortest_path_tree",
    "strongly_connected_components",
    "topological_sort",
    "transitive_closure_brute_force",
    "transitive_closure_matrix",
    "transitive_closure_on_subset",
    "truncated_dijkstra",
    "weighted_dense_graph",
    "weighted_load",
    "weighted_dump",
    "weighted_path_graph",
    "weighted_random_dag",
]
