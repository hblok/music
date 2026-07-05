# CLAUDE.md — trance/ generators

Implementation guide for the trance / synth-score generators in this
directory. The shared **stack, common architecture, and conventions** are
documented once in `../dune/CLAUDE.md` (numpy+scipy only, stdlib `wave`
output, everything synthesized, seeded RNG, `commit()` mix-bus, per-section
RMS verification, `add_at`/`glide_curve`/`reverb` helpers). Read that first;
this file only covers what is specific to the trance tracks.

**Instrument reuse: read `instruments/README.md` first** — the catalog of
every voice, drum and texture across these scripts (source
script:function, character, ownership). Pick from there instead of
re-reading the old generators; copy the function, don't import.

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

- **eisgang** — `eisgang_v3.py` (current, → `eisgang_v3.wav`) — 138 BPM
  hard techno-trance in the CIRCLE form (notes `eisgang_notes.md` +
  v2/v3 amendments; Vivaldi Winter borrows are MECHANISMS only — W3's
  stamping-feet behaviors, W5's ladder+sigh development — never
  pitches): harmony that WALKS the F-minor circle of fifths (verses the
  near half, choruses the full lap home through the one borrowed E♮),
  the skyline refrain hammered in augmentation from bar 1 and SUNG in
  choruses by the sustained skyline lead over the underglow (v3 — two
  percussive voices failed the listen test as "xylophone"; the lesson:
  refrain voices need sustain + slow attack, percussive attacks are for
  texture), run-and-plant thud-bass (duty-cycle checked ≤ 0.6 — the
  anti-rolling bass; the listen verdict's keeper), no closed-hat carpet
  (tick pair instead), the 4& stamp, freeze on the held V, retrograde
  ride-out. Declared rule-breaks live in the notes doc. (`eisgang.py`,
  `eisgang_v2.py` kept for reference.)

- **maschinenherz** — `maschinenherz.py` → `maschinenherz.wav` — the
  first PSY trance track in this directory: 145 BPM, E minor, seed 1997
  (the year German psy broke) — concept "a machine heart learns to sing"
  (design notes: `maschinenherz_notes.md`): the dune psy engine (trance
  kick, K-b-b-b rolling bass, warmed 303, offbeat hats, psy clap, zaps)
  bone dry on the E pedal; the tech_noir `love_phrase` voice ported as a
  declared instrument (new melodies, never the Terminator tune), drenched
  in the long hall; harmony static in verses/drops (E pedal, authentic
  psy) and walking Em–C–D–B in choruses (the D# of the B chord is the
  color — the refrain hangs on D#, resolves D#→E across the barline, the
  nachtkind mechanism transposed); Vivaldi W1/W2/W4a/W8a mechanisms used
  (only the ones eisgang did NOT claim — W3/W5 stay eisgang's); 64-bar
  EVOLVING drops with 4-bar mini-dips (the dune long-drop lesson); drop 1
  machine-only, the voice revealed in chorus 1 (the two-reveal instinct),
  fusion in drop 2; bookend: the voice alone states the final E ("the
  heart wins").

- **silver_wire** — `silver_wire_v2.py` (current, → `silver_wire_v2.wav`)
  — 142 BPM, A minor, seed 303: the 303 IS the singer — one acid line
  only, answering itself from an octave below (register-jump answers; the
  low register speaks the same acid grammar). Concept: where maschinenherz
  was a heart learning to sing over a machine, this track is the machine
  singing, solo (design notes: `silver_wire_notes.md` +
  `silver_wire_v2_notes.md`). Harmony Am–F–G–E; the E chord's G# is the
  borrowed color; the refrain sings the G#→A close itself. THE ANTI-ARC
  RULE (hard constraint from maschinenherz feedback): no track-long cutoff
  ramp; the cutoff breathes in a fixed 16-entry CUT_PROFILE that is part
  of the tune, identical every statement. THE ACID MELODY GRAMMAR (v2):
  the 16-bar refrain constructed in code from per-bar winding-cell step
  lists (Q_STEPS/A_STEPS) through build_half(), which applies an
  every-3rd-16th accent roll phase-locked per half, snaps accented
  chromatics to A-minor scale tones, and resolves slide chains — onset
  density 0.90, 5 rests in 256 steps, one 112-step unbroken run; two
  kept v1 landmarks: screaming hang on E (bar 8) and G#→A slide close
  (bar 16, landing across the barline). Kit split: psy gait outside drops,
  straighter/harder floor inside (open-hat offbeats only, bass sub-duty
  only). No break section; build 2 is the composed trough; bookend = last
  4 A bars + stated A at the thesis filter position. (`silver_wire.py` →
  `silver_wire.wav` kept for reference — its 8-bar melody read as
  pop/funk, the recorded lesson.)

Seeds are thematic: `1984` (tech_noir, the year the machine arrived), `1993`
(nachtkind, the year *Brainchild* came out), `130` (lost, the BPM), `1992`
(ungeschrieben, the year of *No Fate*), `1994` (unsung, the year the
Frankfurt vocal broke), `1725` (eisgang, the year Op. 8 was published),
`1997` (maschinenherz, the year German psy broke — X-Dream's era), `303`
(silver_wire, the machine's own number).

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
- **Warmed 303 family** (maschinenherz base; silver_wire lead one notch
  sharper): the sleeper_awakens within-note bright→dark sweep is KEPT in
  both — that sweep is what makes acid read as acid; never remove it. Base
  voice (`maschinenherz.py:acid_note`): rolled partials `1/k**1.3`, Q 4.5
  `iirpeak`, feedback 1.15 (1.2 on accents), `tanh(1.2)`, 0.30 sine body
  core, sweep `exp(−t/0.055)` or `0.10` for accents. Silver wire lead
  (`silver_wire_v2.py:acid_note`): same recipe pushed one notch: Q 6,
  feedback 1.3/1.35, `tanh(1.5)`. Guardrail in both: the cutoff never
  parks (it rides the per-phrase CUT_PROFILE / the printable arc) — a
  parked resonance screams; the sweep saves it. Neither is the dune recipe
  (Q 11, feedback 1.9, tanh 2.8 — the dentist); never copy those numbers
  into this directory.
- **Psy kit + kit split** (maschinenherz / silver_wire, from dune
  water_of_life / sleeper_awakens lifts): trance kick (150→45 Hz dive),
  psy clap (beats 2 & 4), psy zap (8-bar phrase punctuation), offbeat
  open hats + closed 16th ghost carpet. **Kit split in silver_wire**: psy
  gait OUTSIDE the drops (rolling bass + closed 16th ghosts); straighter,
  harder floor INSIDE the drops — open-hat offbeats only, no ghost
  carpet, bass thins to sine sub duty (`sub_note`). The acid-techno lean
  lives in the drops and nowhere else.
- **K-b-b-b bass contract** (`psy_bass_note` — maschinenherz /
  silver_wire): the rolling psy bass pattern is kick-on-the-beat, bass on
  the THREE 16ths after (gains .8 / .7 / .95), saw stack lowpassed at
  350 Hz, short gate. The 350 Hz lid keeps it from reading harsh despite
  the continuous 16ths — the psy sanctioned exception to "no rolling
  bass". THE CONTRACT (printed as a duty check, per the K-b-b-b gap
  verify): **the bass is silent on every kick 16th (position 0 of each
  beat)**; the gap IS the rest; a bass onset on a kick 16th is a bug.
  Roll mode (full outside drops): `psy_bass_note`, gains .8/.7/.95. Sub
  mode (inside drops, silver_wire): `sub_note` — pure sine + 0.3×2nd
  harmonic, no saw, no lowpass; the 303's low register owns the mid-bass
  there.
- **Acid melody grammar** (silver_wire_v2 — the validated recipe): the
  16-bar refrain is CONSTRUCTED in code from per-bar winding-cell step
  lists (Q_STEPS / A_STEPS, 7 run bars each) through `build_half()`,
  which applies an every-3rd-16th accent roll phase-locked per half, snaps
  accented chromatics to scale tones (free chromatics on weak 16ths only),
  and resolves slide chains to the next sounding pitch. Bars 8 and 16 are
  the two kept landmarks (inserted literally after each half). Checked
  metrics: onset density 0.90, ≤ 24 rests in 256 steps, longest unbroken
  run ≥ 32 (actual: 112), ≥ 4 consecutive bars of 3-cycle accent roll,
  ≥ 4 mid-run slide chains (2+ consecutive slid notes), tied/slid fraction
  ≥ 0.25. THE ANTI-ARC RULE (hard constraint — the maschinenherz-feedback
  lesson): no track-long cutoff ramp; development comes from composition
  (register, arrangement, harmony), not from gradually opening the filter.
  The cutoff breathes in a fixed `CUT_PROFILE` (16 entries, one per bar of
  the refrain) identical every statement; the per-statement cutoff spread
  must be ~0 Hz and the linear trend slope ~zero (both printed and
  checked). The eisgang lesson in acid dialect: **slides are the 303's
  sustain** — a running lead earns its legato through tie chains, not slow
  attacks. Low-register answers speak the same grammar: full-bar mini-runs
  under the two landmarks (E-rooted under the hang, A-rooted under the
  close; both registers land A together across the barline).
- **Vivaldi mechanism assignments** (maschinenherz owns W1/W2/W4a/W8a;
  eisgang keeps W3/W5 — never use either set in another track without a
  declared borrow): W1 shiver stack = additive layers that increase
  DISSONANCE, not density (maschinenherz intro: bare octave → 2nd-clash →
  tritone → alien color, first consonant chord lands with the kick). W4a
  stutter ladder = the 303 locks one pitch per bar in 16th/32nd retrigger,
  climbing chromatically OUT of the key into the drop (build 1 parks on
  the dominant, build 2 ends hammering the leading tone so the drop
  downbeat resolves it — `maschinenherz.py:ladder_bars`). W2 zigzag
  cascade = the chorus arp cell formula root–oct–oct–5th /
  5th–♭3–♭3–root, restated up the chord (`maschinenherz.py:arp_bars`).
  W8a ice-crack = stab—silence—upward flick, the composed seam fill
  (maschinenherz's transition vocabulary; not tom fills, not reverse
  cymbals — those are already claimed).

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
