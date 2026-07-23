"""Parallel reachability and shortest paths on non-sparse digraphs.

This package implements the algorithms from:
"Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
Near-linear Work and Sub-square-root Depth"
by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak (2026).
"""

__version__ = "0.4.0"

from prspnsd import invariants
from prspnsd.generators import (
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
from prspnsd.graph import Digraph, WeightedDigraph
from prspnsd.hopset import (
    build_hopset_for_sssp,
    cfr_hopset,
    cfr_with_truncsssp_pruning,
)
from prspnsd.reachability import (
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
from prspnsd.serialization import (
    digraph_from_json,
    digraph_to_json,
    weighted_digraph_from_json,
    weighted_digraph_to_json,
)
from prspnsd.shortcut_set import (
    Flags,
    build_shortcut_set_for_reachability,
    jls_shortcut_set,
    jls_with_tc_pruning,
)
from prspnsd.shortest_paths import (
    astar,
    compute_d_ancestors,
    compute_d_ball,
    compute_d_descendants,
    dijkstra,
    shortest_path_hopbound,
    shortest_path_tree,
    truncated_dijkstra,
)
from prspnsd.transitive_closure import (
    transitive_closure_brute_force,
    transitive_closure_matrix,
    transitive_closure_on_subset,
)
from prspnsd.work_depth import WorkDepthAccountant

__all__ = [
    "Digraph",
    "Flags",
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
    "digraph_from_json",
    "digraph_to_json",
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
    "shortest_path_hopbound",
    "shortest_path_tree",
    "strongly_connected_components",
    "topological_sort",
    "transitive_closure_brute_force",
    "transitive_closure_matrix",
    "transitive_closure_on_subset",
    "truncated_dijkstra",
    "weighted_dense_graph",
    "weighted_digraph_from_json",
    "weighted_digraph_to_json",
    "weighted_path_graph",
    "weighted_random_dag",
]
