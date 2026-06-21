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

## Compositional observations

- **Modal / drone-based**: almost no chord movement, C pedal for 95% of runtime
- **Macro-form**: the track builds slowly, peaks around 21–25 min, sustains a long
  plateau (§14), then winds down — a single arch over 70 minutes
- **No real breakdown**: even the quietest mid-sections stay close to the mean RMS;
  drops are very brief (§10, §12, §15, §17 are all under 50 seconds)
- **Texture over harmony**: the interest comes from timbre shifts and percussion
  variations rather than chord progressions
