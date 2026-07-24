# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""Cython kernel for CSR-based BFS.

Implements a frontier-based BFS over a CSR adjacency representation
that releases the GIL during the inner loop, enabling genuine
parallel speedup on multi-core machines.

The function operates on integer-indexed arrays only; the caller is
responsible for mapping vertices to indices (see
:func:`reachq.core.csr.build_csr_pair`).

Build instructions:

    cd reachq/accel/cython
    python setup.py build_ext --inplace

The compiled extension ``_cy_bfs`` and ``_cy_dijkstra`` will appear
next to the .pyx files. The wrapper module (``bfs.py``) attempts to
import them at runtime; if the import fails (because the extension
has not been compiled), it falls back to the pure-Python
implementation in :mod:`reachq.core.bfs`.
"""

cimport cython
from libc.stdlib cimport malloc, free
from libc.string cimport memset

import numpy as np
cimport numpy as cnp


@cython.boundscheck(False)
@cython.wraparound(False)
def cy_bfs_forward(
    cnp.ndarray[long long, ndim=1] indptr not None,
    cnp.ndarray[long long, ndim=1] indices not None,
    long long source,
    long long n,
    long long max_depth,
):
    """Forward BFS from ``source`` over a CSR adjacency.

    Returns a numpy boolean array ``reached`` of length n where
    ``reached[v]`` is True iff v is reachable from ``source`` in
    at most ``max_depth`` hops. ``reached[source]`` is always True.

    Parameters are typed numpy arrays of dtype ``int64``. The caller
    must build the CSR arrays via
    :func:`reachq.core.csr.build_csr_pair`.

    Releases the GIL during the inner loop. Safe to call from a
    thread pool.
    """
    cdef cnp.ndarray[uchar, ndim=1, cast=True] reached = np.zeros(n, dtype=np.uint8)
    cdef cnp.ndarray[long long, ndim=1] frontier = np.empty(n, dtype=np.int64)
    cdef cnp.ndarray[long long, ndim=1] next_frontier = np.empty(n, dtype=np.int64)

    cdef long long u, v, i, start, end, frontier_size, next_size, depth
    cdef bint in_queue

    if source < 0 or source >= n:
        return reached
    reached[source] = 1
    frontier[0] = source
    frontier_size = 1
    depth = 0

    with nogil:
        while frontier_size > 0 and depth < max_depth:
            next_size = 0
            for i in range(frontier_size):
                u = frontier[i]
                start = indptr[u]
                end = indptr[u + 1]
                for j in range(start, end):
                    v = indices[j]
                    if reached[v] == 0:
                        reached[v] = 1
                        next_frontier[next_size] = v
                        next_size += 1
            # Swap frontiers.
            frontier[:next_size] = next_frontier[:next_size]
            frontier_size = next_size
            depth += 1
    return reached.astype(bool)


@cython.boundscheck(False)
@cython.wraparound(False)
def cy_bfs_backward(
    cnp.ndarray[long long, ndim=1] indptr not None,
    cnp.ndarray[long long, ndim=1] indices not None,
    long long source,
    long long n,
    long long max_depth,
):
    """Backward BFS from ``source`` over the reversed CSR.

    Same semantics as :func:`cy_bfs_forward` but operates on the
    reversed adjacency (``indptr_rev``, ``indices_rev``). Used for
    computing ``R-(G, pivot)`` in the JLS construction.
    """
    cdef cnp.ndarray[uchar, ndim=1, cast=True] reached = np.zeros(n, dtype=np.uint8)
    cdef cnp.ndarray[long long, ndim=1] frontier = np.empty(n, dtype=np.int64)
    cdef cnp.ndarray[long long, ndim=1] next_frontier = np.empty(n, dtype=np.int64)

    cdef long long u, v, i, start, end, frontier_size, next_size, depth

    if source < 0 or source >= n:
        return reached
    reached[source] = 1
    frontier[0] = source
    frontier_size = 1
    depth = 0

    with nogil:
        while frontier_size > 0 and depth < max_depth:
            next_size = 0
            for i in range(frontier_size):
                u = frontier[i]
                start = indptr[u]
                end = indptr[u + 1]
                for j in range(start, end):
                    v = indices[j]
                    if reached[v] == 0:
                        reached[v] = 1
                        next_frontier[next_size] = v
                        next_size += 1
            frontier[:next_size] = next_frontier[:next_size]
            frontier_size = next_size
            depth += 1
    return reached.astype(bool)