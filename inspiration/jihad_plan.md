# "Jihad" — The Holy War — Track Design Plan
*(produced by Claude Opus, 2026-06-19)*

> Expands the `dune/more_ideas.md` §B3 stub into a full implementation plan.
> Target render: `/workspace/music/jihad.wav`. Generator: `dune/generate_jihad.py`.
> Self-contained legacy-style script (numpy + scipy + stdlib `wave`); do NOT
> import forge. Mirror the architecture of `generate_fall_of_arrakeen.py`.

## Concept
The holy war Paul fears and unleashes. If *Fall of Arrakeen* was one battle,
**Jihad is the war that follows the victory** — the green-and-black banners
crossing the galaxy, world after world, the thing the prescient visions
showed him and that he could not stop. Not mourning, not a single fight:
relentless, spreading, inhuman fervour. The darkest and fastest track on the
album. It does not end — it is **cut off mid-fury**, because the jihad never
actually stops; the music simply leaves us.

This is a **direct energy successor to `fall_of_arrakeen_v2`** — same home key
(D), same room-shake machinery — *weaponised*. It is the deliberate opposite
of `the_navigator` (which floated, softened its low end, and kept deflating
into dead air). Jihad never floats and never stops moving.

## Why this has the energy (and *The Navigator* didn't)
The Navigator was flat because its concept fought propulsion and its mix was
de-fanged. Jihad reverses **every** Navigator softening — these are load-bearing:

| Dial | Navigator (flat) | **JIHAD (room-shake)** |
|------|------------------|------------------------|
| Kick sub tail | 64→48 Hz | **55→37 Hz (lands on D1)** |
| Sub boom | 66→52 Hz, weight 0.22 | **50→37 Hz, weight 0.30** |
| Master low shelf | +0.18 @105 Hz only | **+0.34@95 Hz + +0.30@55 Hz (deep shelf restored)** |
| High shelf | +0.24 @3 kHz | **+0.26 @3 kHz (bite for the scream)** |
| Sidechain pump | duck 45 %, floor 0.40 | **duck 55 %, floor 0.28** |
| Bus tanh | 1.45×, 0.90 | **1.40×, 0.90** |
| Percussion bed | tabla + hats + clap only | **~12 percussion layers (see density target)** |
| Breakdowns | Stillpoint / Held Breath = **dead air** | **the pulse NEVER stops — chant-gate carries every dip** |
| Ending | stillpoint → arrival → 40 s void | **HARD CUT to silence, no fade, no aftermath** |

The three rules that actually make it relentless:
1. **The low end is unconditional and violent** — restore the full Arrakeen
   room-shake stack (kick on D1 + dedicated sub-boom layer + 55 % pump).
2. **The pulse never fully stops.** Even the breakdowns keep the Sardaukar
   **chant-gate** chugging in 16ths. There is no Stillpoint, no dead air.
3. **It escalates in three waves and then sprints**, with only short dark
   recharges between — and no denouement. Energy is front-loaded and climbs.

## Musical DNA
- **BPM: 152** — deliberately the album's fastest base tempo (Arrakeen 148,
  Navigator 145). The aug-2nd mode is genuinely unsettling at this speed.
- **Key: D Hijaz Kar — D Eb F# G A Bb C#** — the "double augmented-second"
  scale. It is D Phrygian dominant (the album's home mode) with the **7th
  raised to C#**: this adds a *second* augmented second (Bb→C#) and a hard
  **leading tone (C#→D)**. Same root as Arrakeen — so it reads as the sequel —
  but weaponised. (Contrast: Navigator was E Hijaz Kar, used for cosmic
  ecstasy; here the same scale family in D is used for menace.)
- **Root: D** (stays in the home key on purpose — this is Arrakeen's war,
  escalated; it is NOT trying to break the D-rut the way Navigator did).
- **Signature intervals:** the **C#→D leading-tone hammer** (inevitability,
  the pull to the root) and the two augmented seconds **Eb→F#** and **Bb→C#**
  (the jagged, alien fervour). The "jihad cry" is the rising **Bb→C#→D**
  (aug-2nd leap up, then leading-tone resolution) — the inverse energy of
  Arrakeen's falling Bb→A "war cry".
- **THEME_JIHAD:** martial, dotted, hammering — see below.

## What makes it *Jihad* (the two headline NEW recipes)
1. **Sardaukar chant-as-rhythm (the chant-gate).** The massed throat-chant is
   no longer a pad — it is chopped into 16th-note gates and becomes the
   track's percussive identity (the "huh-huh-huh-huh" battle-breath of a
   legion). This is the layer that carries every breakdown so the pulse never
   stops.
2. **Screamed carnyx horn.** The `horn_phrase` war-horn pushed into tanh
   saturation with *chaotic* vibrato and a high scream-formant band — a brass
   instrument that sounds like it is tearing. It carries THEME_JIHAD and the
   signal calls.

## Section Map (GRID0=10 s, BAR≈1.579 s at 152 BPM, DURATION≈355 s)
Three escalating waves + the sprint, hard cut. Recharges are dark but never silent.

| Bars    | ~Time | Section | Description |
|---------|-------|---------|-------------|
| pre     | 0:00  | **The Gathering** | Legions-roar atmosphere; distant screamed horn; chant-gate fades IN; D1 drone + Eb shadow + faint C# shimmer |
| 0–11    | 0:10  | **I. The Gathering** | Drone + chant-gate assembling + slow war drums |
| 12–23   | 0:29  | **II. The Muster** | Kick enters HARD (barely held back), bass +4, dark acid +8, the Sardaukar signal-horn |
| 24–31   | 0:48  | **III. Rise 1 (build)** | Riser + snare/frame rolls + acid ramp — short, violent |
| 32–71   | 1:00  | **IV. THE FIRST WAVE (DROP 1)** | Full assault. THEME_JIHAD on screamed horn, chant-gate 16ths, RIFF_HOLY1, war drums, toms. **War-cry dip 56–59** (chant + kick only) |
| 72–79   | 2:04  | **V. Recharge 1** | Kick drops; chant-gate keeps chugging; one screamed horn over it; detonation. NOT silent |
| 80–87   | 2:16  | **VI. Rise 2 (build)** | Rolls, riser, acid climb |
| 88–135  | 2:29  | **VII. THE SECOND WAVE (DROP 2)** | Bigger: both acids in call-response, chant-gate, full toms. **Dips 112–115 and 124–127** |
| 136–143 | 3:45  | **VIII. Recharge 2** | Darkest dip; chant + distant screams; the breath before the end |
| 144–151 | 3:57  | **IX. Rise 3 (build)** | The final build — everything ramping |
| 152–199 | 4:10  | **X. THE SLAUGHTER (DROP 3 — peak)** | Maximum density: both acids, chant-gate at 32nds, screamed-horn calls, toms+war drums. **Dips 172–175, 188–191** |
| 200–215 | 5:26  | **XI. THE SPRINT** | Kick on 8ths, chant-gate on 32nds — fastest, most violent music on the album |
| 216     | 5:51  | **XII. HARD CUT** | One final downbeat stab — then **instant silence**. No fade, no aftermath. ~4 s of true silence to EOF |

`groove_on(b)` plays bars 12–215 except the recharges (72–79, 136–143). The
chant-gate is the one layer that **also** plays through the recharges and the
war-cry dips — it never stops.

## THEME_JIHAD (MIDI, beats — D Hijaz Kar)
Martial and dotted; built on the Eb→F# aug-2nd, the Bb→C# cry, and the C#→D
leading-tone hammer. Stated by the screamed horn (and doubled by the chant on
peaks). D4=62.
```python
THEME_JIHAD = [
    (62, 1.5), (62, 0.5), (63, 1.0), (66, 1.0),     # bar 1: D D Eb -> F#  (Eb->F# aug2)
    (67, 1.0), (66, 1.0), (63, 1.0), (62, 1.0),     # bar 2: G F# Eb D     (the gathering, descent)
    (69, 1.5), (70, 0.5), (73, 1.0), (74, 1.0),     # bar 3: A Bb -> C# -> D  (Bb->C# the jihad cry)
    (73, 1.0), (74, 2.0), (62, 1.0),                # bar 4: C# -> D (hold) -> D  (leading-tone hammer)
]  # 16 beats = 4 bars
```
Sardaukar signal call (muster + peaks; octave-up the scream for the slaughter):
```python
HORN_CALL = [(50, 1.2), (51, 0.4), (54, 0.6), (50, 2.0)]  # D3 Eb3 F#3 D3 (aug-2nd signal)
```

## Acid riffs (D Hijaz Kar — NEW, do NOT reuse RIFF_WAR1/WAR2)
Reuse Arrakeen's `acid_note` / `acid_bars` verbatim. Two new riffs:
```python
# Low driver, D2 territory — Eb->F# slide + C#->D leading tone prominent
RIFF_HOLY1 = [
    (38,1,None),(None,0,None),(38,0,None),(39,1,42),     # D . D  Eb->F#
    (42,0,None),(None,0,None),(45,0,None),(None,0,None),  # F# . A .
    (49,1,50),(50,0,None),(None,0,None),(38,0,None),     # C#->D  D . D
    (46,0,None),(None,0,None),(49,1,50),(38,0,None),     # Bb . C#->D D
]
# High counter, D3-D4 — call-and-response with HOLY1; leans Eb->F# and C#->D
RIFF_HOLY2 = [
    (62,1,None),(62,0,None),(63,0,66),(66,0,None),       # D D Eb->F# F#
    (None,0,None),(69,0,None),(70,1,None),(69,0,None),    # . A Bb A
    (73,1,74),(74,0,None),(None,0,None),(66,0,None),     # C#->D D . F#
    (63,0,None),(61,0,62),(62,1,None),(None,0,None),     # Eb C#->D D .
]
```
Tuple format is `(midi, accent, slide_to)` exactly as in `fall_of_arrakeen`.

## NEW instrument recipes (DSP detail)

### 1. Sardaukar chant-gate — the headline rhythm
Two stages: build a wide many-voice chant, then gate it into 16ths.
- **Voice body (the C1 "Choir of Sietch Tabr" recipe):** take Arrakeen's
  `chant_note(midi, dur)` formant voice and render it **12×** per pitch with
  per-voice detune ±0.8 %, onset jitter ±60 ms, and formant-frequency scatter
  ±5 %; sum and spread the 12 across L/R by voice index. Hammer the **root D**
  (D2=38 / D3=50 unison for weight); use **C#** (49/61) on accented gates as
  the leading-tone bite.
- **The gate:** multiply the summed chant by a 16th-note gate envelope —
  per step a fast attack (~3 ms), short hold, fast decay (gate length ~0.6×
  STEP). Accent pattern can follow the maqsum/pump (louder on beats). In Rise
  sections and THE SLAUGHTER, switch to **32nd gates**; in THE SPRINT, 32nds
  at full gain. The chuffing massed voices ARE the percussion.
- **Crucial:** this layer ALSO plays through both recharges and the war-cry
  dips at reduced gain — it is what keeps the pulse alive (anti-Navigator).
- Lightly pump it (so it breathes with the kick) but keep its floor high.

### 2. Screamed carnyx horn
Start from Arrakeen's `horn_phrase`, then weaponise:
- **Chaotic vibrato:** vibrato *rate* itself wobbles — `f_vib = 5.0 + 3.0*slow_noise(...)`,
  `vib = 1 + 0.02*sin(2π·cumsum(f_vib)/SR)` (depth 0.02, ~3× the controlled
  horn's 0.006).
- **Scream formant:** add a hot band-pass at **1800–3500 Hz** (the tearing
  upper-formant) on top of the existing 450–900 Hz brass formant.
- **Saturation:** `out = tanh(3.0 * out)` then renormalise — the drive is the
  scream.
- **Size:** mix a sub-octave copy (×0.5) at ~0.4 gain.
Used for THEME_JIHAD statements (octave-up in THE SLAUGHTER) and HORN_CALL
signals; one distant, dry, low-pass-1000 version in The Gathering.

### 3. (optional) Anvil / steel strike — brutal metallic accent
Inharmonic metal partials (ratios `1.0, 2.756, 5.404, 8.933`) like the
Navigator stillpoint hit, but **short** (decay ~0.3 s), high-passed at 400 Hz,
struck on wave downbeats and the hard-cut stab. Industrial bite on the accents.

## Inherit from `fall_of_arrakeen_v2` (copy, retune to D Hijaz Kar)
Reuse these recipes verbatim; only retune pitches and re-weight as noted:
- `make_kick_stack` (v2: punch→44 Hz, **sub tail→37 Hz / D1**), `make_sub_boom`
  (50→37 Hz), the **sidechain `pump`** loop — set **duck 0.55, floor 0.28**.
- `psy_bass_note` + the off-beat K-b-b-b walk (see Bass below).
- `make_hat`, `make_shaker`, `make_clap`, `make_snare` (field snare — keep the
  militaristic march in the builds), `make_tom` (battle toms + fill runs),
  `make_war_drum`, `make_doum`/`make_tek`/MAQSUM (darbuka).
- `riser`, `frame_roll`/`make_frame_hit`, `rev_cymbal`, `make_zap`,
  `explosion` (as **punctuation only** — NO death blow), `tremolo_strings`
  (dark dread bed on the D–Eb minor 2nd and the C# leading tone).
- The `commit()` / peak-normalise architecture, the `energy`/`calm` envelope,
  `groove_on()`, and the **master chain** — but with the room-shake shelves
  from the table above and **NO master fade-out** (see Ending).

## Bass — D Hijaz Kar walk
Off-beat rolling bass (the album engine). Notes: D2=38, Eb2=39, F#2=42, G2=43,
A2=45, Bb2=46, C#3=49, D3=50.
- Standard off-beat triplet after each beat: `[F#2, G2, A2]` (42,43,45).
- End-of-phrase cadence (every 4th bar, beat 3): `[Bb2, C#3, D3]` (46,49,50) —
  the aug-2nd cry climbing into the root via the leading tone.
- Octave flick on the heaviest bars (THE SLAUGHTER / SPRINT): drop a D3=50.
- Pump it (`env=pump`) — the kick owns the sub alone; the pumping is the BAM.

## Ending — THE HARD CUT (the album's only unresolved ending)
- THE SPRINT peaks at bar 215. On the downbeat of **bar 216**, place one final
  anvil/kick/horn **stab**, then **everything stops on that frame.**
- **No master fade-out** (every other track fades; this one must not). After
  the stab, only the natural reverb tail of that single frame decays into
  silence. `DURATION ≈ 355` leaves ~4 s of true silence after the cut, then EOF.
- **No aftermath, no death blow, no heartbeat, no lament.** (Those belong to
  `fall_of_arrakeen` / `kanly`.) The jihad does not stop; the music just leaves.

## Layers to commit (density target ≥ 24, matching Arrakeen)
1 legions-roar atmosphere · 2 drone (D1 + Eb shadow + C# shimmer) · 3 kick
stack · 4 sub boom · 5 psy bass · 6 hats · 7 shaker · 8 clap · 9 field snare ·
10 war drums · 11 battle toms · 12 darbuka maqsum · 13 **chant-gate (NEW)** ·
14 sustained chant (dips / war cry) · 15 **screamed carnyx horn (NEW)** ·
16 acid RIFF_HOLY1 · 17 acid RIFF_HOLY2 · 18 risers · 19 frame rolls ·
20 reverse cymbals · 21 zaps · 22 detonations (punctuation) · 23 tremolo
strings · 24 **anvil/steel (NEW, optional)**. Print `N_LAYERS` and a section
map at the end like the other generators.

## Atmosphere & drone (retune for "the legions", not the desert)
- **Atmosphere:** darker than Arrakis wind — a low rumble (massed feet /
  ornithopter engines, band-pass ~40–200 Hz), a mid roar (200–900 Hz), and
  sparse distant high transients (band-passed noise bursts ~2–6 kHz suggesting
  far-off cries). Resonances tuned to D harmonics. Gated up under `calm`.
- **Drone:** D1=26 + 2nd/3rd harmonics + **Eb1 shadow (27)** for the minor-2nd
  dread + a faint **C#2 (37) leading-tone shimmer** that pulls toward D
  (the inevitability). Pump it under the kick.

## What to avoid
- The Navigator's softened "earbud" low end (66→52 Hz, no deep shelf, 45 %
  pump). **Use the full Arrakeen room-shake.**
- **Dead air.** No Stillpoint, no Held Breath — the chant-gate carries every
  dip. The pulse never fully stops.
- A long aftermath / death-blow-then-heartbeat (Arrakeen / kanly). **Hard cut.**
- Reusing Theme WAR (Bb→A) or RIFF_WAR1/WAR2 even transposed — new material on
  C#→D and the aug-2nds.
- Cosmic/floating Navigator palette: choir-formant pad pulsing to silence, gas
  bubbles, FM Goa ecstatic lead, resolving UP to a major third.
- Plain D Phrygian dominant — keep the **raised 7th (C#)**; it is the point.
- A wall of sound with no dynamics — the short dark recharges and the
  16th→32nd chant-gate escalation are what make the peaks hit. Relentless ≠
  undifferentiated.
```
