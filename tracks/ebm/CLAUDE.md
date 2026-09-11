# CLAUDE.md — tracks/ebm/

1990s EBM / dark-electro / futurepop generators. Blueprints:
`../../inspiration/EBM_1990s.md` (the genre, the 1996–2000 futurepop
hinge), `../../inspiration/Apop_Soli_Deo_Gloria.md` (the 1993
dark-electro root — the palette this directory has mined so far) and
`../../inspiration/VNV_Empires.md` (the 1999 VNV record — a third,
unopened dialect; **read its §5 first**, it splits that album into what
to take and what to leave, because *Empires* is where the Frankfurt
trap below actually lives). Read whichever blueprint the track's era
targets before writing a note doc; all three are argued from genre
knowledge, not measured audio, so treat their BPM/key figures as ranges
until an inspector run confirms them (`Apop_Soli_Deo_Gloria.md` §7 and
`VNV_Empires.md` §7 have the calibration commands).

## This directory IMPORTS — the one exception in the repo

Every other track directory (`../dune`, `../trance`, `../psy`, …) is
standalone scripts with duplicated helpers, per the repo-wide rule. This
directory does the opposite on purpose (agreed 2026-09-05): a shared,
parameterised **instrument library** lives in `instruments/`, and track
scripts import from it.

```python
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
import _common
_common.seed(1993)                       # a track owns the shared rng
from sh101_bass import note, render_cell, CELLS
from eps_kick import kick
```

**Read `instruments/README.md` first** — the catalog of every
instrument (source module, character, key knobs) and the shared
conventions (the grid, the register, the sampler dirt, caching). Pick
from there; add a new instrument to the library (with its own audition)
before reaching for something track-specific.

Contract every instrument function honours: one event, mono float
array, peak 1.0, at 44100 Hz — the same thing `make_kick()` returned in
`../dune` and `../trance`. A track script places clips with its own
`add_at()`/`place()` into its own layer buffers and runs its own
`commit()`/mix/master, exactly like every other generate_*.py. The
library never touches stereo, reverb or the master chain.

## Listening: A/B and stems

**Read `LISTENING.md`** before iterating on a voice or a mix balance.
Every track script here carries `--solo`, `--mute`, `--slice`,
`--suffix`, `--stems` (see `reliquary_v2.py` for the pattern: an
`argparse` block, a `want(layer)` guard around each layer's placement
loop, an output block keyed off one `NAME` constant, checks skipped on
a partial render). `../../tools/ab.py` builds an alternating-source
comparison file from two renders. New track scripts in this directory
should carry the same three pieces — copy them, don't reinvent.

## The tracks

- **reliquary** — `reliquary.py` → `reliquary.wav` (v1) — the first
  track, an interlude in the mould of *Soli Deo Gloria*'s "Like Blood
  From The Beloved (Part 1)": 122 BPM, A minor, 48 bars, seed 1993.
  Built entirely from the library: seethe bed, Juno arp/pad/strings/
  bass, the 808 kit, one EPS hit, the Juno lead as the hook. Notes:
  `reliquary_notes.md`. **Verdict: the structure, pads and hook
  placement are good, but the melody read as Frankfurt trance, not
  dark goth EBM** — a tenor arch to C5/D5 with vibrato and chorus over
  an updown two-octave arp and the Am–F–G lift is the Frankfurt
  recipe regardless of the drums under it (the load-bearing lesson,
  see below).
- **reliquary v2/v3** — `reliquary_v2.py` → `reliquary_v2.wav` (v2),
  → `reliquary_v3.wav` / `reliquary_v3.3.wav` (later iterations via the
  `NAME` constant + `--suffix`, same script) — the dark rewrite: same
  form and pads, new melodic vocabulary (baritone A2–B♭3, chant-like
  recitation, the ♭2 and ♭6 as colour, a descending contour landing on
  the low tonic), a hollow voice with an octave-below chest (weight
  raised in v3 — "too thin" was the verdict), no chorus shimmer, a
  one-octave descending arp, the ♭VII lift replaced by the minor v.
  Notes: `reliquary_notes.md` §"v2 amendment" / "v3". Iterating in
  place via `LISTENING.md`'s flags — bump `NAME`, never overwrite a
  kept render.
- **no_access** (working title *Clearance*) — `no_access_v3.py` →
  `no_access_v3.wav` (current: the bass phrase + the two-bar way in;
  `no_access_v2.py` and `no_access.py` are kept for their verdicts): the jackhammer archetype
  (*Backdraft*): 140 BPM, C♯ minor, gallop bass, 160 bars = 4:34, seed
  18, hook target 8. The refrain declaimed on `dark_lead` (G♯2–A3, chest
  1.0 → 1.3); a second SH-101 "tick" counter-sequence as the verse voice
  (**the bark is out** — verdict: "like a burp; doesn't fit anywhere in
  our EBM set"); the ♭2 cluster in the verses, the pad and stabs an
  octave ABOVE the voice in the choruses (the probe-07 lesson: a
  baritone voice under a pad reads muted); the low organ through the
  break; the deeper bass via the SH-101 sub square + a low shelf; a
  fade. ONE spoken slot ("No access" ×3 / "Access granted" ×1) —
  instrumental in v1 (the tick phrase retriggered / plain, `VOICE_GAIN
  = 0`), wired for the user's own spoken take through
  `instruments/machine.py`'s ring mod in a v2. **v2 (2026-09-08):** the
  ticks became six PIN attempts with a falling/rising answer (a keypad,
  not a carpet); the silver_wire pump + sub-boom for "an actual beat"
  (a declared deviation from 1993); the slot filled by a cached edge-tts
  phrase through the robot chain; organ under the pre-choruses and the
  fade. Notes: `no_access_notes.md` (plan + amendments + v1/v2/v3 verdicts);
  probes: `no_access_probe.py` → `/workspace/music/ebm/no_access_probe/`.
  Listen verdict pending.

- **procession** (working title) — **planned, in review**:
  `procession_notes.md` is the design doc for the third track, the
  *Ashes to Ashes '93* **slam** archetype (122 BPM, A minor, seed 1991,
  ~3:56). It is the song `reliquary` bookends, so its refrain is
  Reliquary's hook returned on `dark_lead`, and the track opens and
  closes on Part 1's arp cell (the second time resolved to A). The
  questions are answered (2026-09-11, yes to every recommendation) and
  `procession_probe.py` → `/workspace/music/ebm/procession_probe/`
  renders the 16 probes; no track script until they are heard.

- **litany** (working title) — **planned, in review**:
  `litany_notes.md` is the design doc for the fourth track, the
  *Spiritual Reality* **hammer** archetype (109 BPM, F♯ minor, ~3:58),
  which closes the 1993 set: slam 122, jackhammer 140, hammer 109. No
  new instruments — the whole track is library calls. Its load-bearing
  decision: the archetype wants a bass that never leaves the root and
  the v3 verdict says a repeated cell drones, so **the pitch stays put
  and the phrase moves through the filter, the gate and the accent**.
  Questions unanswered; no probe script yet.

## The Frankfurt-trance trap (load-bearing — read before writing a melody)

Every synth-pop trance track in `../trance` and every Juno preset in
`instruments/juno.py` share a DNA: an arpeggiated sequence, a tenor-ish
lead with vibrato and chorus, an updown or wide-interval contour, a
♭VII-coloured major-key-adjacent lift. That DNA is correct for
`EBM_1990s.md`'s futurepop hinge (1998–2000) — it is **wrong** for the
1993 dark-electro palette in `Apop_Soli_Deo_Gloria.md`. If a hook here
starts to sound like a trance track with darker drums, check it against
these, in order of what actually moved the needle on `reliquary`:

1. **Register**: baritone (A2–B♭3), not tenor (A4–D5). This alone did
   most of the work.
2. **Contour**: descending, chant-like recitation on the tonic, small
   steps (≤ a 4th), not an arch to a high note.
3. **Voice**: no chorus (`depth=0.0` on the Juno preset), a hollow
   square or a chest layer an octave below, not the shimmering
   chorused pad/lead default.
4. **Harmony**: the minor v (or a static pedal), not the ♭VII lift —
   the lift is what makes a progression feel like an arrival, which
   reads as uplifting/trance no matter the tempo or the drums.
5. **Sequence**: a plain descending run or a static cell, not an
   updown arpeggio across two octaves.

None of this is a rule against the Juno presets themselves — `pad`,
`strings`, `arp` with their trance-flavoured defaults are exactly right
for a futurepop-era track. It is a rule about which defaults to reach
for depending on which blueprint's era a track targets.

## Conventions

Same repo-wide stack as `../dune/CLAUDE.md` (numpy+scipy, stdlib `wave`
+ `soundfile`, everything synthesized, 44100 Hz stereo 16-bit,
peak-normalised); `../VERIFY.md` is the verification standard (section
map, hook count, seam checklist, per-section RMS, PASS/FAIL — see
`reliquary.py`'s verify block for the interlude-shape variant: ends
open, the bed's tinnitus check, the sung-grammar window).

Specific to this directory:

- **The grid defaults to 122 BPM** (`instruments/_common.py`, the
  *Soli Deo Gloria* "slam" archetype). A non-122 track calls
  `_common.set_tempo(147)` **before importing any instrument module**
  (they bind BEAT/STEP/BAR and their `dur=STEP` defaults at import;
  `set_tempo` asserts if a sibling is already imported). Added
  2026-09-06 for no_access; `no_access_probe.py` shows the order.
- **Bass register is A2** (midi 45), not A1 — the SH-101 sub-octave
  square lands at 55 Hz at A2 versus 27 Hz (inaudible, headroom-eating)
  at A1. Measured, not a guess; keep new bass writing at A2 unless a
  track has a specific reason to go lower.
- **Declared exceptions** (argue any new one in the track's notes doc):
  bass resonance Q 2.5 above the repo's warmth-recipe default of 1.2
  (guardrails: the cutoff always moves via the envelope, `tanh(1.0)`,
  a sub for body); the EPS snare as a continuous GROOVE element with a
  gated plate tail (the only reverb on a drum in this repo); the
  guitar riff (`instruments/riff.py`) as a texture stab on one track
  only, never a lead; this directory importing at all.
- **Seeds are thematic**: `1993` (the album), `1991` (the *Ashes to
  Ashes* single, reserved for a future track built on that archetype),
  `18` (TATCD 018).
- English titles. The voice: see `VOCALS.md`. As of 2026-09-08 (no_access
  v2) **TTS is allowed for the SAMPLE slot only** — a short machine phrase
  through `instruments/machine.py`, cached once under
  `/workspace/music/vocals/<track>/tts/`, a user's own take taking
  priority; TTS singing stays dead (the `../trance/unsung.py` verdict).
  The bark (`instruments/bark.py`) is a library sound, not to be planned
  on ("like a burp", 2026-09-06).
- Revisions: same conventions as `../trance` — a new WAV name per
  iteration, never overwrite a render the user has listened to. In
  this directory that name comes from the `NAME` constant + `--suffix`
  (see `LISTENING.md`), not a new `_vN` script, *while iterating on one
  track's voices/balance*; a genuine new arrangement or form still gets
  a new script (`reliquary.py` → `reliquary_v2.py`) per the repo norm.
