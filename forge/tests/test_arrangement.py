"""Phase 7 tests: ArrangementView, extended MixerWidget, transport extensions."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_doc():
    from forge.document.model import ProjectDoc
    return ProjectDoc(title="test", bpm=138.0)


# ---------------------------------------------------------------------------
# ArrangementView

class TestArrangementView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _view(self, sections=None):
        from forge.ui.arrangement import ArrangementView
        doc = _make_doc()
        if sections:
            for name, bars in sections:
                doc.add_section(name, bars)
        view = ArrangementView(doc)
        return view, doc

    def test_creates_empty(self):
        view, doc = self._view()
        self.assertIsNotNone(view)
        self.assertEqual(view._list.count(), 0)

    def test_shows_existing_sections(self):
        view, doc = self._view([("intro", 8), ("drop", 16)])
        self.assertEqual(view._list.count(), 2)
        self.assertIn("intro", view._list.item(0).text())
        self.assertIn("drop", view._list.item(1).text())

    def test_add_updates_list(self):
        view, doc = self._view()
        doc.add_section("verse", 8)
        self.assertEqual(view._list.count(), 1)

    def test_remove_updates_list(self):
        view, doc = self._view([("intro", 8), ("drop", 16)])
        doc.remove_section(0)
        self.assertEqual(view._list.count(), 1)
        self.assertIn("drop", view._list.item(0).text())

    def test_rename_updates_list(self):
        view, doc = self._view([("intro", 8)])
        doc.rename_section(0, "prologue")
        self.assertIn("prologue", view._list.item(0).text())

    def test_move_up_reorders(self):
        view, doc = self._view([("A", 4), ("B", 4)])
        view._list.setCurrentRow(1)
        view._on_move_up()
        names = [s["name"] for s in doc.sections]
        self.assertEqual(names, ["B", "A"])

    def test_move_down_reorders(self):
        view, doc = self._view([("A", 4), ("B", 4)])
        view._list.setCurrentRow(0)
        view._on_move_down()
        names = [s["name"] for s in doc.sections]
        self.assertEqual(names, ["B", "A"])

    def test_duplicate_adds_section(self):
        view, doc = self._view([("intro", 8)])
        view._list.setCurrentRow(0)
        view._on_duplicate()
        self.assertEqual(len(doc.sections), 2)
        self.assertIn("copy", doc.sections[1]["name"])

    def test_undo_removes_added_section(self):
        view, doc = self._view()
        doc.add_section("intro", 8)
        doc.undo()
        self.assertEqual(view._list.count(), 0)

    def test_section_selected_signal(self):
        view, doc = self._view([("intro", 8), ("drop", 16)])
        received = []
        view.sectionSelected.connect(lambda s, l: received.append((s, l)))
        view._list.setCurrentRow(1)
        # Signal should be emitted with start_bar=8, length_bars=16
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], (8, 16))

    def test_length_spin_updates_section(self):
        view, doc = self._view([("intro", 8)])
        view._list.setCurrentRow(0)
        view._len_spin.setValue(16)
        self.assertEqual(doc.sections[0]["length_bars"], 16)

    def test_length_spin_shows_current_section(self):
        view, doc = self._view([("intro", 8), ("drop", 16)])
        view._list.setCurrentRow(1)
        self.assertEqual(view._len_spin.value(), 16)


# ---------------------------------------------------------------------------
# MixerWidget extensions: set_mixer, add_strip, remove_strip

class TestMixerWidgetExtensions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _mixer(self, names=("kick", "hat")):
        from forge.ui.mixer import MixerWidget
        return MixerWidget(list(names))

    def test_add_strip(self):
        m = self._mixer(["kick"])
        m.add_strip("bass")
        self.assertIn("bass", m._strips)

    def test_add_strip_idempotent(self):
        m = self._mixer(["kick"])
        m.add_strip("kick")
        self.assertEqual(len(m._strips), 1)

    def test_remove_strip(self):
        m = self._mixer(["kick", "hat"])
        m.remove_strip("kick")
        self.assertNotIn("kick", m._strips)

    def test_remove_strip_noop_if_absent(self):
        m = self._mixer(["kick"])
        m.remove_strip("bass")  # should not raise
        self.assertEqual(len(m._strips), 1)

    def test_set_mixer_pushes_gain(self):
        from forge.playback.mixer import CallbackMixer
        from forge.ui.mixer import MixerWidget
        m = MixerWidget(["kick"])
        m._strips["kick"].set_volume(0.5)
        cm = CallbackMixer(sr=44100)
        cm.add_channel("kick")
        m.set_mixer(cm)
        slot = cm._slots["kick"]
        self.assertAlmostEqual(slot.gain, 0.5, places=2)

    def test_set_mixer_pushes_mute(self):
        from forge.playback.mixer import CallbackMixer
        from forge.ui.mixer import MixerWidget
        m = MixerWidget(["kick"])
        m._strips["kick"]._mute_btn.setChecked(True)
        cm = CallbackMixer(sr=44100)
        cm.add_channel("kick")
        m.set_mixer(cm)
        slot = cm._slots["kick"]
        self.assertTrue(slot.muted)

    def test_fader_change_updates_backend(self):
        from forge.playback.mixer import CallbackMixer
        from forge.ui.mixer import MixerWidget
        m = MixerWidget(["kick"])
        cm = CallbackMixer(sr=44100)
        cm.add_channel("kick")
        m.set_mixer(cm)
        m._strips["kick"]._fader.setValue(60)
        slot = cm._slots["kick"]
        self.assertAlmostEqual(slot.gain, 0.6, places=2)


# ---------------------------------------------------------------------------
# TransportWidget extensions: set_scheduler, set_loop_range

class TestTransportExtensions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _transport(self):
        from forge.playback.service import PlaybackService
        from forge.ui.transport import TransportWidget
        svc = PlaybackService(bpm=138.0)
        return TransportWidget(svc)

    def test_set_scheduler_attaches(self):
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        t = self._transport()
        cache = ContentAddressedCache(cache_dir=None)
        sched = RenderScheduler(cache)
        t.set_scheduler(sched)
        self.assertIs(t._scheduler, sched)
        sched.shutdown()

    def test_set_loop_range_stores(self):
        t = self._transport()
        t.set_loop_range(8.0, 24.0)
        self.assertAlmostEqual(t._loop_start, 8.0)
        self.assertAlmostEqual(t._loop_end, 24.0)

    def test_poll_with_scheduler_no_crash(self):
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        t = self._transport()
        cache = ContentAddressedCache(cache_dir=None)
        sched = RenderScheduler(cache)
        t.set_scheduler(sched)
        t._poll_position()  # should not raise
        sched.shutdown()

    def test_poll_without_scheduler_no_crash(self):
        t = self._transport()
        t._poll_position()  # should not raise


if __name__ == "__main__":
    unittest.main()
