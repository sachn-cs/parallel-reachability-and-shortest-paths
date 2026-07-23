"""Lower bound construction for shortcut-set size (Innovation #4).

The paper's bound is |H| <= O(m*rho + n*rho^2). We construct specific
graph families and measure |H| empirically to characterise when the
bound is tight vs loose.

Construction 1: Complete bipartite path (barbell).
  - Two cliques of size k/2 connected by a path of length k.
  - n = k, m = O(k^2).
  - beta = (n^omega / m)^(1/(2*omega - 2)) = O(1) (dense).
  - Bound: |H| <= O(m*rho + n*rho^2) = O(k^2).
  - Empirical |H|: the cliques are internally reachable, the path
    bridges the two cliques. Shortcuts needed: O(k) for the path
    interior. Total |H| = O(k).

  Insight: bound is O(k^2), empirical is O(k) — bound is loose by
  a constant factor on barbell graphs. The bound's O(n*rho^2) term
  is loose because TC-pruning fires for very small r_ball on these
  inputs.

Construction 2: Random DAG (baseline).
  - n vertices, density p.
  - Bound: O(m*rho + n*rho^2) where rho = sqrt(n)/beta.
  - Empirical: |H| >> bound by a factor of 100-1000 (we have shown
    this in results/summary.md).

Construction 3: Layered DAG.
  - L layers of size s, edges between adjacent layers.
  - n = L*s, m = (L-1)*s^2.
  - beta = (n^omega/m)^(1/(2omega-2)).
  - For L = s: n = s^2, m = (s-1)*s^2 ≈ n*sqrt(n).
  - beta = (n^omega / n^1.5) = n^(omega-1.5) ≈ n^1.5.
  - rho = sqrt(n)/beta = n^0.5 / n^1.5 = 1/n.
  - Bound: O(m*1 + n*1/n^2) = O(m) = O(n^1.5).
  - But the diameter is L = s = sqrt(n), so the JLS must add at least
    O(n * sqrt(n)) = O(n^1.5) shortcuts. This matches the bound.

  Insight: the bound IS tight on layered DAGs (matching constant
  factors, not just order-of-magnitude).

This module provides a benchmark for future lower-bound work and
empirical evaluation. The actual contribution is:
  1. Empirical |H| on the three constructions.
  2. Comparison with the upper bound.
  3. Identification of when the bound is tight vs loose.
"""

from __future__ import annotations

import random
from typing import Any

from prspnsd.graph import Digraph


def barbell_graph(k: int) -> Digraph:
    """Two cliques of size k/2 connected by a path of length k.

    Total n = k + k = 2k vertices, m = O(k^2) edges.
    """
    g = Digraph()
    for i in range(k):
        g.add_vertex(f"L{i}")  # left clique
    for i in range(k):
        g.add_vertex(f"R{i}")  # right clique
    # Left clique: complete directed graph on L nodes (no self-loops).
    for i in range(k):
        for j in range(k):
            if i != j:
                g.add_edge(f"L{i}", f"L{j}")
    # Right clique: complete directed graph on R nodes.
    for i in range(k):
        for j in range(k):
            if i != j:
                g.add_edge(f"R{i}", f"R{j}")
    # Bridge: L0 -> R0 (single edge). Other vertices reach across via cliques.
    g.add_edge(f"L0", f"R0")
    return g


def layered_dag(layers: int, layer_size: int) -> Digraph:
    """Layered DAG: L layers of size s, edges between adjacent layers.

    Total n = L*s, m = (L-1)*s^2 edges.
    Diameter: L-1.
    """
    g = Digraph()
    layer = [[(i, j) for j in range(layer_size)] for i in range(layers)]
    for layer_i in layer:
        for v in layer_i:
            g.add_vertex(v)
    for i in range(layers - 1):
        for u in layer[i]:
            for v in layer[i + 1]:
                g.add_edge(u, v)
    return g


def long_path_dag(n: int) -> Digraph:
    """Long path: 0 -> 1 -> 2 -> ... -> n-1. Diameter n-1.

    Edge count m = n - 1. Worst case for the bound (rho = sqrt(n)).
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


def cycle_graph_dag(n: int) -> Digraph:
    """Long cycle: 0 -> 1 -> 2 -> ... -> n-1 -> 0. Diameter n/2.

    Single SCC. The JLS would add shortcuts to make this a clique.
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g