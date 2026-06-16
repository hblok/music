"""Phase 6 tests: BreakpointCurveWidget, TextureLane, AutomationLane,
render_texture_channel, and the model additions (replace_envelope,
automation breakpoint API, section management)."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ---------------------------------------------------------------------------
# Helper factories

def _make_texture_doc(instrument_id="wind"):
    from forge.document.channels import TextureChannel
    from forge.document.model import ProjectDoc
    doc = ProjectDoc(title="test", bpm=240.0)  # high BPM → short renders
    doc.add_channel(TextureChannel(instrument_id))
    return doc, 0


def _make_auto_doc(target_param="master_gain"):
    from forge.document.channels import AutomationChannel
    from forge.document.model import ProjectDoc
    doc = ProjectDoc(title="test", bpm=138.0)
    doc.add_channel(AutomationChannel(target_param))
    return doc, 0


# ---------------------------------------------------------------------------
# BreakpointCurveWidget (headless-ish: creates widget but doesn't show it)

class TestBreakpointCurveWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _widget(self, bar_count=8):
        from forge.ui.automation_lane import BreakpointCurveWidget
        return BreakpointCurveWidget(bar_count=bar_count)

    def test_starts_empty(self):
        w = self._widget()
        self.assertEqual(w.points(), [])

    def test_set_points(self):
        w = self._widget()
        w.set_points([(0.0, 0.5), (4.0, 1.0)])
        pts = w.points()
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[0][0], 0.0)
        self.assertAlmostEqual(pts[1][0], 4.0)

    def test_set_points_sorted(self):
        w = self._widget()
        w.set_points([(8.0, 0.5), (2.0, 0.2), (0.0, 1.0)])
        bars = [p[0] for p in w.points()]
        self.assertEqual(bars, sorted(bars))

    def test_add_point(self):
        w = self._widget()
        w.add_point(3.0, 0.7)
        pts = w.points()
        self.assertEqual(len(pts), 1)
        self.assertAlmostEqual(pts[0][0], 3.0)
        self.assertAlmostEqual(pts[0][1], 0.7)

    def test_add_point_emits_signal(self):
        w = self._widget()
        received = []
        w.curveChanged.connect(received.append)
        w.add_point(3.0, 0.7)
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]), 1)

    def test_remove_point(self):
        w = self._widget()
        w.set_points([(0.0, 1.0), (4.0, 0.5)])
        w.remove_point(0)
        pts = w.points()
        self.assertEqual(len(pts), 1)
        self.assertAlmostEqual(pts[0][0], 4.0)

    def test_remove_point_emits_signal(self):
        w = self._widget()
        w.set_points([(0.0, 1.0)])
        received = []
        w.curveChanged.connect(received.append)
        w.remove_point(0)
        self.assertEqual(len(received), 1)

    def test_add_multiple_sorted(self):
        w = self._widget()
        w.add_point(8.0, 0.0)
        w.add_point(0.0, 1.0)
        bars = [p[0] for p in w.points()]
        self.assertEqual(bars, sorted(bars))

    def test_clamps_value_to_range(self):
        from forge.ui.automation_lane import BreakpointCurveWidget
        w = BreakpointCurveWidget(bar_count=8, lo=0.2, hi=0.8)
        # _from_px should clamp
        bar, val = w._from_px(0, 0)  # top-left → hi
        self.assertAlmostEqual(val, 0.8)
        bar, val = w._from_px(0, w.height())
        self.assertAlmostEqual(val, 0.2)


# ---------------------------------------------------------------------------
# TextureLane

class TestTextureLane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _lane(self, bar_count=4):
        from forge.ui.automation_lane import TextureLane
        doc, idx = _make_texture_doc()
        lane = TextureLane(idx, doc, bar_count=bar_count)
        return lane, doc, idx

    def test_creates(self):
        lane, doc, idx = self._lane()
        self.assertIsNotNone(lane)

    def test_starts_empty_curve(self):
        lane, doc, idx = self._lane()
        self.assertEqual(lane._curve.points(), [])

    def test_doc_breakpoint_shows_in_curve(self):
        lane, doc, idx = self._lane()
        doc.add_breakpoint(idx, 0.0, 0.5)
        doc.add_breakpoint(idx, 2.0, 1.0)
        pts = lane._curve.points()
        self.assertEqual(len(pts), 2)

    def test_curve_change_updates_doc(self):
        lane, doc, idx = self._lane()
        lane._on_curve_changed([(0.0, 0.3), (4.0, 0.9)])
        env = doc.channel(idx).envelope
        self.assertEqual(len(env), 2)
        self.assertAlmostEqual(env[0].value, 0.3)

    def test_curve_change_is_undoable(self):
        lane, doc, idx = self._lane()
        lane._on_curve_changed([(0.0, 0.5)])
        doc.undo()
        self.assertEqual(len(doc.channel(idx).envelope), 0)

    def test_undo_refreshes_curve(self):
        lane, doc, idx = self._lane()
        lane._on_curve_changed([(0.0, 0.5)])
        doc.undo()
        self.assertEqual(len(lane._curve.points()), 0)

    def test_clear_button_empties_envelope(self):
        lane, doc, idx = self._lane()
        doc.add_breakpoint(idx, 0.0, 1.0)
        lane._on_clear()
        self.assertEqual(len(doc.channel(idx).envelope), 0)

    def test_other_channel_change_not_refreshed(self):
        from forge.document.channels import TextureChannel
        from forge.ui.automation_lane import TextureLane
        doc, idx = _make_texture_doc()
        doc.add_channel(TextureChannel("drone"))
        lane = TextureLane(idx, doc, bar_count=4)
        # Change channel 1 (drone) — channel 0 lane should not update
        doc.add_breakpoint(1, 0.0, 0.5)
        self.assertEqual(len(lane._curve.points()), 0)


# ---------------------------------------------------------------------------
# AutomationLane

class TestAutomationLane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _lane(self, bar_count=4):
        from forge.ui.automation_lane import AutomationLane
        doc, idx = _make_auto_doc()
        lane = AutomationLane(idx, doc, bar_count=bar_count)
        return lane, doc, idx

    def test_creates(self):
        lane, doc, idx = self._lane()
        self.assertIsNotNone(lane)

    def test_curve_change_updates_doc(self):
        lane, doc, idx = self._lane()
        lane._on_curve_changed([(0.0, 1.0), (8.0, 0.0)])
        bps = doc.channel(idx).breakpoints
        self.assertEqual(len(bps), 2)

    def test_curve_change_is_undoable(self):
        lane, doc, idx = self._lane()
        lane._on_curve_changed([(0.0, 1.0)])
        doc.undo()
        self.assertEqual(len(doc.channel(idx).breakpoints), 0)

    def test_doc_bp_shows_in_curve(self):
        lane, doc, idx = self._lane()
        doc.add_automation_bp(idx, 0.0, 1.0)
        doc.add_automation_bp(idx, 4.0, 0.0)
        self.assertEqual(len(lane._curve.points()), 2)

    def test_clear_removes_all(self):
        lane, doc, idx = self._lane()
        doc.add_automation_bp(idx, 0.0, 1.0)
        lane._on_clear()
        self.assertEqual(len(doc.channel(idx).breakpoints), 0)


# ---------------------------------------------------------------------------
# render_texture_channel (headless, no audio device)

class TestRenderTextureChannel(unittest.TestCase):
    def test_renders_wind_short(self):
        from forge.control import render_texture_channel
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind")
        # bpm=600 → 1 bar = 0.4 s; length_bars=1 → 0.4 s render
        buf = render_texture_channel(ch, length_bars=1, bpm=600.0)
        self.assertGreater(buf.data.shape[0], 0)
        self.assertEqual(buf.data.shape[1], 2)

    def test_renders_drone(self):
        from forge.control import render_texture_channel
        from forge.document.channels import TextureChannel
        ch = TextureChannel("drone")
        buf = render_texture_channel(ch, length_bars=1, bpm=600.0)
        self.assertGreater(buf.data.shape[0], 0)

    def test_envelope_applied(self):
        import numpy as np
        from forge.control import render_texture_channel
        from forge.document.channels import Breakpoint, TextureChannel
        # Envelope: 0.0 at bar 0, 0.0 at bar 1 → all silence
        ch = TextureChannel("wind")
        ch.envelope = [Breakpoint(0.0, 0.0), Breakpoint(1.0, 0.0)]
        buf = render_texture_channel(ch, length_bars=1, bpm=600.0)
        self.assertAlmostEqual(np.max(np.abs(buf.data)), 0.0, places=6)

    def test_envelope_full_gain(self):
        import numpy as np
        from forge.control import render_texture_channel
        from forge.document.channels import Breakpoint, TextureChannel
        ch_no_env = TextureChannel("wind", seed=7)
        ch_full = TextureChannel("wind", seed=7)
        ch_full.envelope = [Breakpoint(0.0, 1.0), Breakpoint(1.0, 1.0)]
        buf_no = render_texture_channel(ch_no_env, length_bars=1, bpm=600.0)
        buf_full = render_texture_channel(ch_full, length_bars=1, bpm=600.0)
        np.testing.assert_array_almost_equal(buf_no.data, buf_full.data)

    def test_deterministic(self):
        import numpy as np
        from forge.control import render_texture_channel
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind")
        b1 = render_texture_channel(ch, length_bars=1, bpm=600.0, seed=42)
        b2 = render_texture_channel(ch, length_bars=1, bpm=600.0, seed=42)
        np.testing.assert_array_equal(b1.data, b2.data)

    def test_wrong_type_raises(self):
        from forge.control import render_texture_channel
        from forge.document.channels import PatternChannel
        with self.assertRaises(TypeError):
            render_texture_channel(PatternChannel("kick"), length_bars=1, bpm=138.0)


# ---------------------------------------------------------------------------
# ProjectDoc: replace_envelope + automation BP + section management

class TestReplaceEnvelope(unittest.TestCase):
    def test_replace_sets_envelope(self):
        doc, idx = _make_texture_doc()
        doc.replace_envelope(idx, [(0.0, 0.5), (4.0, 1.0)])
        env = doc.channel(idx).envelope
        self.assertEqual(len(env), 2)
        self.assertAlmostEqual(env[1].value, 1.0)

    def test_replace_is_undoable(self):
        doc, idx = _make_texture_doc()
        doc.replace_envelope(idx, [(0.0, 0.5)])
        doc.undo()
        self.assertEqual(len(doc.channel(idx).envelope), 0)

    def test_remove_breakpoint(self):
        doc, idx = _make_texture_doc()
        doc.add_breakpoint(idx, 0.0, 0.5)
        doc.add_breakpoint(idx, 4.0, 1.0)
        doc.remove_breakpoint(idx, 0)
        env = doc.channel(idx).envelope
        self.assertEqual(len(env), 1)
        self.assertAlmostEqual(env[0].value, 1.0)

    def test_remove_breakpoint_undoable(self):
        doc, idx = _make_texture_doc()
        doc.add_breakpoint(idx, 0.0, 0.5)
        doc.remove_breakpoint(idx, 0)
        doc.undo()
        self.assertEqual(len(doc.channel(idx).envelope), 1)

    def test_wrong_channel_raises(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(PatternChannel("kick"))
        with self.assertRaises(TypeError):
            doc.replace_envelope(0, [])


class TestAutomationBPDoc(unittest.TestCase):
    def test_add_bp(self):
        doc, idx = _make_auto_doc()
        doc.add_automation_bp(idx, 0.0, 1.0)
        bps = doc.channel(idx).breakpoints
        self.assertEqual(len(bps), 1)
        self.assertAlmostEqual(bps[0].value, 1.0)

    def test_add_bp_undoable(self):
        doc, idx = _make_auto_doc()
        doc.add_automation_bp(idx, 0.0, 1.0)
        doc.undo()
        self.assertEqual(len(doc.channel(idx).breakpoints), 0)

    def test_set_automation_bp(self):
        doc, idx = _make_auto_doc()
        doc.add_automation_bp(idx, 0.0, 0.5)
        doc.set_automation_bp(idx, 0, 2.0, 0.8)
        bps = doc.channel(idx).breakpoints
        self.assertAlmostEqual(bps[0].bar, 2.0)
        self.assertAlmostEqual(bps[0].value, 0.8)

    def test_set_automation_bp_undoable(self):
        doc, idx = _make_auto_doc()
        doc.add_automation_bp(idx, 0.0, 0.5)
        doc.set_automation_bp(idx, 0, 2.0, 0.8)
        doc.undo()
        bps = doc.channel(idx).breakpoints
        self.assertAlmostEqual(bps[0].bar, 0.0)

    def test_replace_automation_bps(self):
        doc, idx = _make_auto_doc()
        doc.replace_automation_bps(idx, [(0.0, 1.0), (4.0, 0.0)])
        bps = doc.channel(idx).breakpoints
        self.assertEqual(len(bps), 2)

    def test_replace_automation_undoable(self):
        doc, idx = _make_auto_doc()
        doc.replace_automation_bps(idx, [(0.0, 1.0)])
        doc.undo()
        self.assertEqual(len(doc.channel(idx).breakpoints), 0)

    def test_wrong_channel_raises(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(PatternChannel("kick"))
        with self.assertRaises(TypeError):
            doc.add_automation_bp(0, 0.0, 1.0)


class TestSectionManagement(unittest.TestCase):
    def _doc(self):
        from forge.document.model import ProjectDoc
        return ProjectDoc()

    def test_add_section(self):
        doc = self._doc()
        idx = doc.add_section("intro", 8)
        self.assertEqual(idx, 0)
        self.assertEqual(len(doc.sections), 1)
        self.assertEqual(doc.sections[0]["name"], "intro")

    def test_add_section_undoable(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.undo()
        self.assertEqual(len(doc.sections), 0)

    def test_remove_section(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.add_section("drop", 16)
        doc.remove_section(0)
        self.assertEqual(len(doc.sections), 1)
        self.assertEqual(doc.sections[0]["name"], "drop")

    def test_remove_section_undoable(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.remove_section(0)
        doc.undo()
        self.assertEqual(len(doc.sections), 1)

    def test_rename_section(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.rename_section(0, "prologue")
        self.assertEqual(doc.sections[0]["name"], "prologue")

    def test_set_section_length(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.set_section_length(0, 16)
        self.assertEqual(doc.sections[0]["length_bars"], 16)

    def test_move_section(self):
        doc = self._doc()
        doc.add_section("A", 4)
        doc.add_section("B", 4)
        doc.add_section("C", 4)
        doc.move_section(0, 2)
        names = [s["name"] for s in doc.sections]
        self.assertEqual(names, ["B", "C", "A"])

    def test_move_section_undoable(self):
        doc = self._doc()
        doc.add_section("A", 4)
        doc.add_section("B", 4)
        doc.move_section(0, 1)
        doc.undo()
        names = [s["name"] for s in doc.sections]
        self.assertEqual(names, ["A", "B"])

    def test_sections_in_to_dict(self):
        doc = self._doc()
        doc.add_section("intro", 8)
        d = doc.to_dict()
        self.assertIn("sections", d)
        self.assertEqual(d["sections"][0]["name"], "intro")

    def test_sections_round_trip(self):
        from forge.document.model import ProjectDoc
        doc = self._doc()
        doc.add_section("intro", 8)
        doc.add_section("drop", 16)
        doc2 = ProjectDoc.from_dict(doc.to_dict())
        self.assertEqual(len(doc2.sections), 2)
        self.assertEqual(doc2.sections[1]["name"], "drop")

    def test_schema_version_in_dict(self):
        doc = self._doc()
        d = doc.to_dict()
        self.assertEqual(d.get("schema_version"), "3.0")


if __name__ == "__main__":
    unittest.main()
