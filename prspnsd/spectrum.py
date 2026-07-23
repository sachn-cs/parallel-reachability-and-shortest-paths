"""Spectrum helpers for the SRG/Hamming fixtures.

For symmetric graph generators (Petersen, SRGs, Hamming), the adjacency
spectrum is known analytically. We use scipy/numpy to compute it
empirically and cross-check against the published values.

Honest scope: this is a *cross-check*, not an algorithm improvement.
We document the spectral structure of the test fixtures so that any
unexpected deviation in the shortcut-set construction can be
explained by spectral properties (eigenvalue gap, mixing time) rather
than flagged as a bug.
"""

from __future__ import annotations

import numpy as np


def spectrum(graph) -> np.ndarray:
    """Return the eigenvalues of the adjacency matrix of *graph*.

    The adjacency matrix is built for vertices labelled by their
    position in ``graph.vertices()``. For an undirected graph this
    returns a real symmetric matrix and a sorted real spectrum.

    Returns a 1-D numpy array sorted ascending.
    """
    vertices = sorted(graph.vertices(), key=lambda v: str(v))
    n = len(vertices)
    index = {v: i for i, v in enumerate(vertices)}
    adj = np.zeros((n, n), dtype=np.int64)
    for u in vertices:
        for v in graph.out_edges.get(u, set()):
            adj[index[u], index[v]] = 1
    eigs = np.linalg.eigvalsh(adj.astype(float))
    return np.sort(eigs)


def spectral_gap(graph) -> float:
    """Largest absolute non-trivial eigenvalue of *graph*.

    For a connected graph, this is max(|lambda_2|, |lambda_n|) where
    lambda_1 > lambda_2 >= ... >= lambda_n are the eigenvalues.
    """
    eigs = spectrum(graph)
    if len(eigs) < 2:
        return 0.0
    return float(max(abs(eigs[-2]), abs(eigs[0])))