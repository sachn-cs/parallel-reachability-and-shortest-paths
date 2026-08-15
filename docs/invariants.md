# Invariants and Theorem-Oriented Validation

The `reachq.core.invariants` module provides assertion helpers that encode the
structural properties required by the paper's theorems. These are intended
for testing and debugging, not for production hot paths.

## Reachability Preservation

```python
from reachq.core.invariants import assert_reachability_preserved

assert_reachability_preserved(graph, shortcuts)
```

Verifies that for every vertex v, R^+(G, v) = R^+(G ∪ H, v). This is the
defining property of a shortcut set (Section 2).

## Hopbound Checking

```python
from reachq.core.invariants import assert_hopbound

assert_hopbound(graph, source, shortcuts, beta=5.0)
```

Computes the actual hop count from `source` using BFS on G ∪ H and asserts
it is ≤ beta. Raises `AssertionError` if the bound is violated.

## SCC Cliques

```python
from reachq.core.invariants import assert_scc_shortcuts_form_cliques

assert_scc_shortcuts_form_cliques(graph, shortcuts)
```

Verifies that every SCC becomes a clique in G ∪ H. Theorem 2 requires this
so the condensed DAG is preserved.

## Partition Correctness

```python
from reachq.core.invariants import assert_partition_correctness

assert_partition_correctness(graph, parts)
```

Checks that `parts` is a valid partition of V(G): union equals V(G), parts
are pairwise disjoint.

## Distance Approximation

```python
from reachq.core.invariants import assert_distance_approximation

ratios = assert_distance_approximation(
    graph, hopset, source=0, epsilon=0.1, max_hops=1000
)
```

Verifies the (beta, epsilon)-hopset guarantee:

```
dist_G(s, t) ≤ dist_{G ∪ H}^{(β)}(s, t) ≤ (1 + ε) * dist_G(s, t)
```

Computes exact distances with Dijkstra and approximate distances with
`shortest_path_hopbound`, then asserts the approximation ratio. Returns a
dict mapping vertices to observed ratios.

Raises `AssertionError` if any distance exceeds (1 + ε) times the true
distance or if a reachable vertex is missing from the hop-bounded result.

## Size Bounds

```python
from reachq.core.invariants import (
    assert_shortcut_set_size_bound,
    assert_hopset_size_bound,
)

assert_shortcut_set_size_bound(graph, shortcuts, rho=2.0)
assert_hopset_size_bound(graph, hopset, epsilon=0.1, rho=2.0)
```

Coarse sanity checks against the paper's size bounds:
- Shortcut sets: O~(n ρ^2)
- Hopsets: O~(n/ε^2 + n ρ^2)

These are not tight proofs; they catch gross violations.

## Equivalence Classes

```python
from reachq.core.invariants import check_equivalence_classes

check_equivalence_classes(labels, parts)
```

Verifies that label-based partitioning matches equivalence classes: every
part contains vertices with identical label sets.

## Usage in Tests

All invariant helpers are used by `tests/test_invariants.py`. They can also
be called interactively during development to verify algorithm correctness.
