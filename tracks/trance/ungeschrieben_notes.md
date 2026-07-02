# Ungeschrieben — design notes (the two-reveal form)

Composition document for review before writing `ungeschrieben.py`
(→ `ungeschrieben.wav`; filename follows the title — see question 1).

Inspiration: **Zyon — No Fate (Struggle Continues Mix, 1992)**, per
`inspiration/Zyon-No_Fate.md` — early Frankfurt proto-trance / dream
trance. This is a NEW track with its own story, not a cover: we take the
*form* (hypnotic simmer → string reveal → reduction → bigger second
reveal → ride-out), the *palette era* (909, rolling mono bass, resonant
sequence, rompler strings, no supersaws, no sidechain), and write our
own theme, story, and title.

**The story**: the future is unwritten. The sequence is the present —
one bar, repeating forever, asking the same question over and over,
changing only in how brightly it dares to ask (the filter). The strings
are the future — glimpsed once (reveal 1), doubted (the reduction),
then *chosen* (reveal 2, the peak). Hopeful defiance, not hands-in-the-
air euphoria.

- Tempo/key: **130 BPM, F natural minor** (Aeolian — no leading tone,
  no gothic F#; that's nachtkind's color, not this track's). New key =
  own identity: nachtkind owns G minor + piano, tech_noir D minor +
  machine, lost D/Bm + the journey. This one: F minor + strings.
- Harmony: **i–VI–VII** (Fm–Db–Eb), the era's loop. Groove sections sit
  on an Fm pedal (static, hypnotic); *the strings bring the harmonic
  movement with them* — that's what makes the reveals feel like arrival.
- Seed: `np.random.default_rng(1992)  # the year of No Fate`.
- Length ~5:40–6:10 — the bars the material needs.
- Output: `/workspace/music/ungeschrieben.wav` (+ mp3).

## How the song doctrine maps onto the two-reveal form

1. **The refrain is the string theme** — 8 bars, Q/A at contour level:
   antecedent rising over Fm–Db–Eb and hanging on the VII (Eb — no
   dominant pull in Aeolian, it hangs rather than leads), consequent
   falling home to F over the same chords ending i. Identical melody at
   both reveals; reveal 2 is bigger by *forces* (octaves, descant,
   count), never by changing the tune.
2. **The question is the sequence.** A 1-bar arpeggio cell that NEVER
   changes notes — all its development is the filter (the era's way:
   filter movement instead of melodic development, and instead of
   risers). The doctrine's "state, vary, answer" happens in the cutoff
   curve, printed and checked (see verification).
3. **THE DELIBERATE DOCTRINE DEVIATION — the withheld thesis.** Rule 6
   says state the hook in the first ten seconds. This form's whole
   payload is that the strings are a *reveal* — an early statement
   spoils it. Per the standing principle (the rules serve the music),
   we replace the thesis with a **ghost foreshadow**: once in the
   intro, one dark string voice plays the theme's first phrase through
   a nearly-closed filter, drowned in the hall — half-heard, not
   stated. The check changes accordingly: *zero* full string
   statements before reveal 1 (the ghost is a fragment and doesn't
   count). See question 3.
4. **The fusion payoff** still exists, mapped to this form: at reveal 2
   — and only there — the sequence's filter reaches fully open at the
   same moment the strings peak. The question at full voice under its
   answer. (Reveal 1 rides over a still-half-closed sequence.)
5. **Seams**: filter sweeps, crash cymbals, **909 tom fills** (new),
   and ringing string chords. This track's own vocabulary — no
   white-noise risers (post-era), and no reverse cymbals (that's
   nachtkind's signature; identity separation).

## New instruments (the recipes this track adds)

1. **Rompler strings (M1/D-50 character)** — the emotional centerpiece
   and the biggest new recipe. Not the nachtkind pad (dark sine), not
   the lost cello (solo bowed): a big, slightly *synthetic* sampled-
   strings ensemble. Sketch: per chord voice, a rolled-off saw stack
   (warmth recipe spectrum) + a 2–5 kHz breath-noise bow layer riding
   the same envelope, two detuned copies (chorus width), a fast-ish
   sampled-attack (~120 ms — rompler strings speak faster than analog
   pads), a slow ~6 Hz amplitude flutter (the sample-loop wobble that
   makes it read as *sampled*), long hall (wet ≥ 0.55). Voiced in
   octaves for the reveals.
2. **The sequence** — brighter and more resonant than lost's glassy
   pluck: a plucked analog cell with a real resonant peak riding a
   slowly swept lowpass. The era wants audible resonance; the warmth
   recipe warns about acid bite. Guardrails: moderate Q (~2–2.5), soft
   drive (tanh 0.8), sine sub under it — and the resonance *sweeps*, it
   never parks and screams. See question 4.
3. **909 toms** — high/mid/low pitched-thump family (sine 200/150/110 Hz
   falling, short), used ONLY as transition fills (the era's seam
   device). Two or three fills in the whole track.
4. **Spoken word** — see question 2. If used: our own line, synthesized
   via the existing TTS+OLA pipeline (technique reuse, no Dune
   content), dry, sparse — intro and reduction only, tempo-synced
   delay tail.

Reused as-is: 909 kick/hats/claps recipes (lost_v6 kit, dialed rawer:
punchy not sub-heavy), rolling 16th mono bass on the F pedal with
octave jumps (the lost/nachtkind warmed recipe, single-note discipline),
dark breakdown pad, crash. **Sparse-layering rule from the blueprint:
kick/bass/hats + ONE sequence + ONE string/pad layer at a time.** The
sparseness is the identity; resist stacking.

## Structure (~184 bars + tail, bar = 1.85 s)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | intro (16) | Kick alone, then hats; the sequence enters with the filter nearly CLOSED (a dark throb, barely a pitch). Spoken line (if kept) lands dry ~bar 6. The GHOST at bar 10: one drowned string voice, first phrase only, half-heard. |
| 16 | 0:30 | groove (32) | Bass rolls in on the F pedal; the sequence proper; additive 16-bar cycles (+open hat, +claps at 2&4). The filter opens gradually across the whole section — the question asked braver and braver. |
| 48 | 1:29 | pre-reveal (8) | The filter sweep crests, hats double, tom fill in the last bar, crash → |
| 56 | 1:44 | **REVEAL 1** (24) | THE STRINGS: the theme 2× (Q/A), harmonic movement arrives with them (Fm–Db–Eb under the melody for the first time); 8 more bars of sustained string chords riding the groove. Sequence stays half-open under it. Last chord rings across — |
| 80 | 2:28 | reduction (24) | Strings recede to the dark pad; claps and open hat strip out; the bass filters down; the spoken line returns (or the ghost, again); the sequence's filter CLOSES back down — doubt. |
| 104 | 3:12 | rebuild (8) | Filter reopens faster than before, bass brightens, hats return, the long tom fill, crash → |
| 112 | 3:27 | **REVEAL 2** (32) | The peak: theme 3×, strings in octaves, a high descant answering the consequent phrases; **the sequence reaches fully open here — question and answer at full voice at last** (the fusion). Loudest section of the track. |
| 144 | 4:26 | ride-out (24) | Peel in reverse order: descant gone, strings hand back to the pad, claps out, the filter starts its long descent. |
| 168 | 5:10 | outro (16) | Drums and bass, then bass out; the sequence filters down until it is the intro's dark throb again — the bookend is the *filter position*, not a melody. Kick stops; the throb + one last string chord ring out. |

## Verification (per ../VERIFY.md — the two-reveal variant)

- Section map; seam checklist (sweep / crash / tom fill / ring).
- **String-theme count**: full statements — reveal 1: 2, reveal 2: 3,
  target total >= 5. AND: **zero full statements before bar 56** (the
  ghost is a filtered fragment, uncounted — the reveal must be a
  surprise). Both printed.
- **The filter arc, printed and checked**: sequence cutoff at each
  section boundary (from the automation curve itself, not audio):
  rises monotonically across the groove, drops in the reduction,
  reaches its global maximum inside reveal 2, returns to ~intro value
  in the outro.
- Per-section RMS: intro < groove < reveal 1; reduction is the trough
  between the reveals; **reveal 2 is the loudest section**; ride-out
  descends; outro lands near intro level.
- Banned-list audit (by construction, stated in the printout): no
  supersaw, no sidechain pump, no white-noise riser, no reverse cymbal.

## Open questions for review

1. **Title / story language**: *Ungeschrieben* (German, "unwritten" —
   fits the Frankfurt scene and the story; my recommendation), vs
   *Wendepunkt* ("turning point"), vs English *Unwritten*. The
   filename follows the answer.
   Answer: Ungeschrieben is fine.

2. **The spoken word**: the blueprint's concept-carrier is a dry
   spoken sci-fi line. Options: (a) synthesize OUR OWN line with the
   existing TTS+OLA pipeline (recommended — e.g. "Die Zukunft ist
   ungeschrieben" or an English equivalent; we do NOT set the actual
   T2 quote), (b) fully instrumental — the strings carry the concept
   alone, (c) a whispered-texture almost-voice. If (a): which
   language, and female or male voice? Note this would be the first
   voice in the trance/ tracks — easy to drop later if it cheapens it.
   Answer: Very exited by this. And yes "Die Zukunft ist ungeschrieben" can work - although, a suspect it might be difficult to fit it into a bar. It doesn't carry much rhythm in itself. Also, yes, a knob which can silence the voice in case it doesn't work at all would be welcome - make sure the is clearly documented in the code.
   Furthermore, if I'm reading the structure map correct, the spoken words are repeated at least three times. It could be, that that's too much. In very many trance and techno tracks, such samples or words were dropped in only once, as a single sample, and that's it. (Very often, these tended to be samples from movie). I suspect, our line is more similar to that, rather than a repeating element.

3. **The withheld thesis** (doctrine deviation): confirm replacing the
   early hook statement with the single drowned ghost foreshadow, and
   the check flipping to "zero full statements before reveal 1". I
   recommend yes — the reveal IS this form.
   Answer: Yes, sounds good.

4. **Sequence resonance**: era-authentic moderate resonance (Q ~2–2.5,
   swept, guardrailed as above — my recommendation) vs staying fully
   inside the conservative warmth recipe (Q 1.2)? The resonant sweep is
   a big part of the 1992 sound; the guardrails should keep it round
   rather than acid.
   Answer: Yes, era-authentic sounds good.
   
