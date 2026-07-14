# Parallel Reachability and Shortest Paths on Non-sparse Digraphs

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/sachncs/parallel-reachability-and-shortest-paths/actions/workflows/ci.yml/badge.svg)](https://github.com/sachncs/parallel-reachability-and-shortest-paths/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.0-green.svg)](https://github.com/sachncs/parallel-reachability-and-shortest-paths/releases)

A faithful Python reproduction of **"Parallel Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth"** by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak ([arXiv:2605.03892](https://arxiv.org/abs/2605.03892)).

## Features

- **Shortcut Set Construction** (Theorem 2): JLS algorithm with TC-Pruning for near-linear time beta-shortcut sets
- **Hopset Construction** (Theorem 4): CFR algorithm with TruncSSSP-Pruning for (beta, epsilon)-hopsets
- **Graph Primitives**: BFS, reverse BFS, SCC decomposition, Dijkstra, A*, transitive closure
- **Deterministic Generators**: Path, cycle, DAG, dense, grid, SCC-structured, and weighted graph variants
- **Work/Depth Simulation**: Explicit PRAM work/depth tracking with theoretical bounds
- **Invariant Checkers**: Reachability preservation, distance approximation, SCC clique properties
- **JSON Serialization**: Save and load graphs for reproducible experiments
- **CLI Tooling**: Command-line interface for graph generation, queries, and benchmarks

## Installation

```bash
# Clone the repository
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
cd parallel-reachability-and-shortest-paths

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python >= 3.9
- numpy >= 1.21.0

## Quick Start

### Reachability with Shortcut Sets

```python
from prspnsd.graph import Digraph
from prspnsd.shortcut_set import build_shortcut_set_for_reachability
from prspnsd.reachability import parallel_bfs, bfs_reachability

# Build a digraph
g = Digraph()
for i in range(100):
    g.add_vertex(i)
for i in range(99):
    g.add_edge(i, i + 1)

# Construct shortcut set
shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)

# Query reachability using shortcuts
source = 0
reachable = parallel_bfs(g, source, shortcuts)
assert reachable == bfs_reachability(g, source)  # Reachability is preserved
```

### Shortest Paths with Hopsets

```python
from prspnsd.graph import WeightedDigraph
from prspnsd.hopset import build_hopset_for_sssp
from prspnsd.shortest_paths import dijkstra, shortest_path_hopbound

# Build a weighted digraph
g = WeightedDigraph()
for i in range(80):
    g.add_vertex(i)
for i in range(79):
    g.add_edge(i, i + 1, 1)

# Construct hopset with epsilon approximation
hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)

# Query shortest paths using hopset
source = 0
original = dijkstra(g, source)
approx = shortest_path_hopbound(g, hopset, source, max_hops=1000)

for v in g.vertices():
    assert approx[v] <= (1 + 0.1) * original[v] + 1e-9
```

### Graph Generation

```python
from prspnsd.generators import random_dag, dense_graph, grid_graph

g1 = random_dag(n=50, edge_probability=0.2, random_seed=1)
g2 = dense_graph(n=20, edge_count=150, random_seed=2)
g3 = grid_graph(5, 5)
```

### Serialization

```python
from prspnsd.generators import path_graph
from prspnsd.serialization import digraph_to_json, digraph_from_json

g = path_graph(10)
text = digraph_to_json(g)
h = digraph_from_json(text)
```

## CLI Usage

A full command-line interface is provided via `scripts/cli.py`.

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

## Documentation

- [Getting Started](docs/getting-started.md) - Quick setup guide
- [Architecture](docs/architecture.md) - Codebase structure overview
- [Algorithms](docs/algorithms.md) - Algorithm descriptions and paper references
- [Work/Depth Model](docs/work-depth.md) - PRAM simulation details
- [Invariants](docs/invariants.md) - Theorem validation helpers
- [Benchmarks](docs/benchmarks.md) - Performance evaluation
- [Deployment](docs/deployment.md) - Installation and publishing
- [FAQ](docs/faq.md) - Common questions and answers

## Development

### Running Tests

```bash
pytest                          # Run all tests
pytest -m "not slow"            # Skip slow tests
pytest --cov=prspnsd            # Run with coverage
```

### Code Quality

```bash
ruff check prspnsd tests scripts   # Linting
mypy prspnsd                        # Type checking
```

### Running the Demo

```bash
python scripts/demo.py
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| Dependencies | numpy |
| Testing | pytest, pytest-cov |
| Linting | ruff |
| Type Checking | mypy |
| CI/CD | GitHub Actions |
| Build System | setuptools (PEP 621) |

## Roadmap

- [ ] True PRAM parallelism integration (multiprocessing/ray)
- [ ] Fast matrix multiplication support (ω < 3)
- [ ] MkDocs documentation site
- [ ] PyPI publishing workflow
- [ ] Pre-commit hooks configuration
- [ ] Performance benchmarks on larger graphs
- [ ] Additional graph generators
- [ ] Export `complete_dag` and `graph_stats` in public API

## Important Notes

- **Determinism**: All randomized algorithms accept a `random_seed` parameter and use seeded `random.Random` instances for reproducibility.
- **No true PRAM parallelism**: All algorithms run sequentially. The parallel span bounds are NOT DETERMINED.
- **Missing paper details**: Some constants in the hopset construction are reconstructed from analogy to the shortcut set. These are explicitly marked with `ASSUMPTION` comments in `hopset.py`.
- **Asymptotic bounds**: We do not claim empirical validation proves asymptotic bounds. Benchmarks are for sanity checking only.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For reporting security vulnerabilities, please see [SECURITY.md](SECURITY.md).

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

[MIT](LICENSE)
