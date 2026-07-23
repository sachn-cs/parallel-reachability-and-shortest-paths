"""Demo script for parallel reachability and shortest paths algorithms.

This script demonstrates end-to-end usage of:
1. Shortcut set construction for reachability (Theorem 2)
2. Hopset construction for shortest paths (Theorem 4)
3. Reachability queries using shortcut sets
4. Approximate shortest path queries using hopsets
5. A* search on a grid
"""

import random
import time

from reachq.graph import Digraph, WeightedDigraph
from reachq.hopset import build_hopset_for_sssp
from reachq.reachability import bfs_reachability, parallel_bfs, strongly_connected_components
from reachq.shortcut_set import build_shortcut_set_for_reachability
from reachq.shortest_paths import astar, dijkstra, shortest_path_hopbound


def demo_reachability():
    """Demonstrate shortcut set construction and reachability queries."""
    print("=" * 60)
    print("DEMO 1: Shortcut Set for Reachability")
    print("=" * 60)

    n = 100
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    random.seed(42)
    for j in range(200):  # noqa: B007
        u = random.randint(0, n - 2)
        v = random.randint(u + 1, n - 1)
        g.add_edge(u, v)

    print(f"Input graph: n={g.num_vertices()}, m={g.num_edges()}")

    start = time.time()
    shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    elapsed = time.time() - start

    print(f"Shortcut set size: {len(shortcuts)} edges")
    print(f"Target hopbound beta: {beta:.2f}")
    print(f"Construction time: {elapsed:.3f}s")

    source = 0
    original_reachable = bfs_reachability(g, source)
    shortcut_reachable = parallel_bfs(g, source, shortcuts)
    assert original_reachable == shortcut_reachable
    print(f"Reachability preserved: {len(original_reachable)} vertices reachable")

    from collections import deque

    def hop_count_bfs(graph, source, shortcuts):
        dist = {v: float("inf") for v in graph.vertices()}
        dist[source] = 0
        q = deque([source])
        while q:
            u = q.popleft()
            for v in graph.out_edges.get(u, set()):
                if dist[v] == float("inf"):
                    dist[v] = dist[u] + 1
                    q.append(v)
            if shortcuts:
                for a, b in shortcuts:
                    if a == u and dist[b] == float("inf"):
                        dist[b] = dist[u] + 1
                        q.append(b)
        return dist

    hop_dists = hop_count_bfs(g, source, shortcuts)
    max_hops = max(hop_dists[v] for v in original_reachable)
    print(f"Max hops from source {source} with shortcuts: {max_hops}")
    print()


def demo_shortest_paths():
    """Demonstrate hopset construction and approximate shortest paths."""
    print("=" * 60)
    print("DEMO 2: Hopset for Shortest Paths")
    print("=" * 60)

    n = 80
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)
    random.seed(42)
    for i in range(n - 1):
        g.add_edge(i, i + 1, 1)
    for j in range(150):  # noqa: B007
        u = random.randint(0, n - 2)
        v = random.randint(u + 1, n - 1)
        g.add_edge(u, v, random.randint(1, 5))

    print(f"Input graph: n={g.num_vertices()}, m={g.num_edges()}")

    epsilon = 0.1
    start = time.time()
    hopset, beta = build_hopset_for_sssp(g, epsilon=epsilon, random_seed=42)
    elapsed = time.time() - start

    print(f"Hopset size: {len(hopset)} edges")
    print(f"Target hopbound beta: {beta:.2f}")
    print(f"Approximation factor epsilon: {epsilon}")
    print(f"Construction time: {elapsed:.3f}s")

    source = 0
    original_distances = dijkstra(g, source)
    hopset_distances = shortest_path_hopbound(g, hopset, source, max_hops=1000)

    max_ratio = 0.0
    mismatches = 0
    for v in g.vertices():
        orig = original_distances.get(v, float("inf"))
        hop = hopset_distances.get(v, float("inf"))
        if orig == float("inf"):
            continue
        if hop == float("inf"):
            mismatches += 1
            continue
        if hop > (1 + epsilon) * orig + 1e-9:
            mismatches += 1
        ratio = hop / orig if orig > 0 else 0.0
        max_ratio = max(max_ratio, ratio)

    print(f"Distance preservation check: {mismatches} mismatches")
    print(f"Max observed ratio: {max_ratio:.4f} (limit: {1 + epsilon:.4f})")
    print()


def demo_scc_handling():
    """Demonstrate SCC contraction for reachability on cyclic graphs."""
    print("=" * 60)
    print("DEMO 3: SCC Handling for Cyclic Graphs")
    print("=" * 60)

    g = Digraph()
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 0)
    g.add_edge(2, 3)
    g.add_edge(4, 5)
    g.add_edge(5, 4)
    g.add_edge(3, 4)

    print(f"Input graph: n={g.num_vertices()}, m={g.num_edges()}")

    sccs = strongly_connected_components(g)
    print(f"Strongly connected components: {len(sccs)}")
    for i, scc in enumerate(sccs):
        print(f"  SCC {i}: {scc}")

    shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
    print(f"Shortcut set size: {len(shortcuts)} edges")
    print(f"Target hopbound beta: {beta:.2f}")

    for scc in sccs:
        for u in scc:
            for v in scc:
                if u != v:
                    assert (u, v) in shortcuts

    print("All SCC shortcuts present.")
    print()


def demo_astar():
    """Demonstrate A* search on a grid."""
    print("=" * 60)
    print("DEMO 4: A* Search on a Grid")
    print("=" * 60)

    n = 10
    g = WeightedDigraph()
    for i in range(n):
        for j in range(n):
            g.add_vertex((i, j))
            if i + 1 < n:
                g.add_edge((i, j), (i + 1, j), 1)
            if j + 1 < n:
                g.add_edge((i, j), (i, j + 1), 1)

    target = (n - 1, n - 1)

    def manhattan(v):
        return abs(v[0] - target[0]) + abs(v[1] - target[1])

    start = time.time()
    astar_dist = astar(g, (0, 0), target, manhattan)
    astar_time = time.time() - start

    start = time.time()
    dijkstra_dist = dijkstra(g, (0, 0))[target]
    dijkstra_time = time.time() - start

    print(f"Grid size: {n}x{n}")
    print(f"A* distance: {astar_dist}, time: {astar_time:.4f}s")
    print(f"Dijkstra distance: {dijkstra_dist}, time: {dijkstra_time:.4f}s")
    assert astar_dist == dijkstra_dist
    print()


if __name__ == "__main__":
    demo_reachability()
    demo_shortest_paths()
    demo_scc_handling()
    demo_astar()
    print("All demos completed successfully.")
