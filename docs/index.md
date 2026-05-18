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
- **Missing details**: The exact hopset pseudocode for Sections 6.1--6.3 was partially truncated in the extracted paper text. The reconstruction is marked with `ASSUMPTION` comments in the source.

## Installation

```bash
pip install -e ".[dev]"
```

Or using `requirements.txt`:

```bash
pip install -r requirements.txt
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

### Graph Generation

```python
from prspnsd.generators import random_dag, dense_graph, cycle_graph

# Random DAG with 50 vertices and edge probability 0.2
g1 = random_dag(n=50, edge_probability=0.2, random_seed=1)

# Dense digraph with 20 vertices and 150 edges
g2 = dense_graph(n=20, edge_count=150, random_seed=2)

# Directed cycle with 10 vertices
g3 = cycle_graph(10)
```

### Serialization

```python
from prspnsd.generators import path_graph
from prspnsd.serialization import digraph_to_json, digraph_from_json

g = path_graph(10)
text = digraph_to_json(g)
h = digraph_from_json(text)
assert g.num_vertices() == h.num_vertices()
assert set(g.edges()) == set(h.edges())
```

### Work/Depth Instrumentation

```python
from prspnsd.work_depth import WorkDepthAccountant, record_bfs
from prspnsd.generators import path_graph

graph = path_graph(100)
wd = WorkDepthAccountant()
wd.start_timer()
# ... run algorithm ...
wd.stop_timer()

record_bfs(wd, n=100, m=99)
print(wd.summary())
```

### Invariant Checking

```python
from prspnsd.invariants import assert_reachability_preserved
from prspnsd.shortcut_set import build_shortcut_set_for_reachability

shortcuts, _ = build_shortcut_set_for_reachability(g, random_seed=42)
assert_reachability_preserved(g, shortcuts)
```

## CLI

A command-line interface is available via `scripts/cli.py`.

```bash
# Reachability demo
python -m scripts.cli reachability --n 100 --m 500 --seed 42

# Shortest paths demo
python -m scripts.cli shortest-paths --n 80 --m 400 --epsilon 0.1 --seed 42

# Generate a graph
python -m scripts.cli generate-graph random_dag --n 100 --p 0.2 --output dag.json

# Run benchmarks
python -m scripts.cli benchmark-reachability --sizes 20 50 100 --densities 0.2 0.5
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

### Graph Generators

- `path_graph(n)` — directed path.
- `cycle_graph(n)` — directed cycle.
- `complete_dag(n)` — complete DAG.
- `random_dag(n, edge_probability, random_seed)` — random DAG.
- `erdos_renyi_digraph(n, edge_probability, random_seed)` — random digraph.
- `dense_graph(n, edge_count, random_seed)` — dense digraph with exact edge count.
- `graph_with_sccs(scc_sizes, inter_edge_probability, random_seed)` — graph with specified SCCs.
- `layered_dag(layers, edge_probability, random_seed)` — layered DAG.
- `grid_graph(n, m)` — n × m grid with unit weights.
- `weighted_path_graph(n, weight_range, random_seed)` — weighted directed path.
- `weighted_random_dag(n, edge_probability, weight_range, random_seed)` — weighted random DAG.
- `weighted_dense_graph(n, edge_count, weight_range, random_seed)` — weighted dense digraph.

### Serialization

- `digraph_to_json(graph)` / `digraph_from_json(text)` — JSON for Digraph.
- `weighted_digraph_to_json(graph)` / `weighted_digraph_from_json(text)` — JSON for WeightedDigraph.

### Work/Depth Simulation

- `WorkDepthAccountant` — tracks simulated work, depth, and observed runtime.
- `record_bfs(accountant, n, m)` — record BFS cost.
- `record_dijkstra(accountant, n, m)` — record Dijkstra cost.
- `record_matrix_multiply(accountant, n, omega)` — record matrix multiply cost.
- `record_tc_pruning(accountant, ball_size, omega)` — record TC-Pruning cost.
- `record_truncsssp_pruning(accountant, ball_size)` — record TruncSSSP-Pruning cost.
- `theoretical_shortcut_work(n, m, rho, omega)` / `theoretical_shortcut_depth(n, rho)` — Theorem 2 bounds.
- `theoretical_hopset_work(n, m, rho, epsilon)` / `theoretical_hopset_depth(n, m, rho)` — Theorem 4 bounds.

### Invariants

- `assert_reachability_preserved(graph, shortcuts)` — check reachability equality.
- `assert_hopbound(graph, source, shortcuts, beta)` — check hop count bound.
- `assert_scc_shortcuts_form_cliques(graph, shortcuts)` — check SCC clique property.
- `assert_partition_correctness(graph, parts)` — check partition validity.
- `assert_distance_approximation(graph, hopset, source, epsilon, max_hops)` — check (1+ε) guarantee.
- `assert_shortcut_set_size_bound(graph, shortcuts, rho)` — coarse size sanity check.
- `assert_hopset_size_bound(graph, hopset, epsilon, rho)` — coarse size sanity check.
- `check_equivalence_classes(labels, parts)` — check label-based partitioning.

## Running Tests

```bash
pytest
```

Use `-m "not slow"` to skip slower stress tests.

## License

MIT
