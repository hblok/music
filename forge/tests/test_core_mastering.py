"""Tests for forge.core.mastering."""

import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.mastering import master, soft_limiter, write_wav


class TestSoftLimiter(unittest.TestCase):
    def test_below_threshold_unchanged(self):
        x = np.full(100, 0.5)
        y = soft_limiter(x, threshold=0.95)
        np.testing.assert_array_almost_equal(y, x)

    def test_above_threshold_clamped(self):
        x = np.full(100, 2.0)
        y = soft_limiter(x, threshold=0.95)
        self.assertLess(float(np.max(y)), 1.01)
        self.assertGreater(float(np.min(y)), 0.94)

    def test_preserves_sign(self):
        x = np.array([2.0, -2.0])
        y = soft_limiter(x, threshold=0.95)
        self.assertGreater(y[0], 0)
        self.assertLess(y[1], 0)

    def test_input_not_modified(self):
        x = np.full(100, 2.0)
        x_orig = x.copy()
        soft_limiter(x)
        np.testing.assert_array_equal(x, x_orig)


class TestMaster(unittest.TestCase):
    def _make_buf(self, amplitude=0.5, n=44100):
        buf = AudioBuffer(n)
        buf.data[:] = amplitude
        return buf

    def test_normalizes_to_target(self):
        buf = self._make_buf(amplitude=2.0)
        out = master(buf, target=0.85, fade_in_s=0.0, fade_out_s=0.0, limit=False)
        self.assertAlmostEqual(out.peak(), 0.85, places=5)

    def test_does_not_modify_input(self):
        buf = self._make_buf(amplitude=2.0)
        _ = master(buf, target=0.85)
        self.assertAlmostEqual(buf.peak(), 2.0, places=5)

    def test_returns_new_buffer(self):
        buf = self._make_buf()
        out = master(buf)
        self.assertIsNot(out, buf)

    def test_limiter_keeps_below_one(self):
        buf = self._make_buf(amplitude=1.5)
        # don't normalize first, just limit
        out = master(buf, target=1.0, limit=True, limit_threshold=0.95)
        self.assertLessEqual(out.peak(), 1.01)

    def test_fade_in_reduces_start(self):
        sr = 44100
        buf = AudioBuffer(sr, sr=sr)
        buf.data[:] = 1.0
        out = master(buf, target=1.0, fade_in_s=0.5, fade_out_s=0.0, limit=False)
        self.assertAlmostEqual(float(out.L[0]), 0.0, places=3)
        self.assertAlmostEqual(float(out.L[-1]), 1.0, places=3)


class TestWriteWav(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _make_sine_buf(self, sr=44100, freq=440.0, duration=1.0):
        n = int(sr * duration)
        t = np.arange(n) / sr
        sig = np.sin(2 * np.pi * freq * t) * 0.5
        return AudioBuffer.from_stereo(sig, sig, sr=sr)

    def test_file_created(self):
        buf = self._make_sine_buf()
        path = self.tmp / "out.wav"
        write_wav(buf, path)
        self.assertTrue(path.exists())

    def test_wav_properties(self):
        sr = 44100
        buf = self._make_sine_buf(sr=sr)
        path = self.tmp / "out.wav"
        write_wav(buf, path)
        with wave.open(str(path), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 2)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), sr)
            self.assertEqual(wf.getnframes(), int(sr * 1.0))

    def test_creates_parent_dirs(self):
        buf = self._make_sine_buf()
        deep = self.tmp / "a" / "b" / "c" / "out.wav"
        write_wav(buf, deep)
        self.assertTrue(deep.exists())

    def test_normalize_flag(self):
        buf = AudioBuffer(1000)
        buf.data[:] = 0.1  # low level
        path = self.tmp / "norm.wav"
        write_wav(buf, path, normalize=True, target=0.85)
        # read back and check peak
        import wave as wv
        import numpy as nnp
        with wv.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            data = nnp.frombuffer(raw, dtype=nnp.int16).astype(nnp.float64) / 32768.0
        self.assertAlmostEqual(float(nnp.max(nnp.abs(data))), 0.85, delta=0.01)

    def test_no_normalize(self):
        buf = AudioBuffer(1000)
        buf.data[:] = 0.3
        path = self.tmp / "nonorm.wav"
        write_wav(buf, path, normalize=False)
        import wave as wv
        import numpy as nnp
        with wv.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            data = nnp.frombuffer(raw, dtype=nnp.int16).astype(nnp.float64) / 32768.0
        # peak should be ≈ 0.3 (not normalized)
        self.assertAlmostEqual(float(nnp.max(nnp.abs(data))), 0.3, delta=0.01)


if __name__ == "__main__":
    unittest.main()
