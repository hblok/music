"""Tests for forge.core.mixbus.MixBus."""

import unittest

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.mixbus import MixBus


class TestMixBusBasic(unittest.TestCase):
    def test_empty_render_is_zeros(self):
        bus = MixBus(1000)
        buf = bus.render()
        self.assertAlmostEqual(buf.peak(), 0.0)
        self.assertEqual(len(buf), 1000)

    def test_n_layers_starts_at_zero(self):
        bus = MixBus(100)
        self.assertEqual(bus.n_layers, 0)

    def test_n_layers_increments(self):
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), 1.0)
        self.assertEqual(bus.n_layers, 1)
        bus.commit(np.ones(100), np.ones(100), 0.5)
        self.assertEqual(bus.n_layers, 2)

    def test_sr_propagates_to_render(self):
        bus = MixBus(100, sr=22050)
        self.assertEqual(bus.render().sr, 22050)


class TestMixBusCommit(unittest.TestCase):
    def test_single_layer_normalized(self):
        """A layer with peak=2.0 and weight=1.0 → rendered peak=1.0."""
        bus = MixBus(100)
        L = np.full(100, 2.0)
        R = np.full(100, -2.0)
        bus.commit(L, R, weight=1.0)
        buf = bus.render()
        self.assertAlmostEqual(buf.peak(), 1.0, places=6)

    def test_weight_scales_mix(self):
        """Two equal layers with weights 0.3 and 0.7 → mix sums correctly."""
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), weight=0.3)
        bus.commit(np.ones(100), np.ones(100), weight=0.7)
        buf = bus.render()
        # Each layer has peak=1.0; after norm×weight: 0.3 + 0.7 = 1.0
        np.testing.assert_array_almost_equal(buf.L, np.ones(100), decimal=6)

    def test_two_equal_layers_equal_weights(self):
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), weight=0.5)
        bus.commit(np.ones(100), np.ones(100), weight=0.5)
        buf = bus.render()
        np.testing.assert_array_almost_equal(buf.L, np.ones(100), decimal=6)

    def test_env_applied_before_normalization(self):
        """Env zeros out second half → only first-half contributes to peak."""
        bus = MixBus(100)
        L = np.ones(100)
        R = np.ones(100)
        env = np.concatenate([np.ones(50), np.zeros(50)])
        bus.commit(L, R, weight=1.0, env=env)
        buf = bus.render()
        np.testing.assert_array_almost_equal(buf.L[50:], np.zeros(50), decimal=6)
        np.testing.assert_array_almost_equal(buf.L[:50], np.ones(50), decimal=6)

    def test_shorter_layer_handled(self):
        """A layer shorter than the bus fills only its portion."""
        bus = MixBus(200)
        bus.commit(np.ones(100), np.ones(100), weight=1.0)
        buf = bus.render()
        # first 100 samples filled, rest zeros
        np.testing.assert_array_almost_equal(buf.L[:100], np.ones(100), decimal=6)
        np.testing.assert_array_almost_equal(buf.L[100:], np.zeros(100), decimal=6)

    def test_near_silent_layer_safe(self):
        """Committing a near-zero layer must not raise (1e-12 floor on peak)."""
        bus = MixBus(100)
        bus.commit(np.zeros(100), np.zeros(100), weight=1.0)  # should not raise


class TestMixBusCommitBuffer(unittest.TestCase):
    def test_commit_buffer(self):
        bus = MixBus(100)
        buf_in = AudioBuffer.from_mono(np.ones(100))
        bus.commit_buffer(buf_in, weight=1.0)
        buf_out = bus.render()
        np.testing.assert_array_almost_equal(buf_out.L, np.ones(100), decimal=6)


class TestMixBusRenderPeak(unittest.TestCase):
    def test_render_peak_empty(self):
        self.assertAlmostEqual(MixBus(100).render_peak(), 0.0)

    def test_render_peak_after_commit(self):
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), weight=0.5)
        self.assertAlmostEqual(bus.render_peak(), 0.5, places=6)


class TestMixBusReset(unittest.TestCase):
    def test_reset_clears_layers(self):
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), weight=1.0)
        bus.reset()
        self.assertEqual(bus.n_layers, 0)
        self.assertAlmostEqual(bus.render().peak(), 0.0)

    def test_render_returns_copy(self):
        """Calling render() twice returns independent copies."""
        bus = MixBus(100)
        bus.commit(np.ones(100), np.ones(100), weight=1.0)
        buf1 = bus.render()
        buf2 = bus.render()
        buf1.data[:] = 0.0
        self.assertAlmostEqual(buf2.peak(), 1.0)


if __name__ == "__main__":
    unittest.main()
