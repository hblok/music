"""Tests for inspector.metrics — the shared metric battery."""

from __future__ import annotations

import unittest

import numpy as np

from inspector.metrics import (
    Metrics,
    band_balance,
    band_decay_ms,
    characterize,
    centroid_hz,
    detect_chord,
    fft_peaks,
    onset_stats,
    percussive_ratio,
)
from soundmatch.tests.fixtures import (
    REF_BAND_BALANCE,
    REF_CENTROID_HZ,
    REF_CHORD_SUB_OCTAVE,
    REF_MEDIAN_IOI_S,
    REF_ONSET_COUNT,
    REF_PERCUSSIVE_RATIO,
    TOL_BAND,
    TOL_CENTROID,
    TOL_ONSET_COUNT,
    TOL_PERC,
    ensure_fixture,
)


class TestPercussiveRatio(unittest.TestCase):
    """Test percussive_ratio() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_float(self):
        result = percussive_ratio(self.y, self.sr)
        self.assertIsInstance(result, float)

    def test_range_0_100(self):
        result = percussive_ratio(self.y, self.sr)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 100.0)

    def test_percussive_signal_high(self):
        result = percussive_ratio(self.y, self.sr)
        self.assertGreater(result, 50.0, "Percussive fixture should have >50% perc ratio")

    def test_silent_signal(self):
        y = np.zeros(44100)
        result = percussive_ratio(y, 44100)
        self.assertEqual(result, 0.0)

    def test_pure_tone_low(self):
        sr = 44100
        t = np.arange(sr) / sr
        y = np.sin(2 * np.pi * 440.0 * t)
        result = percussive_ratio(y, sr)
        self.assertLess(result, 30.0, "Pure tone should have low perc ratio")


class TestCentroidHz(unittest.TestCase):
    """Test centroid_hz() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_float(self):
        result = centroid_hz(self.y, self.sr)
        self.assertIsInstance(result, float)

    def test_centroid_reasonable(self):
        result = centroid_hz(self.y, self.sr)
        self.assertGreater(result, 100.0)
        self.assertLess(result, 10000.0)

    def test_high_freq_signal(self):
        sr = 44100
        t = np.arange(sr) / sr
        y = np.sin(2 * np.pi * 5000.0 * t)
        result = centroid_hz(y, sr)
        self.assertGreater(result, 3000.0, "5kHz tone should have centroid >3kHz")


class TestBandBalance(unittest.TestCase):
    """Test band_balance() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_dict(self):
        result = band_balance(self.y, self.sr)
        self.assertIsInstance(result, dict)

    def test_four_bands(self):
        result = band_balance(self.y, self.sr)
        self.assertEqual(len(result), 4)
        for key in ("80-300", "300-800", "800-2500", "2500-9000"):
            self.assertIn(key, result)

    def test_sums_to_100(self):
        result = band_balance(self.y, self.sr)
        total = sum(result.values())
        self.assertAlmostEqual(total, 100.0, delta=1.0)

    def test_mid_band_dominant(self):
        result = band_balance(self.y, self.sr)
        mid = result.get("300-800", 0) + result.get("800-2500", 0)
        self.assertGreater(mid, 20.0, "Mid bands should be significant")


class TestOnsetStats(unittest.TestCase):
    """Test onset_stats() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_dict(self):
        result = onset_stats(self.y, self.sr)
        self.assertIsInstance(result, dict)
        for key in ("onset_count", "onset_density", "median_ioi_s"):
            self.assertIn(key, result)

    def test_onset_count_positive(self):
        result = onset_stats(self.y, self.sr)
        self.assertGreater(result["onset_count"], 0)

    def test_median_ioi_reasonable(self):
        result = onset_stats(self.y, self.sr)
        self.assertGreater(result["median_ioi_s"], 0.0)
        self.assertLess(result["median_ioi_s"], 2.0)

    def test_silent_signal_no_onsets(self):
        y = np.zeros(44100)
        result = onset_stats(y, 44100)
        self.assertEqual(result["onset_count"], 0)


class TestFftPeaks(unittest.TestCase):
    """Test fft_peaks() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_list(self):
        result = fft_peaks(self.y, self.sr)
        self.assertIsInstance(result, list)

    def test_peak_format(self):
        result = fft_peaks(self.y, self.sr)
        if result:
            freq, rel_db = result[0]
            self.assertIsInstance(freq, float)
            self.assertIsInstance(rel_db, float)
            self.assertGreater(freq, 0.0)
            self.assertLessEqual(rel_db, 0.0)

    def test_max_20_peaks(self):
        result = fft_peaks(self.y, self.sr)
        self.assertLessEqual(len(result), 20)


class TestDetectChord(unittest.TestCase):
    """Test detect_chord() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_dict(self):
        result = detect_chord(self.y, self.sr)
        self.assertIsInstance(result, dict)
        for key in ("pitch_classes", "midi", "sub_octave"):
            self.assertIn(key, result)

    def test_pitch_classes_are_notes(self):
        result = detect_chord(self.y, self.sr)
        _NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for pc in result["pitch_classes"]:
            self.assertIn(pc, _NOTES)


class TestBandDecayMs(unittest.TestCase):
    """Test band_decay_ms() against the synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100

    def test_returns_dict(self):
        result = band_decay_ms(self.y, self.sr)
        self.assertIsInstance(result, dict)

    def test_positive_decay(self):
        result = band_decay_ms(self.y, self.sr)
        for label, ms in result.items():
            self.assertGreaterEqual(ms, 0.0, f"Decay for {label} should be >= 0")


class TestCharacterize(unittest.TestCase):
    """Test the characterize() entry point."""

    @classmethod
    def setUpClass(cls):
        cls.y = ensure_fixture()
        cls.sr = 44100
        cls.metrics = characterize(cls.y, cls.sr)

    def test_returns_metrics(self):
        self.assertIsInstance(self.metrics, Metrics)

    def test_metrics_fields_populated(self):
        m = self.metrics
        self.assertGreater(m.percussive_ratio, 0.0)
        self.assertGreater(m.centroid_hz, 0.0)
        self.assertIsInstance(m.band_balance, dict)
        self.assertGreater(m.onset_count, 0)
        self.assertGreater(m.onset_density, 0.0)
        self.assertIsInstance(m.peaks, list)
        self.assertIsInstance(m.chord, dict)
        self.assertIsInstance(m.band_decay_ms, dict)

    def test_metrics_serialization_roundtrip(self):
        d = self.metrics.to_dict()
        m2 = Metrics.from_dict(d)
        self.assertAlmostEqual(m2.percussive_ratio, self.metrics.percussive_ratio, places=3)
        self.assertAlmostEqual(m2.centroid_hz, self.metrics.centroid_hz, places=1)
        self.assertEqual(m2.onset_count, self.metrics.onset_count)

    def test_frozen(self):
        with self.assertRaises(AttributeError):
            self.metrics.percussive_ratio = 0.0  # type: ignore


if __name__ == "__main__":
    unittest.main()