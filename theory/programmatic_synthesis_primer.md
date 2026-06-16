# Programmatic Music Synthesis: A Primer for Coders

A reference for understanding the terminology, music theory, and technical
implementation patterns used in NumPy-based audio synthesis — explained from
a math/code perspective, not a musician's one.

---

## 1. The Physics of Sound (the foundation)

Everything in synthesis starts here. Sound is a pressure wave in air,
representable as a function of amplitude over time.

**Sample rate (SR):** How many numeric amplitude values we store per second.
`SR = 44100` means 44,100 floating-point numbers represent one second of audio.
This is the CD standard; the Nyquist theorem says we can faithfully represent
any frequency up to SR/2 = 22,050 Hz (above human hearing).

```python
SR = 44100
t = np.linspace(0, duration, int(SR * duration), endpoint=False)
```

**Amplitude:** The height of the wave, typically in `[-1.0, 1.0]`. Values
outside this range cause clipping (digital distortion).

**Frequency (Hz):** How many complete wave cycles per second. Perceptually,
frequency = pitch. 440 Hz = the A above middle C.

**Phase:** Where in the cycle you are (0 to 2π). Usually starts at 0.

The most basic waveform:

```python
signal = np.sin(2 * np.pi * freq * t)  # pure sine wave
```

---

## 2. Musical Pitch and Notes

### The note system

Western music divides the octave into 12 equal steps (semitones). Each octave
doubles the frequency. The formula to go from a MIDI note number to Hz:

```python
freq = 440.0 * 2 ** ((midi_note - 69) / 12)
```

Standard MIDI numbers: 60 = middle C (C4), 69 = A4 = 440 Hz.

### Keys and scales

A **key** is a home base note (the *tonic*). A **scale** is a pattern of
intervals (semitone steps) built from it. The two most common:

| Scale | Pattern (semitone steps) | Sound |
|-------|--------------------------|-------|
| Major | 2-2-1-2-2-2-1 | Bright, resolved |
| Minor (natural) | 2-1-2-2-1-2-2 | Dark, melancholic |

So **D minor** = D, E, F, G, A, Bb, C (using D as the starting note and
applying the minor pattern). **G minor** = G, A, Bb, C, D, Eb, F.

In code you'd often represent a scale as a list of MIDI offsets from the root:

```python
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]  # semitone offsets
root = 62  # D4
scale_notes = [root + s for s in MINOR_SCALE]
```

### Chords and Roman numeral notation

A **chord** is 3+ notes played simultaneously. Built by stacking thirds
(every other scale note):

- **Triad**: root + third + fifth (e.g. G minor = G, Bb, D)
- **i, IV, V**: Roman numerals label chords by scale degree
  - Lowercase = minor, uppercase = major
  - **i–VI–VII–V** (the *lost* progression): minor chord, then major chords
    on the 6th, 7th, and 5th scale degrees — the backbone of emotional trance

**Relative major/minor**: D major and B minor share the exact same 7 notes;
you can resolve to either one without changing the harmonic vocabulary. This
is what allows a section to feel "bright" vs "melancholic" with zero note
changes — just which chord you land on.

**Borrowed chord**: A chord imported from the parallel minor/major key.
In G minor, the V chord (D) is naturally minor (Dm), but the CLAUDE.md uses
D **major** — borrowing its F# from outside the G minor scale. That single
raised note is what creates the "gothic colour".

---

## 3. Rhythm and Time

### BPM and beats

**BPM (beats per minute):** Tempo. At 139 BPM:

```python
BPM = 139
BEAT = 60.0 / BPM          # seconds per beat ≈ 0.432 s
BAR = 4 * BEAT              # one bar of 4/4 time
SIXT = BEAT / 4             # one sixteenth note
```

### Time signatures

**4/4**: 4 beats per bar, quarter note gets the beat. The most common pop/dance
time signature.

**13/16**: 13 sixteenth-note slots per bar. Asymmetric — this is the Terminator
"limp" feel. Grouped `3+3+3+2+2` to create an uneven lurch:

```python
BAR = 13 * SIXT
BASS_STEPS = [0, 1, 3, 4, 6, 7, 9, 11]  # hits at these sixteenth positions
```

The asymmetry is the point — do not "fix" it to 4/4.

### Note durations

| Name | Duration | Relative |
|------|----------|----------|
| Whole | 4 beats | 4 × BEAT |
| Half | 2 beats | 2 × BEAT |
| Quarter | 1 beat | BEAT |
| Eighth | half a beat | BEAT/2 |
| Sixteenth | quarter of a beat | BEAT/4 |
| Dotted-eighth | 3/4 of a beat | 0.75 × BEAT |

A **dotted** note is 1.5× its normal value. The ping-pong delay in *nachtkind*
uses `DELAY = 0.75 * BEAT` (a dotted eighth) to sync the echo to the tempo grid.

---

## 4. Waveform Synthesis (the math)

### Additive synthesis and partials

A pure sine is the simplest waveform. Complex timbres are built by summing
multiple sines at harmonically related frequencies — called **partials** or
**harmonics**. The *k*-th harmonic is at `k × f0`.

**Sawtooth wave** (the classic analogue synth wave — buzzy, full of harmonics):

```python
# Ideal saw: all harmonics at 1/k amplitude
signal = sum(np.sin(k * 2*np.pi * f0 * t) / k for k in range(1, N_partials+1))
```

This produces a harsh buzz. Rolling off the higher partials softens it:

```python
# Rolled-off saw: warmer, more like brass or strings
signal = sum(np.sin(k * 2*np.pi * f0 * t) / k**1.35 for k in range(1, N+1))
```

The exponent (1.0 → 1.3 → 1.4) is the primary timbre control knob:
- `1/k**1.0` — raw saw, buzzy/harsh
- `1/k**1.25` — piano-like digital tone
- `1/k**1.35` — warm brass/reed
- Higher → softer/mellower

### Inharmonic partials

Musical instruments aren't perfectly harmonic. Piano strings have **inharmonicity**
because they're stiff: higher partials are slightly sharp of integer multiples.

```python
B = 3.5e-4  # inharmonicity coefficient
fk = f0 * k * np.sqrt(1 + B * k**2)
```

This stretching of high harmonics gives the "M1-era gothic piano" its
slightly-artificial digital character.

**Completely inharmonic** ratios (anvil, bell, metallic objects):
```python
RATIOS = [1, 2.71, 4.07, 5.43, 7.39, 9.21]  # not integer multiples
freqs = [f0 * r for r in RATIOS]
```
Non-integer ratios create the metallic "clang" rather than a musical pitch.

### Detune / chorus width

Two copies of the same waveform, slightly out of tune with each other, produce
a warm, wide stereo "chorus" shimmer:

```python
freq_a = f0 * (1 - 0.0032)   # -0.32 cents flat
freq_b = f0 * (1 + 0.0032)   # +0.32 cents sharp
voice = voice_a + voice_b     # sum = warm, thick
```

The beating between the two copies is perceived as liveliness/movement rather
than two separate pitches.

---

## 5. Amplitude Envelopes

An envelope controls how the volume of a note changes over time:
attack → decay → sustain → release (ADSR).

```python
# Linear attack ramp
envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

# Raised cosine attack — smoother, avoids the "stab" transient
envelope[:attack_samples] = 0.5 - 0.5 * np.cos(np.pi * np.linspace(0, 1, attack_samples))

# Exponential decay (physical instruments decay this way)
envelope = np.exp(-decay_rate * t)
```

**Why this matters for timbre:** A fast linear attack reads as a "stab" —
percussive, intruding. A slow raised-cosine attack "blooms in" — the note
seems to arrive gradually, sitting with the track rather than cutting through.
This is the #3 knob in the warmth recipe.

**Gated reverb effect (the 80s drum slam):**
The kick has a large reverb tail — then that tail is hard-clipped at 140 ms:

```python
clip_samples = int(0.140 * SR)
kick[clip_samples:] *= np.clip((clip_envelope), 0, 1)
```

The sudden silence of a chopped reverb tail is what the brain reads as
"80s gated reverb". The gate is baked into the sample itself rather than
using an actual gate effect.

---

## 6. Filters

A filter removes or boosts frequency bands.

### The lowpass filter

Passes frequencies below a cutoff, attenuates above it. `scipy.signal.butter`
implements this as an IIR (infinite impulse response) filter:

```python
from scipy.signal import butter, sosfilt

sos = butter(N=4, Wn=cutoff_hz, btype='low', fs=SR, output='sos')
filtered = sosfilt(sos, signal)
```

**Cutoff frequency** is the primary brightness/darkness control:
- Low cutoff (900–1600 Hz) → dark, muffled, warm
- High cutoff (3000–8000 Hz) → bright, present, sometimes harsh

The 2–4 kHz band is where "honk/bite" and nasal harshness lives — lowering
the cutoff below this band is the #4 warmth knob.

### Bandpass and peak (resonant) filter

Passes only a band around the center frequency. With a high Q (resonance),
it creates the "acid" bite (the TB-303 sound):

```python
from scipy.signal import iirpeak

b, a = iirpeak(w0=cutoff/(SR/2), Q=3.5)
filtered = lfilter(b, a, signal)
```

- **Q=3.5**: Narrow, nasal, acid peak — the classic 303 resonance squeal
- **Q=1.2**: Broad, gentle bump — warms the body without the bite

Blending the resonant output with the dry signal:

```python
output = 0.3 * resonant + 0.7 * dry   # 0.7 dry = round body, not acid
```

---

## 7. Distortion / Saturation

`np.tanh(drive * signal)` applies soft clipping — louder signals get
compressed towards ±1, adding harmonic richness (odd harmonics, like a tube amp).

```python
# Harsh drive
distorted = np.tanh(1.8 * signal)

# Soft, warm saturation
distorted = np.tanh(0.8 * signal)
```

The drive multiplier before `tanh` is the #5 warmth knob. High drive → more
compressed, more harmonics added, more aggressive. Low drive → gentle coloring.

---

## 8. Pitch Modulation

### Vibrato

Sinusoidal pitch wobble around the base frequency, at a rate of ~4–6 Hz:

```python
vibrato_rate = 4.5  # Hz
vibrato_depth = 0.003  # fraction of semitone
freq_mod = f0 * (1 + vibrato_depth * np.sin(2*np.pi * vibrato_rate * t))
```

Apply vibrato only after a short delay (the "bloom" into the note), not
from the very start.

### Pitch scoop

Starts slightly flat, glides up to the target — common in vocal and brass:

```python
scoop = 1 - 0.018 * np.exp(-t / 0.12)   # starts 1.8% flat, rises in ~120ms
freq_mod = f0 * scoop
```

### Glide / portamento

Smooth pitch transition between two notes:

```python
# Exponential glide from freq_a to freq_b over glide_time
tau = glide_time / 5.0
freq_curve = freq_b + (freq_a - freq_b) * np.exp(-t / tau)
```

---

## 9. Reverb and Space

**Reverb** simulates acoustic space — the collection of delayed reflections
that happen in a room. Implemented as **convolution** with an impulse response
(IR): a recording of a clap in the actual space.

```python
from scipy.signal import fftconvolve
wet = fftconvolve(dry_signal, impulse_response)[:len(dry_signal)]
output = (1 - wet_amount) * dry_signal + wet_amount * wet
```

**IR duration** controls perceived room size:
- 1–2 s IR → small room / plate
- 5–6 s IR → large hall / cathedral

**The Frankfurt aesthetic (nachtkind):** Drums go through zero reverb. All
melodic elements go through a 6-second dark hall at 0.5–0.55 wet. The
perceptual contrast between the mechanical dry drums and the soaking-wet
melody is the defining characteristic of the Eye Q trance sound.

### Delay

A simpler effect: one or more copies of the signal, time-delayed and fed back:

```python
delay_samples = int(delay_time * SR)
output[delay_samples:] += feedback * signal[:-delay_samples]
```

**Tempo-synced delay:** Set `delay_time = 0.75 * BEAT` (dotted eighth) so
echoes land on the off-grid swing points. **Ping-pong delay** alternates the
echoes between left and right channels.

---

## 10. Stereo Panning

Audio is two channels (L, R). Pan position maps `[-1.0, 1.0]` to gain ratios:

```python
pan = 0.3   # slightly right
left_gain  = np.sqrt(0.5 * (1 - pan))
right_gain = np.sqrt(0.5 * (1 + pan))
stereo[0] += left_gain * mono
stereo[1] += right_gain * mono
```

The square root preserves constant perceived loudness as you pan.

---

## 11. The Mix Bus

All sounds are summed into a stereo buffer (`mix`). The **commit** function
normalizes and writes to the WAV file.

**RMS (Root Mean Square):** The standard measure of perceptual loudness:

```python
rms = np.sqrt(np.mean(signal**2))
```

Per-section RMS targets ensure consistent loudness across the track.

**`add_at(mix, signal, t_start)`:** Places a sound at a specific time offset
in the mix buffer (equivalent to `mix[sample_offset:] += signal`).

---

## 12. Track Architecture Patterns

### Seeded RNG

```python
rng = np.random.default_rng(seed=1993)
```

A fixed seed makes all stochastic elements (velocity variations, slight timing
offsets, noise components) reproducible. Change the seed → different variation
of the same structure. The seed is thematic: `1984` for the Terminator track,
`1993` for the Eye Q trance era.

### One standalone script per track

No shared modules. Every track is self-contained — all helper functions
(`add_at`, `glide_curve`, `reverb`) are duplicated inside the file. This
makes each script runnable independently and prevents version coupling.

### Version discipline

Never overwrite a WAV the user has already listened to. New iteration =
new WAV name + `_vN` script suffix. Old versions kept for A/B reference.

### The "add one element every 16 bars" philosophy

Arrangement by gradual layering — each 16-bar block introduces exactly one
new element. This prevents the track from revealing everything at once and
maintains forward motion across a long run time.

---

## 13. Glossary (Quick Reference)

| Term | Meaning |
|------|---------|
| **Partial / Harmonic** | Sine component at k × f0 |
| **Saw wave** | Sum of all harmonics at 1/k amplitude |
| **Timbre** | The "color" of a sound — determined by harmonic content |
| **ADSR** | Attack, Decay, Sustain, Release — volume envelope shape |
| **Lowpass** | Filter that removes high frequencies |
| **Cutoff** | Frequency at which a lowpass begins attenuating |
| **Q / Resonance** | Narrowness of a peak filter; high Q = acid bite |
| **tanh / saturation** | Soft clipping, adds harmonic richness |
| **Detune** | Slightly mistuning copies for chorus/warmth |
| **IR / Convolution reverb** | Room simulation via recorded impulse response |
| **BPM** | Beats per minute; tempo |
| **Tonic / Root** | The home-base note of a key |
| **Relative minor** | The minor key sharing the same notes as a major key |
| **Borrowed chord** | Chord imported from the parallel major/minor |
| **i–VI–VII–V** | Chord progression by scale degree (lost track) |
| **Gated reverb** | Reverb tail hard-clipped short — the 80s drum slam |
| **RMS** | Perceptual loudness measure: √mean(x²) |
| **Seeded RNG** | Reproducible randomness — same seed = same output |
