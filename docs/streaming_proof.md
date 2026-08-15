# StreamingShortcutSet (sketch, no formal bound yet)

**Status.** This document describes a design goal, not the current
implementation. The `StreamingShortcutSet` prototype in
`reachq/research/streaming.py` is **honest about its scope**: the
prototype does NOT achieve the amortised O(log² n) per-insertion
bound that the original paper citation suggests. The prototype
serves as a structural scaffold for future work.

## Design intent

Maintain a shortcut set under edge insertions. Each new edge should
trigger a localised update of the affected pivots, without rebuilding
the set from scratch.

The intended analysis:
- Each pivot's r-ball changes only when a new edge enters the ball.
- The number of edges inside the r-ball is at most |r_ball| · β
  (each vertex has at most β outgoing edges inside the ball, since
  the ball has β-hop diameter).
- A pivot is sampled once and updated at most |r_ball| · β times.
  Each update takes O(|r_ball|) time (BFS to depth β).
- Amortising over the lifetime of a pivot, the per-insertion work
  is O(β³) = O(log³ n) for β = O(log n).

The tighter O(log² n) bound would require a more careful
amortisation argument (likely paired with a different pivot-sampling
rule) that has not been worked out and is not implemented.

## Honest scope

- The prototype is a scaffold. It does not achieve the O(log² n)
  bound.
- The amortised constant depends on the sampling rate and the
  graph structure; a graph-by-graph tight bound requires a per-class
  analysis that is out of scope.
- The complexity claim on the class docstring (`O(log² n) per
  edge insertion`) is the optimistic design intent, not the current
  implementation's behaviour.

## What to expect

If you call `StreamingShortcutSet` in the current state, you get
correctness (the set is consistent with the graph) but no
performance guarantee. Future work would tighten the analysis and
implement the matching sampling rule.
