# Drahtgesang — design notes (the 303 sings the song)

Composition document for review before writing `drahtgesang.py`
(→ `/workspace/music/drahtgesang.wav`). Working title, see Q1.

The brief, from the maschinenherz verdict: **using the 303 with a
melody is super fun — now make a track where a 303 song IS the
theme.** Still trance/psy, harder-edged — *almost* acid techno, but
not all the way: we keep melody, harmony and song form; acid techno's
single-riff jack is the line we walk up to and don't cross.

The inversion of maschinenherz, stated plainly: there the 303 was the
machine's texture and its development was the slow filter arc rising
over seven minutes — OK, but explicitly **not what we're after now**.
Here the 303 is the SINGER. The tune comes first, is stated up front,
and never hides behind a brightness reveal.

- **Genre**: acid/psy trance, four-on-the-floor, ~142 BPM (Q7), ~6:30.
- **Key**: A minor (Q3) — the 303 sweet spot (A1/A2 bass, A3–A4 lead).
  unsung used A minor too; per your own ruling (maschinenherz Q2):
  the scale is not the identity, the melody is.
- **Seed**: `np.random.default_rng(303)` — for once the obvious one.
- Output: `/workspace/music/drahtgesang.wav` (+ mp3). Standalone
  script, helpers duplicated per convention.

## The concept

*Drahtgesang* — wire-song. A machine made of one silver wire, and the
wire sings. Everything in the arrangement exists to let one acid line
be a *voice*: the drums are the floor it stands on, the pads are the
room it sings into, and the only conversation partner is a second,
darker 303 that answers from below (Q2). Where maschinenherz was a
heart learning to sing over a machine, this track is the machine
singing — no borrowed voice, no wet/dry split between heart and
engine. The 303 is both.

## The anti-arc rule (the one hard constraint from the feedback)

**No track-long cutoff ramp. Development never comes from gradually
opening the filter.** What replaces it:

- The cutoff still never parks (the warmth guardrail stands), but it
  breathes in a **per-phrase expression envelope that is part of the
  tune** — the same squelch profile every time the melody returns,
  the way a singer shapes the same line the same way. Accent and
  slide placement are melody notes, not mix moves.
- Development is COMPOSITION: register (the dark low statement, the
  home statement, the octave-up final), the answer 303's counterlines
  growing across the track, the harmony walking under the fixed tune
  in choruses, and arrangement dips.
- Section-to-section brightness may *step* (a verse darker than a
  chorus) as arrangement — it may never *trend* across the track.
  Checkable: the per-statement cutoff profile prints once per
  statement and must be identical (within a tolerance) for identical
  statement types; no monotonic drift across the track.

## The 303 as a refrain voice (the eisgang lesson, applied)

Eisgang's lesson: refrain voices need sustain and slow attack;
percussive attacks carrying a tune read as toys. A 303 is a gated,
plucky instrument — it earns sustain the only way a 303 can:
**slides**. The 303 tie (pitch glides into the next note, no
retrigger) is its legato, and the resonant peak riding a held slide
is its vibrato. So the melody is *written for* the instrument:

- 16th grid; **rests are melody notes** (the gaps make the groove).
- Phrase peaks and phrase ends are **tied/slid** — the long notes
  where the wire actually sings. Target: ≥ 25 % of the refrain's
  sounding 16ths tied (printed and checked — "sings, not plinks").
- **Accents are the stress pattern** of the lyric it doesn't have —
  fixed per phrase, identical every statement.
- Octave drops as punctuation, chromatic passing notes allowed as
  303 idiom (approach notes into slides), one per phrase at most.

The refrain: 8 bars, Q/A at contour level — Q climbs and hangs
off-tonic (on E, the dominant — reachable as a screaming slide-up),
A falls home to A through the signature octave drop. Exact pitches
composed in the script phase, printed in the verify block.

## The band

- **THE LEAD 303** — the singer. Base voice = maschinenherz's warmed
  acid (rolled partials 1/k^1.3, sine body core, within-note
  bright→dark sweep, slides) but pushed **one notch sharper** since
  it must carry the tune over the full track: Q ~6, feedback ~1.3,
  drive tanh(1.5) (Q4). Still guardrailed: never the dune Q 11 /
  tanh 2.8 dentist.
- **THE ANSWER 303** (Q2) — the Hardfloor conversation, one octave
  down, darker (its own lower cutoff band, Q ~4): answers the lead's
  phrase-ends in verses, grows counterlines in the drops, never
  states the refrain itself. Two wires, one song.
- **Psy rolling bass** (K-b-b-b, from the dune kit via maschinenherz)
  — the floor anchor on the A pedal. Where both 303s run, it thins
  to kick-gap sub duty (three voices below 200 Hz is mud).
- **Psy kit** — trance kick, offbeat hats, psy clap, zaps, kick-roll
  builds (same declared dune lifts as maschinenherz; the kit is now
  this directory's psy house style).
- **Dark pads** — the stock `pad_chord`, the room the wire sings
  into: Am–F–G–E laps in choruses (the E major's **G# against the
  A-minor field** is this track's borrowed-leading-tone color — the
  house mechanism, third use, declared), low Am bed in the break.
- **Snare roll + swell** — the era build pair (shared-stock seam
  device; ice-crack stays maschinenherz's, tom fills stay
  ungeschrieben's, ladders stay maschinenherz's W4a).

NOT in the band: the love voice (maschinenherz's heart — this track
has no human voice by design), gothic piano, rompler strings, any
Dune palette, TTS.

## Harmony — one loop, two lights

One progression family: **Am–F–G–E** (i–VI–VII–V), one chord per
bar. Verses sit on the A pedal (psy discipline, the tune carries all
color); choruses walk the lap under the *unchanged* refrain. The Q
phrase hangs on E over the E chord (dominant, G# sounding in the
pad — maximum pull), the A phrase resolves to A across the barline.
The refrain's final held slide lands the G#→A resolution INSIDE the
lead line once per chorus — the singer, not the pad, closes the
loop.

## Structure (sketch — song form, thesis up front)

| t | bars | section | what happens |
|------|------|---------|--------------|
| 0:00 | 4 | thesis | The lead 303 alone, dry, half-filtered: the full Q phrase. The hook in ten seconds — nothing withheld this time. |
| 0:07 | 16 | engine | Kick + rolling bass + hats staircase in; the lead mutters 2-bar fragments low. |
| 0:34 | 16 | verse 1 | THE DARK STATEMENT: full refrain an octave down, dark profile ×2; the answer 303 replies to each phrase-end (2-beat tails). |
| 1:01 | 8 | build | Snare roll + swell, kick rolls, silent beat. No ladder (claimed). |
| 1:15 | 48 | DROP 1 | Refrain in home register ×4 over the A pedal — the floor version. Evolves by forces: statement 1 lead alone / 2 +answer-303 counterline / dip 4 bars (kick + answer 303 only — the understudy's moment) / 3–4 lead + counterline + claps, zaps on 8-bar seams. |
| 2:37 | 16 | chorus 1 | The harmony arrives: Am–F–G–E lap + pads; refrain unchanged ×2 on top; the G#→A close sung by the lead. |
| 3:04 | 16 | break | Floor out. The refrain in AUGMENTATION (half speed) on the lead, filter low but breathing, over the low Am pad — the wire singing slow in the big room. |
| 3:31 | 8 | build 2 | Answer 303 returns first on the pedal (the pickup), roll + swell, silent beat. |
| 3:44 | 48 | DROP 2 | The fusion: BOTH wires in counterpoint — lead sings the refrain, answer 303 runs its own fixed counter-riff beneath (composed, not improvised); harmony walks throughout (the chorus and the drop merge). Dip at 24: both 303s dry and alone, no drums, 4 bars — the two-wire a cappella. Final statements octave-up doubled. |
| 5:07 | 16 | chorus 2 (out) | Fullest: pads up, both wires, last G#→A close rings across the seam. |
| 5:33 | 12 | outro | Strip in reverse order of entry; kick fades. |
| 5:53 | 4+ | bookend | The lead alone again, dry, filter back at the thesis position: the A phrase, ending home on A. The wire finishes the song it started. |

~223 bars ≈ 6:18 + tail at 142 BPM.

Refrain identity: identical melody, accent map and slide map every
statement (register octaves and the augmented break statement are the
two declared transforms). Target ≥ 8 statements counted, first at
bar 0 — the thesis half counts this time? No: same rule as before,
halves and the augmentation are declared fragments; full statements
target ≥ 8 (verse ×2, drop 1 ×4, chorus 1 ×2, drop 2 ×4-ish, chorus 2
×2 — well past it).

## Verify (the script prints)

Per `../VERIFY.md`: section map; refrain statement count ≥ 8 with the
accent/slide maps printed once; per-section RMS ordering (engine <
verse < drop 1; break the trough; drop 2 ≥ drop 1; chorus 2 the
summit or next to it; bookend quietest); seam checklist per boundary;
K-b-b-b gap contract where the rolling bass runs. Plus the two NEW
checks this track exists for:

1. **The anti-arc check**: per-statement cutoff profile printed;
   identical statement types match within tolerance; a linear fit of
   statement-mean cutoff over time has ~zero slope (no trend).
2. **The sings-not-plinks check**: tied/slid fraction of the
   refrain's sounding 16ths ≥ 0.25.

## Open questions for review

1. **Title.** **Drahtgesang** (wire-song — the concept in one word,
   German thread continues). Alternatives: *Silberdraht* (silver
   wire), *Säureherz* (acid heart — maybe too close to
   Maschinenherz). Seed 303 regardless?
   Answer:

2. **One wire or two.** The answer 303 (Hardfloor's two-machine
   conversation: lead sings, a darker one answers from below) gives
   the doctrine's instrument-level Q/A for free and is the classic
   acid-trance texture. Or: ONE 303 only, maximum purity — the song
   truly solo, answers played by register jumps within the same
   voice. Recommended: two — the conversation is where the fun
   compounds, and the two-wire a cappella dip in drop 2 needs it.
   Answer:

3. **Key.** A minor as reasoned above (303 range sweet spot; scale ≠
   identity per your ruling). Fine, or another root?
   Answer:

4. **How sharp may the singer get.** Lead at Q ~6 / feedback ~1.3 /
   tanh(1.5) — a notch past maschinenherz (Q 4.5/1.15/1.2), well
   short of the dune acid (Q 11/1.9/2.8). It has to cut through as a
   lead without becoming the dentist. Start there and judge by ear?
   Answer:

5. **The break's augmentation.** The half-speed refrain over the low
   pad is the plan for the trough (the wire singing slow). Risk: a
   slow 303 line can read as aimless noodling rather than the tune.
   Alternative: normal-speed refrain, dry and nearly alone (the
   thesis texture revisited mid-track). Recommended: try augmentation
   first — it's the one transform that shows the melody is a MELODY,
   not a riff; fall back if it noodles.
   Answer:

6. **How close to acid techno.** As sketched the kit stays psy
   (rolling bass, offbeat hats). The dial toward acid techno would
   be: straighter 909 feel in the drops (open-hat offbeats only, no
   16th ghost carpet), rolling bass thinned to sub duty wherever both
   303s run. Recommended: exactly that split — psy gait in
   verses/build, harder straighter floor inside the drops. Or keep
   full psy throughout?
   Answer:

7. **BPM.** 142 (a hair off maschinenherz's 145; acid lines read
   better with a little more air per 16th). Or hold 145 for a
   matched pair?
   Answer:
