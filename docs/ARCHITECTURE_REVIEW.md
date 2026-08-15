# 1. Executive Summary

> **Historical snapshot.** This review describes the repository *as it
> was* at review time (466 tests passing, flat module layout). It is
> kept for the record; it does not describe the current package. Since
> then the tree moved to `reachq.core.*` / `reachq.research.*`, CI is
> green (lint, typecheck, docs, tests), mypy is clean, mkdocs builds
> `--strict`, and the sampling constant is threaded per-call rather
> than through a module global. Where this review contradicts current
> docs, the current docs win.

`reachq` is a pure-Python reimplementation of the JLS shortcut-set and CFR hopset constructions from a parallel-reachability paper, plus four post-processing refinements and a few research-only extensions. The core algorithms are theoretically sound and the public API is small (~25 functions). However, the repository has accumulated the typical growth-pain profile of a research codebase stretched toward production: **no packaging discipline, no parallel execution actually validated, no observability, no reproducibility guarantees, and a research/extension layer mixed into the core namespace.**

- **Today:** 6,791 LOC of `reachq/`, 5,313 LOC of tests, 84 Python files. 466 tests pass, 14 fail (pre-existing), 1 xfailed. Pure Python with numpy/scipy. Sequential except for one half-wired `ParallelContext` that only works for the JLS path.
- **Final-form aspiration:** A typed, layered, tested, documented, packaged, benchmarked, reproducible library whose core (`reachq-core`) is a 2,000–3,000 LOC pure-Python algorithm library; an opt-in `reachq-accel` extension layer for vectorised/parallel kernels; a separate `reachq-research` namespace for experimental algorithms; and an enterprise-grade documentation, CI, and release pipeline.

The dominant engineering contradictions are:

1. **Generic algorithms vs specialised inner loops.** A single JLS recursion currently mixes sampling, partitioning, recursion, and TC-pruning into one 670-line function. This blocks both performance work and extension.
2. **Performance vs determinism.** The package advertises thread/process parallelism; only thread parallelism is safe today; process parallelism requires a non-picklable module global.
3. **Public API stability vs research churn.** Several research-only modules live at top-level and are imported in tests, so a research-only rename would break downstream.
4. **Algorithmic correctness vs empirical presentation.** The README/CHANGELOG oversell at least three things (streaming prototype, (1+ε) approximation, hopset parallel dispatch).

# 2. Current Repository Assessment

## Strengths

- **Theoretical foundation is solid.** JLS shortcut set, CFR hopset, and TC-pruning are correct; four bugs in the historical reference were fixed and regression-tested.
- **Determinism.** Every randomised algorithm takes `random_seed` and uses `random.Random` instances; this is a property worth preserving.
- **No magic.** No JIT, no Cython, no Rust — the entire codebase is pure Python + numpy + scipy. This lowers the contribution barrier dramatically.
- **Documentation is honest about scope.** Several modules openly admit "research prototype" or "sketch proof."

## Weaknesses

| Area | Issue |
|---|---|
| API | `reachq.research` advertises a stable-looking API surface (`sparsify_hop`, `iterate`, `closed_form`, `adaptive_beta`, `lower_bound` — `docs/REFERENCE.md`) but those modules don't live in `reachq/research/` at all. |
| Tests | 14 pre-existing failures (`test_hopset_soundness.py` uses `omega=` kwarg that doesn't exist; `test_reachability_through_shortcuts.py` passes wrong type; `test_shortest_paths_extended.py` had an import error until just-fixed). |
| Parallelism | `parallel_workers` parameter is exposed on `build_shortcut_set_for_reachability` but the CFR path has no equivalent. ProcessPool mode silently won't work because of a module-global `_PIVOT_STATE` dict. |
| Performance | No GPU, no SIMD, no compiled extensions. The recursion's per-pivot BFS rebuilds Python sets even when CSR is available. `sparsify.py` rebuilds a `shortcut_index` from scratch on every check (O(\|H\|) per call, O(\|H\|²) total). |
| Observability | No metrics, no traces, no counters. The `WorkDepthAccountant` is a manual, opt-in cost recorder — useful for verification but not for production telemetry. |
| Packaging | `pyproject.toml` declares version 0.8.0; no `console_scripts` (now added); no wheels built; no SBOM; no `requires-python` upper bound; no `tests` extra. |
| CI | Single matrix; no caching of test results; no coverage diff; benchmark job runs one trivial benchmark; pre-commit is separate from lint. |
| Reproducibility | `pip install reachq` works (post-fix), but `python -m scripts.cli` requires `scripts/__init__.py` (now added). SNAP "sha256 verification" is a misnomer — the script computes a hash but never compares it. |
| Memory | `sparsify.py` allocates a fresh `dict[Any, list[Any]]` per call. `transitive_closure_matrix` reallocates a COO pair set every iteration. `numpy_bfs.csr_reachable_forward` reallocates `positions` arrays per BFS step. |
| Documentation | 22 `.md` files; only 19 are referenced in `mkdocs.yml`; `examples/` and `benchmarks/` are absent from the nav. |
| Research layer | `StreamingShortcutSet` is honest about being a stub, but its tests still let failures pass via `pass`. `greedy_shortcut_set` is misnamed — it is a vanilla greedy, not (1+ε). |
| Type safety | `mypy` reports 14 pre-existing errors. `mypy --strict` not configured. |
| Configuration | `Flags` is a `dataclass` with 9 boolean fields — already showing the Boolean-flag-explosion anti-pattern. |

## Public API surface today

| Module | Functions/classes | Stability |
|---|---|---|
| `reachq.core.graph` | `Digraph`, `WeightedDigraph`, `Graph`, `partition_by_labels`, `contract_sccs` | stable |
| `reachq.core.reachability` | `bfs_reachability`, `parallel_bfs`, `strongly_connected_components`, `topological_sort`, `compute_*` | stable |
| `reachq.core.shortest_paths` | `dijkstra`, `astar`, `truncated_dijkstra`, `shortest_path`, `shortest_path_hopbound`, `shortest_path_tree` | stable |
| `reachq.core.algorithm` | `build_shortcut_set_for_reachability`, `jls_shortcut_set`, `jls_with_tc_pruning` | stable |
| `reachq.core.config` | `RefinementConfig` (exported as `reachq.Flags`) | stable |
| `reachq.core.hopset` | `build_hopset_for_sssp`, `cfr_hopset`, `cfr_with_truncsssp_pruning` | stable |
| `reachq.core.tc` | `transitive_closure_matrix`, `transitive_closure_brute_force`, `transitive_closure_on_subset` | stable |
| `reachq.core.generators` | 17 generators incl. SRG/Hamming fixtures | stable |
| `reachq.core.io.json` | `dump`, `load`, `weighted_dump`, `weighted_load`, `digraph_to/from_dict` | stable |
| `reachq.core.work_depth` | `WorkDepthAccountant`, `SpanProfiler`, recording fns | stable |
| `reachq.core.spectrum` | `spectrum`, `spectral_gap` | stable |
| `reachq.core.bfs` | vectorised CSR BFS | stable |
| `reachq.core.metrics` | `enable_metrics`, `inc_counter`, `record_histogram`, `snapshot` | stable |
| `reachq.core.trace` | `trace` | stable |
| `reachq.research.adaptive_beta` | `adaptive_beta`, `paper_beta` | research |
| `reachq.research.iterate` | `iterative_shortcut_set` | research |
| `reachq.research.sparsify`, `reachq.research.sparsify_hop` | `sparsify_shortcut_set`, `sparsify_hop_bounded`, `verify_hopbound_preserved` | research |
| `reachq.research.fix_resample` | `fix_resample_shortcut_set` | research |
| `reachq.research.lower_bound` | constructions + `barbell_graph`, `layered_dag` | research |
| `reachq.research.closed_form` | closed-form shortcut sets + `binary_tree_dag` | research |
| `reachq.research.streaming`, `reachq.research.approximation` | prototype streaming shortcut set, (1+ε) approximation | research |

The split is now consistent: the always-imported library layer lives in
`reachq.core.*`; every opt-in/experimental algorithm lives in
`reachq.research.*`. The top-level `reachq` package re-exports the stable
surface (`__all__` in `reachq/__init__.py`).

# 3. Ideal Final Result (IFR)

A flagship, enterprise-and-research-grade parallel-reachability library.

### Architecture (one paragraph)

A two-layer repository: a `reachq_core` Python package implementing the pure-Python algorithm library (≤ 3,000 LOC), and a `reachq_research` Python package implementing experimental algorithms gated behind an `enable()` lifecycle hook. `reachq_core` is dependency-light (numpy + scipy); `reachq_research` may pull in optional ML / GPU / GraphBLAS dependencies. Both share a `reachq_types` package containing the public protocol/ABC interfaces for graphs, RNG, logging, and parallelism backends. A single facade package `reachq` re-exports the stable surface from `reachq_core` for backward compatibility.

### Developer experience

- `pip install reachq` → `from reachq import Digraph, build_shortcut_set_for_reachability` works.
- `pip install reachq[accel]` → optional Rust/Cython kernels available via env var or `flags={"backend": "accel"}`.
- `pip install reachq[research]` → `reachq_research` algorithms available.
- `pip install reachq[dev]` → dev tooling.
- `pre-commit run` runs ruff-format, ruff, mypy, and a docstring check.
- `tox -e py39,py310,py311,py312,py313` runs the full matrix.
- `asv` micro-benchmarks are reproducible across Python versions.
- `make reproduce` runs the full SNAP benchmark on a Docker image and writes `results/`.
- `reachq doctest` validates the doctests embedded in every public function's docstring.
- `reachq compare-configs config_a.json config_b.json` diffs two configurations of refinement flags against benchmark CSVs.

### Performance

- 10× wall-clock speedup on the SNAP `cit-HepPh` (n=34k, m=421k) benchmark through a combination of:
  - vectorised CSR BFS (already partially implemented)
  - single `shortcut_index` reused across `sparsify_shortcut_set` checks
  - Cython/numba kernels for the per-pivot BFS inner loop (out-of-scope today, but staged behind an optional `backend` flag)
  - elimination of unnecessary `g.vertices()` copies in the recursion hot path
- Memory bounded by `O(n + m + |H|)` for shortcut-set construction, where today the bound is `O(n + m + |H|²)` for `sparsify`.

### Memory

- A single adjacency representation per graph instance.
- Streaming pivots for `shortcut_set` (compute one pivot at a time; do not materialise the full pivot dict).
- Single-pass TC-pruning: threshold stored as `int64`, COO pairs emitted once.

### Parallelism

- `ParallelContext` becomes a real strategy pattern: `threads`, `processes`, `mp_queue`, `ray`, `dask`. Default = `threads(n)` for `n = os.cpu_count()`. Each pivot serialises through a `Protocol`-typed function reference so that no module globals are required.
- `processes` mode becomes a first-class backend via `multiprocessing.get_context("spawn").Pool(initializer=_init_worker)` — no global state.
- `ray` / `dask` backends ship as `reachq[accel]` extras.

### Reliability

- Soundness: every public construction has a soundness property test (already present in `tests/test_reachability_through_shortcuts.py`, but those tests don't actually pass — see Contradiction §4).
- Property tests: `Hypothesis` strategies for graph invariants (already present).
- Determinism: per-call `random_seed`, default seed for tests.
- Doctests: every public function has a runnable doctest embedded in its docstring.
- CI: type-checked (`mypy --strict`), lint-enforced (`ruff`), format-enforced (`ruff-format`), security-scanned (`bandit`, `pip-audit`), benchmark-tracked (`asv` with commit-level comparison).

### API simplicity

- `Flags` → `RefinementConfig` (no more Boolean explosion; instead, an enum or a struct).
- `from reachq import Digraph, ...` covers the 95% use case.
- All public functions have type annotations + a single-paragraph `Raises:` section.
- `from reachq import __version__` returns the canonical version.

### Testing

- ≥ 90% line coverage, ≥ 80% branch coverage, enforced in CI.
- 100% of public symbols have at least one passing test.
- Property tests run with `HYPOTHESIS_PROFILE=ci` (max_examples=200, deadline=10s).
- Mutation testing on `reachq_core` via `mutmut` or `cosmic-ray` (long-term).

### Packaging

- `pyproject.toml` declares version, optional-dependencies, console-scripts, type-checking config, ruff config, mypy config, pytest config, cibuildwheel config.
- Pre-built wheels for `cp39-cp313` on `linux_x86_64`, `linux_aarch64`, `macos_x86_64`, `macos_arm64`, `windows_amd64`.
- SBOM generated per release via `cyclonedx-py`.
- Source distribution via `python -m build`.

### Documentation

- `mkdocs` site (already configured) with:
  - Tutorial (Jupyter notebooks in `notebooks/`)
  - How-to guides (`docs/howto/*.md`)
  - Reference (auto-generated from docstrings)
  - Explanation (`docs/PAPER.md`, `docs/INSPIRED_BY.md`, `docs/notes_correctness.md`)
  - Research layer (`reachq.research.*`)
- `examples/` linked from nav.

### Open-source adoption

- Issue templates: bug report, feature request, algorithm proposal, performance issue.
- PR template: includes checklist for tests, docs, benchmark.
- `CONTRIBUTING.md` updated to link to the architecture doc.
- `SECURITY.md` already exists.
- `CODE_OF_CONDUCT.md` already exists.
- `LICENSE` already exists.
- `CHANGELOG.md` already in Keep-a-Changelog format.
- `README.md` has badges (already configured).
- A "Good first issues" label.
- A `ROADMAP.md` (already partially present as `docs/PAPER.md` §6 — needs to be promoted).
- A "Cite this" section (already present).
- A "Performance" section with reproducible numbers (already present, but numbers are stale).

### Research reproducibility

- Every script accepts `--seed` and `--out`.
- Every script writes `hardware.json` (already done in `reproduce_results.py`).
- Every script is reproducible: `make reproduce && diff results/ docs/expected/`.

### Commercial readiness

- LTS policy documented.
- API stability promise documented (semver).
- SLI/SLO documented (paper-lemma benchmarks pass with ≥ 95% confidence over 100 seeds).
- CVE scan in CI.

### Gaps between today and IFR

| Gap | Severity |
|---|---|
| No layer separation between core and research algorithms | High |
| `Flags` boolean explosion | Medium |
| No actual parallelism (only JLS path; CFR path is sequential) | High |
| `parallel_workers` parameter is a half-promise | High |
| Streaming impl is a stub with `pass`-on-failure tests | Medium |
| `greedy_shortcut_set` is misnamed (no (1+ε)) | Medium |
| `sparsify.py` allocates `O(\|H\|²)` in total | High |
| `transitive_closure_matrix` reallocates COO every iter | Medium |
| No `console_scripts` (now added but not tested) | Low |
| No wheels/SBOM | Medium |
| 14 pre-existing test failures | High |
| `mypy` not strict; 14 pre-existing errors | Medium |
| Doc links to deleted files (now fixed) | Low |
| `examples/` not in nav (now fixed) | Low |
| No protocol layer for graph/RNG/parallel backends | Medium |
| No performance regression tracking | Medium |
| SNAP "sha256 verification" is a misnomer | Low |
| Research modules split between top-level and `reachq.research/` (now made consistent with `__init__.py`) | Medium |

# 4. Engineering Contradictions

## C1. Performance vs Memory
**Why:** Sparsification rebuilds a fresh `shortcut_index` dict per shortcut check; storing it across all checks would be `O(|H|²)` memory. Today's path is `O(|H|·(n+m+|H|))` time and `O(n+m+|H|)` memory per call.
**Root cause:** Locality of reference treated as unimportant; allocation considered cheap.
**Impact:** `sparsify_shortcut_set` is `O(|H|²)` in size. On SNAP-scale `|H|`, this is 10¹⁶ ops — infeasible.
**Severity:** High (already acknowledged in the gap analysis; the post-sparsify stage is therefore effectively unused on large inputs).
**Solutions:** (a) Index shortcuts once at function entry, then mutate. (b) For each pivot, only re-check shortcuts with that pivot as source. (c) Use a soundness-aware min-cost-flow formulation.

## C2. Parallelism vs Determinism
**Why:** Parallel pivot processing changes the order of RNG consumption; if the RNG is per-call (not per-pivot), seeds diverge across processes.
**Root cause:** `_PIVOT_STATE` is a module-global; per-pivot RNG is consumed serially in the main thread; a `ProcessPoolExecutor` worker cannot inherit it.
**Severity:** High (currently the `processes` mode is broken; `threads` works because of GIL release on numpy).
**Solutions:** (a) Make per-pivot RNG explicit: `jls_with_tc_pruning(seed_per_pivot=...)`. (b) Use `dask`/`ray` for genuine parallelism. (c) Drop process-mode and document `threads` as the only supported backend.

## C3. Generic API vs Specialised Inner Loops
**Why:** `jls_with_tc_pruning` is a single 670-line function; sampling, recursion, and TC-pruning are entangled.
**Severity:** Medium (inhibits optimisation, profiling, and extension).
**Solutions:** Split into `_jls_recursion`, `_sampling_step`, `_partition_step`, `_tc_prune_step`. Each becomes individually testable and profilable.

## C4. Algorithmic Correctness vs Empirical Presentation
**Why:** README advertises `(1+ε)` approximation, `ParallelContext`, and `StreamingShortcutSet` amortised O(log² n); the code does not deliver these.
**Severity:** Medium (damages trust; misleads users).
**Solutions:** (a) Implement (1+ε) via the random-sampling step (`greedy_random_sampling`). (b) Make `processes` mode work. (c) Either implement proper pivots in `StreamingShortcutSet` or rename it to `StreamingShortcutStub` and document.

## C5. Boolean Flags Explosion vs Clean Configuration
**Why:** 9 flags with default `True`/`False` combinations means 2⁹ = 512 configurations, only 8 of which are tested in `run_ablation.py`.
**Severity:** Medium (testing cost; misconfiguration risk).
**Solutions:** Replace `Flags` with a `RefinementConfig` enum or with a small set of named presets (`RefinementConfig.ALL_ON`, `RefinementConfig.PAPER_BASELINE`, `RefinementConfig.MINIMAL`).

## C6. Documentation vs Maintenance Burden
**Why:** 22 doc files; only 19 in mkdocs nav; multiple cross-references to deleted files.
**Severity:** Low (mostly cosmetic; the gaps are now closed).
**Solutions:** Quarterly doc-audit script that greps for broken links; CI check on `mkdocs build --strict`.

## C7. Reproducibility vs Performance
**Why:** Reproducibility requires stable seeds; the densest performance mode (process-based parallelism) is non-reproducible across machines.
**Severity:** Medium.
**Solutions:** Document reproducibility caveat for each backend; provide a `deterministic_only=True` mode.

## C8. Testing Thoroughness vs Build Time
**Why:** 466 tests currently run in ~37s. Hypothesis-driven tests with `max_examples=200` would push that to >5 minutes.
**Severity:** Low at current scale.
**Solutions:** `pytest -m "not slow"` for PR CI; nightly full run.

## C9. Modularity vs Runtime Cost
**Why:** Splitting `jls_with_tc_pruning` into smaller functions costs Python function-call overhead per recursion level.
**Severity:** Low (Python is already slow; not the bottleneck).
**Solutions:** Inline `__init__`-level hot paths; use `@functools.lru_cache` for memoised subroutines.

## C10. Public API Stability vs Research Churn
**Why:** Several research-only modules live at top-level; users may rely on them; renaming them would break code.
**Severity:** Medium.
**Solutions:** Deprecation cycle (introduce `reachq.research.foo` as alias for `reachq.foo`; deprecate top-level; remove in 2.0).

## C11. Algorithm-Theory Fidelity vs Empirical Performance
**Why:** The paper's analysis is asymptotic; constants matter for real inputs. `JLS+TC-pruning` produces `|H| = 178M` edges on SNAP `cit-HepPh` where the bound is `~600k` — 300× off.
**Severity:** Medium.
**Solutions:** Auto-tune `C` (sampling constant) per graph density (already partly done via `density_aware_constant`); expose as a flag.

## C12. Type Safety vs Implementation Speed
**Why:** Adding full type annotations + `mypy --strict` is a multi-week investment; the algorithms are research code with high churn.
**Severity:** Medium.
**Solutions:** Type the public API first; allow `Any` internally.

# 5. Physical Contradictions

| Property A | Property B | Resolution |
|---|---|---|
| Code should be simple | Code should be extensible | Apply TRIZ "separation in space" — split core (simple) from extension layer (research). |
| Graph should be mutable | Graph should be immutable | Apply TRIZ "separation in time" — graph is mutable during construction, frozen via `freeze()` for sharing across processes. |
| Algorithms should be generic | Algorithms should be specialised | Apply TRIZ "nested doll" — generic outer recursion, specialised inner kernels (CSR BFS, Dijkstra). |
| API should be minimal | API should be feature-rich | Apply TRIZ "extraction" — extract the *minimum* public surface; everything else goes to `reachq.research` or `reachq_extensions`. |
| Tests should be fast | Tests should be thorough | Apply TRIZ "preliminary action" — pre-test in CI using `--co` (collect only); nightly full run. |
| BFS should be sequential | BFS should be parallel | Apply TRIZ "inversion" — run BFS sequentially within a pivot, parallel across pivots. (Already partially implemented.) |
| Performance should be high | Memory should be low | Apply TRIZ "dynamics" — adapt the data structure (sparse vs dense, CSR vs adjacency sets) based on graph density at runtime. |
| API should be stable | Refactoring should be cheap | Apply TRIZ "self-service" — type annotations act as a contract; CI tests pin behaviour. |
| Documentation should be exhaustive | Maintenance should be low | Apply TRIZ "colour/contrast" — auto-generated reference; manually-curated tutorial. |
| Reachability should be deterministic | Algorithm should be efficient | Apply TRIZ "prior counter-action" — pre-compute a structural sketch (SCC, condensation DAG) once; use it to bound stochastic work. |

# 6. TRIZ Principle Analysis (All 40)

1. **Segmentation** — Split the 670-line `jls_with_tc_pruning` into 4–6 smaller functions. *Applies.*
2. **Taking out / Extraction** — Move research modules (`adaptive_beta`, `iterate`, `sparsify*`, `fix_resample`, `lower_bound`, `closed_form`) from top-level into `reachq_research`. *Applies.*
3. **Local quality** — Each module should have a clear local responsibility. The current `work_depth.py` is doing both asymptotic accounting and runtime profiling. *Applies.* Split into `work_depth.py` (theoretical) and `span_profiler.py` (empirical).
4. **Asymmetry** — Different backends for JLS vs CFR (threads-only for CFR, full backend choice for JLS). *Applies.*
5. **Merging** — Combine `parallel.py` and `numpy_bfs.py` into a single `backends/` package. *Applies.* Cleaner dependency graph.
6. **Universality** — `Flags` should become a generic `RefinementConfig` that can be saved/loaded as JSON. *Applies.*
7. **Nested doll** — Inner loop specialisation: per-pivot BFS uses CSR when n ≥ 500; pure-Python sets otherwise. *Already partially applied.*
8. **Anti-weight** — Counter the cost of `sparsify`'s `O(|H|²)` with a sparse index. *Applies.*
9. **Preliminary anti-action** — Before entering recursion, allocate label arrays of size n. Avoid `dict` resize churn. *Applies.*
10. **Preliminary action** — Pre-compute SCC + condensation before JLS starts. *Already done.*
11. **Beforehand cushioning** — Build CSR pair *once* per recursion level (not per pivot). *Already done in current code; refactor must preserve.*
12. **Equipotentiality** — All backends share the same pivot-work signature `(csr_data, rev, graph, max_hops, pivot) -> PivotResult`. *Applies.*
13. **Inversion** — Invert the abstraction: instead of `ParallelContext.imap_unordered`, use a generator that yields work units and let the user provide an executor. *Applies.*
14. **Spheroidality** — Replace `Flags` (boolean tuple) with a `RefinementConfig` dataclass that can be hashed and compared. *Applies.*
15. **Dynamics** — Adapt constants (sampling C, hopbound β, TC threshold) based on graph density. *Already partially done.*
16. **Partial or excessive action** — Skip trivial partition (already done); skip recursion when graph is small (not done).
17. **Another dimension** — Move parallelism to the per-edge level rather than the per-pivot level. *Applies for fine-grained Dijkstra on small r-balls.*
18. **Mechanical vibration** — Use `__slots__` (already done in `Graph`) and `__sizeof__` introspection for memory profiling.
19. **Periodic action** — Cache repeated BFS results in a `lru_cache` keyed by `(source, max_hops)`. *Applies; saves 30–50% on dense graphs where pivots overlap.*
20. **Continuity of useful action** — During TC-pruning, stream the COO pairs to disk if `|R| > threshold`. *Applies; useful for n>10⁶.*
21. **Skipping** — Skip BFS depth 0 trivially (already done). Skip pivots that are isolated.
22. **Blessing in disguise** — The `O(|H|²)` sparsify cost is actually a hint that the JLS output has redundancy; use redundancy to skip shortcut emission.
23. **Feedback** — `RefinementConfig.report()` returns what was actually used vs requested. *Applies.*
24. **Intermediary** — Insert a `Backend` protocol layer between algorithms and executors. *Applies.*
25. **Self-service** — `graph.freeze()` returns a read-only view; useful for sharing across processes. *Applies.*
26. **Copying** — Use virtual views (`memoryview`) for adjacency buffers; reduce refcount churn. *Applies for CSR paths.*
27. **Cheap short-life objects** — Replace `set` allocations with `frozenset` when possible (label compression already does this).
28. **Replacement of mechanical system** — Replace per-pivot Python loop with `joblib.Parallel` backend.
29. **Pneumatic or hydraulic** — Use shared-memory `multiprocessing.RawArray` for adjacency when processes need it. *Applies for `processes` mode.*
30. **Flexible shells or thin films** — Provide a thin `reachq.io` shim for binary formats (GraphBLAS, NetworkX edge lists).
31. **Porous material** — Add filter operations (e.g., `sparsify_shortcut_set` already has a `keep` hook). *Partially applied.*
32. **Changing the colour** — Replace `Flags.bool` with a typed enum so misconfiguration fails at parse time.
33. **Homogeneity** — Use `Protocol` instead of `ABC` for graph interface; enable structural typing.
34. **Discarding and recovering** — `ReachabilitySketch` (HyperLogLog-style) for fast approximate reachability queries. *Applies for very large graphs.*
35. **Parameter changes** — Auto-tune `omega`, `C`, `rho` per graph at construction time. *Already partial.*
36. **Phase transitions** — Switch from Python objects to numpy arrays when graph is dense enough. *Already applied via `should_use_csr`.*
37. **Thermal expansion** — When `|H|` grows beyond a threshold, *don't* add more pivots; fall back to a larger hopbound.
38. **Strong oxidants** — Use Rust/Cython (oxidant — strong typed language) for inner loops.
39. **Inert environment** — Provide a noop backend (`ParallelContext("noop", 1)`) for testing.
40. **Composite materials** — Combine CSR + Python set fallback in `numpy_bfs.should_use_csr`.

# 7. Resource Analysis

- **CPU:** Underutilised. The CFR path is fully sequential; the JLS path uses threads but only for the per-pivot BFS. Switching CFR to threads (each pivot runs a Dijkstra in parallel; GIL released in heapq + numpy paths) would yield 4–8× speedup on 8-core machines.
- **GPU:** Not exploited. SuiteSparse:GraphBLAS + `pygraphblas` would deliver `O(n³ / log n)` practical work for TC-pruning on NVIDIA hardware. Adds a dependency; defer behind `reachq[accel]`.
- **SIMD:** Not exploited. Numba `@njit(parallel=True, fastmath=True)` on the CSR BFS inner loop would give a 5–10× kernel speedup on dense graphs.
- **Compiler optimisations:** Already implicit in numpy/scipy. Cython with typed memoryviews would give a 50× kernel speedup for the per-pivot BFS.
- **Idle memory:** No streaming mode — the entire shortcut set is held in a Python `set`. For 178M edges on `cit-HepPh`, that's ~10 GB of Python object overhead. A compact `numpy.uint32` array would fit in 1.4 GB.
- **Existing metadata:** `edge_count`, `vertex_set` are recomputed in hot paths. Storing as fields (already done) — no further win.
- **Parallelism:** Single-machine threads, only one path. Multi-machine (ray/dask) is not configured.
- **Cache locality:** Python `dict` and `set` have poor cache locality for BFS workloads. CSR arrays (numpy) have excellent locality.
- **Incremental computation:** No incremental mode for `parallel_bfs` — every query walks from source. An incremental frontier would amortise.
- **Build artifacts:** No wheels; no SBOM; no sdist. Loss of commercial-readiness.
- **CI:** Underutilised — runs only 1 matrix combination for benchmark; no caching; no coverage diff; no security scan.
- **Documentation:** 22 files; only 19 in nav; examples not wired. 30 minutes of work to fix.
- **Examples:** 5 working scripts, all isolated. Could form a tutorial.
- **Tests:** 466 passing, 14 failing. CI doesn't gate on test failures.
- **Benchmarks:** `asv` configured but only one trivial benchmark runs in CI. Real numbers not tracked.
- **GitHub Actions:** 5 jobs; 1 runs benchmarks. Could split: `lint`, `typecheck`, `test-fast`, `test-slow`, `bench`, `docs`, `security`, `wheel-build`, `docker-build`, `release`.
- **Developer feedback:** No issue templates, no PR template. Onboarding friction.
- **Community contributions:** None to date — repo is single-author.

# 8. Technology Evolution Roadmap

| Path | Adopt? | Reasoning |
|---|---|---|
| GPU acceleration | Yes, behind `reachq[accel]` | SuiteSparse:GraphBLAS via `pygraphblas`. |
| Distributed execution | Yes, behind `reachq[accel]` | `ray` or `dask` actor pattern; one actor per pivot. |
| Incremental computation | Yes | The paper explicitly studies dynamic reachability. `StreamingShortcutSet` is the entry point. |
| Streaming algorithms | Yes | See `StreamingShortcutSet`. Needs proper implementation. |
| Dynamic graphs | Yes | Adjacent to streaming. |
| Cloud-native execution | Yes | Docker image exists; needs K8s deployment example. |
| GraphBLAS | Yes | The natural data model for sparse Boolean matrix work. |
| Apache Arrow | Yes | For serialising shortcut sets across processes (replace JSON for large H). |
| Rust extensions | Yes, behind `reachq[accel]` | `pyo3` or `maturin` for the per-pivot BFS kernel. |
| WebAssembly | No | Wrong target — Python is the user-facing layer. |
| Python bindings | Already have | n/a. |
| Plugin architecture | Yes | `entry_points(group="reachq.backends")` in pyproject; backends register themselves. |
| AI-assisted development | Opt-in | Add a `copilot-instructions.md` and a `CONTRIBUTING.md` section on AI usage. |
| Automatic verification | Yes | `pytest --doctest-modules` is already on; extend with `hypothesis` profile. |
| Property-based testing | Yes | `Hypothesis` strategies for graph invariants. Already partially done. |
| Formal verification | Long-term | Lean/Coq formalisation of paper theorems. Aspirational. |
| Adaptive optimization | Yes | `density_aware_constant`, `adaptive_beta` already exist. Bundle into a `Tuner` class. |

# 9. Proposed Architecture

### Module map

```
reachq/                          # facade package — re-exports core stable API
├── __init__.py                  # re-exports from reachq_core
├── py.typed

reachq_core/                     # stable algorithm library
├── __init__.py
├── graph.py                     # Digraph, WeightedDigraph, contract_sccs
├── reachability.py              # BFS, SCC, parallel_bfs, topological_sort
├── shortest_paths.py            # Dijkstra, A*, truncated Dijkstra
├── shortcut_set.py              # JLS + TC-pruning
├── hopset.py                    # CFR + TruncSSSP-pruning
├── transitive_closure.py        # sparse Boolean matmul
├── numpy_bfs.py                 # CSR BFS kernels
├── serialization.py             # JSON + Arrow
├── spectrum.py                  # adjacency eigenvalues
├── generators.py                # graph generators
├── refinements.py               # RefinementConfig + presets
├── backends/
│   ├── __init__.py              # Backend protocol
│   ├── threads.py
│   ├── processes.py
│   ├── ray_backend.py           # reachq[accel]
│   └── noop.py
├── logging_config.py
├── work_depth.py                # theoretical accounting
├── span_profiler.py             # empirical profiling
├── invariants.py                # assert_*
└── py.typed

reachq_research/                 # opt-in research algorithms
├── __init__.py                  # enable() lifecycle
├── streaming.py                 # StreamingShortcutSet (proper impl)
├── approximation.py             # greedy_shortcut_set + (1+ε)
├── adaptive_beta.py
├── iterate.py
├── sparsify.py
├── sparsify_hop.py
├── fix_resample.py
├── lower_bound.py
├── closed_form.py
└── py.typed

reachq_accel/                    # optional Rust/Cython kernels
└── ...

benchmarks/
├── jls_construction.py          # asv suite
├── hopset_construction.py
├── sparsify.py
├── iterate.py
├── snap.py                      # SNAP-based benchmark
└── suite.py                     # orchestration

examples/
├── gnn_preprocessing.py
├── rag_reranking.py
├── compiler_inlining.py
├── social_network.py
└── bioinformatics.py

scripts/                         # CLI entry points
├── __init__.py
├── cli.py                       # `reachq` console_script
├── download_datasets.py
├── reproduce_results.py
├── run_ablation.py
└── eval_*.py

docs/
├── index.md
├── getting-started.md
├── architecture.md
├── algorithms.md
├── invariants.md
├── work-depth.md
├── benchmarks.md
├── deployment.md
├── faq.md
├── INSPIRED_BY.md
├── PAPER.md
├── GLOSSARY.md
├── REFERENCE.md                # auto-generated by mkdocstrings
├── START_HERE.md
├── WHY.md
├── notes_correctness.md
├── lit_survey.md
├── howto/                      # new
│   ├── parallelism.md
│   ├── reproducibility.md
│   ├── custom-backends.md
│   └── custom-graph-types.md
└── explanations/                # new
    ├── paper.md                # alias of PAPER.md
    ├── streaming_proof.md
    ├── approximation_analysis.md
    └── spectral_fixtures.md

tests/
├── core/                        # split by module
│   ├── test_graph.py
│   ├── test_reachability.py
│   ├── test_shortcut_set.py
│   └── ...
├── research/                    # tests for reachq_research
└── integration/                 # tests across layers
```

### Public API stability

| Symbol | Stability | Doc page |
|---|---|---|
| `Digraph`, `WeightedDigraph` | stable | yes |
| `build_shortcut_set_for_reachability`, `build_hopset_for_sssp` | stable | yes |
| `Flags` → `RefinementConfig` (with deprecation alias) | stable | yes |
| `work_depth.WorkDepthAccountant`, `work_depth.SpanProfiler` | stable | yes |
| `reachq.research.*` | experimental | yes |
| `reachq_accel.*` | experimental, optional | yes |

### Dependency direction

```
reachq (facade)
  └─ reachq_core
       └─ reachq_research (optional)
       └─ reachq_accel (optional)
```

No reverse imports; `reachq_core` cannot import from `reachq_research`.

### Configuration

Replace `Flags` (9 booleans) with:

```python
class RefinementConfig:
    adaptive_sampling: bool = True
    label_compress: bool = True
    skip_condense: bool = True
    hop_bounded_bfs: bool = True
    degree_ordered_pivots: bool = True
    tight_tc_trigger: bool = True
    skip_trivial_part: bool = True
    enable_tc_pruning: bool = True
    backend: str = "threads"
    backend_workers: int = 0  # 0 == os.cpu_count()

    @classmethod
    def PAPER_BASELINE(cls) -> "RefinementConfig": ...
    @classmethod
    def ALL_ON(cls) -> "RefinementConfig": ...
    @classmethod
    def MINIMAL(cls) -> "RefinementConfig": ...
```

### Plugin system

`pyproject.toml` declares `entry_points(group="reachq.backends")`. Third parties can register custom backends.

### Error handling

All public functions raise specific exceptions (defined in `reachq.core.errors`):
- `ReachqValueError` for invalid input.
- `ReachqTypeError` for type mismatches.
- `ReachqGraphError` for invalid graph state (cycles in DAG-only construction, etc.).
- `ReachqBackendError` for backend failures.

### Logging

Centralised `logging_config` (already exists). Add per-call tracing via `contextvars`:

```python
with reachq.core.trace.trace("shortcut_set", n=graph.num_vertices()):
    H, beta = build_shortcut_set_for_reachability(g)
```

`trace()` emits start/end markers with timing; backend picks logger / OpenTelemetry.

### Telemetry

Counter interface: `reachq.core.metrics.inc_counter(name)` and
`record_histogram(name, value)`. No-ops by default; call
`reachq.core.metrics.enable_metrics()` to activate, and read current values
via `reachq.core.metrics.snapshot()`.

### Observability

- `reachq.core.trace.trace` already exists as the entry/exit context manager.
- `reachq.core.metrics.snapshot()` already returns counter/histogram stats;
  a future `snapshot(graph)` variant could add graph stats `(n, m,
  max_in_deg, max_out_deg, num_sccs, n_strongly_regular, ...)` for dashboards.

# 10. Performance Optimization Plan

| Optimisation | Where | Expected gain | Effort |
|---|---|---|---|
| Index `shortcut_index` once in `sparsify_shortcut_set` | `reachq/sparsify.py` | 10–100× for large `\|H\|` | 1 day |
| Use `set` instead of `dict[set]` for adjacency reads | `reachq/graph.py:edges()` | 1.2× | 1 hour |
| Vectorise SCC via Tarjan's algorithm in Cython | `reachq/reachability.py:strongly_connected_components` | 2–5× | 1 week |
| Hoist `csr_data = build_csr_pair(graph)` to once per top-level call | `reachq/shortcut_set.py` | 1.2× | 1 hour |
| Use `numpy.unique` instead of Python `set` for pivot IDs | `reachq/shortcut_set.py` | 1.5× | 1 day |
| Replace `dict.setdefault` with `collections.defaultdict` | `reachq/research/streaming.py` | 1.3× | 1 hour |
| Move `compute_r_plus` / `compute_r_minus` to numpy CSR BFS in the JLS pivot loop | `reachq/shortcut_set.py` | 3–5× for n ≥ 1000 | 3 days |
| Parallelise CFR (the `processes` mode properly) | `reachq/hopset.py` | 2–4× on 4 cores | 3 days |
| Pre-allocate adjacency in `to_csr` | `reachq/graph.py:to_csr` | 1.1× | 1 hour |
| `frozenset` instead of `set` for label keys | `reachq/shortcut_set.py:partition_by_labels` | 1.05× | 2 hours |
| Per-call RNG seed for parallel pivot dispatch | `reachq/parallel.py` | removes correctness concern | 2 days |

**Total expected speedup without changing algorithms: 10–50× on dense SNAP inputs.**
**With Cython/Numba: 50–200×.**

# 11. Open Source Readiness Review

| Aspect | Status | Action |
|---|---|---|
| README | Has badges, quickstart, citation; missing ROADMAP and "Performance" stability table | Add. |
| Architecture docs | Single `architecture.md` | OK. |
| API reference | `mkdocstrings` configured but not wired for `reachq_core` classes | Wire. |
| Examples | 5 scripts | Link from nav. |
| Tutorials | 5 notebooks | Link from nav; convert to mkdocs. |
| CONTRIBUTING.md | Present | Update with new architecture. |
| CODE_OF_CONDUCT.md | Present (Contributor Covenant v2.1) | OK. |
| SECURITY.md | Present | OK. |
| CHANGELOG.md | Keep-a-Changelog format | OK. |
| ROADMAP.md | Partial (in `docs/PAPER.md`) | Promote. |
| Issue templates | `.github/ISSUE_TEMPLATE/` exists? | Check & verify. |
| PR template | `.github/PULL_REQUEST_TEMPLATE.md` exists? | Check & verify. |
| Discussion forum | None | Optional. |
| Discord/Slack | None | Optional. |
| Funding | `FUNDING.yml` exists? | Check. |
| Citation | BibTeX block in README | OK. |
| Release process | None documented | Document `make release` flow. |
| Wheels | None | cibuildwheel already configured; needs to run. |
| SBOM | None | Add `cyclonedx-py` step. |
| Badges | PyPI, CI, license, stars | OK. |
| "Good first issues" label | None | Add. |

# 12. Enterprise Readiness Review

- **LTS policy:** Document a 2-year LTS for `reachq_core` stable API.
- **Deprecation policy:** Use `DeprecationWarning`; `__deprecated__ = ("use X instead",)` markers; `reachq.compat` shims.
- **API stability:** Semver; `pyproject.toml` declares `version = "0.8.0"`; `reachq/__init__.py` re-exports the stable surface.
- **Compatibility matrix:** Document CPython 3.9–3.13, numpy ≥ 1.21, scipy ≥ 1.10.
- **SLI/SLO:** "All paper-lemma tests pass on `tests/test_paper_lemmas.py` with ≥ 95% confidence over 100 seeds."
- **Compliance:** License (MIT), SECURITY.md, SBOM.
- **Observability:** `trace()`, `metrics` opt-in.
- **On-prem / cloud:** Docker image; `pip install reachq` works everywhere.
- **Support channels:** GitHub Issues, Discussions.
- **Backup policy:** GitHub tags + signed wheels.

# 13. Research Readiness Review

- **Reproducibility:** Every script accepts `--seed`; `reproduce_results.py` writes `hardware.json`; need to add a CI job that runs `make reproduce` on a Docker image and checks the CSV against `docs/expected/`.
- **Versioning of research artifacts:** Research modules should follow `reachq_research.__version__` independently.
- **Paper cross-references:** `docs/INSPIRED_BY.md`, `docs/PAPER.md`, `docs/notes_correctness.md` already exist. Add `docs/PAPER.pdf` (compiled from markdown) for arXiv upload.
- **Empirical claims:** `results/summary.md` and `results/ablation.csv` exist; their freshness depends on whoever last ran the scripts. Add a CI job that re-runs them on every release.
- **Proof artefacts:** `docs/streaming_proof.md` and `docs/approximation_analysis.md` are sketches; mark them as "not formal proofs" in the preamble.
- **Counterexample search:** `scripts/counterexample_search.py` exists; document when it was last run.

# 14. Ranked Improvement Backlog

## Quick Win (≤ 1 day)

1. Wire `examples/` and `notebooks/` into mkdocs nav. *Already partially done.*
2. Move stale README references to deleted doc files. *Already done.*
3. Replace `print()` in remaining scripts. *Already done.*
4. Add `parallel_workers` parameter to `build_hopset_for_sssp`. *Already done (informational).*
5. Add CI job to lint doc links.
6. Add `pytest --doctest-modules` to CI.
7. Make `reachq` console_script. *Already done.*
8. Fix 14 pre-existing test failures (small bugs, not architectural).
9. Add `tests/test_self_loop.py` exercising the asymmetry between `add_edge` (accepts) and `add_undirected_edge` (rejects).
10. Update `docs/streaming_proof.md` and `docs/approximation_analysis.md` to mark them as sketches.

## Medium Effort (1–5 days)

11. Replace `Flags` with `RefinementConfig` (preserves backward compat).
12. Index `shortcut_index` once in `sparsify_shortcut_set`.
13. Parallelise CFR (threads-only) — make the existing `_cfr_recursive` loop dispatch via `ParallelContext`.
14. Make `processes` mode work via `multiprocessing.initializer` (no module globals).
15. Split `jls_with_tc_pruning` into `_sample`, `_partition`, `_recurse`, `_tc_prune`.
16. Add `SpanProfiler` ↔ `trace()` context manager equivalence.
17. Add `reachq.compat` module with deprecation shims.
18. Move research modules from top-level into `reachq_research/`.
19. Make `parallel_workers` parameter part of `RefinementConfig` (not a separate arg).
20. Add `pyproject.toml` extras: `[accel]`, `[research]`, `[docs]`, `[dev]`.
21. Build wheels via cibuildwheel in CI; upload to a private index for testing.
22. Add `reachq doctest` CLI to validate all doctests.
23. Convert `examples/` into `mkdocs` how-to guides.

## Major Refactor (1–3 weeks)

24. Split `reachq` package into `reachq_core` + `reachq_research` + `reachq` facade.
25. Add `Backend` protocol and refactor `parallel.py` around it.
26. Add Cython/Numba kernels in `reachq_accel/`.
27. Replace `sparsify.py`'s O(|H|²) implementation.
28. Add `metrics` + `trace()` telemetry plumbing (already landed in `reachq.core.metrics` / `reachq.core.trace`).
29. Add `reachq.core.metrics.snapshot(graph)` with graph stats for observability (current `snapshot()` returns counter/histogram stats).
30. Add GraphBLAS backend behind `reachq[accel]`.
31. Add `reachq.core.io.arrow` binary serialisation (already landed: `dump_arrow` / `load_arrow`).
32. Migrate CI to `tox` matrix.
33. Add property-based test coverage for `sparsify` invariants.

## Research Project (1–6 months)

34. Proper `StreamingShortcutSet` with pivot-set maintenance.
35. (1+ε) approximation via Rado-Edmonds random sampling.
36. Distributed backend via `ray`.
37. Formal proofs in Lean/Coq for `reachq_core`'s soundness.
38. AI-assisted test generation: a `reachq-tests` tool that proposes adversarial graphs.
39. Empirical study of `|H|/n` vs spectral gap (already partial in `scripts/spectral_check.py`).
40. GPU-accelerated TC-pruning via SuiteSparse:GraphBLAS.

## Long-Term Vision

41. `reachq-graphblas` (Apache Arrow + SuiteSparse bindings).
42. `reachq-cloud` (Kubernetes operator for distributed BFS).
43. WASM build for in-browser graph exploration.
44. AI-driven auto-tuning of refinement flags per graph class.

# 15. 30-Day Roadmap

- Wire examples/ and notebooks/ into mkdocs.
- Fix 14 pre-existing test failures.
- Replace `Flags` with `RefinementConfig`.
- Split `jls_with_tc_pruning` into smaller functions.
- Index `shortcut_index` once in `sparsify`.
- Add `reachq doctest` CLI.
- Build wheels via cibuildwheel.
- Add `make release` flow.
- Set up GitHub issue + PR templates if missing.
- Document `RefinementConfig` and `Backend` protocol.

**Success metrics:**
- All CI green.
- 0 lint errors.
- 0 pre-existing test failures.
- `pytest --doctest-modules` passes for all public symbols.
- `mkdocs build --strict` passes.
- `asv` published numbers for n = 100, 1000, 10000.

# 16. 90-Day Roadmap

- Split into `reachq_core` / `reachq_research` / `reachq` facade.
- Add `Backend` protocol.
- Add `metrics` + `trace()` telemetry.
- Move research modules out of top-level.
- Implement proper `StreamingShortcutSet`.
- Implement (1+ε) approximation.
- Parallelise CFR properly.
- Cython kernel for per-pivot BFS (behind `reachq[accel]`).
- `reachq.core.io.arrow` (`dump_arrow` / `load_arrow`) already provides binary I/O.
- Add `reachq-accel` package on PyPI.
- Issue a 1.0.0 release.
- Add benchmark regression tracking (asv + GitHub Action).

**Success metrics:**
- 10× speedup on SNAP `cit-HepPh`.
- 5–10× speedup on SNAP `p2p-Gnutella31`.
- 0 open `enhancement` issues older than 90 days without progress.
- 5 external contributors merged.
- 100% public-API coverage in CI.

# 17. 12-Month Vision

- `reachq_core` 1.0 stable; `reachq_research` 0.5 experimental; `reachq_accel` 0.5 optional.
- 5+ research papers cite `reachq` (track via Google Scholar).
- 50+ stars on GitHub.
- 10+ external contributors.
- 1k+ monthly PyPI downloads.
- Distributed backend via `ray` ships.
- GraphBLAS backend ships.
- Formal proof of soundness ships (Lean or Coq).
- Conference talk or tutorial at a major venue (NeurIPS, ICML, SOSP).
- `reachq` is the canonical Python implementation of the cited papers.

**Success metrics:**
- ≥ 100 GitHub stars.
- ≥ 1k monthly downloads.
- ≥ 5 external contributors merged.
- ≥ 3 research citations.
- 0 critical bugs open > 30 days.

# 18. Top 10 Highest-Impact Changes

1. **Fix the 14 pre-existing test failures.** Without this, every other improvement is suspect — tests don't gate the codebase.
2. **Split `reachq` into `reachq_core` + `reachq_research` + `reachq` facade.** Removes the API-stability contradiction.
3. **Index `shortcut_index` once in `sparsify.py`.** Single biggest performance win in the repo; unblocks scaling to SNAP.
4. **Replace `Flags` with `RefinementConfig`.** Removes the Boolean-flag explosion.
5. **Make `processes` mode work via `multiprocessing.initializer`.** Closes the gap between advertised and actual behaviour.
6. **Wire examples/notebooks into mkdocs.** Discovery + onboarding.
7. **Implement (1+ε) approximation.** Closes the "advertised but not delivered" gap.
8. **Implement proper `StreamingShortcutSet`.** Same as above.
9. **Add `Backend` protocol + `ray` backend.** Future-proofs parallelism.
10. **Build wheels via cibuildwheel.** Closes the "single-platform Python library" gap that blocks commercial adoption.

# 19. Risks and Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| Splitting `reachq` into multiple packages breaks downstream users | High | Use `reachq` as facade that re-exports from `reachq_core`. Long deprecation cycle. |
| Cython/Numba dependency breaks `pip install reachq` for users without a compiler | Medium | Optional `[accel]` extra; pure Python is the default. |
| Parallelising CFR changes the RNG order, breaking seed-dependent tests | High | Add explicit per-pivot RNG seeding; update tests. |
| Property-based tests with `max_examples=200` slow CI to minutes | Low | Run in nightly job; `pytest -m "not slow"` for PRs. |
| Breaking change to `Flags` API | Medium | Keep `reachq.Flags` as a re-export of `RefinementConfig` (`Flags = RefinementConfig` in `reachq/__init__.py`). |
| Repository churn confuses existing contributors | Low | Clear `CONTRIBUTING.md`, `docs/START_HERE.md` rewrite, single-source-of-truth `docs/PAPER.md`. |
| Long-term maintenance burden of multiple sub-packages | Medium | Each sub-package has its own `pyproject.toml`; CI matrix; fewer cycles for the maintainer. |
| Research-grade code (TRIZ Inventive Principles 38, 39) requires Rust/Cython expertise | High | Document the requirement; recruit a co-maintainer; or accept performance ceiling. |

# 20. Final Repository Score

| Dimension | Score | Reasoning |
|---|---|---|
| Repository purpose clarity | 9/10 | Clear; cited paper, scope, contribution. |
| Architecture | 4/10 | Single-package layout; research mixed with core; `reachq.research` half-empty. |
| Algorithms & correctness | 8/10 | Four bug fixes documented and regression-tested. |
| Performance | 4/10 | O(\|H\|²) sparsify; no real parallelism; no accel layer. |
| Memory | 5/10 | Adjacency OK; COO set allocations OK; shortcut_index rebuilt per call. |
| Parallelism | 3/10 | Half-wired `ParallelContext`; processes mode broken. |
| API design | 6/10 | Small core API; Flags explosion; research API scattered. |
| Type safety | 4/10 | 14 mypy errors; not strict. |
| Testing | 5/10 | 466 pass; 14 fail; 1 xfail; coverage not enforced. |
| Reproducibility | 6/10 | Seeds everywhere; `hardware.json`; but "sha256 verification" is a misnomer. |
| Documentation | 7/10 | 22 .md files; 19 in nav; mkdocs configured; examples isolated. |
| Benchmarking | 5/10 | `asv` configured but only 1 trivial benchmark runs in CI. |
| CI/CD | 5/10 | 5 jobs; no caching; no coverage gate; benchmark trivially executed. |
| Packaging | 6/10 | Pure Python + numpy + scipy; no wheels; no SBOM. |
| Open-source hygiene | 6/10 | LICENSE, SECURITY, CONTRIBUTING, CHANGELOG present; no ROADMAP, no issue templates verified, no LTS policy. |
| Research reproducibility | 6/10 | Seeds + hardware.json; no CI re-run; PDF missing. |
| Enterprise readiness | 3/10 | No wheels, no SBOM, no LTS, no security scanning. |
| Extensibility | 5/10 | No plugin system; no Backend protocol; no `reachq[accel]`. |
| Developer experience | 6/10 | Tests run; doctests pass; but onboarding docs sparse. |

**Weighted total: 56/100.**

The repository is at the "research code, transitioning to library" stage. The next 90-day plan elevates it to ~75; the 12-month vision targets ~90. The dominant bottlenecks are (1) the test failures (gates everything), (2) the lack of real parallelism (advertised, not delivered), and (3) the package layout (research mixed with core).
