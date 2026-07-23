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
JLS construction. (reachq.shortcut_set)

**Pivot.** A vertex chosen by the JLS construction. The construction
adds shortcuts `(pivot, v)` for every v in r_plus(pivot) and
`(v, pivot)` for every v in r_minus(pivot). (reachq.shortcut_set)

**r_plus(v), r_minus(v).** The forward- and backward-reachable sets
of v, respectively. Computed by BFS / CSR-BFS.
(reachq.reachability)

**ρ (rho).** The shortcut-set construction's density parameter:
`rho = sqrt(n) / beta`. Used in the paper's bound
`|H| <= O(m*rho + n*rho^2)`. (reachq.shortcut_set)

**ω (omega).** The matrix-multiplication exponent. The paper's bound
uses ω = 3 (standard schoolbook). Faster ω (Strassen, Strassen-like)
tightens the bound. (reachq.blas_omega)

**SCC.** Strongly connected component. Computed via Kosaraju's
algorithm. (reachq.reachability)

**Trivial condensation.** When all SCCs of a graph have size 1
(typical for DAGs), the condensation step is a no-op and is skipped.
(reachq.shortcut_set, `SkipCondense` flag)

**Hop-bounded BFS.** A BFS that stops after a fixed number of
levels. The β-hopbound-preserving sparsifier uses a depth-limited
BFS to check redundancy. (reachq.sparsify_hop)

**Sparsification (reachbound-preserving).** Iteratively removing
shortcuts whose removal does not break the β-hopbound for any
source-target pair. (reachq.sparsify_hop.sparsify_hop_bounded)

**StreamingShortcutSet.** Incrementally-maintained shortcut set
under edge insertions. Amortised O(log^2 n) per insertion.
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
BFS frontier expansion. (reachq.numpy_bfs)

**Flags.** A dataclass of boolean toggles for each algorithmic
refinement in the shortcut-set construction.
(reachq.shortcut_set.Flags)

**TC-pruning.** Transitive-closure pruning. Adds all-pairs reachability
shortcuts within the pivot's reachable ball when the ball is small
enough that the work is bounded. (reachq.transitive_closure)

**JLS construction.** The shortcut-set construction of
Jambulapati, Liu, Sidford 2019. (reachq.shortcut_set.jls_shortcut_set)

**CFR construction.** The hopset construction of Cao, Fineman,
Russell 2020. (reachq.hopset.cfr_hopset)

**ω (different).** In [reachq.blas_omega] the symbol is used for
the matrix-multiplication exponent, while in some literature it
denotes the mixing time of an expander. reachq uses only the former.

**Flags / short-circuit.** The `Flags` dataclass is a switchboard:
each `Flags.<field> = True` enables the corresponding refinement.
The wrapper `build_shortcut_set_for_reachability` reads the flags
and dispatches them to the JLS recursion.
