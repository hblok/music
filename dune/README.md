# Dune Music — Generative Ambient Soundtrack

Procedurally generated ambient music for the Dune RTS project. Every track is
synthesized entirely in Python (numpy + scipy) — no samples, no external audio
assets, no DAW. Each generator script is deterministic (seeded RNG), so a
track can always be regenerated bit-for-bit from its script.

**Layout:** generator scripts live here in `/repos/dune/music` (tracked in
git); the generated `.wav` files are written to `/workspace/music/` and are
not committed.

## The Tracks

### 1. `ambient_track.wav` — *Untitled Ambient* (3:00)
**Script:** `generate_ambient.py`

The first experiment: a calm, atmospheric electronic ambient piece. A
four-chord pad progression — **Dm9 → B♭maj7 → Fmaj7 → Cadd9** — drifts by at
45 seconds per chord, with each chord voice breathing on its own slow LFO so
the texture never sits still. Underneath: a sub drone on D; above: filtered
noise swells that drift across the stereo field, and sparse sine plucks from
the D minor pentatonic scale with long echo tails.

### 2. `arrakis_winds_v2.wav` — *Arrakis Winds* (3:30)
**Script:** `generate_arrakis.py`

The Dune track: land of sand, wind across the desert, the universe as
backdrop. No chord progression here — instead a static, vast soundscape:

- **Gusting desert wind** that swells and lulls like real weather, drifting
  across the stereo field.
- **Shai-Hulud rumbles** — five sub-bass thumps with falling pitch (felt more
  than heard), something enormous moving under the sand.
- **Distant calls** — duduk-like melodic phrases in **D Phrygian dominant**
  (D–E♭–F♯–G–A–B♭–C), the scale behind the classic "desert" sound, drowned
  in reverb so they sound kilometres away.
- **Sand and stars** — granular crackle that only fires when the wind gusts,
  and faint high "star" partials as an intro-only texture (v2 fades them out
  by 70 s; in v1 they ran the whole track and turned tinnitus-like).

### 3. `base_under_attack_v2.wav` — *Base Under Attack* (3:15)
**Script:** `generate_base_attack.py`

The sequel: designed to **crossfade seamlessly out of Arrakis Winds** — it
opens with the identical wind + drone recipe. Then, at 15 s, a detonation
hits and the assault begins **instantly** — a sudden attack, not a build:

- A brief, urgent **two-tone klaxon** (fast 120 ms beeps, mostly dry)
  announces the strike, repeats twice early on, then stops.
- **Darbuka** (doumbek) percussion at full 128 BPM from the very first bar,
  playing a *maqsum* rhythm — deep *doum* center-strokes (doubled by a
  sub-kick), sharp *tek* rim slaps answering left/right, ghost *ka*
  strokes, and a driving fill every fourth bar.
- A plucked **oud** (double-course detuned strings) drives an eighth-note
  riff in D Phrygian dominant (D–D–E♭–D–C–D–F♯–E♭) with occasional octave
  jumps.
- **Enemy flybys** — detuned cluster swells rising in pitch, sweeping from
  one speaker to the other like craft passing overhead.
- **Explosions, deep and slow** — soft-attack booms lowpassed below 150 Hz
  with falling sub-sine cores, frequent throughout the battle. The final,
  biggest detonation at 168 s kills the groove dead. Only wind and drone
  remain: the aftermath.

(v1 used an accelerating heartbeat kick, a slow reverbed alarm motif and a
sawtooth bass — the alarm read as horror-movie eerie and the bass as a
trombone, neither fitting the Dune universe, so v2 replaced them with real
Earth Middle Eastern instruments and made the attack sudden.)

### 4. `night_pursuit.wav` — *Night Pursuit* (3:45)
**Script:** `generate_night_pursuit.py` (samples: `generate_samples_pursuit.py`)

A chase across the desert at night — more energetic, rhythm-driven, but not
dance music. Reference: the **John Wick 3/4** scores (ticking-clock
ostinati, pulsing bass, percussion momentum) inside the Dune palette. The
focus is **composition**: a five-act story at 104 BPM where no section
repeats verbatim.

- **Act I — Stillness** (0:00): the Arrakis wind + drone recipe (verbatim,
  for crossfading); a single duduk call — the scout spots movement.
- **Act II — The Tick** (0:18): a bone-dry **tick-tock clock** in straight
  eighths — the one constant of the hunt — then a **gated sub-bass pulse**
  (tanh-warmed sine, not sawtooth) and a skipping **frame drum**.
- **Act III — The Chase** (0:55): the oud states **Theme A**, the duduk
  answers an octave up, and a frame-drum roll + noise **riser** slam into
  the full pursuit: **war drums** (taiko-like, falling 90→42 Hz), driving
  16th-note bass, full maqsum darbuka.
- **Breakdown** (2:04): everything cuts dead except the tick and a
  sub-kick **heartbeat** — the prey vanishes behind a dune. A lone held
  E♭ hangs unresolved.
- **Act IV — Cornered** (2:22): the tonal center sinks to **G** — D
  Phrygian dominant is mode 5 of G harmonic minor, so the pitch set is
  unchanged but the gravity darkens. Theme B on the duduk, the heavier
  *saidi* drum pattern (double doum), and a **tremolo-string** bed.
- **Act V — The Strike** (2:50): back to D, Theme A an octave up over
  everything — until at **3:08 the ground answers**: a worm strike kills
  the groove dead. Wind, drone, and a descending duduk coda. The desert
  always wins.

### 5. `the_maker_comes.wav` — *The Maker Comes* (7:20)
**Script:** `generate_maker_comes.py` (samples: `generate_samples_maker.py`)

Long-form extension of *Night Pursuit*, built from listening feedback on
it: the climax at 2:50 ("now it really starts!") ended too soon, and the
sparse stalking intro read as odd. Here the **2:50 material is the main
material** — after ten seconds of wind the full groove starts at full
commitment — and the track runs seven minutes before finally arriving at
the worm-strike ending. The story: all that drumming on open sand is
heard by something far older than any hunter.

- **0:10** — full pursuit groove, Theme A high on the oud, then on the duduk.
- **1:05** — episode, half-time: a **Sardaukar throat chant** (new:
  formant-filtered glottal source, guttural 5.5 Hz pulse, sub-octave) rises
  out of the bass while a **ney flute** (new: near-pure tone + breath
  noise) floats a new **Theme C**. Distant detonations.
- **2:05** — relaunch: Theme C driven on the oud, duduk answering Theme A —
  development, not repetition.
- **3:01** — breakdown callback (tick + heartbeat + the lone flat second).
- **3:19** — cornered in G, Theme B and saidi drums — the chant joins.
- **4:05** — **the long climax**: five 8-bar waves, each adding a layer
  (strings+oud / +duduk / +ney / +chant / +fills everywhere).
- **5:38** — **false ending**: one huge hit, then nothing but wind and the
  tick still counting — and the groove slams back for the final sprint,
  the fastest music in the track.
- **6:19** — the sand erupts: the Maker takes the field. Extended coda —
  receding worm passes, the duduk lament, a ney echo, one last chanted
  breath.

### 6. `water_of_life.wav` — *Water of Life* (7:20)
**Script:** `generate_water_of_life.py` (samples: `generate_samples_water.py`)

The Dune palette taken to **goa/psy trance** — reference: **Juno Reactor**
(the Matrix scores), whose signature is exactly this fusion of tribal
percussion and rolling trance machinery. 140 BPM, still D Phrygian
dominant, still opening from the same wind. The story is the spice agony:

- **0:12** — a trance kick alone in the desert; offbeat hats sneak in.
- **0:39** — the **rolling psy bass** starts (kick-b-b-b): the poison is
  drunk. At **1:07** a dark **303-style acid line** begins to twist, with
  chant pulses underneath.
- **1:34** — break: a duduk prayer (Theme W) over strings, an 8-bar build
  with kick rolls → **2:02 DROP 1 — the agony**: full psy groove with the
  maqsum darbuka riding the trance grid.
- **2:56** — the acid turns melodic, a ney floats above: visions.
- **3:24** — **the inner world**: all rhythm gone — then a 16-bar build,
  chant rising, kick rolls, acid climbing one-way →
- **4:19 DROP 2 — the awakening**, with war drums: taiko over trance.
- **5:21** — after a four-bar dip, the final form: **Theme A from Night
  Pursuit sung over the full groove** — the album's melody over dance
  machinery at last.
- **6:09** — outro: layers strip away, the kick calms like a heartbeat
  and stops at 6:36. Wind, a duduk lament, one chanted breath, a ney
  echo. The sleeper has awakened; the desert is still there.

### 7. `the_sleeper_awakens.wav` — *The Sleeper Awakens* (9:30)
**Script:** `generate_sleeper_awakens.py` (samples: `generate_samples_sleeper.py`)

The psy opus: *Water of Life* rebuilt at full length from listening
feedback on it. The 303 was too flat — the new acid **sweeps its filter
within every note** (bright attack squelching dark, the actual TB-303
envelope), with resonance Q 11, harder drive, and **slide notes** that
glide into the next pitch. The groove was too muted — brighter kick
click, hotter hats, brighter darbuka teks, a new **psy clap** on 2 & 4,
and a master high-shelf. And the drops were over too quickly — both are
now **64 bars (~106 s)** with internal phases and mini-dips so they
evolve instead of looping. 145 BPM, seed 303. The story continues from
Water of Life: this is what the awakened one *sees*.

- **0:12** — kick alone; **0:39** rolling bass; **1:05** the sharp acid
  twists in, chant pulsing underneath.
- **1:45** — break (Theme S, new) and build →
- **2:11 DROP 1 — THE VISIONS** (64 bars): dark riff / syncopated slide
  riff + darbuka / **mini-dip A** (kick + screaming acid alone) / high
  riff + clap / **mini-dip B** (bass + hats + riser) / full peak.
- **3:57** — the acid turns melodic, a ney floats: a gentler timeline.
- **4:24** — **the still point**: all rhythm gone; then the 16-bar build.
- **5:17 DROP 2 — THE GOLDEN PATH** (64 bars), war drums over trance:
  slide riff / high acid + ney calls / **mini-dip C** (kick + chant
  alone — the Sardaukar moment) / melodic ride / peak.
- **7:09** — **the final form** (48 bars): Theme A from Night Pursuit
  sung three times over the full machinery, the last statement doubled
  by the ney an octave up.
- **8:29** — outro; the kick stops at 8:55. Wind, duduk lament, one
  chanted breath, a ney echo. He sees.

### 8. `fall_of_arrakeen_v2.wav` — *The Fall of Arrakeen* (6:05)
**Script:** `generate_fall_of_arrakeen.py` (samples: `generate_samples_arrakeen.py`)

War psy at 148 BPM — the album's heaviest track, built around a beat that
shakes the room. The kick is a **stack**: punch + click landing at 44 Hz,
a long sub tail falling to **D1 itself (37 Hz)** — and under every
4-on-the-floor hit a dedicated **sub boom** layer (a pure 50→37 Hz sine
sustaining the whole beat), while a **sidechain pump** ducks the bass and
drone ~55 % at each kick so the kick owns the sub alone. Three master
shelves (high + low + a deep one at 55 Hz). ~26 layers — field snare,
war horn, battle toms, shaker, reverse cymbals, oud and explosions join
the psy machinery. New themes throughout: **Theme WAR** (martial, dotted,
with a B♭→A "war cry" fall), two acid riffs built on the same cry, and
**Theme L**, the dying-fall lament. The story: preparation for war —
buildup and launch — attack, fight — then the aftermath: silence, agony,
death.

- **0:10** — PREPARATION: the field-snare march, slow war drums, the oud
  riff assembling, chant every bar.
- **0:36** — MUSTER: the kick enters; bass at 0:49; the dark acid and the
  horn's war call at 1:02.
- **1:15** — the rise: snare rolls, riser, kick rolls, a long horn blast →
- **1:28 LAUNCH** (48 bars): war riff / high acid + horn / mini-dip
  (bass + snare march — a glimpse of the battlefield) / peak with toms.
- **2:46** — REGROUP: kick gone — march, chant, distant detonations; the
  second rise →
- **3:12 THE FIGHT** (64 bars): war drums + battle toms over the stack:
  melee / horn calls / mini-dip (kick + chant — the war cry) / peak ride /
  dip + riser / **THE SPRINT** (kick on 8ths, the fastest and heaviest
  music on the album) — ending in
- **4:55 THE DEATH BLOW**: one huge detonation kills everything. Wind,
  falling rumbles, a decelerating heartbeat that stops, the duduk lament
  ending in a dying fall, a sinking drone with a flat-second shimmer —
  the agony — and one far horn over the burning city. Death is quiet.

(v1 had the kick stack but the wall still didn't vibrate — v2 added the
sub boom layer, the sidechain pump, the deeper D1 tail and the 55 Hz
shelf, doubling the drops' sub-60 Hz energy.)

### 9. `arrakis_winds_v3.wav` — *Arrakis Winds v3* (6:00, seamless loop)
**Script:** `generate_arrakis_winds_v3.py`

The original deep-desert ambience rebuilt with everything learned since,
as **the background track for the game** — quiet, no beats, and a
**perfect seamless loop** (the final 10 s are equal-power-folded into the
head, so event and reverb tails survive the wrap and the seam is
inaudible). Twice the length of v2, with subtle interest scattered so each
minute holds one small event, in three families:

- **Pure desert nature** — the gusting wind/sand recipe, six worm rumbles,
  the D1 drone now crossed once (~3:25) by a swelling **E♭ shadow
  partial** (the Dune flat-second, a cloud passing over), and the
  starfield confined to two ~40 s night windows, pulsing to true silence.
- **Distant human traces** — three drowned duduk phrases; two lone
  **baliset** phrases (Karplus-Strong double-course pluck, 2:08 and 5:12)
  from a sietch beyond the dunes; one far-off **throat chant** swelling
  out of the wind at 3:52.
- **Hints of menace** — a single distant **war horn** off to the east at
  4:28, and at 1:26 a **machinery tremor**: eight sub pulses spaced
  exactly 0.9 s apart — too regular to be a worm.

### 10. `spice_must_flow.wav` — *The Spice Must Flow* (4:30, seamless loop)
**Script:** `generate_spice_must_flow.py`

The economy/harvesting state loop — "everything is fine, build your base."
Mid-energy, between the ambient loop and the battle tracks: a harvester
works the open sand at 64 BPM (72 bars exactly, loop-folded over a 2-bar
crossfade so the seam lands on the beat grid).

- **The machine** — two detuned squares on D2 beating against each other,
  amplitude-gated into an 8th-note chug with an idle floor (the engine
  never fully stops); soft footfall thumps on 1 & 3, piston clanks
  answering off to the right.
- **Hammered santur** (new instrument: struck Karplus-Strong, two strings
  per course) playing a hypnotic ostinato that alternates every 8 bars
  and swells on a 24-bar wave.
- **The harvester listens** — twice (1:30, 3:30) a worm rumble rolls
  through and every human-made layer cuts within half a second, holds two
  bars of held breath (wind, drone, rumble only), then spins back up.
- One friendly **cargo-thopter flyby** (2:15) — descending cluster with
  wing-flutter AM slowing 23→13 Hz as it passes L→R — plus two distant
  duduk quotes of Theme A and ~50 high "spice sparkle" pings.

### 11. `stillsuit.wav` — *Stillsuit* (3:00, seamless loop)
**Script:** `generate_stillsuit.py`

The tension/enemy-sighted state loop — enemy units spotted, nothing fired
yet. *Night Pursuit* Act II distilled into a loop at 96 BPM (72 bars,
2-bar grid fold). The design rule: **nothing ever builds** — this loop
must run for ten minutes without resolving, because game logic may never
deliver the drop a build would promise. All variation wanders
(slow-noise gain drift) or cycles; verified flat RMS trend across the
track.

- **The tick-tock clock** is the star — bone dry, straight 8ths, tick
  left answering tock right, at constant gain: the one fixed point of
  the watch.
- A **gated sub-bass pulse** in sparse 16ths on D2 with the C2–E♭2–D2
  cadence walk every 4th bar; **tremolo strings** hold the D+E♭ minor
  second, gain drifting 0.25–1.0 but never ramping.
- **Stillsuit breathing** (new) — your own breath through the mask, one
  cycle per bar (24/min, slightly too fast): a bright inhale on beats
  1–2, a darker exhale on 3–4. Close, dry, centered — inside your hood.
- Twice (0:50, 1:55) a lone held **E♭ hangs over the watch** for two
  bars and fades without ever resolving to D. No fills, no risers,
  no resolution.

### 12. `sandstorm_coriolis.wav` — *Sandstorm Coriolis* (1:12, seamless loop, OVERLAY)
**Script:** `generate_sandstorm_coriolis.py`

Not a standalone track — a **weather overlay** the game engine fades in
*over* whatever state music is playing (everything shares the key of D,
so it blends), holds while the storm lasts, and fades out. Overlay rules:
no melody, no events, and **no lulls** — a slow AGC levels the bus
(verified min/mean 1-s RMS 0.82) while leaving the fast flutter intact.

- **The noise wall** — dense 300 Hz–8 kHz noise, channels drawn
  independently, with 8–14 Hz random flutter AM and gusts at 3× the
  normal arrakis rate over a high floor.
- **Shepard wind** (new trick) — eight whistle voices gliding perpetually
  upward through four octaves and renewing silently at the bottom: the
  auditory illusion of endlessly rising fury that never arrives. Each
  voice pans in a slow 9 s circle — the Coriolis rotation. The 36 s
  traverse is exactly half the loop, so the illusion wraps perfectly.
- **Storm body** — brown-noise sub rumble below 130 Hz surging with the
  front; **sand blast** crackle against the canopy; and a faint **D
  pedal**, the only tonal content, keeping the storm in tune with the
  music underneath.

## The Musical Ideas

**One key, one mode family.** Everything is rooted on **D**. The calm track
uses D minor pentatonic; the Dune tracks use **D Phrygian dominant**, whose
flat second (E♭ against D) provides the exotic menace. This shared root is
what lets the tracks blend into each other.

**Tension without harshness.** Action is conveyed through *rhythm*
(the maqsum groove), *density* (frequent explosions), and *register*
(sub-bass weight) — never through loud transients or bright distortion.
Explosion attacks are 80 ms, not 1 ms. And action arrives *suddenly*: an
attack is a cut, not a crescendo.

**Real Earth roots for the desert.** The battle instruments are synthesized
Middle Eastern ones — darbuka strokes and a Karplus-Strong oud — rather than
western/orchestral timbres, matching Dune's Arabic-inspired world.

**Motion at every timescale.** Per-voice LFOs (seconds), gust cycles
(~5 s), weather fronts and pans (tens of seconds), and section structure
(minutes). Nothing is static, so nothing fatigues the ear — the v1 star-tone
lesson: any constant high-frequency element becomes tinnitus after a minute.

**Distance through reverb and darkness.** Far-away sounds are wet (75–80 %
convolution reverb) and dark (lowpassed IRs and timbres). Close sounds (kick,
bass) are dry.

## Regenerating

```bash
cd /repos/dune/music
python3 generate_ambient.py       # -> /workspace/music/ambient_track.wav
python3 generate_arrakis.py       # -> /workspace/music/arrakis_winds_v2.wav
python3 generate_base_attack.py   # -> /workspace/music/base_under_attack_v2.wav
python3 generate_night_pursuit.py # -> /workspace/music/night_pursuit.wav
python3 generate_maker_comes.py   # -> /workspace/music/the_maker_comes.wav
python3 generate_water_of_life.py # -> /workspace/music/water_of_life.wav
python3 generate_sleeper_awakens.py # -> /workspace/music/the_sleeper_awakens.wav
python3 generate_fall_of_arrakeen.py # -> /workspace/music/fall_of_arrakeen_v2.wav
python3 generate_arrakis_winds_v3.py # -> /workspace/music/arrakis_winds_v3.wav
python3 generate_spice_must_flow.py  # -> /workspace/music/spice_must_flow.wav
python3 generate_stillsuit.py        # -> /workspace/music/stillsuit.wav
python3 generate_sandstorm_coriolis.py # -> /workspace/music/sandstorm_coriolis.wav
```

For game-engine delivery, WAVs convert to mp3 with ffmpeg:

```bash
ffmpeg -i track.wav -vn -ar 44100 -ac 2 -b:a 192k track.mp3
```

(Note: mp3 encoder padding adds ~50 ms of silence at the loop point — for
gapless in-game looping use the WAV or an OGG; mp3 is fine for listening.)

New-instrument samples for Night Pursuit (war drum, frame drum, tick-tock
clock, gated bass, tremolo strings, riser, the assembled groove) are
generated by `generate_samples_pursuit.py` into `/workspace/music/samples/`;
it continues the numbering of `generate_samples.py` and refuses to
overwrite existing files. `generate_samples_maker.py` does the same for
The Maker Comes' new instruments (ney flute, Sardaukar throat chant), and
`generate_samples_water.py` for Water of Life's (trance kick, psy rolling
bass, 303 acid line, offbeat hats, zap FX, the assembled psy groove), and
`generate_samples_sleeper.py` for The Sleeper Awakens' (psy clap, the
sharpened sweeping/sliding 303, the brightened 145 BPM groove), and
`generate_samples_arrakeen.py` for The Fall of Arrakeen's (the v2
room-shaker kick stack, field snare march, war horn, battle toms,
shaker, reverse cymbal, the assembled 148 BPM war groove).

Requires `numpy` (all scripts) and `scipy` (the two Dune tracks). All output
is 44100 Hz stereo 16-bit PCM WAV, written to `/workspace/music/`. See
`CLAUDE.md` for implementation details and conventions when modifying or
adding tracks.
