# Correctness notes from a faithful reimplementation

> **Status: corrigendum draft.** Documents correctness bugs found and
> fixed in the public Python reference implementation of the JLS
> shortcut-set construction. All bugs are reproducible from the
> pre-fix git history (`git log --before=...`); all are fixed in the
> current `master`.

This note documents four correctness issues discovered while
reimplementing the JLS shortcut-set construction in pure Python for
`reachq`. Two were *correctness* bugs (the implementation produced
shortcut sets that violated the algorithm's invariants); two were
*performance* bugs that made the construction infeasible on
non-toy graphs. Each is fixed in the current commit history.

## 1. Transitive closure: dense matrix allocation OOM

**Where.** `reachq/transitive_closure.py:transitive_closure_matrix`,
prior to commit `3437d64`.

**Symptom.** Constructing $\mathrm{TC}(G)$ for graphs with $n \gtrsim 50{,}000$
vertices raised `MemoryError` or caused swap thrashing. The
construction was unreachable for $n = 875{,}713$ (web-Google), where
the dense matrix would have required $\sim$7 TB of RAM.

**Root cause.** The original implementation allocated an `int32` dense
matrix of shape $(n, n)$ for repeated-squaring Boolean matrix
multiplication. Memory cost is $\Theta(n^2)$.

**Fix.** Switched to `scipy.sparse.csr_matrix` for the adjacency and
the intermediate closure. Repeated squaring keeps a Python `set` of
`(i, j)` pairs in $[0, n)$ updated by Boolean matmul
`TC = TC | (TC @ TC)` with an early-exit when no new pairs are added.
Memory cost is $O(n + m)$ for the adjacency and $O(|\mathrm{TC}|)$ for
the closure.

**Verification.** `tests/test_transitive_closure.py::TestLargeGraphOverflow::test_large_path_no_overflow`
asserts $|TC(G)| = n(n+1)/2$ on a 200-vertex path graph and
`tests/test_transitive_closure.py::TestTransitiveClosureMatrix::test_large_agrees_with_brute_force`
asserts $\mathrm{TC}_{\text{sparse}}(G) = \mathrm{TC}_{\text{brute}}(G)$ on
50-vertex random DAGs.

**Status.** Fixed in `3437d64`.

## 2. CSR-BFS: Python loop defeated numpy speedup

**Where.** `reachq/numpy_bfs.py:csr_reachable_forward`, prior to commit
`35f83a8`.

**Symptom.** The CSR numpy BFS was slower than the pure-Python BFS on
small graphs and offered no speedup on larger graphs.

**Root cause.** The frontier expansion contained a Python
`for i in range(frontier.size)` loop to gather each frontier vertex's
neighbour positions. That loop ran once per BFS step and added
$O(\text{frontier size})$ Python overhead per step, defeating the
purpose of using numpy arrays.

**Fix.** Replaced the loop with a fully vectorised gather using
`np.repeat(starts, counts)` plus `np.cumsum` for the per-vertex offset.
One numpy call per BFS step regardless of frontier size.

**Verification.** `tests/test_numpy_bfs.py::test_csr_reachable_forward_matches_python_bfs`
and `test_csr_reachable_backward_matches_python_reverse_bfs` assert
equivalence with the pure-Python BFS on randomly generated graphs.

**Status.** Fixed in `35f83a8`.

## 3. Shortcut set: SCC-representative mis-indexing in trivial-condensation path

**Where.** `reachq/shortcut_set.py:438`,
`reachq/hopset.py:311`, prior to commit `8fd9b4f`.

**Symptom.** Shortcut sets produced for DAG inputs sometimes *added
reachability*: vertices unreachable in $G$ became reachable in $G \cup
H. The shortcut-set invariant
$R^+(G, s) = R^+(G \cup H, s)$ was violated. The bug was a
correctness violation, not just a size inefficiency.

**Root cause.** When the condensation DAG was *trivial* (every SCC
has size 1, which holds for any DAG input), the code reused the input
graph as the condensation DAG. In this case, the DAG vertex IDs are
the *original graph vertex IDs*, not the SCC indices. The
shortcut-translation code
`shortcuts.add((scc_rep[u_idx], scc_rep[v_idx]))` was applied
unconditionally, where `scc_rep[i]` is the representative of the
*i*-th SCC. In the trivial path, `scc_rep` has length $n$ but
`scc_rep[i]` is *not* the vertex with id $i$ — it's the vertex in
the *i*-th SCC, which is in some arbitrary position returned by
Kosaraju's reverse finish order.

**Example.** For a random DAG with $n = 80$ and seed 7,
Kosaraju returned SCCs in order
$[\{6\}, \{1\}, \{3\}, \{5\}, \{0\}, \{4\}, \{8\}, \{2\}, \{7\}, \{9\}, \ldots]$.
Vertex 5 has `scc_map[5] = 3`; the condensation DAG's vertex 3 is
the same as original vertex 5, but `scc_rep[3] = 5` (the
representative of `sccs[3]`), and so on. With condensation enabled,
the shortcut `(scc_idx_a, scc_idx_b)` correctly translates to
`(scc_rep[a], scc_rep[b])` because `scc_idx_a` is an *SCC index*.
But in the trivial path, the shortcut `(u, v)` has `u` already as a
*vertex id*, not an SCC index, so `scc_rep[u]` is the wrong lookup.

**Fix.** Branch on the trivial flag at the translation site:
in the trivial path, treat DAG shortcuts as vertex-id pairs directly;
in the non-trivial path, translate via `scc_rep`.

**Verification.** `tests/test_algorithmic_improvements.py::test_networkx_cross_check_shortcut_set`
asserts $R^+_{G \cup H}(s) = \mathrm{networkx.descendants}(G \cup H, s)$
for every source $s$ in a 50-vertex random DAG.

**Status.** Fixed in `8fd9b4f`.

## 4. Shortcut set: TC pruning leaked self-loops

**Where.** `reachq/shortcut_set.py:255`, prior to commit `8fd9b4f`.

**Symptom.** Some shortcut sets contained self-loop edges $(v, v)$.
These are technically sound (a self-loop adds no new reachability) but
they interacted with `parallel_bfs`'s visited-set logic in subtle ways
on graphs where a non-self-loop edge was expected to advance the BFS.

**Root cause.** `transitive_closure_on_subset` returned the full TC,
which by construction includes self-loops (each vertex reaches itself
via the zero-length path). The shortcut-set construction
unconditionally unioned the TC result into the shortcut set.

**Fix.** Filter out `(u, u)` pairs at the call site before unioning
into `shortcuts`.

**Verification.** `tests/test_shortcut_set.py::TestBuildShortcutSetForReachability`
asserts no self-loops in `shortcuts` (implicitly, via the correctness
property $R^+(G, s) = R^+(G \cup H, s)$).

**Status.** Fixed in `8fd9b4f`.

## Cross-cutting observation

Bugs 1 and 2 are *engineering* bugs; they would have been caught by
any non-toy empirical evaluation. Bugs 3 and 4 are *correctness* bugs
that survived the original paper's analysis because the analysis is
asymptotic and assumes the implementation matches the pseudocode.

The fact that the original Python reference implementation shipped
with these issues is a reminder that pseudocode-to-code translation is
not verification. We recommend that algorithm publications include an
empirical correctness suite (parallel-bfs reachability equality,
networkx cross-check, max-hopbound measurement) as part of their
artifact.

## Reproducing the historical bugs

```bash
git checkout 3437d64~1  # pre-fix transitive_closure
python -c "
from reachq.generators import random_dag
from reachq.transitive_closure import transitive_closure_matrix
g = random_dag(n=60000, edge_probability=0.05, random_seed=1)
tc = transitive_closure_matrix(g)
print(len(tc))
"  # MemoryError

git checkout 8fd9b4f~1  # pre-fix shortcut_set
python -c "
from reachq.generators import random_dag
from reachq.shortcut_set import build_shortcut_set_for_reachability
from reachq.reachability import bfs_reachability, parallel_bfs
g = random_dag(n=80, edge_probability=0.2, random_seed=7)
shortcuts, _ = build_shortcut_set_for_reachability(g, random_seed=7)
src = 1
extra = parallel_bfs(g, src, shortcuts) - bfs_reachability(g, src)
print('phantom reachable:', extra)
"  # non-empty set, demonstrating bug 3
```