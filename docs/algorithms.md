# Algorithms

This document describes the core algorithms implemented in reachq and their
relationship to the paper.

## Reachability Primitives

### BFS Reachability

`bfs_reachability(graph, source)` computes all vertices reachable from `source`
using standard breadth-first search. Time: O(m). Space: O(n).

### Reverse BFS Reachability

`reverse_bfs_reachability(graph, target)` computes all vertices that can reach
`target` by running BFS on the reversed graph. Time: O(m).

### Strongly Connected Components

`strongly_connected_components(graph)` uses Kosaraju's algorithm to decompose a
digraph into its SCCs. Time: O(n + m).

### Parallel BFS with Shortcuts

`parallel_bfs(graph, source, shortcuts)` performs BFS on G ∪ H where H is a
shortcut set. In the paper this is a parallel primitive; our implementation is
sequential. Shortcut edges are indexed by source vertex for O(1) lookup during
BFS traversal. The span bounds are NOT DETERMINED.

## Shortest-Path Primitives

### Dijkstra

`dijkstra(graph, source)` computes exact single-source shortest paths on a
weighted digraph with non-negative integer weights. Time: O(m log n).

### Truncated Dijkstra

`truncated_dijkstra(graph, source, max_distance)` computes distances from
`source` truncated at `max_distance`. Used by TruncSSSP-Pruning.

### Hop-Bounded Shortest Paths

`shortest_path_hopbound(graph, hopset, source, max_hops)` computes shortest
paths using at most `max_hops` hops in G ∪ H. Hopset edges are indexed by
source vertex for O(1) lookup. This simulates the hop-bounded SSSP primitive
from the paper.

## Transitive Closure

### Brute Force

`transitive_closure_brute_force(graph)` runs BFS from every vertex. Time:
O(n * m).

### Matrix Multiplication

`transitive_closure_matrix(graph)` uses repeated Boolean squaring with
`numpy.matmul`. Time: O(n^ω) where ω is the fast matrix multiplication
exponent. We use standard BLAS (effectively ω = 3 for most sizes).

### Subset Transitive Closure

`transitive_closure_on_subset(graph, subset)` computes TC on an induced
subgraph. Used by TC-Pruning.

## Shortcut Set Construction

### JLS Shortcut Set (Baseline)

`jls_shortcut_set(graph, k, max_level, n_global)` implements the Jambulapati,
Liu, Sidford [JLS19] shortcut set algorithm (Section 4.1, Proposition 4.1).

Algorithm outline:
1. Sample pivots independently with probability proportional to k^{level}.
2. For each pivot p, add shortcuts from all ancestors of p to p and from p
to all descendants of p.
3. Label every vertex by its pivot relationships.
4. Partition vertices into equivalence classes by exact label equality.
5. Recurse on each part with level+1.

### JLS with TC-Pruning (Theorem 2)

`jls_with_tc_pruning(graph, k, rho, max_level, n_global)` adds TC-Pruning to
the baseline JLS algorithm (Section 4.2, Theorem 5).

The key additional step: for each pivot p, if |R(G, p)| ≤ (k^2 log^2 n) ρ^2,
add all edges in TC(G[R(G, p)]) to the shortcut set.

This pruning is what achieves the improved work bound: O~(m + n ρ^{2ω-2}).

### High-Level Wrapper

`build_shortcut_set_for_reachability(graph, omega, random_seed)` handles SCC
contraction automatically, then calls `jls_with_tc_pruning` on the condensed
DAG. Returns (shortcut_set, beta) where beta is the target hopbound.

#### Refinement flags

The wrapper accepts a `flags: RefinementConfig` argument (also
re-exported as `reachq.Flags`) that toggles the post-processing
refinements described in `docs/PAPER.md`:

| Flag | Effect |
|---|---|
| `skip_condense` | Skip the SCC-contraction step. Faster on dense graphs; unsafe on graphs with cycles. |
| `skip_trivial_part` | Skip the trivial singleton parts at the recursion base. |
| `degree_ordered_pivots` | Order pivots by degree (highest first). |
| `label_compress` | Compress labels to consecutive integers before recursion. |
| `hop_bounded_bfs` | Use a hop-bounded BFS kernel instead of the full BFS (currently no-op; reserved for the accel path). |
| `enable_tc_pruning` | Apply TC-Pruning (Theorem 2's improvement). |

The default `RefinementConfig` enables all of these. Use
`RefinementConfig()` to get the baseline JLS construction; use
`auto_tune(graph)` to get a density-aware preset.

#### `parallel_workers` parameter

The wrapper exposes a `parallel_workers: int = 1` argument that is
accepted for API symmetry with the future multi-process path. The
current implementation is sequential; the parameter is logged-and-
ignored when set > 1 on the process path. The thread path is
available via `ParallelContext` but is not wired into the
shortcut-set construction because the per-pivot BFS is CPU-bound
and GIL-bound.

## Hopset Construction

### CFR Hopset (Baseline)

`cfr_hopset(graph, k, epsilon, max_level, n_global)` implements the Cao,
Fineman, Russell [CFR20] hopset algorithm (reconstructed from Section 6.1).

Algorithm outline:
1. Sample pivots with probability proportional to k^{level}.
2. For each pivot p, compute a distance scale d = (1+ε)^{level} * O(log n).
3. Add hopset edges from d-ancestors of p to p and from p to d-descendants
of p, weighted by shortest-path distances.
4. Label and partition analogously to JLS.
5. Recurse on each part.

### CFR with TruncSSSP-Pruning (Theorem 4)

`cfr_with_truncsssp_pruning(graph, k, epsilon, rho, max_level, n_global)` adds
TruncSSSP-Pruning to the baseline CFR algorithm (Section 6.3).

The key additional step: for each pivot p, if |R_d(G, p)| ≤ (k^2 log^2 n) ρ^2,
compute all-pairs truncated shortest paths within R_d(G, p) and add them to the
hopset.

This replaces the transitive closure used in TC-Pruning with truncated SSSP,
preserving distances up to (1+ε) distortion.

**ASSUMPTION**: The exact distance scales, TruncSSSP-Pruning thresholds, and
some constants were partially truncated in the extracted paper text. We
reconstructed them from analogy to the shortcut set. See `hopset.py` for
inline `ASSUMPTION` markers.

### High-Level Wrapper

`build_hopset_for_sssp(graph, epsilon, random_seed)` handles SCC contraction
automatically, then calls `cfr_with_truncsssp_pruning` on the condensed DAG.
Returns (hopset, beta) where beta is the target hopbound.

The hopset wrapper also accepts a `parallel_workers: int = 1`
argument with the same semantics as the shortcut-set wrapper:
accepted for API symmetry, currently sequential.

## Parameter Selection

Both high-level wrappers automatically select:
- `k = max(2, log_2 n)`
- `rho = max(1, sqrt(n) / beta)` capped at `sqrt(n)`
- `max_level = O(log_k n)`

The target hopbound beta is derived from the paper's density-dependent
formulas:
- Shortcut sets: β = (n^ω / m)^{1/(2ω-2)}
- Hopsets: β = (n^3 / m)^{1/4}

These formulas reflect the paper's tradeoff between shortcut/hopset size and
the hopbound achieved.
