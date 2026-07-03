# CLAUDE.md — trance/ generators

Implementation guide for the trance / synth-score generators in this
directory. The shared **stack, common architecture, and conventions** are
documented once in `../dune/CLAUDE.md` (numpy+scipy only, stdlib `wave`
output, everything synthesized, seeded RNG, `commit()` mix-bus, per-section
RMS verification, `add_at`/`glide_curve`/`reverb` helpers). Read that first;
this file only covers what is specific to the trance tracks.

## The tracks

- **tech_noir** — `tech_noir_v3.py` (current, → `tech_noir_v3.wav`) —
  early-80s Fiedel / Terminator machine score, 13/16, D minor, composed as
  question (hollow-ended fanfare) / answer (love theme, contour-level) with
  a fusion over the unmoved pedal; ends cold. (`generate_tech_noir.py` and
  `tech_noir_v2.py` kept for reference; both wrote `tech_noir.wav`.)
- **nachtkind** — `nachtkind_v3.py` (current, → `nachtkind_v3.wav`) —
  early-90s Frankfurt / Eye Q trance, 139 BPM, G minor: the gothic piano
  theme as a Q/A refrain (question hangs on the F# leading tone, answer
  resolves F#→G across the barline), solo-piano thesis/bookend, the
  piano+lead duet earned across the choruses. (`nachtkind_v2.py`,
  `nachtkind_v1.py` kept; both wrote `nachtkind.wav`.)
- **lost (trance)** — `lost_v6.py` (current) → `lost_v6.wav` — the
  emotional journey (love/confusion/loss/dread/sadness/hope) as a SONG:
  one identical refrain re-lit by entering the Bm–G–D–A loop at three
  rotation points (bright D / sad Bm / resolved D). (`lost_v4.py` →
  `lost_v5.wav`, `lost_v3.py` → `lost_v4.wav` kept for reference.)
- **ungeschrieben** — `ungeschrieben.py` → `ungeschrieben.wav` — 1992
  Frankfurt proto-trance in the TWO-REVEAL form (blueprint:
  `../../inspiration/Zyon-No_Fate.md`): 130 BPM, F natural minor, Fm–Db–Eb;
  rompler strings as the withheld refrain, the filter arc as the
  development engine, one spoken-word drop ("Die Zukunft ist
  ungeschrieben", `VOICE_GAIN` knob at the top of the script).
- **unsung** — `unsung.py` → `unsung.wav` — the first VOCAL song attempt
  (1993/94 Frankfurt vocal trance, Jam & Spoon school): 132 BPM, A natural
  minor, Am–F–C–G; the hook "So long unsung — until tonight" SUNG by the
  hybrid TTS-graft voice (probe: `unsung_probe.py`), thesis/bookend a
  cappella, the voice/lead duet earned across the choruses.
  `VOICE_MODE = "sung" | "spoken" | "instrumental"` + `VOICE_GAIN` at the
  top of the script; notes doc is `ungesungen_notes.md`. **Verdict: a
  dead end** — every check passes, but the sung voice sounds strange,
  the bridge drop is awkward, and the instrumental offers little. Kept
  for reference, not a base to build on.

Seeds are thematic: `1984` (tech_noir, the year the machine arrived), `1993`
(nachtkind, the year *Brainchild* came out), `130` (lost, the BPM), `1992`
(ungeschrieben, the year of *No Fate*), `1994` (unsung, the year the
Frankfurt vocal broke).

## Composition: the song doctrine

`idea.md` in this directory is the doctrine (refrain identity, Q/A at three
levels, seam devices at every boundary, thesis/bookend, the fusion payoff,
one progression family) and records which shape each track uses — song form,
machine score, or two-reveal — and the dated amendment that sanctions the
voice as a trance instrument (unsung). `../VERIFY.md` is the verification
standard:
every script prints a section map, hook/statement count, seam checklist,
per-section RMS, and PASS/FAIL form checks. Both are load-bearing: write
the `*_notes.md` design doc (with embedded open questions) first, implement
its Verify paragraph exactly, and on a FAIL fix the music, not the check.

## THE warmth recipe (read this before touching any synth voice)

Every harsh-sound complaint on these tracks has had the **same cause and the
same fix**. Saw-stack voices (brass, leads, the octave bass) default to a raw
`1/k` spectrum shoved through a hard `tanh` behind a bright lowpass — that
reads as buzzy, nasal, "intruding", "like getting my teeth pulled". To warm a
voice without changing its notes, turn these knobs together:

1. **Roll off the partials**: `sin(k·ph)/k` → `sin(k·ph)/k**1.3` (…1.4). The
   single biggest move — it's the difference between a round "brass/reed" and
   a buzzy "saw".
2. **Mix a pure sine *body* core** under the stack at ~0.30 — fundamental
   weight = glow in the low-mids.
3. **Soften the attack**: longer and rounded (raised-cosine `0.5-0.5·cos`,
   ~0.2 s) instead of a fast linear ramp. A fast switch-on is what reads as a
   *stab*; a bloom-in sits *with* the track.
4. **Lower the lowpass** (e.g. brass 2200→1600, lead 4000→2600) — tame the
   2–4 kHz "honk/bite" band.
5. **Back off the drive**: `tanh(1.2–1.5·x)` → `tanh(0.8·x)`.
6. **For resonant filters, drop Q and blend**: a peak at the cutoff is the
   acid bite — `iirpeak(cutoff, Q=3.5)`+0.7 → `Q=1.2`+0.3 (a round bump, not
   a nasal whistle), and add a sine sub for body.

Applied so far: tech_noir brass (`brass_phrase`, the `reed()` inner fn),
nachtkind `bass_note` + `lead_phrase`, lost_v3 `lead_phrase` (its comment
literally reads *"Fixed from v3: warm detuned saw, harmonics rolled off, low
cutoff, a sub"*), and `lost_v4.py:bass_note` (the rolling octave bass —
`iirpeak` Q 3.5→1.2 / blend 0.7→0.3, `1/k`→`1/k**1.3`, drives 1.6–1.9→0.9–1.1).
`lost_v3.py` still has the old harsh bass — keep it for A/B reference, but
`lost_v4.py` is the one to build on.

ONE sanctioned exception: `ungeschrieben.py:seq_pluck` runs `iirpeak` at
**Q 2.2 / blend 0.40** — the era-authentic 1992 resonance, agreed in its
notes doc. The guardrails that keep it round rather than acid: soft drive
(`tanh(0.8)`), a sine sub for body, and the peak rides a *sweeping* cutoff —
it never parks and screams. Don't copy the Q without the guardrails.

## Synthesis recipes (track-specific)

- **Warm Oberheim brass fanfare** (tech_noir — feedback: the old fanfare was
  "too harsh and intruding"): `brass_phrase` builds a `reed()` voice
  (`1/k**1.35`) in two reciprocally-detuned copies (±0.32 %) for chorus
  width, plus 0.35× of a pure sine body, a rounded ~0.2 s raised-cosine
  attack, a gentle pitch *scoop* (1 − 0.018·exp(−t/0.12)) into each phrase,
  4.5 Hz bloom vibrato, lowpass 1600 (octave-doubling copies at 2400), and
  only `tanh(0.8)`. Octave doubling on the return at 0.30, brass commit ~0.23.
- **Gated 80s drum slam** (tech_noir): the gate is *baked into the sample* —
  body = pitch-thump sine (52+98·exp(−26t) Hz) + bandpassed noise burst, then
  cut dead at 140 ms by `clip((0.140−t)/0.025)`. The dense reverb-tail noise
  that the gate chops is what makes it read as an 80s gated reverb. Never a
  continuous groove — punctuation across the 13/16 cycle only.
- **Anvil clang** (tech_noir): 6 inharmonic partials (ratios 1, 2.71, 4.07,
  5.43, 7.39, 9.21 on f0≈410, falling decays + ±0.09 % detune pairs for
  shimmer) + a 2.5–9 kHz bandpassed strike transient, under a **big dark
  plate** (5 s IR, ~0.6 wet). Isolated in empty space in the intro = the cold
  open; phrase punctuation later.
- **13/16 herky-jerky grid** (tech_noir): thirteen sixteenths/bar grouped
  3+3+3+2+2 at ~99.5 BPM quarter pulse. `BAR = 13·SIXT`; the bass "DUN-dun"
  doubles ride the grouping (`BASS_STEPS` on steps 0/1, 3/4, 6/7, 9, 11). The
  limp *is* the Fiedel signature — keep it; do not regularize to 4/4. Score is
  **dry forward bass + wet metal**, no risers, no filter sweeps, no sidechain;
  it **ends cold** (one last slam + anvil ring, hard stop).
- **909 dry kit / Eye-Q dry-wet contrast** (nachtkind): drums are bone dry
  and mechanical (punchy non-sub kick 48+102·exp(−50t), 16th closed hats with
  a per-16th gain cell skipping the open-hat slot, accented offbeat open hat,
  claps on 2&4, straight-8th ride in the climax only); **all melodic elements
  go through a long dark hall** (6 s IR, 0.5–0.55 wet). That contrast is the
  whole Frankfurt aesthetic — never reverb the drums.
- **M1-era gothic piano** (nachtkind, also lost_v3): slightly-artificial
  digital piano — stretched-inharmonic partials `fk = f·k·sqrt(1+B·k²)`
  (B≈3.5e-4), `1/k**1.25` gains, **two detuned strings** per note
  (×0.9994/1.0006), a 1.5–4 kHz bandpassed hammer-thunk at ~0.16, exp decays
  rising with k. Cache one render per (pitch, dur). Stately, funereal, very
  wet; it is the *centerpiece*, not accompaniment.
- **Soaring lead over the piano = the duet climax** (nachtkind): the
  signature move is the warmed `lead_phrase` (see recipe above) stacked OVER
  the piano theme through the whole main section, with a tempo-synced
  **dotted-8th ping-pong delay** (`DELAY = 0.75·BEAT`, echoes swap L/R at 0.28
  then 0.13) and an octave-shimmer copy joining on the second 16-bar wave.
- **Reverse cymbal that lands ON the bar** (nachtkind): `RCYM` = a crash
  time-flipped (`CRASH[::-1]`), placed at `bar_t(b) − 1.5` so its swell ENDS
  exactly on the big entry. Leans the ear into the downbeat.
- **Dark gated chord stab** (nachtkind — "the subtle filtered element added
  every 16 bars"): a Gm triad (55/58/62) summed as band-limited saws,
  lowpassed hard at 900 Hz, gated short (`clip((dur−t)/0.05)`), placed on the
  offbeat, panned alternately. The "something new every 16 bars" layering
  philosophy — add one element per 16-bar block, never all at once.
- **Gothic leading-tone** (nachtkind): the progression is i–VI–VII–V
  (Gm–Eb–F–D); the **F# of the D-major V chord** against the G-minor field is
  the single gothic colour — borrowed, not diatonic. In v3 it is also the
  main seam device: pre-choruses end hanging ON the F#, resolved by the
  chorus' first G across the barline; the final chord answers the bookend's
  question-half the same way.
- **Refrain rotation lights** (lost_v6): Bm–G–D–A entered at three points —
  `ROT_Q` ends on A (open), `ROT_D` ends on D (bright), `ROT_B` ends on Bm
  (sad). The refrain's final note is always D: root of D in the bright
  choruses, minor third of Bm in the dread. Re-light the tune with the
  harmony; never change its notes.
- **Rompler strings, M1/D-50 character** (ungeschrieben — the emotional
  centerpiece): three detuned rolled-off saw copies (`1/k**1.3`, dets
  ±0.45 %) + a 2–5 kHz **bow-noise layer** riding the same envelope, a fast
  ~0.12 s raised-cosine "sampled" attack, and a **~5.8 Hz ±5 % amplitude
  flutter per voice** — the sample-loop wobble that makes it read as
  *sampled*, not analog. Long hall, wet 0.55. `strings_line` (glide legato,
  carries the theme) + `strings_chord` (per-bar rearticulated chords — the
  era string-stab feel).
- **The filter arc** (ungeschrieben): the sequence's 1-bar cell never
  changes notes; ALL development is `CUT_BARS`/`CUT_HZ`, a piecewise-linear
  cutoff automation over bars. Each 16th is rendered at the cutoff of its
  own onset and cached in 40 Hz buckets (`seq_pluck(midi, cutoff)`), so the
  sweep is baked into the notes AND the arc is printable/checkable (rise,
  global max inside the peak section, return to the intro value).
- **909 toms** (ungeschrieben): falling sine (`f0*1.6→f0`) + a soft
  400–2500 Hz skin burst; hi/mid/lo at 196/147/110 Hz, panned across.
  Transition fills ONLY — the era's seam device; three in the whole track.
- **Spoken-word drop** (ungeschrieben): edge-tts neural voice rendered ONCE
  to `/workspace/music/samples/` (cache-first — no network needed after the
  first run, graceful instrumental fallback), hardware-sampler pitch-down
  (plain resample ×0.94), 6 kHz lowpass, dry center + tempo-synced
  dotted-8th echoes. Dropped ONCE (the classic single movie-sample
  placement) with a 2-bar sequence dip carved under it. `VOICE_GAIN = 0.0`
  at the top of the script = fully instrumental; that knob is the contract.
- **The hybrid sung voice** (unsung — C7 made real, then judged a DEAD
  END: it measures pitch-perfect but *sounds strange* — the pitch check
  is correctness, not musicality. Recorded so it isn't rebuilt as-is;
  don't retry TTS singing without a new naturalness idea): per melody note,
  the edge-tts syllable's **consonant onset (~0.10 s) and coda are grafted
  onto a synth vowel that holds the target pitch perfectly** — real
  intelligibility, synth control. The vowel: rolled-off harmonic source
  (`1/k**1.2`), two `iirpeak` Q 8 formants per vowel (diphthongs morph
  f1/f2 across the note), a lowpassed chest layer so the fundamental
  survives, 8 % breath, our own 5.7 Hz blooming vibrato (never the TTS
  prosody). TTS syllables are f0-measured (autocorrelation) and resampled
  to target from the nearer of two base renders (+0/+60 Hz) so the ratio
  stays < ~6 % — no chipmunk. Light sampler chain (tanh 0.9, 6 kHz LP),
  near-dry (wet 0.18), detuned ±0.3 % double in choruses only. Pure
  TTS+OLA singing (variant A) drifts up to 1445 cents — don't ship it.
  Two checks come with the recipe: printed per-note pitch (cents) and the
  duet-separation overlap ratio (see `../VERIFY.md`, vocal songs).

## Emotional-trance structure (lost_v3)

Feedback drove this track to be ONE cohesive piece, not six stitched scenes.
The cohesion is a deliberate trinity — keep all three constant when editing:

- **One chord loop**: Bm–G–D–A (vi–IV–I–V). D major and its relative B minor
  share the same seven notes, so a section can resolve **bright** (to D) or
  **melancholic** (to B) with *zero* change to the harmonic language.
- **One recurring theme**: stated in every section — bright in love/hope, sad
  in loss/dread/sadness — voiced on lead, piano, or cello.
- **One instrument set**: warm detuned lead, glassy pluck arpeggio, pads,
  piano, cello — reused throughout. **No section introduces a foreign timbre.**

And the emotional read (feedback, important): **the "dread / Munch Scream"
section is SADNESS, not horror.** It is the cathartic *minor* climax — the
theme soars big on the warm lead with cello an octave below, big
minor-coloured pads, a driving but warm beat — **no acid, no dissonant
stabs.** Leads stay warm (the recipe above), never squeaky/buzzy. Each
section is a labelled drop or break (LOVE/CONFUSION/LOSS/DREAD/SADNESS/HOPE);
use a mid-drop *dip* then return to the fullest wave to keep a long drop alive
(the dune long-drop lesson). The confusion section destabilises by flickering
D major/minor and borrowing a Bb — harmony as the emotion, not a key change.

## Conventions

Same as `../dune/CLAUDE.md`: one standalone script per track (duplicate
helpers, no shared module); **revisions get a new WAV name and a `_vN`
script** — never overwrite a WAV the user has listened to; print event
times + per-section RMS at the end so structure is verifiable without
listening; scripts are tracked in git, generated WAVs go to
`/workspace/music/` and are **never committed**; **stage but do not commit or
push without being asked.**
