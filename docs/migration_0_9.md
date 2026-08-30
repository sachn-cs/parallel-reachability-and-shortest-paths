# Migration to v0.9.0

This release is a correctness-and-reproducibility milestone. The
internal algorithm representation and several contracts have
changed. The list below names each breaking change and points
to the regression test that pins the new behavior.

## Breaking changes

### 1. Graph vertex storage

* ``Graph.vertex_set`` is gone. Insertion order is preserved as
  ``_insertion_order`` (private) and exposed via ``vertices()``
  which returns a tuple.
* ``graph.vertices()`` returns ``tuple[object, ...]`` instead of
  ``set[object]``. Order is the canonical insertion order; SCC,
  sampling, partition, recursion, and CSR all consume it.
* New methods: ``graph.index_of(v)``, ``graph.vertex_at(i)``,
  ``graph.iter_vertices()``.

### 2. SSSP heap contracts

* ``dijkstra`` heap tuple: ``(distance, counter, vertex)``.
* ``truncated_dijkstra`` heap tuple: ``(distance, counter, vertex)``.
* ``shortest_path_hopbound`` heap tuple:
  ``(distance, hops, counter, vertex)``.
* ``astar`` heap tuple: ``(f_score, cost_sofar, counter, vertex)``.
* ``shortest_path_tree`` heap tuple: ``(distance, counter, vertex)``.
* Heap entries never compare vertex objects, so arbitrarily
  hashable types (``object()``, ``frozenset``, custom classes
  without ``__lt__``) work uniformly.

### 3. Reachability contracts

* ``dijkstra(g, source)``: unreachable vertices are **absent**
  from the returned mapping. ``shortest_path(g, source, target)``
  returns the new sentinel
  :data:`reachq.shortest_paths.UNREACHABLE`.
* All SSSP entry points raise ``KeyError`` for sources not in
  the graph and ``ValueError`` for negative
  ``max_distance``/``max_hops``.

### 4. ``shortest_path_hopbound`` correctness

* The implementation is now layered DP keyed by
  ``(vertex, hops)``; it no longer suppresses costlier arrivals
  that leave hops needed to reach the target within the bound.

### 5. Hopset condensation

* The weighted SCC condensation mapping that emitted
  shortcuts via ``scc_rep[idx]`` is removed. CFR runs directly
  on the original weighted graph. Every emitted hopset edge
  weight equals the original shortest-path distance.
* ``cfr_hopset`` is no longer exported from the top-level
  package; the functions still exist in ``reachq.hopset``
  for tests and direct callers.

### 6. Transitive closure

* ``transitive_closure_matrix`` is removed. The replacement is
  :func:`reachq.core.tc.transitive_closure_boolean`, which runs
  in the Boolean semiring (no integer path counts, no overflow).
* New ``max_pairs`` budget with
  :class:`reachq.core.tc.TransitiveClosureBudgetError`.
* ``transitive_closure_on_subset`` accepts and forwards
  ``max_pairs``.

### 7. JLS algorithm package

* ``reachq.core.algorithm`` is now a subpackage:
  ``algorithm/{state,pivots,partition,recursion,scc_lift,
  parallel,adaptive,wrap}.py``.
* Old ``Flags`` import path is gone. Use
  :class:`reachq.config.RefinementConfig`.
* Parallel dispatch uses ``spawn`` and binds state per-task;
  no module-level globals.
* ``adaptive_sampling`` actually changes the next-level
  sampling constant (no more RNG perturbation).
* The legacy ``sparsify_shortcuts=True`` switch is removed.

### 8. Backends

* ``reachq.core.backends`` is removed. Dispatcher lives in
  :class:`reachq.core.algorithm.parallel.ParallelExecutor` and
  ``imap`` is the explicit name (not ``imap_unordered``).

### 9. Logging

* Library code never touches the root logger. CLI entry points
  must call :func:`reachq.config.configure_logging`
  explicitly.

## Backward compatibility

There is no compatibility layer. The user-facing API changes
listed above are hard cuts.

## Migration recipe

1. Replace any usage of ``graph.vertex_set`` with
   ``graph.vertices()`` (returns a tuple) or
   ``graph.iter_vertices()``.
2. Replace the old "absent vs. ``inf``" judgment with membership
   checks against the returned dict, or comparison against
   :data:`reachq.shortest_paths.UNREACHABLE`.
3. Replace ``transitive_closure_matrix`` with
   ``transitive_closure_boolean`` and add a ``max_pairs`` budget
   if the caller cannot guarantee output stays well-behaved.
4. If you depend on ``reachq.core.backends``, port to
   ``reachq.core.algorithm.parallel.ParallelExecutor``.
5. If you import ``Flags`` from ``reachq``, replace with
   ``RefinementConfig``.
6. If you called :func:`shortest_path_hopbound` and relied on
   the old contract (per-vertex distances), the new contract is
   the same — except that previously omitted costlier arrivals
   are now emitted when they leave hops needed for the target.

## New tests

* ``tests/test_hopbound_dominance.py``: reviewer's counterexample.
* ``tests/test_heap_incomparable_vertices.py``: ``object()``
  vertices across every SSSP variant.
* ``tests/test_hopset_weight_accuracy.py``: SCC weight accuracy
  under multi-``PYTHONHASHSEED`` subprocess runs.
* ``tests/test_algorithm_concurrency.py``: concurrent builds
  with ``flags.parallel=True``.
* ``tests/test_networkx_differential_shortest.py``: NetworkX
  reference for SSSP and hopset approximation.
* ``tests/test_reproducibility_subprocess.py``:
  ``PYTHONHASHSEED`` sweep.
* ``tests/test_regression_v0_9_fixes.py``: regression test
  for each item above.
