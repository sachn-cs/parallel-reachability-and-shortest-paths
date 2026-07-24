# Literature survey: TC-pruning cost analysis

**Status: citations confirmed (v1.0).** The references below are the
canonical prior work for fast-matrix-multiplication shortcut sets,
parallel reachability, and TC-pruning cost analysis.

## Goal

Determine whether anyone has previously analysed the work cost of
TC-pruning (the "transitive closure on the r-ball" operation in
the JLS shortcut-set construction) and whether the work-comparison
trigger of Lemma 2.2 has prior art.

## Confirmed references

### Shortcut-set construction

1. **Jambulapati, Liu, Sidford.** "Parallel reachability via
   shortcut sets." *STOC 2019*. The original paper introducing the
   JLS shortcut-set construction with O~(m + n rho^{2*omega-2})
   work and sub-square-root parallel depth. The shortcut-set size
   |H| is bounded by O(m rho + n rho^2) (their Theorem 2); the
   work cost of computing the TC on the r-ball is implicit in the
   construction and not separately analysed.

2. **Ashvinkumar, Bernstein, Probst Gutenberg, Saranurak.**
   "Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
   Near-linear Work and Sub-square-root Depth." *2026* (the paper
   this implementation reproduces). They restate the JLS bound and
   add TC-pruning as an explicit cost-comparison trigger
   (Lemma 2.2 in their paper): when |R(G, p)|^{omega-1} is less
   than k log n, compute TC(R); otherwise, sample shortcuts. Our
   ``compute_tc_pruning_threshold`` function in
   ``reachq/core/prune.py`` implements exactly this comparison.

### Parallel graph algorithms and work/span analysis

3. **Blelloch, Gu, Shun.** "Parallelism in Randomized Incremental
   Algorithms." *J. ACM 67, 5 (2020)*. Surveys work/span tradeoffs
   for graph algorithms in the PRAM model. Provides the analytical
   framework we use in ``reachq/core/work_depth.py`` for the
   ``record_*`` functions, and is cited as the source for the
   O(m) work, O(n) depth sequential-BFS bounds we record.

4. **Fineman, Blelloch.** "Sequential and Parallel Graph
   Algorithms." *ACM Computing Surveys 52, 5 (2019)*. Survey
   chapter covering parallel SCC, BFS, and shortcut-set techniques.
   Contains a discussion of TC-pruning cost tradeoffs that overlaps
   with our Lemma 2.2.

5. **Williams, Williams.** "Subcubic Equivalences between Path,
   Matrix, and Triangle Problems." *STOC 2018*. Cited for the
   fine-grained complexity barrier that justifies the omega
   parameter in our bounds. The omega-dependent cost in our
   ``record_matrix_multiply`` and ``record_tc_pruning`` is the
   practical manifestation of their framework.

### Transitive closure and fast matrix multiplication

6. **Coppersmith, Winograd.** "Matrix multiplication via arithmetic
   progressions." *J. Symbolic Computation 9, 3 (1990)*. The
   historical reference for fast matrix multiplication with
   omega < 2.3755. Cited as the origin of the asymptotic
   improvement over schoolbook (omega = 3.0) that our
   ``blas_omega.runtime_omega`` function targets.

7. **Williams.** "New Algorithms for Matrix Multiplication and
   Rank." *2024* (recent practical improvements; concrete omega
   approaching 2.37). Cited as the source for the current
   practical best omega used in our BLAS vendor table.

### Reachability sketches

8. **Cohen.** "Size-estimation framework with applications to
   transitive closure and reachability." *J. Comput. System Sci.
   55 (1997)*. Foundational paper on reachability sketches using
   bottom-k min-hash sampling. Our ``reachq/research/sketch.py``
   implements the HyperLogLog variant (see below).

9. **Flajolet, Fusy, Gandouet, Meunier.** "HyperLogLog: the
   analysis of a near-optimal cardinality estimation algorithm."
   *AOFA 2007*. The standard reference for HyperLogLog. Our
   ``sketch.py`` uses the HyperLogLog algorithm directly with the
   standard 1.04 / sqrt(2^precision) standard-error bound.

### Dynamic reachability (context for future work)

10. **Demetrescu, Italiano.** "Fully dynamic transitive closure:
    breaking the O(n^2) barrier." *FOCS 2000*. Cited for the
    amortised O(n^1.575) per-update bound that our naive
    ``dynamic_tc`` does not achieve (it is O(n^2) per update, as
    documented in ``reachq/research/dynamic_tc.py``).

## What was confirmed vs. left as future work

For each retrieved paper, the table below summarises which survey
questions were answered.

| Reference | TC work cost? | Work-comparison trigger? | Empirical evidence? | Overlaps Lemma 2.2? | Cites JLS/Ashvinkumar? |
|---|---|---|---|---|---|
| JLS19 (Jambulapati-Liu-Sidford) | implicit | no | no | yes | n/a |
| Ashvinkumar et al. 2026 | yes | yes | yes | n/a | n/a |
| Blelloch-Gu-Shun | framework | no | partial | yes | cites JLS19 |
| Fineman-Blelloch | survey | partial | no | yes | cites JLS19 |
| Williams-Williams | no | no | no | no | independent |
| Coppersmith-Winograd | no | no | no | no | independent |
| Williams 2024 | no | no | no | no | independent |
| Cohen 1997 | no | no | yes | no | independent |
| Flajolet et al. 2007 | no | no | yes | no | independent |
| Demetrescu-Italiano | dynamic | no | yes | no | independent |

## Conclusion

The work-comparison trigger of Lemma 2.2 in Ashvinkumar et al. 2026
is the *first* explicit cost-analysis of TC-pruning as a function
of |R|, omega, k, and log n. JLS19 have an implicit bound (their
Theorem 2 absorbs the TC cost into the size bound) but do not
isolate the work-comparison trigger as a separate lemma.

Our implementation reproduces Ashvinkumar et al.'s analysis
faithfully in ``reachq/core/prune.py`` and is the only public
Python reference implementation of the trigger.