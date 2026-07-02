# More track ideas — brainstorm

Where the album stands (9 tracks): quiet loops (`ambient`, `arrakis_winds_v3`)
on one axis, story-driven psy opuses (`water_of_life` → `sleeper_awakens` →
`fall_of_arrakeen`) on the other, with the hybrid action tracks
(`night_pursuit`, `maker_comes`, `base_attack`) in between. Everything is in
D, Phrygian dominant, one shared palette. These ideas extend along three
lines: **what the game needs**, **where the album story goes next**, and
**sounds we haven't made yet**. (Four older stubs live in `ideas.md` §3 —
harvester, victory stillness, sandstorm, palace interior — expanded below
rather than repeated.)

---

## A. What the game needs (RTS music states)

An RTS effectively has music *states*, not tracks. We already cover
exploration (`arrakis_winds_v3`) and full battle (`base_attack`). Missing
states:

### A1. *The Spice Must Flow* — economy / harvesting loop (4–5 min, seamless)
The "everything is fine, build your base" track. Mid-energy, **between**
ambient and battle: a slow mechanical heartbeat (the harvester idea from
`ideas.md`, promoted to a full track). 60–70 BPM half-time feel. Palette:
a deep rotating **machine pulse** (two detuned sub squares beating at the
"engine" rate, amplitude-gated so it chugs), soft tuned-percussion ostinato
on a new instrument — a **hammered santur** (Karplus-Strong but struck:
shorter excitation burst, two strings per course at ±0.3 %), and the wind
kept low. Occasional duduk fragments quote Theme A so it feels like the same
world. Loop-folded like v3. Interest events: cargo-thopter flyby (the
base_attack flyby recipe, but friendly — slower, descending), a distant
worm rumble that makes the machine pulse *pause* for two bars (the
harvester listens), then resume.

### A2. *Stillsuit* — tension / enemy-sighted loop (2–3 min, seamless)
The state between peace and combat: enemy units spotted, nothing fired yet.
This is `night_pursuit` Act II distilled into a loop: the bone-dry
**tick-tock clock**, a gated sub pulse at ~96 BPM, tremolo strings on the
D–E♭ minor second held at low gain, and NO percussion fills — the loop must
be able to run for ten minutes without resolving. Key design rule: nothing
ever *builds* (a build promises a drop that game logic may never deliver).
The tick is the star; everything else breathes around it.

### A3. *Sandstorm Coriolis* — weather event overlay (60–90 s, seamless)
From `ideas.md`, sharpened: not a track but an **overlay layer** the engine
fades IN OVER whatever is playing (it's all the same key — it will blend).
A dense 300 Hz–8 kHz noise wall with fast random AM (flutter 8–14 Hz), wind
gusts at 3× normal rate, plus a new trick: **Shepard-tone wind** — bandpassed
noise bands that perpetually glide upward and renew at the bottom, the
audio illusion of endlessly rising fury. No tonal content except a faint D
pedal so it stays in tune with the music under it.

### A4. *Victory: The Water of the Dead* — win-state coda (90 s, one-shot)
The `ideas.md` "victory stillness" stub, given a Fremen frame: victory in
Dune is mourning (water for the dead). One slow duduk statement of Theme A
over wind, answered — for the first time in the album — by a **major-third
partial** in the drone (D–F♯ instead of D–E♭): relief, not triumph. A single
soft frame-drum hit, long reverb, then 30 s of wind fading to the menu loop.
Defeat variant (A4b): same skeleton, but the duduk plays Theme L (the
arrakeen lament) and the drone sinks 6 % like the fall_of_arrakeen ending.

### A5. *Menu / title theme* (2–3 min, loop)
The album's overture: wind opens, then quote the first phrase of every
major theme in chronology — Theme A (oud), Theme C (ney), Theme W (duduk),
Theme WAR (horn, distant) — each drowned at arrakis-call wetness, never a
full statement, over the D1 drone with the Eb shadow drifting through.
Listeners who've played for hours will recognize every ghost.

---

## B. Where the album story goes (the psy line)

The psy trilogy is the spice arc: drinking (`water_of_life`), seeing
(`sleeper_awakens`), war (`fall_of_arrakeen`). Natural continuations:

### B1. *Kwisatz Haderach* — the 10-minute closer (9–11 min, ~146 BPM)
The album finale that earns the Man-With-No-Name layer count: target **40+
committed layers** at the climax. Structure idea: a track that *contains the
whole album* — it cycles through the signature groove of each previous psy
track (water's rolling bass → sleeper's sliding 303 → arrakeen's room-shake
stack) as "visions of possible futures", each 32 bars, each interrupted by
the breakdown tick, before fusing all three engines at once in the final
drop (two basses sidechained against the arrakeen kick, both 303 riffs in
call-and-response). Risk to manage: three engines = mud; the sidechain pump
and per-section RMS verification become load-bearing. Ending: every layer
stops except the original arrakis wind — the first sound of the album is
also the last.

### B2. *Spice Agony (Reverend Mother Mix)* — downtempo / dub version (7 min, ~85 BPM)
We have never gone *slow and heavy*. Dub-psy treatment of water_of_life's
material: half-time kick (still the room-shake stack — it hits harder with
more air around it), the rolling bass stretched to dotted-eighth skanks
through a new **tape-echo** recipe (feedback delay where each repeat is
lowpassed a little darker and pitch-wobbled by a slow LFO — `lfilter` chain
per repeat), the 303 playing one note per bar with a full-bar filter sweep.
Massive Attack / Juno Reactor's slower cuts as reference. This is the
"morning after" listening track.

### B3. *Jihad* — the dark one (8 min, 150+ BPM)
If fall_of_arrakeen was a battle, this is the war that follows the victory
— the thing Paul fears. Darker than anything yet: drop the mode to **D
Hijaz Kar** (`ideas.md` palace stub's scale, but weaponized — the double
augmented-second is genuinely unsettling at speed), full-track Sardaukar
chant as a RHYTHM instrument (chopped into 16th-note gates by the pump
curve), and a new **screamed horn** (the carnyx recipe pushed into tanh
saturation with chaotic vibrato). The structural dare: NO aftermath section
— it ends mid-fury with a hard cut to silence. The album's only
unresolved ending.

### B4. *Litany Against Fear* — the beatless psy track (6 min)
A "psychedelic ambient" track — psy-trance texture with no kick at all.
The sleeper 303 played at one-eighth speed (cutoff sweeping over whole
bars), the chant stretched into pure formant drones, and a whispered-voice
texture: bandpassed noise shaped by the chant's formant filters so it
*almost* says words. The litany as music: fear approaches (texture
densifies, flat seconds stack), passes through (one bar of true silence —
the album's only full silence), and only the listener remains (the D drone,
alone, 40 s). Shpongle / ambient-side Juno Reactor reference.

---

## C. Sounds we haven't made yet (new recipes to develop)

Ideas driven by synthesis technique rather than story — each would add a
reusable recipe to CLAUDE.md:

- **C1. Choir of Sietch Tabr** — many-voice unison chant: render the throat
  chant 12× with per-voice random detune (±0.8 %), onset jitter (±60 ms)
  and formant-frequency scatter (±5 %), sum and widen L/R by voice. The
  cheap path to "epic" we've avoided so far. Drop-in upgrade for any climax.
- **C2. Baliset, properly** — extend the v3 Karplus-Strong into a real solo
  instrument: 9-string courses (3×3), strummed chords (stagger course
  onsets 12–25 ms), body resonance via a short fixed IR (two damped modes
  ~110 Hz and ~220 Hz convolved in). Then a whole track of it: *Gurney's
  Song*, the album's only "performed" piece — one instrument, one take
  feel, rubato timing from `slow_noise`.
- **C3. Voice + music fusion** — we already have the game voice lines
  (gTTS+OLA pipeline). Run a line like "The spice must flow" through the
  chant's formant filters and granular-freeze it (overlapping 80 ms grains
  from a single vowel) into a pad. Vocal psy without recording a vocalist.
  Use sparingly: one phrase per track max, or it gets cheesy.
- **C4. Physical-model percussion upgrade** — current drums are
  sine+noise; try a 2D mesh/modal model for the big war drum: 6–10 damped
  resonant modes (`signal.lfilter` two-pole resonators) excited by a click,
  mode frequencies from a real timpani ratio table. Would deepen the taiko
  hits in any future war track.
- **C5. Binaural desert** — an arrakis_winds variant rendered with simple
  HRTF approximation (ITD delays + head-shadow lowpass per azimuth) so
  rumbles and calls have true 3D positions on headphones. The game is
  top-down, but a "night mode" headphone mix is a cheap luxury.
- **C6. The Voice (Bene Gesserit)** — sound-design experiment: a spoken
  syllable layered with a sub-octave copy, a ring-modulated copy, and a
  formant-shifted copy, all time-aligned. Useful as a game SFX *and* as a
  one-shot scare in B3.
- **C7. Real vocals / real lyrics** (from sihaya feedback, 2026-07-02:
  the vowel-only singing works but sounds "a bit strange — like a
  different language"; intriguing, but the next step is words). Take the
  sihaya duet to real text. Paths, cheapest first: (a) **TTS-derived
  singing** — we already have the gTTS/edge-tts + OLA pitch/speed
  pipeline from the game voices; render a line syllable by syllable,
  then OLA pitch-shift and time-stretch each syllable onto the melody
  grid (pitches + durations straight from the hook). edge-tts has Arabic
  neural voices — **Arabic fits the world** better than English and
  hides TTS artifacts from non-speakers; try an `ar-*` female voice for
  Chani's answers. (b) **Hybrid**: keep the synth vowel engine for the
  sustained vowels (it holds pitch perfectly) and graft TTS consonant
  onsets onto each note — real intelligibility, synth control. (c) Full
  English verses only if (a)/(b) prove out — English exposes every
  artifact. First experiment: one hook line ("Sihaya" is conveniently a
  real word) in all three treatments, A/B'd against the vowel engine.

---

## D. Album packaging (once the track list settles)

- Track-order pass: alternate ambient and psy so the album breathes
  (winds → pursuit → stillsuit → water → maker → sleeper → spice-dub →
  arrakeen → jihad → litany → kwisatz → victory coda).
- Master consistency check: per-track integrated RMS within ±2 dB, the
  psy tracks lowpass-matched (same three master shelves), all fades vs.
  loop-folds documented per track.
- Opus/mp3 batch export script (`export_album.py`) building on the ffmpeg
  step from `ideas.md` §1 — one command, full album, tagged filenames.
