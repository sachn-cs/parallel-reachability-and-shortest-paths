<p align="center">
  <h1 align="center">Parallel Reachability and Shortest Paths</h1>
  <p align="center">Faithful Python reproduction of near-linear-work, sub-square-root-depth parallel algorithms on non-sparse digraphs.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/parallel-reachability-and-shortest-paths/ci.yml?branch=master" alt="CI"></a>
    <a href="https://pypi.org/project/prspnsd/"><img src="https://img.shields.io/pypi/v/prspnsd" alt="PyPI"></a>
    <a href="https://github.com/sachncs/parallel-reachability-and-shortest-paths/stargazers"><img src="https://img.shields.io/github/stars/sachncs/parallel-reachability-and-shortest-paths" alt="Stars"></a>
  </p>
</p>

A faithful Python reproduction of **"Parallel Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth"** by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak ([arXiv:2605.03892](https://arxiv.org/abs/2605.03892)).

---

## Features

- **Shortcut Set Construction** (Theorem 2): JLS algorithm with TC-Pruning for near-linear time beta-shortcut sets
- **Hopset Construction** (Theorem 4): CFR algorithm with TruncSSSP-Pruning for (beta, epsilon)-hopsets
- **Graph Primitives**: BFS, reverse BFS, SCC decomposition, Dijkstra, A*, transitive closure
- **Deterministic Generators**: Path, cycle, DAG, dense, grid, SCC-structured, and weighted graph variants
- **Work/Depth Simulation**: Explicit PRAM work/depth tracking with theoretical bounds
- **Invariant Checkers**: Reachability preservation, distance approximation, SCC clique properties
- **JSON Serialization**: Save and load graphs for reproducible experiments
- **CLI Tooling**: Command-line interface for graph generation, queries, and benchmarks

---

## Installation

### From PyPI

```bash
pip install prspnsd
```

### From source

```bash
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
cd parallel-reachability-and-shortest-paths
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Requirements**: Python >= 3.9, numpy >= 1.21.0.

---

## Quick Start

### CLI

```bash
# Reachability demo
python -m scripts.cli reachability --n 100 --m 500 --omega 3.0 --seed 42

# Shortest paths demo
python -m scripts.cli shortest-paths --n 80 --m 400 --epsilon 0.1 --seed 42

# Generate a graph
python -m scripts.cli generate-graph path --n 50 --output graph.json
python -m scripts.cli generate-graph random_dag --n 100 --p 0.2 --seed 1 --output dag.json

# Run benchmarks
python -m scripts.cli benchmark-reachability --sizes 20 50 100 --densities 0.2 0.5 --output results.csv
python -m scripts.cli benchmark-shortest-paths --sizes 20 50 --epsilons 0.05 0.1 --output hopset_results.csv
```

### Python API

```python
# Reachability with shortcut sets
from prspnsd.graph import Digraph
from prspnsd.shortcut_set import build_shortcut_set_for_reachability
from prspnsd.reachability import parallel_bfs, bfs_reachability

g = Digraph()
for i in range(100):
    g.add_vertex(i)
for i in range(99):
    g.add_edge(i, i + 1)

shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)

source = 0
reachable = parallel_bfs(g, source, shortcuts)
assert reachable == bfs_reachability(g, source)  # Reachability is preserved

# Shortest paths with hopsets
from prspnsd.graph import WeightedDigraph
from prspnsd.hopset import build_hopset_for_sssp
from prspnsd.shortest_paths import dijkstra, shortest_path_hopbound

g = WeightedDigraph()
for i in range(80):
    g.add_vertex(i)
for i in range(79):
    g.add_edge(i, i + 1, 1)

hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)

source = 0
original = dijkstra(g, source)
approx = shortest_path_hopbound(g, hopset, source, max_hops=1000)

for v in g.vertices():
    assert approx[v] <= (1 + 0.1) * original[v] + 1e-9

# Graph generation
from prspnsd.generators import random_dag, dense_graph, grid_graph

g1 = random_dag(n=50, edge_probability=0.2, random_seed=1)
g2 = dense_graph(n=20, edge_count=150, random_seed=2)
g3 = grid_graph(5, 5)

# Serialization
from prspnsd.generators import path_graph
from prspnsd.serialization import digraph_to_json, digraph_from_json

g = path_graph(10)
text = digraph_to_json(g)
h = digraph_from_json(text)
```

---

## Configuration

| Parameter | Env Variable | Default | Description |
|-----------|--------------|---------|-------------|
| `omega` | — | `2.0` | Graph-theoretic omega; supports up to the matrix-multiplication exponent |
| `epsilon` | — | `0.1` | Approximation factor for `(beta, epsilon)`-hopsets |
| `random_seed` | — | `42` | Seed for the JLS / CFR / TC-Pruning samplers |
| `beta` | _derived_ | `omega + 1` | Cut parameter for shortcut sets |
| `max_hops` | — | `1000` | Hop bound passed to `shortest_path_hopbound` |

See [docs/algorithms.md](docs/algorithms.md) and [docs/invariants.md](docs/invariants.md)
for the full set of invariants and tuning knobs.

---

## API

| Symbol | Type | Description |
|--------|------|-------------|
| `Digraph` | class | Mutable directed graph (used for reachability) |
| `WeightedDigraph` | class | Mutable weighted directed graph (used for shortest paths) |
| `build_shortcut_set_for_reachability` | function | Theorem-2 construction: JLS + TC-Pruning |
| `build_hopset_for_sssp` | function | Theorem-4 construction: CFR + TruncSSSP-Pruning |
| `parallel_bfs` | function | BFS over a digraph augmented with a shortcut set |
| `bfs_reachability` | function | Sequential baseline used for invariant checks |
| `dijkstra` | function | Dijkstra's algorithm on `WeightedDigraph` |
| `shortest_path_hopbound` | function | Approximate SSSP with hop bound |
| `random_dag`, `dense_graph`, `grid_graph`, `path_graph` | function | Deterministic generators |
| `digraph_to_json`, `digraph_from_json` | function | JSON serialisation |

---

## Examples

```bash
# 1. Reachability demo on a random DAG.
python -m scripts.cli reachability --n 100 --m 500 --omega 3.0 --seed 42

# 2. Shortest-paths demo with epsilon=0.1 approximation.
python -m scripts.cli shortest-paths --n 80 --m 400 --epsilon 0.1 --seed 42

# 3. Generate a path graph and serialise it.
python -m scripts.cli generate-graph path --n 50 --output graph.json

# 4. Run the reachability benchmark across sizes and densities.
python -m scripts.cli benchmark-reachability \
    --sizes 20 50 100 --densities 0.2 0.5 --output results.csv
```

A standalone demo script is also available:

```bash
python scripts/demo.py
```

---

## Documentation

- [Getting Started](docs/getting-started.md) - Quick setup guide
- [Architecture](docs/architecture.md) - Codebase structure overview
- [Algorithms](docs/algorithms.md) - Algorithm descriptions and paper references
- [Work/Depth Model](docs/work-depth.md) - PRAM simulation details
- [Invariants](docs/invariants.md) - Theorem validation helpers
- [Benchmarks](docs/benchmarks.md) - Performance evaluation
- [Deployment](docs/deployment.md) - Installation and publishing
- [FAQ](docs/faq.md) - Common questions and answers

---

## Project Structure

```
parallel-reachability-and-shortest-paths/
├── prspnsd/                    # Main package
│   ├── __init__.py             # Public API exports
│   ├── graph.py                # Digraph and WeightedDigraph
│   ├── reachability.py         # BFS, SCCs, topological sort
│   ├── shortest_paths.py       # Dijkstra, A*, truncated SSSP
│   ├── transitive_closure.py   # Matrix-multiplication TC
│   ├── shortcut_set.py         # JLS + TC-Pruning (Theorem 2)
│   ├── hopset.py               # CFR + TruncSSSP-Pruning (Theorem 4)
│   ├── generators.py           # Deterministic graph generators
│   ├── serialization.py        # JSON serialization/deserialization
│   ├── work_depth.py           # Simulated work/depth accounting
│   └── invariants.py           # Theorem-oriented validation helpers
├── tests/                      # Test suite
├── scripts/                    # CLI and benchmark scripts
├── docs/                       # Documentation
├── .github/                    # GitHub configuration
├── pyproject.toml              # Build configuration
├── CONTRIBUTING.md             # Contribution guidelines
├── CODE_OF_CONDUCT.md          # Community standards
├── SECURITY.md                 # Security policy
├── CHANGELOG.md                # Version history
└── LICENSE                     # MIT License
```

---

## Development

```bash
pytest                          # Run all tests
pytest -m "not slow"            # Skip slow tests
pytest --cov=prspnsd            # Run with coverage
ruff check prspnsd tests scripts   # Linting
mypy prspnsd                        # Type checking
python scripts/demo.py              # Run the demo
```

---

## Testing

```bash
pytest
pytest -m "not slow"
pytest --cov=prspnsd
```

---

## Build

```bash
python -m build
```

---

## Release

Version is bumped in `pyproject.toml`, the changelog updated in
`CHANGELOG.md`, a `vX.Y.Z` tag is cut, and the PyPI publishing workflow
publishes the source and wheel distributions. See
[docs/deployment.md](docs/deployment.md) for the full process.

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.9+ |
| Dependencies | [numpy](https://numpy.org/) |
| Testing | [pytest](https://docs.pytest.org/), pytest-cov |
| Linting | [ruff](https://docs.astral.sh/ruff/) |
| Type Checking | [mypy](https://mypy-lang.org/) |
| CI/CD | GitHub Actions |
| Build System | [setuptools](https://setuptools.pypa.io/) (PEP 621) |

---

## Roadmap

- [ ] True PRAM parallelism integration (multiprocessing/ray)
- [ ] Fast matrix multiplication support (ω < 3)
- [ ] MkDocs documentation site
- [ ] PyPI publishing workflow
- [ ] Pre-commit hooks configuration
- [ ] Performance benchmarks on larger graphs
- [ ] Additional graph generators
- [ ] Export `complete_dag` and `graph_stats` in public API

---

## Important Notes

- **Determinism**: All randomized algorithms accept a `random_seed` parameter and use seeded `random.Random` instances for reproducibility.
- **No true PRAM parallelism**: All algorithms run sequentially. The parallel span bounds are NOT DETERMINED.
- **Missing paper details**: Some constants in the hopset construction are reconstructed from analogy to the shortcut set. These are explicitly marked with `ASSUMPTION` comments in `hopset.py`.
- **Asymptotic bounds**: We do not claim empirical validation proves asymptotic bounds. Benchmarks are for sanity checking only.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For reporting security vulnerabilities, please see [SECURITY.md](SECURITY.md).

---

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

## License

[MIT](LICENSE) © 2026 Sachin
