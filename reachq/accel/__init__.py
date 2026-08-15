"""Acceleration backends (Cython, Rust, Numba, Ray, Dask, GraphBLAS).

Status: **experimental, not shipped**. The PyPI wheel and sdist
contain only the pure-Python fallback wrappers; the Cython ``.pyx``
sources and Rust ``.rs`` sources live in the git repository only.
See ``docs/accel.md`` for the build instructions and the
performance caveats.

The subpackages are:

- ``cython``: BFS and Dijkstra kernels (``reachq/accel/cython``).
- ``numba``: JIT-compiled BFS / Dijkstra helpers.
- ``rust``: PyO3 bindings to a Rust BFS implementation.
- ``ray``, ``dask``, ``graphblas``: distributed / matrix-based
  backends (require optional dependencies).
"""
