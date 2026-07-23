"""Tests for shortest path algorithms."""

from reachq.graph import WeightedDigraph
from reachq.shortest_paths import (
    astar,
    compute_d_ancestors,
    compute_d_ball,
    compute_d_descendants,
    dijkstra,
    shortest_path_hopbound,
    shortest_path_tree,
    truncated_dijkstra,
)


class TestDijkstra:
    """Tests for Dijkstra's algorithm."""

    def test_simple_path(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(0, 2, 10)
        dists = dijkstra(g, 0)
        assert dists[0] == 0
        assert dists[1] == 1
        assert dists[2] == 3

    def test_unreachable(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_vertex(2)
        dists = dijkstra(g, 0)
        assert dists[1] == 1
        assert dists[2] == float("inf")

    def test_single_vertex(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        dists = dijkstra(g, 0)
        assert dists[0] == 0

    def test_empty_graph(self):
        g = WeightedDigraph()
        dists = dijkstra(g, 0)
        assert dists == {0: 0}

    def test_self_loop(self):
        g = WeightedDigraph()
        g.add_edge(0, 0, 5)
        g.add_edge(0, 1, 1)
        dists = dijkstra(g, 0)
        assert dists[0] == 0
        assert dists[1] == 1

    def test_parallel_edges_min_weight(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 5)
        g.add_edge(0, 1, 2)
        dists = dijkstra(g, 0)
        assert dists[1] == 2

    def test_cycle(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 1)
        g.add_edge(2, 0, 1)
        g.add_edge(0, 2, 5)
        dists = dijkstra(g, 0)
        assert dists[2] == 2  # Via 0->1->2

    def test_large_graph(self):
        n = 100
        g = WeightedDigraph()
        for i in range(n):
            g.add_vertex(i)
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        dists = dijkstra(g, 0)
        assert dists[n - 1] == n - 1


class TestAStar:
    """Tests for A* search."""

    def test_simple_path(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(0, 2, 10)

        def h(v):
            return {0: 3, 1: 2, 2: 0}.get(v, 0)

        assert astar(g, 0, 2, h) == 3

    def test_same_source_target(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        assert astar(g, 0, 0, lambda v: 0) == 0

    def test_visited_skip(self):
        """Trigger the 'u in visited' branch via multiple heap entries."""
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(0, 2, 3)
        g.add_edge(1, 2, 1)
        # Vertex 2 is pushed twice (direct 0->2 and via 0->1->2).
        assert astar(g, 0, 2, lambda v: 0) == 2

    def test_unreachable(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        g.add_vertex(1)
        assert astar(g, 0, 1, lambda v: 0) is None

    def test_zero_heuristic_is_dijkstra(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(0, 2, 10)
        astar_dist = astar(g, 0, 2, lambda v: 0)
        dijkstra_dist = dijkstra(g, 0)[2]
        assert astar_dist == dijkstra_dist

    def test_inadmissible_heuristic_still_finds_path(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        # Heuristic overestimates for vertex 0
        assert astar(g, 0, 2, lambda v: 100 if v == 0 else 0) == 3

    def test_grid_heuristic(self):
        """A* on a 5x5 grid with Manhattan heuristic."""
        g = WeightedDigraph()
        n = 5
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

        dist = astar(g, (0, 0), target, manhattan)
        assert dist == 2 * (n - 1)


class TestTruncatedDijkstra:
    """Tests for truncated Dijkstra."""

    def test_truncation(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 10)
        dists = truncated_dijkstra(g, 0, 3)
        assert 0 in dists
        assert 1 in dists
        assert 2 in dists
        assert 3 not in dists

    def test_no_truncation_needed(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        dists = truncated_dijkstra(g, 0, 100)
        assert dists[2] == 3

    def test_empty(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        dists = truncated_dijkstra(g, 0, 10)
        assert dists == {0: 0}

    def test_visited_skip(self):
        """Trigger the 'u in visited' branch via multiple heap entries."""
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(0, 2, 3)
        g.add_edge(1, 2, 1)
        dists = truncated_dijkstra(g, 0, 10)
        assert dists[2] == 2


class TestDBall:
    """Tests for d-ball computations."""

    def test_d_descendants(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 10)
        desc = compute_d_descendants(g, 0, 3)
        assert desc == {0, 1, 2}

    def test_d_ancestors(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 10)
        anc = compute_d_ancestors(g, 3, 3)
        assert anc == {3}

    def test_d_ball(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 0, 1)
        ball = compute_d_ball(g, 0, 1)
        assert ball == {0, 1, 2}


class TestShortestPathHopbound:
    """Tests for hop-bounded shortest paths."""

    def test_basic(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(2, 3, 3)
        hopset = {}
        dists = shortest_path_hopbound(g, hopset, 0, 10)
        assert dists[3] == 6

    def test_with_hopset(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 1)
        g.add_edge(2, 3, 1)
        hopset = {(0, 3): 5}
        dists = shortest_path_hopbound(g, hopset, 0, 2)
        assert dists[3] == 5

    def test_max_hops_zero(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        hopset = {}
        dists = shortest_path_hopbound(g, hopset, 0, 0)
        assert dists == {0: 0}

    def test_unreachable_within_hops(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 1)
        g.add_edge(2, 3, 1)
        hopset = {}
        dists = shortest_path_hopbound(g, hopset, 0, 1)
        assert 3 not in dists


class TestShortestPathTree:
    """Tests for shortest path tree."""

    def test_simple(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_edge(1, 2, 2)
        g.add_edge(0, 2, 10)
        parent = shortest_path_tree(g, 0)
        assert parent[0] is None
        assert parent[1] == 0
        assert parent[2] == 1

    def test_unreachable(self):
        g = WeightedDigraph()
        g.add_edge(0, 1, 1)
        g.add_vertex(2)
        parent = shortest_path_tree(g, 0)
        assert parent[2] is None

    def test_single_vertex(self):
        g = WeightedDigraph()
        g.add_vertex(0)
        parent = shortest_path_tree(g, 0)
        assert parent[0] is None


class TestDeterminism:
    """Tests that shortest path algorithms are deterministic."""

    def test_dijkstra_deterministic(self):
        g = WeightedDigraph()
        for i in range(50):
            g.add_edge(i, i + 1, 1)
        d1 = dijkstra(g, 0)
        d2 = dijkstra(g, 0)
        assert d1 == d2

    def test_astar_deterministic(self):
        g = WeightedDigraph()
        for i in range(20):
            g.add_edge(i, i + 1, 1)
        a1 = astar(g, 0, 20, lambda v: 20 - v)
        a2 = astar(g, 0, 20, lambda v: 20 - v)
        assert a1 == a2
