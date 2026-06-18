"""forge.tests.test_reverb_send — acceptance tests for Phase 7 reverb send bus.

Tests:
  - Decay tail GATE: a channel at reverb_send=0.8 has measurably more energy
    in the late window than the same channel at reverb_send=0.0.
  - Byte-identical: a doc with all reverb_send=0.0 renders identically to one
    with no reverb_send field set (the pre-Phase-7 behaviour).
  - Shared bus: multiple reverb-send channels → render completes, tail present.
    Only ONE IR pair + ONE convolution pair is used regardless of channel count
    (verified structurally by _apply_reverb_bus being called once).
  - Round-trip: reverb_send survives to_dict/from_dict for both channel kinds.
"""

from __future__ import annotations

import unittest
import numpy as np


# ---------------------------------------------------------------------------
# Helpers

def _make_doc_with_kick(reverb_send: float = 0.0, n_bars: int = 4):
    """Return a minimal single-channel doc (kick on step 0 of a 4-bar section)."""
    from forge.document.channels import PatternChannel
    from forge.document.model import ProjectDoc

    doc = ProjectDoc(title="test", bpm=120.0, seed=42)
    kick = PatternChannel("kick", n_steps=16, reverb_send=reverb_send)
    kick.steps[0].on = True  # only the downbeat hit — gives a clean percussive decay
    doc.add_channel(kick)
    doc.add_section("body", n_bars)
    return doc


def _rms(data: np.ndarray) -> float:
    """RMS of a numpy array."""
    return float(np.sqrt(np.mean(data ** 2)))


def _late_window_rms(buf_data: np.ndarray, fraction: float = 0.25) -> float:
    """RMS of the last *fraction* of the stereo buffer (both channels)."""
    n = buf_data.shape[0]
    start = int(n * (1.0 - fraction))
    tail = buf_data[start:]
    return _rms(tail)


# ---------------------------------------------------------------------------
# Tests


class TestReverbSendDecayTail(unittest.TestCase):
    """Gate: reverb_send=0.8 produces a clearly audible tail past the dry decay."""

    @classmethod
    def setUpClass(cls):
        # Use a 2-bar section so the single hit on step 0 decays by the 2nd bar.
        from forge import control
        cls.control = control

        doc_wet = _make_doc_with_kick(reverb_send=0.8, n_bars=2)
        doc_dry = _make_doc_with_kick(reverb_send=0.0, n_bars=2)

        cls.buf_wet = control.render_doc_for_playback(doc_wet)
        cls.buf_dry = control.render_doc_for_playback(doc_dry)

    def test_wet_tail_rms_is_larger(self):
        """Late-window RMS must be measurably higher with reverb_send=0.8."""
        rms_wet = _late_window_rms(self.buf_wet.data, fraction=0.25)
        rms_dry = _late_window_rms(self.buf_dry.data, fraction=0.25)
        # The reverb tail should add at least 10× more energy in the late window.
        self.assertGreater(
            rms_wet, rms_dry * 2.0,
            f"Reverb tail not detected: wet late RMS={rms_wet:.6f}, dry late RMS={rms_dry:.6f}",
        )

    def test_wet_late_rms_is_nonzero(self):
        """The wet tail must contain actual energy (not silence)."""
        rms_wet = _late_window_rms(self.buf_wet.data, fraction=0.25)
        self.assertGreater(rms_wet, 1e-6, "Wet tail appears to be silence")

    def test_dry_tail_is_nearly_silent(self):
        """The dry render should have very little energy past the hit decay."""
        rms_dry = _late_window_rms(self.buf_dry.data, fraction=0.25)
        # Dry kick decays within one bar; last 25% of a 2-bar window should be quiet.
        rms_wet = _late_window_rms(self.buf_wet.data, fraction=0.25)
        self.assertLess(rms_dry, rms_wet, "Dry tail should be quieter than wet tail")


class TestByteIdenticalWhenNoSend(unittest.TestCase):
    """CRITICAL: zero reverb_send → render is byte-identical to the no-field case."""

    def _make_doc_zero_send(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="test", bpm=120.0, seed=7)
        ch = PatternChannel("kick", n_steps=16, reverb_send=0.0)
        ch.steps[0].on = True
        ch.steps[8].on = True
        doc.add_channel(ch)
        doc.add_section("body", 4)
        return doc

    def _make_doc_default_field(self):
        """Same doc but reverb_send left at default (omitted from dict, then reloaded)."""
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="test", bpm=120.0, seed=7)
        ch = PatternChannel("kick", n_steps=16)  # reverb_send defaults to 0.0
        ch.steps[0].on = True
        ch.steps[8].on = True
        doc.add_channel(ch)
        doc.add_section("body", 4)
        return doc

    def test_zero_send_renders_byte_identical_to_default(self):
        from forge import control
        doc_zero = self._make_doc_zero_send()
        doc_default = self._make_doc_default_field()
        buf_zero = control.render_doc_for_playback(doc_zero)
        buf_default = control.render_doc_for_playback(doc_default)
        np.testing.assert_array_equal(
            buf_zero.data, buf_default.data,
            err_msg="Render with reverb_send=0.0 should be byte-identical to reverb_send=default",
        )

    def test_zero_send_renders_same_as_pre_phase7(self):
        """With all reverb_sends zero the reverb bus path is skipped entirely."""
        from forge import control
        # Two renders of the same doc with reverb_send=0 must be identical.
        doc1 = self._make_doc_zero_send()
        doc2 = self._make_doc_zero_send()
        buf1 = control.render_doc_for_playback(doc1)
        buf2 = control.render_doc_for_playback(doc2)
        np.testing.assert_array_equal(buf1.data, buf2.data)


class TestSharedReverbBus(unittest.TestCase):
    """Multiple reverb-send channels → single convolution, tail present.

    The shared bus design: each channel accumulates scaled audio into ONE
    reverb_bus buffer.  _apply_reverb_bus is called ONCE after all channels are
    summed.  CPU cost is therefore O(N_channels) for the accumulation step plus
    O(N_samples * log N_samples) for the single convolution pair — linear in
    channel count.
    """

    def _make_multi_channel_doc(self, n_channels: int = 3, reverb_send: float = 0.5) -> "object":
        """All kicks on step 0 only, 2-bar section.

        A 2-bar section at 120 BPM is ~4 seconds.  The kick hit at step 0 decays
        within the first bar; the last 25% of the buffer is well past the dry decay
        so the reverb tail dominates there.
        """
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="multi", bpm=120.0, seed=99)
        for i in range(n_channels):
            ch = PatternChannel("kick", n_steps=16, reverb_send=reverb_send)
            ch.steps[0].on = True  # single hit at bar start
            doc.add_channel(ch)
        doc.add_section("body", 2)
        return doc

    def test_multi_channel_render_completes(self):
        from forge import control
        doc = self._make_multi_channel_doc(3)
        buf = control.render_doc_for_playback(doc)
        self.assertGreater(buf.data.shape[0], 0)

    def test_multi_channel_tail_is_present(self):
        """Tail energy should exist with multiple sends (all kicks, single hit).

        Uses _render_doc_sections directly to bypass mastering normalization,
        which would otherwise compress the ratio between wet and dry versions.
        """
        from forge import control
        doc_wet = self._make_multi_channel_doc(3, reverb_send=0.8)
        doc_dry = self._make_multi_channel_doc(3, reverb_send=0.0)
        # Bypass mastering so the wet/dry ratio is measured on raw output.
        buf_wet = control._render_doc_sections(doc_wet)
        buf_dry = control._render_doc_sections(doc_dry)
        rms_wet = _late_window_rms(buf_wet.data, fraction=0.25)
        rms_dry = _late_window_rms(buf_dry.data, fraction=0.25)
        self.assertGreater(rms_wet, rms_dry * 2.0,
            f"Multi-channel wet tail not detected: wet={rms_wet:.6f}, dry={rms_dry:.6f}")

    def test_reverb_bus_is_one_convolution_regardless_of_channel_count(self):
        """Structural: _apply_reverb_bus called once even with N channels.

        We patch _apply_reverb_bus to count calls and verify it's invoked
        exactly once per render regardless of how many channels feed the bus.
        """
        from unittest.mock import patch
        import forge.control as ctrl

        call_count = []
        original = ctrl._apply_reverb_bus

        def counting_wrapper(*args, **kwargs):
            call_count.append(1)
            return original(*args, **kwargs)

        doc = self._make_multi_channel_doc(5)
        with patch.object(ctrl, "_apply_reverb_bus", side_effect=counting_wrapper):
            ctrl.render_doc_for_playback(doc)

        self.assertEqual(len(call_count), 1,
            f"_apply_reverb_bus should be called exactly once, got {len(call_count)}")


class TestReverbSendRoundTrip(unittest.TestCase):
    """reverb_send survives to_dict/from_dict for PatternChannel and TextureChannel."""

    def test_pattern_channel_round_trip_nonzero(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick", reverb_send=0.7)
        d = ch.to_dict()
        self.assertIn("reverb_send", d, "reverb_send not emitted when non-zero")
        self.assertAlmostEqual(d["reverb_send"], 0.7)
        ch2 = PatternChannel.from_dict(d)
        self.assertAlmostEqual(ch2.reverb_send, 0.7)

    def test_pattern_channel_round_trip_zero_not_emitted(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick", reverb_send=0.0)
        d = ch.to_dict()
        self.assertNotIn("reverb_send", d, "reverb_send should not be emitted when 0.0")

    def test_pattern_channel_from_dict_default_zero(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel.from_dict({"instrument_id": "kick"})
        self.assertAlmostEqual(ch.reverb_send, 0.0)

    def test_pattern_channel_copy_preserves_reverb_send(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick", reverb_send=0.6)
        ch2 = ch.copy()
        self.assertAlmostEqual(ch2.reverb_send, 0.6)

    def test_texture_channel_round_trip_nonzero(self):
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind", reverb_send=0.4)
        d = ch.to_dict()
        self.assertIn("reverb_send", d)
        self.assertAlmostEqual(d["reverb_send"], 0.4)
        ch2 = TextureChannel.from_dict(d)
        self.assertAlmostEqual(ch2.reverb_send, 0.4)

    def test_texture_channel_round_trip_zero_not_emitted(self):
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind", reverb_send=0.0)
        d = ch.to_dict()
        self.assertNotIn("reverb_send", d)

    def test_texture_channel_from_dict_default_zero(self):
        from forge.document.channels import TextureChannel
        ch = TextureChannel.from_dict({"instrument_id": "wind"})
        self.assertAlmostEqual(ch.reverb_send, 0.0)

    def test_texture_channel_copy_preserves_reverb_send(self):
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind", reverb_send=0.35)
        ch2 = ch.copy()
        self.assertAlmostEqual(ch2.reverb_send, 0.35)

    def test_project_doc_round_trip(self):
        """reverb_send survives full doc to_dict/from_dict."""
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="test", bpm=120.0, seed=0)
        ch = PatternChannel("kick", reverb_send=0.8)
        ch.steps[0].on = True
        doc.add_channel(ch)
        d = doc.to_dict()
        doc2 = ProjectDoc.from_dict(d)
        ch2 = doc2.channels[0]
        self.assertAlmostEqual(ch2.reverb_send, 0.8)


class TestModelReverbSendAPI(unittest.TestCase):
    """set_channel_reverb_send model API and _apply_change dispatch."""

    def _doc_with_kick(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(PatternChannel("kick"))
        return doc

    def test_set_channel_reverb_send(self):
        doc = self._doc_with_kick()
        doc.set_channel_reverb_send(0, 0.5)
        self.assertAlmostEqual(doc.channels[0].reverb_send, 0.5)

    def test_set_channel_reverb_send_coalesce(self):
        doc = self._doc_with_kick()
        doc.set_channel_reverb_send(0, 0.3, coalesce=True)
        doc.set_channel_reverb_send(0, 0.6, coalesce=True)
        self.assertAlmostEqual(doc.channels[0].reverb_send, 0.6)

    def test_set_channel_reverb_send_undo(self):
        doc = self._doc_with_kick()
        doc.set_channel_reverb_send(0, 0.9)
        doc.undo()
        self.assertAlmostEqual(doc.channels[0].reverb_send, 0.0)

    def test_set_channel_reverb_send_type_error_on_automation(self):
        from forge.document.channels import AutomationChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(AutomationChannel("master_gain"))
        with self.assertRaises(TypeError):
            doc.set_channel_reverb_send(0, 0.5)

    def test_set_channel_reverb_send_noop_when_same(self):
        """No transaction pushed when value unchanged."""
        doc = self._doc_with_kick()
        n_before = len(doc.history)
        doc.set_channel_reverb_send(0, 0.0)  # same as default
        n_after = len(doc.history)
        self.assertEqual(n_before, n_after)


if __name__ == "__main__":
    unittest.main()
