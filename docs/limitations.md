# Limitations

This page lists what reachq 0.9.0 does NOT do.

## What is NOT supported

| Capability | Status | Where to look |
|---|---|---|
| Parallel hopset construction | Not implemented. CFR per-pivot SSSP is GIL-bound in Python; the hopset path runs sequentially. JLS dispatches per-pivot BFS through a process pool. | [`docs/migration_0_9.md`](migration_0_9.md), [`docs/algorithms.md`](algorithms.md) |
| JIT / native C extensions | Not implemented. The wheel and sdist ship only pure-Python fallbacks. | [`docs/accel.md`](accel.md) |
| Distributed execution (Ray, Dask, GraphBLAS) | Stub only. | [`reachq/accel/`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/tree/master/reachq/accel) |
| GPU acceleration | Not implemented. | This page. |
| (1+ε)-approximation for the minimum shortcut set | Not implemented. `greedy_shortcut_set` is a vanilla greedy. | [`docs/approximation_analysis.md`](approximation_analysis.md) |
| Amortised O(log² n) streaming shortcut set | Not implemented. | [`docs/streaming_proof.md`](streaming_proof.md) |
| Backward compatibility shims | None. v0.9.0 is a hard cut from v0.8.0. | [`docs/migration_0_9.md`](migration_0_9.md) |
| Real-world graph scale (web-Google, n ≈ 875k) | Memory is unblocked, but wall-clock is dominated by Python's per-edge overhead. | [`README.md`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/README.md) |
| Pretrained / cached predictions | Not implemented. `omega` and `epsilon` are explicit caller-provided parameters with common heuristics in the docstrings (e.g. ``eps = 1 / sqrt(n)`` clamped to ``[0.01, 0.5]`` for hopsets). | n/a |
| Reporting / visualisation beyond printed logs | Not implemented. The CLI prints results; there is no plotting, no dashboard, no HTML report. | [`reachq.cli`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/reachq/cli/main.py) |

## What IS supported

- Pure-Python JLS shortcut-set construction
  (`build_shortcut_set_for_reachability`).
- CFR + TruncSSSP-Pruning hopset construction
  (`build_hopset_for_sssp`).
- Boolean-semiring transitive closure
  (`transitive_closure_boolean`) with an explicit ``max_pairs``
  budget.
- Insertion-order vertex indexing for cross-process
  reproducibility.
- Heap-tie-break correctness for arbitrarily hashable vertex
  types (``object()``, ``frozenset``, custom).
- Per-invocation state binding so concurrent JLS builds cannot
  share mutable worker state.
- Adaptive sampling that actually scales the next-level
  probability.
- Adaptive heuristics (`predict_omega`, `predict_epsilon`,
  `auto_tune`).
- Property-based testing (`pytest` + `hypothesis`) including
  differential NetworkX oracles.
- JSON / Arrow / NetworkX serialization.
- Documentation site (`mkdocs build --strict`).
