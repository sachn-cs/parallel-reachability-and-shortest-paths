# Architecture

This document describes the high-level architecture of reachq and how its
components interact.

## Overview

reachq is organized into six layers, each with clear responsibilities:

```
┌─────────────────────────────────────────────────────┐
│            Validation Layer (core/invariants)        │
├─────────────────────────────────────────────────────┤
│      Parallel Simulation Layer (core/work_depth)    │
├─────────────────────────────────────────────────────┤
│    Shortcut/Hopset Layer (core/shortcut, core/hopset, core/shortcut_parallel)    │
├─────────────────────────────────────────────────────┤
│  Generator/Serialization Layer (core/generators,     │
│                                core/io/json)         │
├─────────────────────────────────────────────────────┤
│    Algorithm Layer (core/reachability,               │
│                      core/shortest_paths)            │
├─────────────────────────────────────────────────────┤
│              Graph Layer (core/graph)                │
└─────────────────────────────────────────────────────┘
```

## Layer Descriptions

### Graph Layer (`core/graph.py`)

The foundation of the entire system. Three-class hierarchy using the template
method pattern:

- **`Graph`** (base): Vertex management, edge count, and shared operations
  (`induced_subgraph`, `reversed`, `copy`) implemented via template hooks.
  Uses `__slots__` for memory efficiency.
- **`Digraph(Graph)`**: Unweighted directed graph with O(1) edge membership.
  Adjacency stored as `dict[object, set[object]]`.
- **`WeightedDigraph(Digraph)`**: Weighted variant with O(1) edge weight
  lookups. Adjacency stored as `dict[object, dict[object, int]]`.

**Template hooks** (overridden by subclasses):

| Hook | Purpose |
|------|---------|
| `initialize_vertex(v)` | Set up adjacency storage for a new vertex |
| `iterate_edges_from(u)` | Yield `(v, data)` for each outgoing edge from `u` |
| `store_edge(u, v, data)` | Store an edge in the adjacency structure |
| `create_empty()` | Create an empty graph of the same concrete type |

**Shared operations** (implemented once on `Graph`, work for all subclasses):

- `induced_subgraph(vertex_subset)` — G[S] as defined in Section 2
- `reversed()` — G^R with all edges flipped
- `copy()` — deep copy

**Module-level helpers** (co-located with graph structures):

- `partition_by_labels(vertices, labels)` — equivalence classes by label equality
- `contract_sccs(graph)` — SCC decomposition and vertex-to-component mapping

### Algorithm Layer

Standard graph primitives used by higher-level constructions:

- **`core/reachability.py`**: BFS, reverse BFS, SCC decomposition (Kosaraju),
  topological sort, parallel BFS with shortcuts
- **`core/shortest_paths.py`**: Dijkstra, A*, truncated Dijkstra, hop-bounded SSSP,
  shortest path trees
- **`core/tc.py`**: transitive closure via sparse Boolean matrix
  multiplication (scipy.sparse), brute-force BFS-based TC, subset TC

### Shortcut/Hopset Layer

The paper's main algorithmic contributions:

- **`core/shortcut.py`**: JLS shortcut set algorithm with TC-Pruning (Theorem 2).
  Constructs beta-shortcut sets in near-linear time.
- **`core/hopset.py`**: CFR hopset algorithm with TruncSSSP-Pruning (Theorem 4).
  Constructs (beta, epsilon)-hopsets in near-linear time.

Both handle SCC contraction automatically via the high-level wrappers:
- `build_shortcut_set_for_reachability()`
- `build_hopset_for_sssp()`

### Generator/Serialization Layer

Utilities for reproducible experiments:

- **`core/generators.py`**: Deterministic graph generators for paths, cycles, DAGs,
  dense graphs, grids, SCC-structured graphs, and weighted variants.
- **`core/io/json.py`**: JSON serialization for all graph types (`dump`, `load`,
  `weighted_dump`, `weighted_load`).

### Parallel Simulation Layer (`core/work_depth.py`)

Since Python lacks PRAM support, this module provides explicit work/depth
accounting:

- **`WorkDepthAccountant`**: Tracks simulated work, depth, and observed runtime.
- **Recording functions**: `record_bfs`, `record_dijkstra`, `record_matrix_multiply`,
  etc. add theoretical costs to the accountant.
- **Theoretical bounds**: `theoretical_shortcut_work`, `theoretical_hopset_work`,
  etc. compute expected PRAM bounds.

This separation ensures we never conflate wall-clock time with theoretical
parallel bounds.

### Validation Layer (`core/invariants.py`)

Structural checks that encode theorem conditions:

- `assert_reachability_preserved()` - check reachability equality
- `assert_hopbound()` - check hop count bound
- `assert_scc_shortcuts_form_cliques()` - check SCC clique property
- `assert_partition_correctness()` - check partition validity
- `assert_distance_approximation()` - check (1+ε) guarantee
- `assert_shortcut_set_size_bound()` - coarse size sanity check
- `assert_hopset_size_bound()` - coarse size sanity check

## Data Flow

A typical workflow follows this pattern:

```
Input Graph
    │
    ▼
[SCC Contraction]  (core/shortcut.py / core/hopset.py)
    │
    ▼
[Algorithm Construction]  (JLS + TC-Pruning / CFR + TruncSSSP-Pruning)
    │
    ▼
[Shortcut/Hopset Edges]
    │
    ├──► [Reachability Query]  (parallel_bfs)
    │
    ├──► [Shortest Path Query]  (shortest_path_hopbound)
    │
    └──► [Invariant Validation]  (core/invariants.py)
```

## Design Principles

1. **Determinism**: All randomized algorithms accept `random_seed` parameters
   and use seeded `random.Random` instances.

2. **Separation of Concerns**: Graph structures, algorithms, and validation
   are cleanly separated. Graph helpers (`partition_by_labels`,
   `contract_sccs`) are co-located in `core/graph.py` since they operate
   directly on graph internals.

3. **OO Hierarchy**: Inheritance only for genuine is-a relationships.
   `Graph` → `Digraph` → `WeightedDigraph`. Template hooks enable shared
   operations without code duplication.

4. **Theoretical Fidelity**: Asymptotic complexity is documented and tracked
   via the work/depth model.

5. **Testability**: Every public function has corresponding tests with both
   positive and negative cases. Test coverage is 76% (last measured
   during the v0.8.0 release with `pytest --cov=reachq` — 3737
   statements, 880 missed, 76% line coverage).

6. **Extensibility**: New graph types can be added by subclassing `Graph`
   and implementing the four template hooks.

## Module Dependencies

```
core/graph.py       (no internal dependencies; contract_sccs lazily imports
    │               strongly_connected_components from core.reachability)
    │
    ├── core/reachability.py
    │       │
    │       ├── core/shortest_paths.py
    │       │
    │       └── core/tc.py
    │
    ├── core/shortcut.py
    │       │
    │       └── core/hopset.py
    │
    ├── core/generators.py
    │
    ├── core/io/json.py
    │
    ├── core/work_depth.py
    │
    └── core/invariants.py
```

## Module Index

The above diagram lists the algorithm-graph dependency roots. The
following modules are part of the implementation but not on the
critical path of the API:

| Module | Responsibility |
|---|---|
| `core/csr.py` | Build forward/reverse CSR arrays from a `Digraph`. |
| `core/predictor.py` | Heuristic graph-property estimators (`predict_omega`, `predict_epsilon`). |
| `core/tuner.py` | `auto_tune` — pick a `RefinementConfig` based on graph density. |
| `core/spectrum.py` | Eigenvalues and spectral-gap helpers for the SRG fixtures. |
| `core/snapshot.py` | `@dataclass` snapshots for per-call inputs/outputs. |
| `core/trace.py` | `trace()` context manager for opt-in timing logs. |
| `core/metrics.py` | Opt-in counter and histogram collectors. |
| `core/errors.py` | The exception hierarchy. |
| `core/backends/` | `Backend` Protocol and `ParallelContext` (sequential / threads / processes). |
| `core/io/arrow.py` | Arrow IPC serialization (optional, requires `pyarrow`). |
| `core/io/networkx.py` | `to_networkx` / `from_networkx` (optional, requires `networkx`). |
| `proto/graph.py` | The `Graph` duck-typed Protocol. |
| `proto/rng.py` | The `RNG` Protocol. |
| `proto/store.py` | The `Store` Protocol. |
| `cli/main.py` | The `reachq` console-script entry point. |

## Future Considerations

- **True Parallelism**: The work/depth model is simulated. A future version
  could integrate with parallel runtimes (e.g., `multiprocessing`, `concurrent.futures`,
  or `ray`).
- **Fast Matrix Multiplication**: TC uses sparse Boolean matmul (scipy.sparse).
  Runtime ω detection exists (`reachq/research/blas_omega.py`, feeding the
  work-comparison analysis in `core/shortcut.py`), but the TC kernel itself
  does not switch to a fast-MM library; that remains future work.
