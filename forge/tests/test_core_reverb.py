"""Tests for forge.core.reverb."""

import unittest

import numpy as np

from forge.core.reverb import make_reverb_ir, make_stereo_ir_pair, reverb, reverb_stereo


class TestMakeReverbIr(unittest.TestCase):
    SR = 44100

    def test_length(self):
        ir = make_reverb_ir(2.0, 1.0, seed=7, sr=self.SR)
        self.assertEqual(len(ir), int(2.0 * self.SR))

    def test_energy_normalized(self):
        ir = make_reverb_ir(2.0, 1.0, seed=7, sr=self.SR)
        energy = float(np.sqrt(np.sum(ir ** 2)))
        self.assertAlmostEqual(energy, 1.0, places=5)

    def test_deterministic(self):
        ir1 = make_reverb_ir(2.0, 1.0, seed=7)
        ir2 = make_reverb_ir(2.0, 1.0, seed=7)
        np.testing.assert_array_equal(ir1, ir2)

    def test_different_seeds_differ(self):
        ir_L = make_reverb_ir(2.0, 1.0, seed=7)
        ir_R = make_reverb_ir(2.0, 1.0, seed=11)
        self.assertFalse(np.array_equal(ir_L, ir_R))

    def test_decays_over_time(self):
        ir = make_reverb_ir(3.0, 0.5, seed=42)
        # RMS of first 0.1 s should exceed RMS of last 0.1 s
        n10 = int(0.1 * 44100)
        rms_early = np.sqrt(np.mean(ir[:n10] ** 2))
        rms_late = np.sqrt(np.mean(ir[-n10:] ** 2))
        self.assertGreater(rms_early, rms_late * 2)

    def test_low_frequency_content(self):
        ir = make_reverb_ir(2.0, 1.0, seed=7)
        spec = np.abs(np.fft.rfft(ir))
        freqs = np.fft.rfftfreq(len(ir), 1.0 / 44100)
        high = np.mean(spec[freqs > 8000])
        low = np.mean(spec[freqs < 2000])
        # dark IR: low freqs should dominate
        self.assertGreater(low, high)


class TestReverb(unittest.TestCase):
    SR = 44100

    def setUp(self):
        self.ir = make_reverb_ir(1.0, 0.5, seed=7, sr=self.SR)

    def test_output_length_matches_input(self):
        x = np.random.default_rng(0).standard_normal(self.SR)
        y = reverb(x, self.ir)
        self.assertEqual(len(y), len(x))

    def test_dry_pass(self):
        x = np.random.default_rng(0).standard_normal(self.SR)
        y = reverb(x, self.ir, wet=0.0)
        np.testing.assert_array_almost_equal(y, x)

    def test_wet_differs_from_dry(self):
        x = np.zeros(self.SR)
        x[100] = 1.0  # impulse
        y = reverb(x, self.ir, wet=0.8)
        # wet output should have energy after the impulse
        self.assertGreater(np.sum(y[101:500] ** 2), 0.001)

    def test_wet_does_not_exceed_dry_peak_much(self):
        x = np.random.default_rng(5).standard_normal(self.SR)
        y = reverb(x, self.ir, wet=0.5)
        # The renorm step prevents wet from wildly exceeding dry
        self.assertLess(np.max(np.abs(y)), np.max(np.abs(x)) * 3.0)


class TestReverbStereo(unittest.TestCase):
    SR = 44100

    def test_returns_two_arrays(self):
        ir_L = make_reverb_ir(0.5, 0.3, seed=7, sr=self.SR)
        ir_R = make_reverb_ir(0.5, 0.3, seed=11, sr=self.SR)
        L = np.random.default_rng(0).standard_normal(self.SR)
        R = np.random.default_rng(1).standard_normal(self.SR)
        out_L, out_R = reverb_stereo(L, R, ir_L, ir_R, wet=0.5)
        self.assertEqual(len(out_L), self.SR)
        self.assertEqual(len(out_R), self.SR)

    def test_L_R_differ(self):
        ir_L = make_reverb_ir(0.5, 0.3, seed=7)
        ir_R = make_reverb_ir(0.5, 0.3, seed=11)
        mono = np.zeros(self.SR)
        mono[0] = 1.0
        out_L, out_R = reverb_stereo(mono, mono, ir_L, ir_R, wet=0.8)
        self.assertFalse(np.array_equal(out_L, out_R))


class TestMakeStereoIrPair(unittest.TestCase):
    def test_default_seeds(self):
        ir_L, ir_R = make_stereo_ir_pair(1.0, 0.5)
        self.assertFalse(np.array_equal(ir_L, ir_R))

    def test_deterministic(self):
        a_L, a_R = make_stereo_ir_pair(1.0, 0.5, seed_L=7, seed_R=11)
        b_L, b_R = make_stereo_ir_pair(1.0, 0.5, seed_L=7, seed_R=11)
        np.testing.assert_array_equal(a_L, b_L)
        np.testing.assert_array_equal(a_R, b_R)


if __name__ == "__main__":
    unittest.main()
