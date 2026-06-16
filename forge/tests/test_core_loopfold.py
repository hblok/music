"""Tests for forge.core.loopfold."""

import unittest

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.loopfold import check_seam, loop_fold


class TestLoopFold(unittest.TestCase):
    def _make_sine_buf(self, n_bars, xf_bars, grid, freq=2.0):
        """Build a buffer with a sine wave for (n_bars + xf_bars) bars."""
        sr = grid.sr
        total_bars = n_bars + xf_bars
        n = int(round(total_bars * grid.bar * sr))
        t = np.arange(n) / sr
        sig = np.sin(2 * np.pi * freq * t)
        return AudioBuffer.from_mono(sig, sr=sr)

    def setUp(self):
        self.grid = Grid(bpm=120.0, sr=44100)

    def test_output_length_correct(self):
        n_bars, xf_bars = 8, 2
        buf = self._make_sine_buf(n_bars, xf_bars, self.grid)
        looped = loop_fold(buf, loop_bars=n_bars, xf_bars=xf_bars, grid=self.grid)
        expected = int(round(n_bars * self.grid.bar * self.grid.sr))
        self.assertEqual(len(looped), expected)

    def test_short_buffer_raises(self):
        buf = AudioBuffer(100)
        with self.assertRaises(ValueError):
            loop_fold(buf, loop_bars=8, xf_bars=2, grid=self.grid)

    def test_output_sr_preserved(self):
        sr = 22050
        g = Grid(bpm=120.0, sr=sr)
        n_bars, xf_bars = 4, 1
        n = int(round((n_bars + xf_bars) * g.bar * sr))
        buf = AudioBuffer(n, sr=sr)
        buf.data[:] = 1.0
        looped = loop_fold(buf, loop_bars=n_bars, xf_bars=xf_bars, grid=g)
        self.assertEqual(looped.sr, sr)

    def test_fade_reduces_discontinuity(self):
        n_bars, xf_bars = 8, 2
        buf = self._make_sine_buf(n_bars, xf_bars, self.grid, freq=1.0)
        looped = loop_fold(buf, loop_bars=n_bars, xf_bars=xf_bars, grid=self.grid)
        # The XF region should have blended values (neither 0 nor original)
        xf_n = int(round(xf_bars * self.grid.bar * self.grid.sr))
        # First few samples of the loop should no longer be the raw original
        # (because the tail was mixed in)
        raw_start = buf.data[:10, 0].copy()
        looped_start = looped.data[:10, 0]
        self.assertFalse(np.allclose(raw_start, looped_start))


class TestCheckSeam(unittest.TestCase):
    def test_perfect_seam(self):
        buf = AudioBuffer.from_mono(np.zeros(1000))
        result = check_seam(buf)
        self.assertEqual(result["discontinuity"], 0.0)
        self.assertTrue(result["ok"])

    def test_bad_seam_detected(self):
        buf = AudioBuffer(100)
        buf.data[0, 0] = 1.0
        buf.data[-1, 0] = -1.0
        result = check_seam(buf, tolerance=0.05)
        self.assertGreater(result["discontinuity"], 0.5)
        self.assertFalse(result["ok"])

    def test_result_keys(self):
        buf = AudioBuffer(100)
        result = check_seam(buf)
        for key in ("start_L", "end_L", "start_R", "end_R", "discontinuity", "ok"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
