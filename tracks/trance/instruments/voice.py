"""The trance spoken-word drop (TTS).

Extracted from the trance track scripts (which are unchanged):
  - `get_voice` <- `ungeschrieben.py:get_voice` -- OWNED by ungeschrieben.
    edge-tts, cache-first to `VOICE_CACHE`, hardware-sampler pitch-down
    (x0.94), dropped ONCE per track.  Set `VOICE_GAIN = 0` to silence.

Needs network + `edge_tts` + `ffmpeg` on the first call only (the WAV is
cached); with neither cache nor network it degrades to
`(None, "unavailable ...")` -- "rendered instrumental" -- exactly like the
script.  Pass-through constants (`VOICE_TEXT`, `VOICE_ID`, `VOICE_CACHE`)
are module globals copied from the script; edit them here for a new line.

Deliberately NOT extracted: `unsung.py:hybrid_note` and the rest of the
hybrid sung voice -- a recorded DEAD END (pitch-perfect but uncanny; see
`../CLAUDE.md`), as is `unsung_probe.py`.  TTS *singing* is not to be
retried without a genuinely new idea.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import wave

import numpy as np
from scipy import signal

from _common import SR

VOICE_GAIN = 1.0
VOICE_TEXT = "Die Zukunft ist ungeschrieben."
VOICE_ID = "de-DE-KatjaNeural"        # edge-tts neural voice (female, dry)
VOICE_CACHE = "/workspace/music/samples/ungeschrieben_voice.wav"


def get_voice():
    if VOICE_GAIN <= 0:
        return None, "silenced (VOICE_GAIN=0)"
    if not os.path.exists(VOICE_CACHE):
        try:
            import edge_tts
            os.makedirs(os.path.dirname(VOICE_CACHE), exist_ok=True)
            tmp = VOICE_CACHE + ".mp3"

            async def go():
                await edge_tts.Communicate(VOICE_TEXT, voice=VOICE_ID).save(tmp)

            asyncio.run(go())
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                            "-ar", str(SR), "-ac", "1", VOICE_CACHE], check=True)
            os.remove(tmp)
        except Exception as e:                    # no net, no cache: instrumental
            return None, f"unavailable ({type(e).__name__}) — rendered instrumental"
    with wave.open(VOICE_CACHE, "rb") as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    v /= np.max(np.abs(v)) + 1e-12
    # hardware-sampler pitch-down: resample by 0.94 (~ -1 semitone, 6 % slower)
    idx = np.arange(0, len(v) - 1, 0.94)
    v = v[idx.astype(int)]
    v = signal.sosfilt(signal.butter(2, 6000, "low", fs=SR, output="sos"), v)
    v = signal.sosfilt(signal.butter(2, 120, "high", fs=SR, output="sos"), v)
    return v / (np.max(np.abs(v)) + 1e-12), "placed once at bar 86"


if __name__ == "__main__":
    # Network-dependent: audition only the contract, never fail offline.
    voice, status = get_voice()
    print(f"get_voice -> {status}")
    if voice is not None:
        assert np.isfinite(voice).all() and np.max(np.abs(voice)) <= 1.0 + 1e-9
    print("voice.py: contract OK")
