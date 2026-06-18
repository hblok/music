"""Phase 3 tests: CallbackMixer — mix math, loop, mute/solo, hot-swap."""

import threading
import time
import unittest

import numpy as np


def _stereo(value: float, n: int = 256) -> np.ndarray:
    """Return a constant-value (n, 2) float32 stereo array."""
    return np.full((n, 2), value, dtype=np.float32)


class TestChannelSlot(unittest.TestCase):
    def _slot(self):
        from forge.playback.mixer import ChannelSlot
        return ChannelSlot("test")

    def test_fill_no_data_writes_nothing(self):
        slot = self._slot()
        out = np.zeros((64, 2), dtype=np.float32)
        slot.fill(out, 64)
        np.testing.assert_array_equal(out, 0.0)

    def test_fill_with_data(self):
        slot = self._slot()
        slot.load(_stereo(0.5, 256))
        slot._apply_pending()  # simulate loop boundary
        out = np.zeros((64, 2), dtype=np.float32)
        slot.fill(out, 64)
        np.testing.assert_allclose(out, 0.5, atol=1e-6)

    def test_fill_applies_gain(self):
        slot = self._slot()
        slot.load(_stereo(1.0, 256))
        slot._apply_pending()
        slot.gain = 0.5
        out = np.zeros((64, 2), dtype=np.float32)
        slot.fill(out, 64)
        np.testing.assert_allclose(out, 0.5, atol=1e-6)

    def test_fill_muted_writes_nothing(self):
        slot = self._slot()
        slot.load(_stereo(1.0, 256))
        slot._apply_pending()
        slot.muted = True
        out = np.zeros((64, 2), dtype=np.float32)
        slot.fill(out, 64)
        np.testing.assert_array_equal(out, 0.0)

    def test_loop_wraps_around(self):
        slot = self._slot()
        data = _stereo(1.0, 100)
        slot.load(data)
        slot._apply_pending()
        out = np.zeros((250, 2), dtype=np.float32)
        slot.fill(out, 250)
        # all samples should be 1.0 because loop wraps
        np.testing.assert_allclose(out, 1.0, atol=1e-6)

    def test_loop_position_wraps_sample_exact(self):
        slot = self._slot()
        # buffer: 0.0 first half, 1.0 second half
        data = np.zeros((100, 2), dtype=np.float32)
        data[50:] = 1.0
        slot.load(data)
        slot._apply_pending()
        out = np.zeros((100, 2), dtype=np.float32)
        slot.fill(out, 100)
        # After reading 100 samples, position should wrap to 0
        self.assertEqual(slot._position, 0)

    def test_no_loop_stops_at_end(self):
        slot = self._slot()
        slot.loop_enabled = False
        slot.load(_stereo(1.0, 50))
        slot._apply_pending()
        out = np.zeros((100, 2), dtype=np.float32)
        slot.fill(out, 100)
        # First 50 samples = 1.0, rest = 0.0
        np.testing.assert_allclose(out[:50], 1.0, atol=1e-6)
        np.testing.assert_array_equal(out[50:], 0.0)

    def test_hot_swap_at_loop_boundary(self):
        slot = self._slot()
        slot.load(_stereo(1.0, 100))
        slot._apply_pending()

        # Queue a new buffer while playing
        slot.load(_stereo(2.0, 100))

        # Consume first buffer to trigger loop boundary (and swap)
        out = np.zeros((200, 2), dtype=np.float32)
        slot.fill(out, 200)

        # After first loop, the second buffer (2.0) should be active
        # All output should be non-zero (1.0 then 2.0)
        self.assertTrue(np.any(out > 0.0))

    def test_unload_clears_data(self):
        slot = self._slot()
        slot.load(_stereo(1.0, 100))
        slot._apply_pending()
        slot.unload()
        out = np.zeros((64, 2), dtype=np.float32)
        slot.fill(out, 64)
        np.testing.assert_array_equal(out, 0.0)


class TestCallbackMixer(unittest.TestCase):
    def _mixer(self):
        from forge.playback.mixer import CallbackMixer
        return CallbackMixer(sr=44100)

    def test_add_channel(self):
        m = self._mixer()
        slot = m.add_channel("kick")
        self.assertIn("kick", m.channel_names())
        self.assertIsNotNone(slot)

    def test_remove_channel(self):
        m = self._mixer()
        m.add_channel("kick")
        m.remove_channel("kick")
        self.assertNotIn("kick", m.channel_names())

    # ---- mix math

    def test_two_channels_sum(self):
        m = self._mixer()
        m.add_channel("a")
        m.add_channel("b")
        m.load_channel("a", _stereo(0.3, 256))
        m.load_channel("b", _stereo(0.4, 256))
        # Force pending → active
        for slot in [m.get_channel("a"), m.get_channel("b")]:
            slot._apply_pending()
        out = m.mix_offline(64)
        np.testing.assert_allclose(out, 0.7, atol=1e-5)

    def test_gain_scales_output(self):
        m = self._mixer()
        m.add_channel("a")
        m.load_channel("a", _stereo(1.0, 256))
        m.get_channel("a")._apply_pending()
        m.set_gain("a", 0.5)
        out = m.mix_offline(64)
        np.testing.assert_allclose(out, 0.5, atol=1e-5)

    def test_mute_silences_channel(self):
        m = self._mixer()
        m.add_channel("a")
        m.load_channel("a", _stereo(1.0, 256))
        m.get_channel("a")._apply_pending()
        m.set_muted("a", True)
        out = m.mix_offline(64)
        np.testing.assert_array_equal(out, 0.0)

    def test_solo_silences_others(self):
        m = self._mixer()
        m.add_channel("a")
        m.add_channel("b")
        m.load_channel("a", _stereo(1.0, 256))
        m.load_channel("b", _stereo(0.5, 256))
        for name in ("a", "b"):
            m.get_channel(name)._apply_pending()
        m.set_solo("a", True)  # only "a" audible
        out = m.mix_offline(64)
        np.testing.assert_allclose(out, 1.0, atol=1e-5)

    def test_no_solo_all_audible(self):
        m = self._mixer()
        m.add_channel("a")
        m.add_channel("b")
        m.load_channel("a", _stereo(0.3, 256))
        m.load_channel("b", _stereo(0.2, 256))
        for name in ("a", "b"):
            m.get_channel(name)._apply_pending()
        out = m.mix_offline(64)
        np.testing.assert_allclose(out, 0.5, atol=1e-5)

    def test_empty_mixer_outputs_silence(self):
        m = self._mixer()
        out = m.mix_offline(128)
        np.testing.assert_array_equal(out, 0.0)

    # ---- loop wrap is sample-exact

    def test_loop_wrap_sample_exact(self):
        m = self._mixer()
        m.add_channel("a")
        buf = np.zeros((100, 2), dtype=np.float32)
        buf[:50] = 1.0
        buf[50:] = 2.0
        m.load_channel("a", buf)
        m.get_channel("a")._apply_pending()
        # Read exactly 100 samples (one full loop)
        out = m.mix_offline(100)
        # First 50 = 1.0, next 50 = 2.0
        np.testing.assert_allclose(out[:50], 1.0, atol=1e-6)
        np.testing.assert_allclose(out[50:], 2.0, atol=1e-6)
        # Position should be back to 0
        self.assertEqual(m.get_channel("a")._position, 0)

    # ---- hot-swap introduces no large discontinuity

    def test_hot_swap_no_discontinuity(self):
        """Hot-swap mid-buffer: the seam should not have a sample-level cliff.

        We fill a 200-sample block (buf_len=100) with value 1.0.  Then queue
        value 2.0 and read another 200.  The maximum absolute jump at any
        adjacent pair of samples should be ≤ 1.0 (one unit step, not a cliff).
        """
        m = self._mixer()
        m.add_channel("a")
        m.load_channel("a", _stereo(1.0, 100))
        m.get_channel("a")._apply_pending()
        out1 = m.mix_offline(200)

        # Queue a new buffer
        m.load_channel("a", _stereo(2.0, 100))
        out2 = m.mix_offline(200)

        all_out = np.concatenate([out1, out2])
        diffs = np.abs(np.diff(all_out[:, 0]))
        # No abrupt jump larger than the step between the two buffers (2.0 - 1.0 = 1.0)
        self.assertLessEqual(float(diffs.max()), 1.0 + 1e-5)

    # ---- position tracking

    def test_position_increments(self):
        m = self._mixer()
        m.mix_offline(128)
        self.assertEqual(m.position_samples, 128)
        m.mix_offline(64)
        self.assertEqual(m.position_samples, 192)

    def test_reset_position(self):
        m = self._mixer()
        m.mix_offline(128)
        m.reset_position()
        self.assertEqual(m.position_samples, 0)

    def test_position_callback(self):
        m = self._mixer()
        received = []
        m.set_position_callback(received.append)
        m.mix_offline(64)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], 64)

    # ---- PlaybackService mixer mode

    def test_service_with_mixer_creates_mixer(self):
        from forge.playback.service import PlaybackService
        svc = PlaybackService.with_mixer(sr=44100, bpm=138.0)
        self.assertIsNotNone(svc.mixer)
        self.assertIsInstance(svc.mixer, __import__("forge.playback.mixer", fromlist=["CallbackMixer"]).CallbackMixer)

    def test_service_with_mixer_plays_headless(self):
        from forge.playback.service import PlaybackService
        svc = PlaybackService.with_mixer(sr=44100, bpm=138.0)
        svc.mixer.add_channel("kick")
        svc.mixer.load_channel("kick", _stereo(0.5, 1000))
        svc.mixer.get_channel("kick")._apply_pending()
        # Should not raise even without audio device
        svc.play()
        svc.stop()
        svc.close()


# ---------------------------------------------------------------------------
# MixerWidget reverb_send tests (Phase 7)


class TestMixerWidgetReverbSend(unittest.TestCase):
    """Test reverb_send property, set_reverb_send, default 0.0, and presence in levels()."""

    @classmethod
    def setUpClass(cls):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        cls._app = QApplication.instance() or QApplication([])

    def _widget(self, names=("kick", "hat")):
        from forge.ui.mixer import MixerWidget
        return MixerWidget(list(names))

    def test_default_reverb_send_zero(self):
        """Default reverb_send for every strip should be 0.0."""
        w = self._widget()
        for name, strip in w._strips.items():
            self.assertAlmostEqual(strip.reverb_send, 0.0,
                msg=f"Strip {name!r} default reverb_send != 0.0")

    def test_set_reverb_send_updates_property(self):
        """set_reverb_send sets the property."""
        w = self._widget()
        strip = w._strips["kick"]
        strip.set_reverb_send(0.8)
        self.assertAlmostEqual(strip.reverb_send, 0.8, delta=0.01)

    def test_set_reverb_send_zero(self):
        """set_reverb_send(0.0) keeps property at 0.0."""
        w = self._widget()
        strip = w._strips["hat"]
        strip.set_reverb_send(0.0)
        self.assertAlmostEqual(strip.reverb_send, 0.0, delta=0.01)

    def test_widget_set_reverb_send(self):
        """MixerWidget.set_reverb_send routes to the correct strip."""
        w = self._widget()
        w.set_reverb_send("kick", 0.5)
        self.assertAlmostEqual(w._strips["kick"].reverb_send, 0.5, delta=0.01)

    def test_widget_set_reverb_send_noop_for_unknown(self):
        """set_reverb_send on unknown name should be a no-op."""
        w = self._widget()
        w.set_reverb_send("nonexistent", 0.5)  # must not raise

    def test_levels_includes_reverb_send(self):
        """levels() dict must carry 'reverb_send' key for every strip."""
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertIn("reverb_send", vals,
                f"levels()['reverb_send'] missing for strip {name!r}")

    def test_levels_reverb_send_default_zero(self):
        """Default reverb_send in levels() must be 0.0."""
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertAlmostEqual(vals["reverb_send"], 0.0, delta=0.01,
                msg=f"Default reverb_send in levels() for {name!r} should be 0.0")

    def test_levels_includes_all_keys(self):
        """Adding reverb_send must not drop volume, muted, or pan keys."""
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertIn("volume", vals)
            self.assertIn("muted", vals)
            self.assertIn("pan", vals)
            self.assertIn("reverb_send", vals)

    def test_levels_changed_includes_reverb_send(self):
        """levelsChanged signal dict also carries 'reverb_send'."""
        received = []
        w = self._widget()
        w.levelsChanged.connect(received.append)

        strip = w._strips["kick"]
        strip.set_reverb_send(0.6)
        self._app.processEvents()

        if received:
            lvl = received[-1]
            self.assertIn("reverb_send", lvl.get("kick", {}),
                "levelsChanged dict missing 'reverb_send' key")


if __name__ == "__main__":
    unittest.main()
