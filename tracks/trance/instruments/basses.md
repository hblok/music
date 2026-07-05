# Basses

Bass voice functions extracted from the trance generators.
Note: `bass_note` name is reused across scripts with very different characters — always check the source.

## `bass_note` — rolling 16th mono bass (canonical)

**Source:** `lost_v6.py:bass_note`  
**Character:** THE house bass: rolled-off saw stack, iirpeak Q 1.2 blend 0.3, half-freq sine sub, tanh 0.9; continuous 16ths on a pedal with octave jumps. Per-section cutoff tables.

```python
def bass_note(midi, cutoff, drive=0.9, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60), round(drive, 1))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(22, int(3500 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3      # rolled-off, rounder
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)         # gentle, not nasal
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)             # round sub for body
    y = np.tanh(drive * y)                                  # soft, not crunchy
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]
```

## `bass_note` — tide pulse bass — owned by adrift

**Source:** `adrift.py:bass_note`  
**Character:** quarter/8th-note pulse gait (dream-era); the rolling bass retired for adrift's character

```python
def bass_note(midi, dur=BEAT * 0.45):
    key = (midi, round(dur, 3))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.06) * SR)
    td = np.arange(n) / SR
    core = (np.sin(2 * np.pi * f * td) + 0.35 * np.sin(4 * np.pi * f * td)
            + 0.12 * np.sin(6 * np.pi * f * td))
    core *= (1 - np.exp(-td / 0.008)) * np.clip((dur - td) / 0.05, 0, 1)
    smear = signal.sosfilt(SMEAR_SOS, np.tanh(2.2 * core))
    smear = signal.oaconvolve(smear, SMEAR_BURST)[:n]
    smear /= np.max(np.abs(smear)) + 1e-12
    x = core + 0.25 * smear
    bass_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return bass_cache[key]
```

## `bass_hit` — machine bass — owned by tech_noir

**Source:** `tech_noir_v3.py:bass_hit`  
**Character:** the dry forward "DUN-dun" on the 13/16 grid

```python
def bass_hit(midi, dur=SIXT * 0.95):
    if midi in bass_cache:
        return bass_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(28, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, 520, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    y += 0.55 * np.sin(2 * np.pi * (f / 2) * td)          # round sub octave
    y = np.tanh(1.8 * y)
    y *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 14.0)
    y *= np.clip((dur - td) / 0.015, 0, 1)
    bass_cache[midi] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[midi]
```

## `thud_bass` — thud-bass (run-and-plant) — owned by eisgang

**Source:** `eisgang_v3.py:thud_bass`  
**Character:** percussive anti-rolling bass: sine + octave + 150–800 Hz knock, no saw; bounce–plant–REST, duty ≤ 0.6. **Listen verdict keeper** (fun!)

```python
def thud_bass(midi, dur, weight=1.0):
    key = (midi, int(dur * 1000))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * td) + 0.45 * np.sin(2 * np.pi * 2 * f * td +
                                                      0.7)
    knock = signal.sosfilt(signal.butter(2, [150, 800], "bandpass", fs=SR,
                                         output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 120)
    knock /= np.max(np.abs(knock)) + 1e-12
    x = body + 0.35 * knock
    env = (1 - np.exp(-td / 0.003)) * \
        (0.5 + 0.5 * np.cos(np.pi * np.clip(td / dur, 0, 1)))
    y = np.tanh(0.9 * x * env) * weight
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]
```

## `psy_bass_note` — psy rolling bass (K-b-b-b)

**Source:** `maschinenherz.py:psy_bass_note`  
**Character:** kick on the beat, bass on 3 16ths after (gains .8/.7/.95); saw stack LP 350 Hz, short gate; NEVER on a kick 16th (the gap IS the rest)

```python
def psy_bass_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(20, int(7000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_b = signal.butter(2, 350, "low", fs=SR, output="sos")
    x = np.tanh(2.0 * signal.sosfilt(sos_b, x))
    env = (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.02, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `sub_note` — sub-duty bass — owned by silver_wire

**Source:** `silver_wire_v2.py:sub_note`  
**Character:** pure sine + 0.3×2nd harmonic; drop-mode replacement when 303 low register owns the mid-bass; no saw, no lowpass

```python
def sub_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.3 * np.sin(2 * np.pi * 2 * f * td)
    x *= (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.02, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)
```
