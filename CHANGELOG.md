# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2026-08-30

Hard-cut correctness release. No backward compatibility shims;
v0.8.x users must follow [`docs/migration_0_9.md`](docs/migration_0_9.md).

### Critical correctness

- **`shortest_path_hopbound` rewritten as layered DP** (reviewer's
  counterexample). The old per-vertex distance map suppressed
  costlier arrivals that left hops needed to reach the target.
  New implementation keeps a per-``(vertex, hops)`` state.
- **Weighted SCC condensation removed from the hopset path** (and
  CFR is run on the original graph). The previous
  ``scc_rep[idx]`` mapping emitted underweighted shortcuts on
  hash-randomized inputs. A multi-``PYTHONHASHSEED`` test now
  pins this.
- **Hop-bounded SSSP raised on incomparable vertices**: every
  heap tuple now includes a per-call monotonic counter so ties
  never fall through to a vertex comparison.
- **Heap contracts documented per algorithm**
  (``(distance, counter, vertex)`` etc.); the constants are part
  of the public contract.
- **TC rewritten in the Boolean semiring.** No more integer path
  counts and no more overflow. New ``max_pairs`` budget with
  ``TransitiveClosureBudgetError``.

### Threading / process parallelism

- **Module-level ``PIVOT_STATE`` removed.** State is bound per
  invocation and passed as the task tuple ``(graph, state,
  pivot)``. Workers never read globals. Process pool uses
  ``mp_context="spawn"``.
- **Concurrent JLS builds no longer corrupt each other**, even
  when ``flags.parallel=True`` and ``parallel_workers > 1``.
- **Adaptive sampling actually scales the next-level sampling
  constant.** The previous "RNG perturbation" workaround
  (``rng.random() × 7 % 13``) is removed.

### Reproducibility

- **Insertion-order vertex index.** ``Graph`` now exposes
  ``vertices()`` as a tuple in canonical insertion order. SCC,
  partition, sampling, recursion, CSR, and ``strongly_connected_components``
  consume the order. ``vertex_set`` is gone.
- **Cross-process byte-stability** verified by
  ``tests/test_reproducibility_subprocess.py``: subprocess runs
  under diverse ``PYTHONHASHSEED`` values produce identical
  shortcut sets.

### Input validation

- ``WeightedDigraph.add_edge`` rejects non-int, ``bool``,
  ``NaN``, ``inf``, and negative weights.
- ``Dijkstra``, ``truncated_dijkstra``, ``shortest_path``,
  ``shortest_path_hopbound``, ``astar``, ``parallel_bfs``,
  ``bfs_reachability``, ``reverse_bfs_reachability`` raise
  ``KeyError`` for sources not in the graph.
- ``truncated_dijkstra`` and ``shortest_path_hopbound`` raise
  ``ValueError`` for negative bounds.
- A* accepts ``reopen=True`` (re-relaxes ``g_score`` on better
  arrivals) and ``require_consistent=True`` (validates the
  heuristic up to ``dist(source, target)``).

### Reachability contract

- ``dijkstra`` returns reachable vertices only; unreachable are
  absent.
- ``shortest_path`` returns the new
  ``UNREACHABLE`` sentinel (~ ``1 << 62``).
- The legacy ``dijkstra(...)[v] == float('inf')`` idiom is gone.

### Removed (dead code)

- The ``reachq.core.backends`` module (per-call executor is in
  :class:`reachq.core.algorithm.parallel.ParallelExecutor`).
- The legacy ``jls_shortcut_set`` and ``cfr_hopset`` thin
  wrappers removed from top-level exports.
- The ``Flags`` alias for ``RefinementConfig``.
- The unsafe ``sparsify_shortcuts=True`` switch.
- ``apply_pivot`` consolidated into ``reachq.core.algorithm.pivots``.
- Module-level ``SAMPLING_CONSTANT``, ``OMEGA_DEFAULT``,
  ``OMEGA_RUNTIME``, ``OMEGA_RUNTIME_HOP``, ``CONFIGURED``.

### Architecture

- ``reachq.core.algorithm`` is now a subpackage
  (``algorithm/{state,pivots,partition,recursion,scc_lift,parallel,adaptive,wrap}.py``).
- ``reachq.proto`` no longer references backends.
- ``reachq.core.config`` no longer mutates the root logger;
  CLI scripts must call ``configure_logging()``.

### Benchmarks

- ``scripts/benchmark_shortest_paths.py`` and
  ``scripts/benchmark_reachability.py`` rewritten around the
  **returned β**. New fields: max hop count, β violations,
  approximation violations, reached %, environment metadata.
- Hop-counting BFS indexes shortcuts by source (no longer
  scans every shortcut edge).

### Tests

- 632 tests pass; new oracles:
  - ``test_hopbound_dominance.py``
  - ``test_heap_incomparable_vertices.py``
  - ``test_hopset_weight_accuracy.py``
  - ``test_algorithm_concurrency.py``
  - ``test_networkx_differential_shortest.py``
  - ``test_reproducibility_subprocess.py``
  - ``test_regression_v0_9_fixes.py``
- The broken ``test_hopset_does_not_introduce_negative_weights``
  test (triple-destructure on empty hopset) is replaced by
  ``test_hopset_weights_match_dijkstra``.

## [0.8.0] - 2026-08-15

The first releaseable version of `reachq`. The previous tag
(`7.0.0`) was a placeholder; this is the first PyPI-published
artifact. **Test count: 575 passed + 1 xfailed (576 total).**

### Added

- **Density-aware sampling constant is per-call.** The constant
  `density_aware_constant(rho, k)` is now threaded through
  `jls_with_tc_pruning` and `iterative_shortcut_set` as an
  explicit parameter rather than a module global. Concurrent
  builds with different graph densities cannot clobber each
  other's constant. The helper's docstring now matches the
  code: the constant is non-decreasing in `rho` (dense keeps
  `C=10`, sparse shrinks, floor `C=1`); the old text claimed
  the opposite direction.
- **`shrikhande_cayley()` generator.** The proper non-rook
  `(16, 6, 2, 2)` strongly regular graph built on `Z_4 x Z_4`
  with the symmetric generator set. Tested in
  `tests/test_shrikhande_cayley.py` and documented in
  `docs/spectral_fixtures.md`.
- **`docs/limitations.md`.** A consolidated page pointing at
  every "what is NOT implemented" claim; previously scattered
  across `WHY.md`, `faq.md`, `accel.md`, `streaming_proof.md`,
  `approximation_analysis.md`, `benchmarks.md`, and the README.
- **`docs/algorithms.md` / `docs/work-depth.md` cover
  `RefinementConfig` and `parallel_workers`.** The wrapper-level
  flags and the (currently sequential-only) parallel-execution
  argument are documented together with their honest scope.
- **`docs/REFERENCE.md` adds 28 missing API directives.** CSR
  numpy BFS kernels, the networkx adapter, the SCC-shortcuts
  assertion, and a CLI section pointing at `reachq.cli.main`.
- **Google-style docstring upgrades across ~60 functions and
  12 modules.** Includes `core/io/json`, `core/io/arrow`,
  `core/io/networkx`, `core/{bfs, reachability, shortest_paths,
  work_depth, generators, invariants, metrics, tuner, tc,
  spectrum, prune}`, `research/{iterate, adaptive_beta,
  approximation, blas_omega, fix_resample, lower_bound}`,
  `accel/{rust, dask, graphblas, ray}`, and `cli/main.py`.

### Fixed

- **`prunning` → `pruning` rename in `core/hopset.py`.** The CFR
  shared body and its two public entry points used a typo. 6
  occurrences; no external callers (parameter is keyword-only).
- **Dead `n = ...; del n` removed from `core/predictor.py`.**
  `predict_omega` assigned an unused local and immediately
  deleted it.
- **`Backend` Protocol de-duplicated.** `reachq.core.backends`
  is now the canonical home; `reachq/proto/backend.py` was
  deleted. Plus `@runtime_checkable` was added to the canonical
  Protocol.
- **`tree_shortcut_set_lower_bound` docstring is now honest.**
  Body returns `0` as a placeholder; the documented `n - 1`
  bound is unimplemented. No callers exist.
- **cibuildwheel config: `build-platform` and the top-level
  `archs` removed.** cibuildwheel 4.2.0 rejects `build-platform`
  in a config file with a hard error that broke `wheels.yml`
  on every runner. Verified after the fix that all three
  platforms (linux/macos/windows) produce the expected build
  identifiers (16/8/4 wheels).
- **`docs/streaming_proof.md` rewritten as an honest sketch.**
  The title and body claimed an amortised O(log² n) per-
  insertion bound that the prototype does not implement; the
  derivation produced O(log³ n) but then hand-waved to a
  "tighter analysis" that doesn't exist. The new title says
  "sketch, no formal bound yet" and points at the code's own
  honest scope.
- **`PAPER.md` is marked as a historical draft.** The
  StreamingShortcutSet and greedy_shortcut_set claims no
  longer match the implementation; the banner points at
  `docs/limitations.md` and warns against hard-coding test
  counts.
- **`ARCHITECTURE_REVIEW.md` renamed to
  `HISTORICAL_ARCHITECTURE_REVIEW.md`.** The 819-line document
  is acknowledged as a historical snapshot; the new filename
  and `mkdocs` label make the historical nature unmissable.
- **`notes_correctness.md` banner names the regression tests.**
  All four bugs documented in the corrigendum are fixed in
  v0.8.0; the new banner points at the four test files that
  pin each fix.
- **`docs/PAPER.md`, `docs/ARCHITECTURE_REVIEW.md`,
  `docs/INSPIRED_BY.md`, `docs/WHY.md` corrections.** Version
  references (`1.0.0` → `0.8.0`), test counts (the stale
  "422 tests pass" is replaced with a pointer to CHANGELOG),
  the streaming O(log² n) overclaim, and the (1+ε) formal-
  guarantee overclaim.
- **`docs/spectral_fixtures.md` documents `shrikhande_cayley()`.**
  Removed the stale "future work" claim.
- **`docs/index.md` API name drift fixed.** The doc previously
  referenced non-existent `digraph_to_json`/`digraph_from_json`/
  `weighted_digraph_to_json`/`weighted_digraph_from_json`;
  replaced with the real `dump`/`load`/`weighted_dump`/
  `weighted_load`/`digraph_to_dict`/`digraph_from_dict`.
- **`docs/faq.md`, `docs/getting-started.md` Python 3.10+**
  (was 3.9+; pyproject.toml requires ≥ 3.10).
- **`docs/notes_correctness.md` test path corrected.** The
  pre-fix `tests/test_shortcut_set.py` was split into four
  files; the corrigendum now points at
  `tests/test_shortcut_set_basic.py::TestJlsBasic`.
- **`reachq/cli/main.py` module docstring lists all 6
  subcommands.** The argparse registers `benchmark-large` but
  the docstring only listed 5.
- **`docs/accel.md` correctly states what ships.** The wheel
  and sdist contain only the pure-Python fallback wrappers;
  the `.pyx` and Rust sources live only in the git repo.

### Changed

- **README roadmap de-staled.** Networkx cross-check, property
  tests, `REACHQ_HYPOTHESIS=10000` nightly, MkDocs strict
  build, the sdist publish workflow, pre-commit ruff, and the
  lit survey are all marked done (with caveats). The remaining
  Planned section is short and reflects the real remainder.
- **`docs/architecture.md` Module Index now lists the 14
  modules that were missing from the architecture diagram.**
  Coverage claim is the verified 76% (3737 statements, 880
  missed) instead of an unverified "~76%".
- **`docs/algorithms.md` documents the `RefinementConfig` flags
  and the `parallel_workers` parameter** (currently
  logged-and-ignored).
- **`docs/getting-started.md` example uses `complete_dag(10)`.**
  The old path-on-100-vertices example produced 0 shortcuts
  by design (the path already has the right reachability), which
  was confusing for new readers. The complete DAG produces
  45 shortcuts with seed 42.
- **`docs/GLOSSARY.md` adds 8 new terms** (ParallelContext,
  Backend, SpanProfiler, Snapshot, Recorder/record_*,
  RefinementConfig, sparsify_shortcut_set vs
  sparsify_hop_bounded). The StreamingShortcutSet entry
  corrected from "amortised O(log² n)" to "no formal amortised
  bound yet".

### Removed

- **`reachq/proto/backend.py`** — moved to
  `reachq/core/backends/__init__.py`.
- **`docs/ARCHITECTURE_REVIEW.md`** — renamed to
  `docs/HISTORICAL_ARCHITECTURE_REVIEW.md` to make the
  historical nature unmissable.

## [0.7.0] - 2026-07-23

### Added

- **Algorithmic improvements.** Adaptive sampling probability,
  label compression, skip-SCC condensation on DAG inputs,
  hop-bounded pivot BFS, degree-ordered pivot iteration,
  skip-trivial-partition guard, tightened TC-pruning trigger.
  All toggleable via `reachq.Flags` (= `RefinementConfig`).
- **`tests/test_algorithmic_improvements.py`** — parametrized
  correctness tests with each flag toggled off, plus a networkx
  cross-check on shortcut-set reachability.
- **`tests/test_properties.py`** — Hypothesis-based property
  tests on random DAGs.

### Fixed

- **`transitive_closure_matrix` now uses `scipy.sparse`**
  Boolean matmul. Previous dense `np.zeros((n, n))` OOMed
  above ~50k vertices; sparse stays O(n + m) memory and scales
  to web-Google (n=875k).
- **Vectorised `csr_reachable_forward`** — replaced the Python
  `for i in range(frontier.size)` inside the frontier expansion
  with a vectorised `np.repeat` + `cumsum` gather.
- **SCC-representative translation** in both wrappers was
  indexing outside the SCC coordinates when the trivial
  condensation path was active. Fixed by branching.
- **TC-pruning self-loops** filtered at the call site (they
  used to leak into the shortcut set and break `parallel_bfs`).
- **Hopset `graph.reversed()`** hoisted once per recursion
  level (was once per pivot).

### Removed

- The separate `jls_shortcut_set` (no-pruning) code path and its
  4 `DEBUG print(...)` blocks. The function is now a thin
  wrapper around `jls_with_tc_pruning` with
  `enable_tc_pruning=False`.
- The half-wired multiprocessing pivot-parallelisation
  scaffold.

## [0.6.0] - 2026-07-24

### Added

- **Test fixtures from algebraic graph theory.**
  `petersen_graph`, `paley_graph`, `shrikhande_graph`,
  `hamming_graph` in `reachq/core/generators.py`. Documented
  in `docs/spectral_fixtures.md`.
- **`Digraph.add_undirected_edge(u, v)`** — adds both
  directions, counts one edge. Required for the symmetric
  generators.
- **`reachq/core/spectrum.py`** — `spectrum(g)` and
  `spectral_gap(g)` helpers.
- **`reachq/research/fix_resample.py`** — Fix/Resample variant
  inspired by Assadi–Yazdanyar's dynamic graph coloring.
  Static analogue only; honest scoping as an experimental
  baseline (dynamic-update bounds do not apply to a static
  codebase).
- **`scripts/eval_fix_resample.py`** — empirical comparison
  vs JLS. Result: 16% of JLS's `|H|` on average, but with a
  looser hopbound (~3 vs JLS's ~1).
- **`scripts/spectral_check.py`** — runs each named fixture
  through the JLS construction and reports `|H|`, `β`, spectral
  gap.

### Fixed

- `petersen_graph()` inner cycle order corrected to pentagram
  (was producing a non-isomorphic 3-regular graph).
- `hamming_graph()` digit-ordering inconsistency.
- `paley_graph()` documentation now reflects the actual
  eigenvalues `(-1 ± √q)/2`.

## [0.5.0] - 2026-07-22

### Added

- Graph base class with template method pattern
  (`initialize_vertex`, `iterate_edges_from`, `store_edge`,
  `create_empty`).
- Covariant return types on `Digraph`/`WeightedDigraph`
  overrides.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `CHANGELOG.md`, `.editorconfig`, `.gitattributes`,
  `.env.example`, GitHub issue + PR templates.
- `docs/getting-started.md`, `docs/architecture.md`,
  `docs/deployment.md`, `docs/faq.md`.

### Changed

- `partition_by_labels` and `contract_sccs` extracted into
  `core/graph.py`.
- All `_`-prefixed identifiers renamed to public names across
  14 files (~78 sites).
- `Graph` → `Digraph` → `WeightedDigraph` inheritance hierarchy
  with template hooks.

## [0.4.0] - 2026-07-22

Process mode uses fork-safe initializer (`_init_pivot_worker`).
`graph` passed via a dedicated initializer instead of module-level
globals.

## [0.3.0] - 2026-07-22

`Flags` replaced by `RefinementConfig`. Frozen dataclass with
`__slots__` in `core/config.py`. `reachq.Flags = RefinementConfig`
alias kept.

## [0.2.0] - 2026-07-22

Drop Python 3.9 support. Restructure into subpackages:
`reachq/core/`, `reachq/research/`, `reachq/cli/`, `reachq/proto/`,
`reachq/accel/`. Rename `logging_config` → `core.config`,
`serialization` → `core.io.json`.

## [0.1.0] - 2026-07-22

Initial release. JLS shortcut-set construction, CFR hopset
construction, sparse transitive closure, RDF parsing, SNAP
loader, and basic CI.
