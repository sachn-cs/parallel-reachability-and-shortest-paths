# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (test fixtures from Papers 2/3 — algebraic graph theory)

- `petersen_graph()`, `paley_graph(q)`, `shrikhande_graph()`,
  `hamming_graph(d, q)` in `prspnsd/generators.py`. Canonical graphs
  from the algebraic graph theory literature with known structural
  properties. The rook's graph (K₄ □ K₄) substitutes for the proper
  Shrikhande Cayley construction since both share parameters
  (16, 6, 2, 2). The Clebsch graph is documented as omitted rather
  than shipped broken (the correct construction requires Cayley
  tables on Z₂⁵ / {x ~ complement(x)}).
- `Digraph.add_undirected_edge(u, v)`: adds both directions, counts
  one edge. Required for the symmetric generators.
- `prspnsd/spectrum.py`: `spectrum(g)` and `spectral_gap(g)` helpers
  for the cross-check script.
- `docs/spectral_fixtures.md`: explains the test fixtures and what's
  deliberately not here.

### Added (Fix/Resample variant — Paper 1)

- `prspnsd/fix_resample.py`: experimental Fix/Resample variant
  inspired by Assadi–Yazdanyar's dynamic coloring algorithm.
  Static analogue only — the dynamic-update bounds from Paper 1 do
  not apply to our codebase. Honest framing as an experimental
  baseline.
- `scripts/eval_fix_resample.py`: empirical comparison vs JLS.
  Empirical finding across 9/9 fixtures: Fix/Resample produces
  smaller `|H|` (16% of JLS on average) but with a looser hopbound
  (~3 vs JLS's ~1). Trade-off documented in `docs/fix_resample.md`.
- `docs/fix_resample.md`: scope, mechanism, empirical result, and the
  trade-off interpretation.

### Added (spectral cross-check)

- `scripts/spectral_check.py`: runs each named fixture through the JLS
  shortcut-set construction and reports `|H|`, `β`, spectral gap. The
  result confirms that the construction's `|H|` depends on density ρ
  rather than directly on the spectrum.

### Bug fixes

- `petersen_graph()`: corrected inner cycle order to pentagram
  `(5,7),(7,9),(9,6),(6,8),(8,5)` matching NetworkX. Previously
  produced a non-isomorphic 3-regular graph.
- `hamming_graph()`: fixed `_int_to_base_q` / `_base_q_to_int`
  inconsistency (different digit orderings). Hamming graphs now
  produce the correct eigenvalues.
- `paley_graph()`: documentation and tests now reflect the actual
  eigenvalues `(-1 ± √q)/2` rather than the integer placeholder.

### Tests

- `tests/test_generators.py`: 8 new tests for SRG / Hamming
  generators (degree, edge count, feasibility, error paths).
- `tests/test_spectrum.py`: 6 tests verifying generator spectra
  match published values.
- `tests/test_fix_resample.py`: 8 tests (soundness on 4 fixtures,
  reproducibility, edge cases, threshold control).
- Total: 352 tests pass (was 346).

### Changed

- README roadmap now lists test-fixture work as Done in v0.8.0.

---

## [0.7.0] - 2026-07-23

### Added

- `scripts/download_datasets.py`: idempotent SNAP dataset downloader with sha256 verification.
- `scripts/reproduce_results.py`: end-to-end benchmark reproducer with hardware auto-detection,
  sampling ladder, SNAP benchmarks, and Markdown summary. Writes `results/{scaling,snap}.csv`
  and `results/{summary.md,hardware.json}`.
- `prspnsd.shortcut_set.Flags`: dataclass of toggles for every algorithmic refinement.
  Pass via the `flags` keyword to `jls_with_tc_pruning`, `build_shortcut_set_for_reachability`,
  `cfr_hopset`, `cfr_with_truncsssp_pruning`, `build_hopset_for_sssp`.
- Algorithmic improvements (each toggleable, all on by default):
  1. Adaptive sampling probability (observes part sizes from previous level).
  2. Label compression: pivot-set labels instead of strings (reduces memory and hashing).
  3. Skip SCC condensation on already-DAG inputs (trivial condensation fast path).
  4. Hop-bounded pivot BFS at the wrapper's `beta` estimate.
  5. Degree-ordered pivot iteration (cheap BFS first).
  6. Skip-trivial-partition guard (no recursion when partition is single-part).
  7. Tightened TC-pruning trigger by work comparison vs sampling cost.
- `tests/test_algorithmic_improvements.py`: parametrized correctness tests with each flag
  toggled off, plus a networkx cross-check on shortcut-set reachability.
- `docs/algorithmic_improvements.md`: technical writeup of the seven refinements.

### Changed

- **Bug fix**: `prspnsd.transitive_closure.transitive_closure_matrix` now uses
  `scipy.sparse` Boolean matmul. The previous dense `np.zeros((n, n))` OOMed above ~50k
  vertices; sparse stays O(n + m) memory and scales to web-Google (n=875k).
- **Bug fix**: `prspnsd.numpy_bfs.csr_reachable_forward` had a Python `for i in
  range(frontier.size)` loop inside the frontier expansion, defeating the numpy fast path.
  Replaced with a vectorised `np.repeat` + `cumsum` gather.
- **Bug fix**: SCC-representative translation in `build_shortcut_set_for_reachability`
  and `build_hopset_for_sssp` was indexing `scc_rep[u_idx]` even when the trivial-condensation
  path was active (where `u_idx` is already a vertex, not an SCC index). This caused
  phantom shortcuts to leak into `parallel_bfs`. Fixed by branching on `trivial`.
- **Bug fix**: TC-pruning leaked self-loops into the shortcut set, breaking parallel_bfs.
  Filtered at the call site.
- **Bug fix**: `prspnsd.hopset` previously rebuilt `graph.reversed()` once per pivot inside
  the per-pivot loop; now hoisted once per recursion level.
- `jls_shortcut_set` (no-pruning baseline) is now a thin compatibility wrapper around
  `jls_with_tc_pruning` with `enable_tc_pruning=False`. The separate code path that
  existed previously has been deleted (along with its 4 `DEBUG print(...)` blocks).
- `prspnsd.shortcut_set` multiprocessing pivot-parallelisation path removed. It was
  half-wired (module-level `_worker_*` globals + `assert graph is not None` after use)
  and defaulted to `workers=1` anyway. Replaced with a clean CSR-or-Python-BFS branch.

### Removed

- `prspnsd/shortcut_set.py:45-119` original `jls_shortcut_set` body (kept as a one-line
  wrapper above).
- 4× `print(f"DEBUG level=...", flush=True)` blocks in the shortcut-set hot path.
- Half-wired `multiprocessing` pivot-parallelisation scaffold in `prspnsd/shortcut_set.py`
  (`_pivot_bfs_python`, `_pivot_bfs_csr`, `_process_pivots_worker`, `_init_worker_csr`,
  `_init_worker_graph`, the `_worker_*` globals).

### Known limitations

- The implementation produces shortcut sets significantly larger than the paper's
  worst-case bound `O(m * rho + n * rho^2)` because (a) the sampling constant `C=10`
  is not auto-tuned per graph, (b) the hop-bounded BFS bound `n^(omega/(2omega-2))`
  is a coarse upper bound. See `docs/algorithmic_improvements.md` for a discussion
  and the ablation flags `--no-adaptive-sampling` / `--no-hop-bounded-bfs`.
- On SNAP datasets larger than ~60k vertices the construction can take 1–4 minutes
  and produce shortcut sets in the hundreds of millions. See `results/snap.csv`.
- `web-Google` (n=875k) is currently out of reach for a pure-Python single-process
  build. The `transitive_closure_matrix` fix unblocks the memory ceiling; wall-clock
  remains the bottleneck.

## [0.5.0] - 2026-07-22

### Added

- Graph base class with template method pattern (`initialize_vertex`, `iterate_edges_from`, `store_edge`, `create_empty`) ([e4ba761])
- Covariant return types on Digraph/WeightedDigraph overrides ([e4ba761])
- ~47 new tests across generators, graph, invariants, serialization, and work_depth modules; coverage 94% → 97% ([582442b])
- CONTRIBUTING.md with development guidelines ([#4])
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1) ([#4])
- SECURITY.md with vulnerability reporting policy ([#4])
- CHANGELOG.md for tracking changes ([#4])
- .editorconfig for consistent formatting ([#4])
- .gitattributes for line ending normalization ([#4])
- .env.example documenting optional configuration ([#4])
- GitHub issue templates for bug reports and feature requests ([#4])
- GitHub pull request template ([#4])
- Dependabot configuration for automated dependency updates ([#5])
- GitHub funding configuration ([#5])
- Documentation: getting-started.md, architecture.md, deployment.md, faq.md ([#4])

### Changed

- Extracted `partition_by_labels` and `contract_sccs` into graph.py for co-location with graph structures ([9e37747], [f03d9d0])
- Indexed shortcut edges by source vertex in `parallel_bfs` for O(1) edge lookup ([9b30ed0])
- Indexed hopset edges by source vertex in `shortest_path_hopbound` for O(1) edge lookup ([a2ba6ba])
- Renamed all underscore-prefixed identifiers to public names across 14 files (~78 sites) ([0abc514])
- Extracted Graph → Digraph → WeightedDigraph inheritance hierarchy with template hooks ([e4ba761])
- Graph base class provides shared operations (induced_subgraph, reversed, copy) via template method pattern ([e4ba761])
- Updated architecture, algorithms, index, and FAQ docs to reflect OO hierarchy and O(1) lookups
- Rewrote README.md with improved structure, badges, and comprehensive documentation ([#4])
- Updated pyproject.toml with corrected metadata and project URLs ([#4])
- Improved CI workflow with dependency caching and documentation job fixes ([#4])
- Synced package version with git tags (0.4.0) ([#4])

### Fixed

- Integer overflow in matrix transitive closure (`np.int8` → `np.int32`) ([203a75c])
- mypy `python_version` updated to 3.12 for runtime numpy stub compatibility ([70f8170])
- Version mismatch between \_\_init\_\_.py (0.1.0) and git tags (0.4.0) ([#4])
- CI docs job was a no-op (mkdocs not installed) ([#4])

[Unreleased]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/releases/tag/v0.1.0
[#4]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/pull/4
[#5]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/pull/5
