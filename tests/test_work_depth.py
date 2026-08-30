"""Tests for work/depth simulation model."""

from reachq.work_depth import (
    WorkDepthAccountant,
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

    def test_record_with_details(self):
        wd = WorkDepthAccountant()
        wd.record("op", work=1.0, depth=1.0, details="note")
        assert wd.operations()[0].details == "note"

    def test_timer(self):
        wd = WorkDepthAccountant()
        wd.start_timer()
        wd.stop_timer()
        assert wd.elapsed_seconds >= 0.0

    def test_stop_timer_no_start(self):
        wd = WorkDepthAccountant()
        wd.stop_timer()
        assert wd.elapsed_seconds == 0.0

    def test_repr(self):
        wd = WorkDepthAccountant()
        wd.record("x", work=100, depth=10)
        r = repr(wd)
        assert "1.00e+02" in r
        assert "1.00e+01" in r

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
        assert wd1.depth == 8.0

    def test_parallel_composition_empty(self):
        wd = WorkDepthAccountant()
        wd.record("a", work=10, depth=3)
        wd.parallel_composition([])
        assert wd.work == 10.0
        assert wd.depth == 3.0

    def test_summary(self):
        wd = WorkDepthAccountant()
        wd.record("x", work=100, depth=10)
        s = wd.summary()
        assert s["work"] == 100.0
        assert s["depth"] == 10.0


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


class TestSpanProfiler:
    """Tests for SpanProfiler (empirical parallel span measurement)."""

    def test_empty_profiler_reports_zero_span(self):
        from reachq.work_depth import SpanProfiler

        p = SpanProfiler()
        assert p.total_span_seconds() == 0.0
        s = p.summary()
        assert s["span_seconds"] == 0.0
        assert s["theoretical_work"] == 0.0

    def test_phases_accumulate(self):
        import time as _t

        from reachq.work_depth import SpanProfiler

        p = SpanProfiler()
        p.begin_phase("a")
        _t.sleep(0.01)
        # begin_phase closes the previous phase, so 'a' is recorded.
        p.begin_phase("b")
        _t.sleep(0.01)
        p.end_phase()
        span = p.total_span_seconds()
        # a + b = ~20ms minimum; allow slack
        assert span >= 0.02, f"expected >= 20ms, got {span}"
        assert len(p.phases) == 2
        assert {ph.name for ph in p.phases} == {"a", "b"}

    def test_summary_includes_all_phases(self):
        from reachq.work_depth import SpanProfiler

        p = SpanProfiler()
        p.begin_phase("first")
        p.end_phase()
        p.begin_phase("second")
        p.end_phase()
        s = p.summary()
        assert "phase_first_seconds" in s
        assert "phase_second_seconds" in s

    def test_repr_includes_span(self):
        from reachq.work_depth import SpanProfiler

        p = SpanProfiler()
        r = repr(p)
        assert "SpanProfiler" in r
        assert "span=" in r
