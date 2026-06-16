"""Phase 8 tests: instrument panel, mixer, pattern editor (offscreen Qt)."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestInstrumentPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _kick_schemas(self):
        from forge import control
        instruments = {e["id"]: e for e in control.list_instruments()}
        return instruments["kick"]["params"]

    def test_panel_creates(self):
        from forge.ui.instrument_panel import InstrumentPanel
        panel = InstrumentPanel("kick", self._kick_schemas())
        panel.show()
        self.assertTrue(panel.isVisible())
        panel.close()

    def test_panel_has_controls(self):
        from forge.ui.instrument_panel import InstrumentPanel
        schemas = self._kick_schemas()
        panel = InstrumentPanel("kick", schemas)
        self.assertEqual(len(panel._controls), len(schemas))

    def test_current_params_returns_dict(self):
        from forge.ui.instrument_panel import InstrumentPanel
        panel = InstrumentPanel("kick", self._kick_schemas())
        p = panel.current_params()
        self.assertIsInstance(p, dict)
        self.assertGreater(len(p), 0)

    def test_current_params_has_all_schema_names(self):
        from forge.ui.instrument_panel import InstrumentPanel
        schemas = self._kick_schemas()
        panel = InstrumentPanel("kick", schemas)
        p = panel.current_params()
        for s in schemas:
            self.assertIn(s["name"], p)

    def test_params_changed_signal_emits(self):
        from forge.ui.instrument_panel import InstrumentPanel
        received = []
        panel = InstrumentPanel("kick", self._kick_schemas())
        panel.paramsChanged.connect(received.append)
        panel._emit()
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], dict)

    def test_from_registry(self):
        from forge.ui.instrument_panel import InstrumentPanel
        panel = InstrumentPanel.from_registry("hat")
        p = panel.current_params()
        self.assertIn("open_", p)
        panel.close()

    def test_bool_schema_creates_checkbox(self):
        from PySide6.QtWidgets import QCheckBox
        from forge.ui.instrument_panel import InstrumentPanel
        bool_schemas = [{"name": "flag", "kind": "bool", "default": False}]
        panel = InstrumentPanel("test", bool_schemas)
        self.assertIsInstance(panel._controls["flag"], QCheckBox)

    def test_int_schema_creates_spinbox(self):
        from PySide6.QtWidgets import QSpinBox
        from forge.ui.instrument_panel import InstrumentPanel
        int_schemas = [{"name": "midi", "kind": "int", "default": 60,
                        "lo": 0, "hi": 127}]
        panel = InstrumentPanel("test", int_schemas)
        self.assertIsInstance(panel._controls["midi"], QSpinBox)


class TestMixerWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_mixer_creates(self):
        from forge.ui.mixer import MixerWidget
        mx = MixerWidget(["kick", "hat", "bass"])
        mx.show()
        self.assertEqual(len(mx._strips), 3)
        mx.close()

    def test_levels_returns_dict(self):
        from forge.ui.mixer import MixerWidget
        mx = MixerWidget(["kick", "hat"])
        lvls = mx.levels()
        self.assertIn("kick", lvls)
        self.assertIn("volume", lvls["kick"])
        self.assertIn("muted", lvls["kick"])

    def test_set_volume(self):
        from forge.ui.mixer import MixerWidget
        mx = MixerWidget(["bass"])
        mx.set_volume("bass", 0.5)
        self.assertAlmostEqual(mx.levels()["bass"]["volume"], 0.5, delta=0.01)

    def test_mute_default_false(self):
        from forge.ui.mixer import MixerWidget
        mx = MixerWidget(["kick"])
        self.assertFalse(mx.levels()["kick"]["muted"])

    def test_levels_changed_signal(self):
        from forge.ui.mixer import MixerWidget
        received = []
        mx = MixerWidget(["kick"])
        mx.levelsChanged.connect(received.append)
        mx._emit()
        self.assertEqual(len(received), 1)


class TestPatternEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_editor_creates(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor(bpm=138.0, length_bars=4)
        ed.show()
        self.assertTrue(ed.isVisible())
        ed.close()

    def test_add_row(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor()
        self.assertEqual(len(ed._rows), 0)
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        self.assertEqual(len(ed._rows), 1)

    def test_to_pattern_spec_empty(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor(bpm=140.0, length_bars=2)
        spec = ed.to_pattern_spec()
        self.assertAlmostEqual(spec["bpm"], 140.0)
        self.assertEqual(spec["length_bars"], 2)
        self.assertEqual(spec["tracks"], [])

    def test_to_pattern_spec_with_row(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor(bpm=138.0, length_bars=4)
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        # toggle step 0
        ed._rows[0]._buttons[0].setChecked(True)
        spec = ed.to_pattern_spec()
        self.assertEqual(len(spec["tracks"]), 1)
        self.assertEqual(spec["tracks"][0]["instrument"], "kick")
        self.assertEqual(spec["tracks"][0]["steps"][0], 1)

    def test_clear_all(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor()
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        ed._add_row()
        ed._clear_all()
        self.assertEqual(len(ed._rows), 0)

    def test_pattern_changed_signal(self):
        from forge.ui.pattern_editor import PatternEditor
        received = []
        ed = PatternEditor()
        ed.patternChanged.connect(received.append)
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        self.assertGreater(len(received), 0)
        self.assertIsInstance(received[-1], dict)

    def test_render_requested_signal(self):
        from forge.ui.pattern_editor import PatternEditor
        received = []
        ed = PatternEditor()
        ed.renderRequested.connect(received.append)
        ed._on_render()
        self.assertEqual(len(received), 1)

    def test_pattern_row_steps(self):
        from forge.ui.pattern_editor import PatternRow
        row = PatternRow("kick")
        # default all off
        self.assertEqual(sum(row.steps()), 0)
        row._buttons[0].setChecked(True)
        row._buttons[4].setChecked(True)
        self.assertEqual(sum(row.steps()), 2)
        self.assertEqual(row.steps()[0], 1)
        self.assertEqual(row.steps()[4], 1)

    def test_pattern_row_set_steps(self):
        from forge.ui.pattern_editor import PatternRow
        row = PatternRow("kick")
        row.set_steps([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
        self.assertEqual(row.steps().count(1), 4)


# ---------------------------------------------------------------------------
# Phase 4: WorkshopPanel

class TestWorkshopPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _make(self, instrument_id="kick"):
        import tempfile
        from pathlib import Path
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        from forge.ui.instrument_panel import WorkshopPanel

        tmp = tempfile.mkdtemp()
        cache = ContentAddressedCache(cache_dir=Path(tmp))
        sched = RenderScheduler(cache, n_workers=1)
        doc = ProjectDoc(title="test", bpm=138.0)
        doc.add_channel(PatternChannel(instrument_id))
        panel = WorkshopPanel(0, doc, sched, bpm=138.0, length_bars=2)
        return panel, doc, sched

    def test_workshop_panel_creates(self):
        panel, doc, sched = self._make()
        panel.show()
        self.assertTrue(panel.isVisible())
        panel.close()
        sched.shutdown()

    def test_title_matches_instrument(self):
        panel, doc, sched = self._make("hat")
        self.assertEqual(panel.title(), "hat")
        sched.shutdown()

    def test_current_params_returns_dict(self):
        panel, doc, sched = self._make()
        p = panel.current_params()
        self.assertIsInstance(p, dict)
        sched.shutdown()

    def test_seed_spin_reflects_channel_seed(self):
        panel, doc, sched = self._make()
        doc.set_seed(0, 77)
        # The panel should sync (observer is called synchronously)
        self.assertEqual(panel._seed_spin.value(), 77)
        sched.shutdown()

    def test_reroll_changes_seed_in_doc(self):
        panel, doc, sched = self._make()
        doc.set_seed(0, 7)
        panel._on_reroll()
        self.assertNotEqual(doc.channel(0).seed, 7)
        sched.shutdown()

    def test_param_change_creates_doc_transaction(self):
        panel, doc, sched = self._make()
        # Simulate slider move for the first float param
        schema = next((s for s in panel._schemas if s.get("kind", "float") == "float"), None)
        if schema is None:
            self.skipTest("no float param in kick schemas")
        name = schema["name"]
        lo = float(schema.get("lo") or 0.0)
        # Directly call the internal change handler
        panel._controls[name].set_value(lo)
        panel._on_param_changed(name)
        self.assertTrue(doc.history.can_undo())
        sched.shutdown()

    def test_undo_syncs_back_to_panel(self):
        """After a param edit and an undo, the panel slider reflects the undone state."""
        panel, doc, sched = self._make()
        schema = next((s for s in panel._schemas if s.get("kind", "float") == "float"), None)
        if schema is None:
            self.skipTest("no float param")
        name = schema["name"]
        lo = float(schema.get("lo") or 0.0)
        hi = float(schema.get("hi") or 1.0)
        default = float(schema.get("default", lo))

        # Set param to hi via doc directly (not via slider, to avoid coalesce complications)
        doc.set_param(0, name, hi)
        self.assertAlmostEqual(panel._controls[name].value, hi, delta=(hi - lo) * 0.02)

        # Undo → param removed (back to "not set"); panel should revert to schema default
        doc.undo()
        expected = doc.channel(0).params.get(name, default)
        self.assertAlmostEqual(panel._controls[name].value, expected, delta=(hi - lo) * 0.02)
        sched.shutdown()

    def test_status_label_exists(self):
        panel, doc, sched = self._make()
        self.assertIsNotNone(panel._status_label)
        sched.shutdown()

    def test_instrument_type_error(self):
        from forge.document.channels import TextureChannel
        from forge.document.model import ProjectDoc
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        from forge.ui.instrument_panel import WorkshopPanel
        import tempfile
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        cache = ContentAddressedCache(cache_dir=Path(tmp))
        sched = RenderScheduler(cache)
        doc = ProjectDoc()
        doc.add_channel(TextureChannel("wind"))
        with self.assertRaises(TypeError):
            WorkshopPanel(0, doc, sched)
        sched.shutdown()


if __name__ == "__main__":
    unittest.main()
