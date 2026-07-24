"""No-op (single-threaded) backend."""

from reachq.core.backends import ParallelContext

SEQUENTIAL = ParallelContext("sequential", 1)
