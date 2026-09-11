# TODO.md — tracks/ebm/

Everything started and not finished. Rewritten 2026-09-11 after the
`answers` commit: **the listening backlog is cleared and three track
scripts are unblocked.** The bottleneck moved from ears to five small
decisions, one of which is a real design hole.

Conventions: `../VERIFY.md` is the form-check standard, `LISTENING.md`
the A/B and stem workflow, `CLAUDE.md` the directory rules.

---

## 1. Closed — verdicts in, nothing further

- **Reliquary v3.3** — *"v3 is an excellent opening. Nothing to change
  here for now."* `dark_lead` is confirmed by extension, which was the
  verdict three planned tracks were waiting on.
- **No Access v3** — *"v3 works quite well. It's not a full-on banger,
  but a good track on the album."* The phrase-not-cell fix and the
  2-bar way in both landed. **No v4.**
- **The ROM orchestra and the 1999 dialect** — judged through the
  watchfire probes rather than the auditions: `01a` was picked as the
  best of its ladder and question 8 came back *"No, I think we're
  good"*, so `rom.strings` needs no warm-lead sibling.

---

## 2. Tracks — one built, two waiting on decisions

| track | state | what is left |
|---|---|---|
| **Procession** (the slam, 122, A minor) | 10 answers + probe verdicts in. The refrain solo `04c` was *"really cool — love it!"*, the beat is `06b`, the bookend stays open | one knob: the slam's snare weight was never picked from 0.90 / 1.15 / 1.40 |
| **Ruin** (the hammer, 109, F♯ minor; renamed from *Litany*, which collided with a dune track) | 10 answers in; the engine ladder came back *"drone-as-phrase is good, phrase with moving pitch is also good"*. Files and script renamed to `ruin_*` | pick an opening from probe `10`, plus two smaller calls. See below |
| **Watchfire** (the ascent, 126, B minor) | **BUILT 2026-09-11** — `watchfire.py` → `/workspace/music/watchfire.wav`, 136 bars, 4:22, all checks pass | a listen. One genre remark to settle if you want to |

---

## 3. The five decisions

1. **Ruin's opening: pick one of three.** The toll was rejected and no
   replacement idea was to hand, so probe `10` renders three candidates
   instead of guessing: **(a) the naked blow**, kick and slam together
   with 1.1 s of silence between them, which no other track here does;
   **(b) the way in**, no_access v3's swell-organ-sweep device, already
   passed by ear on that track; **(c) no opening at all**, the engine
   starting cold. Measured at -10.4, -24.1 and -5.7 dBFS across their
   first two bars, so they are three different proposals rather than
   three mixes of one. No longer a blocker — a listen.
2. **Ruin: does the pitch move or not?** Both `01b` (the phrase, pitch
   fixed) and `01c` (the phrase with a walking pedal) were called good.
   That makes the track's stated load-bearing decision — the pitch never
   moves, the filter does the phrasing — optional rather than necessary.
   Worth choosing deliberately, because the archetype's whole claim
   rests on it.
3. **Ruin: the kick to 8ths in the final chorus** is *"unsure"*. The
   probe found it only fits if the hats give up their eighths, which
   drops the bar from 26 onsets to 18. Recommend taking it with hats
   out; it is the one energy move available at 109 that adds no density.
4. **Procession: the snare weight.** Probe `01` renders 0.90 / 1.15 /
   1.40 and 1.15 is the provisional default. Pick one or keep 1.15.
5. **Two seeds were never stated.** Ruin's answer replaced the seed
   line, and Watchfire's *"geradeaus"* reads as approval of the title.
   Defaults stand unless told otherwise: **2018** for Ruin, **1999** for
   Watchfire.

---

## 4. One open observation, not a question

Watchfire *"might have left the dark goth… we've entered early 90s
techno. U96 — Das Boot!"*, said twice, alongside calling probe `02`
great and `01a` the best of its ladder. Read as a remark rather than a
complaint, so nothing is being changed on it. If that reference is
worth pinning down properly it would be a fourth blueprint next to the
Apop, genre and VNV docs, and it would change what this directory is.

---

## 5. Still unheard, low priority

The older instrument demos: `demo_colour`, `demo_arp808`, `demo_seethe`,
`demo_riff`. `demo_groove` is a confirmed keeper and `bark` is rejected.
None of them block a track.

`VOCALS.md`'s five questions are also still open from 2026-09-06: sung
or declaimed, which archetype gets the voice, whose words, how much
treatment, and whether a vocoder is on the table. No Access filled its
one slot with a cached machine phrase and left all five standing; none
of the three tracks below has a vocal slot, so they stay parked.

---

## 6. Deferred on purpose

- **The 13-bit quantise is not exposed.** `_common.dirt` always applies
  it and no instrument passes `bits` through. Its own docstring calls it
  cosmetic, so it stays hidden until a listen disagrees, at which point
  it is a one-line passthrough per instrument.
- **No detune knob on the bass.** The 1999 Pro One reading is the
  existing note with lower resonance and the dirt off. If it reads thin
  next to the real thing, that is when to add a second oscillator.
- **No warm-lead sibling in `rom.py` — now settled, not deferred.** The
  ascent's refrain carrier is `strings` on a single note, and question 8
  came back *"No, I think we're good"*. The module stays at two entry
  points.
- **Keeper voices are not promoted.** `LISTENING.md` says a voice change
  that survives a verdict moves into `instruments/` with its own
  audition. Nothing has been promoted since `dark_lead` on 2026-09-06,
  because nothing has had a verdict since.

---

## 7. Calibration, blocked on reference audio

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
