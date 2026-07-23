"""Detect the matrix-multiplication exponent omega of the runtime BLAS.

The paper's bound (Theorem 2) holds for any omega < 2.371. The
classical schoolbook algorithm achieves omega = 3.0; Strassen's
algorithm 2.807; the current practical best (Williams 2024 / others)
is ~2.37. Different BLAS vendors implement different algorithms
under the hood.

Returns a conservative runtime estimate of omega. Used by
``shortcut_set._OMEGA_DEFAULT`` to tighten the TC trigger bound.

Honest caveat: this function does NOT measure actual omega by
benchmarking. It identifies the BLAS vendor and returns a literature
upper bound for that vendor's published algorithm. Use the value as
an upper bound in the Lemma 2.2 trigger; the actual achievable
omega may be lower (faster) on the running hardware.
"""

from __future__ import annotations

import numpy as np

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

    Inspects numpy.show_config() output for known vendor substrings.
    show_config() prints (it doesn't return), so we capture stdout.
    """
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            np.show_config()
        except Exception:
            return None
    text = buf.getvalue().lower()
    for vendor in BLAS_OMEGA_TABLE:
        if vendor in text:
            return vendor
    # numpy may report a vendor as 'openblas64' (ILP64) or 'mkl_rt'
    # (Intel). Normalise those to the canonical name.
    if "openblas" in text:
        return "openblas"
    if "mkl" in text:
        return "mkl"
    if "accelerate" in text:
        return "accelerate"
    if "blis" in text:
        return "blis"
    return None


def runtime_omega() -> float:
    """Return the conservative runtime omega estimate.

    Default to 3.0 (schoolbook) if the vendor cannot be identified.
    """
    vendor = detect_blas_vendor()
    if vendor is None:
        return 3.0
    return BLAS_OMEGA_TABLE[vendor]


def omega_table() -> dict[str, float]:
    """Return the full vendor -> omega mapping (for inspection)."""
    return dict(BLAS_OMEGA_TABLE)
