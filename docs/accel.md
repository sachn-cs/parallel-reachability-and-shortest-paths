# Acceleration Backends

reachq ships with optional acceleration backends for performance-critical
workloads. All backends expose the same Python API and fall back to the
pure-Python implementation when the compiled extension is unavailable.

## Backend overview

| Backend | Build tool | Speedup vs pure-Python | When to use |
|---|---|---|---|
| **Cython** | `python setup.py build_ext` | 5-50x for CSR BFS, 3-10x for Dijkstra | Production deployments with a C compiler available |
| **Numba** | none (JIT-compiles on first call) | 3-30x after warmup | Quick experimentation without a build step |
| **Rust** | `maturin develop` | 10-100x for hot loops | When maximum throughput matters and Rust toolchain is available |

All three expose identical Python APIs:

- `cy_bfs_forward(indptr, indices, source, n, max_depth=...) -> ndarray[bool]`
- `cy_bfs_backward(indptr_rev, indices_rev, source, n, max_depth=...) -> ndarray[bool]`
- `cy_dijkstra(indptr, indices, weights, source, n) -> ndarray[float64]`

Plus helpers `is_cython_available()`, `is_numba_available()`,
`is_rust_available()`.

## Building the Cython extensions

```bash
cd reachq/accel/cython
python setup.py build_ext --inplace
```

The compiled extensions (`_cy_bfs*.so` and `_cy_dijkstra*.so`)
appear next to the `.pyx` files. The wrapper modules
`reachq.accel.cython.bfs` and `reachq.accel.cython.dijkstra` will
pick them up automatically on the next Python startup.

For CI/CD, install with `pip install reachq[accel-cython]` and
build the extensions in the install hook.

## Using Numba JIT

Numba is a JIT compiler; no build step is required. The first call
to each kernel pays a one-time compilation cost (typically a few
seconds per kernel). After that, subsequent calls run at
near-native speed.

```python
from reachq.accel.numba import njit_bfs_forward, is_numba_available

print("Numba available:", is_numba_available())
# ...
```

## Building the Rust extensions

```bash
cd reachq/accel/rust
maturin develop --release
```

The compiled extension `_reachq_rust` is importable as
`reachq.accel.rust._reachq_rust`. Maturin handles the PyO3 glue
and produces a Python-compatible `.so` file.

For PyPI distribution, use `maturin build --release` to produce
wheels, then upload to your index.

## Fallback behaviour

When the compiled extension is unavailable, the wrapper functions
call into the equivalent pure-Python code in `reachq.core.bfs`
and `reachq.core.shortest_paths`. The fallback is always
correct; the only downside is performance.

You can check which backend is active at runtime via
`is_cython_available()`, `is_numba_available()`, and
`is_rust_available()`.

## Benchmarks

See `benchmarks/` for asv suites comparing the backends. In
practice:

- Pure-Python BFS over a 100k-edge graph: ~5 seconds.
- Cython BFS over the same graph: ~0.1 seconds.
- Numba BFS over the same graph (after warmup): ~0.3 seconds.
- Rust BFS over the same graph: ~0.05 seconds.

Numbers are illustrative; actual performance depends on the
graph structure and the machine.

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