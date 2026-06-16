"""Phase 9 tests: A/B compare, autosave/recovery, render-queue status."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_pattern_doc(bpm=138.0):
    from forge.document.channels import PatternChannel
    from forge.document.model import ProjectDoc
    doc = ProjectDoc(title="test", bpm=bpm, seed=0)
    ch = PatternChannel("kick")
    ch.steps[0].on = True
    doc.add_channel(ch)
    return doc


# ---------------------------------------------------------------------------
# AutoSave

class TestAutoSave(unittest.TestCase):
    def test_flush_creates_file(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path, interval=100)
            saver.flush()
            saver.stop()
            self.assertTrue(path.exists())

    def test_autosave_on_interval(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path, interval=3)
            doc.toggle_step(0, 1)
            doc.toggle_step(0, 2)
            self.assertFalse(path.exists())  # 2 changes, not yet
            doc.toggle_step(0, 3)            # 3rd → triggers
            saver.stop()
            self.assertTrue(path.exists())

    def test_recover_returns_doc(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path)
            saver.flush()
            saver.stop()
            recovered = AutoSave.recover(path)
        self.assertIsNotNone(recovered)
        self.assertAlmostEqual(recovered.bpm, 138.0)
        self.assertEqual(len(recovered.channels), 1)

    def test_recover_step_state(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path)
            saver.flush()
            saver.stop()
            recovered = AutoSave.recover(path)
        self.assertTrue(recovered.channel(0).steps[0].on)

    def test_recover_missing_file_returns_none(self):
        from forge.document.autosave import AutoSave
        result = AutoSave.recover(Path("/no/such/path.json"))
        self.assertIsNone(result)

    def test_recover_corrupt_file_returns_none(self):
        from forge.document.autosave import AutoSave
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("NOT JSON {{{")
            result = AutoSave.recover(path)
        self.assertIsNone(result)

    def test_atomic_write_no_tmp_left(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path)
            saver.flush()
            saver.stop()
            tmp_path = path.with_suffix(".tmp.json")
            self.assertFalse(tmp_path.exists())

    def test_stop_unsubscribes(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path, interval=1)
            saver.stop()
            doc.toggle_step(0, 5)  # after stop, should NOT trigger
            self.assertFalse(path.exists())

    def test_clear_removes_file(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path)
            saver.flush()
            saver.stop()
            AutoSave.clear(path)
            self.assertFalse(path.exists())

    def test_clear_noop_if_missing(self):
        from forge.document.autosave import AutoSave
        AutoSave.clear(Path("/no/such/path.json"))  # should not raise

    def test_round_trip_with_sections(self):
        from forge.document.autosave import AutoSave
        doc = _make_pattern_doc()
        doc.add_section("intro", 8)
        doc.add_section("drop", 16)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autosave.json"
            saver = AutoSave(doc, path)
            saver.flush()
            saver.stop()
            recovered = AutoSave.recover(path)
        self.assertEqual(len(recovered.sections), 2)
        self.assertEqual(recovered.sections[1]["name"], "drop")


# ---------------------------------------------------------------------------
# ABCompareWidget

class TestABCompareWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _widget(self):
        from forge.ui.ab_compare import ABCompareWidget
        doc = _make_pattern_doc()
        w = ABCompareWidget(doc)
        return w, doc

    def test_creates(self):
        w, doc = self._widget()
        self.assertIsNotNone(w)

    def test_initial_no_snaps(self):
        w, doc = self._widget()
        self.assertFalse(w.has_snap("A"))
        self.assertFalse(w.has_snap("B"))
        self.assertFalse(w._toggle_btn.isEnabled())

    def test_snap_a(self):
        w, doc = self._widget()
        w.snapshot("A")
        self.assertTrue(w.has_snap("A"))
        self.assertEqual(w.current, "A")

    def test_toggle_enabled_after_both_snaps(self):
        w, doc = self._widget()
        w.snapshot("A")
        self.assertFalse(w._toggle_btn.isEnabled())
        w.snapshot("B")
        self.assertTrue(w._toggle_btn.isEnabled())

    def test_toggle_switches_current(self):
        w, doc = self._widget()
        w.snapshot("A")
        w.snapshot("B")
        # current is "B" (last snapped)
        w._toggle()
        self.assertEqual(w.current, "A")

    def test_toggle_emits_signal(self):
        w, doc = self._widget()
        w.snapshot("A")
        w.snapshot("B")
        received = []
        w.stateChanged.connect(received.append)
        w._toggle()
        self.assertEqual(received, ["A"])

    def test_toggle_restores_channel_state(self):
        w, doc = self._widget()
        # step 0 is on in snap A
        w.snapshot("A")
        # toggle step 0 off, then snap B
        doc.toggle_step(0, 0)
        self.assertFalse(doc.channel(0).steps[0].on)
        w.snapshot("B")
        # toggle back to A — step 0 should be on again
        w._toggle()
        self.assertTrue(doc.channel(0).steps[0].on)

    def test_toggle_back_to_b(self):
        w, doc = self._widget()
        w.snapshot("A")
        doc.toggle_step(0, 0)
        w.snapshot("B")
        w._toggle()  # → A
        w._toggle()  # → B
        self.assertEqual(w.current, "B")
        self.assertFalse(doc.channel(0).steps[0].on)

    def test_restore_notifies_observers(self):
        w, doc = self._widget()
        w.snapshot("A")
        w.snapshot("B")
        received = []
        doc.subscribe(lambda txn: received.append(txn))
        w._toggle()
        ab_txns = [t for t in received
                   if any(c.path[0] == "ab_restore" for c in t.changes)]
        self.assertGreater(len(ab_txns), 0)

    def test_buttons_trigger_snaps(self):
        w, doc = self._widget()
        w._snap_a_btn.click()
        self.assertTrue(w.has_snap("A"))
        w._snap_b_btn.click()
        self.assertTrue(w.has_snap("B"))


# ---------------------------------------------------------------------------
# Render-queue tooltip via TransportWidget

class TestRenderQueueStatus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_tooltip_empty_when_idle(self):
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        from forge.playback.service import PlaybackService
        from forge.ui.transport import TransportWidget
        svc = PlaybackService(bpm=138.0)
        t = TransportWidget(svc)
        cache = ContentAddressedCache(cache_dir=None)
        sched = RenderScheduler(cache)
        t.set_scheduler(sched)
        t._poll_position()
        self.assertEqual(t._pos_label.toolTip(), "")
        sched.shutdown()

    def test_no_scheduler_no_crash(self):
        from forge.playback.service import PlaybackService
        from forge.ui.transport import TransportWidget
        svc = PlaybackService(bpm=138.0)
        t = TransportWidget(svc)
        t._poll_position()  # no scheduler set — should not raise


if __name__ == "__main__":
    unittest.main()
