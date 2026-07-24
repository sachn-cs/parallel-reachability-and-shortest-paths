"""Centralised logging configuration.

Call ``configure()`` once at the entry point of a CLI / script. Module
loggers (``logging.getLogger(__name__)``) inside ``reachq`` pick up the
handler automatically because we attach to the root logger.

Honour the ``REACHQ_LOG`` environment variable: ``DEBUG``, ``INFO``
(default), ``WARNING``, ``ERROR``. Or pass an explicit level to
``configure``.
"""

from __future__ import annotations

import logging
import os
import sys

CONFIGURED: bool = False


def configure(level: int | str | None = None) -> None:
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
    configure()
    return logging.getLogger(name)
