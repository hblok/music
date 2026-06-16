"""Tests for forge.core.dsp."""

import unittest

import numpy as np

from forge.core.dsp import (
    bandpass,
    fade,
    fft_bandpass,
    feedback_delay,
    glide_curve,
    highpass,
    lowpass,
    midi_to_hz,
    raised_cosine,
    raised_cosine_attack,
    ramp,
    sine_phase,
    slow_noise,
    warm_partials,
)


class TestMidiToHz(unittest.TestCase):
    def test_a4(self):
        self.assertAlmostEqual(midi_to_hz(69), 440.0, places=6)

    def test_a3(self):
        self.assertAlmostEqual(midi_to_hz(57), 220.0, places=6)

    def test_c4(self):
        self.assertAlmostEqual(midi_to_hz(60), 261.6255, places=3)

    def test_octave_doubles(self):
        self.assertAlmostEqual(midi_to_hz(81) / midi_to_hz(69), 2.0, places=6)


class TestRaisedCosine(unittest.TestCase):
    def test_starts_zero(self):
        w = raised_cosine(100)
        self.assertAlmostEqual(w[0], 0.0, places=6)

    def test_peak_near_middle(self):
        w = raised_cosine(100)
        # peak should be ≥0.99 somewhere near the middle
        self.assertGreater(w[50], 0.99)

    def test_ends_near_zero(self):
        w = raised_cosine(100)
        self.assertAlmostEqual(w[-1], 0.0, places=2)

    def test_length(self):
        self.assertEqual(len(raised_cosine(200)), 200)


class TestRaisedCosineAttack(unittest.TestCase):
    def test_starts_zero(self):
        self.assertAlmostEqual(raised_cosine_attack(100)[0], 0.0, places=6)

    def test_ends_one(self):
        w = raised_cosine_attack(100)
        self.assertAlmostEqual(w[-1], 1.0, places=2)

    def test_monotonic(self):
        w = raised_cosine_attack(100)
        self.assertTrue(np.all(np.diff(w) >= 0))


class TestFade(unittest.TestCase):
    def test_fade_in_starts_near_zero(self):
        sr = 44100
        x = np.ones(sr)
        fade(x, fade_in=1.0, fade_out=0.0, sr=sr)
        self.assertAlmostEqual(x[0], 0.0, places=4)
        self.assertAlmostEqual(x[-1], 1.0, places=4)

    def test_fade_out_ends_near_zero(self):
        sr = 44100
        x = np.ones(sr)
        fade(x, fade_in=0.0, fade_out=1.0, sr=sr)
        self.assertAlmostEqual(x[0], 1.0, places=4)
        self.assertAlmostEqual(x[-1], 0.0, places=4)

    def test_returns_same_array(self):
        x = np.ones(100)
        result = fade(x, 0.0, 0.0)
        self.assertIs(result, x)

    def test_zero_fades_noop(self):
        x = np.ones(100)
        fade(x, 0.0, 0.0)
        np.testing.assert_array_equal(x, np.ones(100))


class TestSlowNoise(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(42)

    def test_length(self):
        sig = slow_noise(1.0, rate_hz=5.0, rng=self.rng, sr=44100)
        self.assertEqual(len(sig), 44100)

    def test_range(self):
        sig = slow_noise(1.0, rate_hz=5.0, lo=0.2, hi=0.8, rng=self.rng)
        self.assertGreaterEqual(float(sig.min()), 0.19)
        self.assertLessEqual(float(sig.max()), 0.81)

    def test_deterministic(self):
        a = slow_noise(1.0, rate_hz=5.0, rng=np.random.default_rng(99))
        b = slow_noise(1.0, rate_hz=5.0, rng=np.random.default_rng(99))
        np.testing.assert_array_equal(a, b)

    def test_power_deepens_lulls(self):
        sig1 = slow_noise(2.0, rate_hz=3.0, power=1.0, rng=np.random.default_rng(1))
        sig2 = slow_noise(2.0, rate_hz=3.0, power=2.2, rng=np.random.default_rng(1))
        # power>1 should lower the minimum (deeper lulls)
        self.assertLessEqual(float(sig2.min()), float(sig1.min()))

    def test_default_rng_does_not_crash(self):
        sig = slow_noise(0.5, rate_hz=2.0)  # rng=None → internal default
        self.assertEqual(len(sig), int(0.5 * 44100))


class TestRamp(unittest.TestCase):
    def test_interpolates(self):
        t = np.linspace(0.0, 1.0, 100)
        r = ramp(t, [(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)])
        self.assertAlmostEqual(r[0], 0.0, places=5)
        self.assertAlmostEqual(r[50], 1.0, places=1)
        self.assertAlmostEqual(r[-1], 0.0, places=5)

    def test_single_point_constant(self):
        t = np.linspace(0.0, 1.0, 50)
        r = ramp(t, [(0.0, 0.5), (1.0, 0.5)])
        np.testing.assert_array_almost_equal(r, np.full(50, 0.5))


class TestFilters(unittest.TestCase):
    SR = 44100

    def _noise(self):
        return np.random.default_rng(0).standard_normal(self.SR)

    def test_lowpass_attenuates_high(self):
        x = np.sin(2 * np.pi * 10000 * np.arange(self.SR) / self.SR)
        y = lowpass(x, cutoff=500.0, sr=self.SR)
        # skip the initial filter transient (first ~200 samples) and check steady-state
        self.assertLess(np.max(np.abs(y[200:])), 0.01)

    def test_highpass_attenuates_low(self):
        x = np.sin(2 * np.pi * 50 * np.arange(self.SR) / self.SR)
        y = highpass(x, cutoff=5000.0, sr=self.SR)
        self.assertLess(np.max(np.abs(y[self.SR // 4:]), ), 0.01)

    def test_bandpass_preserves_passband(self):
        f = 440.0
        x = np.sin(2 * np.pi * f * np.arange(self.SR) / self.SR)
        y = bandpass(x, lo=200.0, hi=2000.0, sr=self.SR)
        # passband signal should survive mostly intact
        self.assertGreater(np.max(np.abs(y[self.SR // 4:])), 0.5)

    def test_fft_bandpass_reduces_out_of_band(self):
        x = np.random.default_rng(0).standard_normal(self.SR)
        y = fft_bandpass(x, lo=200.0, hi=2000.0, sr=self.SR)
        # out-of-band should be much quieter
        spec = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(self.SR, 1.0 / self.SR)
        out_of_band_power = np.sum(spec[freqs < 100] ** 2) + np.sum(spec[freqs > 5000] ** 2)
        in_band_power = np.sum(spec[(freqs >= 200) & (freqs <= 2000)] ** 2)
        self.assertGreater(in_band_power, out_of_band_power)


class TestGlideCurve(unittest.TestCase):
    SR = 44100

    def test_length(self):
        notes = [(69, 0.5), (72, 0.5)]
        n = self.SR
        f = glide_curve(notes, n, sr=self.SR)
        self.assertEqual(len(f), n)

    def test_converges_to_target(self):
        # a single note held for 2 seconds; the curve should be near 440 at the end
        notes = [(69, 2.0)]
        n = int(2.0 * self.SR)
        f = glide_curve(notes, n, tau=0.06, sr=self.SR)
        self.assertAlmostEqual(f[-1], 440.0, delta=1.0)

    def test_starts_at_first_frequency(self):
        notes = [(69, 1.0)]
        n = self.SR
        f = glide_curve(notes, n, tau=0.06, sr=self.SR)
        self.assertAlmostEqual(f[0], 440.0, delta=5.0)

    def test_glide_between_notes(self):
        # start at A4 (440), glide to A5 (880)
        notes = [(69, 0.1), (81, 0.5)]
        n = int(0.6 * self.SR)
        f = glide_curve(notes, n, tau=0.02, sr=self.SR)
        # near end should be close to 880
        self.assertAlmostEqual(f[-1], 880.0, delta=10.0)


class TestSinePhase(unittest.TestCase):
    def test_constant_freq_produces_correct_period(self):
        sr = 44100
        freq = 440.0
        n = sr
        phase = sine_phase(np.full(n, freq), sr=sr)
        # after 1 second at 440 Hz: phase advance = 2π×440
        self.assertAlmostEqual(phase[-1], 2 * np.pi * 440, delta=0.01)

    def test_output_length(self):
        self.assertEqual(len(sine_phase(np.ones(1000))), 1000)


class TestFeedbackDelay(unittest.TestCase):
    def test_length_preserved(self):
        x = np.zeros(44100)
        x[0] = 1.0
        y = feedback_delay(x, delay_s=0.1, feedback=0.5)
        self.assertEqual(len(y), len(x))

    def test_echo_appears_at_delay(self):
        sr = 44100
        x = np.zeros(sr)
        x[0] = 1.0
        delay_s = 0.1
        y = feedback_delay(x, delay_s=delay_s, feedback=0.5, taps=3, sr=sr)
        delay_samples = int(delay_s * sr)
        self.assertGreater(abs(y[delay_samples]), 0.4)


class TestWarmPartials(unittest.TestCase):
    def test_output_shape(self):
        phase = np.linspace(0, 2 * np.pi, 1000)
        stack = warm_partials(phase)
        self.assertEqual(stack.shape, phase.shape)

    def test_rolloff_reduces_amplitude(self):
        phase = np.linspace(0, 2 * np.pi, 1000)
        raw = warm_partials(phase, rolloff=1.0)
        warm = warm_partials(phase, rolloff=1.3)
        # warmth recipe should have lower amplitude (more rolled off)
        self.assertLess(np.max(np.abs(warm)), np.max(np.abs(raw)))

    def test_sub_mix(self):
        phase = np.linspace(0, 2 * np.pi, 1000)
        without_sub = warm_partials(phase, sub_mix=0.0)
        with_sub = warm_partials(phase, sub_mix=0.3)
        self.assertFalse(np.allclose(without_sub, with_sub))


if __name__ == "__main__":
    unittest.main()
