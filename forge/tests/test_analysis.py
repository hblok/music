"""Phase 6 tests: loudness analysis and loop-quality checks."""

import unittest

import numpy as np

from forge.analysis.loops import full_loop_report, rms_flatness_report, seam_report
from forge.analysis.loudness import (
    intro_vs_aftermath,
    peak_headroom_db,
    rms_trend_slope,
    section_rms_report,
)
from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.rng import RngContext
from forge.patterns.groove import render_loop
from forge.patterns.schedule import Schedule


# ---------------------------------------------------------------------------
# Helpers

def _sine_buf(freq=220.0, duration=4.0, sr=44100) -> AudioBuffer:
    n = int(duration * sr)
    t = np.arange(n, dtype=np.float64) / sr
    sig = 0.5 * np.sin(2.0 * np.pi * freq * t)
    return AudioBuffer.from_mono(sig, sr=sr)


def _ramping_buf(n=44100 * 4, sr=44100) -> AudioBuffer:
    """Buffer whose RMS rises linearly — should fail flatness check."""
    ramp = np.linspace(0, 1, n, dtype=np.float64)
    sig = ramp * np.sin(2.0 * np.pi * 220.0 * np.arange(n) / sr)
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------------------
# section_rms_report

class TestSectionRmsReport(unittest.TestCase):
    def test_has_required_keys(self):
        buf = _sine_buf()
        r = section_rms_report(buf)
        for k in ("section_rms", "mean_rms", "max_rms", "min_rms", "peak", "peak_db"):
            self.assertIn(k, r)

    def test_section_count(self):
        r = section_rms_report(_sine_buf(), n_sections=4)
        self.assertEqual(len(r["section_rms"]), 4)

    def test_peak_matches_buffer(self):
        buf = _sine_buf()
        r = section_rms_report(buf)
        self.assertAlmostEqual(r["peak"], buf.peak(), places=6)

    def test_silent_buf_zero_rms(self):
        buf = AudioBuffer(44100)
        r = section_rms_report(buf)
        self.assertAlmostEqual(r["mean_rms"], 0.0)


# ---------------------------------------------------------------------------
# rms_trend_slope

class TestRmsTrendSlope(unittest.TestCase):
    def test_constant_signal_flat(self):
        buf = _sine_buf(duration=4.0)
        slope = rms_trend_slope(buf)
        self.assertAlmostEqual(slope, 0.0, delta=0.001)

    def test_ramping_signal_positive(self):
        slope = rms_trend_slope(_ramping_buf())
        self.assertGreater(slope, 0)

    def test_decaying_signal_negative(self):
        n = 44100 * 4
        decay = np.linspace(1, 0, n, dtype=np.float64)
        sig = decay * np.sin(2.0 * np.pi * 220.0 * np.arange(n) / 44100)
        buf = AudioBuffer.from_mono(sig)
        slope = rms_trend_slope(buf)
        self.assertLess(slope, 0)


# ---------------------------------------------------------------------------
# peak_headroom_db

class TestPeakHeadroom(unittest.TestCase):
    def test_normalized_buffer(self):
        buf = _sine_buf().normalize(target=1.0)
        db = peak_headroom_db(buf)
        self.assertAlmostEqual(db, 0.0, delta=0.1)

    def test_quiet_buffer(self):
        buf = _sine_buf().normalize(target=0.5)
        db = peak_headroom_db(buf)
        self.assertAlmostEqual(db, 6.02, delta=0.1)

    def test_silence_high_headroom(self):
        db = peak_headroom_db(AudioBuffer(1000))
        self.assertGreater(db, 90.0)


# ---------------------------------------------------------------------------
# intro_vs_aftermath

class TestIntroVsAftermath(unittest.TestCase):
    def test_has_required_keys(self):
        buf = _sine_buf(duration=8.0)
        r = intro_vs_aftermath(buf, bpm=138.0, intro_bars=2, aftermath_bars=2)
        for k in ("intro_rms", "aftermath_rms", "ratio_db", "aftermath_quieter"):
            self.assertIn(k, r)

    def test_decaying_track_aftermath_quieter(self):
        n = int(8.0 * 44100)
        decay = np.linspace(1, 0.1, n, dtype=np.float64)
        sig = decay * np.sin(2.0 * np.pi * 220.0 * np.arange(n) / 44100)
        buf = AudioBuffer.from_mono(sig)
        r = intro_vs_aftermath(buf, bpm=138.0, intro_bars=2, aftermath_bars=2)
        self.assertTrue(r["aftermath_quieter"])
        self.assertLess(r["ratio_db"], 0.0)

    def test_growing_track_aftermath_louder(self):
        buf = _ramping_buf(n=44100 * 8)
        r = intro_vs_aftermath(buf, bpm=138.0, intro_bars=2, aftermath_bars=2)
        self.assertFalse(r["aftermath_quieter"])
        self.assertGreater(r["ratio_db"], 0.0)


# ---------------------------------------------------------------------------
# seam_report

class TestSeamReport(unittest.TestCase):
    def test_silence_perfect_seam(self):
        buf = AudioBuffer(44100)
        r = seam_report(buf)
        self.assertEqual(r["discontinuity"], 0.0)
        self.assertTrue(r["ok"])

    def test_has_required_keys(self):
        r = seam_report(AudioBuffer(1000))
        for k in ("start_L", "end_L", "start_R", "end_R", "discontinuity", "ok"):
            self.assertIn(k, r)

    def test_step_function_large_discontinuity(self):
        n = 1000
        buf = AudioBuffer(n)
        buf.data[:n // 2] = 1.0
        buf.data[n // 2:] = 0.0
        r = seam_report(buf)
        self.assertGreater(r["discontinuity"], 0.5)
        self.assertFalse(r["ok"])


# ---------------------------------------------------------------------------
# rms_flatness_report

class TestRmsFlatnessReport(unittest.TestCase):
    def test_constant_signal_ok(self):
        r = rms_flatness_report(_sine_buf(), n_sections=8, max_slope=0.005)
        self.assertAlmostEqual(r["slope"], 0.0, delta=0.001)
        self.assertTrue(r["ok"])

    def test_ramping_not_ok(self):
        r = rms_flatness_report(_ramping_buf(), n_sections=8, max_slope=0.005)
        self.assertFalse(r["ok"])
        self.assertGreater(r["slope"], 0)

    def test_has_required_keys(self):
        r = rms_flatness_report(_sine_buf())
        for k in ("section_rms", "slope", "ok"):
            self.assertIn(k, r)


# ---------------------------------------------------------------------------
# full_loop_report (integration)

class TestFullLoopReport(unittest.TestCase):
    def test_rendered_kick_loop_passes_flatness(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 4,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf = render_loop(sched, RngContext(42), xf_bars=2.0)
        r = full_loop_report(buf, seam_tolerance=0.5, max_slope=0.05)
        self.assertIn("seam", r)
        self.assertIn("flatness", r)
        # flatness check: a uniform kick pattern should be flat
        self.assertTrue(r["flatness"]["ok"])

    def test_full_report_ok_key(self):
        buf = _sine_buf()
        r = full_loop_report(buf, seam_tolerance=0.5, max_slope=0.01)
        self.assertIn("ok", r)
        self.assertIsInstance(r["ok"], bool)


if __name__ == "__main__":
    unittest.main()
