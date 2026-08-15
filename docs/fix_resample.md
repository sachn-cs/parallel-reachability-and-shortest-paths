# Fix/Resample variant (Paper 1, experimental)

This note describes `reachq/research/fix_resample.py`, an experimental variant
of the JLS shortcut-set construction inspired by Assadi–Yazdanyar's
*Fully Dynamic Algorithms for Coloring Triangle-Free Graphs*
(arXiv:2604.20648).

## Honest scope

Paper 1 targets the **dynamic** setting where the graph changes
between updates. Our codebase is purely **static**, so the
dynamic-update bounds (O(Δ² log n) amortised) do not apply. We
implement the *static analogue* purely as an **experimental baseline**
for comparison with the JLS approach.

## What it does

The Fix/Resample variant:
1. Starts with empty `H` and `F = V` (all vertices uncovered).
2. Greedily picks an uncovered vertex `v`, makes it a pivot
   (adds shortcuts from `v` to `r_plus(v)` and from `r_minus(v)` to
   `v`), and removes `v` and newly-reached vertices from `F`.
3. With small probability per iteration, picks a random pivot already
   in `H` and "resamples" it (no-op structurally, since `H` is a set,
   but represents Paper 1's `Resample` subroutine).
4. Stops when `|F| ≤ threshold * |V|` or `max_iterations` reached.

## Empirical comparison (vs JLS)

`scripts/eval_fix_resample.py` measures both algorithms on:

- Named fixtures: Petersen, Paley(13), Shrikhande, Hamming(2,4),
  Hamming(3,3).
- Random DAGs at n ∈ {50, 100}, density ∈ {0.1, 0.3}.

Across 9/9 cases (so far; see
[`tests/test_fix_resample.py`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/tests/test_fix_resample.py)
for the full parameter grid):

| metric | Fix/Resample | JLS |
|---|---|---|
| `|H|` (smaller is better) | **16% of JLS** | 100% |
| Empirical hopbound (smaller is better) | ~3 | **~1** |

The Fix/Resample variant produces smaller shortcut sets but with a
looser hopbound. JLS oversamples and gets a tighter hopbound.

## Trade-off interpretation

The trade-off is fundamental:
- Pick **Fix/Resample** if `|H|` matters more than query time (e.g.,
  offline preprocessing, storage-constrained settings).
- Pick **JLS** if hopbound matters more than `|H|` (e.g., online
  parallel reachability queries).

## What this experiment does NOT prove

- We do NOT claim Fix/Resample beats JLS — JLS wins on hopbound.
- We do NOT claim any algorithmic improvement to the paper — both
  algorithms are static analogues of known techniques.
- We do NOT claim dynamic-update applicability — the codebase is
  static.

The contribution is *empirical*: documenting the trade-off between
the two approaches on standard fixtures.