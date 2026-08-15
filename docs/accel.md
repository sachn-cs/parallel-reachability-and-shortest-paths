# Acceleration Backends (experimental, not shipped)

`reachq/accel/` contains optional, **experimental** scaffolding for native
kernels (Cython, Rust, Numba) plus Dask/Ray/GraphBLAS hooks. It is **not
part of the PyPI wheel**: `pip install reachq` gives you a pure-Python
package with no JIT and no native extensions.

## What ships vs what does not

| Component | In the PyPI wheel / sdist? |
|---|---|
| `reachq.core.*` pure-Python algorithms | yes |
| `reachq.accel` wrapper modules + pure-Python fallbacks (`bfs.py`, `dijkstra.py`, `setup.py`) | yes |
| Cython `.pyx` kernels (`reachq/accel/cython`) | **no** (git repo only) |
| Compiled `_cy_*.so` / Rust `.so` extensions | **no** |
| Rust source (`reachq/accel/rust`, `Cargo.toml`, `src/lib.rs`) | **no** (git repo only) |

The shipped wheel and sdist contain only the pure-Python fallback
wrappers. The `.pyx` and Rust sources live only in the git repository,
so the kernels cannot be compiled from an installed package. There is
**no build hook**: `pip install "reachq[accel-cython]"` only installs
build dependencies (`cython`), it does not compile anything.

## Status and support

- **Experimental.** These backends are scaffold, not a supported feature.
  They are not exercised by CI beyond the pure-Python fallback path, and
  the speedups in this document are illustrative, not measured against
  the shipped package.
- The only behavior guaranteed and tested is the fallback: every wrapper
  falls back to the pure-Python implementations in `reachq.core.bfs` and
  `reachq.core.shortest_paths` when the compiled extension is absent
  (covered by `tests/test_accel_fallbacks.py`).
- Do not rely on the native kernels for correctness or performance until
  a build + test path is added and CI-verified.

## If you build them anyway

This requires a **git checkout** of the repo — the kernel sources are
not in the PyPI wheel or sdist. Building the Cython kernels requires a C
compiler and numpy headers:

```bash
cd reachq/accel/cython
python setup.py build_ext --inplace
```

This produces `_cy_bfs*.so` and `_cy_dijkstra*.so` next to the `.pyx`
files; the wrappers `reachq.accel.cython.bfs` and
`reachq.accel.cython.dijkstra` pick them up on the next import. The Rust
backend builds with `maturin develop --release` in `reachq/accel/rust`.

## Backend overview

| Backend | Build tool | Speedup vs pure-Python (illustrative) |
|---|---|---|
| **Cython** | `python setup.py build_ext` | 5-50x for CSR BFS, 3-10x for Dijkstra |
| **Numba** | none (JIT-compiles on first call) | 3-30x after warmup |
| **Rust** | `maturin develop --release` | 10-100x for hot loops |

All expose the same Python API:

- `cy_bfs_forward(indptr, indices, source, n, max_depth=...) -> ndarray[bool]`
- `cy_bfs_backward(indptr_rev, indices_rev, source, n, max_depth=...) -> ndarray[bool]`
- `cy_dijkstra(indptr, indices, weights, source, n) -> ndarray[float64]`

Plus helpers `is_cython_available()`, `is_numba_available()`,
`is_rust_available()` that report whether a compiled kernel is loadable
(always `False` for a default install).

## Adding a new backend

To add a new backend (e.g., a GPU kernel):

1. Implement the three kernel functions in your language of choice.
2. Build a Python extension module exposing those functions.
3. Add a wrapper module in `reachq/accel/<name>/__init__.py` that
   tries `import <your_extension>` and falls back to the
   pure-Python implementations.
4. Add an `is_<name>_available()` helper.
5. Add tests in `tests/test_accel_fallbacks.py` covering the
   fallback path.
