"""Typed exception hierarchy for reachq.

All public APIs raise ``ReachqError`` (or a subclass) instead of
bare ``ValueError``/``TypeError`` so callers can catch the
algorithm-specific failures without leaking Python built-ins.

Exception hierarchy::

    ReachqError
        ReachqValueError       -- invalid scalar argument
        ReachqTypeError        -- argument of the wrong type
        ReachqGraphError       -- graph structure/precondition failure
            TransitiveClosureBudgetError
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


__all__ = [
    "ReachqError",
    "ReachqGraphError",
    "ReachqTypeError",
    "ReachqValueError",
]
