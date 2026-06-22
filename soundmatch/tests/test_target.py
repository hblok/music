"""Tests for soundmatch.core.target."""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from inspector.metrics import Metrics, characterize
from soundmatch.core.target import Target
from soundmatch.tests.fixtures import ensure_fixture


class TestTargetFromDict(unittest.TestCase):
    """Test Target serialization round-trip."""

    def test_roundtrip(self):
        m = characterize(ensure_fixture(), 44100)
        t = Target(
            path=Path("/some/file.mp3"),
            start_s=1.0,
            end_s=10.0,
            stem="other",
            sr=22050,
            metrics=m,
        )
        d = t.to_dict()
        t2 = Target.from_dict(d)
        self.assertEqual(t2.path, t.path)
        self.assertEqual(t2.start_s, t.start_s)
        self.assertEqual(t2.end_s, t.end_s)
        self.assertEqual(t2.stem, t.stem)
        self.assertAlmostEqual(t2.metrics.percussive_ratio, t.metrics.percussive_ratio, places=1)

    def test_metrics_none_roundtrip(self):
        t = Target(path=Path("test.wav"), start_s=0, end_s=5, stem="mix")
        d = t.to_dict()
        t2 = Target.from_dict(d)
        self.assertIsNone(t2.metrics)


class TestTargetMetrics(unittest.TestCase):
    """Test that Target carries Metrics from characterize."""

    def test_metrics_populated(self):
        y = ensure_fixture()
        sr = 44100
        m = characterize(y, sr)
        t = Target(path=Path("test.wav"), start_s=0, end_s=2, stem="mix", y=y, sr=sr, metrics=m)
        self.assertIsInstance(t.metrics, Metrics)
        self.assertGreater(t.metrics.percussive_ratio, 0)


class TestTargetDefaults(unittest.TestCase):
    """Test default values."""

    def test_default_stem(self):
        t = Target(path=Path("x"), start_s=0, end_s=1)
        self.assertEqual(t.stem, "other")

    def test_default_sr(self):
        t = Target(path=Path("x"), start_s=0, end_s=1)
        self.assertEqual(t.sr, 22050)

    def test_default_metrics_none(self):
        t = Target(path=Path("x"), start_s=0, end_s=1)
        self.assertIsNone(t.metrics)


if __name__ == "__main__":
    unittest.main()
