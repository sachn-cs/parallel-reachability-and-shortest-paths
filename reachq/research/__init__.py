"""Research-only algorithms not covered by the cited papers.

Modules in this subpackage are explicitly marked ``__experimental__``
at the module level. They are not part of the reachq versioning
contract; they may change without a major-version bump.

**Stable boundary**: any code under :mod:`reachq.core` may
import from :mod:`reachq.research` only via the symbols
re-exported here, and only behind an explicit experimental flag.
Production callers should treat the public surface here as
best-effort.

**Importing from production code**: importing anything from
:mod:`reachq.research` inside :mod:`reachq.core` is unsupported.
Doing so means accepting breakage on any release.
"""

from reachq.research.approximation import greedy_shortcut_set
from reachq.research.streaming import StreamingShortcutSet

__all__ = [
    "StreamingShortcutSet",
    "greedy_shortcut_set",
]
