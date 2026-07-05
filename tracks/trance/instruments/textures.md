# Textures, Builds & Seam Devices

Transition, build, and texture functions. Roll+swell = the era build pair.

## `roll` — snare roll

**Source:** `adrift.py:roll`  
**Character:** the era build: 16th→32nd roll; always paired with swell

```python
def roll(b0, b1, base):
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, bar_t(b, s * 4.0 / div), g, 0.5)
```

## `swell` — bandlimited swell

**Source:** `adrift.py:swell`  
**Character:** 250–2400 Hz bandlimited swell (never white noise); the era build pair with roll

```python
def swell(b0, b1, gain=1.0):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    prog = np.arange(n) / n
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(5):
        c = 250 * (2400 / 250) ** (k / 4)
        win = np.clip(1 - np.abs(prog - np.log(c / 250) / np.log(2400 / 250)) * 4, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.8, c * 1.25], "bandpass",
                                            fs=SR, output="sos"), noise) * win
    out *= prog ** 2
    out /= np.max(np.abs(out)) + 1e-12
    add_at(lay_L, out, t0, gain)
    add_at(lay_R, out, t0, gain * 0.96)
```

## `riser` — noise riser

**Source:** `lost_v6.py:riser`  
**Character:** lost's own; banned by construction in the era-strict tracks

```python
def riser(b0, b1, gain=1.0):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    prog = td / (t1 - t0)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):
        c = 350 * (6000 / 350) ** (k / 7)
        win = np.clip(1 - np.abs(prog - np.log(c / 350) / np.log(6000 / 350)) * 6, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.85, c * 1.18], "bandpass", fs=SR, output="sos"), noise) * win
    out += 0.4 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(50) * 2 ** (2 * prog)) / SR)
    out *= prog ** 2
    add_at(lay_L, out / (np.max(np.abs(out)) + 1e-12), t0, gain)
    add_at(lay_R, out / (np.max(np.abs(out)) + 1e-12), t0, gain * 0.96)
```

## `cloud` — cloud — owned by adrift

**Source:** `adrift.py:cloud`  
**Character:** symmetric bandpassed wash that *passes by* (sin² envelope) — a non-riser

```python
def cloud(b0, nbars, gain):
    n = int(nbars * BAR * SR)
    prog = np.arange(n) / n
    x = signal.sosfilt(signal.butter(2, [300, 1800], "bandpass", fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= np.sin(np.pi * prog) ** 2                   # symmetric: it passes by
    x /= np.max(np.abs(x)) + 1e-12
    p0, p1 = (0.3, 0.7) if rng.random() < 0.5 else (0.7, 0.3)
    pan = p0 + (p1 - p0) * prog
    add_at(lay_L, x * np.cos(pan * np.pi / 2), bar_t(b0), gain)
    add_at(lay_R, x * np.sin(pan * np.pi / 2), bar_t(b0), gain)
```

## `silent_beat` — silent beat

**Source:** `lost_v6.py:silent_beat`  
**Character:** the one composed drop-beat before a slam/final chorus

```python
def silent_beat(b, beat):
    # the composed drop-silence: bar 124 beat 0 belongs to nobody
    return b == B_HOPE and beat < 1.0
```

## `tide_out` — tide out — owned by adrift

**Source:** `adrift.py:tide_out`  
**Character:** kick+bass exit under a still-ringing melody; the return lands mid-phrase

```python
def tide_out(b):
    return B_DRIFT <= b < B_RET      # the tide: no drums, no bass
```

## `cutoff_at` — filter arc (cutoff_at)

**Source:** `penumbra.py:cutoff_at`  
**Character:** piecewise-linear cutoff curve, checked at boundaries; development as a printable arc

```python
def cutoff_at(b):
    return float(np.interp(b, CUT_BARS, CUT_HZ))
```

## `shiver_stab` — shiver stack — owned by maschinenherz

**Source:** `maschinenherz.py:shiver_stab`  
**Character:** additive dissonance intro: one stab voice per 4 bars, layering DISSONANCE (octave → 2nd-clash → tritone → leading tone), first consonant chord lands with the kick

```python
def shiver_stab(midis):
    if midis in stab_cache:
        return stab_cache[midis]
    n = int(0.10 * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(5000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    v = signal.sosfilt(signal.butter(2, 1100, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.002)) * np.clip((0.085 - td) / 0.025, 0, 1)
    stab_cache[midis] = v / (np.max(np.abs(v)) + 1e-12)
    return stab_cache[midis]
```

## `ice_crack` — ice-crack seam — owned by maschinenherz

**Source:** `maschinenherz.py:ice_crack`  
**Character:** stab—silence—upward flick; the psy glitch transition (not tom fills, not reverse cymbals)

```python
def ice_crack(b):
    for gi, (beat0, flick) in enumerate(zip((0.0, 1.25, 2.5), ICE_FLICKS)):
        add_at(lay_L, PB[40], bar_t(b, beat0), 0.8)          # the low stab
        add_at(lay_R, PB[40], bar_t(b, beat0), 0.8)
        for i, m in enumerate(flick):                        # the 32nd flick
            p = 0.35 + 0.3 * gi / 2
            place_pan(lay_L, lay_R, pluck(m), bar_t(b, beat0 + 0.75 + i * 0.125),
                      0.55 + 0.1 * i, p)
```

## `ladder_bars` — stutter ladder — owned by maschinenherz

**Source:** `maschinenherz.py:ladder_bars`  
**Character:** 303 locks one pitch per bar in 16th retrigger, climbing chromatically out of key into the drop; build 1 parks on dominant, build 2 ends on leading tone

```python
def ladder_bars(b0, pitches):
    # W4a: lock ONE pitch per bar, 16th retrigger with a chatter gain
    # cell; the pitch climbs chromatically out of the key.
    cell = [1.0, 0.72, 0.88, 0.72]
    for i, m in enumerate(pitches):
        b = b0 + i
        n16 = 12 if b in ROLL_16TH else 16      # honor the composed silence
        for s16 in range(n16):
            cut = cutoff_at(b + s16 / 16.0)
            x = acid_note(m, cut, accent=(s16 % 4 == 0), dur=STEP * 0.55)
            p = 0.5 + 0.12 * (1 if s16 % 2 else -1)
            add_at(lay_L, x, bar_t(b, s16 * 0.25), cell[s16 % 4] * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s16 * 0.25), cell[s16 % 4] * np.sin(p * np.pi / 2))
```

## `arp_bars` — zigzag arp — owned by maschinenherz

**Source:** `maschinenherz.py:arp_bars`  
**Character:** chorus arp cell: root–oct–oct–5th / 5th–♭3–♭3–root, restated up chord tones; glassy pluck voice

```python
def arp_bars(b0, b1, octave=0, gain=1.0, double=False):
    for b in range(b0, b1):
        cell = ARP_CELLS[CH_LAP[b % 4]]
        for s16 in range(16):
            m = cell[s16 % 8] + octave
            g = gain * (1.0 if s16 % 2 == 0 else 0.8)
            p = 0.5 + 0.25 * np.sin(2 * np.pi * s16 / 8)
            place_pan(lay_L, lay_R, pluck(m), bar_t(b, s16 * 0.25), g, p)
            if double:
                place_pan(lay_L, lay_R, pluck(m + 12), bar_t(b, s16 * 0.25),
                          g * 0.4, 1.0 - p)
```
