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

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from reachq.core.graph import Digraph


def spectrum(graph: Digraph) -> np.ndarray:
    """Return the eigenvalues of the adjacency matrix of ``graph``.

    The adjacency matrix is built for vertices labelled by their
    position in ``graph.vertices()``. For an undirected graph this
    returns a real symmetric matrix and a sorted real spectrum.

    Args:
        graph: The input digraph.

    Returns:
        1-D numpy array of eigenvalues sorted ascending.
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


def spectral_gap(graph: Digraph) -> float:
    """Largest absolute non-trivial eigenvalue of ``graph``.

    For a connected graph, this is ``max(|λ_2|, |λ_n|)`` where
    ``λ_1 > λ_2 >= ... >= λ_n`` are the eigenvalues.

    Args:
        graph: The input digraph.

    Returns:
        The spectral gap, or 0.0 if the graph has fewer than 2
        eigenvalues.
    """
    eigs = spectrum(graph)
    if len(eigs) < 2:
        return 0.0
    return float(max(abs(eigs[-2]), abs(eigs[0])))
