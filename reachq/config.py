"""Algorithmic refinement config, runtime introspection, and logging setup.

Public surface:

* :class:`RefinementConfig` -- per-call toggle for algorithmic
  refinements. Frozen dataclass; default is "all on" so the
  caller can omit the argument.
* :func:`runtime_omega` -- conservative runtime estimate of the
  fast-matrix-multiplication exponent ``omega`` based on the
  detected BLAS vendor.
* :func:`configure_logging` -- attach a single stderr handler to
  the ``reachq`` logger. The library never calls this; only CLI /
  script entry points should.
* :func:`get_logger` -- return a per-module logger without
  configuring.

The library never touches the root logger.
"""

from __future__ import annotations

import contextlib
import io
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


# Conservative omega upper bounds per BLAS vendor. Sources:
#   - OpenBLAS 0.3.23 (Apr 2024): Strassen-class, ~2.37.
#   - Accelerate (Apple): Strassen-class, ~2.37.
#   - MKL (Intel): Strassen-class, ~2.37.
#   - BLIS: Strassen-class, ~2.37.
#   - netlib: schoolbook, 3.0.
# All other vendors: default to schoolbook 3.0 unless overridden.
BLAS_OMEGA_TABLE: dict[str, float] = {
    "openblas": 2.5,
    "accelerate": 2.5,
    "mkl": 2.5,
    "blis": 2.5,
    "netlib": 3.0,
}


def detect_blas_vendor() -> str | None:
    """Return the BLAS vendor name as a string, or None if undetected.

    Inspects ``numpy.show_config()`` output for known vendor
    substrings. ``show_config()`` prints (it doesn't return), so we
    capture stdout.

    Returns:
        The detected vendor name (one of :data:`BLAS_OMEGA_TABLE`
        keys, or the normalised ``openblas64`` / ``mkl_rt``
        variants), or ``None`` if no vendor is detected.
    """
    import numpy as np

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            np.show_config()
        except Exception:  # noqa: BLE001 - show_config output is not stable API
            return None
    text = buf.getvalue().lower()
    for vendor in BLAS_OMEGA_TABLE:
        if vendor in text:
            return vendor
    if "openblas" in text:
        return "openblas"
    if "mkl" in text:
        return "mkl"
    if "accelerate" in text:
        return "accelerate"
    if "blis" in text:
        return "blis"
    return None


_runtime_omega_cache: float | None = None


def runtime_omega() -> float:
    """Conservative runtime omega estimate for the running BLAS.

    Defaults to 3.0 (schoolbook) if the vendor cannot be identified.
    The first call's result is cached for the process lifetime --
    the BLAS vendor does not change after interpreter startup.

    Returns:
        The conservative omega for the detected vendor, or 3.0.
    """
    global _runtime_omega_cache
    if _runtime_omega_cache is None:
        vendor = detect_blas_vendor()
        _runtime_omega_cache = BLAS_OMEGA_TABLE[vendor] if vendor is not None else 3.0
    return _runtime_omega_cache


def omega_table() -> dict[str, float]:
    """Return the full vendor -> omega mapping (for inspection)."""
    return dict(BLAS_OMEGA_TABLE)


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


__all__ = [
    "BLAS_OMEGA_TABLE",
    "RefinementConfig",
    "configure_logging",
    "detect_blas_vendor",
    "get_logger",
    "omega_table",
    "runtime_omega",
]
