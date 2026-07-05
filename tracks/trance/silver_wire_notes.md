# Silver Wire — design notes (the 303 sings the song)

Composition document for `silver_wire.py`
(→ `/workspace/music/silver_wire.wav`). Title settled (Q1): **Silver
Wire** — English this time, a deliberate break from the German-title
thread; the concept in two words. All open questions answered
2026-07-05; the decisions are folded in below and the original Q&A
kept at the bottom for the record.

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

- **Genre**: acid/psy trance, four-on-the-floor, **142 BPM** (Q7),
  ~5:40 (the break is cut — Q5; duration is not a goal).
- **Key**: **A minor** (Q3) — the 303 sweet spot (A1/A2 low, A3–A4
  lead). unsung used A minor too; per your ruling (maschinenherz Q2):
  the scale is not the identity, the melody is.
- **Seed**: `np.random.default_rng(303)` — for once the obvious one.
- Output: `/workspace/music/silver_wire.wav` (+ mp3). Standalone
  script, helpers duplicated per convention.

## The concept

*Silver Wire* — a machine made of one silver wire, and the wire
sings. **One 303 only** (Q2): everything in the arrangement exists to
let one acid line be a *voice* — the drums are the floor it stands
on, the pads are the room it sings into, and its only conversation
partner is **itself, an octave below**: the register-jump answers.
The same voice drops low to answer its own phrase-ends — a singer
doing both parts. Where maschinenherz was a heart learning to sing
over a machine, this track is the machine singing, solo.

## The anti-arc rule (the one hard constraint from the feedback)

**No track-long cutoff ramp. Development never comes from gradually
opening the filter.** What replaces it:

- The cutoff still never parks (the warmth guardrail stands), but it
  breathes in a **per-phrase expression envelope that is part of the
  tune** — the same squelch profile every time the melody returns,
  the way a singer shapes the same line the same way. Accent and
  slide placement are melody notes, not mix moves.
- Development is COMPOSITION: register (the dark low statement, the
  home statement, the octave-up final), the register answers growing
  across the track, the harmony walking under the fixed tune in
  choruses, and arrangement dips.
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

- **THE 303** — the singer, and the whole melodic cast (Q2). Base
  voice = maschinenherz's warmed acid (rolled partials 1/k^1.3, sine
  body core, within-note bright→dark sweep, slides) pushed **one
  notch sharper** since it must carry the tune: **Q ~6, feedback
  ~1.3, tanh(1.5)** (Q4 — agreed; never the dune Q 11 / 2.8
  dentist). Three registers, one instrument:
  - *home* (A3-centered) — the refrain;
  - *low* (octave down, darker per-phrase profile) — the
    **register-jump answers**: composed echoes of the phrase-ends,
    the singer answering itself; also the dark verse statement;
  - *high* (octave-up doubling) — the final statements only.
- **Psy rolling bass** (K-b-b-b, dune kit via maschinenherz) — the
  floor anchor on the A pedal in engine/verses/builds. **Inside the
  drops it thins to kick-gap sub duty** (Q6): the 303's low register
  owns the mid-bass there.
- **Psy kit, split per Q6**: psy gait outside the drops (rolling
  bass, offbeat open hats, closed 16th ghosts); **straighter, harder
  floor inside the drops** (open-hat offbeats only, no ghost carpet,
  claps) — the acid-techno lean lives in the drops and nowhere else.
  Trance kick, psy clap, zaps, kick-roll builds throughout.
- **Dark pads** — the stock `pad_chord`, the room the wire sings
  into: Am–F–G–E laps in choruses (the E major's **G# against the
  A-minor field** is this track's borrowed-leading-tone color — the
  house mechanism, third use, declared).
- **Snare roll + swell** — the era build pair (shared-stock seam
  device; ice-crack stays maschinenherz's, tom fills stay
  ungeschrieben's, ladders stay maschinenherz's W4a).

NOT in the band: a second 303 (Q2 — one wire), the love voice, any
human voice, gothic piano, rompler strings, Dune palette, TTS.

## Harmony — one loop, two lights

One progression family: **Am–F–G–E** (i–VI–VII–V), one chord per
bar. Verses sit on the A pedal (psy discipline, the tune carries all
color); choruses walk the lap under the *unchanged* refrain. The Q
phrase hangs on E over the E chord (dominant, G# sounding in the
pad — maximum pull), the A phrase resolves to A across the barline.
The refrain's final held slide lands the G#→A resolution INSIDE the
lead line once per chorus — the singer, not the pad, closes the
loop.

## Structure (rewritten per Q5: NO BREAK — the flow is
## thesis → engine → verse → build → DROP → chorus → build → DROP → chorus → out)

With the break cut, the breathers are composed INTO the flow: the
builds start stripped (build 2 kickless — the 8-bar trough), the
drops carry 4-bar dips, and the bookend is the only full stop.

| t | bars | section | what happens |
|------|------|---------|--------------|
| 0:00 | 4 | thesis | The 303 alone, dry, half-filtered: the full Q phrase. The hook in ten seconds — nothing withheld. |
| 0:07 | 16 | engine | Kick + rolling bass + hats staircase in (psy gait); the 303 mutters 2-bar fragments low. |
| 0:34 | 16 | verse 1 | THE DARK STATEMENT: full refrain an octave down, dark profile, ×2; low-register answers tail each phrase (the singer starts talking to itself). |
| 1:01 | 8 | build 1 | Snare roll + swell, kick rolls, composed silent beat. No ladder (claimed). |
| 1:15 | 48 | DROP 1 | Home register over the A pedal; the floor goes STRAIGHT (Q6). Evolves by forces, ×4 statements: 1 — lead alone on the new hard floor / 2 — +register answers / dip 4 bars: kick + the LOW register only (the answer holds the floor alone) / 3 — +claps, answers doubled / 4 — fullest pedal wave; zaps on 8-bar seams. |
| 2:36 | 16 | chorus 1 | The harmony arrives: Am–F–G–E lap + pads (psy gait returns under the walk); refrain unchanged ×2; the G#→A close sung by the lead. |
| 3:03 | 8 | build 2 | The composed trough: kickless, pads out, bass drops to the pedal; the 303 low fragments as its own pickup; roll + swell; silent beat. |
| 3:16 | 48 | DROP 2 | The summit run, straight floor again, ×4: 1–2 — refrain + low answers now COUNTERPHRASED (the answer starts before the phrase ends — the two registers overlap at last) / dip 4 bars: the 303 alone, dry, no drums — the wire a cappella / 3–4 — octave-up doubling joins, harmony keeps walking (chorus and drop merged), arc-free brightness at its composed step-maximum. |
| 4:37 | 16 | chorus 2 (out) | Fullest: pads up, all three registers; last G#→A close rings across the seam. |
| 5:04 | 12 | outro | Strip in reverse order of entry; kick fades. |
| 5:25 | 4+ | bookend | The 303 alone, dry, filter at the thesis position: the A phrase, ending home on A. The wire finishes the song it started. |

196 bars ≈ 5:32 + tail at 142 BPM.

Refrain identity: identical melody, accent map and slide map every
statement; the register octaves are the one declared transform (the
augmentation died with the break). Full statements target ≥ 8:
verse ×2, drop 1 ×4, chorus 1 ×2, drop 2 ×4, chorus 2 ×2 = 14. The
thesis Q-half, bookend A-half, engine/build fragments and the low
ANSWER phrases are declared fragments, uncounted.

## Verify (the script prints)

Per `../VERIFY.md`: section map; refrain statement count ≥ 8 with the
accent/slide maps printed once; per-section RMS ordering (engine <
verse < drop 1; **build 2 is the trough** between chorus 1 and drop 2
— it inherits the cut break's job; drop 2 ≥ drop 1; the summit is
drop 2 or chorus 2; outro settles; bookend quietest); seam checklist
per boundary; K-b-b-b gap contract wherever the rolling bass runs
full (outside the drops). Plus the two checks this track exists for:

1. **The anti-arc check**: per-statement cutoff profile printed;
   identical statement types match within tolerance; a linear fit of
   statement-mean cutoff over time has ~zero slope (no trend).
2. **The sings-not-plinks check**: tied/slid fraction of the
   refrain's sounding 16ths ≥ 0.25.

## Decisions record (Q&A, answered 2026-07-05)

1. **Title** — "Let's go with an English name this time. 'Silver
   Wire' is good." (Seed 303 stands.)
2. **One wire or two** — "Let's go with only one 303, and answers by
   register jumps."
3. **Key** — "A minor is good."
4. **Sharpness** — Q ~6 / feedback ~1.3 / tanh(1.5): "Yes, sounds
   good."
5. **The break** — "Cut the break completely out this time. Let's go
   Thesis, engine, verse, build → Drop. Chorus → build → drop, and
   so on." (Structure above rewritten accordingly; the augmentation
   transform went with it.)
6. **Acid-techno lean** — the psy/straight split: "The split sounds
   fun."
7. **BPM** — "Let's try 142."
