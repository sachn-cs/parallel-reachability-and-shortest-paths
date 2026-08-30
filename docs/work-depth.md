# Work/Depth Instrumentation

The paper analyzes algorithms in the PRAM work/depth model. Since Python does
not provide PRAM, we simulate work and depth explicitly.

## Model

- **Work** = total number of operations performed by the algorithm.
- **Depth** = length of the longest critical path (span).

Our simulation tracks both quantities alongside observed wall-clock time, but
they are never conflated.

## WorkDepthAccountant

The central type is `WorkDepthAccountant` in `reachq/core/work_depth.py`.

```python
from reachq.work_depth import WorkDepthAccountant, record_bfs

wd = WorkDepthAccountant()
wd.start_timer()
# ... run algorithm ...
wd.stop_timer()

record_bfs(wd, n=100, m=200)
print(wd.summary())
```

### Composition Rules

- **Sequential composition**: work and depth add.
- **Parallel composition**: work sums; depth takes the maximum across branches.

These rules mirror standard PRAM composition.

## Recording Functions

Each major primitive has a recording function that adds its asymptotic cost:

| Primitive | Work | Depth |
|-----------|------|-------|
| BFS | O(m) | O(n) |
| Dijkstra | O(m log n) | O(m log n) |
| Matrix multiply | O(n^ω) | O(log n) |
| Transitive closure | O(n^ω) | O(log n) |
| TC-Pruning | O(|R|^ω) | O(log |R|) |
| TruncSSSP-Pruning | O(|R| * m_R) | O(|R| * m_R) |
| Shortcut construction | O~(m + n ρ^{2ω-2}) | O~(n) |
| Hopset construction | O~(m/ε^2 + n ρ^4) | O~(n) |

The recording functions accept `accountant=None` to allow unconditional
calls that silently do nothing when instrumentation is disabled.

## Theoretical Bounds

Helper functions provide the paper's theoretical bounds for comparison:

- `theoretical_shortcut_work(n, m, rho, omega)` — Theorem 2 work bound.
- `theoretical_shortcut_depth(n, rho)` — Theorem 2 parallel depth bound.
- `theoretical_hopset_work(n, m, rho, epsilon)` — Theorem 4 work bound.
- `theoretical_hopset_depth(n, m, rho)` — Theorem 4 parallel depth bound.

These are used by the CLI `--verbose` flag to display bounds alongside
observed construction times.

## Limitations

- The simulated work is a coarse asymptotic estimate, not an exact operation
  count.
- The simulated depth does not reflect actual parallel execution because Python
  is sequential.
- We do not claim PRAM equivalence. The instrumentation is for traceability
  and educational purposes only.

## SpanProfiler

For an *empirical* parallel-span lower bound, `reachq/core/work_depth.py`
also exposes `SpanProfiler`. The construction is run sequentially on
one process and each coarse phase (sample, partition, recursion) is
timed. The sum of phase times is a lower bound on the true PRAM
span: real parallelism can only be faster than sequential per-phase
work. The `summary()` method returns both the measured span and
the theoretical bounds side by side, so you can compare observed
span against the bound for your hardware.

```python
from reachq.work_depth import SpanProfiler, theoretical_shortcut_work

sp = SpanProfiler()
sp.theoretical_work = theoretical_shortcut_work(n=1000, m=5000, rho=2.0)
sp.begin_phase("sample_pivots")
# ...
sp.end_phase()
print(sp.summary())
```

## `parallel_workers` parameter

Both `build_shortcut_set_for_reachability` and `build_hopset_for_sssp`
accept a `parallel_workers: int = 1` argument. The current
implementation is sequential; the parameter is accepted for API
symmetry with the future multi-process path. See
[`docs/algorithms.md`](algorithms.md) for the full semantic note.
