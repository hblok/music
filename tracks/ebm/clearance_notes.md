# Clearance — design notes (2026-09-06, the second tracks/ebm/ track)

**The fast one.** A 4:21 song in the mould of *Soli Deo Gloria*'s
*Backdraft* — the record's **jackhammer** archetype
(`../../inspiration/Apop_Soli_Deo_Gloria.md` §3, §6): 147 BPM, C♯ minor,
the SH-101 as the engine, drums carrying the 16th energy, "tempo as
aggression". Fast, but dark, heavy and brooding — NOT trance, NOT psy.
The brooding is a contrast device: **the engine runs at 147 while the
song stands still** — harmony moving every two bars, the seethe bed
under everything, a baritone refrain declaimed at 1–2 notes per second,
the ♭2 cluster in the verses. Working title *Clearance* (security
clearance — the thing the track keeps refusing; alternatives in Q1).
Seed **18** (TATCD 018).

**Workflow — probe first (new for this directory).** Nothing in this doc
is rendered as a track until it has been heard small: `clearance_probe.py`
renders ~10 short samples (4–8 bars each at 147) of the instruments,
the drum figures, the bed, the refrain and the vocal-slot treatment,
and prints the same inspection the track's verify block will print.
Each probe is tied to an open question below. The track script is
written only after the probe verdicts — so the parameters and the
checks exist before the arrangement does.

Blueprints: `Apop_Soli_Deo_Gloria.md` §3 (*Backdraft*: "expect 8ths on
the SH-101 with the drums carrying the 16th energy — double-kick
figures, machine-gun snare runs, closed hats every 16th"; §6 "the
gallop cell on the bass, snare rolls as a GROOVE device"), `EBM_1990s.md`
§5 (cells), §6 (drums), §3 (form). This is not the song *Reliquary*
bookends — that is the 122 slam (*Ashes to Ashes*, seed 1991, still to
write), which quotes Reliquary's hook. *Clearance* has its own refrain.

## Declared up front (not questions)

- **147 BPM, 4/4, 160 bars + the last hit ≈ 4:21, C♯ natural minor.**
  The first non-122 track: `_common.set_tempo(147)` now exists and is
  called BEFORE the instrument imports (it asserts if not — the modules
  bind the grid at import). `--bpm 140` on the probe renders the same
  material a notch slower for comparison (Q2).
- **Script** `tracks/ebm/clearance.py` → `/workspace/music/clearance.wav`
  + `.flac`, one `NAME` constant, the `LISTENING.md` flags (`--solo`,
  `--mute`, `--slice`, `--suffix`, `--stems`). Imports from
  `instruments/`; everything else per `reliquary_v2.py`.
- **Register.** Bass roots C♯3 (49, sub square at 69 Hz), A2 (45) and
  G♯2 (44, sub at 52 Hz) — all inside the measured-good band; no bass
  below G♯2. The refrain lives **G♯2–A3** (44–57): recitation on C♯3
  (138 Hz — lower and darker than Reliquary's A3 centre), the low hang
  on G♯2, the climax on the ♭6 (A3) falling to the 5th. Its chest layer
  goes an octave under (G♯1 = 52 Hz on the hang) — the one declared
  reason for anything below A2, and it is a voice, not the bass.
- **The 1993 palette**: SH-101 bass, EPS kick/slam/hats, the Juno pad
  and offbeat stab, one EPS orchestral hit, the seethe bed, the bark as
  the verse's harsh voice, the dark lead as the refrain. **No 808, no
  strings, no arp wall, no supersaw, no sub-boom, no pump** (§5 "what it
  is NOT"). One Juno 8th-note sequence is allowed in the final chorus
  only (a single sequence is *Arp*; a wall is 2000).
- **Instrumental by default, with ONE spoken slot** (VOCALS.md):
  `VOICE_GAIN = 0.0` and the bark fill the slot when no take exists; the
  take is the user's own SPOKEN "No access" / "Access granted" (not
  sung — ten seconds with a phone), from `/workspace/music/vocals/
  clearance/`. Treated by `instruments/machine.py` into a sampler speech
  snippet (band, crude dirt, ring mod, retrigger) — the voice is never
  naked. TTS stays ruled out (the standing rule).
- **The slot is a form device**: NO ACCESS on the last bar of each
  pre-chorus and stuttered in the break (three denials), ACCESS GRANTED
  exactly once — the downbeat of the final double chorus, right after
  the composed silent beat. The nonsense phrase becomes the payoff.
- **Harmony**: verses on a C♯ pedal under the ♭2 cluster (G♯3 C♯4 D4);
  pre-chorus C♯m ×4 | A ×2 | G♯m ×2 (the minor v as the hang — no ♭VII
  lift, the Frankfurt-trap rule); chorus **i i VI v | i i VI i**
  (C♯m C♯m A G♯m | C♯m C♯m A C♯m), one bar each, i.e. the reliquary v2
  loop's grammar at the faster grid. Close voicings sharing tones:
  C♯m (56 61 64), A (57 61 64), G♯m (56 59 63). No modulation.
- **One continuous cursor**: the seethe bed (throb 0.4) runs from bar 0
  to the hard stop; every seam is crossed by it plus one named device.
- **Ends cold**: a final kick + slam + hit on the downbeat of bar 160
  and nothing after it (no fade, no tail beyond the hit's 250 ms).
- **Master: minimal**, the reliquary chain (HP 30 Hz, +0.22 shelf at
  3 kHz, `tanh(1.12)`, out 0.92), no pump, no sub-boom. Guardrails
  printed: true peak < 1.0, crest ≥ 3.2 in the final chorus, sub-60
  share per section.
- **Bass gate duty ≤ 0.5 of the step** (the 1993 rule, stricter than
  the futurepop 0.6). At 147 that is a 51 ms note on a 16th cell —
  probe 01 decides whether the gallop survives that or the 8th stomp
  carries the engine (Q3).

## The refrain (8 bars, C♯ minor, declaimed)

The same dialect as Reliquary v2 (recitation on the tonic, the ♭2 as
the neighbour, the ♭6 falling to the 5th, descending contour, no leap
above a 4th except the phrase restart) with its own signature: the
**stutter** — three repeated tonic 8ths then a held note (the
jackhammer's articulation in the voice) — and the **echo** — a short
note, a rest, the same note held (bars 2 and 4). Q hangs on the LOW 5th
(G♯2 — the chest drop), A climbs through ♭3–4–5 to the ♭6 climax and
falls to the tonic. 8 tokens per bar, `-` hold, `.` rest:

```
Q | C#3 C#3 C#3 - E3 - D3 - | C#3 - . C#3 - - - - | E3 - E3 E3 F#3 - E3 - | G#2 - . G#2 - - - - |
A | C#3 C#3 C#3 - E3 - D3 - | C#3 - - - . E3 F#3 G#3 | A3 - G#3 - F#3 - E3 - | C#3 - - - - - . . |
```

28 onsets / 128 16ths = 0.22 (window 0.20–0.50); held (≥ a quarter)
19/28 = 0.68; longest 8th run 3 (the ♭3–4–5 climb); down-steps 10/19;
max upward leap 5 (the restart G♯2→C♯3); ♭2 (D) onsets 2; ceiling A3.
The probe prints all of it (07) and the ear judges the rest. Voice:
`instruments/dark_lead.py` (the reliquary v3.3 voice, promoted) with
chest 0.8 in chorus 1 → 1.0 from chorus 2; the final chorus's second
pass adds the same line an octave up at 0.35 (the fusion, wide).

## Structure (160 bars, 16-bar blocks)

| bars | time | section | what plays | seam into it |
|---|---|---|---|---|
| 0–16 | 0:00 | **Intro** | bed from 0; the bass riff NAKED on C♯ from bar 0 (the DAF thesis: the cell is the hook's skeleton); kick from bar 4; slam + hats + hit 1 on bar 8 | — |
| 16–32 | 0:26 | **Verse 1** | full engine on the pedal (kick figures A/B/C, slam 2&4, 16th hats, gallop or stomp per Q3); cluster pad G♯3 C♯4 D4; sparse barks (one per 2 bars, "UH"/"KAH") | the bark on the downbeat |
| 32–40 | 0:52 | **Pre-chorus 1** | bass to the OFFBEAT cell (never on the kick) following C♯m/A/G♯m; the Juno stab on the off-8ths; open hats; snare run bar 35 beat 4; bars 38–40 the roll (8th→16th→32nd) + riser; **NO ACCESS on bar 39** | the roll + riser + the drop |
| 40–56 | 1:05 | **Chorus 1** | hit on the downbeat; the refrain ×2 (chest 0.8); pad on the loop; bass rolling+octave on the roots (or gallop, Q3); stab continues | — |
| 56–72 | 1:31 | **Verse 2** | as verse 1 + the chant cell (`x..3..x.5...x...`, the harsh voice grows); the stab drops out | the last chorus bar's bass turnaround |
| 72–80 | 1:58 | **Pre-chorus 2** | as pre 1; **NO ACCESS on bar 79** | roll + riser + the drop |
| 80–96 | 2:11 | **Chorus 2** | identical refrain, chest 1.0 (the voice deepens); hit | — |
| 96–112 | 2:37 | **Break** | kick + slam OUT at 96; the bed exposed (throb up); cluster pad; the riff alone on the pedal at 8ths, dark cutoff (the sample-slot's instrumental statement); low barks; **NO ACCESS retriggered ×3 on bars 104–105**; bars 108–111 roll + riser; **the silent beat: bar 111 beat 4** (everything stops, bed included, for one beat) | the silent beat |
| 112–144 | 2:43 | **Final chorus ×2** | **ACCESS GRANTED on the downbeat of 112** with the hit; refrain ×4; second pass (128) adds the octave-up double + the Juno 8th sequence; the loudest section | — |
| 144–160 | 3:35 | **Outro** | 144–152 the chorus instrumental (pad + engine, no lead); 152–158 strip to kick + bass; 158–160 the bass alone; **bar 160: kick + slam + hit, then nothing** | the pad's release across 152 |

Energy: intro < verse 1 < chorus 1; chorus > its pre-chorus; chorus 2 ≥
chorus 1; the break is the trough; the final is the peak; the outro
settles. Hook statements: 2 + 2 + 4 = **8** (target ≥ 8).

## Kit (library calls)

- `eps_kick.kick()` — the slam kick; probe 05 tests the "harder,
  shorter" variant (`drive=2.6, cut=0.12`) for the double-kick figures.
  Figures: A `x...x...x...x...`, B `x...x...x...x.x.` (odd bars), C
  `x..xx...x...x.x.` (every 4th bar).
- `eps_snare.snare()` on 2 & 4 everywhere the kick plays; runs
  `............xxxx` on bars 4n+3 (a groove device, §3); the 2-bar roll
  into every chorus.
- `hats.hat()` closed 16ths always (accents 1.0 .5 .7 .5); open on the
  off-8ths in pre-choruses and choruses.
- `sh101_bass.note` / `CELLS`: verse **gallop** or **stomp** (Q3);
  pre-chorus **offbeat**; chorus **rolling** (or gallop); break the
  8ths with `cutoff=(900, 250)`.
- `seethe.seethe(49, END, throb=0.4, grit=0.3)` — the bed; tinnitus
  rule printed.
- `juno.pad` on the cluster / the loop, `depth=0.0` (no chorus shimmer
  — the dark rule) except the stab, which keeps the Juno chorus (the
  goth-dance element); `juno.stab` on the off-8ths; `juno.noise_sweep`
  the risers; one `juno.arp(..., rate=2, octaves=1, pattern="down")`
  8th sequence in the final chorus's second pass.
- `eps_hit.hit((49, 56, 61, 64))` — the C♯m orchestral hit on every
  chorus downbeat, bar 8, and the last downbeat.
- `bark.bark` / `chant` — the verse voice; `machine.machine` +
  `retrigger` — the spoken slot.
- `dark_lead.dark_lead` — the refrain.

## The probes (`clearance_probe.py` → `/workspace/music/ebm/clearance_probe/`)

Raw, mono, no master (the refrain probes carry their own 0.25 reverb so
the voice is judged as it will sit). Each prints its inspection; a
FAIL there is a FAIL the track would print.

| # | file | what | decides |
|---|---|---|---|
| 01 | `engine_gallop_cs3` | kick + slam + 16th hats + gallop bass, C♯3, 4 bars | Q3 (the cell at 147), Q4 (the key's weight) |
| 02 | `engine_stomp_cs3` | same, the 8th stomp | Q3 — A/B against 01 |
| 03 | `engine_gallop_a2` | as 01 at A2 | Q4 — A/B against 01 |
| 04 | `drums_jackhammer` | 8 bars: figures A/B/C, snare runs, open hats from bar 5, the roll + riser into bar 8; no bass | Q5 (the drums), truncation printed |
| 05 | `drums_jackhammer_shortkick` | 04 with the short hard kick | Q5 — A/B against 04 |
| 06 | `brood_verse` | 8 bars: engine + bed (throb) + cluster pad + sparse barks | Q6 (does it brood), the tinnitus check |
| 07 | `refrain_chorus` | 8 bars: engine (rolling bass on the roots) + pad loop + hit + the refrain | Q7 (the melody, the voice at 147); the DARK line printed |
| 08 | `refrain_solo` | the refrain alone with its reverb | Q7 — the voice itself |
| 09 | `machine_voice` | 4 bars of engine; a 1.2 s stand-in voice (the demucs stem in `/workspace/music/vocaltest/`, never in the track) through `machine()` three ways: band + dirt / + ring at the root / + retrigger | Q8 (the slot treatment) |
| 10 | `break_riff` | 8 bars: bed + cluster + the 8th riff dark + low barks, no kick | Q9 (the break) |

Listen order: 01 vs 02 vs 03 (the engine — everything else sits on it),
then 04/05, then 06 and 10 (the mood), then 07/08 (the refrain), then 09.
`tools/ab.py --bpm 147 --bars 2` on any pair.

## Verify (the track script prints)

Blocks 1, 3, 4 always (`../VERIFY.md`); the check set:

1. **Section map** + composed events: riff in (0), kick in (4), engine +
   hit 1 (8), the three NO ACCESS bars, kick out (96), the retrigger
   (104), the silent beat (111.75), ACCESS GRANTED (112), the strip
   (152), the hard stop (160).
2. **Hook count ≥ 8** (full 8-bar refrain statements; the octave double
   and the bass riff uncounted).
3. **Seam checklist**: the bed continuous from 0 to the stop except the
   silent beat (asserted from its RMS), plus the named device per
   boundary.
4. **Per-section RMS** (post-master) and the ordering: intro < verse 1
   < chorus 1; each chorus > its pre-chorus; chorus 2 ≥ chorus 1; the
   break < both neighbours; the final chorus loudest; outro < final.
5. **The stomp**: kick on every quarter and snare on 2 & 4 in every
   groove section (from the tables); the kick-out sections have none.
6. **Bass cells**: the cell per section printed; gate duty ≤ 0.5; onsets
   per bar == the cell; no bass onset on a kick 16th in the offbeat
   cell; the chorus **root ledger** (bass root == chord root per bar).
7. **The refrain sings + DARK** (from the table): density 0.20–0.50,
   held ≥ 0.5, run ≤ 4, both phrase ends held ≥ a half note; Q ends on
   a G♯, A on a C♯; floor ≥ G♯2 (44), ceiling ≤ A3 (57); down-steps
   ≥ 0.5; max upward leap ≤ 5; ≥ 2 ♭2 (D) onsets.
8. **Truncation**: every drum sample's length ≤ its declared cut + 10 ms.
9. **Bed check**: strongest peak per 2 s < 120 Hz (bed alone).
10. **Two-voice separation**: bark onsets in verses + break ≫ choruses;
    refrain onsets the reverse (printed ratio, choruses < 0.1 bark share).
11. **The slot**: `VOICE_GAIN` printed; the placement table (3 denials,
    1 grant, their bars) checked from the events whether the take
    exists or the bark fills in; the silent beat's 0.4 s measured
    < −50 dB.
12. **Ends cold**: the last onset is bar 160.0; RMS of the last 0.1 s of
    the file < −60 dB; no drum onset after the stop.
13. **Master guardrails**: true peak < 1.0; final-chorus crest ≥ 3.2;
    sub-60 share per section (expect 0.3–0.5 where the kick plays;
    > 0.6 = the sub square or the seethe sub too loud). In C♯ nothing
    but the kick lives below 60 Hz (the sub square and the seethe sub sit
    at 69 Hz — probe 10 measures 0.02 with the kick out), so the break
    and the intro's first bars are printed, not checked.

A FAIL means fix the music, not the check.

## Open questions for review

1. **Title.** *Clearance* recommended (the thing denied three times and
   granted once; one word; English). Alternatives: *Checkpoint*, *No
   Access*, *Keycard*. The phrase itself stays "No access / Access
   granted" (your pick) — "Fast forward" and "geradeaus!" are noted as
   spare barks for a later track, not this one.
   Answer: Let's use "No Access" instead.

2. **Tempo.** 147 (the *Backdraft* jackhammer) recommended. 140 is the
   fallback if the probes read frantic rather than heavy — the probe's
   `--bpm 140` renders the same set; decide from 01/02 at both.
   Answer: Let's slow it down to 140.

3. **The engine's cell at 147** — gallop (16ths, 51 ms notes) or the
   8th stomp with the drums carrying the 16ths (the blueprint's own
   guess for *Backdraft*)? Probe 01 vs 02. My guess: the stomp in the
   verses, the gallop reserved for the pre-chorus lift; but the ear
   decides, and the chorus's rolling+octave (07) is the same question
   at 16 onsets a bar.
   Answer: gallop at 140 bpm works best.

4. **Key.** C♯ minor (Backdraft's, and the album's third key after
   Reliquary's A minor) recommended; the bass then sits at C♯3. A minor
   at A2 is heavier by 4 semitones and would make three A-minor pieces
   in a row. Probe 01 vs 03.
   Answer: c#

5. **The kick under the double figures**: the default slam kick
   (200 ms) or the short hard one (120 ms)? Probe 04 vs 05.
   Answer: Probe 04, without the shortkick.

6. **Does the verse brood** (06)? If the bed + cluster read as mood
   under the engine, keep; if the engine buries them, the verse drops
   the hats to 8ths (space) rather than turning the bed up.
   Answer: No, this part we have to re-do. The worst part is the "bark" - see below. We need to get the bark out and come up with something else.

7. **The refrain** (07/08): the stutter-and-echo line on the dark lead.
   If it reads timid at 147, the fixes in order: chest 1.0 from chorus
   1, a slower vibrato onset, longer held ends — not a higher register.
   If the melody itself is wrong, say which bar; the table is the unit
   of iteration.
   Answer: refrain solo (08) works very well. However, 07 sounds more muted - it loses much of its dark heavy element; can we fix this?

8. **The slot's treatment** (09): band + dirt only (the EPS snippet), or
   the ring mod (the robot), or with the retrigger? Recommended: dirt
   + a light ring mod for the denials, the retrigger only in the break,
   the grant cleaner (dirt only) — it is the one that should land as a
   voice. And: will you speak the two phrases? Spoken, not sung; the
   chain hides the speaker. Until a take exists the bark stands in.
   Answer: hehe, the robot works surprisingly well. It's impossible to hear what it's saying, though. But that really doesn't matter. It does sound like a voice.

9. **The break** (10): the riff alone on 8ths + bed + cluster + low
   barks, kick out for 16 bars — or shorter (8 bars) if 16 stalls?
   Recommended 16 with the retrigger event at its midpoint.
   Answer: Again the problem with the bark, it must go out. We need a different plan here.

10. **The outro's hard stop** on bar 160 (old-school, recommended) — or
    a strip that fades on the bed like Reliquary? The hard stop is the
    jackhammer's ending; the bed fade is the interlude's.
    Answer: Let's do a fade out.

Extra problem: The bark. It sounds stupid: like somebody saying "Aaa" or "Ahhh" or even a burp. It's a reather annoying sound, which first of all would take away the rest of the excellent part of this track, but also doesn't seem to fit anywhere in our EBM set. (Now, we don't need to delete the instrument, but we need a different plan for this track).

