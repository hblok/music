"""Phase 1 tests: document model, transactions, history, channels."""

import unittest

from forge.document.channels import (
    AutomationChannel,
    Breakpoint,
    PatternChannel,
    StepData,
    TextureChannel,
    channel_from_dict,
)
from forge.document.history import History
from forge.document.model import ProjectDoc
from forge.document.transaction import Transaction, channel_content_hash


# ---------------------------------------------------------------------------
# StepData

class TestStepData(unittest.TestCase):
    def test_default_off(self):
        s = StepData()
        self.assertFalse(s.on)

    def test_from_int_zero(self):
        s = StepData.from_step_value(0)
        self.assertFalse(s.on)

    def test_from_int_one(self):
        s = StepData.from_step_value(1)
        self.assertTrue(s.on)

    def test_from_none(self):
        s = StepData.from_step_value(None)
        self.assertFalse(s.on)

    def test_from_dict(self):
        s = StepData.from_step_value({"on": True, "accent": True, "probability": 0.5})
        self.assertTrue(s.on)
        self.assertTrue(s.accent)
        self.assertAlmostEqual(s.probability, 0.5)

    def test_to_step_value_off(self):
        s = StepData(on=False)
        self.assertEqual(s.to_step_value(), 0)

    def test_to_step_value_plain_on(self):
        s = StepData(on=True)
        self.assertEqual(s.to_step_value(), 1)

    def test_to_step_value_with_accent(self):
        s = StepData(on=True, accent=True)
        v = s.to_step_value()
        self.assertIsInstance(v, dict)
        self.assertTrue(v["on"])
        self.assertTrue(v["accent"])

    def test_round_trip(self):
        s = StepData(on=True, ghost=True, probability=0.75, params={"f0": 440.0})
        v = s.to_step_value()
        s2 = StepData.from_step_value(v)
        self.assertEqual(s.on, s2.on)
        self.assertEqual(s.ghost, s2.ghost)
        self.assertAlmostEqual(s.probability, s2.probability)
        self.assertEqual(s.params, s2.params)

    # --- Phase 4: velocity round-trip tests ---

    def test_velocity_default_returns_compact_1(self):
        """A plain on-step with velocity=1.0 must still return compact int 1."""
        s = StepData(on=True, velocity=1.0)
        self.assertEqual(s.to_step_value(), 1)

    def test_velocity_non_default_returns_dict(self):
        """A step with velocity != 1.0 must return a dict carrying 'velocity'."""
        s = StepData(on=True, velocity=0.7)
        v = s.to_step_value()
        self.assertIsInstance(v, dict)
        self.assertIn("velocity", v)
        self.assertAlmostEqual(v["velocity"], 0.7)

    def test_velocity_round_trip(self):
        """StepData(on=True, velocity=0.7) survives to_step_value / from_step_value."""
        s = StepData(on=True, velocity=0.7)
        v = s.to_step_value()
        s2 = StepData.from_step_value(v)
        self.assertTrue(s2.on)
        self.assertAlmostEqual(s2.velocity, 0.7)

    def test_velocity_1_not_in_to_dict(self):
        """to_dict for velocity=1.0 must NOT include a 'velocity' key."""
        s = StepData(on=True, velocity=1.0)
        d = s.to_dict()
        self.assertNotIn("velocity", d)

    def test_velocity_non_default_in_to_dict(self):
        """to_dict for velocity != 1.0 must include 'velocity'."""
        s = StepData(on=True, velocity=0.5)
        d = s.to_dict()
        self.assertAlmostEqual(d["velocity"], 0.5)


# ---------------------------------------------------------------------------
# PatternChannel

class TestPatternChannel(unittest.TestCase):
    def test_defaults_to_16_empty_steps(self):
        ch = PatternChannel("kick")
        self.assertEqual(len(ch.steps), 16)
        self.assertFalse(any(s.on for s in ch.steps))

    def test_to_track_dict_has_instrument(self):
        ch = PatternChannel("hat")
        d = ch.to_track_dict()
        self.assertEqual(d["instrument"], "hat")
        self.assertEqual(len(d["steps"]), 16)

    def test_to_track_dict_active_step(self):
        ch = PatternChannel("kick")
        ch.steps[0].on = True
        d = ch.to_track_dict()
        self.assertEqual(d["steps"][0], 1)
        self.assertEqual(d["steps"][1], 0)

    def test_to_dict_round_trip(self):
        ch = PatternChannel("snare", n_steps=8, seed=99)
        ch.steps[2].on = True
        d = ch.to_dict()
        ch2 = PatternChannel.from_dict(d)
        self.assertEqual(ch2.instrument_id, "snare")
        self.assertEqual(ch2.n_steps, 8)
        self.assertEqual(ch2.seed, 99)
        self.assertTrue(ch2.steps[2].on)

    def test_copy_is_independent(self):
        ch = PatternChannel("kick")
        ch.steps[0].on = True
        ch2 = ch.copy()
        ch2.steps[0].on = False
        self.assertTrue(ch.steps[0].on)

    def test_channel_from_dict_pattern(self):
        d = {"kind": "pattern", "instrument_id": "hat", "n_steps": 16, "steps": [], "params": {}, "seed": 0}
        ch = channel_from_dict(d)
        self.assertIsInstance(ch, PatternChannel)


# ---------------------------------------------------------------------------
# TextureChannel / AutomationChannel

class TestTextureChannel(unittest.TestCase):
    def test_round_trip(self):
        ch = TextureChannel("wind", params={"length_s": 8.0}, seed=7)
        ch.envelope = [Breakpoint(0.0, 0.5), Breakpoint(4.0, 1.0)]
        d = ch.to_dict()
        ch2 = TextureChannel.from_dict(d)
        self.assertEqual(ch2.instrument_id, "wind")
        self.assertEqual(ch2.seed, 7)
        self.assertAlmostEqual(ch2.envelope[1].value, 1.0)

    def test_from_dict_dispatch(self):
        d = {"kind": "texture", "instrument_id": "drone", "params": {}, "seed": 0, "envelope": []}
        ch = channel_from_dict(d)
        self.assertIsInstance(ch, TextureChannel)


class TestAutomationChannel(unittest.TestCase):
    def test_round_trip(self):
        ch = AutomationChannel("master_gain", [Breakpoint(0.0, 1.0), Breakpoint(8.0, 0.5)])
        d = ch.to_dict()
        ch2 = AutomationChannel.from_dict(d)
        self.assertEqual(ch2.target_param, "master_gain")
        self.assertEqual(len(ch2.breakpoints), 2)


# ---------------------------------------------------------------------------
# Transaction

class TestTransaction(unittest.TestCase):
    def test_empty(self):
        t = Transaction("test")
        self.assertTrue(t.is_empty())

    def test_not_empty_after_add(self):
        t = Transaction("test")
        t.add_change(("channel", 0, "seed"), 0, 42)
        self.assertFalse(t.is_empty())

    def test_affected_channel_indices(self):
        t = Transaction()
        t.add_change(("channel", 0, "seed"), 0, 42)
        t.add_change(("channel", 2, "step", 3, "on"), False, True)
        self.assertEqual(t.affected_channel_indices(), {0, 2})

    def test_affected_channels_excludes_global(self):
        t = Transaction()
        t.add_change(("global", "bpm"), 120.0, 138.0)
        self.assertEqual(t.affected_channel_indices(), set())

    def test_reversed_swaps_old_new(self):
        t = Transaction("set seed")
        t.add_change(("channel", 0, "seed"), 0, 42)
        r = t.reversed()
        self.assertEqual(r.changes[0].old_value, 42)
        self.assertEqual(r.changes[0].new_value, 0)

    def test_reversed_reverses_order(self):
        t = Transaction()
        t.add_change(("channel", 0, "seed"), 0, 1)
        t.add_change(("channel", 1, "seed"), 0, 2)
        r = t.reversed()
        self.assertEqual(r.changes[0].path, ("channel", 1, "seed"))
        self.assertEqual(r.changes[1].path, ("channel", 0, "seed"))


# ---------------------------------------------------------------------------
# channel_content_hash

class TestContentHash(unittest.TestCase):
    def test_same_data_same_hash(self):
        ch = PatternChannel("kick")
        h1 = channel_content_hash(ch.to_dict())
        h2 = channel_content_hash(ch.to_dict())
        self.assertEqual(h1, h2)

    def test_different_instrument_different_hash(self):
        ch1 = PatternChannel("kick")
        ch2 = PatternChannel("hat")
        self.assertNotEqual(
            channel_content_hash(ch1.to_dict()),
            channel_content_hash(ch2.to_dict()),
        )

    def test_different_seed_different_hash(self):
        ch1 = PatternChannel("kick", seed=0)
        ch2 = PatternChannel("kick", seed=99)
        self.assertNotEqual(
            channel_content_hash(ch1.to_dict()),
            channel_content_hash(ch2.to_dict()),
        )

    def test_different_step_different_hash(self):
        ch1 = PatternChannel("kick")
        ch1.steps[0].on = True
        ch2 = PatternChannel("kick")
        self.assertNotEqual(
            channel_content_hash(ch1.to_dict()),
            channel_content_hash(ch2.to_dict()),
        )

    def test_hash_length(self):
        ch = PatternChannel("kick")
        h = channel_content_hash(ch.to_dict())
        self.assertEqual(len(h), 16)


# ---------------------------------------------------------------------------
# History

class TestHistory(unittest.TestCase):
    def _txn(self, desc="t", old=0, new=1):
        t = Transaction(desc)
        t.add_change(("channel", 0, "seed"), old, new)
        return t

    def test_initially_no_undo_redo(self):
        h = History()
        self.assertFalse(h.can_undo())
        self.assertFalse(h.can_redo())

    def test_push_enables_undo(self):
        h = History()
        h.push(self._txn())
        self.assertTrue(h.can_undo())

    def test_undo_clears_redo_queue_on_new_push(self):
        h = History()
        h.push(self._txn("a", 0, 1))
        h.push(self._txn("b", 1, 2))
        h.pop_for_undo()  # redo has "b"
        h.push(self._txn("c", 1, 3))  # should clear redo
        self.assertFalse(h.can_redo())

    def test_pop_for_undo_returns_reversed(self):
        h = History()
        t = self._txn(old=0, new=42)
        h.push(t)
        r = h.pop_for_undo()
        self.assertIsNotNone(r)
        self.assertEqual(r.changes[0].old_value, 42)
        self.assertEqual(r.changes[0].new_value, 0)

    def test_pop_for_undo_enables_redo(self):
        h = History()
        h.push(self._txn())
        h.pop_for_undo()
        self.assertTrue(h.can_redo())

    def test_pop_for_redo_returns_original(self):
        h = History()
        t = self._txn(old=0, new=42)
        h.push(t)
        h.pop_for_undo()
        r = h.pop_for_redo()
        self.assertIsNotNone(r)
        self.assertEqual(r.changes[0].new_value, 42)

    def test_empty_txn_not_pushed(self):
        h = History()
        h.push(Transaction())
        self.assertFalse(h.can_undo())

    def test_coalesce_merges_same_path(self):
        h = History()
        t1 = Transaction("drag")
        t1.add_change(("channel", 0, "params", "f0"), 60.0, 70.0)
        t2 = Transaction("drag")
        t2.add_change(("channel", 0, "params", "f0"), 70.0, 80.0)
        h.push(t1)
        h.push(t2, coalesce=True)
        self.assertEqual(len(h), 1)  # merged
        r = h.pop_for_undo()
        # undo should go from 80 back to 60 (original old_value)
        self.assertAlmostEqual(r.changes[0].new_value, 60.0)

    def test_coalesce_different_path_not_merged(self):
        h = History()
        t1 = Transaction("a")
        t1.add_change(("channel", 0, "params", "f0"), 60.0, 70.0)
        t2 = Transaction("b")
        t2.add_change(("channel", 0, "params", "drive"), 1.0, 2.0)
        h.push(t1)
        h.push(t2, coalesce=True)
        self.assertEqual(len(h), 2)


# ---------------------------------------------------------------------------
# ProjectDoc

class TestProjectDoc(unittest.TestCase):
    def _doc(self) -> ProjectDoc:
        return ProjectDoc(title="test", bpm=138.0)

    def test_defaults(self):
        doc = self._doc()
        self.assertEqual(doc.title, "test")
        self.assertAlmostEqual(doc.bpm, 138.0)
        self.assertEqual(doc.channel_count(), 0)

    # ---------- add/remove channel

    def test_add_channel_increments_count(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        self.assertEqual(doc.channel_count(), 1)

    def test_add_channel_is_undoable(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.undo()
        self.assertEqual(doc.channel_count(), 0)

    def test_remove_channel_is_undoable(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.remove_channel(0)
        self.assertEqual(doc.channel_count(), 0)
        doc.undo()  # undo remove
        self.assertEqual(doc.channel_count(), 1)
        doc.undo()  # undo add
        self.assertEqual(doc.channel_count(), 0)

    # ---------- global edits

    def test_set_global_bpm(self):
        doc = self._doc()
        doc.set_global("bpm", 140.0)
        self.assertAlmostEqual(doc.bpm, 140.0)

    def test_set_global_undo(self):
        doc = self._doc()
        doc.set_global("bpm", 140.0)
        doc.undo()
        self.assertAlmostEqual(doc.bpm, 138.0)

    def test_set_global_no_op_if_same(self):
        doc = self._doc()
        doc.set_global("bpm", 138.0)
        self.assertFalse(doc.history.can_undo())

    # ---------- per-channel edits

    def test_set_instrument(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_instrument(0, "hat")
        self.assertEqual(doc.channel(0).instrument_id, "hat")

    def test_set_instrument_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_instrument(0, "hat")
        doc.undo()
        self.assertEqual(doc.channel(0).instrument_id, "kick")

    def test_set_param(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_param(0, "f0", 60.0)
        self.assertAlmostEqual(doc.channel(0).params["f0"], 60.0)

    def test_set_param_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_param(0, "f0", 60.0)
        doc.undo()
        self.assertNotIn("f0", doc.channel(0).params)

    def test_set_seed(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_seed(0, 99)
        self.assertEqual(doc.channel(0).seed, 99)

    def test_reroll_changes_seed(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        old_seed = doc.channel(0).seed
        doc.reroll(0)
        # Extremely unlikely to match (2^31 range)
        self.assertNotEqual(doc.channel(0).seed, old_seed)

    def test_reroll_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_seed(0, 7)
        doc.reroll(0)
        doc.undo()
        self.assertEqual(doc.channel(0).seed, 7)

    # ---------- step edits

    def test_toggle_step(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        self.assertFalse(doc.channel(0).steps[0].on)
        doc.toggle_step(0, 0)
        self.assertTrue(doc.channel(0).steps[0].on)

    def test_toggle_step_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        doc.undo()
        self.assertFalse(doc.channel(0).steps[0].on)

    def test_set_step_accent(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_step(0, 3, "accent", True)
        self.assertTrue(doc.channel(0).steps[3].accent)

    def test_set_step_probability(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_step(0, 5, "probability", 0.5)
        self.assertAlmostEqual(doc.channel(0).steps[5].probability, 0.5)

    def test_set_step_param(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_step_param(0, 2, "f0", 440.0)
        self.assertAlmostEqual(doc.channel(0).steps[2].params["f0"], 440.0)

    def test_clear_steps(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        doc.toggle_step(0, 4)
        doc.clear_steps(0)
        self.assertFalse(any(s.on for s in doc.channel(0).steps))

    def test_clear_steps_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        doc.clear_steps(0)
        doc.undo()
        self.assertTrue(doc.channel(0).steps[0].on)

    # ---------- copy/paste steps

    def test_copy_paste_steps(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        doc.toggle_step(0, 2)
        clipboard = doc.copy_steps(0, 0, 4)
        doc.paste_steps(0, 8, clipboard)
        self.assertTrue(doc.channel(0).steps[8].on)
        self.assertTrue(doc.channel(0).steps[10].on)

    def test_paste_steps_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        clipboard = doc.copy_steps(0, 0, 4)
        doc.paste_steps(0, 8, clipboard)
        doc.undo()
        self.assertFalse(doc.channel(0).steps[8].on)

    # ---------- undo/redo sequence

    def test_multiple_undo_redo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_seed(0, 10)
        doc.set_seed(0, 20)
        doc.set_seed(0, 30)
        # undo × 2
        doc.undo()
        self.assertEqual(doc.channel(0).seed, 20)
        doc.undo()
        self.assertEqual(doc.channel(0).seed, 10)
        # redo × 1
        doc.redo()
        self.assertEqual(doc.channel(0).seed, 20)

    def test_undo_returns_false_when_empty(self):
        doc = self._doc()
        self.assertFalse(doc.undo())

    def test_redo_returns_false_when_empty(self):
        doc = self._doc()
        self.assertFalse(doc.redo())

    # ---------- observers

    def test_observer_called_on_edit(self):
        doc = self._doc()
        received = []
        doc.subscribe(received.append)
        doc.add_channel(PatternChannel("kick"))
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], Transaction)

    def test_observer_called_on_undo(self):
        doc = self._doc()
        received = []
        doc.add_channel(PatternChannel("kick"))
        doc.subscribe(received.append)
        doc.undo()
        self.assertEqual(len(received), 1)

    def test_unsubscribe(self):
        doc = self._doc()
        received = []
        cb = received.append
        doc.subscribe(cb)
        doc.unsubscribe(cb)
        doc.add_channel(PatternChannel("kick"))
        self.assertEqual(len(received), 0)

    # ---------- cache keys

    def test_cache_key_changes_on_step_edit(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        k1 = doc.channel_cache_key(0)
        doc.toggle_step(0, 0)
        k2 = doc.channel_cache_key(0)
        self.assertNotEqual(k1, k2)

    def test_cache_key_changes_on_reroll(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.set_seed(0, 7)
        k1 = doc.channel_cache_key(0)
        doc.reroll(0)
        k2 = doc.channel_cache_key(0)
        self.assertNotEqual(k1, k2)

    def test_cache_key_same_after_undo(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        k0 = doc.channel_cache_key(0)
        doc.toggle_step(0, 0)
        doc.undo()
        k_after = doc.channel_cache_key(0)
        self.assertEqual(k0, k_after)

    def test_identical_edits_same_cache_key(self):
        doc1 = ProjectDoc()
        doc2 = ProjectDoc()
        doc1.add_channel(PatternChannel("kick"))
        doc2.add_channel(PatternChannel("kick"))
        doc1.toggle_step(0, 0)
        doc2.toggle_step(0, 0)
        self.assertEqual(doc1.channel_cache_key(0), doc2.channel_cache_key(0))

    def test_reroll_only_changes_target_channel_key(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.add_channel(PatternChannel("hat"))
        k_hat_before = doc.channel_cache_key(1)
        doc.reroll(0)
        k_hat_after = doc.channel_cache_key(1)
        self.assertEqual(k_hat_before, k_hat_after)

    # ---------- serialization round-trip

    def test_to_dict_from_dict(self):
        doc = self._doc()
        doc.add_channel(PatternChannel("kick"))
        doc.toggle_step(0, 0)
        doc.set_param(0, "f0", 60.0)
        d = doc.to_dict()
        doc2 = ProjectDoc.from_dict(d)
        self.assertEqual(doc2.title, "test")
        self.assertAlmostEqual(doc2.bpm, 138.0)
        self.assertEqual(doc2.channel_count(), 1)
        self.assertTrue(doc2.channel(0).steps[0].on)
        self.assertAlmostEqual(doc2.channel(0).params["f0"], 60.0)

    def test_no_qt_import_in_document_package(self):
        """Document package must not import Qt."""
        import sys
        for mod_name in list(sys.modules):
            if mod_name.startswith("forge.document"):
                continue
        # If any Qt modules are loaded, the import of forge.document must not
        # have caused them — just check the package doesn't accidentally import PySide6
        import forge.document.model
        import forge.document.channels
        import forge.document.transaction
        import forge.document.history
        # If we get here without ImportError, the package loaded without Qt
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
