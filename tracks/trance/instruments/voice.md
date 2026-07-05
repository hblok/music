# The Voice (TTS)

Speech and singing synthesis. `hybrid_note` is kept as reference only — the approach is a dead end.

## `get_voice` — spoken-word drop

**Source:** `ungeschrieben.py:get_voice`  
**Character:** edge-tts, cache-first to `/workspace/music/samples/`, sampler pitch-down ×0.94, dropped ONCE, VOICE_GAIN knob documented in-script

```python
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
```

## `hybrid_note` — hybrid sung voice (dead end)

**Source:** `unsung.py:hybrid_note`  
**Character:** consonant-graft + formant vowel at perfect pitch — **recorded dead end** (pitch-perfect but uncanny). Don't rebuild without a genuinely new naturalness idea.

```python
def hybrid_note(text, midi, beats):
    """One sung note: TTS onset/coda grafted onto the pitch-held vowel.
    Returns (audio, measured_f0_of_the_held_vowel)."""
    f_t = midi_to_hz(midi)
    p = SYL[text]
    dur = beats * BEAT * (0.92 if beats <= 1 else 0.97)
    tts = get_syllable(text, f_t)
    note = np.zeros(int((dur + 0.35) * SR))
    pos = 0
    if p["onset"] > 0:
        on = tts[: int(p["onset"] * SR)].copy()
        on[-XF:] *= np.linspace(1, 0, XF)
        note[: len(on)] += on
        pos = max(0, len(on) - XF)
    vow = vowel_note(f_t, dur - pos / SR, p["v1"], p["v2"])
    xfade_place(note, vow * 0.9, pos, XF)
    if p["coda"] > 0:
        co = tts[-int(p["coda"] * SR):].copy()
        co[:XF] *= np.linspace(0, 1, XF)
        k2 = int(0.02 * SR)
        co[-k2:] *= np.linspace(1, 0, k2)
        i0 = int(dur * SR) - len(co) // 3
        note[i0:i0 + len(co)] += co * 0.8 * np.max(np.abs(vow))
    vs = int((pos / SR + 0.10) * SR)
    ve = int(min(dur - 0.05, pos / SR + 0.40) * SR)
    f_m = estimate_f0(note[vs:max(ve, vs + int(0.1 * SR))])
    return note, f_m
```
