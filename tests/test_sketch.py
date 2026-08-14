"""Tests for HyperLogLog reachability sketches."""

from __future__ import annotations

from reachq.core.generators import dense_graph, path_graph
from reachq.research.sketch import (
    HyperLogLogSketch,
    sketch_reachability_estimate,
    sketch_reachability_streaming,
)


def test_hll_empty_sketch():
    """An empty sketch has cardinality 0."""
    sketch = HyperLogLogSketch(precision=14)
    assert sketch.cardinality() == 0


def test_hll_single_item():
    """A sketch with one item has cardinality >= 1."""
    sketch = HyperLogLogSketch(precision=14)
    sketch.add("hello")
    # The estimate should be at least 1.
    assert sketch.cardinality() >= 1


def test_hll_known_cardinality():
    """Sketching 1000 distinct items gives an estimate close to 1000."""
    sketch = HyperLogLogSketch(precision=14)
    for i in range(1000):
        sketch.add(f"item-{i}")
    estimate = sketch.cardinality()
    # HyperLogLog with p=14 has standard error ~1.04/sqrt(2^14) ~= 0.81%.
    # Allow 5% tolerance for safety.
    assert abs(estimate - 1000) / 1000 < 0.05, f"estimate {estimate} too far from 1000"


def test_hll_merge():
    """Merging two sketches of disjoint sets gives the union cardinality."""
    sketch_a = HyperLogLogSketch(precision=14)
    sketch_b = HyperLogLogSketch(precision=14)
    for i in range(500):
        sketch_a.add(f"a-{i}")
    for i in range(500):
        sketch_b.add(f"b-{i}")
    sketch_a.merge(sketch_b)
    estimate = sketch_a.cardinality()
    assert abs(estimate - 1000) / 1000 < 0.05


def test_hll_invalid_precision():
    """Precision outside [4, 16] raises ValueError."""
    try:
        HyperLogLogSketch(precision=3)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_hll_merge_different_precision_raises():
    """Merging sketches of different precisions raises ValueError."""
    s1 = HyperLogLogSketch(precision=14)
    s2 = HyperLogLogSketch(precision=10)
    try:
        s1.merge(s2)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_sketch_reachability_path_graph():
    """Sketch reachability from 0 in a path graph of 50 vertices."""
    g = path_graph(50)
    estimate = sketch_reachability_estimate(g, 0, precision=14)
    assert abs(estimate - 50) / 50 < 0.05


def test_sketch_reachability_streaming_returns_sketch():
    """The streaming variant returns a HyperLogLogSketch, not a count."""
    g = path_graph(20)
    sketch = sketch_reachability_streaming(g, 0, precision=12)
    assert isinstance(sketch, HyperLogLogSketch)
    estimate = sketch.cardinality()
    assert abs(estimate - 20) / 20 < 0.08


def test_sketch_reachability_dense_graph():
    """A dense graph where every vertex reaches every other."""
    g = dense_graph(10, 90, random_seed=42)  # near-complete
    estimate = sketch_reachability_estimate(g, 0, precision=14)
    # The estimate should be close to 10.
    assert abs(estimate - 10) / 10 <= 0.10
