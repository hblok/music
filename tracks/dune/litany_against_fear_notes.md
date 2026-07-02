# Litany Against Fear — design notes (B4)

Composition document for review before writing
`generate_litany_against_fear.py`. Spec source: `more_ideas.md` B4
("beatless psy, 6 min — Shpongle / ambient-side Juno Reactor").

## Concept

The litany is not a description of fear — it is a *procedure* for
surviving it. The track performs the procedure. Eight sections, one per
line of the litany, over 6:00. No kick, no bar-grid percussion at all.

The compositional conceit: **the D drone is "I"** — it fades in first,
never changes character, and is the only thing left at the end.
Everything else in the track is fear: it approaches, densifies, passes
*through* the stereo field, recedes, and is gone. The drone doesn't
flinch — while fear peaks around it, the drone holds exactly steady.
That's the litany: the self as the constant term.

- Length 6:00 (360 s). Beatless — the only pulse is the slowed 303 cycle
  and (optionally) a heartbeat.
- Key: D. Fear = the flat second (Eb against D), stacking as it nears.
- Seed: `np.random.default_rng(0)  # where the fear has gone: nothing`.
- Output: `/workspace/music/litany_against_fear.wav`.

## Tempo: the 1/8-speed sleeper 303

sleeper_awakens runs at 145 BPM, 16th = 0.1034 s. At **1/8 speed** one
riff step = 0.827 s, so one 16-step riff statement = **13.2 s = one slow
bar**. That slow bar is the track's breathing rate (~27 statements over
the track). All section boundaries land on slow-bar edges.

Riff: **RIFF_DARK** quoted verbatim from sleeper — it broods on D (50)
and already contains the Eb (51) *and* the slide 48→50: the flat second
is built into the source material. In the peak sections a second 303
voice adds RIFF_SYNC's answering contour a slow-bar later, panned
opposite.

## Structure — one section per litany line

| t | line | what happens |
|---|------|--------------|
| 0:00 | *I must not fear.* | D drone fades in from nothing (deep, dark, evolving). Breath-whispers, barely there. One 303 note per slow bar: a single D blooming open and closing (cutoff up-down over the whole bar). |
| 0:44 | *Fear is the mind-killer.* | The full RIFF_DARK begins at 1/8 speed. Formant drone enters on D (chant recipe, pulse removed, 4 s attacks). Whispers start forming phrase-shapes. |
| 1:28 | *Fear is the little-death that brings total obliteration.* | Fear approaches: Eb formant drone stacks against the D. A second 303 voice (RIFF_SYNC) enters offset, opposite pan. Whisper phrases more insistent, texture-dust shimmers begin. Heartbeat emerges at ~52 BPM, slowly quickening. |
| 2:18 | *I will face my fear.* | Peak density — but the D drone holds perfectly steady underneath. Eb *and* E-natural drones beat against D. Both 303s with cutoff ceilings rising each bar. Whispers almost intelligible, dense dust. Heartbeat ~72 BPM. This is the loudest section, RMS target ~0.11. |
| 3:06 | *I will permit it to pass over me and through me.* | The pass-through: the entire fear stack (303s, Eb/E drones, whispers, dust) makes one slow traverse of the stereo field, L → through center → R, over ~20 s, then starts thinning. The D drone does not move. Heartbeat begins slowing. |
| 3:50 | *And when it has gone past, I will turn the inner eye to see its path.* | Recession: layers strip one per slow bar (dust, second 303, E, Eb, whispers...). The first 303 slows to 1/16 speed — its last note is a long slide 48→50 that never resolves its cutoff. Two final heartbeats. Breath. |
| 4:38 | *Where the fear has gone there will be nothing.* | **TRUE SILENCE** — hard cut to digital zero, ~x s (album's only full silence; even Gurney's room tone rule is suspended, deliberately). (see notes below regarding lenth of silence) |
| 4:47 | *Only I will remain.* | The D drone alone, unchanged, ~43 s — then a 30 s fade to nothing (5:30–6:00). The fade is part of the remaining. |

## Instruments / layers

1. **The D drone ("I")** — per the drone-bed rules: LOW (D1+D2,
   36.7/73.4 Hz core with a quiet 146.8 partial), detuned pairs
   lowpassed ~400 Hz, evolving only via slow_noise filter/amp drift, no
   mid-frequency beating. Constant gain from 0:20 to 5:30. Never ducks,
   never swells with the fear — that is the point.
   (User note: Be careful here: The drone sounds can be pretty overwhelming and distract from the rest of the music. Especially if it last a long time. Let's make sure the entire song does not sound like a vacum cleaner is running in the background).

2. **Slowed 303 × 2** — sleeper's `acid_note` engine (iirpeak Q=11,
   tanh(2.8x), bright→dark crossfade) with the time base ×8: note
   durations 0.8–13 s, the per-note filter zap replaced by a whole-bar
   cutoff arc (rise-fall raised-cosine, lo 250 Hz, hi climbing 900 →
   2600 Hz section by section). Slides become 1+ s glides (cumsum pitch
   curve, as in sleeper). Level: ambient — a voice inside the texture,
   not a lead.
3. **Formant drones (the chant, stretched)** — chant_note's formant
   stack ((380,560), (750,1000), (2200,2700) bandpasses) minus the
   5.5 Hz pulse: 4 s attacks, 6 s releases. One on D throughout from
   0:44; fear adds Eb (1:28) and E (2:18) copies. The 2.2–2.7 kHz
   formant kept ≤ 0.10 gain (anti-tinnitus).
   (User note: Again, be careful with constant unwavering sounds)

4. **Whisper texture (the litany itself)** — white noise through two
   swept formant bandpasses (F1/F2, Q≈8) walking vowel targets:
   i(270,2300) e(530,1840) a(730,1090) o(570,840) u(300,870). Each
   "phrase" = a 2–4 s breath envelope traversing 3–6 vowels — it
   *almost* says words. Alternates ears L/R like someone whispering
   close (the psy element). Density/urgency follows the fear arc.
   (User note: "white noise" - they we want to be ver careful with that)

5. **Fear stack pads** — Eb and E sine-cluster pads (detuned ±0.3%)
   that beat against the drone's D2/D3 partials at 1–4 Hz — audible
   dissonance roughness = fear proximity. Mid register, moderate gain,
   removed one at a time in the recession.
6. **Heartbeat** — soft doum (falling 55→35 Hz sine, no click): 52 BPM
   at 1:28 → 72 at the peak → slowing through the pass-through → two
   final beats alone at ~4:30, then silence. The body's fear, calming.
7. **Texture dust** — sparse Shpongle grains: tiny (60–150 ms)
   highpassed chimes/reversed shimmers at low gain, density tracking
   the fear arc, gone by the recession. No melodic content.

## Master / verification

Long hall reverb (5 s IR) at higher wet than the groove tracks (~0.35)
— except the drone, which stays dry/close (it's *inside* the listener).
Gentle tanh bus. Target arc: intro ~0.03 → build 0.06 → peak ~0.11 →
recession 0.05 → silence 0.000 exactly → coda drone ~0.035.

Built-in checks: (a) peak section = *I will face my fear*; (b) the
silence bar RMS must print 0.000; (c) drone-band (30–90 Hz) RMS
measured at 2:30 vs 5:00 must match within ~1 dB — proof the "I" never
flinched.

## Decision points for review

1. **Silence length**: spec says "one bar" = 13.2 s of digital black.
   Proposed ~9 s instead — long enough to be shocking, short enough
   that it doesn't read as playback failure. Happy to do the full bar.
   (User note: I'll push back on this: a 9s silence is not shocking - it sounds like the track already stopped, so it's puzzeling when it comes back and plays for another few bars)

2. **Heartbeat**: in the current plan (it made ambient_composition
   better per earlier feedback). Cut if it reads as a beat in a track
   whose point is beatlessness.
3. **Whisper intelligibility**: vowel sequences can be scripted from
   the actual litany lines ("I-must-not-fear" = i-a-o-i...) so each
   section whispers its own line, or kept as random vowel walks
   (more abstract, less risk of sounding gimmicky). Currently planned:
   scripted per-section sequences — it's invisible structure that
   costs nothing.

## Build conventions

Standalone script, numpy+scipy only, duplicate helpers. Layer-commit
bus with per-layer peak norm (jihad.py pattern) — this track has ~8
layers and needs the balance control. WAV to /workspace/music, script
staged in git, not committed. Section RMS report + the three checks
above printed at the end.
