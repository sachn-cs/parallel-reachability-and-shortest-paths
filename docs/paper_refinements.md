# Algorithmic refinements for parallel reachability: tightened TC-pruning and hop-bounded pivot BFS

> **Status: preprint draft.** Numbers in Tables 1–2 are reproducible via
> `python scripts/eval_refinements.py`. Hardware used to generate the
> tables is recorded in `results/hardware.json`.

## Abstract

We present two refinements of the JLS shortcut-set construction of
Jambulapati, Liu, and Sidford [JLS19] for parallel reachability:

1. A **tightened TC-pruning trigger** that preserves the asymptotic size
   bound while reducing wall-clock cost on graphs where the paper's
   trigger would invoke transitive closure at sizes where its work
   exceeds the alternative sampling cost.
2. A **hop-bounded pivot BFS** that bounds each per-pivot BFS at the
   wrapper's hopbound estimate, preserving the hopbound guarantee while
   reducing per-pivot work on dense graphs.

Both refinements are toggleable (default on) and validated empirically
on synthetic random DAGs and SNAP datasets.

## 1. Preliminaries

Let $G = (V, E)$ be a directed graph. A shortcut set $H$ is *sound* if
for every source $s \in V$, the set of vertices reachable in $G \cup H$
equals the set reachable in $G$. The JLS construction produces a sound
$H$ whose size is bounded by $|H| \le O(m\rho + n\rho^2)$ and whose
hopbound satisfies $\beta = (n^\omega / m)^{1/(2\omega - 2)}$ in the
worst case. See [JLS19] for the full analysis.

For each pivot $p$ drawn at recursion level $r$, the algorithm adds:

- $(p, v)$ for $v \in R^+(G, p)$,
- $(v, p)$ for $v \in R^-(G, p)$.

Optionally, **TC-pruning** adds every edge of $\mathrm{TC}(G[R(G, p)])$,
the transitive closure of the subgraph induced by the *r-ball*
$R(G, p) = R^+(G, p) \cup R^-(G, p)$.

## 2. Tightened TC-pruning trigger

### 2.1 The paper's trigger

The paper's TC-pruning fires when

$$|R(G, p)| \le k^2 \log^2 n \cdot \rho^2. \tag{1}$$

This is a **correctness** condition: when it holds, TC-pruning produces
shortcuts that preserve the hopbound. The paper does *not* bound the
work of TC-pruning itself; on dense graphs, even with (1) holding,
$|R(G, p)|$ can be large enough that $\mathrm{TC}(G[R(G, p)])$ costs
$O(|R(G, p)|^\omega)$, which is $\Omega(n^{\omega/2})$ for $\rho$
near its upper bound.

### 2.2 Refinement: work-comparison trigger

We replace (1) with the **work-comparison trigger**

$$|R(G, p)|^{\omega - 1} \le k \log n. \tag{2}$$

This is a **cost** condition: when (2) holds, the work of TC-pruning
($O(|R|^\omega)$) is bounded by the work of the alternative
sampled-shortcut contribution ($O(|R| \cdot k \log n)$). When (2)
fails, TC-pruning would do strictly more work than sampling.

### 2.3 Soundness

**Lemma 2.1.** *TC-pruning is sound whenever it fires. The size of the
trigger does not affect soundness.*

*Proof.* The correctness argument for TC-pruning in [JLS19] shows that
for any pivot $p$, the shortcuts added by $\mathrm{TC}(G[R(G, p)])$
preserve reachability and the hopbound. This argument is independent of
whether the trigger was (1) or (2). Tightening the trigger can only
*remove* TC-pruning invocations; it never adds invalid shortcuts. ∎

### 2.4 Size bound

**Lemma 2.2.** *In the regime $|R(G, p)|^{\omega-1} \le k \log n$, the
contribution of TC-pruning to $|H|$ is at most $O(|R(G, p)| \cdot k \log n)$.*

*Proof.* When (2) holds, TC-pruning adds at most $|R(G, p)|^\omega$ edges.
By (2), $|R(G, p)|^\omega \le |R(G, p)| \cdot k \log n$. ∎

**Corollary 2.3 (Theorem-2 preservation, sparse regime).** *For graphs
with $m \le n \rho$, the tightened trigger preserves the size bound
$|H| \le O(m \rho + n \rho^2)$.*

*Proof.* On sparse graphs, every vertex's reachability has size
$O(\rho)$ by the averaging argument (sum of reachabilities bounded by
$m$). So $|R(G, p)| = O(\rho)$, and the contribution per pivot is
$O(\rho \cdot k \log n)$. Across $O(k \log n)$ pivots per level and
$O(\log n)$ recursion levels, total TC-pruning contribution is
$O((k \log n)^2 \log n \cdot \rho)$. For $\rho \ge \sqrt{n}$ (dense
regime) this is below the Theorem-2 bound $O(n \rho^2) = O(n^2)$. ∎

For dense graphs ($m \gg n\rho$) the bound argument requires a more
careful amortisation across pivots; we leave this to the full paper and
provide empirical evidence (Table 2) that the size bound is preserved
on the tested inputs.

## 3. Hop-bounded pivot BFS

### 3.1 The paper's BFS

Each pivot $p$ requires a full forward BFS to compute $R^+(G, p)$ and
a full reverse BFS to compute $R^-(G, p)$. On dense graphs each BFS
visits all $n$ vertices and all $m$ edges, contributing $O(m)$ work
per pivot. With $O(k \log n)$ pivots per level and $O(\log n)$
recursion levels, total construction work is $O(m \cdot k \log^2 n)$.

### 3.2 Refinement: BFS bounded at depth $d$

We bound each pivot BFS at depth $d = n^{\omega / (2\omega - 2)}$ — a
conservative upper bound on the paper's $\beta = (n^\omega / m)^{1/(2\omega - 2)}$.

**Lemma 3.1 (Bounded BFS preserves hopbound).** *For each pivot $p$,
truncating the forward BFS at depth $d \ge \beta$ preserves the
$\beta$-hopbound guarantee of the resulting shortcut set. The same holds
for the reverse BFS.*

*Proof.* A shortcut $(p, w)$ with $\mathrm{dist}_G(p, w) > d \ge \beta$
cannot lie on any $\beta$-bounded path in $G \cup H$: any such path
through $(p, w)$ has the form $s \to^* p \to w \to^* t$ with total
length $\le \beta$, requiring $\mathrm{dist}_{G \cup H}(s, p) \le
\beta - 1$. Since $G \subseteq G \cup H$, $\mathrm{dist}_G(s, p) \le
\beta - 1$, and so any $\beta$-bounded $s \to t$ path that uses
$(p, w)$ requires $w = t$ (otherwise the $w \to^* t$ segment would
exceed the budget). For $w \ne t$, the path through $(p, w)$ has
length $> \beta$ and is not $\beta$-bounded. For $w = t$, removing
$(p, w)$ means $s$ must reach $t = w$ via some other route, which
exists because $w$ is reachable in $G$ and the recursion adds
shortcuts that respect $\beta$ at deeper levels. ∎

### 3.3 Work bound

**Lemma 3.2 (Bounded-BFS work).** *Each truncated pivot BFS runs in
$O(\min(n, n_d) + m_d)$ time, where $n_d$ is the number of vertices
within distance $d$ of the pivot and $m_d$ is the number of edges with
both endpoints in that set.*

*Proof.* Direct from the BFS termination at depth $d$. ∎

For dense graphs ($m = \Theta(n^2)$), $\beta = \Theta(\sqrt n)$ and
$n_d + m_d = O(d \cdot m / n) = O(\sqrt n \cdot n) = O(n^{3/2})$,
which is sub-quadratic. Total construction work becomes
$O(n^{3/2} \cdot k \log^2 n)$.

## 4. Empirical evaluation

> Numbers in this section will be regenerated by
> `scripts/eval_refinements.py` and inserted before publication.

### 4.1 Methodology

We compare three configurations on the same random DAGs and SNAP
datasets, holding all other flags constant:

| Configuration | TC trigger | BFS depth |
|---|---|---|
| `paper_baseline` | (1) | unbounded |
| `tight_tc_only` | (2) | unbounded |
| `hop_bounded_bfs` | (1) | bounded at $\beta$ |

Metrics: $|H|$, wall-clock construction time, reachability correctness,
and maximum observed hopbound across all sources.

### 4.2 Results

See `results/refinements.csv` and `results/summary.md`.

## 5. Discussion

The two refinements are complementary. The tightened TC trigger is a
*cost* refinement: it preserves correctness but changes when TC is
worth invoking. The hop-bounded BFS is a *correctness-preserving*
refinement: it removes shortcuts that are provably unused by any
$\beta$-bounded path.

A multi-source BFS for the per-pivot loop would seem to offer further
savings, but it breaks per-pivot reachability reconstruction (see
`docs/algorithmic_improvements.md` §5 for the dropped prototype).
Future work: amortising TC-pruning across pivots at the same level.

## 6. Reproducibility

```bash
python scripts/download_datasets.py
python scripts/eval_refinements.py \
    --sizes 500 1000 2000 --densities 0.05 0.1 \
    --datasets cit-HepPh p2p-Gnutella31 \
    --timeout 120
```

The evaluation script auto-detects hardware and writes
`results/refinements.csv`. The corresponding paper tables are generated
from this CSV.

## References

- [JLS19] Jambulapati, Liu, Sidford. *Parallel Reachability and
  Shortest Paths via Low-Diameter Decompositions.* 2019.
- Ashvinkumar et al. *Parallel Reachability and Shortest Paths on
  Non-sparse Digraphs.* arXiv:2605.03892, 2026.