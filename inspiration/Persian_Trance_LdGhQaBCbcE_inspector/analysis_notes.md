# Persian Trance — Analysis Notes

Source: `Persian_Trance_LdGhQaBCbcE.mp3`  
Duration: 1:10:20  
Analysed with: `/repos/music/inspector` (librosa 0.11 + essentia 2.1-beta6)

---

## Tempo — ~95–99 BPM

The global BPM estimator returns 129 but that is a doubling artefact.
The per-window table shows the track sits consistently at **95–99 BPM** throughout,
with the detector occasionally halving/doubling (92↔184, 99↔198).
There are no meaningful tempo changes — this is a locked, machine-quantised groove.

## Key — C minor

- librosa (Krumhansl-Kessler): C major, correlation 0.61
- essentia (KeyExtractor):      **C minor**, strength 0.78  ← more confident reading

The low correlation on both estimates is expected: Persian/Middle Eastern scales
use augmented seconds and intervals that don't map to the 12-note chromatic grid,
so chroma energy bleeds across adjacent semitones. The result is an unusually flat
chroma profile (C=1.00, G=0.63, C#=0.58 … down to D#=0.32) rather than the
sparse 3–4 note cluster you'd see in a purely diatonic track.

Trust essentia's **C minor** as the closest Western approximation.
The actual mode is likely **C Phrygian Dominant** (C–D♭–E–F–G–A♭–B♭),
a.k.a. the Spanish/Persian scale, which is common in this genre.

## Harmony — C pedal throughout

The dominant note per minute is C for almost the entire 70 minutes, with three
brief excursions:
- **7:00–9:00** → G  (perfect fifth, classic drone shift)
- **9:00–12:00** and **22:00–25:00** → C#/D  (flat-2 / Phrygian upper neighbour)
- **58:00–1:01:00** → D  (transition section)

This is extremely tonal/modal — essentially a single-drone composition built on
C as a pedal, with occasional moves to the ♭2 and ♭7.

## Structure — 20 sections, one long central movement

| Range | Duration | Character |
|---|---|---|
| §1  0:00–0:13 | 13 s | Cold open / silence |
| §2  0:13–2:54 | 2:41 | First peak (RMS –13.8 dB, dense) |
| §3–§6  2:54–15:30 | ~12 min | Main body, two sub-drops |
| §7  15:30–18:29 | 3 min | Build (rising centroid) |
| §8–§9  18:29–24:36 | 6 min | Second peak cluster |
| §10, §12  brief | <30 s | Micro-drops (silence) |
| §13  28:21–37:38 | 9:17 | Extended main movement |
| **§14  37:38–57:24** | **19:46** | Long undifferentiated plateau — the centrepiece |
| §15–§17  57:24–1:00:58 | ~4 min | Wind-down / transition |
| §18–§20  1:00:58–1:10:20 | ~9 min | Outro movement, darker centroid |

Section §14 is a nearly 20-minute sustained passage where spectral features
are stable enough that the segmenter treats it as one block.
Re-run with `--sections 30` to force finer cuts into that region.

## Timbral character

- **Very bass-heavy**: 44% of spectral energy below 250 Hz — dominant kick/sub-bass
- **Dark**: avg spectral centroid 961 Hz (typical pop/rock sits around 2–3 kHz)
- **Minimal high end**: only 8.6% above 4 kHz — few cymbals or air
- **Moderate density**: 3.6 events/sec average (not a fast-arpeggiated style)
- RMS swing: –20.1 dB (drops) to –13.8 dB (peaks) — about 6 dB dynamic range

## Scale / Maqam

The maqam comparison built a pitch-class histogram from pYIN-tracked melody across
all sections and correlated it against Arabic/Persian scale templates.
All five top scores cluster tightly (0.491–0.503), which mirrors the flat chroma
profile: the track doesn't cleanly belong to one 12-TET scale.

Top matches:
1. **Phrygian Dominant / Maqam Hijaz / Dastgah Homayoun** (0.495)
2. **Double Harmonic / Maqam Hijaz Kar** (0.492)
3. Major / Natural Minor — nearly tied (0.491)

The presence of a prominent flat-2 (C# at relative energy 0.58) and the strong G
(0.63) tips the balance toward **Dastgah Homayoun** or **Maqam Hijaz**:
C – D♭ – E – F – G – A♭ – B♭. The major 3rd (E natural) distinguishes these from
pure minor modes, consistent with what the ear hears as the "exotic" raised-3rd
character of Persian music. Quarter tones (half-flats) that exist in the
original scale are approximated to the nearest semitone in this analysis.

## Harmonic / Percussive balance

HPSS (harmonic-percussive source separation) per section:

- Track average: **~52% harmonic, ~12% percussive** (remainder is residual/noise)
- Dense sections §4–5 (6:27–12:05) and §18 (1:00:58–1:03:55): harmonic drops
  to 33–45% as percussion is most prominent
- §1 (cold open): 91% harmonic — essentially pure pad/drone with no drums
- §17 (13-second micro-drop at 1:00:45): 97% harmonic — reverb tail only
- The high harmonic fraction overall is consistent with rich melodic/pad layering
  sitting well above the percussive element in the mix

## Instrument estimates

Analysis via HPSS + pYIN pitch tracking + onset profiling:

**Confirmed with HIGH confidence:**
- **Synthesizer pad** — high harmonic energy, very low spectral flatness (≈0.008),
  sustained throughout; the sonic "floor" of the entire track
- **Bass synthesizer / sub-bass** — accounts for much of the 44% energy below 250 Hz;
  machine-generated, sustained, no human drift
- **Darbuka / Doumbek** — onset low:high ratio 27%:37% matches the characteristic
  doum (low) / tak (high) split; regularity 0.33 is loose enough to be a humanised
  pattern rather than pure step sequencing
- **Riq (Arabic tambourine)** — consistent with the same mixed low/high onset
  profile; may overlap with or be the same layer as the Darbuka reading

**Plausible with MEDIUM confidence:**
- **Ney (Persian end-blown flute)** — vibrato detected throughout (depth ~3 semitones);
  note: 3 st is too large for acoustic finger vibrato (0.3–0.8 st is typical) —
  this is more likely a **synth ney with LFO pitch modulation**, a very common
  production technique in this genre. The breathy timbre signature is real.
- **Qanun (zither)** or **Oud (Arabic lute)** — short melodic events detected in
  the mid range; however pYIN frequently locked onto the sub-bass fundamental
  (C2) rather than the melodic line, so note duration (0.16 s) and low pitch
  centre are partially artefacts. A dedicated melody-separation step (e.g. Demucs)
  would be needed to confirm.

**Analysis caveats:**
- pYIN's minimum frequency (C2 ≈ 65 Hz) causes it to latch onto kick/sub-bass
  transients in the harmonic component, polluting melodic pitch estimates
- "Vibrato depth" of 3+ semitones across all sections reflects pitch-modulated
  synth effects or LFO, not acoustic instrument vibrato
- Hi-hat / Electronic kick receive MEDIUM/LOW estimates partly because the
  darbuka onset pattern absorbs most of the percussive energy signature;
  whether the percussion is acoustic darbuka or a sample/synth replica is
  indistinguishable from spectrum alone

## Compositional observations

- **Modal / drone-based**: almost no chord movement, C pedal for 95% of runtime
- **Macro-form**: the track builds slowly, peaks around 21–25 min, sustains a long
  plateau (§14), then winds down — a single arch over 70 minutes
- **No real breakdown**: even the quietest mid-sections stay close to the mean RMS;
  drops are very brief (§10, §12, §15, §17 are all under 50 seconds)
- **Texture over harmony**: the interest comes from timbre shifts and percussion
  variations rather than chord progressions
