# Ungesungen — design notes (the vocal song)

Composition document for review before writing any code. Per the roadmap
in `idea.md`: next candidate is "a second original in a proven shape, or
a new shape entirely — note doc with embedded questions first, as
always." This is BOTH: **song form** (the proven lost/nachtkind shape)
carried, for the first time, by a **singing voice** — the new shape is
the vocalist, not the architecture.

**Where this comes from.** `ungeschrieben` proved the voice pipeline is
easy: edge-tts renders a clean German line, cache-first, with a
documented gain knob and a graceful instrumental fallback. That was one
*spoken* drop. The question this track answers: can we make an actual
**vocal song** — the refrain *sung*, on pitch, on the grid? The repo
already holds every ingredient, just never combined:

- the **spoken-word pipeline** (edge-tts + cache + sampler treatment) —
  `ungeschrieben.py:get_voice`;
- the **OLA pitch/speed machinery** (independent pitch shift and time
  stretch) — `dune/voices.md`, `generate_voice_samples.py`;
- the **sung vowel-voice engine** (melodic glottal source, vowel
  formants, vibrato, chest layer) — `generate_sihaya.py`;
- and the written next step: `dune/more_ideas.md` **C7 "Real vocals /
  real lyrics"** sketches exactly this — TTS rendered syllable by
  syllable, OLA-mapped onto the melody grid, or a hybrid grafting TTS
  consonant onsets onto the vowel engine's held notes.

**The story** (and the title): *Ungesungen* — "unsung." The companion
piece to *Ungeschrieben*. That track said the future is unwritten; this
one is about the song that was always there and never had a voice — the
trance tracks themselves, instrumental by doctrine until now, finally
singing. The lyric is minimal and mantra-like (era-correct): the hook
says what the track does.

**Era blueprint**: Frankfurt again, one step further down the same
timeline — **Jam & Spoon, "Right in the Night" (1993/94)**: real sung
female vocal over classic trance, same scene as nachtkind's Eye Q and
ungeschrieben's proto-trance. Melancholic-warm, hypnotic groove, the
vocal as the emotional center — NOT hands-in-the-air 2000s uplifting
vocal trance (no supersaws, no sidechain pump; those postdate the era).
See question 8 on whether we write a proper inspiration doc first.

- Tempo/key: **132 BPM, A natural minor** (Aeolian). New key = own
  identity (the standing rule): nachtkind owns G minor + piano,
  tech_noir D minor + machine, lost D/Bm + the journey, ungeschrieben
  F minor + strings. This one: **A minor + the voice.** A minor also
  sits the melody comfortably on a female neural voice's natural range
  (hook centered ~A3–E4, small pitch-shift ratios = fewer artifacts;
  see the recipe notes below). See question 7.
- Harmony: **i–VI–III–VII (Am–F–C–G)** — the classic early-vocal-trance
  loop (the *Right in the Night* family), one progression family for
  the whole track per doctrine rule 4. The relative-major pivot (C, G)
  lets the identical refrain land warm or sad by rotation — the lost_v6
  re-lighting trick is available if we want it.
- Seed: `np.random.default_rng(1994)  # the year the Frankfurt vocal broke`.
- Length ~5:30–6:00. Bar = 1.818 s at 132 BPM.
- Output: `/workspace/music/unsung.wav` (+ mp3) — English title per the
  question-3 answer, so the track is **Unsung** (`unsung.py`).

## THE DOCTRINE AMENDMENT (must be sanctioned — question 1)

`idea.md`, "What stays behind": *"Vowel singing. These tracks stay
instrumental... the 'voice' work continues in the dune songbook, not
here."* This track deliberately breaks that rule — that is its entire
premise. Per the standing principle (the rules serve the music), the
proposal:

- Amend `idea.md` to date the rule: the instrumental-only rule held for
  the first four tracks; `ungesungen` sanctions the voice as a trance
  instrument, with its own identity separation (TTS-derived singing —
  NOT the dune vowel engine's sound; if the hybrid path wins, the
  engine is a component under real consonants, not the exposed timbre).
- Everything else in "what stays behind" still stands: no Dune palette,
  no chant/choir, existing genre rules load-bearing.

## Feasibility, honestly — and the staged plan (question 2)

Sung TTS is the riskiest recipe in the repo so far. What we know:

- **Proven**: edge-tts German line, clean and dry (ungeschrieben);
  OLA pitch/speed with known-good ranges (dune voices); pitch-perfect
  sustained vowels (sihaya engine); syllable-level melody mapping is
  designed on paper (C7).
- **Unproven**: pitch-*quantizing* a TTS syllable to a target note
  (needs per-syllable f0 estimation — autocorrelation on the voiced
  part — then resample by target/measured ratio, then OLA back to the
  note's grid duration); how musical the result feels; whether
  formant shift ("chipmunk"/"giant") stays acceptable. Guardrails:
  keep every shift within ±4 semitones of the voice's natural f0
  (the melody is *written to the voice*, another reason for A minor),
  and let vibrato come from our own 5.5–6 Hz pitch LFO applied after
  quantization, not from the TTS prosody.
- **The C7 fallback ladder**, cheapest risk first:
  (a) pure TTS+OLA singing;
  (b) **hybrid** — TTS consonant onset (~first 80 ms of the syllable)
  grafted onto a sihaya-engine sustained vowel that holds the pitch
  perfectly: real intelligibility, synth control;
  (c) if both disappoint: the hook stays sung by an instrument and the
  voice contributes spoken/whispered lines only (the proven
  ungeschrieben mode) — the track still works as a song.

**Stage 1 — the probe** (before the track): a tiny standalone script,
`ungesungen_probe.py`, renders ONE hook line three ways over a bare
Am–F–C–G pad: (a) TTS+OLA sung, (b) hybrid, (c) sihaya vowel engine
alone as the control. Three short WAVs, one listen, one decision. The
full track is gated on this A/B. (Probe WAVs go to `/workspace/music/`
like everything else; they're throwaway names, not track names.)

**Stage 2 — the track**, built with whichever treatment won, and with
the contract knob generalized: `VOICE_MODE = "sung" | "spoken" |
"instrumental"` + `VOICE_GAIN`, clearly documented at the top of the
script. In "instrumental" mode the warm lead carries the refrain — the
track must survive its singer.

## The lyric (question 5)

Era-correct means minimal — a mantra, not verses of prose. Proposal
(German; language discussion in question 4):

- **The hook** (the refrain, identical every chorus, doctrine rule 1):
  > **"Ungesungen — bis heute Nacht."**
  ("Unsung — until tonight.") Eight syllables: *Un-ge-sun-gen* (4) as
  the antecedent, rising and hanging off-tonic; *bis heu-te Nacht* (4)
  as the consequent, falling home to A. The Q/A pair IS the lyric's
  grammar — dash as the question mark.
- **Verse lines** (only if the sung-verses option in question 5 is
  chosen; otherwise verses are instrumental questions and the voice is
  chorus-only): two short lines per verse, same tune different words,
  e.g. *"So lange still / so lang nur ein Traum"* (v1), *"Die Stimme
  wach / das Warten vorbei"* (v2). Draft — edit freely in the answer.

## How the song doctrine maps on

1. **Refrain identity**: the sung hook, identical melody every chorus.
   Melody sketch: antecedent A3–C4–D4–E4 rising over Am–F hanging on
   the E over G (off-tonic); consequent E4–D4–C4–A3 over C–G–(Am)
   resolving home. Final note always A.
2. **Q/A at three levels**: inside the melody (above); between
   performers — **the voice calls, the warm lead answers the tail**
   (a written echo entering ON the held final note, the sihaya stitch);
   between sections — sparse dark verses ask, full choruses answer, the
   bridge asks the oldest question (the thesis line, alone again) and
   the final chorus answers it.
3. **Thesis early / bookend** (rule 6, fully honored — the inversion of
   ungeschrieben's withheld thesis): the track OPENS with the naked
   voice — the hook a cappella (one voice, near-dry, one pad swell
   under its tail) in the first ten seconds. The outro closes with the
   same solo statement. The whole point of the track in its first
   breath: this is the one that sings.
4. **The fusion payoff**: the final chorus sounds the counter-theme
   (the lead's answer-echo material, grown across choruses 1–2 from
   tail-echoes into a full countermelody) UNDER the sung refrain —
   voice and instrument together at last. Before chorus 3 they only
   ever trade; they never overlap.
5. **Seams**: every boundary crossed — vocal pickups (a syllable
   landing across the barline is this track's own seam device), ringing
   chords, fills, filter sweeps. The one composed silence: the
   drop-beat before the final chorus with a lone vocal pickup hanging
   in it (the sihaya pop-silence, now with an actual voice).
6. **One progression family**: Am–F–C–G everywhere; sections differ by
   density, register, and who carries the tune.

## New instruments / recipes this track adds

1. **The sung voice** (the headline recipe — exact treatment decided by
   the probe): per melody note, one TTS syllable → f0-estimated →
   resampled to the target pitch → OLA-stretched to the note's grid
   duration → our own vibrato LFO (blooming over ~0.5 s) → the
   ungeschrieben sampler chain lightly (6 kHz lowpass, gentle tanh) →
   fairly dry (wet ≤ 0.25, the sihaya "close duet not a hall" lesson),
   center, with a quiet detuned double (±0.3 %) for width in choruses
   only. Cache: every rendered syllable to
   `/workspace/music/samples/ungesungen/` — cache-first, no network
   after the first run, graceful degradation to `VOICE_MODE
   = "instrumental"`.
2. **The answer lead** — the warm detuned lead (full warmth recipe:
   `1/k**1.3`, sine core, raised-cosine attack, low cutoff, tanh 0.8)
   with the nachtkind dotted-8th ping-pong delay; it is the voice's
   duet partner and the fusion's counter-theme carrier.
3. **Reused as-is**: 909 kit (lost_v6 recipes), rolling 16th mono bass
   on A (warmed recipe, single-note discipline with octave jumps), dark
   breakdown pad, crash; gated chord stabs (nachtkind recipe, re-voiced
   to Am) as the every-16-bars development engine inside verses.
   Identity separation: no reverse cymbals (nachtkind's), no resonant
   sequence or rompler strings (ungeschrieben's), no piano centerpiece
   (nachtkind's), no 13/16 (tech_noir's).

## Structure (~180 bars + tail, bar = 1.818 s)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | THESIS (8) | The hook a cappella — one voice, near-dry, one dark pad swelling under its tail. The last syllable rings into — |
| 8 | 0:15 | intro groove (16) | Kick, then hats, then the rolling bass on A. Additive 16-bar engine starts. |
| 24 | 0:44 | verse 1 (16) | Sparse and dark: bass + stabs carry melodic questions (or sung verse lines, per question 5). Lead answers fragments — the duet only trades, never overlaps. |
| 40 | 1:13 | pre-chorus (8) | Layering rise, filter sweep, drum fill, vocal pickup across the barline → |
| 48 | 1:27 | **CHORUS 1** (16) | The drop: full groove, the hook SUNG 2× (Q/A), lead echoing each tail. |
| 64 | 1:56 | verse 2 (16) | Groove holds (unbroken — no teardown), new stab layer per the 16-bar engine; second verse questions. |
| 80 | 2:25 | pre-chorus 2 (8) | As before but hotter; roll + sweep → |
| 88 | 2:40 | **CHORUS 2** (16) | Hook 2×; the lead's echoes grow into half-countermelody (still never overlapping the sung phrases). |
| 104 | 3:09 | bridge (24) | The teardown: strip one layer per bar, avoid the tonic. The voice speaks the oldest question — the thesis line returns ALONE over the dark pad (bar ~114). Rebuild; the composed silent beat at the end, one vocal pickup hanging in it → |
| 128 | 3:53 | **CHORUS 3 — the fusion** (24) | Loudest section: hook 3×, and for the first time the lead's full countermelody sounds UNDER the sung refrain. Question and answer together. Detuned vocal double, octave lead shimmer. |
| 152 | 4:36 | ride-out (16) | Peel in reverse: countermelody out, stabs out, claps out; bass filters down. |
| 168 | 5:05 | BOOKEND (12) | Kick stops; the hook a cappella once more over the pad's last swell — same solo statement as bar 0. Ring out. |

## Verification (per ../VERIFY.md — song-form set + vocal additions)

- Section map; seam checklist (vocal pickup / ringing chord / fill /
  sweep / the composed silent beat).
- **Hook count**: sung full statements — thesis 1, chorus 1: 2,
  chorus 2: 2, bridge line (spoken/alone — counts? see note), chorus 3:
  3, bookend 1 → target **>= 9** full sung statements (the bridge's
  spoken thesis return is a deliberate fragment, uncounted).
- **The vocal pitch check** (new, this form's own): for every sung
  note, the script re-measures the f0 of the *rendered* syllable and
  prints target vs measured in cents; check: median |error| <= 35
  cents, max <= 60. The singing is verifiable without listening —
  same spirit as ungeschrieben's printed filter arc.
- **Duet separation check** (new): printed overlap ratio of voice and
  countermelody activity per chorus — choruses 1–2 near zero (they
  trade), chorus 3 substantially overlapped (the fusion is earned).
- Per-section RMS, standard song-form ordering: thesis < verse 1 <
  chorus 1; each chorus > its pre-chorus; chorus 3 loudest; bridge is
  the trough; bookend lands near thesis level.
- Banned-list audit: no supersaw, no sidechain pump, no reverse cymbal,
  no borrowed track signatures (piano centerpiece, resonant sequence,
  rompler strings).
- `VOICE_MODE`/`VOICE_GAIN` printed; in "instrumental" mode the hook
  count target still holds (lead-carried statements count instead).

## Open questions for review

1. **The doctrine amendment**: confirm sanctioning the voice — i.e.
   amending `idea.md`'s "these tracks stay instrumental" to a dated
   rule with `ungesungen` as the sanctioned exception (wording per the
   section above). This is the load-bearing question; everything else
   follows from it.
   Answer: Yes, of course, we are heading in a different direction with this track, so the "only instrumental" rule is no longer absolute.

2. **The staged plan**: confirm the probe-first approach —
   `ungesungen_probe.py` rendering ONE hook line three ways
   (TTS+OLA sung / hybrid / vowel-engine control) over a bare pad,
   decision by listening, THEN the full track. Alternative: skip the
   probe and build the track directly with the hybrid as default
   (faster, riskier). I recommend the probe — it is cheap and the
   whole track leans on this one unproven recipe.
   Answer: Yes, let's probe

3. **Title / language of the story**: *Ungesungen* ("unsung" — the
   companion to *Ungeschrieben*, my recommendation), vs *Stimme*
   ("voice"), vs English *Unsung*. Filename follows the answer.
   Answer: Let's try English this time.

4. **The voice itself**: (a) female German neural voice — continuity
   with ungeschrieben's Katja, though a different voice ID keeps the
   tracks' identities separate (e.g. `de-DE-SeraphinaMultilingualNeural`
   or `de-DE-AmalaNeural`); (b) male; (c) a female/male duet (call and
   answer voices — doubles the risk, but the doctrine's Q/A structure
   would love it). German hides TTS artifacts from non-native ears and
   fits the Frankfurt story; English would be era-authentic for vocal
   trance but exposes every artifact (the C7 warning). I recommend
   (a), German female, and the probe can render two candidate voice
   IDs for the same price.
   Answer: Let's try English, female voice. And yes, ara-authentic Frankfurt. Let's focus on only one.

5. **How much singing**: (a) hook-only vocal — verses stay
   instrumental, the voice appears only in thesis/choruses/bookend
   (safest, very era-plausible); (b) full vocal song — sung verse
   lines too (the draft couplets above, or your edits). I recommend
   deciding AFTER the probe: if the sung voice is strong, (b); if it
   is fragile, (a) keeps its exposure short and precious.
   Answer: Yes, a, hook only.

6. **The lyric**: approve or edit the hook line ("Ungesungen — bis
   heute Nacht") and, if (5b), the verse couplets. Constraint to keep:
   the hook must split into a 4-syllable question + 4-syllable answer.
   Answer: I don't think we clearify the lyrics - but I don't have any ideas right now. However, it is important that the words make some kind of sense. It cannot just be more vowels.

7. **Key / tempo sanity check**: A natural minor at 132 BPM,
   Am–F–C–G. Confirm, or push toward E minor (darker, sits lower on a
   male voice if question 4 goes that way).
   Answer: Let's keep it lighter, trance-like.

8. **Inspiration doc**: should I first write
   `inspiration/JamAndSpoon-Right_in_the_Night.md` (a blueprint doc in
   the Zyon-No_Fate style — form, palette, negative constraints) and
   have you review it before the track, as was done for ungeschrieben?
   Recommended if we want the era nailed; skippable if the doctrine +
   this doc feel sufficient.
   Answer: No, we don't need further docs right now. Let's write the generator script.



## Status — DONE

- **The probe** (`unsung_probe.py` → `unsung_probe.wav`): variant B, the
  hybrid (TTS consonant onset/coda grafted onto the pitch-held synth
  vowel), won — median 3 cents error, max 6. Variant A (pure TTS+OLA)
  drifts up to 1445 cents; variant C is pitch-perfect but wordless.
- **The lyric, final** (English per the answers): the hook is
  **"So long unsung — until tonight."** — 4+4 syllables, Q rising to
  hang on E4 over F, A falling home to A3; the same line SPOKEN is the
  bridge's fragment. Voice: `en-US-AriaNeural`, one voice only.
- **The track** (`unsung.py` → `unsung.wav`, 5:28): built as designed —
  hook-only vocal, thesis/bookend a cappella, the earned duet (choruses
  1–2 trade at 0.00 overlap, chorus 3 fuses at 1.00), the composed
  silent beat with the sung pickup. The knob generalized as planned:
  `VOICE_MODE = "sung" | "spoken" | "instrumental"` + `VOICE_GAIN`;
  syllable cache at `/workspace/music/samples/unsung/`. All 11 checks
  pass (song-form set + vocal pitch median 3 cents + duet separation).