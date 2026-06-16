"""Phase 7 tests: playback clock, service, and Qt window (offscreen)."""

import os
import sys
import unittest

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from forge.playback.clock import PlaybackClock
from forge.playback.service import PlaybackService

# Run Qt with the offscreen platform so tests work headless.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ---------------------------------------------------------------------------
# PlaybackClock

class TestPlaybackClock(unittest.TestCase):
    def test_initial_state(self):
        c = PlaybackClock(bpm=138.0)
        self.assertEqual(c.position_samples, 0)
        self.assertFalse(c.is_playing)

    def test_play_sets_playing(self):
        c = PlaybackClock()
        c.play()
        self.assertTrue(c.is_playing)

    def test_pause_stops_playing(self):
        c = PlaybackClock()
        c.play()
        c.pause()
        self.assertFalse(c.is_playing)

    def test_stop_resets_position(self):
        c = PlaybackClock(sr=44100)
        c.play()
        c.advance(1000)
        c.stop()
        self.assertEqual(c.position_samples, 0)
        self.assertFalse(c.is_playing)

    def test_advance_increments_when_playing(self):
        c = PlaybackClock(sr=44100)
        c.play()
        c.advance(512)
        self.assertEqual(c.position_samples, 512)

    def test_advance_no_change_when_paused(self):
        c = PlaybackClock(sr=44100)
        c.advance(512)
        self.assertEqual(c.position_samples, 0)

    def test_seek(self):
        c = PlaybackClock(sr=44100)
        c.seek(10000)
        self.assertEqual(c.position_samples, 10000)

    def test_position_seconds(self):
        c = PlaybackClock(sr=44100)
        c.seek(44100)
        self.assertAlmostEqual(c.position_seconds, 1.0)

    def test_position_bars(self):
        c = PlaybackClock(bpm=60.0, sr=44100)
        # 1 bar at 60 BPM = 4 beats = 4 seconds = 176400 samples
        c.seek(44100 * 4)
        self.assertAlmostEqual(c.position_bars, 1.0)

    def test_bar_beat_string_format(self):
        c = PlaybackClock(bpm=120.0, sr=44100)
        s = c.bar_beat_string()
        self.assertIn(":", s)


# ---------------------------------------------------------------------------
# PlaybackService (no real audio device needed for logic tests)

class TestPlaybackService(unittest.TestCase):
    def _buf(self, duration=1.0, sr=44100):
        n = int(duration * sr)
        sig = 0.5 * np.sin(2.0 * np.pi * 440.0 * np.arange(n) / sr)
        return AudioBuffer.from_mono(sig, sr=sr)

    def test_initial_not_playing(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        self.assertFalse(svc.is_playing)

    def test_play_sets_playing(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.play()
        self.assertTrue(svc.is_playing)
        svc.stop()
        svc.close()

    def test_pause(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.play()
        svc.pause()
        self.assertFalse(svc.is_playing)
        svc.close()

    def test_stop_resets_position(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.load(self._buf())
        svc.play()
        svc.stop()
        self.assertAlmostEqual(svc.position_seconds, 0.0)
        svc.close()

    def test_load_replaces_buffer(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.load(self._buf())
        svc.load(self._buf(duration=2.0))
        svc.close()

    def test_callback_fills_silence_when_not_playing(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.load(self._buf())
        out = np.ones((512, 2), dtype=np.float32)
        svc._callback(out, 512, None, None)
        np.testing.assert_array_equal(out, np.zeros_like(out))
        svc.close()

    def test_callback_fills_audio_when_playing(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        buf = self._buf()
        svc.load(buf)
        svc.play()
        out = np.zeros((512, 2), dtype=np.float32)
        svc._callback(out, 512, None, None)
        self.assertGreater(np.max(np.abs(out)), 0)
        svc.stop()
        svc.close()

    def test_callback_stops_at_end(self):
        sr = 44100
        svc = PlaybackService(sr=sr, bpm=120.0)
        buf = self._buf(duration=0.01)  # very short
        svc.load(buf)
        svc.play()
        # advance past end
        svc.clock.seek(len(buf))
        out = np.ones((512, 2), dtype=np.float32)
        svc._callback(out, 512, None, None)
        np.testing.assert_array_equal(out, np.zeros_like(out))
        self.assertFalse(svc.is_playing)
        svc.close()

    def test_position_bars(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        svc.seek_bar(2.0)
        self.assertAlmostEqual(svc.position_bars, 2.0, delta=0.01)
        svc.close()

    def test_bar_beat_string(self):
        svc = PlaybackService(sr=44100, bpm=120.0)
        s = svc.bar_beat_string
        self.assertIn(":", s)
        svc.close()


# ---------------------------------------------------------------------------
# Qt window tests (offscreen)

class TestQtWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_window_creates(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120.0)
        win = MainWindow(svc)
        win.show()
        self.assertTrue(win.isVisible())
        win.close()
        svc.close()

    def test_transport_widget_creates(self):
        from forge.playback.service import PlaybackService
        from forge.ui.transport import TransportWidget
        svc = PlaybackService(sr=44100, bpm=120.0)
        tw = TransportWidget(svc)
        tw.show()
        self.assertTrue(tw.isVisible())
        tw.close()
        svc.close()

    def test_window_title(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120.0)
        win = MainWindow(svc)
        self.assertIn("Forge", win.windowTitle())
        win.close()
        svc.close()

    def test_transport_set_total_bars(self):
        from forge.playback.service import PlaybackService
        from forge.ui.transport import TransportWidget
        svc = PlaybackService(sr=44100, bpm=120.0)
        tw = TransportWidget(svc)
        tw.set_total_bars(32.0)
        self.assertAlmostEqual(tw._slider_total_bars, 32.0)
        svc.close()


if __name__ == "__main__":
    unittest.main()
