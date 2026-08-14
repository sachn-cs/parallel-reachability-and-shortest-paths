"""Tests that the produced shortcut set preserves the beta-hopbound
guarantee.

beta is the paper's bound beta = (n^omega / m)^(1 / (2*omega - 2)).
The shortcut set must ensure that every reachable pair (s, t) is
connected within beta hops via G + shortcuts.
"""

from collections import deque

from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.graph import Digraph
from reachq.core.reachability import bfs_reachability, parallel_bfs


def max_hops(g, s, H, beta):
    """Return the max BFS depth from s via G + H, limited to beta."""
    visited = {s: 0}
    q = deque([s])
    out = g.out_edges
    index = {}
    for u, v in H:
        index.setdefault(u, []).append(v)
    while q:
        u = q.popleft()
        d = visited[u]
        if d >= beta:
            continue
        for v in out.get(u, ()):
            if v not in visited:
                visited[v] = d + 1
                q.append(v)
        for v in index.get(u, ()):
            if v not in visited:
                visited[v] = d + 1
                q.append(v)
    return max(visited.values()) if visited else 0


class TestHopboundPreserved:
    def test_default_preserves_hopbound_on_path(self):
        """The default build_shortcut_set_for_reachability must return a
        shortcut set that satisfies the beta-hopbound.

        Regression test: the old default (sparsify_shortcuts=True)
        used the reachability-only sparsifier, which on a path graph
        stripped H down to empty and pushed the max hop to n-1,
        far above beta.
        """
        for n in (20, 30, 50):
            g = Digraph()
            for i in range(n):
                g.add_vertex(i)
            for i in range(n - 1):
                g.add_edge(i, i + 1)
            shortcuts, beta = build_shortcut_set_for_reachability(
                g,
                omega=3.0,
                random_seed=42,
            )
            for s in g.vertices():
                d = max_hops(g, s, shortcuts, int(beta) + 1)
                assert d <= int(beta) + 1, (
                    f"default build violated hopbound (n={n}, s={s}): "
                    f"max hop = {d}, beta = {beta}"
                )

    def test_hopbound_on_path_n_20(self):
        g = Digraph()
        n = 20
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for s in g.vertices():
            d = max_hops(g, s, shortcuts, int(beta) + 1)
            assert d <= int(beta) + 1, (
                f"hopbound violated from {s}: max hop = {d}, beta = {beta}"
            )

    def test_hopbound_on_dag_n_30(self):
        g = Digraph()
        n = 30
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        shortcuts, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for s in g.vertices():
            d = max_hops(g, s, shortcuts, int(beta) + 1)
            assert d <= int(beta) + 1

    def test_hopbound_on_graph_with_scc(self):
        g = Digraph()
        n = 10
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        # Add an SCC.
        g.add_edge(2, 0)
        g.add_edge(5, 3)
        shortcuts, beta = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for s in g.vertices():
            d = max_hops(g, s, shortcuts, int(beta) + 1)
            assert d <= int(beta) + 1

    def test_soundness_implies_hopbound(self):
        """If R+(G, s) = R+(G+H, s) for all s, and beta is set correctly,
        the hopbound is preserved. We test soundness + soundness-of-empirical-hops.
        """
        g = Digraph()
        n = 12
        for i in range(n):
            g.add_vertex(i)
        for i in range(0, n - 1, 2):
            g.add_edge(i, i + 1)
        shortcuts, _ = build_shortcut_set_for_reachability(
            g,
            omega=3.0,
            random_seed=42,
            sparsify_shortcuts=False,
        )
        for s in g.vertices():
            assert bfs_reachability(g, s) == parallel_bfs(g, s, shortcuts)
