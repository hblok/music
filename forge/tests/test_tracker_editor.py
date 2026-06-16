"""Phase 5 tests: TrackerEditor — keyboard entry, accent/ghost/prob, copy/paste."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_doc(instrument_id="kick", n_steps=16):
    from forge.document.channels import PatternChannel
    from forge.document.model import ProjectDoc
    doc = ProjectDoc(title="test", bpm=138.0)
    doc.add_channel(PatternChannel(instrument_id, n_steps=n_steps))
    return doc


class TestTrackerRow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _row(self, n=16):
        from forge.ui.pattern_editor import TrackerRow
        return TrackerRow("kick", n)

    def test_creates(self):
        row = self._row()
        self.assertEqual(len(row._cells), 16)
        self.assertEqual(len(row._accent_btns), 16)
        self.assertEqual(len(row._ghost_btns), 16)

    def test_refresh_step_updates_cell(self):
        from forge.document.channels import StepData
        row = self._row()
        step = StepData(on=True, accent=True)
        row.refresh_step(0, step)
        self.assertTrue(row._cells[0]._on)
        self.assertTrue(row._cells[0]._accent)
        self.assertTrue(row._accent_btns[0].isChecked())

    def test_refresh_all_syncs(self):
        from forge.document.channels import StepData
        row = self._row(8)
        steps = [StepData(on=(i % 2 == 0)) for i in range(8)]
        row.refresh_all(steps)
        for i, cell in enumerate(row._cells):
            self.assertEqual(cell._on, (i % 2 == 0))

    def test_cursor_highlights_cell(self):
        row = self._row()
        row.set_cursor(3)
        self.assertTrue(row._cells[3]._cursor)
        self.assertFalse(row._cells[0]._cursor)

    def test_selected_range(self):
        row = self._row()
        row.set_selected(2, 6)
        for i in range(16):
            self.assertEqual(row._cells[i]._selected, 2 <= i < 6)


class TestTrackerEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _editor(self, instrument_id="kick"):
        from forge.ui.pattern_editor import TrackerEditor
        doc = _make_doc(instrument_id)
        editor = TrackerEditor(0, doc)
        return editor, doc

    def test_creates(self):
        editor, doc = self._editor()
        editor.show()
        self.assertTrue(editor.isVisible())
        editor.close()

    def test_requires_pattern_channel(self):
        from forge.document.channels import TextureChannel
        from forge.document.model import ProjectDoc
        from forge.ui.pattern_editor import TrackerEditor
        doc = ProjectDoc()
        doc.add_channel(TextureChannel("wind"))
        with self.assertRaises(TypeError):
            TrackerEditor(0, doc)

    def test_initial_cursor_at_zero(self):
        editor, doc = self._editor()
        self.assertEqual(editor.cursor, 0)

    # ---- keyboard: navigation

    def _press(self, editor, key, mods=None):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        mods = mods or Qt.KeyboardModifier.NoModifier
        event = QKeyEvent(QEvent.Type.KeyPress, key, mods)
        editor.keyPressEvent(event)

    def test_right_arrow_moves_cursor(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Right)
        self.assertEqual(editor.cursor, 1)

    def test_left_arrow_clamps_at_zero(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Left)
        self.assertEqual(editor.cursor, 0)

    def test_right_clamps_at_n_steps(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        for _ in range(20):
            self._press(editor, Qt.Key.Key_Right)
        self.assertEqual(editor.cursor, doc.channel(0).n_steps - 1)

    def test_cursor_moved_signal(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        positions = []
        editor.cursorMoved.connect(positions.append)
        self._press(editor, Qt.Key.Key_Right)
        self.assertEqual(positions, [1])

    # ---- keyboard: step toggle

    def test_space_toggles_step(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self.assertFalse(doc.channel(0).steps[0].on)
        self._press(editor, Qt.Key.Key_Space)
        self.assertTrue(doc.channel(0).steps[0].on)

    def test_space_toggle_is_undoable(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Space)
        doc.undo()
        self.assertFalse(doc.channel(0).steps[0].on)

    def test_space_emits_channel_changed(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        received = []
        editor.channelChanged.connect(received.append)
        self._press(editor, Qt.Key.Key_Space)
        self.assertEqual(received, [0])

    # ---- keyboard: accent

    def test_a_key_toggles_accent(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_A)
        self.assertTrue(doc.channel(0).steps[0].accent)
        self._press(editor, Qt.Key.Key_A)
        self.assertFalse(doc.channel(0).steps[0].accent)

    def test_accent_is_undoable(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_A)
        doc.undo()
        self.assertFalse(doc.channel(0).steps[0].accent)

    # ---- keyboard: ghost

    def test_g_key_toggles_ghost(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_G)
        self.assertTrue(doc.channel(0).steps[0].ghost)

    # ---- keyboard: delete

    def test_delete_clears_step(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Space)   # on
        self._press(editor, Qt.Key.Key_Delete)  # clear
        self.assertFalse(doc.channel(0).steps[0].on)

    # ---- keyboard: undo/redo via Ctrl+Z/Y

    def test_ctrl_z_undoes(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Space)  # step 0 on
        self._press(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        self.assertFalse(doc.channel(0).steps[0].on)

    def test_ctrl_y_redoes(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        self._press(editor, Qt.Key.Key_Space)
        self._press(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        self._press(editor, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(doc.channel(0).steps[0].on)

    # ---- copy/paste

    def test_copy_paste_block(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        # Set steps 0,2 on
        doc.toggle_step(0, 0)
        doc.toggle_step(0, 2)
        # Select all (Ctrl+A)
        self._press(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        # Copy (Ctrl+C)
        self._press(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        # Move cursor to step 8 and paste
        for _ in range(8):
            self._press(editor, Qt.Key.Key_Right)
        self._press(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        # Steps 8 and 10 should now be on (pasted from 0 and 2)
        self.assertTrue(doc.channel(0).steps[8].on)
        self.assertTrue(doc.channel(0).steps[10].on)

    def test_paste_is_undoable(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        doc.toggle_step(0, 0)
        self._press(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        self._press(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        for _ in range(4):
            self._press(editor, Qt.Key.Key_Right)
        self._press(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(doc.channel(0).steps[4].on)
        doc.undo()
        self.assertFalse(doc.channel(0).steps[4].on)

    def test_copy_without_select_copies_cursor_step(self):
        from PySide6.QtCore import Qt
        editor, doc = self._editor()
        doc.toggle_step(0, 0)
        # No select — cursor is at 0
        self._press(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        self.assertIsNotNone(editor._clipboard)
        self.assertEqual(len(editor._clipboard), 1)

    # ---- doc sync

    def test_doc_change_refreshes_cells(self):
        editor, doc = self._editor()
        # Toggle step 5 directly in doc
        doc.toggle_step(0, 5)
        # Cell should be refreshed via observer
        self.assertTrue(editor._row._cells[5]._on)

    def test_other_channel_change_not_refreshed(self):
        from forge.document.channels import PatternChannel
        editor, doc = self._editor()
        # Add another channel
        doc.add_channel(PatternChannel("hat"))
        # Change channel 1 — channel 0 editor should not crash
        doc.toggle_step(1, 0)
        self.assertFalse(editor._row._cells[0]._on)  # channel 0 unaffected

    # ---- to_pattern_spec

    def test_to_pattern_spec_structure(self):
        editor, doc = self._editor()
        doc.toggle_step(0, 0)
        spec = editor.to_pattern_spec()
        self.assertIn("bpm", spec)
        self.assertIn("tracks", spec)
        self.assertEqual(len(spec["tracks"]), 1)
        self.assertEqual(spec["tracks"][0]["instrument"], "kick")
        # Step 0 should be on
        self.assertEqual(spec["tracks"][0]["steps"][0], 1)

    def test_to_pattern_spec_with_accent(self):
        editor, doc = self._editor()
        doc.toggle_step(0, 0)
        doc.set_step(0, 0, "accent", True)
        spec = editor.to_pattern_spec()
        step_val = spec["tracks"][0]["steps"][0]
        self.assertIsInstance(step_val, dict)
        self.assertTrue(step_val["accent"])

    # ---- mouse click

    def test_mouse_click_toggles_step(self):
        editor, doc = self._editor()
        editor._row._cells[3].clicked.emit(3)
        self.assertTrue(doc.channel(0).steps[3].on)

    def test_accent_button_click_toggles_accent(self):
        editor, doc = self._editor()
        editor._row.accentToggled.emit(3)
        self.assertTrue(doc.channel(0).steps[3].accent)

    def test_ghost_button_click_toggles_ghost(self):
        editor, doc = self._editor()
        editor._row.ghostToggled.emit(5)
        self.assertTrue(doc.channel(0).steps[5].ghost)


# ---------------------------------------------------------------------------
# Verify backward compatibility: original PatternEditor API still works

class TestPatternEditorBackwardCompat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_add_row_and_to_spec(self):
        from forge.ui.pattern_editor import PatternEditor
        ed = PatternEditor(bpm=138.0, length_bars=4)
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        ed._rows[0]._buttons[0].setChecked(True)
        spec = ed.to_pattern_spec()
        self.assertEqual(spec["tracks"][0]["instrument"], "kick")
        self.assertEqual(spec["tracks"][0]["steps"][0], 1)

    def test_pattern_changed_signal(self):
        from forge.ui.pattern_editor import PatternEditor
        received = []
        ed = PatternEditor()
        ed.patternChanged.connect(received.append)
        ed._instrument_combo.setCurrentText("kick")
        ed._add_row()
        self.assertGreater(len(received), 0)


if __name__ == "__main__":
    unittest.main()
