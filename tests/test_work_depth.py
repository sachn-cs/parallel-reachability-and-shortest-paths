"""Tests for work/depth simulation model."""

import math

import pytest

from prspnsd.work_depth import (
    WorkDepthAccountant,
    record_bfs,
    record_dijkstra,
    record_hopset_construction,
    record_matrix_multiply,
    record_shortcut_set_construction,
    record_tc_pruning,
    record_truncsssp_pruning,
    theoretical_hopset_depth,
    theoretical_hopset_work,
    theoretical_shortcut_depth,
    theoretical_shortcut_work,
)


class TestWorkDepthAccountant:
    """Tests for WorkDepthAccountant."""

    def test_empty(self):
        wd = WorkDepthAccountant()
        assert wd.work == 0.0
        assert wd.depth == 0.0
        assert wd.elapsed_seconds == 0.0
        assert wd.operations() == []

    def test_record(self):
        wd = WorkDepthAccountant()
        wd.record("test_op", work=10.0, depth=5.0)
        assert wd.work == 10.0
        assert wd.depth == 5.0
        assert len(wd.operations()) == 1
        assert wd.operations()[0].name == "test_op"

    def test_timer(self):
        wd = WorkDepthAccountant()
        wd.start_timer()
        wd.stop_timer()
        assert wd.elapsed_seconds >= 0.0

    def test_sequential_composition(self):
        wd1 = WorkDepthAccountant()
        wd1.record("a", work=10, depth=3)
        wd2 = WorkDepthAccountant()
        wd2.record("b", work=20, depth=5)
        wd1.sequential_composition(wd2)
        assert wd1.work == 30.0
        assert wd1.depth == 8.0

    def test_parallel_composition(self):
        wd1 = WorkDepthAccountant()
        wd1.record("a", work=10, depth=3)
        wd2 = WorkDepthAccountant()
        wd2.record("b", work=20, depth=5)
        wd1.parallel_composition([wd2])
        assert wd1.work == 30.0
        # depth = old_depth + max(other depths) = 3 + 5 = 8
        assert wd1.depth == 8.0

    def test_summary(self):
        wd = WorkDepthAccountant()
        wd.record("x", work=100, depth=10)
        s = wd.summary()
        assert s["work"] == 100.0
        assert s["depth"] == 10.0


class TestRecordingFunctions:
    """Tests for individual recording functions."""

    def test_record_bfs(self):
        wd = WorkDepthAccountant()
        record_bfs(wd, n=10, m=50)
        assert wd.work == 50.0
        assert wd.depth == 10.0

    def test_record_bfs_none(self):
        # Should not raise when accountant is None
        record_bfs(None, n=10, m=50)

    def test_record_dijkstra(self):
        wd = WorkDepthAccountant()
        record_dijkstra(wd, n=16, m=100)
        expected_work = 100 * math.log2(18)
        assert wd.work == pytest.approx(expected_work)
        assert wd.depth == pytest.approx(expected_work)

    def test_record_matrix_multiply(self):
        wd = WorkDepthAccountant()
        record_matrix_multiply(wd, n=100, omega=3.0)
        assert wd.work == 100 ** 3
        assert wd.depth == pytest.approx(math.log2(102))

    def test_record_tc_pruning(self):
        wd = WorkDepthAccountant()
        record_tc_pruning(wd, ball_size=16, omega=3.0)
        assert wd.work == 16 ** 3
        assert wd.depth == pytest.approx(math.log2(18))

    def test_record_tc_pruning_trivial(self):
        wd = WorkDepthAccountant()
        record_tc_pruning(wd, ball_size=1, omega=3.0)
        assert wd.work == 0.0

    def test_record_truncsssp_pruning(self):
        wd = WorkDepthAccountant()
        record_truncsssp_pruning(wd, ball_size=10)
        assert wd.work == 10 ** 3

    def test_record_shortcut_set_construction(self):
        wd = WorkDepthAccountant()
        record_shortcut_set_construction(wd, n=100, m=500, rho=2.0, omega=3.0)
        assert wd.work > 0.0
        assert wd.depth > 0.0

    def test_record_hopset_construction(self):
        wd = WorkDepthAccountant()
        record_hopset_construction(wd, n=100, m=500, rho=2.0, epsilon=0.1)
        assert wd.work > 0.0
        assert wd.depth > 0.0


class TestTheoreticalBounds:
    """Tests for theoretical bound helper functions."""

    def test_theoretical_shortcut_work_positive(self):
        w = theoretical_shortcut_work(n=100, m=500, rho=2.0, omega=3.0)
        assert w > 0.0

    def test_theoretical_shortcut_depth_positive(self):
        d = theoretical_shortcut_depth(n=100, rho=2.0)
        assert d > 0.0

    def test_theoretical_hopset_work_positive(self):
        w = theoretical_hopset_work(n=100, m=500, rho=2.0, epsilon=0.1)
        assert w > 0.0

    def test_theoretical_hopset_depth_positive(self):
        d = theoretical_hopset_depth(n=100, m=500, rho=2.0)
        assert d > 0.0
