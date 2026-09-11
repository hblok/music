# TODO.md — tracks/ebm/

Everything started and not finished, newest first within each block.
Written 2026-09-11. The directory's actual bottleneck is at the top:
**five things are rendered and unheard, and most of the rest is blocked
behind them.** Nothing here is a bug; it is all work-in-progress with a
verdict missing.

Conventions: `../VERIFY.md` is the form-check standard, `LISTENING.md`
the A/B and stem workflow, `CLAUDE.md` the directory rules.

---

## 1. Waiting on a listen (blocking everything below)

| what | file | why it is waiting |
|---|---|---|
| **No Access v3** | `/workspace/music/no_access_v3.wav` | The v2 verdict was "pretty good", but the bass "becomes very monotone after a while… it really drags" and "the whole thing starts abruptly". v3 answers both: an 8-bar bass phrase instead of one repeated cell, a talking filter, accents, a verse pedal that answers, and a 2-bar way in. All 42 checks pass. **Slices**: `--solo bass --slice 16 32` for the phrase, `--slice -2 8` for the way in |
| **Reliquary v3.3** | `/workspace/music/reliquary_v3.3.wav` | The chest was raised twice after "too thin". `dark_lead.py` still says the v3.3 verdict is pending, and that voice is now the refrain carrier for three planned tracks, so this verdict is worth more than one track. An A/B of the two lead takes is already rendered next to it |
| **Procession probes** | `/workspace/music/ebm/procession_probe/` | 18 samples rendered 2026-09-11, never heard. The ladders to listen in: `02a → 02b → 02d` (the drone argument), the three levels inside `03d`, `05a/05b`, `06a/06b`, the three weights inside `01`, the three root choices inside `02c` |
| **The ROM orchestra** | `/workspace/music/ebm/instruments/rom.wav` | New today. Nine isolated settings then two four-chord loops. The questions: does the 5-voice detune read as a section or as a wobble, and is the choir's `o` vowel the monkish one |
| **The 1999 dialect** | `/workspace/music/ebm/instruments/demo_rom.wav` | New today. Eight bars: the kit with its dirt off, the Pro One bass reading, then the registral lift. **This one decides whether the whole 1999 premise holds** — that the era move is one knob plus one voice |

Older instrument demos also still unheard: `demo_colour`, `demo_arp808`,
`demo_seethe`, `demo_riff`. `demo_groove` is a confirmed keeper and
`bark` is rejected; everything else in `instruments/README.md` is listed
as awaiting a listen.

---

## 2. Blocked on those verdicts

- **`procession.py`** — the slam track. The notes are complete, the
  questions are answered, the probes are rendered. Only the ear is
  missing. This is the closest thing to shippable in the directory.
- **`litany_probe.py`** then **`litany.py`** — the hammer. Notes are
  written; the ten questions in `litany_notes.md` are unanswered, so
  the probe script cannot be written yet.
- **A 1999 track notes doc** — the blueprint exists
  (`../../inspiration/VNV_Empires.md`) and so does the orchestra, but no
  track has been proposed. The archetype ranking in its §6 puts *the
  ascent* first, after *Saviour*, because its emotional centre is
  instrumental and so is this repo.
- **A No Access v4, or none** — depends entirely on the v3 verdict.

---

## 3. Open questions on paper, no answer yet

- **`litany_notes.md`, ten questions.** The load-bearing ones: the sub
  at F sharp 2 sits at 46 Hz against the directory's measured-good 55,
  and the snare's plate tail would stretch the truncation rule.
- **`VOCALS.md`, five questions**, open since 2026-09-06: sung or
  declaimed, which archetype gets the voice, whose words, how much
  treatment, and whether a vocoder is on the table at all. No Access
  filled its one slot with a cached machine phrase and left all five
  standing.
- **The Litany title collides.** `../dune/generate_litany_against_fear.py`
  already exists. The notes doc offers *Vigil*, *Toll*, *Threnody* and
  *Mortal Coil* as alternatives; one of them should win, or a new one.
- **Two tracks want the same tempo.** VNV's *Kingdom* is tagged at 108
  and the hammer is designed at 109. Both are slow, heavy and
  orchestral. Decide which keeps the tempo before both get built.

---

## 4. Deferred on purpose

- **The 13-bit quantise is not exposed.** `_common.dirt` always applies
  it and no instrument passes `bits` through. Its own docstring calls it
  cosmetic, so it stays hidden until a listen disagrees, at which point
  it is a one-line passthrough per instrument.
- **No detune knob on the bass.** The 1999 Pro One reading is the
  existing note with lower resonance and the dirt off. If it reads thin
  next to the real thing, that is when to add a second oscillator, not
  before.
- **Keeper voices are not promoted.** `LISTENING.md` says a voice change
  that survives a verdict moves into `instruments/` with its own
  audition. Nothing has been promoted since `dark_lead` on 2026-09-06,
  because nothing has had a verdict since.

---

## 5. Calibration, blocked on reference audio

All three blueprints were argued from genre knowledge with **no audio
measured**, and each carries an empty table plus the exact inspector
commands to fill it:

| doc | tracks to measure | what the table is missing |
|---|---|---|
| `Apop_Soli_Deo_Gloria.md` §7 | 13 | every BPM, key, bass cell, snare pattern and vocal range |
| `EBM_1990s.md` §13 | 6 | the same, plus the tenor-versus-baritone confirmation |
| `VNV_Empires.md` §7 | 10 | everything except four algorithmic BPM tags; no keys at all |

Nothing can start here: `/workspace/music/refs/` does not exist and
`yt-dlp` is not installed in this container, so the files have to be
dropped in by hand. Until then every BPM and key figure in the three
docs is a range, not a measurement, and should be read that way.
