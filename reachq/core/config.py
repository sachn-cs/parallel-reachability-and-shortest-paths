"""Algorithmic refinement config and CLI entry-point logging setup.

``RefinementConfig`` is a frozen dataclass of refinement toggles.
The library never touches the root logger. ``configure_logging``
attaches a single stderr handler; call it once at the entry
point of CLI scripts, not at import time.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class RefinementConfig:
    """Per-call toggle for algorithmic refinements. Default: all on."""

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
    def from_dict(cls, d: dict[str, bool] | None = None) -> "RefinementConfig":
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
    """Attach a single stderr handler to the ``reachq`` logger.

    Idempotent: subsequent calls update the level only.
    Library code never calls this; only CLI / script entry
    points should.
    """
    if level is None:
        env = os.environ.get("REACHQ_LOG", "INFO").upper()
        level = getattr(logging, env, logging.INFO)
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    log = logging.getLogger("reachq")
    log.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name without configuring."""
    return logging.getLogger(name)
