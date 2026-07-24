"""Typed exceptions for reachq.

All public APIs raise these instead of bare ValueError/TypeError so
callers can catch domain-specific errors.
"""

from __future__ import annotations


class ReachqError(Exception):
    """Base exception for all reachq errors."""


class ReachqValueError(ReachqError, ValueError):
    """Invalid value passed to a reachq function."""


class ReachqTypeError(ReachqError, TypeError):
    """Wrong type passed to a reachq function."""


class ReachqGraphError(ReachqError):
    """Error related to graph structure or constraints."""


class ReachqBackendError(ReachqError):
    """Error in a parallel-execution backend."""


class ReachqConfigError(ReachqError):
    """Invalid configuration."""
