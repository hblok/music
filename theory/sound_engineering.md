# Sound Engineering: From Signal to Record

The third layer of the craft. *Music theory* decides which notes; the
*synthesis primer* decides what each sound is made of; **sound engineering**
decides how the sounds coexist — how twenty signals become one record that
translates to headphones, club systems and laptop speakers alike.

Like its siblings, this is written from a math/code perspective. Examples
use the NumPy/SciPy idioms of the track scripts in `tracks/trance/`.

---

## 1. The Three Layers of Production

| Layer | Question it answers | Where it happens in our pipeline |
|-------|--------------------|----------------------------------|
| **Sound design** | What does this one instrument sound like in isolation? | the `make_*` / `*_note` functions |
| **Mixing** | How do all instruments coexist — levels, spectrum, space, dynamics? | gains at `add_at` time, per-sound filters, reverb sends |
| **Mastering** | How does the finished stereo file behave in the world — loudness, peaks, format? | the `commit` normalize step (currently the whole of it) |

In a studio these are separate jobs done by separate people with separate
tools. In our scripts they interleave — but the *decisions* remain distinct,
and most "this sounds wrong" complaints are a mixing decision misdiagnosed
as a sound-design one. A harsh lead might need a darker filter (design), or
it might just be 3 dB too loud (mix). Check the cheaper hypothesis first.

---

## 2. The Signal Chain — the Lesson from Hardware

Every classic synthesizer is a fixed pipeline of analog circuit blocks:

```
VCO ──► VCF ──► VCA ──► FX ──► mixer channel ──► bus ──► master
(osc)   (filter) (amp)  (delay,  (EQ, pan,        (sum)   (final gain,
                         reverb)  fader)                    limiter)
```

- **VCO** — voltage-controlled oscillator: the raw waveform (our partial sums).
- **VCF** — voltage-controlled filter: the timbre shaper (our `butter`/`iirpeak`).
- **VCA** — voltage-controlled amplifier: the volume envelope (our ADSR arrays).

The deep idea is in the **VC** prefix: on a modular synth, *every parameter
is a signal*. Pitch is a voltage, cutoff is a voltage, volume is a voltage —
and any output can drive any input. An LFO wobbling a filter and an envelope
opening an amplifier are the same mechanism pointed at different targets.

NumPy gives us this for free: any scalar parameter can become an array over
time. `cutoff_at(t)` filter arcs, per-note pitch scoops, ducking curves —
these are all CV thinking. When a sound feels static, the hardware question
is "what would I patch into this?" — i.e. which parameter should stop being
a constant.

**The channel strip** is the other canonical structure. On a mixing console,
every channel processes in a fixed order:

```
input gain → highpass → EQ → compressor → sends (reverb/delay) → pan → fader
```

This order is not arbitrary: you clean up (highpass, EQ) *before* you
compress, because a compressor reacts to everything it hears — feed it
rumble and it ducks the whole channel for frequencies nobody can hear. And
sends come after dynamics so the reverb receives the controlled signal.
When a per-instrument function applies transforms in a strange order and
sounds wrong, this is the reference order to compare against.

---

## 3. Gain Staging and Headroom

Digital full scale is a hard wall: samples outside `[-1.0, 1.0]` clip, and
digital clipping is harsh in a way analog overload is not (see §9). The
engineering discipline:

1. **Work quiet.** Individual sounds mix in at conservative gains; the
   summed bus may sit well below 1.0. Quiet costs nothing in float64.
2. **Normalize exactly once, at the end.** The `commit` pattern —
   `mix /= np.max(np.abs(mix)) / 0.95` — is a legitimate mastering move
   *because* it is the only gain decision made against the ceiling.
3. **Balance with faders before anything else.** The single highest-leverage
   mixing act is setting relative levels. A mix that works with faders alone
   is nearly done; EQ and compression then fix what faders can't.

Two measurements, two purposes:

```python
peak = np.max(np.abs(x))          # will it clip? (instantaneous)
rms  = np.sqrt(np.mean(x**2))     # how loud does it feel? (average power)
```

Their ratio (**crest factor**, usually in dB) describes how spiky a signal
is. Drums: high crest (quiet on average, tall peaks). Pads: low crest.
This is why per-section RMS targets work for judging loudness while peak
normalization guards the ceiling — they answer different questions.

---

## 4. The Frequency Spectrum as Shared Real Estate

A mix is ~20 Hz to 20 kHz of space, and every sound wants some of it. When
two sounds occupy the same band at the same time, the louder one **masks**
the other — the ear literally receives less of the quieter one. Most "I
can't hear the X" problems are masking, and the fix is subtraction, not
turning X up (which just starts a loudness war between channels).

The bands and their failure modes:

| Band | Range | What lives there | When it's wrong |
|------|-------|------------------|-----------------|
| Sub | 20–60 Hz | kick fundamental, sub bass | rumble; invisible on small speakers |
| Bass | 60–250 Hz | bass body, kick punch | boom |
| Low mids | 250–500 Hz | warmth/body of almost everything | **mud** — the default problem of dense mixes |
| Mids | 500–2 kHz | melody body, chord voicings | boxy, honky |
| High mids | 2–6 kHz | attack, presence, bite | **harsh** — the zone the warmth recipe lowpasses away |
| Air | 6–20 kHz | hats, shimmer, noise texture | brittle, hissy |

Working rules:

**One owner per band per moment.** The kick owns the sub, the bass owns
60–250, the lead owns its melody register, hats own the air. Two claimants
→ one gets carved. This is why the psy bass *never* lands on a kick
sixteenth: that rule is spectrum allocation enforced in time rather than
frequency — the two sounds share a band but never a moment.

**Highpass everything that doesn't need lows.** The cheapest, most
effective mix move. Pads, leads, plucks and textures all generate low-mid
energy that adds nothing melodic but sums into mud:

```python
sos = butter(2, 120, btype='high', fs=SR, output='sos')
pad = sosfilt(sos, pad)   # the pad no longer fights the bass for 80 Hz
```

**Carve, don't boost.** To make the lead cut through, cut the pad 2–4 dB
in the lead's register rather than boosting the lead. Subtractive moves
keep headroom and avoid escalation. (The warmth recipe is this philosophy
applied at the design layer: remove harshness rather than compensate.)

**Loudness is frequency-dependent.** Equal-loudness contours (Fletcher–
Munson): the ear is most sensitive around 2–5 kHz and insensitive to lows
at quiet volumes. Practical consequences — a little energy at 3 kHz goes a
long way (and hurts first, which is why harshness complaints always point
there); bass that feels right at loud monitoring vanishes when quiet; so
judge a balance at more than one playback volume.

---

## 5. Dynamics

Dynamics engineering exists on three time scales:

- **Micro (per note):** the amplitude envelope — already a synthesis-layer
  tool (primer §5). Transient shape decides percussive vs. blooming.
- **Meso (per phrase/bar):** compression and ducking — this section.
- **Macro (per section):** arrangement-level loudness (the per-section RMS
  targets, drop-beats, builds). Composition and engineering shake hands here.

### Compression

A compressor is an automatic fader: when the signal exceeds a threshold, it
turns the gain down by a ratio. Two components: an **envelope follower**
that measures how loud the signal currently is, and a **gain computer**
that decides the reduction.

```python
def envelope_follower(x, attack=0.005, release=0.100):
    a_att = np.exp(-1.0 / (attack * SR))
    a_rel = np.exp(-1.0 / (release * SR))
    env, level = np.zeros_like(x), 0.0
    for i, v in enumerate(np.abs(x)):     # ponytail: O(n) python loop —
        c = a_att if v > level else a_rel  # fine offline; numba if it hurts
        level = c * level + (1 - c) * v
        env[i] = level
    return env

def compress(x, thresh_db=-18.0, ratio=4.0):
    env_db  = 20 * np.log10(np.maximum(envelope_follower(x), 1e-9))
    over    = np.maximum(env_db - thresh_db, 0.0)
    gain_db = -over * (1.0 - 1.0 / ratio)
    return x * 10 ** (gain_db / 20)
```

Attack time decides whether transients survive (slow attack = the hit
punches through before the gain drops); release decides how fast the sound
recovers (too fast = audible pumping — unless pumping is the point, below).

In a fully synthesized pipeline, compression is less essential than in
recording: we already control every envelope at the source. Reach for it
when a *sum* is the problem — e.g. gluing a drum bus — not to fix a single
synthesized voice whose envelope we could just edit.

### Sidechain ducking — the trance pump

The genre-defining dynamics move: the bass/pads duck every time the kick
hits, then swell back. In hardware this is a compressor whose *detector*
listens to the kick while its *gain* acts on the bass ("sidechain" input).
In code we skip the detector entirely — we know exactly when the kicks are:

```python
def duck_curve(n, kick_times, depth=0.6, recover=0.20):
    """Gain curve: dips to (1-depth) at each kick, exp-recovers to 1."""
    g = np.ones(n)
    for kt in kick_times:
        i = int(kt * SR)
        m = min(int(4 * recover * SR), n - i)
        t = np.arange(m) / SR
        g[i:i+m] = np.minimum(g[i:i+m], 1 - depth * np.exp(-t / recover))
    return g

bass_line *= duck_curve(len(bass_line), kick_times)
```

Beyond the pump aesthetic, ducking is masking control (§4) done in time:
the kick gets the low band to itself for 100 ms, then hands it back. Depth
0.3–0.5 is transparent groove-tightening; 0.7+ is the audible pump.

### Limiting

A limiter is a compressor at ∞:1 ratio with fast attack — a ceiling
nothing passes. Mastering limiters push the average level up against it to
gain loudness at the cost of crest factor. `np.tanh` is the one-line
version (soft, adds harmonics); a lookahead limiter is the transparent
version. Peak-normalizing to 0.95 with no limiter (the current `commit`)
preserves all dynamics but leaves the track quieter than commercial
masters — a legitimate choice, just a known one.

---

## 6. Space: Placing Sounds in Three Dimensions

A mix is a stage, and every sound has a position:

- **X (left–right):** panning. (Constant-power law: primer §10.)
- **Z (front–back):** dry/wet ratio, pre-delay, and brightness.
- **Y (up–down):** psychoacoustic — high frequencies read as "above",
  lows as "below". You get Y for free from spectrum allocation.

Depth (Z) is the engineered one. Cues the ear uses for distance:

1. **Dry/wet ratio** — more reverb = further away. A dry sound is *close*.
2. **Pre-delay** — the gap between the direct sound and the first
   reflections. Long pre-delay (20–40 ms) says "close to me, in a big
   room"; zero pre-delay pushes the source into the far wall.
3. **Brightness** — air absorbs highs; distant things are darker. A
   lowpass on the reverb tail (or the source) adds distance.

This is why the Frankfurt aesthetic (primer §9) works as *depth staging*,
not just as an effect choice: bone-dry drums sit at the front edge of the
stage, the 0.5-wet melodies stand at the back of a six-second hall, and
the contrast between the two planes is the picture.

**Shared reverb = shared room.** On a console, reverb is a *send* bus: many
channels feed one reverb at different amounts. Everything wet sounds like
it is in the *same* space — coherent — and one `fftconvolve` serves the
whole mix instead of one per instrument. Per-sound reverbs put every
instrument in a different room; do that only as a deliberate effect.

```python
reverb_bus = np.zeros_like(mix)
add_at(reverb_bus, 0.5 * lead, t)     # send amounts differ per sound…
add_at(reverb_bus, 0.3 * piano, t)
mix += fftconvolve(reverb_bus, hall_ir)[:len(mix)]   # …one room for all
```

---

## 7. The Stereo Image and the Mono Test

Width tools, in increasing risk order:

- **Panning** the dry sound: safe, always mono-compatible.
- **Detuned copies panned apart** (the chorus trick): safe-ish; the copies
  differ in frequency, not delay.
- **Haas widening** (same signal, one side delayed 5–25 ms): wide and free,
  but the delayed copy comb-filters against the original when the channels
  sum — the classic mono-collapse casualty.

Two rules keep the image honest:

**Bass stays in the middle.** Below ~120 Hz, pan everything center. Wide
bass wobbles on club systems (which often sum lows to one sub anyway) and
wastes the most power-hungry band on an effect the ear barely localizes.

**Check the mono fold.** Clubs, phones, and half of Bluetooth speakers are
effectively mono. Verify nothing vanishes:

```python
mono = mix.mean(axis=0)
fold_loss_db = 20 * np.log10(
    np.sqrt(np.mean(mono**2)) /
    np.sqrt(np.mean(((mix[0]**2 + mix[1]**2) / 2))))
# ≈ -3 dB is normal; a lead dropping much further = phase cancellation
```

---

## 8. Mastering

If the mix is right, mastering is small. Its jobs, in order of relevance
to a synthesized pipeline:

1. **Tonal sanity** — one gentle EQ over the whole bus, comparing the
   spectrum against reference tracks of the target genre. (Render a known
   commercial track's spectrum with the inspector and compare bands.)
2. **Loudness** — the modern standard is **LUFS** (Loudness Units Full
   Scale): K-weighted, gated average loudness that approximates perception
   far better than RMS. Streaming platforms normalize to about −14 LUFS;
   club/trance masters are pushed to −8 to −6 with a limiter. Measure with
   `pyloudnorm` (~5 lines) rather than reimplementing the weighting.
3. **True peak** — inter-sample peaks can exceed the sample maximum after
   DAC reconstruction; masters aim for a −1.0 dBTP ceiling. At 0.95
   (−0.45 dBFS) peak-normalize without a limiter this is rarely a problem.
4. **Format** — float64 → int16 WAV is a bit-depth reduction; strictly
   correct practice adds **dither** (±0.5 LSB noise that decorrelates the
   rounding error). At music levels the audible difference is nil; it
   matters for long quiet fades.

The honest current state of our pipeline: step 4's normalize is the whole
mastering chain, and the tracks are dynamically intact but quiet next to
commercial references. Closing that gap = one limiter + one LUFS meter,
*if* louder is ever the goal.

---

## 9. What the Circuits Teach

The classic boxes — including the 303/808 remakes on the shelf — embody
engineering lessons that survive translation into NumPy.

**Everything drifts.** Analog components have tolerances; oscillators
detune with temperature; tape wows. Nothing in an analog signal path is
exactly on spec, and the ear reads the resulting micro-variation as *alive*.
Every "warmth" trick in the codebase is a drift simulation: detuned saw
pairs, wow on the dream piano, seeded per-note velocity jitter. When a
sound is too perfect, add a tolerance.

**Everything saturates.** Every analog stage — transistor, tape, transformer
— compresses gently as it approaches its limits, adding harmonics on the
way. Analog paths are dozens of `tanh(0.1·x)` in series; that's the
texture "digital coldness" lacks. The corollary: low-drive saturation in
many places beats high drive in one.

**Fixed architecture breeds identity.** The 303 is unpatchable: one osc,
one filter, one envelope, one sequencer. Its poverty *is* its sound — every
303 line is recognizably a 303. Infinite flexibility produces anonymous
sounds; constraints produce signatures. This is the circuit-level
justification for the instrument catalog's identity-separation rule: a
track's palette is its fixed architecture.

**Coupled controls beat independent ones.** The 303's accent knob drives
the VCA *and* the filter envelope *and* the resonance behavior from one
control — accented notes get louder, brighter and squelchier together,
which is why they read as one musical gesture. Velocity → level + cutoff
+ drive in a single mapping is more playable than three parameters.

**Drum voices are pinged resonators.** The 808 kick is a bridged-T
oscillator that isn't oscillating — the trigger *pings* it and it rings
down at ~50 Hz, pitch sagging as it decays: precisely the falling-sine
`make_kick`. The 808 snare is two of those pings plus filtered noise; the
hats are six square oscillators at inharmonic ratios through a bandpass —
the anvil's recipe. The catalog's drum functions aren't approximations of
these circuits; they are the same math the circuits compute in voltage.

**The console is the master data structure.** Gain → filter → dynamics →
send → pan → fader, per channel, into buses, into a master. When a script's
mix stage grows confusing, this is the shape to reorganize toward.

(Whether to also *build* circuits is a separate adventure — worth having
the vocabulary above first, since every module in a rack is one of these
blocks with a patch cable where the function call would be.)

---

## 10. The Mix Process, In Order

The order matters because each step changes what the later ones hear:

1. **Sound design in context.** Audition a new voice *inside* the mix
   after the first solo check; solo lies about masking.
2. **Static balance.** Faders only, full arrangement playing. Get it as
   close as levels alone allow.
3. **Carve.** Highpass the non-bass; resolve masking collisions by
   cutting the less important claimant (§4).
4. **Dynamics.** Ducking for the low end; compression only where a *sum*
   misbehaves (§5).
5. **Space.** Pan positions, then depth planes via sends (§6).
6. **Movement.** Automate what was static — filter arcs, per-section
   gains, width changes. (CV thinking, §2.)
7. **The master.** Headroom check, normalize/limit, LUFS + true-peak
   glance, mono fold (§7), and an A/B against a reference track.
8. **Listen elsewhere.** At least one small-speaker or headphone pass;
   every playback system is a different EQ curve.

Steps 1–2 fix most problems. A mix that needs heavy processing at steps
3–5 usually has a balance or arrangement problem wearing a disguise.

---

## 11. Glossary (Quick Reference)

| Term | Meaning |
|------|---------|
| **Gain staging** | Managing levels at every chain stage so nothing clips before the final normalize |
| **Headroom** | Distance between the signal peak and full scale |
| **Crest factor** | Peak ÷ RMS — how spiky a signal is |
| **Masking** | A louder sound hiding a quieter one in the same band |
| **Carving** | Cutting one sound's EQ where another needs to be heard |
| **Channel strip** | The canonical per-channel order: gain → HPF → EQ → comp → sends → pan → fader |
| **Send / bus** | Routing several channels into one shared effect or sum |
| **Compressor** | Automatic fader: reduces gain above a threshold by a ratio |
| **Attack / release** | How fast a compressor reacts / recovers |
| **Sidechain** | Feeding a compressor's detector a *different* signal (kick ducks bass) |
| **Limiter** | ∞:1 compressor — a hard ceiling |
| **Pre-delay** | Gap between dry sound and reverb onset; a distance cue |
| **Haas effect** | ≤ ~30 ms delayed copy reads as width, not echo — with mono-collapse risk |
| **Mono fold** | Summing L+R to check phase cancellation |
| **LUFS** | Perceptual loudness standard (streaming target ≈ −14) |
| **True peak (dBTP)** | Inter-sample peak after reconstruction; master ceiling ≈ −1.0 |
| **Dither** | Noise added at bit-depth reduction to decorrelate rounding error |
| **CV (control voltage)** | Hardware's "every parameter is a signal" — our time-varying parameter arrays |
| **VCO / VCF / VCA** | Oscillator → filter → amplifier: the classic voice architecture |
| **Bridged-T** | The pinged resonator circuit behind the 808 kick — a decaying sine in hardware |
| **Equal-loudness contours** | Ear sensitivity varies by band (peaks 2–5 kHz); judge mixes at multiple volumes |
