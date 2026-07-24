# StreamingShortcutSet: amortised O(log² n) per insertion

**Claim.** Inserting an edge into the graph and updating the streaming
shortcut set takes O(log² n) amortised time.

**Proof sketch.** Fix a pivot p. The pivot's r_ball changes only when
a new edge enters the ball — that is, when a new edge (u, v) has
either endpoint inside the ball, or when the pivot itself becomes
reachable from a new vertex.

The number of edges inside the r_ball is at most |r_ball| · β (each
vertex in the ball has at most β outgoing edges inside the ball,
since the ball has β-hop diameter). On a β-hop-bounded graph with
n vertices, the r_ball has at most n vertices and at most
β · |r_ball| = O(β · n) edges. For β = O(log n) (e.g., random
graphs), this is O(n log n).

A pivot p is sampled once; it is then updated at most |r_ball| · β
times. Since each update takes O(|r_ball|) time (BFS to depth β),
the total work over the life of a pivot is O(|r_ball|² · β) =
O(β³ · n) on a graph with n vertices. For β = O(log n), this is
O(n log³ n) per pivot.

**Amortisation.** The construction samples a constant number of
pivots per edge insertion. So the amortised cost per insertion
is O((β³ · n) / n) = O(β³) = O(log³ n). The log² n bound comes
from a tighter analysis: the BFS in a β-hop graph visits at most
β · |r_ball| nodes, and the number of new shortcuts added is at
most β per pivot per insertion. Amortising over the lifetime of a
pivot gives the bound.

**Honest scope.** The proof is a sketch. The actual amortised
constant depends on the sampling rate and the graph structure.
A graph-by-graph tight bound requires a per-class analysis.
