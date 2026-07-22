# Architecture

This document describes the high-level architecture of PRSPNSD and how its
components interact.

## Overview

PRSPNSD is organized into six layers, each with clear responsibilities:

```
┌─────────────────────────────────────────────────┐
│            Validation Layer (invariants.py)      │
├─────────────────────────────────────────────────┤
│     Parallel Simulation Layer (work_depth.py)   │
├─────────────────────────────────────────────────┤
│  Shortcut/Hopset Layer (shortcut_set, hopset)   │
├─────────────────────────────────────────────────┤
│  Generator/Serialization Layer (generators, ser) │
├─────────────────────────────────────────────────┤
│  Algorithm Layer (reachability, shortest_paths)  │
├─────────────────────────────────────────────────┤
│         Graph Layer (graph.py)                   │
└─────────────────────────────────────────────────┘
```

## Layer Descriptions

### Graph Layer (`graph.py`)

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

- **`reachability.py`**: BFS, reverse BFS, SCC decomposition (Kosaraju),
  topological sort, parallel BFS with shortcuts
- **`shortest_paths.py`**: Dijkstra, A*, truncated Dijkstra, hop-bounded SSSP,
  shortest path trees
- **`transitive_closure.py`**: Matrix multiplication TC (numpy BLAS), brute-force
  BFS-based TC, subset TC

### Shortcut/Hopset Layer

The paper's main algorithmic contributions:

- **`shortcut_set.py`**: JLS shortcut set algorithm with TC-Pruning (Theorem 2).
  Constructs beta-shortcut sets in near-linear time.
- **`hopset.py`**: CFR hopset algorithm with TruncSSSP-Pruning (Theorem 4).
  Constructs (beta, epsilon)-hopsets in near-linear time.

Both handle SCC contraction automatically via the high-level wrappers:
- `build_shortcut_set_for_reachability()`
- `build_hopset_for_sssp()`

### Generator/Serialization Layer

Utilities for reproducible experiments:

- **`generators.py`**: Deterministic graph generators for paths, cycles, DAGs,
  dense graphs, grids, SCC-structured graphs, and weighted variants.
- **`serialization.py`**: JSON serialization/deserialization for all graph types.

### Parallel Simulation Layer (`work_depth.py`)

Since Python lacks PRAM support, this module provides explicit work/depth
accounting:

- **`WorkDepthAccountant`**: Tracks simulated work, depth, and observed runtime.
- **Recording functions**: `record_bfs`, `record_dijkstra`, `record_matrix_multiply`,
  etc. add theoretical costs to the accountant.
- **Theoretical bounds**: `theoretical_shortcut_work`, `theoretical_hopset_work`,
  etc. compute expected PRAM bounds.

This separation ensures we never conflate wall-clock time with theoretical
parallel bounds.

### Validation Layer (`invariants.py`)

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
[SCC Contraction]  (shortcut_set.py / hopset.py)
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
    └──► [Invariant Validation]  (invariants.py)
```

## Design Principles

1. **Determinism**: All randomized algorithms accept `random_seed` parameters
   and use seeded `random.Random` instances.

2. **Separation of Concerns**: Graph structures, algorithms, and validation
   are cleanly separated. Graph helpers (`partition_by_labels`,
   `contract_sccs`) are co-located in `graph.py` since they operate
   directly on graph internals.

3. **OO Hierarchy**: Inheritance only for genuine is-a relationships.
   `Graph` → `Digraph` → `WeightedDigraph`. Template hooks enable shared
   operations without code duplication.

4. **Theoretical Fidelity**: Asymptotic complexity is documented and tracked
   via the work/depth model.

5. **Testability**: Every public function has corresponding tests with both
   positive and negative cases. Test coverage is 97%.

6. **Extensibility**: New graph types can be added by subclassing `Graph`
   and implementing the four template hooks.

## Module Dependencies

```
graph.py          (no internal dependencies; lazy import from reachability.py
    │              in contract_sccs)
    │
    ├── reachability.py
    │       │
    │       ├── shortest_paths.py
    │       │       │
    │       │       └── transitive_closure.py
    │       │
    │       └── shortcut_set.py
    │               │
    │               └── hopset.py
    │
    ├── generators.py
    │
    ├── serialization.py
    │
    ├── work_depth.py
    │
    └── invariants.py
```

## Future Considerations

- **True Parallelism**: The work/depth model is simulated. A future version
  could integrate with parallel runtimes (e.g., `multiprocessing`, `concurrent.futures`,
  or `ray`).
- **Fast Matrix Multiplication**: Current TC uses standard BLAS (ω = 3). Future
  work could integrate fast MM libraries for ω < 3.
- **Type stubs**: A `py.typed` marker would enable PEP 561 compliance for
  downstream type checking.
