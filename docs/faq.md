# Frequently Asked Questions

## General

### What is reachq?

reachq is a Python reproduction of the algorithms from the paper "Parallel
Reachability and Shortest Paths on Non-sparse Digraphs: Near-linear Work and
Sub-square-root Depth" by Ashvinkumar, Bernstein, Probst Gutenberg, and
Saranurak (2026).

### What does reachq implement?

- Graph hierarchy: `Graph` → `Digraph` → `WeightedDigraph` with template hooks
- Shortcut set construction (Theorem 2) with TC-Pruning
- Hopset construction (Theorem 4) with TruncSSSP-Pruning
- Graph primitives (BFS, Dijkstra, SCC, transitive closure)
- Deterministic graph generators
- JSON serialization
- Work/depth simulation
- Invariant checkers

### What is NOT implemented?

- True PRAM parallelism (Python doesn't support PRAM)
- The HJS26 parallelization framework
- Fast matrix multiplication (ω < 3)
- Some hopset details (partially truncated in paper)

### What Python versions are supported?

Python 3.10 through 3.13.

## Installation

### Do I need numpy?

Yes. numpy is a required dependency used for matrix multiplication in the
transitive closure algorithm.

### How do I install development dependencies?

```bash
pip install -e ".[dev]"
```

This installs pytest, mypy, ruff, and other development tools.

## Usage

### How do I build a graph?

```python
from reachq.graph import Digraph

g = Digraph()
g.add_edge(0, 1)
g.add_edge(1, 2)
```

### How do I construct a shortcut set?

```python
from reachq.shortcut import build_shortcut_set_for_reachability

shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
```

### How do I query reachability?

```python
from reachq.reachability import parallel_bfs

reachable = parallel_bfs(g, source=0, shortcuts=shortcuts)
```

### How do I compute shortest paths?

```python
from reachq.shortest_paths import dijkstra

distances = dijkstra(g, source=0)
```

### How do I use hopsets for approximate shortest paths?

```python
from reachq.hopset import build_hopset_for_sssp
from reachq.shortest_paths import shortest_path_hopbound

hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
approx_distances = shortest_path_hopbound(g, hopset, source=0, max_hops=1000)
```

### How do I ensure reproducibility?

All randomized algorithms accept a `random_seed` parameter:

```python
shortcuts, _ = build_shortcut_set_for_reachability(g, random_seed=42)
hopset, _ = build_hopset_for_sssp(g, random_seed=42)
```

### How do I generate test graphs?

```python
from reachq.generators import random_dag, dense_graph, grid_graph

g1 = random_dag(n=50, edge_probability=0.2, random_seed=1)
g2 = dense_graph(n=20, edge_count=150, random_seed=2)
g3 = grid_graph(5, 5)
```

## Performance

### How fast are the algorithms?

Shortcut set and hopset construction run in near-linear time O~(m). The exact
runtime depends on graph size and structure. Use the benchmark scripts for
empirical measurements:

```bash
python -m scripts.cli benchmark-reachability --sizes 20 50 100
```

### Can I use reachq for large graphs?

The algorithms handle large graphs, but Python's single-threaded nature limits
throughput. For graphs with millions of vertices, consider:

1. Using the matrix-based transitive closure with an optimized BLAS library
2. Processing graphs in parallel at the application level
3. Monitoring memory usage

### Why is the matrix transitive closure slow?

The TC uses numpy's matmul, which relies on standard BLAS (ω = 3). Fast matrix
multiplication (ω < 3) is not available in standard numpy. The brute-force BFS-based
TC may be faster for sparse graphs.

## Troubleshooting

### Tests are failing

1. Ensure you're using Python 3.10+
2. Reinstall dependencies: `pip install -e ".[dev]"`
3. Check for version conflicts: `pip check`

### Import errors

Ensure the package is installed in editable mode:

```bash
pip install -e ".[dev]"
```

### Memory errors

Large graphs may consume significant memory. Try:

1. Reducing graph size
2. Using sparse graph generators (random_dag, path_graph)
3. Monitoring memory with `psutil` or system tools

### Numerical precision issues

Floating-point operations in shortest path algorithms may have precision
limitations. For critical applications:

1. Use integer weights where possible
2. Set appropriate tolerances in distance comparisons
3. Verify results with exact algorithms

## Contributing

See [CONTRIBUTING.md](https://github.com/sachncs/parallel-reachability-and-shortest-paths/blob/master/CONTRIBUTING.md) for guidelines on:

- Setting up the development environment
- Branch naming conventions
- Commit message format
- Pull request process
- Coding standards
- Running tests

## Getting Help

- Open an issue on [GitHub](https://github.com/sachncs/parallel-reachability-and-shortest-paths/issues)
- Check the [API Reference](index.md) for function documentation
- Review the [Algorithms](algorithms.md) documentation for theoretical background
