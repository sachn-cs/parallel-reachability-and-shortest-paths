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
from reachq.core.work_depth import WorkDepthAccountant, record_bfs

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
