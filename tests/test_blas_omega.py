"""Tests for reachq.blas_omega (runtime omega detection)."""

from __future__ import annotations

from reachq.research.blas_omega import (
    BLAS_OMEGA_TABLE,
    detect_blas_vendor,
    omega_table,
    runtime_omega,
)


class TestDetectBlasVendor:
    def test_returns_string_or_none(self):
        v = detect_blas_vendor()
        assert v is None or isinstance(v, str)

    def test_runtime_omega_is_a_float(self):
        omega = runtime_omega()
        assert isinstance(omega, float)
        assert 2.0 <= omega <= 3.0, f"omega out of plausible range: {omega}"


class TestOmegaTable:
    def test_all_known_vendors_have_entries(self):
        assert "openblas" in omega_table()
        assert "accelerate" in omega_table()
        assert "mkl" in omega_table()
        assert "blis" in omega_table()
        assert "netlib" in omega_table()

    def test_omega_in_range_for_each(self):
        for vendor, omega in BLAS_OMEGA_TABLE.items():
            assert 2.0 <= omega <= 3.0, f"{vendor}: omega={omega} out of range"

    def test_default_schoolbook_is_3(self):
        # netlib / unknown vendor should default to the classical schoolbook.
        assert BLAS_OMEGA_TABLE["netlib"] == 3.0
