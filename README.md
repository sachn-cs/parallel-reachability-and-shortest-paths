<p align="center">
  <h1 align="center">Parallel Reachability and Shortest Paths</h1>
  <p align="center">Pure-Python reimplementation of the JLS shortcut-set and CFR hopset constructions, with seven toggleable algorithmic refinements and four documented correctness fixes.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/parallel-reachability-and-shortest-paths/ci.yml?branch=master" alt="CI"></a>
    <a href="https://pypi.org/project/prspnsd/"><img src="https://img.shields.io/pypi/v/prspnsd" alt="PyPI"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/stargazers"><img src="https://img.shields.io/github/stars/sachncs/parallel-reachability-and-shortest-paths" alt="Stars"></a>
  </p>
</p>

## What this is

A pure-Python reimplementation of two parallel graph algorithms from:

> **"Parallel Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth"**
> Ashvinkumar, Bernstein, Probst Gutenberg, Saranurak. [arXiv:2605.03892](https://arxiv.org/abs/2605.03892).

It also contains three research contributions layered on top:

1. **[`docs/paper_refinements.md`](docs/paper_refinements.md)** — Two lemmas formalising algorithmic refinements of the JLS construction, with proofs and empirical tables.
2. **[`docs/notes_correctness.md`](docs/notes_correctness.md)** — A corrigendum documenting four bugs found and fixed in the reference implementation.
3. **[`docs/algorithmic_improvements.md`](docs/algorithmic_improvements.md)** — Engineering notes on seven refinements (the two formalised above, plus five engineering wins).
4. **[`docs/spectral_fixtures.md`](docs/spectral_fixtures.md)** — Test fixtures from Papers 2/3 (SRG, Hamming, Paley, Petersen) with honest scope notes.
5. **[`docs/fix_resample.md`](docs/fix_resample.md)** — Experimental Fix/Resample variant from Paper 1, including the empirical trade-off (smaller `|H|`, looser hopbound) vs JLS.

---

## Installation

```bash
pip install prspnsd
# or
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
cd parallel-reachability-and-shortest-paths
pip install -e ".[dev]"
```

**Requirements:** Python ≥ 3.9, `numpy` ≥ 1.21, `scipy` ≥ 1.10. No JIT, no native extensions.

---

## Quick start

```python
from prspnsd.generators import random_dag
from prspnsd.shortcut_set import build_shortcut_set_for_reachability
from prspnsd.reachability import bfs_reachability, parallel_bfs

g = random_dag(n=1000, edge_probability=0.1, random_seed=42)
shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)

src = next(iter(g.vertices()))
assert bfs_reachability(g, src) == parallel_bfs(g, src, shortcuts)
```

Disable any refinement:

```python
shortcuts, beta = build_shortcut_set_for_reachability(
    g, omega=3.0, random_seed=42,
    flags={"enable_tc_pruning": False, "tight_tc_trigger": True},
)
```

---

## Algorithmic refinements (paper contribution)

Two are formalised with proofs in [`docs/paper_refinements.md`](docs/paper_refinements.md):

| # | Refinement | Lemma | Default |
|---|---|---|---|
| 1 | Tightened TC-pruning trigger | Lemma 2.1 (soundness), Lemma 2.2 (size contribution) | on |
| 2 | Hop-bounded pivot BFS | Lemma 3.1 (hopbound preservation), Lemma 3.2 (work bound) | on |

Five more (data-structure and engineering wins) are documented in [`docs/algorithmic_improvements.md`](docs/algorithmic_improvements.md): adaptive sampling, label compression, trivial-condensation fast path, degree-ordered pivots, skip-trivial-partition guard.

---

## Reproducing results

```bash
# 1. Fetch SNAP datasets (idempotent, sha256-verified).
python scripts/download_datasets.py

# 2. Sampling ladder + SNAP benchmarks.
python scripts/reproduce_results.py
# Produces: results/scaling.csv, results/snap.csv, results/hardware.json, results/summary.md

# 3. Ablation over refinement flags.
python scripts/run_ablation.py --sizes 500 1000 --densities 0.1
# Produces: results/ablation.csv

# 4. Empirical tables for the paper (Lemmas 2 and 3).
python scripts/eval_refinements.py --sizes 500 1000 2000 --densities 0.05 0.1
# Produces: results/refinements.csv
```

Every script auto-detects hardware (CPU, RAM, Python, BLAS) and writes it to `results/hardware.json`. Each refinement can be disabled individually via `--no-*` flags.

---

## Tests

```bash
pytest                        # 304 tests
pytest -m "not slow"          # skip slow tests
pytest --cov=prspnsd          # with coverage
pytest tests/test_paper_lemmas.py -v   # the 22 empirical lemma tests
```

The lemma tests run 50 random seeds per invariant claim; failures would indicate the lemmas don't hold empirically on the tested graph class.

---

## API summary

```python
from prspnsd import Flags, Digraph, WeightedDigraph
from prspnsd.shortcut_set import (
    build_shortcut_set_for_reachability,  # Theorem-2 wrapper
    jls_with_tc_pruning,                  # direct recursion
    jls_shortcut_set,                     # wrapper, TC pruning off
)
from prspnsd.hopset import (
    build_hopset_for_sssp,                # Theorem-4 wrapper
    cfr_with_truncsssp_pruning,           # direct recursion
    cfr_hopset,                           # wrapper, TruncSSSP off
)
from prspnsd.reachability import (
    bfs_reachability, parallel_bfs, strongly_connected_components,
    topological_sort,
)
from prspnsd.shortest_paths import (
    dijkstra, shortest_path_hopbound, truncated_dijkstra,
    compute_d_ball, compute_d_ancestors, compute_d_descendants,
)
from prspnsd.transitive_closure import (
    transitive_closure_matrix, transitive_closure_brute_force,
)
from prspnsd.generators import (
    random_dag, weighted_random_dag, layered_dag, dense_graph,
    graph_with_sccs, path_graph, cycle_graph, grid_graph,
    petersen_graph, paley_graph, shrikhande_graph, hamming_graph,
)
from prspnsd.serialization import (
    digraph_to_json, digraph_from_json,
    weighted_digraph_to_json, weighted_digraph_from_json,
)
```

Full API reference: [`docs/algorithms.md`](docs/algorithms.md).

---

## Project structure

```
parallel-reachability-and-shortest-paths/
├── prspnsd/                          # Main package
│   ├── logging_config.py             # Centralised logging setup
│   ├── graph.py                      # Digraph, WeightedDigraph
│   ├── reachability.py               # BFS, SCC, topological sort
│   ├── shortest_paths.py             # Dijkstra, A*, truncated SSSP
│   ├── transitive_closure.py         # Sparse Boolean matmul TC
│   ├── shortcut_set.py               # JLS + TC-Pruning (Theorem 2)
│   ├── hopset.py                     # CFR + TruncSSSP-Pruning (Theorem 4)
│   ├── generators.py                 # Deterministic generators + SNAP loader
│   ├── numpy_bfs.py                  # Vectorised CSR BFS
│   ├── serialization.py              # JSON serialisation
│   ├── work_depth.py                 # PRAM work/depth accounting
│   └── invariants.py                 # Theorem-oriented validators
├── tests/                            # 304 tests
│   ├── test_paper_lemmas.py          # Empirical support for paper lemmas
│   ├── test_algorithmic_improvements.py   # Per-flag ablation tests
│   ├── test_numpy_bfs.py             # Vectorised BFS equivalence
│   ├── test_shortcut_set.py
│   ├── test_hopset.py
│   ├── test_reachability.py
│   ├── test_shortest_paths.py
│   ├── test_transitive_closure.py
│   ├── test_generators.py
│   ├── test_graph.py
│   ├── test_invariants.py
│   ├── test_serialization.py
│   ├── test_work_depth.py
│   └── test_benchmark_sanity.py
├── scripts/                          # CLI / benchmark / reproduction
│   ├── cli.py                        # argparse CLI
│   ├── download_datasets.py          # SNAP downloader
│   ├── reproduce_results.py          # Main benchmark reproducer
│   ├── run_ablation.py               # Per-flag ablation
│   ├── eval_refinements.py           # Empirical paper tables
│   ├── benchmark_large.py            # Original large-graph benchmark
│   ├── benchmark_reachability.py
│   ├── benchmark_shortest_paths.py
│   └── demo.py
├── docs/                             # Research + user documentation
│   ├── paper_refinements.md          # Paper draft (Lemmas 2.1, 2.2, 3.1, 3.2)
│   ├── notes_correctness.md          # Corrigendum on 4 bugs found
│   ├── algorithmic_improvements.md   # Engineering notes on 7 refinements
│   ├── algorithms.md                 # Algorithm descriptions
│   ├── architecture.md
│   ├── invariants.md
│   ├── work-depth.md
│   ├── benchmarks.md
│   ├── deployment.md
│   ├── getting-started.md
│   ├── faq.md
│   └── index.md
├── results/                          # Auto-generated, gitignored
│   ├── scaling.csv                   # Synthetic ladder
│   ├── snap.csv                      # SNAP datasets
│   ├── ablation.csv                  # Per-flag ablation
│   ├── refinements.csv               # Empirical paper tables
│   ├── hardware.json                 # Detected hardware
│   └── summary.md                    # Markdown summary
├── data/                             # SNAP downloads, gitignored
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── README.md
└── LICENSE
```

---

## Hardware

Reported numbers were generated on:

| | |
|---|---|
| CPU | Apple M3 Pro (12 cores) |
| RAM | 18 GB |
| OS | macOS 26.6 (Darwin 25.6.0, arm64) |
| Python | 3.12.7 (clang) |
| numpy | 1.26.4 (BLAS: OpenBLAS 0.3.23) |
| scipy | 1.13.1 |

`scripts/reproduce_results.py` auto-detects the local hardware and writes it to `results/hardware.json`.

---

## Headline numbers

| Configuration | n | \|H\| | wall-clock | β |
|---|---|---|---|---|
| Synthetic random DAG | 1000 | 358,975 | 0.4s | 11.9 |
| Synthetic weighted DAG | 1000 | 416,202 (hopset) | 8.4s | 11.9 |
| SNAP cit-HepPh | 34,546 | 178M | 93s | 99.4 |
| SNAP p2p-Gnutella31 | 62,586 | 201M | 191s | 201.8 |

The refinement-with-all-on vs all-off comparison (synthetic n=500, density=0.1):

| | hopset time |
|---|---|
| All refinements on (production) | 1.02s |
| All refinements off (paper baseline) | 9.17s |
| Only degree-ordered pivots | 1.07s |

**~9× speedup**, almost entirely from the degree-ordered pivots heuristic. The two formalised refinements (Lemmas 2 and 3) reduce wall-clock modestly but change *what shortcuts get added*, not just the order. See [`results/ablation.csv`](results/ablation.csv) for the full table.

---

## Known limitations

- `|H|` on SNAP is **330–680×** the paper's worst-case bound $O(m\rho + n\rho^2)$. The asymptotic bound is correct; the constants in the paper's analysis (sampling rate, TC trigger threshold, β estimate) are loose on real-world graphs. A tighter sampling constant and per-graph auto-tuning would close this gap. **See [`results/summary.md`](results/summary.md) for the honest breakdown.**
- `web-Google` (n=875,713) is out of reach for single-process Python: memory is unblocked (sparse TC), but wall-clock is dominated by Python's per-edge overhead. The improvement to break this is a Cython/numba port of the BFS and Dijkstra inner loops — explicitly out of scope per the user's design constraint.
- All randomised algorithms use seeded `random.Random` instances for reproducibility. No true parallel execution; parallel span bounds are not measured.

---

## Roadmap

### Done (v0.6.0)
- [x] Faithful reimplementation of JLS shortcut set + CFR hopset
- [x] Two formalised algorithmic refinements with proofs (`docs/paper_refinements.md`)
- [x] Corrigendum on four correctness bugs found (`docs/notes_correctness.md`)
- [x] Five engineering refinements documented (`docs/algorithmic_improvements.md`)
- [x] Toggleable per-refinement flags (`prspnsd.Flags`)
- [x] Sparse Boolean transitive closure (scipy.sparse)
- [x] Vectorised CSR BFS (numpy)
- [x] SNAP dataset loader + sha256 verification
- [x] Reproducible benchmark suite (`scripts/reproduce_results.py`)
- [x] Per-flag ablation (`scripts/run_ablation.py`)
- [x] Empirical paper tables (`scripts/eval_refinements.py`)
- [x] Logging-based output (no prints in scripts)

### Done (v0.7.0)
- [x] Hypothesis-based property testing on random DAGs (`tests/test_properties.py`)
- [x] SpanProfiler for empirical parallel span (`prspnsd/work_depth.py`)
- [x] Formalise Lemma 2.2 for dense graphs — strengthened Corollary 2.3 to ALL regimes
- [x] Counterexample search for Lemma 2.2 — no counterexample found in 24 cases
- [x] Auto-tuned sampling constant per graph density (`density_aware_constant`)
- [x] Parallel pivot processing — `ParallelContext` with threads + processes modes, 1.8–2.9× speedup
- [x] Fast matrix multiplication support (ω < 3) — runtime omega detection (`prspnsd/blas_omega.py`)
- [x] PRAM span measurement — `SpanProfiler` for sequential phase timing
- [x] True PRAM parallelism integration — `ParallelContext` with process-based dispatch

### Done (v0.8.0 — Papers 1, 2, 3 ideas)
- [x] SRG + Hamming graph test fixtures (Papers 2/3) — `petersen_graph`,
  `paley_graph`, `shrikhande_graph`, `hamming_graph` in
  `prspnsd/generators.py`.
- [x] Spectrum helpers + cross-check script (Paper 2) — `prspnsd/spectrum.py`,
  `scripts/spectral_check.py`. Verifies generator spectra match published
  values; documents `|H|/n` correlation with density rather than spectrum.
- [x] Fix/Resample experimental variant (Paper 1) —
  `prspnsd/fix_resample.py`, `scripts/eval_fix_resample.py`. Empirical
  finding across 9/9 fixtures: Fix/Resample produces smaller `|H|`
  (16% of JLS on average) but with looser hopbound. Trade-off
  documented in `docs/fix_resample.md`.
- [x] Honest documentation of each paper's contribution — `docs/spectral_fixtures.md`,
  `docs/fix_resample.md`. The user explicitly asked for honest
  framing: Paper 1's algorithm targets the dynamic setting (we're
  static), and Papers 2/3 contribute test inputs rather than
  algorithmic novelty.

### In progress (v0.7.x)
- [ ] Networkx cross-check in CI for every PR
- [ ] Hypothesis-based property tests in CI (currently run locally)
- [ ] Property-based tests for the lemmas at scale (PRSPNSD_HYPOTHESIS=10000)

### Planned (v0.8+)
- [ ] Cython port of the per-pivot BFS inner loop (for web-Google-scale inputs)
- [ ] Online documentation site (MkDocs)
- [ ] PyPI publishing workflow
- [ ] Pre-commit hooks (ruff + mypy + pytest)
- [ ] Fill in literature survey citations (`docs/lit_survey.md`)
- [ ] Star / sponsor / contributor recognition

### Deferred
- [ ] PRAM span for the *actual* parallel runtime (requires real PRAM model; SpanProfiler measures sequential phases only)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For research questions, see [`docs/paper_refinements.md`](docs/paper_refinements.md) for what's been proved and what's empirical.

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
@misc{prspnsd2026refinements,
  title={Algorithmic refinements for parallel reachability:
         tightened TC-pruning and hop-bounded pivot BFS},
  author={prspnsd contributors},
  year={2026},
  howpublished={\url{https://github.com/sachncs/parallel-reachability-and-shortest-paths}}
}
```

## License

[MIT](LICENSE) © 2026 Sachin