# Maschinenherz — design notes (the first PSY track in trance/)

Composition document for review before writing `maschinenherz.py`
(→ `/workspace/music/maschinenherz.wav`). Working title, see Q1.

The brief: a psy trance track (NOT Frankfurt, NOT dream trance —
harder, faster) that mixes declared borrows from four places:

- **nachtkind** — the *heart*: dry-engine/wet-melodics contrast, the
  Q/A refrain hanging on the raised leading tone and resolving across
  the barline, one-new-element-per-16-bars development.
- **ungeschrieben** — the *engine discipline*: development as a
  printable filter arc (here voiced through the 303, not seq_pluck),
  and the two-reveal instinct — the full refrain is withheld.
- **tech_noir** — the *voice*: `love_phrase`, the plaintive
  nearly-pure glide voice, very wet — the terminator love-song
  singing. As an INSTRUMENT with new melodies in the new key; the
  Terminator tune itself is never quoted.
- **Winter_Vivaldi.md** — *mechanisms only, never pitches*, and only
  the ones eisgang did NOT claim (eisgang owns W3 stamping + W5
  ladder/sigh): W1 shiver-stack additive dissonance, W2 zigzag
  cascade formula, W4a stutter ladder, W8a ice-crack seam.
- **dune psy kit** (water_of_life / sleeper_awakens) — the genre
  machinery: trance kick, K-b-b-b rolling bass, offbeat hats, psy
  clap, psy zap, kick-roll builds, the long-drop mini-dip lesson.
  NO sand: no wind beds, worms, darbuka, duduk, ney, chant, choir.

- **Genre**: psy trance, four-on-the-floor, ~145 BPM (Q3), ~6:00.
- **Key**: E minor (Q2) — every claimed key avoided (F minor =
  ungeschrieben/eisgang, G minor = nachtkind, D minor = tech_noir,
  A minor = unsung, B minor = lost).
- **Seed**: `np.random.default_rng(1997)` — the year German psy broke
  (X-Dream's *Radiaktivität* era; the Frankfurt-to-psy handover).
- Output: `/workspace/music/maschinenherz.wav` (+ mp3). New script,
  standalone, helpers duplicated per convention.

## The concept

A machine heart that learns to sing. The psy engine is the machine —
bone dry, mechanical, static on its E pedal, harder and faster than
anything else in this directory. The tech_noir voice is the heart —
plaintive, human, drenched in the long hall. The track is the two
meeting: the engine runs, the voice sings *over* it, and in the final
drop they trade question and answer. nachtkind's dry/wet contrast
IS this concept mixed as sound: drums and bass and 303 bone dry, the
voice and pads in the big wet space behind them.

## Harmony — static engine, walking heart

Psy verses sit on ONE root; Frankfurt choruses walk. Both, as the
form's duality:

- **Verses/drops**: static E minor over the rolling-bass pedal —
  authentic psy. Color from the lead lines, never chord changes.
- **Choruses (the refrain)**: the harmony arrives as an *event* —
  Em–C–D–B (i–VI–VII–V), the nachtkind progression family
  transposed. The **D# of the B-major V chord** against the E-minor
  field is THE gothic color (nachtkind's F#→G mechanism, new key):
  the refrain's question phrase hangs ON the D#, the answer resolves
  D#→E across the barline. Every chorus→verse seam resolves the same
  way — the walking harmony collapses back onto the E pedal.

One progression family, doctrine rule 4: E natural minor + the one
borrowed D#, nothing else.

## The band (all declared borrows or dune lifts, one new voice port)

Bone dry (the machine):

- **Trance kick** — dune `water_of_life` recipe (150→45 Hz dive).
- **Psy rolling bass** — the K-b-b-b engine, root E: kick on the
  beat, bass on the three 16ths after (gains .8/.7/.95), saw
  lowpassed at 350 Hz, short gate. The 350 Hz lid is why this saw
  never reads harsh — it's the sanctioned psy exception to
  "no continuous 16th bass" territory; the kick-gap IS the rest.
- **303 acid** — sleeper_awakens' within-note sweep (that sweep is
  what makes acid read as acid, keep it) but WARMED per Q4: rolled
  partials `1/k**1.3` before filtering, resonance capped ~Q 4–5
  (not 11), feedback ≤ 1.2× (not 1.9), drive `tanh(1.2)` (not 2.8),
  a sine sub under it, and the cutoff NEVER parks — it rides the
  printable filter arc (the ungeschrieben device, declared). Slides
  kept. Not hard saw; acid without the dentist.
- **Offbeat hats** — open on every offbeat, closed 16th ghosts L/R.
- **Psy clap** — beats 2 & 4 through drops, panned L/R.
- **Psy zap** — 8-bar phrase punctuation inside drops.
- **Kick-roll builds** — 8th→16th rising-gain bars into drops.

Very wet (the heart — long dark hall, ~5–6 s IR, wet ≈ 0.5):

- **THE VOICE** — tech_noir `love_phrase` ported (declared): sine +
  3 rolled harmonics, glide curve, 5.2 Hz late vibrato, LP 3000.
  Sings the refrain and its fragments — new melodies only. Octave
  double joins in the final drop.
- **Dark pads** — the stock `pad_chord`, carries Em–C–D–B in
  choruses, a low E drone bed in the break.
- **Zigzag arp (W2)** — the cascade formula as a sequencer cell:
  root–octave–octave–fifth / fifth–♭3–♭3–root, stated on rising
  chord tones (state, restate higher, restate higher, cadence) —
  motif development for free. Glassy pluck voice (lost family),
  chorus support layer.

## The Vivaldi mechanisms (unclaimed ones only, no pitches)

- **W1 shiver stack → the intro**: additive layers that increase
  *dissonance*, not just density. Over the E pedal, one repeated-8th
  stab voice enters per 4 bars — first bare octave, then a 2nd-clash,
  then a tritone color — and the first fully consonant Em lands
  exactly when the kick drops. The psy staircase intro and the 1725
  intro are the same idea; this composes them together.
- **W4a stutter ladder → the pre-drop builds**: the 303 locks onto
  ONE pitch in 16th/32nd retrigger for a bar, then re-locks a step
  higher, climbing chromatically OUT of the key (the wrong-note
  tension is the point), cutoff rising along the arc, into the drop.
  A gate riff with a built-in build.
- **W2 zigzag cascade** → the chorus arp cell (above).
- **W8a ice-crack → the seam device**: stab — silence — upward flick,
  the composed glitch fill. This is the track's transition vocabulary
  instead of tom fills (ungeschrieben owns those) or reverse cymbals
  (nachtkind owns that). Psy glitch culture and 1725 agree here.

## Structure (sketch — song form with a withheld reveal)

| t | bars | section | what happens |
|------|------|---------|--------------|
| 0:00 | 4 | thesis | The voice alone in the hall: the refrain's question phrase, once, hanging on D#. Air bed under it. (Doctrine: thesis in 10 s.) |
| 0:07 | 16 | shiver intro (W1) | E pedal drone + stab voices entering one per 4 bars, dissonance rising; kick-roll build in the last bar. |
| 0:33 | 16 | engine start | Kick + rolling bass lock in; hats, then clap staircase in (gains held ≤ 0.8 pre-drop). |
| 1:00 | 16 | verse 1 | 303 enters low and dark, cutoff arc rising; voice sings 2-bar FRAGMENTS of the refrain (ghost foreshadow — the two-reveal instinct). |
| 1:26 | 8 | build (W4a) | Stutter ladder climbs; kick roll; one silent beat. |
| 1:39 | 32 | DROP 1 | Full psy engine, 303-led. Mini-dips at 16 (kick+303 only, 4 bars). Zaps on 8-bar seams. The voice is ABSENT — the machine's drop. |
| 2:32 | 16 | chorus 1 | The harmony event: Em–C–D–B arrives, pads + zigzag arp; the voice sings the FULL refrain for the first time (the reveal). Q hangs on D#, A resolves to E. |
| 2:59 | 16 | break | Engine out (ice-crack seam, W8a). Voice + pads + low drone: the refrain restated slow, half-voice; heartbeat-quiet. |
| 3:25 | 8 | build 2 | Ladder again, higher entry; roll; silent beat. |
| 3:38 | 32 | DROP 2 / fusion | The payoff: full engine AND the walking chorus harmony AND the voice + octave double — 303 answers each vocal phrase-end in the gaps (composed trades, Q/A level 2). Mini-dip at 16: voice + kick only, 4 bars. |
| 4:31 | 16 | chorus 2 (out) | Fusion continues, arp on top — fullest 16 bars; last refrain statement. |
| 4:58 | 16 | outro | Strip layer by layer (bass out, 303 dims down the arc to its intro cutoff, hats out); kick fades like a calming heartbeat. |
| 5:24 | 4 | bookend | The voice alone again: the ANSWER phrase this time, resolving D#→E. Hall tail rings out. |

Refrain identity: the sung refrain melody is identical every full
statement (target ≥ 6 counted: thesis-half, chorus 1, break, drop 2
×2 waves, bookend-half; halves count as declared).

## Verify (the script prints)

Per `../VERIFY.md`: section map with times; refrain statement count
≥ 6; per-section RMS with ordering (drop 2 ≥ drop 1 > verse; break
is the trough; outro settling); seam checklist naming the device at
every boundary (ice-crack / zap / roll / silent beat / ringing
chord); the 303 filter arc printed with rise / global max inside
drop 2 / return-to-intro checks (the ungeschrieben device, checked
the ungeschrieben way); and the psy-bass gap check — the bass is
SILENT on every kick 16th (the K-b-b-b contract, printed as a duty
line like eisgang's).

## What stays banned here

Frankfurt kit and centerpieces (gothic piano, rompler strings,
reverse cymbal, the Eye Q 909 carpet); everything Dune-palette
(wind, worms, darbuka, duduk, ney, chant, choir — no sand storms, no
chants); TTS in any form (the voice is `love_phrase`, a synth
instrument — unsung stays a dead end); hard-saw acid (Q4
guardrails); risers other than the composed ones named above; W3 and
W5 (eisgang's claimed Vivaldi mechanisms); quoting any Vivaldi or
Fiedel pitch sequence.

## Open questions for review

1. **Title.** Working title **Maschinenherz** (machine heart — the
   concept in one word, and it keeps the German-title thread of
   nachtkind/ungeschrieben). Alternatives: *Herzmaschine*,
   *Nachtmaschine*. Seed 1997 as reasoned above — or pick another
   thematic year.
   Answer: Maschinenherz - perfect.

2. **Key.** E minor recommended (all claimed keys avoided; E pedal
   sits well for the rolling bass at E1/E2). Any reason to prefer
   another?
   Answer: E minor - good. (Just note our previous conclusion: the scale is not identity; we can afford to share scale across. (For a 7-note scale like D minor (D, E, F, G, A, B♭, C) using exactly 7 unique notes without repetition, there are 5,040 different sequential combinations. And this of course grows with longer sequences and melodies. Thus, the melody is the identity of the song)).

3. **BPM.** 145 recommended (psy's home range 140–148; clearly
   harder/faster than nachtkind's 139 and eisgang's 138). Go higher
   (148) for more aggression, or hold 145?
   Answer: 145 is good

4. **How much squelch on the 303.** The dune sharp-303 (Q 11,
   feedback 1.9×, tanh 2.8) is era-authentic psy but violates every
   warmth rule; the plan above caps it (rolled partials, Q 4–5,
   feedback ≤ 1.2, tanh 1.2, sine sub, always-sweeping cutoff) —
   between ungeschrieben's sanctioned Q 2.2 and the dune acid.
   Recommendation: build the capped version first, and treat the Q/
   feedback pair as the one knob to push if it reads flat rather
   than starting hard. Agree, or start closer to the dune recipe?
   Answer:

5. **The voice's reach.** As planned it sings fragments (verse 1),
   the full reveal (chorus 1), the break, and the fusion trades
   (drop 2). Should it ALSO ride inside drop 1 (more voice, less
   contrast), or is drop 1 staying machine-only the right reading of
   the concept (recommended — the reveal lands harder)?
   Answer: Yes, agree with recommended - reveal lands harder.

6. **Drop lengths.** Two 32-bar drops with one mini-dip each (~53 s
   at 145). The dune lesson says 64-bar drops work if they evolve;
   going 64+64 would push the track toward ~7:30. Recommendation:
   32+32 — this track's story is the voice/machine meeting, not a
   floor marathon. Stretch if you want a DJ cut?
   Answer: Let's stretch, but make sure evolves, not just repeat. 

7. **The ending.** Bookend as planned (voice resolves D#→E, hall
   rings out) vs ending cold on the machine (tech_noir's move —
   the heart stops). The bookend says the heart wins; the cold stop
   says the machine does. Recommended: the bookend — every borrow
   here is about the machine learning the song, and psy tracks
   traditionally land, not cut.
   Answer: Yes, let it land and fade - the heart wins.



