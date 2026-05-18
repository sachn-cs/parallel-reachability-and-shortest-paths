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

4. **Graph Generators and Utilities**  
   - Deterministic generators for paths, cycles, DAGs, dense graphs, grids, and SCC-structured graphs.
   - JSON serialization/deserialization for all graph types.

5. **Work/Depth Simulation Model**  
   - Explicit work and depth/span tracking aligned with the paper's PRAM bounds.
   - Separate observed runtime from simulated theoretical costs.

6. **Theorem-Oriented Validation**  
   - Invariant checkers for reachability preservation, distance approximation, SCC cliques, hop bounds, and partition correctness.

7. **Benchmark and CLI Tooling**  
   - Benchmark scripts for varying sizes, densities, and parameters.
   - CLI for graph generation, shortcut/hopset construction, reachability queries, and shortest-path queries.

## What is NOT Implemented

- **True PRAM parallelism**: Python does not provide the PRAM model. All algorithms run sequentially. The parallel span bounds are NOT DETERMINED.
- **HJS26 parallelization framework**: The paper black-boxes parallelization using [HJS26]; this framework is not reproduced.
- **Exact fast matrix multiplication with omega < 2.371339**: We use numpy's `matmul` which relies on standard BLAS (effectively omega = 3 for most sizes).
- **The o(1) terms in asymptotic bounds**: These are theoretical and absorbed into constants for finite inputs.
- **Some CFR hopset details**: Sections 6.1--6.3 were partially truncated in the extracted paper text. The hopset reconstruction is noted with `ASSUMPTION` comments.

## Setup

### Requirements

- Python >= 3.9
- numpy >= 1.21.0

### Installation

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with development dependencies (pytest).

### Using requirements.txt

```bash
pip install -r requirements.txt
```

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
4. A* search on a grid.

## CLI Usage

A full command-line interface is provided via `scripts/cli.py`.

### Reachability

```bash
python -m scripts.cli reachability --n 100 --m 500 --omega 3.0 --seed 42
```

### Shortest Paths

```bash
python -m scripts.cli shortest-paths --n 80 --m 400 --epsilon 0.1 --seed 42
```

### Generate a Graph

```bash
python -m scripts.cli generate-graph path --n 50 --output graph.json
python -m scripts.cli generate-graph random_dag --n 100 --p 0.2 --seed 1 --output dag.json
python -m scripts.cli generate-graph dense --n 50 --m 500 --weighted --output dense.json
```

### Benchmarks

```bash
python -m scripts.cli benchmark-reachability --sizes 20 50 100 --densities 0.2 0.5 --output results.csv
python -m scripts.cli benchmark-shortest-paths --sizes 20 50 --epsilons 0.05 0.1 --output hopset_results.csv
```

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
│   ├── hopset.py                # CFR + TruncSSSP-Pruning (Section 6)
│   ├── generators.py            # Deterministic graph generators
│   ├── serialization.py         # JSON serialization/deserialization
│   ├── work_depth.py            # Simulated work/depth accounting
│   └── invariants.py            # Theorem-oriented validation helpers
├── tests/
│   ├── test_graph.py
│   ├── test_reachability.py
│   ├── test_shortest_paths.py
│   ├── test_transitive_closure.py
│   ├── test_shortcut_set.py
│   ├── test_hopset.py
│   ├── test_generators.py
│   ├── test_serialization.py
│   ├── test_work_depth.py
│   ├── test_invariants.py
│   └── test_benchmark_sanity.py
├── scripts/
│   ├── demo.py
│   ├── cli.py
│   ├── benchmark_reachability.py
│   └── benchmark_shortest_paths.py
├── .github/workflows/ci.yml
├── pyproject.toml
├── requirements.txt
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

### Work/Depth Instrumentation

```python
from prspnsd.work_depth import WorkDepthAccountant, record_bfs
from prspnsd.generators import path_graph
from prspnsd.reachability import bfs_reachability

graph = path_graph(100)
wd = WorkDepthAccountant()
wd.start_timer()
bfs_reachability(graph, 0)
wd.stop_timer()

# Explicitly record theoretical cost
record_bfs(wd, n=100, m=99)
print(wd.summary())
```

### Invariant Checking

```python
from prspnsd.invariants import assert_reachability_preserved, assert_distance_approximation
from prspnsd.shortcut_set import build_shortcut_set_for_reachability

shortcuts, beta = build_shortcut_set_for_reachability(g, random_seed=42)
assert_reachability_preserved(g, shortcuts)
```

## Architecture Overview

The codebase is organized into layers:

1. **Graph Layer** (`graph.py`): Core data structures for directed and weighted directed graphs. Vertices are arbitrary hashable objects. Edge membership is O(1).

2. **Algorithm Layer** (`reachability.py`, `shortest_paths.py`, `transitive_closure.py`): Standard graph primitives (BFS, Dijkstra, SCCs, TC) used by the higher-level constructions.

3. **Shortcut/Hopset Layer** (`shortcut_set.py`, `hopset.py`): The paper's main constructions. `shortcut_set.py` implements JLS and JLS+TC-Pruning. `hopset.py` implements CFR and CFR+TruncSSSP-Pruning. Both handle SCC contraction automatically.

4. **Generator/Serialization Layer** (`generators.py`, `serialization.py`): Deterministic graph construction and JSON I/O for reproducible experiments.

5. **Parallel Simulation Layer** (`work_depth.py`): Since Python lacks PRAM, this module provides explicit work/depth accounting. Each major primitive can add its theoretical cost to a `WorkDepthAccountant`. This is mathematically traceable to the paper's bounds but does not claim actual parallelism.

6. **Validation Layer** (`invariants.py`): Structural checks that encode theorem conditions (reachability preservation, distance approximation, SCC cliques, partition correctness).

## Explanation of Work/Depth Instrumentation

The paper analyzes algorithms in the PRAM work/depth model:
- **Work** = total number of operations.
- **Depth** = length of the longest critical path (span).

Our implementation tracks these explicitly via `WorkDepthAccountant`:
- **Observed runtime** is measured with `time.perf_counter()`.
- **Simulated work** is accumulated as coarse-grained asymptotic estimates. For example, a BFS call adds O(m) work; a matrix multiplication adds O(n^omega) work.
- **Simulated depth** tracks the critical path length. For sequential phases, depth accumulates additively. For parallel phases, depth takes the maximum across branches.

This separation ensures we never conflate wall-clock time with theoretical parallel bounds.

## Evaluation

The implementation is evaluated via:

1. **Correctness tests**: Reachability and shortest-path distances are preserved exactly (reachability) or within (1 + epsilon) (hopsets).
2. **Invariants**: SCC shortcuts form cliques; partitioning preserves equivalence classes.
3. **Property tests**: TC-Pruning and TruncSSSP-Pruning add edges without violating reachability/distance bounds.
4. **Hop count estimation**: On test graphs, observed hop counts are consistent with theoretical beta bounds (up to constant factors).
5. **Benchmark sanity**: Benchmark and CLI scripts execute without errors on small inputs.

## Important Notes

- **Determinism**: All randomized algorithms accept a `random_seed` parameter and use seeded `random.Random` instances for reproducibility.
- **No true PRAM parallelism**: All algorithms run sequentially. The parallel span bounds are NOT DETERMINED.
- **Missing paper details**: Some constants in the hopset construction are reconstructed from analogy to the shortcut set. These are explicitly marked with `ASSUMPTION` comments in `hopset.py`.
- **Asymptotic bounds**: We do not claim empirical validation proves asymptotic bounds. Benchmarks are for sanity checking only.

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
