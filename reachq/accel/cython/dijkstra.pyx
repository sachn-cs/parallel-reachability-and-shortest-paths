# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""Cython kernel for binary-heap Dijkstra.

Implements Dijkstra's shortest-path algorithm with a binary
min-heap, operating on integer-indexed CSR adjacency. Releases the
GIL during the inner loop; safe for thread-pool dispatch.

Build instructions:

    cd reachq/accel/cython
    python setup.py build_ext --inplace
"""

cimport cython
from libc.stdlib cimport malloc, free

import numpy as np
cimport numpy as cnp


@cython.boundscheck(False)
@cython.wraparound(False)
def cy_dijkstra(
    cnp.ndarray[long long, ndim=1] indptr not None,
    cnp.ndarray[long long, ndim=1] indices not None,
    cnp.ndarray[double, ndim=1] weights not None,
    long long source,
    long long n,
):
    """Dijkstra from ``source`` over a weighted CSR adjacency.

    Returns a numpy float64 array of length n where ``dist[v]`` is
    the shortest-path distance from ``source`` to ``v`` (or
    ``inf`` if unreachable).

    Parameters are typed numpy arrays; the caller builds the CSR
    via :func:`reachq.core.csr.build_csr_pair` and provides a
    parallel weight array of length ``len(indices)``.

    Implementation: binary min-heap with O((n + m) log n) work.
    For dense graphs where m >> n, prefer a Fibonacci heap or a
    GPU kernel; both are out of scope for this module.
    """
    cdef cnp.ndarray[double, ndim=1] dist = np.full(n, np.inf, dtype=np.float64)
    if source < 0 or source >= n:
        return dist

    # Min-heap on (distance, vertex). Python heapq is not nogil-safe,
    # so we implement a tiny inline binary heap.
    cdef long long cap = n + 16
    cdef double *heap_dist = <double *> malloc(sizeof(double) * cap)
    cdef long long *heap_vertex = <long long *> malloc(sizeof(long long) * cap)
    cdef long long *heap_pos = <long long *> malloc(sizeof(long long) * n)
    cdef long long heap_size = 0
    cdef long long u, v, j, k, parent, child
    cdef double du, alt

    try:
        for k in range(n):
            heap_pos[k] = -1

        dist[source] = 0.0
        heap_dist[0] = 0.0
        heap_vertex[0] = source
        heap_pos[source] = 0
        heap_size = 1
        with nogil:
            while heap_size > 0:
                # Pop the minimum.
                u = heap_vertex[0]
                du = heap_dist[0]
                heap_size -= 1
                if heap_size > 0:
                    heap_dist[0] = heap_dist[heap_size]
                    heap_vertex[0] = heap_vertex[heap_size]
                    heap_pos[heap_vertex[0]] = 0
                    # Sift down.
                    k = 0
                    while True:
                        child = 2 * k + 1
                        if child >= heap_size:
                            break
                        if child + 1 < heap_size and heap_dist[child + 1] < heap_dist[child]:
                            child += 1
                        if heap_dist[k] <= heap_dist[child]:
                            break
                        heap_dist[k], heap_dist[child] = heap_dist[child], heap_dist[k]
                        heap_vertex[k], heap_vertex[child] = heap_vertex[child], heap_vertex[k]
                        heap_pos[heap_vertex[k]] = k
                        heap_pos[heap_vertex[child]] = child
                        k = child
                heap_pos[u] = -2  # Settled.
                # Relax outgoing edges.
                j = indptr[u]
                while j < indptr[u + 1]:
                    v = indices[j]
                    alt = du + weights[j]
                    if alt < dist[v]:
                        dist[v] = alt
                        if heap_pos[v] == -2:
                            # Already settled: re-push (lazy deletion).
                            heap_dist[heap_size] = alt
                            heap_vertex[heap_size] = v
                            heap_pos[v] = heap_size
                            heap_size += 1
                            # Sift up.
                            k = heap_size - 1
                            while k > 0:
                                parent = (k - 1) // 2
                                if heap_dist[parent] <= heap_dist[k]:
                                    break
                                heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                                heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                                heap_pos[heap_vertex[parent]] = parent
                                heap_pos[heap_vertex[k]] = k
                                k = parent
                        elif heap_pos[v] >= 0:
                            # Decrease-key: update in place and sift up.
                            k = heap_pos[v]
                            heap_dist[k] = alt
                            while k > 0:
                                parent = (k - 1) // 2
                                if heap_dist[parent] <= heap_dist[k]:
                                    break
                                heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                                heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                                heap_pos[heap_vertex[parent]] = parent
                                heap_pos[heap_vertex[k]] = k
                                k = parent
                        else:
                            # New vertex: push and sift up.
                            heap_dist[heap_size] = alt
                            heap_vertex[heap_size] = v
                            heap_pos[v] = heap_size
                            heap_size += 1
                            k = heap_size - 1
                            while k > 0:
                                parent = (k - 1) // 2
                                if heap_dist[parent] <= heap_dist[k]:
                                    break
                                heap_dist[parent], heap_dist[k] = heap_dist[k], heap_dist[parent]
                                heap_vertex[parent], heap_vertex[k] = heap_vertex[k], heap_vertex[parent]
                                heap_pos[heap_vertex[parent]] = parent
                                heap_pos[heap_vertex[k]] = k
                                k = parent
                    j += 1
    finally:
        free(heap_dist)
        free(heap_vertex)
        free(heap_pos)
    return dist