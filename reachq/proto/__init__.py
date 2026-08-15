"""Protocol definitions for reachq extension points.

These Protocols describe the duck-typed interfaces that
third-party code can implement to plug into reachq:

- ``graph.Graph``: the digraph shape the algorithms consume.
- ``rng.RNG``: a reproducible random-number source.
- ``store.Store``: a key-value store for snapshots.

The ``Backend`` Protocol previously lived here but has been
consolidated into ``reachq/core/backends/__init__.py`` (the
canonical home, used by all internal callers).
"""
