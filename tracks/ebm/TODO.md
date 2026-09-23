# TODO.md — tracks/ebm/

Everything started and not finished. Amended 2026-09-16 after the
verdict on the 2026-09-11/12 batch — Ruin, Watchfire, the Procession
probes, heard together: **"not bad, but flat, boring, and similar."**
The diagnosis is in `ruin_notes.md` §2026-09-16 (the same drum / bass /
bed skeleton in all three, Ruin's hook = Reliquary's transposed, none of
No Access's seam devices anywhere). The rule from it: **one song at a
time** — Ruin first; the others are parked with notes (§2b), not work.

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

## 2. Tracks — two built, one waiting on a decision

| track | state | what is left |
|---|---|---|
| **Ruin** (the hammer, 109, F♯ minor) | **v3 BUILT 2026-09-18** — `ruin_v3.py` → `/workspace/music/ruin_v3.wav`. v2 was "not bad at all" but its bass read as "a 1980s commodore game"; v3 changes the bass ONLY (the dense reading + an octave-double layer, from the `sh101_bass_ruin.py` fork), all checks pass. v1 and v2 kept for the A/B | **a listen.** `BASS_READING` switches between the five probed readings in one word (probes 17a-e). Verdict decides whether Ruin is done and the next track (§2b) starts |
| **Procession** (the slam, 122, A minor) | 10 answers + probe verdicts in; snare weight unpicked | **parked** until Ruin is through. Notes in §2b |
| **Watchfire** (the ascent, 126, B minor) | **v2 BUILT 2026-09-23** — `watchfire_v2.py`: darker loop (Bm G Em F♯m) + a falling ♭2 hook, kick+boom with the offbeat bass (`--bass dense|juno|v1`), the §2b seam kit. v1 heard 2026-09-16 and again: flat, jolly lead, commodore bass | v2 heard: "really good … a goth EBM". **v2.1 BUILT** (`watchfire_v2_1.py`): juno bass, darker hats, the answer phrase, "Keep the fire" in the trough. **A listen** on `watchfire_v2.1.wav`. Notes: `watchfire_notes.md` §v2.1 |

---

## 2b. What we can do on the parked tracks (notes, not work)

Written 2026-09-16 from the diagnosis; nothing here is built. The
shared part is done already: `instruments/devices.py` holds the seam
kit (kick figures A/B/C, the snare run, the roll, riser, downsweep, the
silent beat, a dotted-8th delay mono or ping-pong). When a track's turn
comes it starts from these, probe-first.

**Both:** the seam kit at every verse→chorus and into the final (each
track has one hole and a hit today); vary the hook statements
(state / vary / answer — today every statement is identical); a
different seethe bed per track (all three run the same throb / grit /
rate); a bass cell nobody uses (`riff`, `offbeat`, `gallop` — every
track here is stomp or hammer).

**Watchfire** (the 1999 track, and the one denied the 1999 kit):
- the dotted-8th ping-pong on the strings' refrain tails and the hit —
  the VNV signature, and no track has a delay
- roll + riser + crash into each chorus (era-correct, on the
  blueprint's own list), the silent beat before the final
- verse 2 actually denser than verse 1 (they are identical today:
  stomp on the B pedal, orchestra 0.34)
- the trough with a quarter-note feedback delay on the strings, so the
  half-speed statement is a different *sound*, not just quieter
- the chant moving against the refrain (contrary motion) instead of
  static chords, if it is to be the counter-melody it was declared as
- the remark to settle: *"early 90s techno — U96, Das Boot"*, said
  twice. If that is a direction, it is a fourth blueprint.

**Procession** (still probes; the script can be written *with* the kit
instead of retrofitted):
- figure B every 4th bar is already in the probes; add the run and the
  roll into the choruses (the notes declined the roll as "no_access's
  device" — that reasoning is what produced three tracks with nothing
  in them; revisit)
- the final's "development" made real: the `TAG` as a counter-line
  under the quote, the stabs through the ping-pong, rather than a third
  identical pass
- the guitar bursts and the `stomp5`/`riff`/`walk` phrase are already
  events — keep them; they are the most alive thing in the batch
- the snare weight (0.90 / 1.15 / 1.40) is still unpicked

## 3. The five decisions

1. ~~Ruin's opening~~ — **answered 2026-09-16: the way in (10b).**
2. ~~Ruin: does the pitch move~~ — stands as built (verse 1 refuses,
   verse 2 gives in once); not re-asked, v2 keeps it.
3. ~~Ruin: the kick to 8ths~~ — stands as built (`KICK_8THS = True`,
   hats out); not re-asked, v2 keeps it.
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
- ~~**No detune knob on the bass.**~~ **Done 2026-09-18** — the trigger
  fired ("the SH-101 bass is just too timid", ruin v2) and the second
  oscillator exists as `detune` in `instruments/sh101_bass_ruin.py`, a
  FORK so the tracks with verdicts keep their sound. Watchfire's 1999
  Pro One reading can take the same knob when its turn comes.
- **No warm-lead sibling in `rom.py` — now settled, not deferred.** The
  ascent's refrain carrier is `strings` on a single note, and question 8
  came back *"No, I think we're good"*. The module stays at two entry
  points.
- **Keeper voices are not promoted.** `LISTENING.md` says a voice change
  that survives a verdict moves into `instruments/` with its own
  audition. Nothing has been promoted since `dark_lead` on 2026-09-06,
  because nothing has had a verdict since.
- **The delays in `devices.py` are unheard.** Everything else in that
  module shipped inside No Access v3; `delay` / `pingpong` are new. Their
  first use is a probe (Watchfire's, when its turn comes).

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
