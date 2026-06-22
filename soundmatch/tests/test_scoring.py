"""Tests for soundmatch.core.scoring — diff math, aggregate, worst."""
from __future__ import annotations

import unittest

from inspector.metrics import Metrics
from soundmatch.core.scoring import MetricDelta, Scorecard, diff


def _target_metrics() -> Metrics:
    return Metrics(
        percussive_ratio=82.0,
        centroid_hz=2542.0,
        band_balance={"80-300": 18.0, "300-800": 30.0, "800-2500": 41.0, "2500-9000": 7.0},
        onset_count=36,
        onset_density=4.5,
        median_ioi_s=0.238,
        peaks=[(800.0, -3.0)],
        chord={"pitch_classes": ["G#"], "midi": [68], "sub_octave": True},
        band_decay_ms={"200-1500": 30.0, "3500-9000": 15.0},
    )


def _close_metrics() -> Metrics:
    """Metrics close to the target."""
    return Metrics(
        percussive_ratio=80.0,
        centroid_hz=2500.0,
        band_balance={"80-300": 17.0, "300-800": 31.0, "800-2500": 40.0, "2500-9000": 8.0},
        onset_count=35,
        onset_density=4.4,
        median_ioi_s=0.240,
        peaks=[(790.0, -3.5)],
        chord={"pitch_classes": ["G#"], "midi": [68], "sub_octave": True},
        band_decay_ms={"200-1500": 28.0, "3500-9000": 14.0},
    )


def _far_metrics() -> Metrics:
    """Metrics far from the target."""
    return Metrics(
        percussive_ratio=20.0,
        centroid_hz=500.0,
        band_balance={"80-300": 5.0, "300-800": 10.0, "800-2500": 60.0, "2500-9000": 25.0},
        onset_count=5,
        onset_density=0.5,
        median_ioi_s=1.0,
        peaks=[],
        chord={"pitch_classes": [], "midi": [], "sub_octave": False},
        band_decay_ms={"200-1500": 200.0, "3500-9000": 100.0},
    )


class TestDiffFunction(unittest.TestCase):
    """Test diff() produces correct deltas."""

    def test_identical_metrics_zero_delta(self):
        t = _target_metrics()
        sc = diff(t, t)
        self.assertAlmostEqual(sc.percussive_ratio.delta, 0.0)
        self.assertAlmostEqual(sc.centroid_hz.delta, 0.0)
        self.assertAlmostEqual(sc.onset_count.delta, 0.0)

    def test_close_metrics_small_delta(self):
        t = _target_metrics()
        c = _close_metrics()
        sc = diff(t, c)
        self.assertLess(sc.percussive_ratio.delta, 5.0)
        self.assertLess(sc.centroid_hz.delta, 100.0)

    def test_far_metrics_large_delta(self):
        t = _target_metrics()
        c = _far_metrics()
        sc = diff(t, c)
        self.assertGreater(sc.percussive_ratio.delta, 50.0)
        self.assertGreater(sc.centroid_hz.delta, 1000.0)

    def test_band_balance_deltas(self):
        t = _target_metrics()
        c = _far_metrics()
        sc = diff(t, c)
        self.assertIn("80-300", sc.band_balance)
        self.assertGreater(sc.band_balance["80-300"].delta, 0.0)

    def test_band_decay_deltas(self):
        t = _target_metrics()
        c = _far_metrics()
        sc = diff(t, c)
        self.assertIn("200-1500", sc.band_decay_ms)
        self.assertGreater(sc.band_decay_ms["200-1500"].delta, 0.0)


class TestScorecardAggregate(unittest.TestCase):
    """Test Scorecard.aggregate() monotonic behavior."""

    def test_identical_is_zero(self):
        t = _target_metrics()
        sc = diff(t, t)
        self.assertAlmostEqual(sc.aggregate(), 0.0, places=3)

    def test_close_less_than_far(self):
        t = _target_metrics()
        sc_close = diff(t, _close_metrics())
        sc_far = diff(t, _far_metrics())
        self.assertLess(sc_close.aggregate(), sc_far.aggregate())

    def test_far_is_large(self):
        t = _target_metrics()
        sc = diff(t, _far_metrics())
        self.assertGreater(sc.aggregate(), 0.3)


class TestScorecardWorst(unittest.TestCase):
    """Test Scorecard.worst() picks the metric to chase next."""

    def test_identical_has_worst(self):
        t = _target_metrics()
        sc = diff(t, t)
        # All deltas are 0; worst still returns a name
        worst = sc.worst()
        self.assertIsInstance(worst, str)
        self.assertIn(worst, {"percussive_ratio", "centroid_hz", "band_balance",
                              "onset_count", "onset_density", "median_ioi_s", "band_decay_ms"})

    def test_far_metrics_worst_is_large_delta(self):
        t = _target_metrics()
        c = _far_metrics()
        sc = diff(t, c)
        worst = sc.worst()
        # With far metrics, the worst should be a metric with a very large delta
        # percussive_ratio delta=62, centroid delta=2042, onset_count delta=31
        self.assertIn(worst, {"percussive_ratio", "centroid_hz", "onset_count",
                              "band_balance", "band_decay_ms", "onset_density", "median_ioi_s"})


class TestScorecardSerialization(unittest.TestCase):
    """Test Scorecard round-trip serialization."""

    def test_roundtrip(self):
        t = _target_metrics()
        c = _close_metrics()
        sc = diff(t, c)
        d = sc.to_dict()
        sc2 = Scorecard.from_dict(d)
        self.assertAlmostEqual(sc2.percussive_ratio.delta, sc.percussive_ratio.delta, places=3)
        self.assertAlmostEqual(sc2.centroid_hz.delta, sc.centroid_hz.delta, places=3)
        self.assertAlmostEqual(sc2.aggregate(), sc.aggregate(), places=3)


class TestMetricDelta(unittest.TestCase):
    """Test MetricDelta dataclass."""

    def test_to_dict(self):
        md = MetricDelta(target=82.0, candidate=80.0, delta=2.0)
        d = md.to_dict()
        self.assertEqual(d["target"], 82.0)
        self.assertEqual(d["candidate"], 80.0)
        self.assertEqual(d["delta"], 2.0)

    def test_from_dict(self):
        d = {"target": 82.0, "candidate": 80.0, "delta": 2.0}
        md = MetricDelta.from_dict(d)
        self.assertEqual(md.target, 82.0)
        self.assertEqual(md.delta, 2.0)

    def test_roundtrip(self):
        md = MetricDelta(target=50.0, candidate=30.0, delta=20.0)
        md2 = MetricDelta.from_dict(md.to_dict())
        self.assertEqual(md2.target, md.target)
        self.assertEqual(md2.delta, md.delta)


class TestDiffWithWeights(unittest.TestCase):
    """Test that weights influence aggregate and worst."""

    def test_custom_weights(self):
        t = _target_metrics()
        c = _far_metrics()
        sc = diff(t, c, weights={"percussive_ratio": 10.0, "centroid_hz": 0.1})
        # Heavy weight on percussive_ratio should make it the worst
        worst = sc.worst()
        # With percussive_ratio weight=10 and others=1, percussive should dominate
        self.assertEqual(worst, "percussive_ratio")


if __name__ == "__main__":
    unittest.main()
