"""No-op (single-threaded) backend.

Re-exports ``SEQUENTIAL`` from ``reachq.core.backends`` so that
``from reachq.core.backends.noop import SEQUENTIAL`` works as an
alternative import path. This module exists for symmetry with the
``threads`` and ``processes`` submodules; it does not define any
new behaviour.
"""

from reachq.core.backends import SEQUENTIAL

__all__ = ["SEQUENTIAL"]
