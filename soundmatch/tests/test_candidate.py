"""Tests for soundmatch.core.candidate — render_phrase determinism and layers."""
from __future__ import annotations

import unittest

from forge.core.buffer import AudioBuffer
from soundmatch.core.candidate import render_phrase
from soundmatch.core.phrase import Note, Phrase


def _simple_phrase() -> Phrase:
    """A minimal phrase with 2 notes."""
    return Phrase(
        bpm=120,
        length_s=1.0,
        notes=[Note(t=0.0, midi=[60]), Note(t=0.5, midi=[64])],
        loop=False,
    )


class TestRenderPhraseDeterminism(unittest.TestCase):
    """Same seed → identical AudioBuffer."""

    def test_same_seed_same_output(self):
        phrase = _simple_phrase()
        params = {"midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        buf1 = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=44100)
        buf2 = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=44100)
        self.assertEqual(buf1.data.shape, buf2.data.shape)
        self.assertTrue((buf1.data == buf2.data).all(),
                        "Same seed should produce identical buffers")

    def test_different_seed_different_output(self):
        phrase = _simple_phrase()
        params = {"midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        buf1 = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=44100)
        buf2 = render_phrase(phrase, "synth_brass", params, [], seed=99, sr=44100)
        self.assertFalse((buf1.data == buf2.data).all(),
                         "Different seeds should produce different buffers")


class TestRenderPhraseOutput(unittest.TestCase):
    """Basic output shape and type checks."""

    def test_returns_audio_buffer(self):
        phrase = _simple_phrase()
        params = {"midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        buf = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=44100)
        self.assertIsInstance(buf, AudioBuffer)

    def test_buffer_length_matches_phrase(self):
        sr = 44100
        phrase = Phrase(bpm=120, length_s=2.0, notes=[Note(t=0.0, midi=[60])], loop=False)
        params = {"midi": 60, "duration": 2.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        buf = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=sr)
        expected = int(2.0 * sr)
        self.assertEqual(len(buf.data), expected)

    def test_stereo_output(self):
        phrase = _simple_phrase()
        params = {"midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        buf = render_phrase(phrase, "synth_brass", params, [], seed=42, sr=44100)
        self.assertEqual(buf.data.ndim, 2)
        self.assertEqual(buf.data.shape[1], 2)


class TestRenderPhraseLayers(unittest.TestCase):
    """Test that additional layers are summed."""

    def test_layers_produce_output(self):
        phrase = _simple_phrase()
        params = {"midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
                  "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
                  "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
                  "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18}
        # Add a hat layer for the snap
        hat_params = {"f0": 8000.0, "decay": 0.05}
        buf = render_phrase(phrase, "synth_brass", params,
                            [("hat", hat_params)], seed=42, sr=44100)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0.0, "Layered render should produce non-silent output")


class TestRenderPhraseUnknownInstrument(unittest.TestCase):
    """Graceful handling of unknown instrument IDs."""

    def test_unknown_instrument_produces_silence(self):
        phrase = _simple_phrase()
        buf = render_phrase(phrase, "nonexistent_instrument", {}, [], seed=42, sr=44100)
        self.assertAlmostEqual(buf.peak(), 0.0, places=6,
                               msg="Unknown instrument should produce silence")


if __name__ == "__main__":
    unittest.main()
