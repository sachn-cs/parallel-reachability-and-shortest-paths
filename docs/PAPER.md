# reachq: parallel reachability with β-hopbound-preserving shortcut sets

> **Historical draft.** This document is a unified paper draft kept
> for the record. Section 5.1's `StreamingShortcutSet` claim and
> Section 5.2's `greedy_shortcut_set` claim do not match the current
> implementation; see [`docs/limitations.md`](limitations.md) for
> the current state. The current test count is in CHANGELOG.md; do
> not hard-code counts here.

This document is the unified paper draft. It consolidates the
previous `paper_innovations.md`, `paper_refinements.md`, and
`paper_contribution.md` into a single canonical source. The
relationship to the cited papers is in [`docs/INSPIRED_BY.md`](INSPIRED_BY.md).

## 1. Background

The JLS shortcut-set construction of Jambulapati, Liu, Sidford
[JLS19] is the algorithmic basis of Theorem 2 in the parallel
reachability paper of Ashvinkumar et al. [2026]. The construction
samples a set of "pivots" from each connected component and adds
shortcuts from each pivot to all vertices it can reach in the
underlying graph. The theorem's size bound is:

    |H| <= O(m * rho + n * rho^2)

where `rho = sqrt(n) / beta` and `beta = (n^omega / m)^(1 / (2 * omega - 2))`.

The construction is **over-sampled** in practice. On every standard
graph class we tested, the JLS output is dominated by redundant
shortcuts that the underlying graph already provides.

## 2. Two contributions layered on top

### 2.1. Sparsification with hopbound preservation

A shortcut `(u, v)` is *redundant* iff `v` is reachable from `u`
in `G + (H \ {(u, v)})` *within the β-hopbound*. A naive
sparsification (removing any redundant shortcut by **unbounded BFS**)
preserves reachability but **violates the β-hopbound guarantee** — the
sparsified set has a strictly larger empirical diameter.

**Theorem (β-hopbound-preserving sparsification).** The
`reachq.research.sparsify_hop.sparsify_hop_bounded(graph, H, beta)` function
preserves both:
1. `R+(G, s) = R+(G+H, s)` for all s, and
2. the empirical diameter of `G + H` is bounded by `beta`.

The result: the JLS output can be reduced by 50-100% on dense
random graphs while preserving both invariants.

### 2.2. Adaptive β from graph structure

The paper's `beta = (n^omega / m)^(1 / (2 * omega - 2))` is a
worst-case bound based on edge density. `reachq.research.adaptive_beta.adaptive_beta`
computes a graph-aware β from the empirical eccentricity of a sample
of source vertices, scaled by a safety factor. The two estimates
diverge on dense graphs and converge on sparse ones.

## 3. Five engineering refinements

These are the post-processing refinements (Innovation #3-#7 from the
paper draft). All default to on, all individually toggleable.

1. **Trivial-condensation fast path.** When the input graph is a DAG
   (all SCCs of size 1), the condensation step is skipped
   (`RefinementConfig.skip_condense`).
2. **Degree-ordered pivot iteration.** Pivots are processed in
   ascending out-degree order, so cheap BFSes finish first
   (`RefinementConfig.degree_ordered_pivots`).
3. **Label compression.** Labels are stored as `frozenset[int]`
   pivot IDs instead of `set[str]`, reducing memory and hashing cost
   (`RefinementConfig.label_compress`).
4. **Skip-trivial-partition guard.** When the partition has only one
   part, the recursion cannot shrink, so we return immediately
   (`RefinementConfig.skip_trivial_part`).
5. **Hop-bounded BFS in the pivot loop.** The pivot BFS is bounded
   at the wrapper's β estimate
   (`RefinementConfig.hop_bounded_bfs`).

## 4. Bound gap analysis

We constructed four graph classes (random DAG, layered DAG, long
path, chain of stars) and measured the JLS output against the paper's
bound. **Across all 12 tested constructions, the JLS essential
shortcut set (after `sparsify_hop_bounded`) has |H| ≈ 0** — the bound
is uniformly loose on standard graph classes. See
`scripts/eval_lower_bound.py` and `results/lower_bound.csv`.

## 5. Two new algorithms (reachq.research.*)

Both are distinct from the cited papers.

### 5.1. StreamingShortcutSet

Maintains a shortcut set under edge insertions. **Experimental
prototype; no formal bound yet** (the design intent is amortised
O(log² n) per insertion, but the current implementation does not
achieve it). See [`docs/streaming_proof.md`](streaming_proof.md)
for the honest sketch. Distinct from the paper's batch construction.
(`reachq.research.streaming.StreamingShortcutSet`)

### 5.2. greedy_shortcut_set

A (1+ε)-approximation algorithm. Produces a shortcut set of size at
most (1+ε) times the optimal. Polynomial time in n and 1/ε.
(`reachq.research.approximation.greedy_shortcut_set`)

## 6. Reproducibility

```bash
python -m pytest tests/ -q
# current test count is in CHANGELOG.md; do not hard-code here
python scripts/eval_lower_bound.py
# results in results/lower_bound.csv
```

## 7. References

- [JLS19] Jambulapati, Liu, Sidford. *Parallel Reachability via
  Shortcut Sets.* 2019.
- Ashvinkumar et al. *Parallel Reachability and Shortest Paths on
  Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth.*
  arXiv:2605.03892, 2026.
