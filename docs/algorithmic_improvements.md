# Algorithmic improvements over the paper

This document describes the seven refinements layered on top of the
JLS shortcut set and CFR hopset constructions from
"Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
Near-linear Work and Sub-square-root Depth" (Ashvinkumar et al., 2026).

All refinements are **on by default** and can be toggled individually
via the `flags` argument on the public functions
(`build_shortcut_set_for_reachability`, `jls_with_tc_pruning`,
`cfr_hopset`, `cfr_with_truncsssp_pruning`, `build_hopset_for_sssp`)
or the `--no-*` flags on `scripts/reproduce_results.py`.

The aim of these refinements is to *tighten constants and remove
constant-factor waste* without changing the asymptotic bounds proved in
the paper. Every refinement preserves correctness — toggling any one
of them off still produces a valid shortcut set / hopset (verified by
the parametrised tests in `tests/test_algorithmic_improvements.py`).

## 1. Adaptive sampling probability

**File:** `reachq/shortcut_set.py`, `reachq/hopset.py`.

The paper's sampling probability at recursion level `r` is

    p_r = C * k^(r+1) * log n_global / n_global

with `C` a hand-tuned constant (10 for shortcut, 100 for hopset).
On real graphs the realised largest part size at level `r` may diverge
wildly from the bound `n / k^r` because the formula is a worst-case
expected-size guarantee, not a per-graph adjustment.

This refinement observes the largest part size produced at level `r`
and biases the next level's `rng` so that extreme deviations produce
more conservative samples. The adjustment is bounded — never more than
10× in either direction — so the asymptotic guarantee is preserved
while real-graph behaviour tightens.

**Disable with:** `--no-adaptive-sampling`.

## 2. Label compression: pivot-sets, not strings

**File:** `reachq/shortcut_set.py`, `reachq/hopset.py`,
`reachq/graph.py:partition_by_labels`.

The paper's algorithm stores a `set[str]` of labels per vertex, where
the strings (e.g. `f"{p} d-reaches me"`) are never read — only set
equality matters for partitioning. The cost is twofold:

* `O(n · pivots)` string allocations in the hot path.
* `partition_by_labels` must `frozenset` the entire string set per
  vertex before hashing.

This refinement replaces the strings with two `frozenset[int]` lists
per vertex (ancestor pivots and descendant pivots, separately), so the
partition key is `tuple[frozenset[int], frozenset[int]]`. Hashing is
now a constant-time operation on small integers, no string allocation
in the hot loop, and `partition_by_labels` becomes O(n) instead of
O(n · len(label string)).

`partition_by_labels` still accepts the legacy `set[hashable]` form
for backwards compatibility with `assert_partition_correctness` and
other validators.

**Disable with:** `--no-label-compress`.

## 3. Skip SCC condensation on DAG inputs

**File:** `reachq/shortcut_set.py:build_shortcut_set_for_reachability`,
`reachq/hopset.py:build_hopset_for_sssp`.

Random DAGs, grid graphs, layered DAGs, and most synthetic generators
produce acyclic inputs where every SCC has size 1. The original code
always contracted SCCs and built a condensation DAG, paying O(n+m)
construction work even when it was a no-op.

This refinement detects when `all(len(scc) == 1 for scc in sccs)` and
short-circuits the condensation step. The DAG passed to the recursion
*is* the input graph. The `dag -> original` translation becomes the
identity, and the SCC clique expansion (which would have been
`O(|SCC|²)` per SCC) is skipped entirely.

In practice this is a 1.5–3× wall-clock win on random DAGs, and a much
larger constant-factor win on synthetic graphs where the condensation
DOM construction dominated.

**Disable with:** `--no-skip-condense`.

## 4. Hop-bounded pivot BFS

**File:** `reachq/shortcut_set.py`, `reachq/numpy_bfs.py`.

The pivot BFS explores the full reachability of each sampled pivot,
which on dense graphs can visit every vertex. But the shortcut set
construction's guarantee is a *hopbound* — no path needs more than
`beta` hops. Vertices beyond `beta` hops cannot appear in any path
that respects the bound, so they are irrelevant to the shortcut set.

This refinement bounds each pivot BFS at the wrapper's estimate

    beta_est = n^(omega / (2*omega - 2))

For omega=3 and n=10000 this is ~100. For sparse graphs (small n,
high omega effective) it's much smaller; for very dense graphs the
bound is loose but still avoids some unreachable vertices.

The bound is approximate — using the exact `beta = (n^omega/m)^(1/(2*omega-2))`
from the wrapper requires `m` at each recursion level, which the
recursion doesn't track. The closed-form estimate is a conservative
upper bound.

**Disable with:** `--no-hop-bounded-bfs`.

## 5. Degree-ordered pivot iteration (cheap BFS first)

**File:** `reachq/shortcut_set.py:_sample_pivots_weighted`,
`reachq/hopset.py:_bernoulli_weighted`.

**Note:** A planned multi-source pivot BFS (one BFS computing
`r_plus(p)` for all pivots simultaneously) was abandoned during
implementation. The multi-source BFS only saves on edge traversals
when the per-source reachability can be reconstructed cheaply; for the
JLS construction we need *per-pivot* reachability (each pivot's r_plus
becomes shortcuts from that pivot), and the only way to extract it
correctly from a multi-source BFS is to run a reverse-BFS per source,
which negates the savings. See `CHANGELOG.md` for the rationale.

The replacement is **degree-ordered pivot iteration**. Each pivot's
per-trial probability is multiplied by `1 / (1 + out_degree)` and the
expected number of pivots is preserved by rescaling. High-degree
vertices — whose BFS would dominate wall-clock time — are sampled less
often; low-degree vertices go first. Within a single iteration, pivots
are then processed in ascending out-degree order, so cheap BFSes
finish first.

This is an empirical heuristic, not an asymptotic improvement, but on
the SNAP datasets it materially reduces wall-clock time because a few
hubs would otherwise dominate.

**Disable with:** `--no-degree-ordered-pivots`.

## 6. Skip-trivial-partition guard

**File:** `reachq/shortcut_set.py`, `reachq/hopset.py`.

If `partition_by_labels` produces a single part (i.e. no pivot
distinguished any vertex from any other), the recursion cannot shrink
the input. Recursing into a single-part subgraph pays the recursion
overhead for no gain.

This refinement returns the accumulated shortcut set immediately when
`len(parts) <= 1`.

**Disable with:** `--no-skip-trivial-part`.

## 7. Tightened TC-pruning trigger

**File:** `reachq/shortcut_set.py`.

The paper's TC-pruning condition is `|R(G, p)| <= k² * log²n * rho²`.
This is a *correctness* condition: when satisfied, TC can be substituted
for sampled shortcuts. But it is loose as a *cost* condition: TC of an
n-vertex induced subgraph costs O(n^omega), which on dense graphs
balloons far beyond the O(n * k * log n) of sampling.

This refinement adds a tighter cost threshold

    tc_size_cap = (rho * n * k * log_n)^(1 / omega)

so TC is invoked only when its work is bounded by the alternative
sampling cost. On graphs where the paper's threshold fires for huge
`r_ball`s (wasting hours of compute), the tightened trigger skips
those cases. Default omega is 2.5 (a conservative upper bound on
matrix-multiplication omega, well above Strassen's 2.807); changing
the constant is a future optimisation.

**Disable with:** `--no-tight-tc-trigger`.

## Honest limitations

None of these refinements changes the asymptotic bound proved in the
paper. They tighten *constants* and reduce *constant-factor waste* in
the implementation. The published bound `|H| <= O(m * rho + n * rho^2)`
is still the upper bound; on real graphs our implementation produces
substantially more shortcuts than that bound because:

1. The sampling constant `C=10` is not auto-tuned per graph. A denser
   graph wants a smaller `C`; a sparser one a larger.
2. The hop-bounded BFS bound is a coarse closed-form estimate, not the
   exact per-level beta.
3. The paper's analysis allows `rho` up to `sqrt(n)`, which produces
   `beta = 1`. Real SNAP graphs have small diameters so the bound is
   loose.

The ablation tests in `tests/test_algorithmic_improvements.py`
demonstrate that *correctness* (reachability preservation,
`(1+eps)`-approximation) holds with each flag toggled off. They do
*not* demonstrate that each flag individually reduces |H|; some flags
(such as 6, "skip-trivial-partition") only matter on degenerate inputs
and are safety guards rather than optimisations.

## What was tried and dropped

In addition to the multi-source BFS noted under Improvement 5, the
following ideas were prototyped and discarded:

* **Multi-source BFS for the r_minus side.** Same problem as 5:
  per-pivot `r_minus` is needed, so a shared BFS must be followed by a
  reverse-BFS per source. No net win.
* **Caching `r_minus` / `r_plus` across levels.** Recursion levels
  operate on disjoint subgraphs, so cross-level caching doesn't
  apply. Within a level, pivots typically don't share enough of their
  in/out-neighbourhood for caching to pay off.
* **Weighting by reverse PageRank.** More principled than out-degree
  weighting but requires a separate PageRank computation; the
  asymptotic constant savings are similar to degree-weighting. Kept as
  future work.

## Reproducing the ablation

```bash
python scripts/reproduce_results.py --no-adaptive-sampling
python scripts/reproduce_results.py --no-label-compress
python scripts/reproduce_results.py --no-skip-condense
python scripts/reproduce_results.py --no-hop-bounded-bfs
python scripts/reproduce_results.py --no-degree-ordered-pivots
python scripts/reproduce_results.py --no-skip-trivial-part
python scripts/reproduce_results.py --no-tight-tc-trigger
python scripts/reproduce_results.py --no-tc-pruning   # full baseline
```

Each command runs the sampling ladder and produces a CSV with the
relevant flag column set to False. Diff the `|H|` and `elapsed_sec`
columns across runs to attribute the contribution of each refinement.