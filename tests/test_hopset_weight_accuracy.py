"""Hopset weight accuracy under multi-PYTHONHASHSEED.

Every hopset edge weight must equal the original-graph exact
shortest-path distance. The earlier weighted SCC condensation
emitted underweighted shortcuts on hash-randomized inputs.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from reachq.core.graph import WeightedDigraph
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.shortest_paths import dijkstra


REPO_ROOT = Path(__file__).parent.parent


def _weighted_graph_with_sccs() -> WeightedDigraph:
    """Reviewer's SCC counterexample: a <-> b cost 100; b -> c cost 1.

    True distance from a to c is 101.
    """
    g = WeightedDigraph()
    g.add_edge("a", "b", 100)
    g.add_edge("b", "a", 100)
    g.add_edge("b", "c", 1)
    return g


def test_hopset_weights_match_dijkstra():
    g = _weighted_graph_with_sccs()
    H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
    for (u, v), w in H.items():
        assert isinstance(w, int)
        assert w >= 0
        actual = dijkstra(g, u).get(v)
        assert actual == w, (
            f"hopset edge {u}->{v} claims weight {w} but exact distance is {actual}"
        )


def test_hopset_under_random_seeds_is_stable():
    """Across many ``random_seed`` values, every emitted weight is exact."""
    g = _weighted_graph_with_sccs()
    for seed in range(20):
        H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=seed)
        for (u, v), w in H.items():
            actual = dijkstra(g, u).get(v)
            assert actual == w, (
                f"seed={seed}: hopset claims {u}->{v} weight {w} "
                f"but exact is {actual}"
            )


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_hopset_reproducible_under_hash_seeds(seed):
    """Distinct ``PYTHONHASHSEED`` values must produce byte-identical
    hopset outputs for the same ``random_seed``.

    Runs the construction in a fresh subprocess so the hash
    randomization takes effect.
    """
    code = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, '{REPO_ROOT}')
        from reachq.core.graph import WeightedDigraph
        from reachq.core.hopset import build_hopset_for_sssp
        g = WeightedDigraph()
        g.add_edge('a', 'b', 100)
        g.add_edge('b', 'a', 100)
        g.add_edge('b', 'c', 1)
        H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        print(repr(sorted(H.items())))
        """
    )
    results = []
    for run in range(2):
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
        )
        results.append(result.stdout.strip())
    assert results[0] == results[1], (
        f"hash seed {seed}: hopset output unstable across runs"
    )


def test_weight_accuracy_under_hash_seed():
    """Under hash randomization, no emitted shortcut underweights
    the original distance."""
    code = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, '%s')
        from reachq.core.graph import WeightedDigraph
        from reachq.core.hopset import build_hopset_for_sssp
        from reachq.core.shortest_paths import dijkstra
        g = WeightedDigraph()
        g.add_edge('a', 'b', 100)
        g.add_edge('b', 'a', 100)
        g.add_edge('b', 'c', 1)
        H, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=42)
        for (u, v), w in H.items():
            actual = dijkstra(g, u).get(v, 1 << 62)
            print(repr(((u, v), w)) + " : " + repr((u, v)) + " -> " + str(actual))
        """ % REPO_ROOT
    )
    for seed in range(3):
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            inner = line.strip("{} ")
            parts = inner.split(" : ")
            short_label = parts[0].strip()
            actual_label = parts[-1].strip()
            assert short_label == actual_label, (
                f"hash seed {seed}: hopset mismatch: {line}"
            )
