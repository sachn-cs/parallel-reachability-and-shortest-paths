"""Reached exceptions for reachq.

All public APIs raise ``ReachqError`` (or a subclass) instead of
bare ``ValueError``/``TypeError`` so callers can catch the
algorithm-specific failures without leaking Python built-ins.

Exception hierarchy::

    ReachqError
        ReachqValueError       -- invalid scalar argument
        ReachqTypeError        -- argument of the wrong type
        ReachqGraphError       -- graph structure/precondition failure
            TransitiveClosureBudgetError
        ReachqBackendError     -- execution backend failure
        ReachqConfigError      -- invalid configuration
"""

from __future__ import annotations


class ReachqError(Exception):
    """Base exception for all reachq errors."""


class ReachqValueError(ReachqError, ValueError):
    """Invalid scalar argument."""


class ReachqTypeError(ReachqError, TypeError):
    """Argument of the wrong type."""


class ReachqGraphError(ReachqError):
    """Graph structure or precondition failure."""


class ReachqBackendError(ReachqError):
    """Execution backend failure."""


class ReachqConfigError(ReachqError):
    """Invalid configuration."""


__all__ = [
    "ReachqError",
    "ReachqValueError",
    "ReachqTypeError",
    "ReachqGraphError",
    "ReachqBackendError",
    "ReachqConfigError",
]
