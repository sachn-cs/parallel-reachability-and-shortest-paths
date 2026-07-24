"""Tests for the new within-layer shortcuts in layered_dag_shortcut_set."""

from __future__ import annotations

from reachq.research.closed_form import (
    layered_dag_shortcut_set,
    verify_bipartite_layered_soundness,
    verify_layered_dag_optimality,
)


def test_layered_dag_shortcut_set_size():
    """The shortcut set should have L * s * (s-1) entries."""
    layers, layer_size = 3, 4
    H = layered_dag_shortcut_set(layers, layer_size)
    assert len(H) == layers * layer_size * (layer_size - 1)


def test_layered_dag_shortcut_set_within_layer_only():
    """All shortcuts should connect vertices in the same layer."""
    layers, layer_size = 3, 4
    H = layered_dag_shortcut_set(layers, layer_size)
    for u, v in H:
        u_layer, u_idx = divmod(u, layer_size)
        v_layer, v_idx = divmod(v, layer_size)
        assert u_layer == v_layer, f"cross-layer shortcut ({u}, {v})"
        assert u_idx != v_idx, f"self-loop shortcut ({u}, {v})"


def test_verify_layered_dag_optimality_passes():
    """The verification function should pass for small parameters."""
    result = verify_layered_dag_optimality(layers=2, layer_size=3)
    assert result["graph"] == "layered_2x3"
    # layers * layer_size * (layer_size - 1) = 2 * 3 * 2 = 12
    assert result["optimal_|H|"] == 12


def test_verify_bipartite_layered_soundness_passes():
    """The bipartite-only verification should pass."""
    result = verify_bipartite_layered_soundness(layers=3, layer_size=2)
    assert result["n"] == 6
    # m = (layers - 1) * layer_size^2 = 2 * 2 * 2 = 8
    assert result["m"] == 8