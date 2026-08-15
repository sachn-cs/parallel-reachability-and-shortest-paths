# Why reachq exists

reachq exists because the algorithm in the paper is useful and the
implementation in the paper's reference repo has some friction that
makes it hard to use as a library. The contribution of reachq is
*turning a research result into a usable, reproducible, well-tested
Python package*, plus a small number of post-processing refinements
that the paper's analysis does not preclude but also does not include.

## What reachq is for

- Running the JLS shortcut-set construction on a graph and using the
  output for parallel reachability queries.
- Computing the CFR hopset and using it for approximate shortest
  paths.
- A reproducible implementation that can be cited and benchmarked.

## What reachq is NOT for

- Re-implementing the analysis of the paper. The analysis is in the
  cited papers; reachq is the implementation.
- Replacing the JLS construction. reachq adds post-processing on top;
  the construction itself is unchanged.

## When to use reachq

Use reachq when you want a Python library that:
- Computes shortcut sets for parallel reachability.
- Computes hopsets for approximate shortest paths.
- Has reproducible benchmarks and tests.

## When to use something else

If you want a general-purpose graph library with full algorithms
(BFS, Dijkstra, SCC, etc.), use `networkx` or `igraph` and call
reachq only for the specific parallel-reachability shortcuts.

## Comparison

| feature | reachq | networkx | igraph |
|---|---|---|---|
| JLS shortcut set | yes | no | no |
| CFR hopset | yes | no | no |
| parallel reachability queries | yes (sequential simulation) | no | no |
| full graph library | no (focused) | yes | yes |
| reproducible benchmarks | yes | partial | no |
| hop-bound-preserving sparsification | yes | no | no |
| streaming shortcut set | prototype only, no formal bound (reachq.research) | no | no |
| (1+ε) approximation | prototype only, no formal (1+ε) bound (reachq.research) | no | no |

## Where to look next

- [`docs/START_HERE.md`](START_HERE.md) for the routing question
  "I want to use / understand / extend the library".
- [`docs/PAPER.md`](PAPER.md) for the algorithmic content.
- [`docs/INSPIRED_BY.md`](INSPIRED_BY.md) for the relationship to the
  cited papers.
