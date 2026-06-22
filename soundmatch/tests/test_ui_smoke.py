"""Tests for soundmatch.ui — offscreen construct-without-crash checks.

Each test constructs a widget under QT_QPA_PLATFORM=offscreen and feeds it
a tiny synthetic buffer, asserting no exceptions and that key signals fire.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from soundmatch.tests.fixtures import ensure_fixture


# Ensure offscreen rendering for CI
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

# Get or create QApplication (must exist before any widget is created)
_app = QApplication.instance() or QApplication([])


class TestSpectrogramWidget(unittest.TestCase):
    """Smoke test SpectrogramWidget."""

    def test_construct(self):
        from soundmatch.ui.spectrogram import SpectrogramWidget
        w = SpectrogramWidget()
        self.assertIsNotNone(w)

    def test_set_audio(self):
        from soundmatch.ui.spectrogram import SpectrogramWidget
        w = SpectrogramWidget()
        y = ensure_fixture()
        w.set_audio(y, 44100, title="Test")
        # Should not raise

    def test_clear(self):
        from soundmatch.ui.spectrogram import SpectrogramWidget
        w = SpectrogramWidget()
        w.clear()
        # Should not raise


class TestWaveformWidget(unittest.TestCase):
    """Smoke test WaveformWidget."""

    def test_construct(self):
        from soundmatch.ui.spectrogram import WaveformWidget
        w = WaveformWidget()
        self.assertIsNotNone(w)

    def test_set_audio(self):
        from soundmatch.ui.spectrogram import WaveformWidget
        w = WaveformWidget()
        y = ensure_fixture()
        w.set_audio(y, 44100)

    def test_set_selection(self):
        from soundmatch.ui.spectrogram import WaveformWidget
        w = WaveformWidget()
        y = ensure_fixture()
        w.set_audio(y, 44100)
        w.set_selection(0.5, 1.0)


class TestMetricsPanel(unittest.TestCase):
    """Smoke test MetricsPanel."""

    def test_construct(self):
        from soundmatch.ui.metrics_panel import MetricsPanel
        w = MetricsPanel()
        self.assertIsNotNone(w)

    def test_set_metrics(self):
        from inspector.metrics import characterize
        from soundmatch.ui.metrics_panel import MetricsPanel
        y = ensure_fixture()
        m = characterize(y, 44100)
        w = MetricsPanel()
        w.set_metrics(m)
        self.assertIsNotNone(w.metrics)

    def test_clear(self):
        from soundmatch.ui.metrics_panel import MetricsPanel
        w = MetricsPanel()
        w.clear()
        self.assertIsNone(w.metrics)


class TestStemsPanel(unittest.TestCase):
    """Smoke test StemsPanel."""

    def test_construct(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.stems_panel import StemsPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = StemsPanel(svc)
        self.assertIsNotNone(w)

    def test_set_stems(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.stems_panel import StemsPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = StemsPanel(svc)
        y = ensure_fixture()
        w.set_stems({"other": y, "drums": y * 0.5}, sr=44100)
        self.assertIsNotNone(w.get_stem_audio("other"))


class TestReferencePanel(unittest.TestCase):
    """Smoke test ReferencePanel."""

    def test_construct(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.reference_panel import ReferencePanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ReferencePanel(svc)
        self.assertIsNotNone(w)

    def test_selection_changed_signal(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.reference_panel import ReferencePanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ReferencePanel(svc)

        received = []
        w.selectionChanged.connect(lambda s, e: received.append((s, e)))
        w.set_selection(1.0, 5.0)
        # set_selection doesn't emit; _on_apply_selection does
        w._on_apply_selection()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], (1.0, 5.0))


class TestMainWindow(unittest.TestCase):
    """Smoke test MainWindow."""

    def test_construct(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        self.assertIsNotNone(w)
        self.assertIsNotNone(w.reference_panel)
        self.assertIsNotNone(w.stems_panel)
        self.assertIsNotNone(w.metrics_panel)

    def test_characterize_target(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        # Load synthetic audio into reference panel
        y = ensure_fixture()
        w.reference_panel._y = y
        w.reference_panel._sr = 44100
        w._characterize_target(0.0, 2.0, stem="mix")
        self.assertIsNotNone(w.metrics_panel.metrics)


class TestDrawHelpers(unittest.TestCase):
    """Test the pure-matplotlib draw_spectrogram and draw_waveform helpers."""

    def test_draw_spectrogram(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from soundmatch.ui.spectrogram import draw_spectrogram
        fig, ax = plt.subplots()
        y = ensure_fixture()
        draw_spectrogram(ax, y, 44100, title="Test Spec")
        plt.close(fig)

    def test_draw_waveform(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from soundmatch.ui.spectrogram import draw_waveform
        fig, ax = plt.subplots()
        y = ensure_fixture()
        draw_waveform(ax, y, 44100, title="Test Wave")
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
