# TODO.md — tracks/ebm/

Everything started and not finished. Written 2026-09-11. The directory's
bottleneck is one block: **seven things are rendered and unheard, and
everything else is blocked behind them.** Nothing here is a bug; it is
all work-in-progress with a verdict missing.

Conventions: `../VERIFY.md` is the form-check standard, `LISTENING.md`
the A/B and stem workflow, `CLAUDE.md` the directory rules.

---

## 1. Waiting on a listen — in this order

The order is not arbitrary. Items 1 and 2 validate a voice and a design
lesson that three unbuilt tracks already depend on, and items 4 and 5
gate the entire 1999 dialect, including the probes at item 7.

| # | what | file | why it is waiting, and what it unblocks |
|---|---|---|---|
| 1 | **Reliquary v3.3** | `/workspace/music/reliquary_v3.3.wav` | The chest was raised twice after "too thin", and `dark_lead.py` still says the verdict is pending. That voice is the refrain carrier for **three** planned tracks, so this verdict is worth more than one track. An A/B of the two lead takes is rendered beside it |
| 2 | **No Access v3** | `/workspace/music/no_access_v3.wav` | The v2 verdict was "pretty good", but the bass "becomes very monotone after a while… it really drags" and "the whole thing starts abruptly". v3 answers both: an 8-bar bass phrase instead of one repeated cell, a talking filter, accents, a verse pedal that answers, a 2-bar way in. All 42 checks pass. **`litany`'s whole design copies this fix**, so it is being judged twice over. Slices: `--solo bass --slice 16 32`, then `--slice -2 8` |
| 3 | **Procession probes** | `/workspace/music/ebm/procession_probe/` | 18 samples, never heard. The nearest thing in the directory to a shippable track. Ladders: `02a → 02b → 02d` (the drone argument), the three levels inside `03d`, `05a/05b`, `06a/06b`, the three weights inside `01`, the three roots inside `02c` |
| 4 | **The ROM orchestra** | `/workspace/music/ebm/instruments/rom.wav` | The one new voice of the 1999 dialect. Nine isolated settings, then two four-chord loops. The questions: does the 5-voice detune read as a section or as a wobble, and is the choir's `o` vowel the monkish one |
| 5 | **The 1999 dialect** | `/workspace/music/ebm/instruments/demo_rom.wav` | Eight bars: the kit with its dirt off, the Pro One bass reading, then the registral lift. **This decides whether the whole 1999 premise holds** — that the era move is one knob plus one voice. Measured, the era A/B shifts the spectral centroid only about 8 %, so this one can invalidate a blueprint rather than refine it |
| 6 | **Litany probes** | `/workspace/music/ebm/litany_probe/` | 13 samples, all checks passing, downstream of nothing unheard except `dark_lead` at item 1. Ladders: `01a → 01b → 01c` (the drone argument, and whether "root only" is worth keeping at all), the three levels inside `02`, `03`, `05` and `08`, the three roots inside `04`, the three kick readings inside `09` |
| 7 | **Watchfire probes** | `/workspace/music/ebm/watchfire_probe/` | 11 samples, all checks passing, but written out of order: every one uses the ROM orchestra from items 4 and 5. Ladders: `01a → 01b → 01c` (the anti-trap argument), `02` (the ascent as an opening), `05` (the chant against the arp), `06` (the era again, in context) |

Older instrument demos also unheard: `demo_colour`, `demo_arp808`,
`demo_seethe`, `demo_riff`. `demo_groove` is a confirmed keeper and
`bark` is rejected; everything else in `instruments/README.md` is listed
as awaiting a listen.

---

## 2. Blocked on those verdicts

- **`procession.py`** — the slam. Notes complete, questions answered,
  probes rendered. Only the ear is missing.
- **`litany.py`** — the hammer. Same position as `procession` now: notes
  and probes both written and rendered. Its ten questions can be
  answered from the probes rather than on paper.
- **`watchfire.py`** — the ascent. Notes and probes written and
  rendered, but doubly blocked, since the probes themselves are
  downstream of items 4 and 5. A bad verdict there rebuilds the probe
  script rather than retuning it.
- **A No Access v4, or none** — depends entirely on the v3 verdict.
- **A check that cannot fail is worse than no check.** Two audits this
  session found six such checks. Three asserted a literal `True` while
  their names claimed to verify gate duty, the bookend match and an
  editorial fact. One read chord inversions as roots. One was weaker
  than its name. One was flaky, passing in a full run and failing alone,
  because these scripts share one seeded RNG and every noise-dependent
  measurement therefore depends on how many probes ran before it. **That
  last one is unfixed**: a subset render is not bit-identical to the
  same probe inside a full render. It does not affect the checks any
  more, but it does mean `--only` output is not the shipped file.
- **Carried into all three track scripts:** a chord's root must come
  from a declared root map, never from the lowest note of its voicing.
  The watchfire probe's anti-♭VII check read inversions as F♯ G F♯ G
  and passed for the wrong reason until it was fixed. A check that
  passes by accident is worse than no check.

---

## 3. Open questions on paper, no answer yet

- **`litany_notes.md`, ten questions.** Two now have measurements
  attached and need only the ear: the sub at F♯2, whose square lands at
  46 Hz, sits at a 0.65 sub-60 share and so is affordable on the
  numbers; and the kick-to-8ths move, which breaks the track's own space
  ceiling unless the hats give up their eighths. The one still purely a
  judgement call is the snare's plate tail, which would stretch the
  truncation rule.
- **`watchfire_notes.md`, eight questions.** The load-bearing ones: the
  refrain's peak at A4 and whether the octave doubling is enough to keep
  it off the Frankfurt arch (it moves energy below 400 Hz from 0.43 to
  0.54, the right direction but modest), leaving the arp out entirely,
  and whether 126 carries the momentum the archetype needs.
- **`VOCALS.md`, five questions**, open since 2026-09-06: sung or
  declaimed, which archetype gets the voice, whose words, how much
  treatment, and whether a vocoder is on the table at all. No Access
  filled its one slot with a cached machine phrase and left all five
  standing.
- **The Litany title collides.** `../dune/generate_litany_against_fear.py`
  already exists. The notes doc offers *Vigil*, *Toll*, *Threnody* and
  *Mortal Coil*; one should win, or a new one. The rename is a `git mv`
  of three files whenever it is decided.
- **One soft chord in Watchfire's low end.** In the rising-roots
  reading, G2's sub square lands at 49 Hz while B2, D3 and E3 sit at
  61.7, 73.4 and 82.4. Probe 03 renders the pedal alternative beside it.
- **Two tracks want the same tempo.** VNV's *Kingdom* is tagged at 108
  and the hammer is designed at 109, both slow, heavy and orchestral.
  Hypothetical until someone builds the *throb* archetype, but it would
  be a collision, so `VNV_Empires.md` §3 already says not to build both.

---

## 4. Deferred on purpose

- **The 13-bit quantise is not exposed.** `_common.dirt` always applies
  it and no instrument passes `bits` through. Its own docstring calls it
  cosmetic, so it stays hidden until a listen disagrees, at which point
  it is a one-line passthrough per instrument.
- **No detune knob on the bass.** The 1999 Pro One reading is the
  existing note with lower resonance and the dirt off. If it reads thin
  next to the real thing, that is when to add a second oscillator.
- **No warm-lead sibling in `rom.py`.** The ascent's refrain carrier is
  `strings` on a single note. A dedicated sustained lead voice gets
  written only if probe `01a` says the section on one note is wrong.
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
