# `reachq` is inspired by the cited papers

`reachq` is a reimplementation and empirical analysis of the
algorithms in:

- Ashvinkumar, Bernstein, Probst Gutenberg, Saranurak.
  *"Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
  Near-linear Work and Sub-square-root Depth."*
  arXiv:2605.03892, 2026.

- Jambulapati, Liu, Sidford. *"Parallel Reachability via Shortcut
  Sets."* 2019.

The JLS construction, the `ρ` bound, the
`β`-hopbounded reachability guarantee, and the theoretical
foundations are due to the cited authors.

## What `reachq` contributes

`reachq` is a derivative work that stands on the shoulders of the
cited authors. The contributions of `reachq` are:

- **Engineering polish.** A typed `Digraph` / `WeightedDigraph`
  abstraction, `ParallelContext` for thread/process dispatch,
  `SpanProfiler` for empirical work-depth measurement, a
  `Flags` dataclass for ablation, and a CLI + benchmark harness.

- **Post-processing refinements.** β-hopbound-preserving
  sparsification, iterative refinement, adaptive β, and
  closed-form empirical analysis. Each is on top of the JLS
  construction; none contradicts the cited bounds. The four
  refinements, in the order they appear in the code:
  1. **TC-pruning** (Theorem 2 improvement): apply full
     transitive closure on small r-balls instead of sampling
     shortcuts; see `reachq/core/algorithm.py::jls_with_tc_pruning`.
  2. **β-hopbound-preserving sparsification**:
     `reachq/research/sparsify_hop.py::sparsify_hop_bounded`.
  3. **Iterative refinement**:
     `reachq/research/iterate.py::iterative_shortcut_set`.
  4. **Adaptive β**:
     `reachq/research/adaptive_beta.py::adaptive_beta`.

- **Two new algorithms** (in `reachq.research.*`):
  streaming maintenance of shortcut sets under edge insertions
  (`StreamingShortcutSet`, experimental prototype — no formal
  amortised bound yet) and a greedy approximation algorithm for
  shortcut-set size (`greedy_shortcut_set`, plain greedy without
  the formal (1+ε) guarantee). Both are distinct from the cited
  papers and do not modify the JLS construction.

- **Four documented correctness fixes.** A corrigendum
  documents four bugs found in the reference implementation and
  fixed here (see `docs/notes_correctness.md`).

- **A test fixture library** from the algebraic-graph-theory
  literature (Petersen, Paley, Shrikhande, Hamming, see
  `docs/spectral_fixtures.md`) for regression-testing the
  construction across graph classes.

## What `reachq` does NOT contribute

- A new asymptotic bound that improves the JLS analysis.
- A construction that supersedes the JLS construction.
- A different problem formulation.
- A new variant of parallel reachability.

The cited authors' contributions are the theoretical foundation.
`reachq` is a usable, well-tested, and reproducibly benchmarked
implementation of those contributions, plus the empirical and
engineering work above.
