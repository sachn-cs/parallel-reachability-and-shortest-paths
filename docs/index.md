# PRSPNSD Documentation

## Overview

**PRSPNSD** (Parallel Reachability and Shortest Paths on Non-Sparse Digraphs) is a Python reproduction of the algorithms from:

> Ashvinkumar, Bernstein, Probst Gutenberg, and Saranurak.  
> "Parallel Reachability and Shortest Paths on Non-Sparse Digraphs: Near-linear Work and Sub-square-root Depth."  
> arXiv:2605.03892v1, 2026.

This package implements the core sequential constructions from the paper:

1. **Shortcut sets for reachability** (Theorem 2) — JLS with TC-Pruning.
2. **Hopsets for approximate shortest paths** (Theorem 4) — CFR with TruncSSSP-Pruning.
3. **Deterministic graph primitives** — BFS, Dijkstra, A*, SCC decomposition, transitive closure.

## Important Notes

- **No true PRAM parallelism**: Python does not support the PRAM model. Algorithms are sequential simulations. Parallel span bounds are NOT DETERMINED.
- **Determinism**: All randomized algorithms accept a `random_seed` parameter and use seeded `random.Random` instances for reproducibility.
- **Matrix multiplication**: Transitive closure uses `numpy.matmul` (standard BLAS, effectively $\omega = 3$ for most problem sizes).

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Reachability

```python
from prspnsd.graph import Digraph
from prspnsd.shortcut_set import build_shortcut_set_for_reachability
from prspnsd.reachability import parallel_bfs, bfs_reachability

g = Digraph()
g.add_edge(0, 1)
g.add_edge(1, 2)

shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
reachable = parallel_bfs(g, 0, shortcuts)
assert reachable == bfs_reachability(g, 0)
```

### Shortest Paths

```python
from prspnsd.graph import WeightedDigraph
from prspnsd.hopset import build_hopset_for_sssp
from prspnsd.shortest_paths import dijkstra, shortest_path_hopbound

g = WeightedDigraph()
g.add_edge(0, 1, 1)
g.add_edge(1, 2, 2)

hopset, beta = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
original = dijkstra(g, 0)
approx = shortest_path_hopbound(g, hopset, 0, max_hops=100)
```

## API Reference

### Graph Types

- `Digraph` — unweighted directed graph with O(1) edge membership.
- `WeightedDigraph` — weighted directed graph with O(1) edge membership.

### Reachability

- `bfs_reachability(graph, source)` — standard BFS reachability.
- `parallel_bfs(graph, source, shortcuts)` — BFS augmented with shortcut edges.
- `strongly_connected_components(graph)` — Kosaraju's algorithm.
- `topological_sort(graph)` — Kahn's algorithm.

### Shortest Paths

- `dijkstra(graph, source)` — exact SSSP.
- `astar(graph, source, target, heuristic)` — A* search.
- `truncated_dijkstra(graph, source, max_distance)` — SSSP truncated at a distance bound.
- `shortest_path_hopbound(graph, hopset, source, max_hops)` — hop-bounded SSSP with hopset.

### Transitive Closure

- `transitive_closure_brute_force(graph)` — O(n(m+n)) brute force.
- `transitive_closure_matrix(graph)` — O(n^ω) via repeated Boolean squaring.
- `transitive_closure_on_subset(graph, subset)` — TC on an induced subgraph.

### Shortcut Sets

- `build_shortcut_set_for_reachability(graph, omega, random_seed)` — high-level wrapper.
- `jls_shortcut_set(graph, k, max_level, n_global, random_seed)` — baseline JLS.
- `jls_with_tc_pruning(graph, k, rho, max_level, n_global, random_seed)` — JLS + TC-Pruning.

### Hopsets

- `build_hopset_for_sssp(graph, epsilon, random_seed)` — high-level wrapper.
- `cfr_hopset(graph, k, epsilon, max_level, n_global, random_seed)` — baseline CFR.
- `cfr_with_truncsssp_pruning(graph, k, epsilon, rho, max_level, n_global, random_seed)` — CFR + TruncSSSP-Pruning.

## Running Tests

```bash
pytest
```

## License

MIT
