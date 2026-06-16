# CLAUDE.md — trance/ generators

Implementation guide for the trance / synth-score generators in this
directory. The shared **stack, common architecture, and conventions** are
documented once in `../dune/CLAUDE.md` (numpy+scipy only, stdlib `wave`
output, everything synthesized, seeded RNG, `commit()` mix-bus, per-section
RMS verification, `add_at`/`glide_curve`/`reverb` helpers). Read that first;
this file only covers what is specific to the trance tracks.

## The tracks

- **tech_noir** — `generate_tech_noir.py` (current) — early-80s Fiedel /
  Terminator machine score, 13/16, D minor. (`tech_noir_v2.py` is a parallel
  take kept for reference.)
- **nachtkind** — `nachtkind_v2.py` (current), `nachtkind_v1.py` (kept) —
  early-90s Frankfurt / Eye Q trance, 139 BPM, G minor, gothic piano + lead.
- **lost (trance)** — `lost_v3.py` (script) → renders `lost_v4.wav` — a
  one-piece emotional-trance reworking of the ambient `../ambient/lost.py`.

Seeds are thematic: `1984` (tech_noir, the year the machine arrived), `1993`
(nachtkind, the year *Brainchild* came out).

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
cutoff, a sub"*). **Known remaining offender:** `lost_v3.py:bass_note` still
has the old `iirpeak(Q=3.5)`+0.7 and `tanh(1.6)` — it is the next warming
candidate if that bass is called harsh.

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
  the single gothic colour — borrowed, not diatonic.

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
