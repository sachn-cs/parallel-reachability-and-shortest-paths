"""Parallel reachability and shortest paths on non-sparse digraphs.

This package implements the algorithms from:
"Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
Near-linear Work and Sub-square-root Depth"
by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak (2026).
"""

__version__ = "0.1.0"

from prspnsd.graph import Digraph, WeightedDigraph
from prspnsd.reachability import (
    bfs_reachability,
    reverse_bfs_reachability,
    compute_r_plus,
    compute_r_minus,
    compute_r_ball,
    compute_ancestors,
    compute_descendants,
    compute_bridges,
    parallel_bfs,
    strongly_connected_components,
    topological_sort,
)
from prspnsd.shortest_paths import (
    dijkstra,
    astar,
    truncated_dijkstra,
    compute_d_descendants,
    compute_d_ancestors,
    compute_d_ball,
    shortest_path_hopbound,
    shortest_path_tree,
)
from prspnsd.transitive_closure import (
    transitive_closure_brute_force,
    transitive_closure_matrix,
    transitive_closure_on_subset,
)
from prspnsd.shortcut_set import (
    jls_shortcut_set,
    jls_with_tc_pruning,
    build_shortcut_set_for_reachability,
)
from prspnsd.hopset import (
    cfr_hopset,
    cfr_with_truncsssp_pruning,
    build_hopset_for_sssp,
)
from prspnsd.generators import (
    cycle_graph,
    dense_graph,
    erdos_renyi_digraph,
    graph_with_sccs,
    grid_graph,
    layered_dag,
    path_graph,
    random_dag,
    weighted_dense_graph,
    weighted_path_graph,
    weighted_random_dag,
)
from prspnsd.serialization import (
    digraph_from_json,
    digraph_to_json,
    weighted_digraph_from_json,
    weighted_digraph_to_json,
)
from prspnsd.work_depth import WorkDepthAccountant
from prspnsd import invariants

__all__ = [
    "Digraph",
    "WeightedDigraph",
    "bfs_reachability",
    "reverse_bfs_reachability",
    "compute_r_plus",
    "compute_r_minus",
    "compute_r_ball",
    "compute_ancestors",
    "compute_descendants",
    "compute_bridges",
    "parallel_bfs",
    "strongly_connected_components",
    "topological_sort",
    "dijkstra",
    "astar",
    "truncated_dijkstra",
    "compute_d_descendants",
    "compute_d_ancestors",
    "compute_d_ball",
    "shortest_path_hopbound",
    "shortest_path_tree",
    "transitive_closure_brute_force",
    "transitive_closure_matrix",
    "transitive_closure_on_subset",
    "jls_shortcut_set",
    "jls_with_tc_pruning",
    "build_shortcut_set_for_reachability",
    "cfr_hopset",
    "cfr_with_truncsssp_pruning",
    "build_hopset_for_sssp",
    "cycle_graph",
    "dense_graph",
    "erdos_renyi_digraph",
    "graph_with_sccs",
    "grid_graph",
    "layered_dag",
    "path_graph",
    "random_dag",
    "weighted_dense_graph",
    "weighted_path_graph",
    "weighted_random_dag",
    "digraph_from_json",
    "digraph_to_json",
    "weighted_digraph_from_json",
    "weighted_digraph_to_json",
    "WorkDepthAccountant",
    "invariants",
]
