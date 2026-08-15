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
JLS construction. (reachq.core.algorithm)

**Pivot.** A vertex chosen by the JLS construction. The construction
adds shortcuts `(pivot, v)` for every v in r_plus(pivot) and
`(v, pivot)` for every v in r_minus(pivot). (reachq.core.algorithm)

**r_plus(v), r_minus(v).** The forward- and backward-reachable sets
of v, respectively. Computed by BFS / CSR-BFS.
(reachq.core.reachability)

**ρ (rho).** The shortcut-set construction's density parameter:
`rho = sqrt(n) / beta`. Used in the paper's bound
`|H| <= O(m*rho + n*rho^2)`. (reachq.core.algorithm)

**ω (omega).** The matrix-multiplication exponent. The paper's bound
uses ω = 3 (standard schoolbook). Faster ω (Strassen, Strassen-like)
tightens the bound. (reachq.research.blas_omega)

**SCC.** Strongly connected component. Computed via Kosaraju's
algorithm. (reachq.core.reachability)

**Trivial condensation.** When all SCCs of a graph have size 1
(typical for DAGs), the condensation step is a no-op and is skipped.
(reachq.core.algorithm, `RefinementConfig.skip_condense` flag)

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

**SP.** Shortest path. (reachq.core.shortest_paths)

**DAG.** Directed acyclic graph. (reachq.core.generators.random_dag)

**SRG.** Strongly regular graph. (reachq.core.generators.petersen_graph
and similar)

**CSR.** Compressed sparse row. A matrix storage format used for
BFS frontier expansion. (reachq.core.bfs)

**Flags.** A dataclass of boolean toggles for each algorithmic
refinement in the shortcut-set construction.
(reachq.core.config.RefinementConfig, exported as reachq.Flags)

**TC-pruning.** Transitive-closure pruning. Adds all-pairs reachability
shortcuts within the pivot's reachable ball when the ball is small
enough that the work is bounded. (reachq.core.tc)

**JLS construction.** The shortcut-set construction of
Jambulapati, Liu, Sidford 2019. (reachq.core.algorithm.jls_shortcut_set)

**CFR construction.** The hopset construction of Cao, Fineman,
Russell 2020. (reachq.core.hopset.cfr_hopset)

**ω (different).** In [reachq.research.blas_omega] the symbol is used for
the matrix-multiplication exponent, while in some literature it
denotes the mixing time of an expander. reachq uses only the former.

**Flags / short-circuit.** The `Flags` dataclass is a switchboard:
each `Flags.<field> = True` enables the corresponding refinement.
The wrapper `build_shortcut_set_for_reachability` reads the flags
and dispatches them to the JLS recursion.

**RefinementConfig.** The canonical name of the `Flags` toggle
structure. `reachq.Flags = reachq.core.config.RefinementConfig`;
the `Flags` alias is preserved for backward compatibility.

**ParallelContext.** A selector for the parallel-execution mode
(`sequential`, `threads`, or `processes`). The two shorthand
helpers `threads(n)` and `processes(n)` live in
`reachq.core.backends.{threads,processes}`. The current
shortcut-set construction is sequential; the `parallel_workers`
parameter is accepted for API symmetry.

**Backend.** The `Backend` Protocol that `ParallelContext`
satisfies. `Backend` is the duck-typed extension point for
third-party dispatchers (Ray, Dask, GraphBLAS). Canonical
location: `reachq.core.backends.Backend`.

**SpanProfiler.** A coarse wall-clock profiler used to estimate
the *empirical* parallel span of a sequential run. Wraps
each phase of the shortcut-set construction in `begin_phase` /
`end_phase`. The sum of phase times is a lower bound on the
true PRAM span. (reachq.core.work_depth.SpanProfiler)

**Snapshot.** A dataclass (`reachq.core.snapshot.Snapshot`) that
captures per-call inputs and outputs. Useful for
regression-testing where you want to compare exact constructor
behaviour across versions.

**Recorder / `record_*`.** The 14 `record_*` helpers in
`reachq.core.work_depth` (`record_bfs`, `record_dijkstra`,
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
