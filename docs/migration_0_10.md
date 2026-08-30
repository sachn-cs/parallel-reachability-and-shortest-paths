# Migration to v0.10.0

v0.10.0 is a hard-cut refactor for clarity, correctness, and
performance. Every API change in this release is a breaking
change; no compat shims are retained.

The test suite pins every invariant below in
`tests/test_regression_invariants.py`.

## Architecture

* `reachq.core.algorithm/` is gone. The JLS shortcut-set
  construction lives in `reachq.shortcut`; the per-call
  process-pool dispatcher lives in `reachq.shortcut_parallel`.
* `reachq.core.tc` is renamed `reachq.closure`.
* `reachq.core.metrics` is deleted (no callers).
* `reachq.core.tuner` is deleted (`auto_tune` had no callers).
* `reachq.core.predictor` is renamed `reachq.core.predict`.
* `reachq.core.backends` is deleted. The dispatcher is
  `reachq.shortcut_parallel.ParallelExecutor`.

## SSSP and reachability contracts

* Unreachable vertices are *absent* from `dijkstra`, `truncated_dijkstra`,
  `astar`, `shortest_path_hopbound`, and `shortest_path_tree`.
* `shortest_path` returns `UNREACHABLE` for an unreachable target.
* `dijkstra` raises `ReachqGraphError` for an unknown source;
  `truncated_dijkstra` raises `ValueError` for a negative bound.
* All heap tuples include a per-call monotonic counter, so vertex
  keys like `object()` or `frozenset` work without `TypeError`.

## Hopset weight correctness

* The hopset is computed directly on the original weighted graph.
  The previous weighted SCC condensation mapping that emitted
  underweighted shortcuts is removed.
* `transitive_closure_matrix` is gone. Use `transitive_closure`
  on the Boolean semiring.
* `TransitiveClosureBudgetError` raises when the configured
  `max_pairs` budget is exceeded; pass `budget_strict=False` to
  return the partial result instead.

## Graph model

* Insertion order is the canonical vertex index.
  `graph.vertices()` returns a `tuple` in insertion order.
* `Digraph.__contains__`, `__iter__`, `__len__` are supported.
* `WeightedDigraph.add_edge` rejects non-`int` weights (including
  `bool`, `float`, `NaN`, `inf`) and negative `int` weights.

## Removal of compat shims

* The legacy `Flags = RefinementConfig` alias is gone.
* `jls_shortcut_set`, `cfr_hopset` are no longer exported from the
  top-level package; use the `*_pruning` / `*_for_sssp` entry
  points.
* `compute_r_plus`, `compute_r_minus`, `compute_r_ball` are gone;
  use `bfs_reachability` and `reverse_bfs_reachability` directly.
* `paper_bound_const` is renamed `upper_bound_paper(n, m)`.
* `predict_omega` no longer takes a graph argument.

## New or replaced tests

* `tests/test_regression_invariants.py` is the new regression
  test for v0.10 invariants.
* `tests/test_predictor.py` exercises the renamed predictors.
* `tests/test_work_depth.py` is slimmed to the dataclasses
  and theoretical-bound functions (the 11 unused `record_*`
  helpers are gone).

## Build / CLI

* `python -m scripts.cli` is replaced by `python -m reachq.cli`.
* `benchmarks/bench_sparsify.py` no longer passes
  `sparsify_shortcuts=False`; that switch was removed.

## Source-breaking examples

```python
# Old
from reachq.core.tc import transitive_closure_matrix
from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq import Flags
# New
from reachq.closure import transitive_closure
from reachq.shortcut import build_shortcut_set_for_reachability
from reachq import RefinementConfig
```

See `docs/migration_0_9.md` for the prior migration and the
`CHANGELOG.md` for the full history.
