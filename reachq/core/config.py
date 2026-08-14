"""Centralised logging configuration and algorithmic refinement config.

Call ``configure_logging()`` once at the entry point of a CLI / script. Module
loggers (``logging.getLogger(__name__)``) inside ``reachq`` pick up the
handler automatically because we attach to the root logger.

``RefinementConfig`` is a frozen dataclass that replaces the old ``Flags``
class. It controls which algorithmic refinements are active.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, fields

CONFIGURED: bool = False


@dataclass(frozen=True, slots=True)
class RefinementConfig:
    """Per-call toggle for algorithmic refinements. Default: all on.

    Replaces the old ``Flags`` class. Frozen and immutable — construct a
    new instance to change settings.

    Examples:
        >>> RefinementConfig()
        RefinementConfig(...)
        >>> RefinementConfig(enable_tc_pruning=False)
        RefinementConfig(...)
    """

    adaptive_sampling: bool = True
    label_compress: bool = True
    skip_condense: bool = True
    hop_bounded_bfs: bool = True
    degree_ordered_pivots: bool = True
    tight_tc_trigger: bool = True
    skip_trivial_part: bool = True
    enable_tc_pruning: bool = True
    parallel: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, bool] | None = None) -> RefinementConfig:
        """Construct from a partial dict. Missing keys default to True."""
        if not d:
            return cls()
        valid = {f.name for f in fields(cls)}
        bad = set(d) - valid
        if bad:
            raise ValueError(
                f"Unknown refinements: {sorted(bad)}; valid: {sorted(valid)}"
            )
        return cls(**{k: v for k, v in d.items() if k in valid})


def configure_logging(level: int | str | None = None) -> None:
    """Idempotent logger setup.

    Idempotent so importing this module multiple times (which happens in
    tests) doesn't double-attach handlers.
    """
    global CONFIGURED
    if CONFIGURED:
        return
    if level is None:
        env = os.environ.get("REACHQ_LOG", "INFO").upper()
        level = getattr(logging, env, logging.INFO)
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)
    CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name, configuring on first call."""
    configure_logging()
    return logging.getLogger(name)
