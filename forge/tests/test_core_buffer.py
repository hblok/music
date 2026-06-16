"""Tests for forge.core.buffer.AudioBuffer."""

import unittest

import numpy as np

from forge.core.buffer import AudioBuffer


class TestAudioBufferConstruction(unittest.TestCase):
    def test_zeros_on_init(self):
        buf = AudioBuffer(1000)
        self.assertEqual(buf.data.shape, (1000, 2))
        self.assertTrue(np.all(buf.data == 0))

    def test_default_sr(self):
        self.assertEqual(AudioBuffer(100).sr, 44100)

    def test_custom_sr(self):
        self.assertEqual(AudioBuffer(100, sr=22050).sr, 22050)

    def test_from_stereo(self):
        L = np.ones(100) * 0.5
        R = np.ones(100) * 0.3
        buf = AudioBuffer.from_stereo(L, R, sr=22050)
        np.testing.assert_array_equal(buf.L, L)
        np.testing.assert_array_equal(buf.R, R)
        self.assertEqual(buf.sr, 22050)

    def test_from_stereo_length_mismatch(self):
        with self.assertRaises(ValueError):
            AudioBuffer.from_stereo(np.ones(10), np.ones(11))

    def test_from_mono(self):
        x = np.linspace(0, 1, 50)
        buf = AudioBuffer.from_mono(x)
        np.testing.assert_array_equal(buf.L, x)
        np.testing.assert_array_equal(buf.R, x)

    def test_len(self):
        self.assertEqual(len(AudioBuffer(500)), 500)

    def test_len_seconds(self):
        self.assertAlmostEqual(AudioBuffer(44100, sr=44100).len_seconds(), 1.0)


class TestAudioBufferChannels(unittest.TestCase):
    def test_L_view(self):
        buf = AudioBuffer(10)
        buf.data[:, 0] = 1.0
        np.testing.assert_array_equal(buf.L, np.ones(10))

    def test_R_view(self):
        buf = AudioBuffer(10)
        buf.data[:, 1] = 2.0
        np.testing.assert_array_equal(buf.R, np.ones(10) * 2.0)


class TestAudioBufferMetrics(unittest.TestCase):
    def setUp(self):
        self.buf = AudioBuffer.from_stereo(
            np.full(1000, 0.5), np.full(1000, -0.3)
        )

    def test_peak(self):
        self.assertAlmostEqual(self.buf.peak(), 0.5)

    def test_peak_channel(self):
        self.assertAlmostEqual(self.buf.peak_channel(0), 0.5)
        self.assertAlmostEqual(self.buf.peak_channel(1), 0.3)

    def test_rms(self):
        # all samples are ±constant → rms = sqrt(mean(L^2 + R^2) / 2) over both
        expected = float(np.sqrt(np.mean(
            np.column_stack([np.full(1000, 0.5), np.full(1000, -0.3)]) ** 2
        )))
        self.assertAlmostEqual(self.buf.rms(), expected, places=6)

    def test_rms_channel(self):
        self.assertAlmostEqual(self.buf.rms_channel(0), 0.5, places=6)
        self.assertAlmostEqual(self.buf.rms_channel(1), 0.3, places=6)

    def test_section_rms_count(self):
        self.assertEqual(len(self.buf.section_rms(8)), 8)
        self.assertEqual(len(self.buf.section_rms(4)), 4)

    def test_section_rms_uniform_signal(self):
        rms_vals = self.buf.section_rms(8)
        first = rms_vals[0]
        for v in rms_vals:
            self.assertAlmostEqual(v, first, places=5)


class TestAudioBufferNormalize(unittest.TestCase):
    def test_normalize_sets_peak(self):
        buf = AudioBuffer.from_stereo(np.full(100, 2.0), np.full(100, 1.0))
        buf.normalize(0.85)
        self.assertAlmostEqual(buf.peak(), 0.85, places=6)

    def test_normalize_returns_self(self):
        buf = AudioBuffer(100)
        buf.data[:] = 0.5
        result = buf.normalize()
        self.assertIs(result, buf)

    def test_normalize_silent_buffer_safe(self):
        buf = AudioBuffer(100)  # all zeros
        buf.normalize()  # must not raise / divide by zero
        self.assertAlmostEqual(buf.peak(), 0.0)


class TestAudioBufferAddAt(unittest.TestCase):
    def test_add_mono_at_start(self):
        buf = AudioBuffer(100)
        sig = np.ones(20) * 0.5
        buf.add_at(sig, 0.0)
        np.testing.assert_array_almost_equal(buf.L[:20], np.full(20, 0.5))
        np.testing.assert_array_almost_equal(buf.R[:20], np.full(20, 0.5))
        np.testing.assert_array_equal(buf.L[20:], np.zeros(80))

    def test_add_mono_with_gain(self):
        buf = AudioBuffer(100)
        buf.add_at(np.ones(10), 0.0, gain=2.0)
        np.testing.assert_array_almost_equal(buf.L[:10], np.full(10, 2.0))

    def test_add_at_offset(self):
        sr = 44100
        buf = AudioBuffer(sr, sr=sr)
        sig = np.ones(100)
        buf.add_at(sig, 0.5)   # 0.5 seconds = 22050 samples
        i0 = int(0.5 * sr)
        np.testing.assert_array_almost_equal(buf.L[i0 : i0 + 100], np.ones(100))
        np.testing.assert_array_equal(buf.L[:i0], np.zeros(i0))

    def test_add_bounds_clip_at_end(self):
        buf = AudioBuffer(100)
        sig = np.ones(200)
        buf.add_at(sig, 0.0, gain=1.0)  # sig longer than buf — must not raise
        np.testing.assert_array_almost_equal(buf.L, np.ones(100))

    def test_add_past_end_noop(self):
        buf = AudioBuffer(100)
        buf.add_at(np.ones(10), start_s=1000.0)  # way past end
        self.assertAlmostEqual(buf.peak(), 0.0)

    def test_add_stereo(self):
        buf = AudioBuffer(100)
        stereo = np.column_stack([np.full(50, 1.0), np.full(50, 0.5)])
        buf.add_at(stereo, 0.0)
        np.testing.assert_array_almost_equal(buf.L[:50], np.ones(50))
        np.testing.assert_array_almost_equal(buf.R[:50], np.full(50, 0.5))

    def test_accumulates(self):
        buf = AudioBuffer(100)
        buf.add_at(np.ones(10), 0.0)
        buf.add_at(np.ones(10), 0.0)
        np.testing.assert_array_almost_equal(buf.L[:10], np.full(10, 2.0))


class TestAudioBufferAddAtPan(unittest.TestCase):
    def test_center_pan(self):
        buf = AudioBuffer(100)
        buf.add_at_pan(np.ones(50), 0.0, pan=0.5)
        # constant-power at pan=0.5: L=R=cos(π/4)=sin(π/4)≈0.707
        expected = np.cos(0.5 * np.pi / 2.0)
        self.assertAlmostEqual(buf.L[0], expected, places=5)
        self.assertAlmostEqual(buf.R[0], expected, places=5)

    def test_hard_left(self):
        buf = AudioBuffer(100)
        buf.add_at_pan(np.ones(50), 0.0, pan=0.0)
        self.assertAlmostEqual(buf.L[0], 1.0, places=6)
        self.assertAlmostEqual(buf.R[0], 0.0, places=6)

    def test_hard_right(self):
        buf = AudioBuffer(100)
        buf.add_at_pan(np.ones(50), 0.0, pan=1.0)
        self.assertAlmostEqual(buf.L[0], 0.0, places=6)
        self.assertAlmostEqual(buf.R[0], 1.0, places=6)


class TestAudioBufferCopyZero(unittest.TestCase):
    def test_copy_is_independent(self):
        buf = AudioBuffer.from_mono(np.ones(100))
        c = buf.copy()
        c.data[:] = 0.0
        self.assertAlmostEqual(buf.peak(), 1.0)

    def test_zero(self):
        buf = AudioBuffer.from_mono(np.ones(100))
        buf.zero()
        self.assertAlmostEqual(buf.peak(), 0.0)


if __name__ == "__main__":
    unittest.main()
