"""Tests for prspnsd.spectrum (Paper 2/3 spectral cross-check)."""

from __future__ import annotations

import pytest

from prspnsd.generators import (
    hamming_graph,
    paley_graph,
    petersen_graph,
    shrikhande_graph,
)
from prspnsd.spectrum import spectral_gap, spectrum


class TestSpectrumHelpers:
    def test_spectrum_petersen(self):
        """Petersen spectrum: {3, 1^5, -2^4}."""
        g = petersen_graph()
        eigs = sorted(spectrum(g).tolist())
        # Round to avoid float noise.
        rounded = sorted(round(e, 4) for e in eigs)
        assert rounded == sorted([-2.0] * 4 + [1.0] * 5 + [3.0])

    def test_spectrum_paley_13(self):
        """Paley(13): eigenvalues 6, (-1+sqrt(13))/2 (~1.303) and (-1-sqrt(13))/2 (~-2.303),
        each with multiplicity 6."""
        import math
        g = paley_graph(13)
        eigs = sorted(spectrum(g).tolist())
        sqrt13 = math.sqrt(13)
        plus = (-1 + sqrt13) / 2
        minus = (-1 - sqrt13) / 2
        expected = sorted([plus] * 6 + [minus] * 6 + [6.0])
        assert len(eigs) == len(expected)
        for actual, exp in zip(eigs, expected):
            assert actual == pytest.approx(exp, abs=1e-9)

    def test_spectrum_shrikhande_rook(self):
        """rook's graph K_4 ☐ K_4: eigenvalues 6, 2*6, -2*9."""
        g = shrikhande_graph()
        eigs = sorted(round(e, 4) for e in spectrum(g).tolist())
        assert eigs == sorted([-2.0] * 9 + [2.0] * 6 + [6.0])

    def test_spectrum_hamming_2_3(self):
        """H(2, 3) = K_3 ☐ K_3: eigenvalues 4, 1*4, -2*4."""
        g = hamming_graph(2, 3)
        eigs = sorted(spectrum(g).tolist())
        expected = sorted([-2.0] * 4 + [1.0] * 4 + [4.0])
        assert len(eigs) == len(expected)
        for actual, exp in zip(eigs, expected):
            assert actual == pytest.approx(exp, abs=1e-9)

    def test_spectral_gap_is_largest_non_trivial(self):
        """For a connected k-regular graph, lambda_1 = k and the spectral
        gap is max(|lambda_2|, |lambda_n|)."""
        g = petersen_graph()  # 3-regular, 10 vertices
        gap = spectral_gap(g)
        assert gap == pytest.approx(2.0)  # max(|-2|, |1|) = 2

    def test_spectral_gap_empty_graph(self):
        from prspnsd.graph import Digraph
        g = Digraph()
        assert spectral_gap(g) == 0.0