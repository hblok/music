"""Phase 0 tests: inventory doc exists; collect_stats works on synthetic WAV."""

import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

# repo root is two levels up from forge/tests/
REPO_ROOT = Path(__file__).parent.parent.parent


class TestInventory(unittest.TestCase):
    def test_inventory_exists(self):
        inv = REPO_ROOT / "forge" / "INVENTORY.md"
        self.assertTrue(inv.exists(), f"INVENTORY.md not found at {inv}")

    def test_inventory_has_core_entries(self):
        inv = REPO_ROOT / "forge" / "INVENTORY.md"
        text = inv.read_text()
        for name in ("midi_to_hz", "fade", "slow_noise", "make_reverb_ir",
                     "reverb", "add_at", "commit", "bar_t", "glide_curve"):
            self.assertIn(name, text, f"Expected '{name}' in INVENTORY.md")

    def test_inventory_has_instrument_families(self):
        inv = REPO_ROOT / "forge" / "INVENTORY.md"
        text = inv.read_text()
        for family in ("textures", "percussion", "strings", "voices", "bass", "fx"):
            self.assertIn(family, text, f"Expected instrument family '{family}' in INVENTORY.md")

    def test_reference_readme_exists(self):
        readme = REPO_ROOT / "reference" / "README.md"
        self.assertTrue(readme.exists(), f"reference/README.md not found at {readme}")


class TestCollectStats(unittest.TestCase):
    """collect_stats.wav_stats on a synthetic 16-bit stereo WAV."""

    @classmethod
    def _write_test_wav(cls, path: Path, sr: int, duration: float, amplitude: float) -> None:
        n_frames = int(sr * duration)
        t = np.arange(n_frames) / sr
        # 440 Hz sine wave, stereo
        sig = (np.sin(2 * np.pi * 440 * t) * amplitude).astype(np.float64)
        pcm = (np.column_stack([sig, sig]) * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.wav = self.tmp / "test.wav"
        self._write_test_wav(self.wav, 44100, 1.0, 0.5)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _stats(self):
        from forge.tools.collect_stats import wav_stats
        return wav_stats(self.wav)

    def test_duration(self):
        s = self._stats()
        self.assertAlmostEqual(s["duration"], 1.0, places=2)

    def test_sr(self):
        self.assertEqual(self._stats()["sr"], 44100)

    def test_n_channels(self):
        self.assertEqual(self._stats()["n_channels"], 2)

    def test_peak_approx(self):
        s = self._stats()
        # sine at amplitude 0.5 → peak ≈ 0.5 (with int16 rounding)
        self.assertAlmostEqual(s["peak"], 0.5, delta=0.002)

    def test_rms_approx(self):
        s = self._stats()
        # sine RMS = amplitude / sqrt(2) ≈ 0.354
        self.assertAlmostEqual(s["rms"], 0.5 / (2 ** 0.5), delta=0.005)

    def test_section_rms_count(self):
        s = self._stats()
        self.assertEqual(len(s["section_rms"]), 8)

    def test_section_rms_roughly_uniform(self):
        s = self._stats()
        rms_vals = s["section_rms"]
        mean_rms = sum(rms_vals) / len(rms_vals)
        for v in rms_vals:
            self.assertAlmostEqual(v, mean_rms, delta=mean_rms * 0.05)

    def test_collect_writes_json(self):
        from forge.tools.collect_stats import collect
        out = self.tmp / "stats.json"
        result = collect(self.tmp, out)
        self.assertTrue(out.exists())
        data = json.loads(out.read_text())
        self.assertIn("test.wav", data)
        self.assertAlmostEqual(data["test.wav"]["duration"], 1.0, places=2)

    def test_collect_empty_dir(self):
        from forge.tools.collect_stats import collect
        empty = self.tmp / "empty"
        empty.mkdir()
        out = self.tmp / "empty_stats.json"
        result = collect(empty, out)
        self.assertEqual(result, {})

    def test_missing_wav_graceful(self):
        """wav_stats on a non-existent path raises an informative error."""
        from forge.tools.collect_stats import wav_stats
        with self.assertRaises(Exception):
            wav_stats(self.tmp / "no_such_file.wav")


if __name__ == "__main__":
    unittest.main()
