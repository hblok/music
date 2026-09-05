# Reliquary (Part 1) — design notes (2026-09-05, first tracks/ebm/ track)

**The short one.** A 1:35 opener in the mould of *Soli Deo Gloria*'s
*Like Blood From The Beloved (Part 1)* — the album's atmospheric first
piece, the idea that returns as *Part 2* at the end. Not a song: an
interlude that STATES a hook once or twice and leaves it hanging. Small
on purpose: the first track built entirely from the instrument library
(`instruments/README.md`), so what we learn is about the library and
the master, not about form. Working title *Reliquary* (a container for
relics — the record's woodcut-and-liturgy frame; alternatives in Q1).
Seed **1993**.

Blueprints: `../../inspiration/Apop_Soli_Deo_Gloria.md` §4 (the
interludes, the bookend pair, the "pure sequence" *Arp*) and
`EBM_1990s.md` §12. The verdict on this piece decides the directory's
`CLAUDE.md`.

## Declared up front (not questions)

- **122 BPM, 4/4, 48 bars + tail ≈ 1:36, A natural minor.** The library
  grid is 122 and the tempo gap (`set_tempo`) stays closed until a
  non-122 track needs it.
- **Script** `tracks/ebm/reliquary.py` → `/workspace/music/reliquary.wav`
  + `.flac`. Imports from `instruments/` (the declared exception);
  everything else per `../dune/CLAUDE.md` (seeded rng via
  `_common.seed(1993)`, layer buffers + `commit()`, printed verify,
  `_vN` on revision, never commit audio). Stereo out: the library is
  mono, the script pans (arp slightly left, hit right, bed and lead
  centre, pad/strings widened by the ±0.12 % detune trick).
- **Instrumental**, no spoken drop, no bark (Q6). English title.
- **The 1992 home-studio palette only**: the Juno (arp, pad, strings,
  lead, bass), the 808, one EPS hit, the seethe bed. **No SH-101, no
  EPS kick/snare, no riff** — those are the songs' engine; the interlude
  is the Juno's piece (the *Arp (808 Edit)* lesson: a synth indulgence
  over an 808).
- **Part 1 ends OPEN** — the last chord is E (the V), unresolved; *Part
  2*, written after the song it bookends exists, resolves it to A (Q4).
- **Thesis early, at album scale**: the arp cell IS the hook's skeleton
  and plays from bar 5; the lead sings the full hook twice (bars 25–40).
  A later song quotes this hook as its refrain — that is what a Part 1
  is for.
- **One continuous cursor**: the seethe bed runs unbroken from bar 1 to
  the last sample. Every seam is crossed by it plus one named device.
- **Master: minimal**, era-appropriate (Q7): HP 30 Hz, the +0.22 high
  shelf, `tanh(1.12)` glue, output 0.92; NO sidechain pump, NO sub-boom
  layer (the 808 kick at 48 Hz is the sub). Guardrails printed: true
  peak < 1.0, crest ≥ 3.2 in the loud sections, sub-60 share.

## The hook (8 bars, A minor, sung grammar)

Two four-bar phrases, question / answer, on the Juno lead (delayed
vibrato — the singer). Note values, not runs: 2–4 notes/s, held phrase
ends, a breath rest before each phrase.

```
Q  | A4 . C5 . | B4 . . . | A4 G4 A4 . | E4 . . . |   hangs on the 5th
A  | A4 . C5 . | D5 . . . | C5 B4 A4 . | A4 = = = |   lands on the root
```

(quarters; `.` held, `=` tied). The arp cell under it is the hook's
skeleton: Am updown over two octaves, 16ths — the sequence the ear hums
first, the melody the ear recognises second (the *Arp* → song relation).
Harmony: **Am–F–G–Am** one bar each under the groove, **Am–F–G–E** under
the hook's second statement so the piece ends on E. One family, no
modulation.

## Structure (48 bars)

| bars | time | section | what plays | seam into it |
|---|---|---|---|---|
| 1–8 | 0:00–0:16 | **Bed** | seethe rises from silence (0.5 s in); pad Am from bar 1; arp enters bar 5 dark (`cutoff` 400) | — |
| 9–24 | 0:16–0:47 | **Groove** | 808 pattern (kick `decay=0.2`), Juno bass 8ths on the roots (Q5), arp opens (`cutoff` 600 → per-section table, not a ramp), pad Am–F–G–Am | reverse-less: the 808 enters ON the bar with the first orchestral hit |
| 25–32 | 0:47–1:03 | **Hook 1** | lead states the hook; arp + pad continue; 808 adds the cowbell off-8ths | the lead's pickup note (E4 on the & of 4 of bar 24) |
| 33–40 | 1:03–1:19 | **Hook 2** | hook again; strings (PWM) replace the pad; second hit on bar 33; harmony Am–F–G–**E** | the hit + a `noise_sweep` up over bars 31–32 |
| 41–48 | 1:19–1:35 | **Out** | 808 and bass stop dead at bar 41 (the composed cut — no fill); arp thins to 8ths, then stops at bar 45; the E strings chord and the seethe hold; strings release, seethe fades over the last bar; ends cold on the bed | the ringing E chord across the cut |

Energy: bed < groove < hook 1 ≤ hook 2 (the peak) > out (settling
toward the bed level). No breakdown, no build, no roll: an interlude
has no chorus to earn. Density is the whole arc.

## Kit (library calls, all defaults unless stated)

- `seethe(45, 48 * BAR + tail, throb=0.0, grit=0.25)` — the bed;
  tinnitus rule printed (strongest peak per 2 s < 120 Hz).
- `juno.arp(AM, pattern="updown", octaves=2)` — cutoff per section:
  400 / 600 / 700 / 700 / 500 (a table, printed; the anti-arc rule).
- `juno.pad` (bed, groove, hook 1) → `juno.strings` (hook 2, out).
- `juno.lead(m, dur)` — the hook; `vib` default; register per Q3.
- `juno.bass` — 8ths on chord roots, A2 register, groove + hooks only.
- `kit808.pattern` with the tight kick; cowbell line only from bar 25.
- `eps_hit()` — twice: bar 9 and bar 33. `juno.noise_sweep` once.

## Verify (script prints)

Blocks 1, 3, 4 always (`../VERIFY.md`); the check set is the
interlude's own:

1. **Section map** with the composed events: arp in (bar 5), 808 in
   (9), lead pickup (24.75), the cut (41), arp out (45), end.
2. **Hook count**: full 8-bar lead statements — target **≥ 2**; the arp
   skeleton and the pickup are uncounted.
3. **Seam checklist**: one line per boundary; the bed is continuous at
   every one (asserted from the bed's own RMS never touching zero between
   bar 1 and the last bar), plus the named device.
4. **Per-section RMS** (post-master) and the ordering checks: bed <
   groove < hook1 ≤ hook2; hook2 is the loudest; out < groove; out
   within 6 dB of the bed.
5. **Ends open**: the last pad/strings chord root == E and the last lead
   note == E4 or B4 (printed from the event lists); no drum onset after
   bar 41 (printed last drum time); the last 1 s is bed-only.
6. **The hook sings**: from the lead's note list — onset density in the
   window 0.20–0.50, held fraction ≥ 0.5, run ceiling ≤ 4, both phrase
   ends held ≥ a half note; the Q phrase ends on E, the A phrase on A.
7. **Bed check**: strongest spectral peak of the bed alone per 2 s
   window < 120 Hz, in every window.
8. **Master guardrails**: per-channel true peak < 1.0; crest ≥ 3.2 in
   hook 2; sub-60 share printed per section (expect 0.3–0.5; no bass
   instrument owns the sub here — if it exceeds 0.6 the 808 decay is
   too long for the grid).

A FAIL means fix the music (an arp cutoff, the bass gain, the 808
decay), not the check.

## Open questions for review

1. **Title.** *Reliquary (Part 1)* recommended (the frame: relics,
   woodcut, glory-to-God-alone; short; English). Alternatives: *Vigil*,
   *Threshold*, *Cold Chapel*. Whatever it is, the song it bookends and
   *Part 2* inherit it.
   Answer: Reliquary is good.
   
2. **Length.** 48 bars (1:36) recommended — the source interludes are
   1:12–1:53. Or 64 bars (2:06) with a third hook statement? The
   recommendation is the short one: an interlude that overstays is a
   song without a chorus.
   Answer: Yes, 48 bars is good.
   
3. **Lead register.** Tenor (A4–D5, Groth's register — the Apop colour)
   recommended for this frame; baritone (A3–D4, the VNV colour, argued
   in `EBM_1990s.md`) is the alternative and would make the Juno lead
   read more voice-like. The later song's refrain voice follows this
   choice.
   Answer: Yes, tenor.
   
4. **Ends open on E.** Recommended — the whole point of a Part 1. The
   alternative is a resolved ending (last chord Am) and Part 2 becomes a
   free reprise instead of the answer.
   Answer: Open ending is good.
   
5. **Juno bass 8ths under the groove**, or 808 kick only (the sparser,
   more *Arp*-like read)? Recommended: bass in — the 808 kick alone at
   122 reads thin without it, and the bass is the library's least-heard
   Juno preset.
   Answer: the juno bass is great!
   
6. **No bark in Part 1** (recommended: the interlude is the Juno's
   piece; the barks belong to the songs) — or one low "UH" under each
   orchestral hit as the record's harsh-voice signature?
   Answer: No bark.
   
7. **Master.** Minimal chain as declared (HP, shelf, tanh, no pump, no
   sub-boom) — recommended, 1993-appropriate and the interlude has no
   4-on-the-floor to pump against. Or the full big-room chain for
   consistency with the songs to come?
   Answer: Keep it minimal.
   
8. **Part 2 timing.** Write it only after the song it bookends exists
   (recommended), so it can quote what the song did to the hook; or
   write both parts now as a pair?
   Answer: No, just the part 1 one.

Extra: I notice the cowbell. I'm really not sure about that. Is it really in style? Does it fit with the dark goth ebm?


## Amendments (2026-09-05, pre-script — from the answers)

- **The cowbell is out.** It is an electro / Miami-bass signature, not a
  dark-EBM one; nothing on *Soli Deo Gloria* suggests it. The bar-25
  density step is now the 808 closed hats going from 8ths to 16ths plus
  the open hat on the & of 2 and 4. (`kit808.py` keeps the cowbell as
  a library sound; this track does not call it.)
- **The hook sketch tightened to 8th-note motion** so it passes its own
  sung-grammar window (the quarter-note sketch above measures 0.09
  onsets per 16th, below the 0.20 floor). The script's `HOOK` table is
  the reference (8 tokens per bar, `-` hold, `.` rest):

```
Q | A4 - A4 C5 - - B4 - | A4 - - - . E4 G4 A4 | B4 - A4 G4 A4 - - - | E4 - - - - - . . |
A | A4 - A4 C5 - - D5 - | D5 - - C5 . C5 B4 C5 | B4 - C5 B4 A4 - - - | A4 - - - - - . . |
```

  27 onsets / 128 steps = 0.21; held (>= a quarter) 14/27; the Q hangs
  on E4, the A lands on A4; a breath rest closes each phrase.
- **The tag.** Both statements stay identical (refrain identity), so
  the open ending is a two-bar TAG after hook 2, over the cut:
  `A4 - G4 - E4 - - - | - - - - - - . .` — the question re-asked, the
  last lead note E4 (check 5). Uncounted.
- **The open chord is E MINOR** (52, 55, 59), not E major: Apop stays
  Aeolian, and the raised-7th hang is nachtkind's device.
- **Strings hold** the Em for 6 bars from bar 41, releasing before the
  last bar; check 5's "bed-only last second" is measured as the non-bed
  layers' pre-master RMS < 25 % of the bed's in the final second (reverb
  tails are real).
- **Stereo:** pads, strings and the lead use the Juno's own stereo
  chorus (the modulation inverted between channels — `juno.chorus(...,
  phase=np.pi)` for the right side), not a detune trick.
