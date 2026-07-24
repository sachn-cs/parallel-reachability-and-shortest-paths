"""Research-only algorithms not covered by the cited papers.

Modules in this subpackage are experimental. Their soundness,
complexity claims, and API surface are not part of the reachq
versioning contract; they may change without a major-version bump.
"""

from reachq.research.approximation import greedy_shortcut_set
from reachq.research.streaming import StreamingShortcutSet

__all__ = [
    "StreamingShortcutSet",
    "greedy_shortcut_set",
]
