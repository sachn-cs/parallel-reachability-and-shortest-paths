# Literature survey: TC-pruning cost analysis

**Status: outline only.** This document was prepared offline; the
final version should fill in citations and confirm/refute each item
below by retrieving the referenced papers. The `git grep -n TODO
docs/lit_survey.md` line below indicates pending items.

> `TODO docs/lit_survey.md` — search-and-confirm pass not yet done.

## Goal

Determine whether anyone has previously analysed the work cost of
TC-pruning (the "transitive closure on the r-ball" operation in
the JLS shortcut-set construction) and whether the work-comparison
trigger of Lemma 2.2 has prior art.

## Search keywords

To run the actual search, the following terms should be tried:

- "JLS shortcut set cost analysis"
- "TC-pruning work bound"
- "transitive closure on induced subgraph work bound"
- "fast matrix multiplication shortcut set"
- "Beta TC-pruning complexity"
- "near-linear work parallel reachability transitive closure"

## Candidate prior work

These are plausible references; **none have been retrieved yet**.

1. **Jambulapati, Liu, Sidford [JLS19].** The original paper. The
   cost of TC-pruning is bounded implicitly by their Theorem 2 size
   bound; whether they explicitly bound the *work* of computing TC
   (as opposed to the number of edges it adds) is unclear without
   retrieval.

2. **Ashvinkumar et al. [2026].** The paper this implementation
   reproduces. They state the asymptotic bound |H| = O(m rho + n rho^2)
   but again, the work cost of TC is implicit.

3. **Blelloch, Gu, Shun [2016, "Parallelism in Randomized Incremental
   Algorithms"].** Discusses work/span tradeoffs for graph algorithms
   in the PRAM model. May have analysis of TC-style operations.

4. **Fineman [2018, "Sequential and Parallel Graph Algorithms"]**.
   Survey chapter on TC-pruning cost is plausible; needs check.

5. **Williams, Williams [2018, "Subcubic Equivalences between Path,
   Matrix, and Triangle Problems"].** Discusses fine-grained omega
   barriers; could be cited for omega-dependence in the bound.

## What to record when retrieved

For each retrieved paper, note:

| Question | Answer |
|---|---|
| Does the paper analyse TC work cost (separate from |H| contribution)? | |
| Does it bound the work-comparison threshold |R|^(omega-1) <= k log n? | |
| Does it provide empirical evidence on random DAGs / SNAP datasets? | |
| Does it overlap with our Lemma 2.2 / Corollary 2.3? | |
| Does it cite JLS19 or Ashvinkumar et al.? | |

## Why this matters

If prior work has analysed the work cost of TC-pruning, our
contribution is incremental and should be cited. If prior work has
*not* analysed it, the work-comparison trigger of Lemma 2.2 is a
novel refinement and the paper's contribution is more substantial.

Either outcome strengthens the paper: novelty in the former case,
reproducibility / extension in the latter.

## Decision for v0.7.0 release

Without internet access from this session, the paper draft
(`docs/paper_refinements.md`) currently cites only [JLS19] and
[Ashvinkumar et al. 2026]. The literature section will be filled
in before any conference submission.

The implementation is unaffected by the survey: Corollary 2.3
stands on its own proof regardless of prior art.