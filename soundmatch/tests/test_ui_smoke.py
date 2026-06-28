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


class TestPatchEditor(unittest.TestCase):
    """Smoke test PatchEditor."""

    def test_construct(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        self.assertIsNotNone(w)

    def test_instrument_id(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        # Should have a valid instrument selected
        self.assertIsNotNone(w.instrument_id)
        self.assertTrue(len(w.instrument_id) > 0)

    def test_params_dict(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        params = w.params
        self.assertIsInstance(params, dict)

    def test_seed_value(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        self.assertIsInstance(w.seed, int)
        self.assertEqual(w.seed, 42)

    def test_patch_changed_signal(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        received = []

        def on_patch(inst_id, params, layers, seed):
            received.append((inst_id, params, layers, seed))

        w.patchChanged.connect(on_patch)
        # Change seed to trigger signal (debounced)
        w._seed_spin.setValue(123)
        # Process the debounce timer
        _app.processEvents()
        # The debounce timer is 300ms; we need to wait for it
        from PySide6.QtCore import QTimer
        # Force the timeout by calling the slot directly
        w._emit_patch()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][3], 123)  # seed

    def test_add_layer(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        w._on_add_layer()
        self.assertEqual(len(w.layers), 1)

    def test_remove_layer(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        w._on_add_layer()
        self.assertEqual(len(w.layers), 1)
        w._switch_to(0)  # activate the layer so _on_remove_active knows which to remove
        w._on_remove_active()
        self.assertEqual(len(w.layers), 0)

    def test_set_patch(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        w.set_patch("kick", {"f0": 60.0}, [("snare", {"tone": 0.5})], 999)
        self.assertEqual(w.seed, 999)


class TestScorecardPanel(unittest.TestCase):
    """Smoke test ScorecardPanel."""

    def test_construct(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        self.assertIsNotNone(w)

    def test_set_target_metrics(self):
        from forge.playback.service import PlaybackService
        from inspector.metrics import characterize
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        y = ensure_fixture()
        m = characterize(y, 44100)
        w.set_target_metrics(m)
        # No exception

    def test_set_scorecard(self):
        from forge.playback.service import PlaybackService
        from inspector.metrics import characterize
        from soundmatch.core.scoring import diff
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        y = ensure_fixture()
        m = characterize(y, 44100)
        # Create a scorecard from identical metrics
        sc = diff(m, m)
        w.set_scorecard(sc, cand_y=y, cand_sr=44100)
        self.assertIsNotNone(w.scorecard)
        self.assertAlmostEqual(w.scorecard.aggregate(), 0.0, places=5)

    def test_scorecard_display_values(self):
        from forge.playback.service import PlaybackService
        from inspector.metrics import characterize
        from soundmatch.core.scoring import diff
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        y = ensure_fixture()
        m = characterize(y, 44100)
        # Create a scorecard from two different metrics
        # High-freq noise has very different spectral shape
        rng = np.random.default_rng(99)
        y2 = rng.standard_normal(len(y))
        m2 = characterize(y2, 44100)
        sc = diff(m, m2)
        w.set_scorecard(sc)
        self.assertGreater(w.scorecard.aggregate(), 0.0)

    def test_clear(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        w.clear()
        self.assertIsNone(w.scorecard)

    def test_play_btn_disabled_when_no_audio(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.scorecard_panel import ScorecardPanel
        svc = PlaybackService(sr=44100, bpm=120)
        w = ScorecardPanel(svc)
        self.assertFalse(w._play_btn.isEnabled())


class TestMainWindowPatchEditor(unittest.TestCase):
    """Test MainWindow with patch editor and scorecard integration."""

    def test_has_patch_editor(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        self.assertIsNotNone(w.patch_editor)

    def test_has_scorecard_panel(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        self.assertIsNotNone(w.scorecard_panel)

    def test_patch_renders_and_scores(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        # Load synthetic audio into reference panel
        y = ensure_fixture()
        w.reference_panel._y = y
        w.reference_panel._sr = 44100
        w._characterize_target(0.0, 2.0, stem="mix")
        # Now trigger a patch change
        w._on_patch_changed("kick", {"f0": 60.0}, [], 42)
        # Scorecard should be populated
        self.assertIsNotNone(w.scorecard_panel.scorecard)


class TestABViewer(unittest.TestCase):
    """Smoke test ABViewer widget."""

    def test_construct(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        self.assertIsNotNone(w)

    def test_set_target(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        y = ensure_fixture()
        w.set_target(y, 44100)
        self.assertTrue(w._play_a_btn.isEnabled())

    def test_set_candidate(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        y = ensure_fixture()
        w.set_candidate(y, 44100)
        self.assertTrue(w._play_b_btn.isEnabled())

    def test_clear(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        y = ensure_fixture()
        w.set_target(y, 44100)
        w.set_candidate(y, 44100)
        w.clear()
        self.assertFalse(w._play_a_btn.isEnabled())
        self.assertFalse(w._play_b_btn.isEnabled())

    def test_export_montage(self):
        """Test that export_montage produces a PNG file."""
        import tempfile
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        y = ensure_fixture()
        w.set_target(y, 44100)
        w.set_candidate(y * 0.5, 44100)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test_montage.png"
            w.export_montage(p)
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 0)

    def test_current_property(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        self.assertEqual(w.current, "A")

    def test_export_enabled_when_both_set(self):
        from soundmatch.ui.ab_viewer import ABViewer
        w = ABViewer()
        y = ensure_fixture()
        self.assertFalse(w._export_btn.isEnabled())
        w.set_target(y, 44100)
        self.assertFalse(w._export_btn.isEnabled())
        w.set_candidate(y, 44100)
        self.assertTrue(w._export_btn.isEnabled())


class TestExporters(unittest.TestCase):
    """Test headless exporter functions."""

    def test_export_snippet(self):
        import tempfile
        from soundmatch.core.exporters import export_snippet
        from soundmatch.core.phrase import Phrase, Note
        phrase = Phrase(bpm=120.0, length_s=2.0, notes=[Note(t=0.0, midi=[60])])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "snippet.py"
            export_snippet(phrase, "kick", {"f0": 60.0}, [], 42, p)
            self.assertTrue(p.exists())
            content = p.read_text()
            self.assertIn("render_phrase", content)
            self.assertIn("kick", content)

    def test_export_snippet_with_layers(self):
        import tempfile
        from soundmatch.core.exporters import export_snippet
        from soundmatch.core.phrase import Phrase, Note
        phrase = Phrase(bpm=120.0, length_s=2.0, notes=[Note(t=0.0, midi=[60])])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "snippet.py"
            export_snippet(
                phrase, "synth_brass", {"f0": 60.0},
                [("snare", {"tone": 0.5})], 42, p,
            )
            content = p.read_text()
            self.assertIn("snare", content)

    def test_export_markdown(self):
        import tempfile
        from inspector.metrics import characterize
        from soundmatch.core.exporters import export_markdown
        y = ensure_fixture()
        m = characterize(y, 44100)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "report.md"
            export_markdown(m, reference="test.wav", instrument_id="synth_brass", path=p)
            self.assertTrue(p.exists())
            content = p.read_text()
            self.assertIn("Percussive Ratio", content)
            self.assertIn("Spectral Centroid", content)
            self.assertIn("test.wav", content)

    def test_export_markdown_with_scorecard(self):
        import tempfile
        from inspector.metrics import characterize
        from soundmatch.core.exporters import export_markdown
        from soundmatch.core.scoring import diff
        y = ensure_fixture()
        m = characterize(y, 44100)
        rng = np.random.default_rng(99)
        y2 = rng.standard_normal(len(y))
        m2 = characterize(y2, 44100)
        sc = diff(m, m2)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "report.md"
            export_markdown(m, cand_metrics=m2, scorecard_dict=sc.to_dict(), path=p)
            content = p.read_text()
            self.assertIn("Candidate Comparison", content)
            self.assertIn("percussive_ratio", content)

    def test_export_montage_png(self):
        import tempfile
        from soundmatch.core.exporters import export_montage_png
        y = ensure_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "montage.png"
            export_montage_png(y, 44100, y * 0.5, 44100, p)
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 0)


class TestProjectSaveLoad(unittest.TestCase):
    """Test project save/load through MainWindow."""

    def test_new_project(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        w._on_new_project()
        self.assertIsNone(w._target_metrics)

    def test_save_and_load_project(self):
        import tempfile
        from forge.playback.service import PlaybackService
        from inspector.metrics import characterize
        from soundmatch.core.phrase import seed_from_metrics
        from soundmatch.core.project import MatchProject
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)

        # Set up some target metrics
        y = ensure_fixture()
        m = characterize(y, 44100)
        w._target_metrics = m
        w._phrase = seed_from_metrics(m, bpm=138.0)

        # Save
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test_project.smatch"
            w._save_project_to(p)
            self.assertTrue(p.exists())

            # Load into a new window
            w2 = MainWindow(svc)
            proj = MatchProject.load(p)
            self.assertIsNotNone(proj.target_metrics)
            self.assertAlmostEqual(
                proj.target_metrics.percussive_ratio, m.percussive_ratio, places=1,
            )


class TestMainWindowVariantGrid(unittest.TestCase):
    """Test MainWindow variant grid integration."""

    def test_has_variant_grid(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        self.assertIsNotNone(w.variant_grid)

    def test_has_ab_viewer(self):
        from forge.playback.service import PlaybackService
        from soundmatch.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120)
        w = MainWindow(svc)
        self.assertIsNotNone(w.ab_viewer)


# --- Keep existing variant card/grid tests below ---

class TestVariantCard(unittest.TestCase):
    """Smoke test _VariantCard widget."""

    def test_construct(self):
        from soundmatch.ui.variant_grid import _VariantCard
        card = _VariantCard(name="V0", score=0.25, metrics_summary="perc=50%")
        self.assertIsNotNone(card)

    def test_construct_with_audio(self):
        from soundmatch.ui.variant_grid import _VariantCard
        y = ensure_fixture()
        card = _VariantCard(
            name="V0", score=0.1, metrics_summary="cent=440Hz",
            y=y, sr=44100,
        )
        self.assertIsNotNone(card)

    def test_promote_signal(self):
        from soundmatch.ui.variant_grid import _VariantCard
        card = _VariantCard(
            name="V0", score=0.3, metrics_summary="",
            params={"f0": 60.0}, layers=[("snare", {"tone": 0.5})],
        )
        received = []
        card.promoteRequested.connect(lambda p, l: received.append((p, l)))
        card._on_promote()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], {"f0": 60.0})
        self.assertEqual(received[0][1], [("snare", {"tone": 0.5})])


class TestVariantGrid(unittest.TestCase):
    """Smoke test VariantGrid widget."""

    def test_construct(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        self.assertIsNotNone(grid)

    def test_set_results_with_stubs(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        # Use simple namespace objects as stubs
        from types import SimpleNamespace
        stubs = [
            SimpleNamespace(name="V0", aggregate=0.15, summary="cent=440Hz",
                            params={"f0": 60.0}, layers=[]),
            SimpleNamespace(name="V1", aggregate=0.35, summary="cent=880Hz",
                            params={"f0": 120.0}, layers=[]),
            SimpleNamespace(name="V2", aggregate=0.55, summary="cent=220Hz",
                            params={"f0": 30.0}, layers=[]),
        ]
        y = ensure_fixture()
        audio_data = [(y, 44100)] * 3
        grid.set_results(stubs, audio_data=audio_data)
        self.assertEqual(len(grid._cards), 3)
        self.assertEqual(grid._count_label.text(), "3 variants")

    def test_set_results_clears_previous(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        from types import SimpleNamespace
        stubs1 = [SimpleNamespace(name="A", aggregate=0.1, summary="",
                                   params={}, layers=[])]
        stubs2 = [
            SimpleNamespace(name="B", aggregate=0.2, summary="",
                            params={}, layers=[]),
            SimpleNamespace(name="C", aggregate=0.3, summary="",
                            params={}, layers=[]),
        ]
        grid.set_results(stubs1)
        self.assertEqual(len(grid._cards), 1)
        grid.set_results(stubs2)
        self.assertEqual(len(grid._cards), 2)

    def test_sweep_requested_signal(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        received = []
        grid.sweepRequested.connect(lambda a, v: received.append((a, v)))
        # Set axis and values
        grid._axis_combo.setCurrentText("drive")
        grid._values_edit.setText("0.0, 0.5, 1.0")
        grid._on_sweep()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "drive")
        self.assertEqual(received[0][1], [0.0, 0.5, 1.0])

    def test_sweep_ignores_empty_values(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        received = []
        grid.sweepRequested.connect(lambda a, v: received.append((a, v)))
        grid._values_edit.setText("")
        grid._on_sweep()
        self.assertEqual(len(received), 0)

    def test_sweep_ignores_bad_values(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        received = []
        grid.sweepRequested.connect(lambda a, v: received.append((a, v)))
        grid._values_edit.setText("abc, def")
        grid._on_sweep()
        self.assertEqual(len(received), 0)

    def test_promote_requested_signal(self):
        from soundmatch.ui.variant_grid import VariantGrid
        grid = VariantGrid()
        from types import SimpleNamespace
        stubs = [
            SimpleNamespace(name="V0", aggregate=0.2, summary="",
                            params={"f0": 60.0}, layers=[("snare", {})]),
        ]
        grid.set_results(stubs)
        received = []
        grid.promoteRequested.connect(lambda p, l: received.append((p, l)))
        # Simulate promote from the card
        grid._cards[0]._on_promote()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], {"f0": 60.0})
        self.assertEqual(received[0][1], [("snare", {})])


class TestPatchEditorSuggest(unittest.TestCase):
    """Test PatchEditor suggest button."""

    def test_suggest_signal(self):
        from soundmatch.ui.patch_editor import PatchEditor
        w = PatchEditor()
        received = []
        w.suggestRequested.connect(lambda: received.append(True))
        # Find and click the suggest button
        suggest_btn = w.findChild(object, 'suggest-btn')
        self.assertIsNotNone(suggest_btn)
        suggest_btn.click()
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
