# Leads

Lead voice functions. The warm detuned saw is the canonical template — every other entry is a deliberate variation.

## `lead_phrase` — warm detuned saw lead (canonical)

**Source:** `lost_v6.py:lead_phrase`  
**Character:** THE warm lead: 3 saws det ±0.4 %, 1/k**1.3, sine sub 0.3, LP 2600–2800; the refrain/duet voice

```python
def lead_phrase(notes, lowpass=2800, detune=(0.996, 1.0, 1.004), sub=0.3):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vibe = 1.0 + 0.003 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    K = max(3, int(5000 / np.max(f)))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate(detune):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.4               # rolled-off = warm
        pan = (j / (len(detune) - 1) - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    ph0 = 2 * np.pi * np.cumsum(f * vibe) / SR
    body = np.sin(ph0 / 2.0) * sub                       # sub octave for warmth
    L += body
    R += body
    env = np.minimum(np.clip(tt / 0.10, 0, 1), np.clip((total + 0.5 - tt) / 1.4, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak
```

## `lead_phrase` — reed lead + ping-pong — owned by nachtkind

**Source:** `nachtkind_v3.py:lead_phrase`  
**Character:** soaring duet-over-piano voice, dotted-8th ping-pong delay, octave shimmer

```python
def lead_phrase(notes):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.06)
    vib = 1.0 + 0.003 * np.sin(2 * np.pi * 5.0 * tt) * np.clip(tt / 1.8, 0, 1)
    K = max(3, int(7000 / np.max(f_curve)))

    def reed(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.3
        return v

    base = reed(1.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve * vib) / SR)
    vL = base + reed(0.9965) + 0.30 * body
    vR = base + reed(1.0038) + 0.30 * body
    env = np.minimum(np.clip(tt / 0.6, 0, 1),
                     np.clip((total + 0.8 - tt) / 1.8, 0, 1))
    sos_w = signal.butter(2, 2600, "low", fs=SR, output="sos")
    vL = np.tanh(0.8 * signal.sosfilt(sos_w, vL * env))
    vR = np.tanh(0.8 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak
```

## `brass_phrase` — Oberheim brass — owned by tech_noir

**Source:** `tech_noir_v3.py:brass_phrase`  
**Character:** reciprocally detuned reed pair, pitch scoop, bloom vibrato, LP 1600

```python
def brass_phrase(notes, lowpass=1600.0):
    total = sum(d for _, d in notes) * SIXT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in notes], n, tau=0.05)
    f_curve *= 1.0 - 0.018 * np.exp(-tt / 0.12)           # a gentler scoop
    vib = 1.0 + 0.0024 * np.sin(2 * np.pi * 4.5 * tt) * np.clip(tt / 1.4, 0, 1)
    K = max(3, int(5200 / np.max(f_curve)))

    def reed(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.35
        return v

    base = reed(1.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve * vib) / SR)   # round core
    vL = base + reed(0.9968) + 0.35 * body
    vR = base + reed(1.0032) + 0.35 * body
    atk = np.clip(tt / 0.20, 0, 1)                        # slow bloom-in
    atk = 0.5 - 0.5 * np.cos(np.pi * atk)                 # rounded, not linear
    env = np.minimum(atk, np.clip((total + 0.35 - tt) / 1.0, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    vL = np.tanh(0.8 * signal.sosfilt(sos_w, vL * env))   # a whisper of drive
    vR = np.tanh(0.8 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak
```

## `love_phrase` — love theme voice — owned by tech_noir

**Source:** `tech_noir_v3.py:love_phrase`  
**Character:** the warm answer/contour voice of the machine score

```python
def love_phrase(notes):
    total = sum(d for _, d in notes) * SIXT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    v = (np.sin(ph) + 0.40 * np.sin(2 * ph) +
         0.16 * np.sin(3 * ph) + 0.07 * np.sin(4 * ph))
    env = np.minimum(np.clip(tt / 0.25, 0, 1),
                     np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos_w = signal.butter(2, 3000, "low", fs=SR, output="sos")
    v = signal.sosfilt(sos_w, v * env)
    v /= np.max(np.abs(v)) + 1e-12
    return v
```

## `skyline_note` — skyline lead — owned by eisgang

**Source:** `eisgang_v3.py:skyline_note`  
**Character:** warm-lead family dialed darker + SUSTAINED: LP 2200, 1/k**1.35, sine body, bloom attack scaled to note length, full sustain, bloom vibrato; chorus refrain voice

```python
def skyline_note(midi, dur):
    # the sustained warm dark saw (warmth recipe, full sustain, no pling):
    # bloom attack scaled to the note (short ladder 16ths still speak),
    # flat sustain to dur, soft release
    key = (midi, round(dur, 2))
    if key in skyline_cache:
        return skyline_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.5) * SR)
    td = np.arange(n) / SR
    vib = 1.0 + 0.003 * np.sin(2 * np.pi * 5.3 * td) * \
        np.clip(td / 0.35, 0, 1)                   # bloom vibrato
    x = np.zeros(n)
    K = max(3, min(22, int(2600 / f)))
    for det, w in [(0.996, 1.0), (1.0, 0.9), (1.004, 1.0)]:
        ph = 2 * np.pi * np.cumsum(f * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.35        # rolled off: round
        x += w * v
    x += 0.32 * np.sin(2 * np.pi * np.cumsum(f * vib) / SR)   # sine body
    atk = min(0.10, 0.35 * dur)                    # slow bloom, scaled
    env = np.minimum(0.5 - 0.5 * np.cos(np.pi * np.clip(td / atk, 0, 1)),
                     np.clip((dur + 0.18 - td) / 0.18, 0, 1))
    y = np.tanh(0.85 * x) * env
    y = signal.sosfilt(signal.butter(2, 2200, "low", fs=SR, output="sos"), y)
    skyline_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return skyline_cache[key]
```

## `lead_line` — the underglow (lead_line at −12)

**Source:** `eisgang_v3.py:lead_line`  
**Character:** dark sustain bed under the refrain voice; D-50 trick. Runs at −12 transpose, LP 1600, quiet. Carries held notes across the held V.

```python
def lead_line(notes, transpose=0, lowpass=2600):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m + transpose, d * BEAT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.0035 * np.sin(2 * np.pi * 5.5 * tt) * \
        np.clip(tt / 0.6, 0, 1)
    ph_base = 2 * np.pi * np.cumsum(f * vib) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for det, gL, gR in [(0.997, 1.0, 0.6), (1.003, 0.6, 1.0)]:
        K = max(3, int(2600 / np.min(f)))
        v = np.zeros(n)
        for k in range(1, K + 1, 2):               # odd: the hollow core
            v += np.sin(k * ph_base * det) / k ** 1.3
        v += 0.30 * np.sin(ph_base * det)
        L += gL * v
        R += gR * v
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.15, 0, 1))
    env = np.minimum(atk, np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, np.tanh(0.8 * L) * env)
    R = signal.sosfilt(sos, np.tanh(0.8 * R) * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak
```

## `make_signal` — the signal — owned by adrift

**Source:** `adrift.py:make_signal`  
**Character:** glide-whistle call (B5→F#5) on a long dotted-8th feedback trail; an FX-lead, once per chorus

```python
def make_signal():
    notes = [(83, 0.75 * BEAT), (78, 2.5 * BEAT)]
    total = sum(d for _, d in notes)
    n = int((total + 0.5) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.08)              # the slide IS the voice
    vibe = 1.0 + 0.006 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vibe) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph)
    breath = signal.sosfilt(BREATH_SOS, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    x += 0.05 * breath
    x *= np.minimum(0.5 - 0.5 * np.cos(np.pi * np.clip(td / 0.15, 0, 1)),
                    np.clip((total + 0.2 - td) / 0.6, 0, 1))
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `acid_note` — warmed 303 acid

**Source:** `maschinenherz.py:acid_note`  
**Character:** rolled 1/k^1.3, Q 4.5, fb 1.15/1.2, tanh(1.2), 0.30 sine body, within-note bright→dark sweep; cutoff from printable arc, never parked

```python
def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    if dur is None:
        dur = STEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 6500))
    key = (m, int(cutoff // 60), accent, slide_to, round(dur, 4))
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:                                  # the 303 tie: glide the back half
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(k * ph) / k ** 1.3          # rolled — not hard saw

    def res_lp(sig_in, c):
        c = float(min(c, 8000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 7500.0), Q=4.5, fs=SR)
        return y + (1.2 if accent else 1.15) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 2.5)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(1.2 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)                      # the sine body core
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y
```

## `acid_note` — silver wire 303 — owned by silver_wire

**Source:** `silver_wire_v2.py:acid_note`  
**Character:** one notch sharper: Q 6, fb 1.3/1.35, tanh(1.5); 16-bar refrain from Q_STEPS/A_STEPS winding cells, every-3rd accent roll, anti-arc CUT_PROFILE

```python
def acid_note(m, cutoff, accent=False, slide_to=None, dur=STEP * 0.92):
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 6500))
    key = (m, int(cutoff // 40), accent, slide_to, round(dur, 4))
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(k * ph) / k ** 1.3

    def res_lp(sig_in, c):
        c = float(min(c, 8000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 7500.0), Q=6.0, fs=SR)
        return y + (1.35 if accent else 1.3) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 2.5)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(1.5 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y
```

## `voice_phrase` — love-voice port

**Source:** `maschinenherz.py:voice_phrase`  
**Character:** sine + 3 rolled harmonics, 5.2 Hz late vibrato, LP 3000, long hall wet ~0.5; new melodies only. Original owned by tech_noir; maschinenherz borrow declared in notes.

```python
def voice_phrase(notes):
    key = tuple(notes)
    if key in voice_cache:
        return voice_cache[key]
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    v = (np.sin(ph) + 0.40 * np.sin(2 * ph) +
         0.16 * np.sin(3 * ph) + 0.07 * np.sin(4 * ph))
    env = np.minimum(np.clip(tt / 0.25, 0, 1),
                     np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos_w = signal.butter(2, 3000, "low", fs=SR, output="sos")
    v = signal.sosfilt(sos_w, v * env)
    v /= np.max(np.abs(v)) + 1e-12
    voice_cache[key] = v
    return v
```
