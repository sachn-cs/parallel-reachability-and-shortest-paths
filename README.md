# Parallel Reachability and Shortest Paths on Non-sparse Digraphs

Reproduction of **"Parallel Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and Sub-square-root Depth"** by Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak (arXiv:2605.03892v1).

## What is Implemented

This repository contains a faithful Python reproduction of the paper's core algorithmic contributions:

1. **Sequential Shortcut Set Construction (Theorem 2)**  
   - The JLS shortcut set algorithm ([JLS19]) with **TC-Pruning** (Section 4).
   - Near-linear time construction of a beta-shortcut set with size O~(m).

2. **Sequential Hopset Construction (Theorem 4)**  
   - The CFR hopset algorithm ([CFR20]) with **TruncSSSP-Pruning** (Section 6).
   - Near-linear time construction of a (beta, epsilon)-hopset with size O~(m / epsilon^2).

3. **Reachability and Shortest-Path Primitives**  
   - BFS, reverse BFS, SCC decomposition (Kosaraju).
   - Dijkstra, truncated Dijkstra, hop-bounded shortest paths.
   - Transitive closure via matrix multiplication (numpy BLAS).

4. **High-Level Wrappers**  
   - `build_shortcut_set_for_reachability`: automatic parameter selection.
   - `build_hopset_for_sssp`: automatic parameter selection.

## What is NOT Implemented

- **True PRAM parallelism**: Python does not provide the PRAM model. All algorithms run sequentially. The parallel span bounds are NOT DETERMINED.
- **HJS26 parallelization framework**: The paper black-boxes parallelization using [HJS26]; this framework is not reproduced.
- **Exact fast matrix multiplication with omega < 2.371339**: We use numpy's `matmul` which relies on standard BLAS (effectively omega = 3 for most sizes).
- **The o(1) terms in asymptotic bounds**: These are theoretical and absorbed into constants for finite inputs.

## Setup

### Requirements

- Python >= 3.9
- numpy >= 1.21.0

### Installation

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with development dependencies (pytest).

## Running Tests

```bash
pytest
```

All tests run in under a minute on a modern laptop.

## Running the Demo

```bash
python scripts/demo.py
```

The demo shows:
1. Shortcut set construction on a 100-vertex test graph.
2. Hopset construction on an 80-vertex weighted test graph.
3. SCC handling on a cyclic graph.

## Project Structure

```
prspnsd/
├── prspnsd/
│   ├── __init__.py
│   ├── graph.py                 # Digraph and WeightedDigraph
│   ├── reachability.py          # BFS, SCCs, topological sort
│   ├── shortest_paths.py        # Dijkstra, A*, truncated SSSP, hop-bounded paths
│   ├── transitive_closure.py    # Matrix-multiplication TC
│   ├── shortcut_set.py          # JLS + TC-Pruning (Section 4)
│   └── hopset.py                # CFR + TruncSSSP-Pruning (Section 6)
├── tests/
│   ├── test_graph.py
│   ├── test_reachability.py
│   ├── test_shortest_paths.py
│   ├── test_transitive_closure.py
│   ├── test_shortcut_set.py
│   └── test_hopset.py
├── scripts/
│   └── demo.py
├── .github/workflows/ci.yml
├── pyproject.toml
└── README.md
```

## Usage

### Shortcut Set for Reachability

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

# Construct shortcut set (omega=3 for combinatorial, omega=2.37 for fast MM)
shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)

# Query reachability using shortcuts
source = 0
reachable = parallel_bfs(g, source, shortcuts)
assert reachable == bfs_reachability(g, source)  # Reachability is preserved
```

### Hopset for Shortest Paths

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

## Evaluation

The implementation is evaluated via:

1. **Correctness tests**: Reachability and shortest-path distances are preserved exactly (reachability) or within (1 + epsilon) (hopsets).
2. **Invariants**: SCC shortcuts form cliques; partitioning preserves equivalence classes.
3. **Property tests**: TC-Pruning and TruncSSSP-Pruning add edges without violating reachability/distance bounds.
4. **Hop count estimation**: On test graphs, the observed hop counts are consistent with the theoretical beta bounds (up to constant factors).

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

MIT
