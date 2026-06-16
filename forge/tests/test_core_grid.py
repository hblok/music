"""Tests for forge.core.grid.Grid."""

import unittest

from forge.core.grid import Grid


class TestGridBasicProperties(unittest.TestCase):
    def setUp(self):
        self.g = Grid(bpm=120.0)  # BEAT=0.5s, BAR=2s, STEP=0.125s

    def test_beat(self):
        self.assertAlmostEqual(self.g.beat, 0.5)

    def test_bar(self):
        self.assertAlmostEqual(self.g.bar, 2.0)

    def test_step(self):
        self.assertAlmostEqual(self.g.step, 0.125)

    def test_invalid_bpm(self):
        with self.assertRaises(ValueError):
            Grid(bpm=0)
        with self.assertRaises(ValueError):
            Grid(bpm=-10)


class TestGridBarT(unittest.TestCase):
    def setUp(self):
        self.g = Grid(bpm=120.0)  # bar=2s, beat=0.5s

    def test_bar_zero(self):
        self.assertAlmostEqual(self.g.bar_t(0), 0.0)

    def test_bar_one(self):
        self.assertAlmostEqual(self.g.bar_t(1), 2.0)

    def test_bar_beat_offset(self):
        # bar=1, beat=2 → 1*2 + 2*0.5 = 3.0
        self.assertAlmostEqual(self.g.bar_t(1, beat=2.0), 3.0)

    def test_grid0_offset(self):
        g = Grid(bpm=120.0, grid0=0.5)
        self.assertAlmostEqual(g.bar_t(0), 0.5)
        self.assertAlmostEqual(g.bar_t(1), 2.5)

    def test_fractional_bar(self):
        # bar=0.5 at 120 BPM → 1.0s
        self.assertAlmostEqual(self.g.bar_t(0.5), 1.0)

    def test_matches_legacy_formula(self):
        """Verify bar_t matches the legacy `(b*4 + beat) * BEAT` formula."""
        BPM = 104.0
        BEAT = 60.0 / BPM
        g = Grid(bpm=BPM)
        for b in range(10):
            for beat in (0.0, 1.0, 2.0, 3.0):
                expected = (b * 4 + beat) * BEAT
                self.assertAlmostEqual(g.bar_t(b, beat), expected, places=10)


class TestGridStepT(unittest.TestCase):
    def setUp(self):
        self.g = Grid(bpm=120.0)  # step=0.125s

    def test_step_zero(self):
        self.assertAlmostEqual(self.g.step_t(0, 0), 0.0)

    def test_step_one_step(self):
        self.assertAlmostEqual(self.g.step_t(0, 1), 0.125)

    def test_step_16_steps_equals_one_bar(self):
        self.assertAlmostEqual(self.g.step_t(0, 16), self.g.bar)


class TestGridSamples(unittest.TestCase):
    def setUp(self):
        self.g = Grid(bpm=120.0, sr=44100)

    def test_bar_samples_integer(self):
        samples = self.g.bar_samples(1)
        self.assertIsInstance(samples, int)
        # 2 seconds at 44100 = 88200
        self.assertEqual(samples, 88200)

    def test_step_samples(self):
        # step = 0.125s × 44100 = 5512.5 → floor = 5512
        self.assertEqual(self.g.step_samples(0, 1), int(0.125 * 44100))


class TestGridConversions(unittest.TestCase):
    def setUp(self):
        self.g = Grid(bpm=120.0)

    def test_seconds_to_bar_roundtrip(self):
        for b in (0, 1, 4, 16):
            t = self.g.bar_t(b)
            self.assertAlmostEqual(self.g.seconds_to_bar(t), float(b))

    def test_seconds_to_beat_roundtrip(self):
        for beat in (0, 4, 8, 16):
            t = self.g.bar_t(0, beat)
            self.assertAlmostEqual(self.g.seconds_to_beat(t), float(beat))

    def test_duration_bars(self):
        self.assertAlmostEqual(self.g.duration_bars(self.g.bar * 8), 8.0)

    def test_n_samples(self):
        # 4 bars × 2s × 44100 = 352800
        self.assertEqual(self.g.n_samples(4), 352800)


class TestGridTimeVector(unittest.TestCase):
    def test_starts_at_zero(self):
        g = Grid(120.0, sr=44100)
        t = g.time_vector(100)
        self.assertAlmostEqual(t[0], 0.0)

    def test_step_equals_1_over_sr(self):
        sr = 44100
        g = Grid(120.0, sr=sr)
        t = g.time_vector(100)
        self.assertAlmostEqual(t[1] - t[0], 1.0 / sr)

    def test_length(self):
        g = Grid(120.0)
        self.assertEqual(len(g.time_vector(500)), 500)


if __name__ == "__main__":
    unittest.main()
