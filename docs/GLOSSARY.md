# Glossary

Terms used in the reachq codebase and docs. Each definition is
self-contained and references the module or function that introduces
the term.

**β (beta) hopbound.** The maximum allowed hop-distance for
reachability queries after adding a shortcut set. A shortcut set
H is *β-hop-bounded* if `parallel_bfs(g, s, H)` reaches every
v in `R+(G, s)` in ≤ β hops.

**Shortcut set.** A set H of additional directed edges added to a
graph G such that `R+(G, s) = R+(G+H, s)` for all s. Used in the
JLS construction. (reachq.shortcut)

**Pivot.** A vertex chosen by the JLS construction. The construction
adds shortcuts `(pivot, v)` for every v in r_plus(pivot) and
`(v, pivot)` for every v in r_minus(pivot). (reachq.shortcut)

**r_plus(v), r_minus(v).** The forward- and backward-reachable sets
of v, respectively. Computed by BFS / CSR-BFS.
(reachq.reachability)

**ρ (rho).** The shortcut-set construction's density parameter:
`rho = sqrt(n) / beta`. Used in the paper's bound
`|H| <= O(m*rho + n*rho^2)`. (reachq.shortcut)

**ω (omega).** The matrix-multiplication exponent. The paper's bound
uses ω = 3 (standard schoolbook). Faster ω (Strassen, Strassen-like)
tightens the bound. Detected at runtime from the BLAS vendor via
`reachq.config.runtime_omega`; re-exported through
`reachq.research.blas_omega` for the research boundary.

**SCC.** Strongly connected component. Computed via Kosaraju's
algorithm. (reachq.reachability)

**Trivial condensation.** When all SCCs of a graph have size 1
(typical for DAGs), the condensation step is a no-op and is skipped.
(reachq.shortcut, `RefinementConfig.skip_condense` flag)

**Hop-bounded BFS.** A BFS that stops after a fixed number of
levels. The β-hopbound-preserving sparsifier uses a depth-limited
BFS to check redundancy. (reachq.research.sparsify_hop)

**Sparsification (reachbound-preserving).** Iteratively removing
shortcuts whose removal does not break the β-hopbound for any
source-target pair. (reachq.research.sparsify_hop.sparsify_hop_bounded)

**StreamingShortcutSet.** Incrementally-maintained shortcut set
under edge insertions. Experimental prototype; no formal
amortised O(log² n) per insertion bound is implemented yet.
(reachq.research.streaming)

**greedy_shortcut_set.** A (1+ε)-approximation algorithm for the
minimum-β-hop-bounded shortcut set. (reachq.research.approximation)

**α-sparsification / β-sparsification.** In the paper: α-sparsification
removes shortcuts that break reachability; β-sparsification
(our name) additionally preserves the hopbound.

**SP.** Shortest path. (reachq.shortest_paths)

**DAG.** Directed acyclic graph. (reachq.generators.random_dag)

**SRG.** Strongly regular graph. (reachq.generators.petersen_graph
and similar)

**CSR.** Compressed sparse row. A matrix storage format used for
BFS frontier expansion. (reachq.bfs)

**Flags.** A dataclass of boolean toggles for each algorithmic
refinement in the shortcut-set construction.
(reachq.config.RefinementConfig; exported at the top level as
`reachq.RefinementConfig`. The legacy `Flags = RefinementConfig`
alias was removed in v0.10.)

**TC-pruning.** Transitive-closure pruning. Adds all-pairs reachability
shortcuts within the pivot's reachable ball when the ball is small
enough that the work is bounded. (reachq.prune)

**JLS construction.** The shortcut-set construction of
Jambulapati, Liu, Sidford 2019. (reachq.shortcut.jls_recursive)

**CFR construction.** The hopset construction of Cao, Fineman,
Russell 2020. (reachq.hopset.cfr_hopset)

**ω (different).** In [reachq.research.blas_omega] the symbol is used for
the matrix-multiplication exponent, while in some literature it
denotes the mixing time of an expander. reachq uses only the former.

**Flags / short-circuit.** The `RefinementConfig` dataclass is a
switchboard: each field enables (or disables) the corresponding
refinement. The wrapper `build_shortcut_set_for_reachability`
reads the flags and dispatches them to the JLS recursion.

**RefinementConfig.** The canonical name of the refinement-toggle
dataclass. `reachq.RefinementConfig = reachq.config.RefinementConfig`.

**ParallelContext.** *Removed in v0.10.* The shortcut-set
construction accepts a `parallel_workers` argument and dispatches
through `_run_pivots(graph, state, pivots, *, parallel, n_workers)`
inside `reachq.shortcut`. There is no public dispatcher class;
the only branch point is the `flags.parallel` boolean and the
`parallel_workers > 1` count.

**Backend.** *Removed in v0.10.* The stub `Backend` Protocol and
the `reachq.accel.dask` / `reachq.accel.ray` / `reachq.accel.graphblas`
dispatchers were self-admitted non-implementations and are gone.
The Cython / Numba / Rust accelerator wrappers under
`reachq.accel.{cython,numba,rust}` remain and are wired into
`reachq.bfs.csr_reachable_forward` when the compiled extension
is available.

**SpanProfiler.** A coarse wall-clock profiler used to estimate
the *empirical* parallel span of a sequential run. Wraps
each phase of the shortcut-set construction in `begin_phase` /
`end_phase`. The sum of phase times is a lower bound on the
true PRAM span. (reachq.work_depth.SpanProfiler)

**Snapshot.** *Removed in v0.10.* The `Snapshot` dataclass had no
internal callers; the diagnostic information it captured is
already exposed via the algorithm-level logging and the
`trace()` context manager in `reachq.trace`.

**Recorder / `record_*`.** The 14 `record_*` helpers in
`reachq.work_depth` (`record_bfs`, `record_dijkstra`,
`record_matrix_multiply`, `record_tc_pruning`, …) that add
asymptotic work/depth estimates to a `WorkDepthAccountant`. Each
accepts `accountant=None` for a no-op.

**sparsify_shortcut_set** vs. **sparsify_hop_bounded.** Two
sparsification post-processing steps. The first removes
shortcuts that are not on the unique β-hop path of any
source-target pair (reachbound-preserving). The second does
the same but additionally preserves the hopbound for every
source-target pair (hopbound-preserving). The latter is the
"β-sparsification" referenced in the paper.
