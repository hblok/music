# Black Box — Strike It Up: Intro Analysis (1–10s)

**Source**: `Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3`, seconds 1–10
**Analysed**: 0.19 s actual chroma resolution (--interval 0.1, snapped to HOP_COARSE frame)
**BPM**: 117.5 — one beat = 0.511s, one 8th = 0.255s, one 16th = 0.128s

---

## The melodic phrase: exact notes

The chroma timeline at 0.19s resolution (roughly 1.5 sixteenth notes per window) gives
this picture:

```
1.00–2.49s   G#  ×8 windows  ≈ 1.5s ≈ 3 beats  — long held opening note
2.67–3.23s   A#  ×4           ≈ 0.56s ≈ 1 beat  — rises to A#
3.41s        G#  ×1           single 16th        — back down
3.60s         B  ×1           single 16th        — up to B
3.79s        A#  ×1                              — A# again
3.97–4.53s   G#, A#, G#      — ornamental riff returning to G#
4.72–5.83s   A#, G#, A#, A#, A#  — A# becomes more prominent
6.02–9.92s   mostly G#/A# alternating, A# slightly more
```

**Reconstructed phrase** (approximate, MIDI notation in concert pitch):

```
G#4 (dotted half) | G# A# G# B A# | G# A# G# A# A# | G# A# …
```

The entire phrase is built from just three notes: **G#4, A#4, B4** — the root, ♭3, and
minor third of the G# minor scale. No 4th, 5th, or 7th appear. This is a tight,
intentionally narrow riff; the B only appears once as a passing/upper neighbour to A#.

The phrase resolves back toward G# in the final bars (8–10s), which confirms G# as the
tonic/root.

---

## Is it sax or trumpet?

The instrument analysis pipeline is calibrated for Middle Eastern instruments and is
confused here (it's reading "oud/ney"), but the raw acoustic evidence points clearly:

**§1 (1–2s, solo before the beat):**
- Spectral flatness: 0.0001 — extremely tonal, near-pure harmonic series
- Spectral centroid: 944 Hz with G#4 fundamental (~415 Hz) → energy concentrated at
  2nd harmonic (~830 Hz) and above — steep but structured harmonic roll-off
- No vibrato detected in the attack/sustain of the opening held note
- 49.6% harmonic, only 8% percussive — very clean, sustained tone

**§3–§4 (2–8s, with beat underneath):**
- Flatness rises slightly (0.002–0.004) as drum content mixes in
- Vibrato now detected — consistent with a reed instrument's natural sustain vibrato
- Note durations 0.09–0.12s — short, punchy attacks in the riff section

**Conclusion: most likely alto saxophone** (or possibly soprano sax).

- The centroid of 944–2001 Hz for a note around G#4/A#4 is consistent with the
  harmonic envelope of a saxophone in that register. A trumpet in the same pitch range
  tends to sit 500–800 Hz higher in centroid and brighter in the upper partials.
- The vibrato (detected in the riff sections but not in the opening held note) fits
  sax playing style: players often hold the attack straight and add vibrato on the
  sustain.
- The flatness of 0.0001 in the solo opening section is characteristic of a reed/brass
  instrument playing a single sustained mid-range note with little room reverb.
- The note range (G#4–B4) sits squarely in the sweet spot of an alto sax, right where
  the instrument speaks most naturally and projectively.

Trumpet is possible but less likely — the centroid is slightly low for a trumpet in
this range, and the vibrato character and harmonic profile lean toward reed.

---

## Structure of the intro

| Time | What happens |
|------|--------------|
| 0:01–0:02 | Solo horn line, held G#4. Pure tone, no percussion. |
| 0:02–0:04 | Beat enters (high onset density, percussive energy spikes to 37%). Horn continues riff. |
| 0:04–0:08 | Main groove locked in. Centroid 1797 Hz, density 4.7 ev/s. |
| 0:08–0:10 | Slight timbral shift (34.9% harmonic, longer 0.19s notes) — possible phrase breath. |

The segmenter found a clear structural break at 0:02 matching exactly when the
percussion enters. This is the intro's defining moment: one or two bars of solo horn,
then the full beat drops.

---

## Notes for sampling

- **G#4** is the root pitch to tune any sample chop or layering to.
- The opening G# held note (1.0–2.49s) is the cleanest, most isolable window:
  no percussion, very high harmonic purity. A good sample start point.
- The riff from 2.7–4.5s is the repeating melodic idea: G# A# (G# B A#) — 3–4 notes
  max. Simple enough to reconstruct on synth if needed.
- The phrase is minor pentatonic flavour (root + ♭3 only), so it sits over G# minor,
  C# minor, or any tonal centre that uses these as chord tones.
