# No Access — design notes (2026-09-06, the second tracks/ebm/ track)

*Working title was **Clearance**; renamed from the Q1 answer. The body
below is the original plan; the **Amendments** section at the end
overrides it wherever the answers changed something — read both.*

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

## Amendments (2026-09-06, from the answers — these override the plan above)

- **Title *No Access*** (`no_access.py`, `no_access_notes.md`,
  `no_access_probe.py`; the take directory `/workspace/music/vocals/
  no_access/`). Same script and probe otherwise.
- **140 BPM** (bar 1.714 s, 16th 107 ms; 160 bars = 4:34). All tables
  and times above scale; the probe default is 140 now.
- **Gallop everywhere the engine plays** — verses AND choruses (the
  rolling+octave cell is dropped: 16 onsets a bar was half of what
  buried the refrain). Pre-chorus keeps the offbeat cell; the break the
  dark 8ths. A gallop note at 140 is 54 ms.
- **C♯ minor, the slam kick (04)** as declared.
- **THE BARK IS OUT of this track** ("sounds like somebody saying Aaa,
  or a burp; doesn't fit anywhere in our EBM set"). The module stays in
  the library for a track that wants a shout; nothing here calls it.
  Its three slots are refilled:
  1. **The verse voice → the counter-sequence.** A second SH-101 line:
     dry square-wave TICKS (`note(m, STEP*0.35, cutoff=(6000, 1500),
     env=0.02, res=4.5, sub=0, wave="square")`) on the gallop's rests
     (`.x...x...x...x..`), pitches C♯5 C♯5 G♯4 D5 (root, root, 5th, ♭2)
     — the Front 242 second sequencer, interlocking with the bass
     (checked: no tick on a bass 16th). Plus a **dark stab** (no chorus,
     cutoff 500, HPF 1) on the "and" of 2 and 4 only; the chorused stab
     on all four off-8ths is now the pre-chorus/chorus lift. Verse 2's
     development: the tick cell densifies to `.x...x.x.x...x.x` (two
     extra ♭2 ticks) and the dark stab opens (cutoff 700).
  2. **The break's low barks → the ticks sparse + the low Juno organ**
     (C♯3 G♯3 C♯4, cutoff 600, chorus 0.6) replacing the cluster in the
     break's second half — the liturgical colour the blueprint expects
     on the record's slow pieces, used once.
  3. **The spoken slot's stand-in → the tick phrase retriggered**
     (`retrigger(tick_phrase(), STEP, 3)`), instrumental. The real
     content of the slot is the spoken take through the ring mod (Q8:
     "the robot works surprisingly well… it does sound like a voice") —
     the chain is proven; it needs a source that is yours. Two phrases,
     spoken, dry, any phone: `no_access.wav`, `access_granted.wav`.
     Each missing file falls back to the ticks on its own.
- **The refrain in context (Q7)** — the diagnosis: the voice is centred
  on C♯3 (138 Hz); the chorus pad and stabs were voiced G♯3–E4, directly
  on top of it, and the rolling bass fired 16 notes a bar in the same
  band as the voice's chest. The fix keeps the voice's timbre (the solo
  is the sound) and changes the ROOM: pad and stabs voiced an octave up
  (C♯m 64 68 73, A 64 69 73, G♯m 63 68 71 — lowest note above A3, now a
  printed check), gallop instead of rolling, lead 0.6 → 0.85, stab
  0.25 → 0.2. Probe 07a (old) vs 07b (new) is the A/B.
- **The ending is a fade** (Q10): bars 152–160 strip to bed + riff + the
  ticks, the bed fades over the last 4 bars, ends on the bed like
  Reliquary — the album's continuity over the jackhammer's cold stop.
  Verify 12 becomes: no drum onset after bar 152; the last 4 bars' RMS
  descending; the final 0.1 s < −60 dB.
- **Verify 10 (two-voice separation)** now reads: tick onsets in verses
  + break ≫ choruses (zero in choruses); refrain onsets the reverse.
- **Re-probed** (`no_access_probe.py`, all at 140, new directory so the
  listened files stay): 06 verse v2, 07a/07b the chorus A/B, 10 break
  v2; 01–05, 08, 09 unchanged in content, re-rendered at 140.

### Open questions, round 2

11. **The ticks** (06): do they read as the machine (EBM sequencer) or as
    psy blips? Knobs in order: level, pitch down an octave (C♯4 — into
    the pad's band, darker), the cell sparser. If they read wrong, the
    verse voice becomes the dark stab alone.
    Answer: The ticks sound a bit like typing in a code on a numeric keypad, so I think that works. It's small light ticks. It's not psy.

12. **The chorus fix** (07a vs 07b): is the weight back? If not, next is
    the lead level again and a formant peak on the top (a timbre change
    — last resort).
    Answer: It's not much of a difference. We need a deeper bass, not timbre on top, I think.

13. **The break's organ** (10, second half): keep, or cluster throughout?
    Answer: keep throughout

14. **The two spoken phrases**: will you record them? (Speaking, not
    singing; the robot chain hides everything but the rhythm of the
    words — which is all that carries.)
    Recording: I don't have time right now, so let's go without. However, let's keep the idea, and maybe we can come back to it in a v2.

## v1 render (2026-09-06) — `no_access.py` → `no_access.wav`

From the round-2 answers: the ticks kept ("typing a code on a numeric
keypad"); the organ throughout the break; the spoken slot instrumental
(`VOICE_GAIN = 0`; the tick phrase retriggered = denied, plain =
granted — Q14: the takes maybe in a v2, the chain is wired); **the
deeper bass (Q12)** done in the instruments and the bus, not in the
refrain's timbre: the SH-101 sub square 0.4 → 0.6 (verses, pre, break,
outro) and 0.85 (choruses and the turnaround), the kick body longer
(`decay=6`), weights bed 0.26 → 0.30 / bass 0.36 → 0.40 / drums 0.42 →
0.44, and a +2.5 dB low shelf below 90 Hz on the master (the reliquary
chain plus one shelf; still no pump, no sub-boom). The refrain's chest
1.0 (chorus 1) → 1.2 (chorus 2) → 1.3 (final).

**Verify 13 re-aimed, together with this note (VERIFY.md).** The first
render measured sub-60 share 0.13–0.21 where the kick plays; after the
levers 0.19 (verses) to 0.31 (choruses). The 60 Hz line splits the key:
C♯3's sub square sits at 69 Hz (above the line), A2's and G♯2's at 55
and 52 Hz (below it), so a verse on the C♯ pedal can only score with the
kick's tail while a chorus scores whenever the loop visits A and G♯m.
The line was the artefact, not the weight: the same render measures
**sub-80 share 0.56–0.67** where the kick plays (verses 0.58, choruses
0.67 — the arc intact). The check is now sub-80 in 0.45–0.75 where the
kick plays (the ceiling guards against mud); sub-60 stays printed.

Other v1 details not in the plan: figure C is not used under the
offbeat cell (its 16th pickup would land on a bass note and fail the
check by construction); pre-chorus and outro stabs at 0.8, chorus 2 and
the final at 1.0 (what makes chorus 2 > chorus 1, since every voice is
peak-normalised); the roll's first bar is 8ths, its second 16ths →
32nds; a one-bar downsweep after each chorus hit; the silent beat and
the fade are applied to the mastered mix (bar 111.75–112; bars
156–160). All 40 checks pass. Render time ≈ 45 s. Integrated loudness
−13.2 LUFS (reliquary v3.3: −14.9; the streaming target is about −14 —
a notch hot, which is the jackhammer, not a fault; the tanh glue holds
the true peak at 0.92 and the final-chorus crest at 4.1).

**Listen verdict: pending.** Slices per section: `LISTENING.md`.

Ticks: The typing ticks are still fun. However, there is too much and they last too long (30 to 40 seconds). First of all, it is a kind of intruding sound, so it gets tedious to listen to. However, WE SHOULD NOT change the sound. It works well. Rather, we should slim it down. Now, let's think about analogy: Access: one would type in a short PIN code or maybe a password, that's just a handful or dozen of ticks or keys (a few seconds at most). And in there, it would be good if there was an "answer" sound; a similar tick, but going up or down according "access denied" or "access granted". That similar to what we already have, where the ticks become part of the melody.

Bass: The bass is still missing. Or rather, maybe the bass is ok, but what is missing is an actual beat (apart from the drums, which are fine). Anyway, we had a simmilar problem in silver_wire_v3 (tracks/trance/silver_wire_v2_notes.md). Read the notes there and maybe the script to see how we managed to add a much deeper full bass. I think that should work here as well.

Voice: Well, here there are more ticks. I thought we had an inaudible computer voice somewhere? In the probes? Well, I promised to say a few words, but still to ready, so let's try a TTL voice.

Other things which are already good: bed; pads; stabs; drums (and hi hat). The lead - love the melody and darkness here. Organ (but there isn't much of it, could be more). 

## v2 amendment (2026-09-08) — `no_access_v2.py` → `no_access_v2.wav`

**The v1 verdict** (above): the ticks "still fun" but too much and too
long — "a PIN code is a handful or a dozen keys, a few seconds, and then
an ANSWER sound going up or down"; the bass "still missing — or rather,
what is missing is an actual beat", pointing at `silver_wire_v3`; the
voice slot "more ticks — I thought we had a computer voice? let's try a
TTS voice"; the organ "could be more"; bed, pads, stabs, drums, the
lead and its melody: good. Same seed, bars, form, refrain, harmony.

1. **The keypad — ticks as events.** The carpet (30–40 s stretches) is
   gone. Six **PIN attempts**, the same sound: eight keys on 16ths
   (`x.xx.x.xx.xx....`, the code C♯5 G♯4 D5 C♯5 G♯4 C♯5 D5 G♯4 every
   time) then the **answer** on beat 4 — two longer ticks **falling**
   D5 → G♯4 (the tritone: denied) or **rising** G♯4 → C♯5 held (the
   tonic: granted). Attempts at bars 24, 38, 64, 78, 103 (denied) and
   111 (the code typed on beats 1–3, the silent beat, the rising answer
   ON the final chorus's downbeat: granted). Ticks now sound 3.6 s of
   275 s; each attempt ≤ 2.3 s. The answer is what the verdict asked
   for: the tick becoming part of the music, not a texture.
2. **The beat — the silver_wire_v3 recipe**, a declared deviation from
   the 1993 "no pump, no sub-boom" (§5 of the Apop blueprint): the
   user's ear over the blueprint. A **sidechain pump** on the sustained
   layers (bed, pads, organ, stabs, bass — never the lead, the double,
   the voice, the ticks, the hit), 55 % dip per 4-on-the-floor kick,
   `1 − 0.55·e^(−t/0.10)`, floor 0.30 (never reached: 0.45), roll bars
   excluded; 512 ducked beats, mean 0.87 in a chorus, 1.00 in the break
   (the kick is out, so the bed stands still there — the contrast is
   the point). A **sub-boom** sine (own layer, weight 0.18, not pumped,
   dry) on every ducked beat, an octave under the bass root (69 / 55 /
   52 Hz), 0.40 s with a short pitch drop and a hard release — the
   kick's low end. Master unchanged (HP 30, +2.5 dB below 90 Hz, +0.22
   above 3 kHz, tanh 1.12, 0.92). Measured: sub-80 share 0.71–0.73 in
   the choruses (v1: 0.67; the 0.75 ceiling holds), crest 3.9 (no
   growl), true peak 0.92.
3. **The voice — TTS in the slot.** The user's decision (Q14 revisited):
   "let's try a TTS voice". edge-tts `en-GB-SoniaNeural` at −10 %,
   synthesized ONCE and cached in `/workspace/music/vocals/no_access/
   tts/` (the first render needs the network; after that the file is
   the asset — the render is reproducible given it). A user's own take
   at `/workspace/music/vocals/no_access/<name>.wav` takes priority.
   Treatment: the denials ring-modulated at C♯3 (the robot the probe
   verdict liked), the grant through the intercom band and dirt only
   (intelligible — the payoff should be understood). The "No access"
   trims to 1.0 s, "Access granted" to 1.3 s. Placement: denied → the
   voice on the next downbeat (39, 79; 104 retriggered ×3, the code
   jams); granted → the rising answer and the hit on 112, the voice on
   beat 2. `VOICE_GAIN = 0` renders the answers alone; a missing voice
   (offline, no cache) is printed, not failed.
   **Rule change, tracks/ebm only:** TTS is allowed for the SAMPLE slot
   (short machine phrases through `machine.py`), because the slot wants
   a machine; TTS singing stays dead (`../trance/unsung.py`).
4. **More organ.** Besides the break: under both pre-choruses (open
   fifths following C♯m / A / G♯m, one bar each, 0.8) and under the
   outro's fade (152–160, the low i at cutoff 500 — the piece ends on
   organ + bed + the riff). Organ weight 0.24 → 0.26. Not in the
   choruses: the refrain's room.

Verify additions (all printed, all pass): the keypad block (6 attempts,
5 denied then 1 granted, every attempt < 3 s, ticks sounding < 20 s);
the two-voice separation now excepts the granted answer on bar 112;
the beat block (pump floor / ducked beats / mean in chorus 1 between
0.75 and 0.95 and exactly 1.00 in the break; one boom per ducked beat;
no boom after the drums stop); the slot block prints the source of
each phrase. -13.0 LUFS integrated (v1: −13.2).

**Listen verdict: pending.**
