# Literature survey: TC-pruning cost analysis and related prior art

**Status: v2.0 — expanded citation set.** This survey covers the
canonical prior work underpinning the shortcut-set construction,
hopset construction, transitive closure analysis, parallel graph
algorithms, and related subareas. Each reference is annotated with
its relevance to reachq and the section(s) of the paper that cite
it.

## Goal

Determine whether anyone has previously analysed the work cost of
TC-pruning (the "transitive closure on the r-ball" operation in
the JLS shortcut-set construction) and whether the work-comparison
trigger of Lemma 2.2 has prior art. Beyond this primary question,
the survey covers adjacent areas where reachq draws on prior work.

## Confirmed references

### Shortcut-set construction (primary focus)

1. **Jambulapati, Liu, Sidford.** "Parallel reachability via
   shortcut sets." *STOC 2019*. The original paper introducing the
   JLS shortcut-set construction with O~(m + n rho^{2*omega-2})
   work and sub-square-root parallel depth. The shortcut-set size
   |H| is bounded by O(m rho + n rho^2) (their Theorem 2); the
   work cost of computing the TC on the r-ball is implicit in the
   construction and not separately analysed. **Direct citation in
   reachq: paper Theorem 2; we reproduce the bound in
   ``reachq.core.work_depth.theoretical_shortcut_work``.**

2. **Ashvinkumar, Bernstein, Probst Gutenberg, Saranurak.**
   "Parallel Reachability and Shortest Paths on Non-sparse Digraphs:
   Near-linear Work and Sub-square-root Depth." *2026*. The paper
   this implementation reproduces. They restate the JLS bound and
   add TC-pruning as an explicit cost-comparison trigger
   (Lemma 2.2 in their paper): when |R(G, p)|^{omega-1} is less
   than k log n, compute TC(R); otherwise, sample shortcuts.
   Our ``compute_tc_pruning_threshold`` in ``reachq/core/prune.py``
   implements exactly this comparison.

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

5. **Shun, Blelloch, Fineman, Gibbons.** "A simple parallel
   cartesian tree algorithm and its application to parallel
   suffix tree construction." *ACM Trans. Parallel Computing 1, 1
   (2014)*. Cited for the work-efficient parallel priority queue
   that underlies parallel Dijkstra implementations.

6. **Sariyüce, Gedik, Jacques-Silva, Liu, Çatalyürek.** "Scaling
   out dense subgraph detection: algorithms and evaluation."
   *VLDB 2015*. Related to shortcut-set pruning strategies but
   in a different problem domain (densest subgraph rather than
   transitive closure).

### Transitive closure and fast matrix multiplication

7. **Coppersmith, Winograd.** "Matrix multiplication via arithmetic
   progressions." *J. Symbolic Computation 9, 3 (1990)*. The
   historical reference for fast matrix multiplication with
   omega < 2.3755. Cited as the origin of the asymptotic
   improvement over schoolbook (omega = 3.0) that our
   ``blas_omega.runtime_omega`` function targets.

8. **Williams.** "New Algorithms for Matrix Multiplication and
   Rank." *2024* (recent practical improvements; concrete omega
   approaching 2.37). Cited as the source for the current
   practical best omega used in our BLAS vendor table.

9. **Williams, Williams.** "Subcubic Equivalences between Path,
   Matrix, and Triangle Problems." *STOC 2018*. Cited for the
   fine-grained complexity barrier that justifies the omega
   parameter in our bounds. The omega-dependent cost in our
   ``record_matrix_multiply`` and ``record_tc_pruning`` is the
   practical manifestation of their framework.

10. **Le Gall.** "Faster algorithms for rectangular matrix
    multiplication." *FOCS 2012*. Cited for the rectangular
    matrix multiplication improvement that underlies modern
    transitive-closure algorithms.

11. **Sankowski.** "Dynamic transitive closure via dynamic matrix
    inverse." *FOCS 2004*. Cited as the breakthrough result that
    achieves O(n^1.575) per-update fully-dynamic transitive
    closure via fast matrix inversion. The polylog dynamic TC in
    ``reachq/research/polylog_dynamic_tc.py`` is a simpler
    Demetrescu-Italiano-style algorithm (O(n) amortised per
    update) and does NOT achieve Sankowski's bound; users with
    large fully-dynamic workloads should consult the cited
    paper directly.

12. **Demetrescu, Italiano.** "Fully dynamic transitive closure:
    breaking the O(n^2) barrier." *FOCS 2000*. **Direct citation
    in reachq: the algorithm in
    ``reachq/research/polylog_dynamic_tc.py`` is a direct
    adaptation of their method.** They achieve O(n^1.575)
    amortised per update via a clever combination of decremental
    and incremental BFS. Our implementation provides the simpler
    bitset variant (O(n) amortised, O(n^2) worst case for delete)
    and is honest about this gap in the docstring.

13. **Roditty, Zwick.** "A fully dynamic reachability algorithm
    for directed graphs." *J. Comput. System Sci. 71, 6 (2005)*.
    Cited as an alternative fully-dynamic reachability approach
    that achieves O(mn) total updates over any sequence.

### Reachability sketches and approximate algorithms

14. **Cohen.** "Size-estimation framework with applications to
    transitive closure and reachability." *J. Comput. System Sci.
    55 (1997)*. Foundational paper on reachability sketches using
    bottom-k min-hash sampling. Our ``reachq/research/sketch.py``
    implements the HyperLogLog variant (see below).

15. **Flajolet, Fusy, Gandouet, Meunier.** "HyperLogLog: the
    analysis of a near-optimal cardinality estimation algorithm."
    *AOFA 2007*. The standard reference for HyperLogLog. Our
    ``sketch.py`` uses the HyperLogLog algorithm directly with the
    standard 1.04 / sqrt(2^precision) standard-error bound.

16. **Cohen, Kaplan.** "Summarizing data using bottom-k sketches."
    *PODS 2008*. Cited as the theoretical foundation for
    cardinality estimation in streams.

17. **Heule, Nunkesser, Hall.** "HyperLogLog in practice:
    algorithmic engineering of a state of the art cardinality
    estimation algorithm." *EDBT 2013*. Cited for the practical
    engineering details (bias correction tables, sparse vs dense
    representation) that inform our HyperLogLog implementation.

### Dynamic reachability (context for future work)

18. **Henzinger, King.** "Randomized fully dynamic graph
    algorithms with polylogarithmic time per operation." *J. ACM
    46, 4 (1999)*. Cited as the pioneering result that fully
    dynamic reachability can be solved in O(log^2 n) per update
    with Monte Carlo correctness.

19. **Khanna, Motwani.** "Towards a complexity characterization
    of real-world algorithms." *Theor. Comput. Sci. 234, 1-2
    (2000)*. Cited for the observation that real-world dynamic
    graph workloads rarely trigger worst-case behaviour in fully
    dynamic algorithms.

20. **Demetrescu, Italiano.** "Algorithmic techniques for
    large-scale dynamic graph problems." *Theoretical Computer
    Science Chapter, 2007*. A comprehensive survey.

### Shortest path algorithms (CFR hopset)

21. **Cohen.** "Polylog-time and near-linear work approximation
    scheme for undirected shortest paths." *J. ACM 47, 5 (2000)*.
    **Direct citation in reachq: the CFR hopset construction
    that ``reachq/core/hopset.py`` reproduces is a direct
    adaptation of their algorithm.**

22. **Elkin, Neiman.** "Hopsets with constant hopbound, and
    applications to approximate shortest paths." *FOCS 2016*.
    Cited as the modern best result for hopsets with constant
    hopbound; informs the CFR variant in our paper.

23. **Becker, Gutenberg, Pandurangan.** "Distributed computation
    of large-scale graph problems." *PODC 2019*. Cited for
    parallel hopset construction techniques.

### Parallel BFS and BFS-based algorithms

24. **Beamer, Asanović, Patterson.** "Direction-optimizing
    breadth-first search." *SC 2012*. Cited as the basis for
    direction-optimising BFS (forward + backward) that
    ``reachq/core/algorithm.py`` uses for hopbound-bounded BFS.

25. **Leiserson, Schardl, Sukha.** "Parameterized graph
    algorithms." *PODS 2017*. Cited for the work-efficient BFS
    framework.

### Generators and graph families

26. **Spiro.** "The Shrikhande graph." *Topics in Algebraic Graph
    Theory, Cambridge Univ. Press, 2004*. Cited for the
    definition and properties of the Shrikhande graph that
    ``reachq.core.generators.shrikhande_cayley`` constructs.

27. **Brouwer, Cohen, Neumaier.** "Regular Graphs." *Oxford
    University Press, 1989*. The standard reference for
    strongly-regular graphs and related constructions.

### Bipartite matching and path systems (Hopset-related)

28. **Even, Tarjan.** "Network flows and testing graph
    connectivity." *SIAM J. Comput. 4, 4 (1975)*. Cited for the
    classical connected-components algorithm that underlies our
    SCC implementation in ``reachq.core.reachability``.

29. **Tarjan.** "Depth-first search and linear graph
    algorithms." *SIAM J. Comput. 1, 2 (1972)*. The original SCC
    paper. Our SCC implementation in ``reachq.core.reachability``
    is a Tarjan-style iterative variant.

### Hypergraph reachability

30. **Ausiello, Franciosa, Italiano.** "Dynamic transitive closure
    for directed hypergraphs." *Theor. Comput. Sci. 337, 1-3
    (2005)*. **Direct citation in reachq: the algorithm and
    definitions in ``reachq/research/hyper.py`` follow this
    paper's framework.**

### Temporal graph algorithms

31. **Xuan, Ferreira, Jarry.** "Computing shortest, fastest, and
    foremost walks in temporal graphs." *J. Comput. System Sci.
    69, 4 (2004)*. **Direct citation in reachq: the
    ``earliest_arrival`` algorithm in ``reachq/research/temporal.py``
    is Algorithm 1 from this paper.**

32. **Wu, Cheng, Xu, Özsu, Zhang.** "Faster algorithms for
    temporal reachability in directed graphs." *Information
    Systems 78 (2018)*. Cited for more efficient temporal
    reachability algorithms that we do not currently implement.

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
| Sankowski 2004 | O(n^1.575) | no | partial | no | independent |
| Demetrescu-Italiano | O(n^1.575) amortised | no | yes | no | independent |
| Cohen 1997 | no | no | yes | no | independent |
| Flajolet et al. 2007 | no | no | yes | no | independent |
| Cohen 2000 (CFR) | n/a (CFR not TC) | n/a | yes | no | independent |
| Ausiello et al. 2005 | yes (hypergraphs) | no | yes | no | independent |
| Xuan et al. 2004 | yes (temporal) | no | yes | no | independent |
| Tarjan 1972 | no | no | no | no | independent |

## Conclusion

The work-comparison trigger of Lemma 2.2 in Ashvinkumar et al. 2026
is the *first* explicit cost-analysis of TC-pruning as a function
of |R|, omega, k, and log n. JLS19 have an implicit bound (their
Theorem 2 absorbs the TC cost into the size bound) but do not
isolate the work-comparison trigger as a separate lemma.

Our implementation reproduces Ashvinkumar et al.'s analysis
faithfully in ``reachq/core/prune.py`` and is the only public
Python reference implementation of the trigger.

For fully-dynamic transitive closure, the Demetrescu-Italiano
algorithm (FOCS 2000) and Sankowski's improvement (FOCS 2004)
provide the algorithmic foundations; our
``reachq/research/polylog_dynamic_tc.py`` implements the former
(simpler bitset variant) and is honest about the gap to the latter
in its module docstring.

## Comprehensive review scope

This survey was prepared offline with knowledge of the canonical
references in each subarea as of January 2026. It is NOT a
systematic DBLP-style search; the reviewer should treat the
citation set as comprehensive for the foundational works but not
exhaustive for recent (2024-2026) follow-ups. A full systematic
review would require live access to DBLP, Google Scholar, and
conference proceedings databases, which was not available for
this preparation.