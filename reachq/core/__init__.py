"""Core algorithms and data structures for reachq.

This package contains the implementation-level modules that the
public API in ``reachq/__init__.py`` re-exports. The internal
layout is grouped by responsibility:

* ``graph`` -- in-memory Digraph and WeightedDigraph.
* ``csr`` -- compressed-sparse-row views.
* ``bfs`` -- CSR numpy BFS kernels (forward, backward, layered).
* ``generators`` -- synthetic graph fixtures.
* ``reachability`` -- BFS, SCC, topological sort, parallel_bfs.
* ``shortest_paths`` -- Dijkstra, A*, hop-bounded SSSP.
* ``closure`` -- Boolean-semiring transitive closure.
* ``hopset`` -- CFR hopset construction.
* ``shortcut`` -- JLS shortcut-set construction.
* ``shortcut_parallel`` -- per-call process-pool dispatcher.
* ``prune`` -- TC-pruning threshold computation and application.
* ``predict`` -- heuristic predictors for omega, epsilon, rho.
* ``work_depth`` -- manual work/depth accounting and span profiling.
* ``spectrum`` -- spectral-gap helpers.
* ``snapshot`` -- per-call inputs/outputs.
* ``generators`` -- synthetic graphs and SNAP dataset loaders.
* ``io`` -- JSON / Arrow / NetworkX serialization.
* ``config`` -- RefinementConfig, logging setup.
* ``trace`` -- ``trace()`` context manager.
* ``errors`` -- typed exception hierarchy.

Everything here is pure Python; the experimental acceleration
backends live in :mod:`reachq.accel`.
"""
