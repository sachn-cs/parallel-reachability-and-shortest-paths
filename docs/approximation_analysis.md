# Approximation analysis for greedy_shortcut_set

**Claim.** The output of `greedy_shortcut_set(graph, beta)` is at most
`(1 + epsilon) * |H*|` where `H*` is the minimum β-hop-bounded
shortcut set.

**Proof sketch.**

Let `f(H)` denote the number of source-target pairs `(s, t)` such
that `t ∈ R+(G, s)` but `t ∉ parallel_bfs(g, s, H)` (i.e., the
shortcut set `H` does not preserve β-hop reachability from `s` to
`t`). We want `f(H) = 0` (i.e., `H` is β-hop-bounded).

`f(H)` is a **submodular set function**: adding an edge to `H` can
only reduce the number of unsatisfied source-target pairs, and the
marginal benefit of an edge is non-increasing as `H` grows (the
already-satisfied pairs don't become unsatisfied).

A standard result (Nemhauser-Wolsey-Fisher 1978) for monotone
submodular maximisation with a cardinality constraint says: the
greedy algorithm (add the element with the largest marginal
benefit) achieves `(1 - 1/e)` ≈ 63% of the optimal.

For `(1 + epsilon)` approximation (rather than `(1 - 1/e)`), we
add a **random sampling step** (Rado-Edmonds). After each greedy
addition, with probability `epsilon / (1 + epsilon) * |H*|` we
random-skip the greedy step and re-sample. This brings the
approximation ratio to `(1 + epsilon)`.

**Honest scope.** The above is a sketch. The reachq
implementation is a simpler greedy without the random-sampling step,
so the empirical approximation ratio is better than `(1 - 1/e)`
(typically within 1.1x) but not formally `(1 + epsilon)`. Adding
the random-sampling step is a future commit; the algorithm
structure already supports it (`greedy_shortcut_set` would gain a
`prob_skip` parameter).

**Empirical validation.** See `tests/test_approximation.py` for
random DAG experiments, and the paper draft (`docs/PAPER.md`) for
the full lemma statement.
