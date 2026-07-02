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

### 13. `kanly.wav` — *Kanly* (3:40)
**Script:** `generate_kanly.py`

The daytime mirror of *Night Pursuit*, and its answer. Where that track
ends with the desert winning (the worm erases the hunt), this one is the
lone rider who **completes** the kill at dawn — and finds only emptiness
on the other side of it. *Kanly* is the Dune word for the formal
blood-feud; the rider crosses open sand to settle one. Reference:
**Lawrence of Arabia's** relentless crossings and the **John Wick**
single-minded assassin. A six-act story at 112 BPM where no section
repeats verbatim.

- **Act I — Dawn** (0:00): the shared wind + drone recipe (for
  crossfading), brightened by a rising **sunrise shimmer** — a swept
  noise band and warm partials carrying the **major third F#**, the
  warmth the night tracks deny. A **ney** call quotes the world's Theme A:
  the rider wakes, the sun crests the dune.
- **Act II — The Ride** (0:24): **galloping hoofbeats** (a new recipe —
  dry dusty thuds in a triplet canter, lead/trail hooves alternating L/R)
  are the engine. A gated sub on the stride; the oud states **Theme R**,
  the rider's theme, in D Phrygian dominant (Hijaz) with its exotic
  augmented second. Relentless but patient.
- **Act III — The Wait** (1:15): the gallop cuts dead. **Destiny's clock**
  (the *Night Pursuit* tick) counts alone over a held-breath sub and a
  **tremolo-string** bed on the E♭–F# augmented second; the duduk asks one
  question, unanswered. He waits at the elder's door.
- **Act IV — The Hunt** (1:41): a noise **riser** launches the gallop back,
  doubled and wider, over **war drums**, driving 16th-note bass and full
  maqsum darbuka; Theme R an octave up, urgent. The closing-in.
- **Act V — The Kill** (2:28): one decisive blow — the highest-energy
  moment of the track, a sub-boom under a short metallic **blade ring** —
  and the groove stops dead. Not the worm. A man's blade.
- **Act VI — Emptiness** (2:32): the hollow after. The drone **sinks 6%**
  with a faint flat-second partial (the *Fall of Arrakeen* agony recipe),
  a lone broken duduk plays Theme R in dying fragments, and the wind
  floods back — ducked below the dawn, colder and emptier. One far
  hoofbeat that never repeats: the horse walking away. The kanly is
  settled and it bought nothing.

### 14. `the_navigator.wav` — *The Navigator* (6:05)
**Script:** `generate_the_navigator.py`

Dune + Goa trance: a Guild Navigator consuming the spice and folding
space, consciousness dilating until past and future collapse into one
fold. The album's first escape from home: **E Hijaz Kar**
(E–F–G♯–A–B–C–D♯), the first key that resolves to a **major third** —
and **THEME_FOLD**, a 4-bar hook that resolves *upward* to G♯: the
album's first ecstatic, unshadowed resolution. New machinery to match:
a two-operator **FM Goa lead** (index decaying 4→0.8, bright→warm
sweep — the nasal Juno Reactor melody voice), a **choir-formant pad**
("ah"-vowel bandpasses pulsing to true zero), a **crystalline FM
arpeggio** ping-ponging hard L/R and doubling to 32nds in builds, and a
**tabla tarang** (darbuka with tuned E2/B2 resonator rings). Also the
bass-mastering reset: the deep 55 Hz shelf removed, sub boom lifted to
66→52 Hz — the earbud-friendly target (~+2 dB below 100 Hz) all later
psy tracks inherit. Structure: submersion → awareness → PRESCIENCE
(drop 1) → the held breath → CONVERGENCE → **THE FOLD** (peak drop) →
stillpoint (one vast hit, then dead air — the ship has arrived) →
arrival (the groove returns warmer, THEME_FOLD resolved to a long G♯
hold) → the void beyond, stripped layer by layer to silence.

### 15. `jihad.wav` — *Jihad* (5:55)
**Script:** `jihad.py`

The dark one (idea B3): the holy war Paul foresaw — the war that
*follows* the victory. War psy at 152 BPM in **D Hijaz Kar** (the
Navigator's scale, weaponised back onto the album's D root), a direct
energy successor to *Fall of Arrakeen*: same room-shake kick stack, sub
boom and sidechain pump, but the pulse never fully stops. The
**Sardaukar chant is chopped into rhythm** — 16th- and 32nd-note gated
chant bursts are the battle-breath that carries every recharge — and
above it a **screamed carnyx horn** (the war horn pushed into chaotic
vibrato, a 1.8–3.5 kHz scream formant and tanh drive) declaims
THEME_JIHAD over each drop. First appearance of the wide **12-voice
choir** (the Choir of Sietch Tabr recipe, later quoted by *Kwisatz
Haderach* and *Sihaya*), and a war-noise bed instead of desert wind:
low massed feet and engines, mid roar, far screams. The piece escalates
through **three waves**, each drop longer and heavier than the last,
then an 8th-note kick sprint — and **ends mid-fury with a hard cut to
silence**: the album's only unresolved ending. The war does not end;
the track just stops being able to watch.

### 16. `kwisatz_haderach.wav` — *Kwisatz Haderach* (9:00)
**Script:** `generate_kwisatz_haderach.py`

The album closer (idea B1): a track that **contains the whole album**.
The one who can be many places at once sees every timeline the psy line
has visited — three "visions of possible futures" cycle the actual
engines and riffs of the previous psy tracks: *Water of Life*'s trance
kick and rolling K-b-b-b bass (Theme W on the duduk), *Sleeper*'s
brighter kick and sliding 303 (Theme S), *Arrakeen*'s room-shake stack,
snare march and war horn (THEME_WAR). Each vision is interrupted by the
*Night Pursuit* tick and a heartbeat: time itself changing the channel.
Then the still point (ghosts of all three themes drift past), the
24-bar build, and **THE FUSION** — 104 bars with all three engines at
once: both basses sidechained against the arrakeen kick, both 303
riffs in 2-bar call-and-response panned L/R, the 12-voice choir, war
drums, two mini-dips, **Theme A over the machine**, a false ending, and
a last wave where Theme A (duduk + ney) and THEME_WAR (horn) sound
together over an 8th-note kick sprint. 146 BPM, 33 committed layers,
seed 10193. At 8:14 one final stab silences everything — except the
original arrakis wind, which plays the album out alone: **the first
sound of the album is also the last**.

### 17. `gurneys_song_v2.wav` — *Gurney's Song* (4:15)
**Script:** `generate_gurneys_song.py` (design notes: `gurneys_song_notes.md`)

The album's only **performed** piece (idea C2): Gurney Halleck alone
with his baliset between battles — one instrument, one-take feel, fully
rubato, no wind, no drone, no grid. He plays the album's main theme
(THEME_A, the duduk line from *Water of Life* and *Kwisatz Haderach*)
as a song. The **baliset** is the oud recipe grown up: 9 strings in 3
triple courses (three detuned Karplus-Strong strings per note), a warm
3-tap pick, body resonance from a two-mode IR (110/220 Hz — wood, not
synth), strummed chords with staggered onsets, flageolet harmonics, and
performance dirt (fret squeaks, room tone). Intimate small-room reverb.
v2 rebuilt the piece around the feedback that became the *Sihaya*
doctrine: **one continuous performance cursor** (no dead seams — every
section starts where the last ends), the tuning intro cut to a breath,
and the good motifs (the arpeggio figure, the descant) properly
developed instead of abandoned after four bars.

### 18. `litany_against_fear.wav` — *Litany Against Fear* (6:00)
**Script:** `generate_litany_against_fear.py` (design notes: `litany_against_fear_notes.md`)

The beatless psy track (idea B4): the litany is not a description of
fear but a *procedure* for surviving it, and the track performs the
procedure — eight sections, one per line. The compositional conceit:
**the D drone is "I"** — it fades in first, never changes character,
holds perfectly steady while fear peaks around it, and is the only
thing left at the end. Everything else is fear: *Sleeper*'s 303 engine
at **1/8 speed** (RIFF_DARK quoted verbatim, one riff statement = one
13.2 s slow bar), the chant's formant stack stretched into E♭/E drones
beating against D, **whispered-noise vowels that almost say the words**
(pink noise through i/e/a/o/u formant pairs — the recipe that became
*Sihaya*'s singing voices), texture dust, and a heartbeat that quickens
toward the peak and slows as fear recedes. After the pass-through and
recession: **3.5 seconds of exact digital zero** — the album's only
true silence ("where the fear has gone there will be nothing") — and
then the drone alone, unchanged, fading only because the track ends.
Only I will remain.

### 19. `sihaya.wav` — *Sihaya* (6:00)
**Script:** `generate_sihaya.py` (design notes: `sihaya_notes.md`)

The album's first actual **song** — verse / chorus / bridge form, a
refrain the listener can hum, and question-and-answer at every level.
Reference: *Inama Nushif* from the Children of Dune miniseries. *Sihaya*
("desert spring") is Paul's name for Chani, and the track is a **duet**
between two new synthesized singing voices: the Sardaukar glottal source
made melodic and sung through interpolated vowel formants — **Paul**, a
close dry baritone, and **Chani**, an octave up, brighter and breathier.
The "lyrics" are vowel sequences; the refrain is the title itself:
i–a–a, *si-ha-ya*, identical in all four choruses (18 sung hook
statements in total). 96 BPM, D Phrygian dominant, one chord-progression
family for the whole song (the Gurney's Song voicings — same songbook).

- **0:00** — baliset arpeggio; Chani hums the hook half-voice: the
  thesis in ten seconds, her last note ringing across the verse downbeat.
- **0:10** — verse 1: Paul sings paired question/answer phrases (same
  rhythm, questions ending off-tonic, answers resolving to D), the oud
  echoing every tail; pre-chorus trades (he asks, she answers) rise into
- **1:10** — CHORUS 1: the refrain — Paul, Chani an octave up, Paul,
  Chani — full darbuka, quiet choir. **1:50** verse 2 swaps the roles:
  Chani leads a varied melody and *Paul* echoes; the second pre-chorus
  runs the rise in canon, her one bar behind.
- **2:50** — CHORUS 2: both voices in parallel octaves, war drums on the
  cell downbeats.
- **3:30** — the bridge: layers strip one per bar down to baliset and
  wind while the duduk drifts unresolved **Theme A** fragments — the
  album's oldest question — then the rebuild: the voices hum Theme A in
  alternation, strings and riser crescendo, and everything cuts to
  **one beat of near-silence** with only Chani's pickup note hanging in
  it —
- **4:20** — CHORUS 3 slams back; ney descants answer every line.
- **5:00** — CHORUS 4, the everything-chorus: the choir doubles the
  hook, and **Theme A on the duduk sounds under the refrain as a
  counter-line** — question and answer together at last. The final line
  stretches ritardando across the seam.
- **5:40** — outro bookend: the band stops on one ringing strum, Chani
  hums the hook once more over the arpeggio, a last quiet strum rings
  into the wind.

The script verifies its own form: it prints the sung-hook count, a seam
checklist (what crosses every section boundary — pickup, ringing chord,
or fill), and per-section RMS with ordering checks (chorus 1 above its
pre-chorus, chorus 4 the loudest, the bridge trough the quietest point).

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
python3 generate_kanly.py            # -> /workspace/music/kanly.wav
python3 generate_the_navigator.py    # -> /workspace/music/the_navigator.wav
python3 jihad.py                     # -> /workspace/music/jihad.wav
python3 generate_kwisatz_haderach.py # -> /workspace/music/kwisatz_haderach.wav
python3 generate_gurneys_song.py     # -> /workspace/music/gurneys_song_v2.wav
python3 generate_litany_against_fear.py # -> /workspace/music/litany_against_fear.wav
python3 generate_sihaya.py           # -> /workspace/music/sihaya.wav
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
