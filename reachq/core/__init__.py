"""Core algorithms and data structures for reachq.

This package contains the implementation-level modules that the
public API in ``reachq/__init__.py`` re-exports. The internal
layout is grouped by responsibility:

- ``graph``: in-memory Digraph and WeightedDigraph representations.
- ``csr``: compressed-sparse-row views used by the BFS kernels.
- ``generators``: synthetic graph fixtures (random, complete, paley,
  shrikhande, hamming, ...).
- ``reachability`` / ``shortest_paths``: low-level BFS and Dijkstra.
- ``algorithm``: the JLS shortcut-set construction and its CFR
  hopset sibling.
- ``hopset``: CFR-with-TruncSSSP-Pruning shared body and the two
  public entry points.
- ``work_depth``: manual work/depth accounting for empirical
  span profiling (NOT a true parallel implementation).
- ``predictor`` / ``tuner``: heuristic graph-property estimators
  used to pick a RefinementConfig preset.
- ``prune``: TC-pruning threshold computation and application.
- ``tc``: transitive-closure helpers (numpy + hashable fallback).
- ``spectrum``: spectral-gap helpers used in sanity checks.
- ``invariants``: runtime checks that align with the cited papers'
  theorem statements.
- ``config``: the ``RefinementConfig`` dataclass (exported as
  ``reachq.Flags``) and the logging configuration.
- ``errors``: the exception hierarchy.
- ``backends``: the ``Backend`` Protocol and ``ParallelContext``
  (sequential / threads / processes).
- ``io``: serialization backends (JSON, Arrow, networkx).
- ``trace``: the ``trace()`` context manager used for opt-in
  timing logs.
- ``metrics``: per-call counters exposed via ``reachq.metrics``.
- ``snapshot``: dataclasses for capturing per-call inputs/outputs.

Everything in this package is pure Python (no JIT, no native
extensions); the experimental acceleration backends live in
``reachq/accel``.
"""
