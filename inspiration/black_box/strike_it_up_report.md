# Black Box — Strike It Up: Analysis

**Source**: `Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3` (3:31)
**Analysed**: 0.37 s chroma intervals, `--interval 0.5`

---

## Key

Essentia says **C# minor** (strength 0.89 — high confidence). Librosa says G# minor,
which is the relative major/minor ambiguity the KK algorithm often has; trust essentia
here. The maqam comparison flags Double Harmonic / Hijaz Kar and Phrygian Dominant as
top matches (cosine ~0.61–0.63), which suggests the vocal sample or synth riff contains
a raised or flat interval not in standard natural minor — worth listening for a ♭2 or ♯4.

## BPM

**117.5 bpm**, locked solid across all 30-second windows (σ = 0.0). Essentia agrees at
118.4. Pure house grid, no swing or tempo drift anywhere in the track.

## Harmonic timeline

The chroma sequence tells the story in two clear phases:

- **0–40 s (intro)**: G# dominates almost every window with occasional A# and A. This
  is the tonic area of C# minor — the track is circling I before the main groove lands.
- **40 s onward (main section)**: the dominant note cycles through **F# → G# → B → C#**
  repeatedly. F# is the IV, B is the VII, C# is the I — a classic IV–VII–I turnaround
  in C# minor. This pattern runs continuously from ~42 s all the way to ~203 s (3:23).
- **3:23–3:31 (outro)**: the chroma dissolves into G, A, A#, D, C — likely the fade/tail
  with the harmonic content smearing as the track ends.

The shift from G#-dominant (tonic pedal) to the F#/B/C# cycle at ~42 s is where the
main vocal/riff element enters. That transition point is the structural hinge.

## Structure

5 sections detected:
- §1 (0:00–0:02): near-silence / cold intro
- §2 (0:02–0:42): first drop/peak — higher centroid (3209 Hz), 6 ev/s onset density
- §3 (0:42–3:23): main body — densest section (7.5 ev/s, centroid 3403 Hz)
- §4 (3:23–3:29): abrupt energy drop to -68 dB, the track cutting out
- §5 (3:29–3:31): silence/tail

The segmenter didn't find a separate intro/breakdown before the drop — §1 is only 2
seconds. If the track has a longer intro on a different version, it's not present here.

## Instrument hints

The percussive content is clearly electronic — darbuka/doumbek pattern detected (27%
low / 64% high onsets, regularity 0.37), consistent with the programmed percussion
typical of early 90s house. The "ney / oud / qanun" hits from the maqam detector are
almost certainly the vocal sample being misread as wind/plucked instruments — the
sample's pitch content matches that register. The bass synthesizer read is plausible;
the track's low end is thin (17% below 250 Hz), so it's more of a mid-bass than a sub.

## Notes for sampling / remake

- The F#–G#–B–C# chroma loop from 42 s onward maps cleanly onto a C# minor backing.
- The 117.5 bpm grid is tight enough to chop without drift correction.
- The harmonic flat-2 / raised-4 character (if real) would fit a Phrygian or Hijaz
  modal harmony rather than straight natural minor — test against C# Phrygian (D natural).
