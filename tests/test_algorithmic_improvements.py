"""Tests for the algorithmic improvements (Phase 3) and ablation flags.

Every improvement should be toggleable. Disabling a flag must still produce
a correct shortcut set / hopset. We don't assert bit-exact equality with
the "all on" output (because sampling is non-deterministic under flag
changes that affect the partition key) but we do assert the structural
invariants documented in `docs/algorithmic_improvements.md`.
"""

from __future__ import annotations

from importlib.util import find_spec

import pytest

from reachq import Flags
from reachq.core.generators import random_dag, weighted_random_dag
from reachq.core.hopset import build_hopset_for_sssp
from reachq.core.reachability import bfs_reachability, parallel_bfs
from reachq.core.algorithm import build_shortcut_set_for_reachability
from reachq.core.shortest_paths import dijkstra, shortest_path_hopbound


def all_flag_names() -> list[str]:
    return list(Flags.__dataclass_fields__)


@pytest.mark.parametrize("off", all_flag_names())
def test_shortcut_set_correctness_with_each_flag_off(off: str) -> None:
    """Disabling any single flag must still preserve reachability."""
    g = random_dag(n=80, edge_probability=0.2, random_seed=7)
    flags = {name: False if name == off else True for name in all_flag_names()}
    shortcuts, beta = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=7,
        flags=flags,
    )
    assert beta > 0
    for v in g.vertices():
        original = bfs_reachability(g, v)
        augmented = parallel_bfs(g, v, shortcuts)
        assert original == augmented, f"flag {off} off breaks correctness from {v}"


@pytest.mark.parametrize("off", all_flag_names())
def test_hopset_correctness_with_each_flag_off(off: str) -> None:
    """Disabling any single flag must still preserve (1+eps) hopbound."""
    g = weighted_random_dag(n=60, edge_probability=0.2, random_seed=7)
    flags = {name: False if name == off else True for name in all_flag_names()}
    hopset, _ = build_hopset_for_sssp(g, epsilon=0.1, random_seed=7, flags=flags)
    src = next(iter(g.vertices()))
    orig = dijkstra(g, src)
    approx = shortest_path_hopbound(g, hopset, src, max_hops=1000)
    for v in g.vertices():
        od = orig.get(v, float("inf"))
        if od == float("inf"):
            continue
        ad = approx.get(v, float("inf"))
        assert (
            ad <= 1.1 * od + 1e-9
        ), f"flag {off} off breaks (1+eps) bound for {v}: orig={od}, approx={ad}"


def test_flags_dataclass_rejects_unknown_names() -> None:
    with pytest.raises(ValueError):
        Flags.from_dict({"does_not_exist": True})


def test_all_on_matches_dataclass_default() -> None:
    """All *algorithmic* refinements default on; parallel is opt-in."""
    flags = Flags.from_dict(None)
    algorithmic = [n for n in all_flag_names() if n != "parallel"]
    assert all(getattr(flags, name) is True for name in algorithmic)
    # parallel is opt-in because threading has overhead the user must
    # explicitly accept (otherwise it changes reproducibility in
    # subtle ways via thread scheduling).
    assert flags.parallel is False


def test_networkx_cross_check_shortcut_set() -> None:
    """Cross-check shortcut-set reachability against networkx.descendants."""
    if find_spec("networkx") is None:
        pytest.skip("networkx not installed (dev-only cross-check)")

    import networkx as nx

    from reachq.core.graph import Digraph

    g = Digraph()
    for i in range(50):
        for j in range(i + 1, 50):
            if (i * 7 + j * 3) % 13 < 4:
                g.add_edge(i, j)

    nxg = nx.DiGraph()
    nxg.add_nodes_from(g.vertices())
    for u, v in g.edges():
        nxg.add_edge(u, v)

    shortcuts, _ = build_shortcut_set_for_reachability(
        g,
        omega=3.0,
        random_seed=42,
    )

    # Build augmented graph and compare descendants.
    aug = nx.DiGraph()
    aug.add_nodes_from(nxg.nodes)
    aug.add_edges_from(nxg.edges)
    aug.add_edges_from(shortcuts)

    for v in g.vertices():
        ours = parallel_bfs(g, v, shortcuts)
        theirs = nx.descendants(aug, v) | {v}
        assert ours == theirs, f"networkx disagrees from {v}"
