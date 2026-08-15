# Limitations

This page lists what reachq 0.8.0 does NOT do. Each item links to
the doc that explains the limitation in detail.

## What is NOT supported

| Capability | Status | Where to look |
|---|---|---|
| True parallel execution (PRAM / threads / processes) | Not implemented. The current code is single-threaded; the `parallel_workers` parameter is logged-and-ignored on the process path. The CFR path exposes it but the underlying map is not picklable. | [`docs/algorithms.md`](algorithms.md), [`docs/ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) |
| JIT / native C extensions | Not implemented. The wheel and sdist ship only pure-Python fallbacks; the Cython `.pyx` and Rust `.rs` sources live in the git repo only. | [`docs/accel.md`](accel.md) |
| Distributed execution (Ray, Dask, GraphBLAS) | Stub only. The Backend Protocol shape is provided but the implementations are not wired into the JLS construction. | [`reachq/accel/`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/tree/master/reachq/accel) |
| GPU acceleration | Not implemented. | This page. |
| (1+ε)-approximation for the minimum shortcut set | Not implemented. `greedy_shortcut_set` is a vanilla greedy without the formal (1+ε) bound. | [`docs/approximation_analysis.md`](approximation_analysis.md) |
| Amortised O(log² n) streaming shortcut set | Not implemented. The prototype is a structural scaffold; the bound is not achieved. | [`docs/streaming_proof.md`](streaming_proof.md) |
| Test counts in user-facing docs | Tests counts are not hard-coded in this documentation; see [`CHANGELOG.md`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/CHANGELOG.md) for the current count. | CHANGELOG.md |
| Real-world graph scale (web-Google, n ≈ 875k) | Memory is unblocked (sparse TC), but wall-clock is dominated by Python's per-edge overhead. The `web-Google` benchmark is shown in the README as a known limit. | [`README.md`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/README.md) |
| Pretrained / cached predictions | Not implemented. `predict_omega` and `predict_epsilon` are heuristics, not learned models. | [`reachq.core.predictor`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/reachq/core/predictor.py) |
| Packaged wheels on PyPI | The sdist ships on PyPI (via `release.yml`); wheels are built on every commit by `wheels.yml` but are not currently published. | [`docs/deployment.md`](deployment.md) |
| Reporting / visualisation beyond printed logs | Not implemented. The CLI prints results; there is no plotting, no dashboard, no HTML report. | [`reachq.cli.main`](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/reachq/cli/main.py) |

## What IS supported

- Pure-Python JLS shortcut-set construction (`build_shortcut_set_for_reachability`).
- CFR + TruncSSSP-Pruning hopset construction (`build_hopset_for_sssp`).
- Sparse transitive closure (`transitive_closure_matrix`) handling graphs up to ~875k vertices.
- Adaptive heuristics (`predict_omega`, `predict_epsilon`, `auto_tune`).
- Property-based testing (`pytest` + `hypothesis`).
- JSON / Arrow / NetworkX serialization.
- Documentation site (`mkdocs build --strict`).
- Pre-commit (ruff) and CI (mypy, ruff, pytest, networkx cross-check, nightly slow).
