<p align="center">
  <h1 align="center">reachq</h1>
  <p align="center"><em>reachq: graph reachability, queryable.</em></p>
  <p align="center">Pure-Python reimplementation of the JLS shortcut-set and CFR hopset constructions. Insertion-order vertex indexing, deterministic cross-process reproducibility, Boolean-semiring transitive closure.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/parallel-reachability-and-shortest-paths/ci.yml?branch=master" alt="CI"></a>
    <a href="https://pypi.org/project/reachq/"><img src="https://img.shields.io/pypi/v/reachq" alt="PyPI"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/stargazers"><img src="https://img.shields.io/github/stars/sachncs/parallel-reachability-and-shortest-paths" alt="Stars"></a>
  </p>
</p>

## What this is

A pure-Python reimplementation of two parallel graph algorithms from:

> **"Parallel Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth"**
> Ashvinkumar, Bernstein, Probst Gutenberg, Saranurak. [arXiv:2605.03892](https://arxiv.org/abs/2605.03892).

See [`docs/INSPIRED_BY.md`](docs/INSPIRED_BY.md) for the full disclaimer
about the relationship between `reachq` and the cited papers.

It also contains contributions layered on top of the cited work:

- **[`docs/PAPER.md`](docs/PAPER.md)** — the unified paper draft
  (historical; current claims about StreamingShortcutSet and
  greedy_shortcut_set do not match the implementation; see
  [`docs/limitations.md`](docs/limitations.md)).
- **[`docs/notes_correctness.md`](docs/notes_correctness.md)** — a
  corrigendum documenting four bugs found and fixed in the reference
  implementation.
- **[`docs/spectral_fixtures.md`](docs/spectral_fixtures.md)** — test
  fixtures from Papers 2/3 (SRG, Hamming, Paley, Petersen).
- **[`docs/fix_resample.md`](docs/fix_resample.md)** — experimental
  Fix/Resample variant from Paper 1.

## When to use reachq

Use reachq when you want a Python library that:

- Computes shortcut sets for parallel reachability.
- Computes hopsets for approximate shortest paths.
- Has reproducible benchmarks and tests.

## When to use something else

If you want a general-purpose graph library with full algorithms
(BFS, Dijkstra, SCC, etc.), use `networkx` or `igraph` and call
reachq only for the specific parallel-reachability shortcuts.

## Comparison

| feature | reachq | networkx | igraph |
|---|---|---|---|
| JLS shortcut set | yes | no | no |
| CFR hopset | yes | no | no |
| beta-hopbound-preserving sparsification | yes (small graphs) | no | no |
| streaming shortcut set | experimental prototype (no formal bound) | no | no |
| (1+ε) approximation | vanilla greedy (no formal guarantee) | no | no |
| full graph library | no (focused) | yes | yes |
| reproducible benchmarks | yes | partial | no |

---

## Installation

```bash
pip install reachq
# or
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths
cd parallel-reachability-and-shortest-paths
pip install -e ".[dev]"
```

**Requirements:** Python ≥ 3.10, `numpy` ≥ 1.21, `scipy` ≥ 1.10.
No JIT, no native extensions; the wheel is pure-Python.

---

## Quick start

```python
from reachq.shortcut import build_shortcut_set_for_reachability
from reachq.generators import random_dag
from reachq.reachability import bfs_reachability, parallel_bfs

g = random_dag(n=1000, edge_probability=0.1, random_seed=42)
shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)

src = next(iter(g.vertices()))
assert bfs_reachability(g, src) == parallel_bfs(g, src, shortcuts)
```

Disable any refinement:

```python
from reachq import RefinementConfig

shortcuts, beta = build_shortcut_set_for_reachability(
    g,
    omega=3.0,
    random_seed=42,
    flags=RefinementConfig(enable_tc_pruning=False, tight_tc_trigger=True),
)
```

Five more end-to-end applications live in [`examples/`](examples/):

- `gnn_preprocessing.py` — citation graph → PyG Data object.
- `rag_reranking.py` — passage-citation graph → pivot-reach ranking.
- `compiler_inlining.py` — IR graph → inlining candidate ranking.
- `social_network.py` — SNAP cit-HepPh → `|H|/|E|` ratio.
- `bioinformatics.py` — synthetic PPI → downstream-hub detection.

---

## Algorithmic refinements

The seven toggles on `RefinementConfig` (re-exported as
`reachq.Flags`); all default to on except `parallel`.

| Flag | Effect |
|---|---|
| `adaptive_sampling` | Adapt per-level sampling probability from observed part sizes. |
| `label_compress` | Store labels as `frozenset[int]` instead of `set[str]`. |
| `skip_condense` | Skip SCC condensation on DAG inputs. |
| `hop_bounded_bfs` | Use a hop-bounded BFS kernel in the pivot loop. |
| `degree_ordered_pivots` | Process pivots in ascending out-degree order. |
| `tight_tc_trigger` | Tighten the TC-pruning trigger by work comparison. |
| `skip_trivial_part` | Skip recursion when the partition is a single part. |
| `enable_tc_pruning` | Enable TC-pruning (Theorem 2's improvement). |
| `parallel` | When True, dispatch per-pivot BFS through a process pool with `parallel_workers > 1`. |

The `parallel_workers` parameter on `build_shortcut_set_for_reachability`
now dispatches per-pivot BFS through a process pool when
`flags.parallel=True`. The hopset path runs sequentially because
the per-pivot workload is a SSSP (GIL-bound in Python).
See [`docs/algorithms.md`](docs/algorithms.md) §"Refinement flags"
and [`docs/migration_0_9.md`](docs/migration_0_9.md).

---

## Tests

```bash
pytest                        # 575 passed + 1 xfailed (576 total)
pytest -m "not slow"          # skip slow tests
pytest --cov=reachq          # with coverage (currently 76%)
```

The lemma tests run 50 random seeds per invariant claim; failures
would indicate the lemmas don't hold empirically on the tested
graph class.

The current test count is in [`CHANGELOG.md`](CHANGELOG.md); do
not hard-code counts in user-facing docs.

---

## API summary

```python
from reachq import RefinementConfig as Flags, Digraph, WeightedDigraph
from reachq.shortcut import (
    build_shortcut_set_for_reachability,  # Theorem-2 wrapper
    jls_with_tc_pruning,  # direct recursion
)
from reachq.hopset import (
    build_hopset_for_sssp,  # Theorem-4 wrapper
    cfr_with_truncsssp_pruning,  # direct recursion
)
from reachq.reachability import (
    bfs_reachability,
    parallel_bfs,
    strongly_connected_components,
    topological_sort,
)
from reachq.shortest_paths import (
    dijkstra,
    shortest_path_hopbound,
    truncated_dijkstra,
    compute_d_ball,
    compute_d_ancestors,
    compute_d_descendants,
    UNREACHABLE,
)
from reachq.closure import (
    TransitiveClosureBudgetError,
    transitive_closure_boolean,
    transitive_closure_brute_force,
)
from reachq.generators import (
    random_dag,
    weighted_random_dag,
    layered_dag,
    dense_graph,
    graph_with_sccs,
    path_graph,
    cycle_graph,
    grid_graph,
    petersen_graph,
    paley_graph,
    shrikhande_graph,
    shrikhande_cayley,
    hamming_graph,
)
from reachq.io import (
    dump,  # digraph -> JSON string
    load,  # JSON string -> digraph
    weighted_dump,
    weighted_load,
)
```

Full API reference: [`docs/REFERENCE.md`](docs/REFERENCE.md) (auto-
generated by mkdocstrings from the actual signatures).

---

## Project structure

```
parallel-reachability-and-shortest-paths/
├── reachq/                          # Main package
│   ├── __init__.py                  # Public API + __version__
│   ├── core/                        # Always-imported library layer
│   │   ├── algorithm.py             # JLS + TC-pruning (Theorem 2)
│   │   ├── bfs.py                   # Vectorised CSR BFS
│   │   ├── config.py                # RefinementConfig + logging
│   │   ├── csr.py                   # CSR pair builder
│   │   ├── generators.py            # Deterministic generators + SNAP loader
│   │   ├── graph.py                 # Digraph, WeightedDigraph
│   │   ├── hopset.py                # CFR + TruncSSSP-pruning (Theorem 4)
│   │   ├── invariants.py            # Theorem-oriented validators
│   │   ├── io/                      # JSON + Arrow + NetworkX
│   │   ├── metrics.py               # Opt-in counters and histograms
│   │   ├── predictor.py             # Heuristic graph-property estimators
│   │   ├── prune.py                 # TC-pruning (extracted)
│   │   ├── reachability.py          # BFS, SCC, topological sort
│   │   ├── shortest_paths.py        # Dijkstra, A*, truncated SSSP
│   │   ├── snapshot.py              # Frozen graph snapshot dataclass
│   │   ├── spectrum.py              # Eigenvalues and spectral gap
│   │   ├── tc.py                    # Sparse Boolean matmul TC
│   │   ├── trace.py                 # Contextmanager tracing
│   │   ├── tuner.py                 # auto_tune RefinementConfig
│   │   ├── work_depth.py            # PRAM work/depth accounting
│   │   └── backends/                # Backend Protocol + ParallelContext
│   ├── research/                    # Opt-in refinements (off-paper)
│   ├── accel/                       # Experimental Cython/Rust/Numba (see docs/accel.md)
│   ├── cli/                         # Console-script entry point
│   └── proto/                       # Duck-typed Protocols
├── tests/                            # 576 tests
├── scripts/                          # CLI / benchmark / reproduction
├── docs/                             # 24 docs (see docs/index.md)
├── examples/                         # 5 end-to-end applications
├── benchmarks/                       # asv micro-benchmarks
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── README.md
└── LICENSE
```

The docs list is in [`docs/index.md`](docs/index.md). See also
[`docs/architecture.md`](docs/architecture.md) for the per-module
responsibility table.

---

## Documentation

```bash
pip install -e ".[dev]"
mkdocs build --strict        # verify the docs build cleanly
mkdocs serve                  # preview at http://127.0.0.1:8000
```

The documentation site is built by CI on every PR but is not yet
deployed to GitHub Pages (see the Roadmap).

Notable entry points:

- [`docs/START_HERE.md`](docs/START_HERE.md) — three routing paths
  (use / understand / extend).
- [`docs/getting-started.md`](docs/getting-started.md) — install +
  first construction.
- [`docs/algorithms.md`](docs/algorithms.md) — algorithm
  descriptions, parameter selection, RefinementConfig flags.
- [`docs/architecture.md`](docs/architecture.md) — module responsibilities
  + dependencies.
- [`docs/REFERENCE.md`](docs/REFERENCE.md) — full API reference.
- [`docs/limitations.md`](docs/limitations.md) — what is NOT implemented.
- [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — terminology.

---

## Known limitations

See [`docs/limitations.md`](docs/limitations.md) for the consolidated
list. The short version:

- **Process parallelism** is real for the JLS shortcut-set
  construction when `flags.parallel=True` and
  `parallel_workers > 1`. The hopset construction runs sequentially
  because the per-pivot workload is a SSSP (GIL-bound in Python).
- **No JIT / no native extensions.** Pure-Python wheel; the
  experimental Cython/Rust kernels in `reachq/accel/` are not
  built or shipped.
- **No formal (1+ε) approximation.** `greedy_shortcut_set` is a
  vanilla greedy.
- **No amortised streaming bound.** `StreamingShortcutSet` is a
  prototype; the O(log² n) per-insertion bound is not implemented.
- **`web-Google` (n=875k) is out of reach** for single-process
  Python.
- **Exact transitive closure** is inherently output-quadratic; the
  Boolean-semiring core respects an explicit `max_pairs` budget and
  raises `TransitiveClosureBudgetError` when exceeded.

---

## Roadmap

### Planned

- [ ] Cython port of the per-pivot BFS inner loop (for
      web-Google-scale inputs) — scaffolding exists under
      `reachq/accel/` but is not built or shipped (see
      [`docs/accel.md`](docs/accel.md)).
- [ ] Deploy the MkDocs site to GitHub Pages.
- [ ] Publish the cibuildwheel wheels to PyPI (`release.yml`
      currently publishes only the sdist).

### Deferred

- [ ] PRAM span for the *actual* parallel runtime (requires a
      real PRAM model; `SpanProfiler` measures sequential phases
      only).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For research questions, see
[`docs/PAPER.md`](docs/PAPER.md) for what's been proved and what's
empirical.

## Citation

```bibtex
@article{ashvinkumar2026parallel,
  title={Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
         Near-linear Work and Sub-square-root Depth},
  author={Ashvinkumar, Vikrant and Bernstein, Aaron and
          Probst Gutenberg, Maximilian and Saranurak, Thatchaphol},
  journal={arXiv preprint arXiv:2605.03892},
  year={2026}
}
```

For the refinements in this implementation:

```bibtex
@misc{reachq2026refinements,
  title={Algorithmic refinements for parallel reachability:
         tightened TC-pruning and hop-bounded pivot BFS},
  author={reachq contributors},
  year={2026},
  howpublished={\url{https://github.com/sachncs/parallel-reachability-and-shortest-paths}}
}
```

## License

[MIT](LICENSE) © 2026 Sachin
