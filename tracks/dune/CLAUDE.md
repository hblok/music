# CLAUDE.md — music/ generators

Implementation guide for the procedural music generators in this directory.
Read `README.md` first for the musical ideas; this file covers how the sound
is actually made and the conventions to follow when modifying or adding
tracks.

## Stack & constraints

- **numpy + scipy** (scipy ≥ 1.17 available). WAV output via the stdlib
  `wave` module or `soundfile`/`pydub` (both available).
  `generate_ambient.py` predates scipy being installed and is numpy-only
  (FFT-based filtering instead of Butterworth).
- Everything is synthesized: **no samples, no external audio assets**.
- Output format: 44100 Hz, stereo, 16-bit PCM. Mix is peak-normalized to
  0.85–0.88 before int16 conversion.
- All randomness goes through a single seeded `np.random.default_rng(seed)`
  so tracks are **bit-for-bit reproducible**. Seeds are thematic: 42
  (ambient), 1965 (novel publication year), 10191 (Atreides arrival year).

## Common architecture

Every script follows the same shape:

1. Constants: `SR = 44100`, `DURATION` (seconds), `N = int(SR*DURATION)`,
   `t = np.arange(N)/SR`.
2. Helper functions (copy them between scripts; they are deliberately
   duplicated so each script is standalone):
   - `midi_to_hz(m)` — pitch from MIDI number.
   - `fade(x, in, out)` — raised-cosine fade-in/out on the final mix.
   - `slow_noise(rate_hz, lo, hi)` — smooth random control signal: sparse
     normals at `rate_hz` points/sec, 3-point smoothed, `np.interp`'d to SR,
     min-max normalized. Used for gusts, pans, weather. Raise to a power
     (`**2.2`) to deepen the lulls.
   - `make_reverb_ir(seconds, decay, seed)` — exponentially decaying white
     noise, lowpassed at 4 kHz (dark tail), energy-normalized. Separate
     seeds (7 / 11) for L/R decorrelation.
   - `reverb(x, ir, wet)` — `scipy.signal.fftconvolve`, tail renormalized to
     the dry peak, then wet/dry mix. wet=0.4 near, 0.75–0.8 far away.
   - `add_at(buf, x, start_s, gain)` — bounds-safe event placement.
3. One section per instrument layer, each producing `layer_L`, `layer_R`
   normalized to peak 1.0.
4. Final mix: weighted sum of layers (weights are the balance knobs),
   `fade()`, peak-normalize, interleave to `(N, 2)`, int16, `wave.open`.
5. Print absolute output path, duration, and key event times.

## Synthesis recipes (the reusable tricks)

- **Wind**: white noise → Butterworth bandpass. Two bands: *whoosh*
  120–900 Hz (body) + *hiss* 2–7 kHz (sand), gains modulated by
  `slow_noise(0.22)**2.2` (gusts) + `slow_noise(0.07)**1.5` (weather front).
  Pan via constant-power law `cos/sin(pan·π/2)` with `slow_noise(0.05)`.
- **Drone**: D1 (MIDI 26, ~36.7 Hz) sine + harmonics 2 and 3, plus a 3.003×
  detuned copy of harmonic 3 for slow beating; amplitude "breath" LFO at
  0.012 Hz.
- **Pads** (ambient track): per chord-voice, two detuned sines (±0.07 %) +
  quiet octave partial, per-voice amplitude LFO 0.02–0.07 Hz; chords
  crossfaded with 8 s raised-cosine edges. L/R use reciprocal detune.
- **Pitch-glide tones** (worm thumps, kicks, explosion cores, flybys): build
  a frequency curve `f(t)`, then `phase = 2π·np.cumsum(f)/SR`,
  `np.sin(phase)`. Never multiply `f(t)·t` directly — that chirps wrongly.
- **Worm thump / explosion**: falling sub-sine (55→27 Hz or 60→22 Hz) +
  lowpassed noise. Explosions: *brown* noise (`np.cumsum` of white, detrended)
  → 150 Hz lowpass, envelope `(1-exp(-t/0.08))·exp(-t/1.8)` — the 80 ms
  attack is what keeps them "deep, not harsh".
- **Distant voice** (duduk-like calls): step-target frequency curve smoothed
  by a one-pole filter (`signal.lfilter` with ~90 ms time constant) for
  portamento; vibrato 5.2 Hz blooming over 1.2 s; harmonics 1–4 with falling
  gains; 2.2 kHz lowpass; 75 % wet reverb.
- **Darbuka kit**: *doum* = falling sine 55+35·exp(-28t) Hz + 190 Hz ring,
  doubled by a sub-kick (36+60·exp(-16t) Hz) for weight; *tek* = 2.5–9 kHz
  bandpassed noise slap + 640 Hz ping; *ka* = quieter, faster-damped tek.
  Rhythm = maqsum in 16th steps `{0:D, 2:T, 6:T, 8:D, 12:T}` with random
  ghost kas on off-16ths (p=0.3) and a tek fill every 4th bar.
- **Oud** (plucked string): Karplus-Strong — noise buffer of one period,
  smoothed (warm pick), then repeat with `prev = damp·0.5·(prev+roll(prev,1))`
  per period (damp≈0.992). Double-course: layer a second pluck at f·1.004
  at 0.6 gain. Pre-render one pluck per distinct pitch, reuse via `add_at`.
- **Klaxon** (alarm that isn't horror-eerie): six fast 120 ms beeps
  alternating 740/988 Hz, 8 ms attacks, only 25 % reverb wet. Brief and
  rare — onset plus two decaying repeats, then silence.
- **Sudden attack**: do NOT ramp tempo or fade instruments in. Pick an
  onset time, trigger a big explosion exactly there, start percussion and
  riff at full tempo/volume on the first bar, and duck the calm layers
  over ~1.5 s. (v1 used a 60→126 BPM accelerating heartbeat + slow
  reverbed alarm + sawtooth bass; user feedback: alarm = horror-movie,
  saw bass = trombone, build too gradual. v2 replaced all three.)
- **Tick-tock clock** (night_pursuit, the John Wick ostinato): 30 ms dry
  clicks — bandpassed noise burst + damped sine ping — alternating tick
  (2.1 kHz / 1250 Hz ping, panned L) and tock (1.5 kHz / 880 Hz, panned R)
  in straight eighths. Keep it bone dry (no reverb) and constant across
  sections while everything else changes; vary only its gain.
- **Gated bass pulse**: per-note events of sine + 0.35·(2nd harmonic)
  through `tanh(1.6·x)` for warmth (saw reads as trombone — v1 lesson),
  5 ms attack, hard `clip((dur-t)/0.05)` release. Accent pattern in 16th
  steps; cadence walk (C2–E♭2–D2) every 4th bar.
- **War drum** (taiko-like): sine body falling 90→42 Hz (exp, rate 9) +
  100–420 Hz bandpassed skin-noise slap, shared 6 ms-attack envelope
  decaying at 5.5/s. Doubled hits (beat 1 + 1.5) read as "heavier/cornered".
- **Frame drum (daf) + roll**: 180–1400 Hz bandpassed noise + 95 Hz skin
  tone, 120 ms. Roll = hits at an accelerating rate (9→20 /s) with gain
  ramping 0.3→1.0 — the standard section-launch gesture.
- **Galloping hoofbeats** (kanly — the lone-rider engine): a dry dusty
  thud — fast downward pitch-thump (sine 200→62 Hz, exp rate 55, decay
  ~40/s) + 220–1700 Hz bandpassed "sand kicked up" noise burst at 0.45,
  short ~120 ms, NO reverb (it's on the ground). Two variants (lead/trail
  hoof) with slightly different f0/decay. Pattern on a TRIPLET grid (3
  hits per beat); per-beat gain cells like `[1.0, 0, 0.55]` (DUM·da) and
  `[0.85, 0.5, 0.55]` (DUM da da) alternated across the bar = a canter;
  busier cells `[1.0, 0.6, 0.7]` = a full gallop for the chase. Alternate
  lead/trail hooves L/R per hit (constant-power pan) so the gait itself
  pans — reads unmistakably as a horse crossing open sand, relentless.
- **Sunrise shimmer** (kanly — DAWN warmth, the anti-night gesture): a
  rising swept-noise band (8 fixed bandpass bands 700→3000 Hz,
  triangular time-windows so the center sweeps up = light spreading) plus
  warm partials carrying the **major third F#** (D5/F#5/A5 sines, each
  pulsed to silence via `clip(sin,0,1)**2`). One swell that crests at
  ~14 s and fades by ~28 s — the sun is up, no need to keep shimmering, so
  the anti-tinnitus rule is satisfied by fading within a minute. The major
  third is the tell: every other track lives on the E♭ flat-second
  shadow; F# in the light is the one warm, hopeful color in the palette.
- **Decisive single blow / "the kill"** (kanly — contrast with
  night_pursuit's worm): the human counter to "the desert wins". A
  sub-boom (brown noise → 150 Hz lowpass, 30 ms attack, + falling sub core
  60→30 Hz via cumsum) for the body, under a short metallic **blade ring**
  — 4 inharmonic damped sines (2300/3470/5150/6900 Hz, decay 18–40/s) +
  a 2–8 kHz bandpassed transient, ~30% reverb, gone in <1 s, with a 4 ms
  ITD between L/R so it "cuts across". Then SILENCE: end every rhythmic
  layer's bar range AT the kill bar, so the dead air after the ring is the
  blow landing. Weight the strike so the kill is the loudest section by
  RMS (~0.20 vs a ~0.14 chase) — a deep blow is felt more than peaked, so
  RMS dominance, not sample-peak, is the right target (pushing the boom's
  literal peak higher just steals normalization headroom — the
  fall_of_arrakeen lesson).
- **Tremolo strings**: per chord note, 3 detuned copies (±0.4–0.5 %) of an
  additive saw (harmonics 1–8, 1/k gains), bandpassed 180–2600 Hz, then a
  10–12 Hz tremolo `(0.5+0.5·sin)**1.2` that touches silence every cycle
  (anti-tinnitus compliant). Minor-second voicings (D+E♭) carry the tension.
- **Riser**: white noise crossfaded through ~10 bandpass bands rising
  300 Hz→5.5 kHz (triangular windows along time) + a sine climbing two
  octaves, all under a `t²` amplitude ramp.
- **Storytelling structure** (night_pursuit): build sections on a bar grid
  (`bar_t(bar, beat)` helper, section boundaries as bar constants) and give
  every layer a per-section schedule, so no section repeats verbatim. A
  piecewise-linear `energy(t)` curve (interp over breakpoints) ducks the
  calm layers as intensity rises. Mid-track tonal-center shift for free:
  D Phrygian dominant = mode 5 of G harmonic minor, so re-rooting on G
  (bass/drone on G1, phrases ending on G) darkens the scene with zero new
  pitches. Cut hard into a breakdown (tick + heartbeat only) before the
  final act — contrast is what makes the climax land.
- **Ney flute** (maker_comes): like the duduk voice but nearly pure —
  harmonics 1/0.25/0.08 — plus 13 % of 1.2–4 kHz bandpassed breath noise
  riding the same envelope; faster, shallower vibrato (6 Hz, 0.4 %),
  shorter portamento attacks. Reads as airy/floating vs the duduk's reedy.
- **Sardaukar throat chant**: 14-harmonic glottal source (1/k^0.8 gains)
  through three parallel formant bandpasses — 380–560 (g 1.0), 750–1000
  (0.6), 2200–2700 Hz (0.15) — a dark "oh"; 5.5 Hz guttural amplitude
  pulse and a 0.4-gain sub-octave sine for throat-singing weight. Chant
  register D2–G2; pattern of long+short syllables per bar.
- **Long-form lessons** (maker_comes, 7:20): peak-normalized layers hide
  RMS imbalance — sustained sub (half-note bass, chant) carries far more
  energy than gated 16ths at the same peak, so drop sustained-bass gains
  to ~0.45 or quiet episodes out-weigh the climax (verify with per-section
  RMS, the climax/sprint should be the loudest sections). For 7+ min of
  float64 layers, commit each normalized layer into the mix bus
  immediately (`commit()` + del) instead of keeping all layers alive.
  Keep a long climax alive in 8-bar waves that each add one layer, and use
  a FALSE ENDING (one huge hit, then only wind + the still-counting tick
  for ~1.5 bars, then slam back) before the final sprint.
- **User feedback on night_pursuit**: the sparse stalking section
  (tick + sparse bass alone, 0:30–0:54) read as "strange/odd" — don't
  linger half-engaged; either stay fully ambient or commit to the groove.
  The breakdown bridge and the 2:50 climax were the strongest parts; the
  user wanted the climax material extended into a much longer story
  (hence the_maker_comes). Don't name a local variable `wave` — it
  shadows the stdlib module used for the final write.
- **Trance kick** (water_of_life): sine diving 150→45 Hz (exp, rate 55),
  0.8 ms attack, 25 % noise click, decay 9/s. Four to the floor; builds
  use 8th- then 16th-note kick-roll bars with rising gain.
- **Psy rolling bass**: the K-b-b-b engine — kick on the beat, bass on
  the three 16ths after (gains .8/.7/.95). Band-limited saw (harmonics to
  7 kHz) on D2, lowpassed at 350 Hz, `tanh(2x)` drive, 2 ms gate. The
  350 Hz lowpass + short gate is why this saw does NOT read as trombone.
- **303 acid line**: band-limited saw → butter lowpass at the cutoff +
  `signal.iirpeak(cutoff, Q=7)` added back 1.1–1.5× = the squelch, then
  `tanh(2.2x)`. Accents multiply the cutoff 1.6×; the base cutoff
  breathes over 16-bar sine cycles (or ramps one-way for builds). Cache
  notes keyed (midi, cutoff//75, accent) — per-note filtering is cheap.
- **Offbeat hats**: 7 kHz highpassed noise; open (120 ms, decay 30) on
  every offbeat, closed (45 ms, decay 110) 16th ghosts answering L/R.
- **Psy zap**: sine diving 1980→80 Hz in ~150 ms, 35 Hz ring-mod
  shimmer — punctuates 8-bar phrase boundaries in drops.
- **Trance arrangement notes**: staircase the intro (kick alone → +bass →
  +acid, RMS rising each time) but hold kick/bass gains at 0.65–0.8
  before the first drop or the drop won't step up (the sustained-sub RMS
  lesson again). Tribal layers (maqsum darbuka at ~0.6, war drums on
  phrase downbeats) ride the trance grid for the Juno Reactor fusion.
  Strip the outro layer by layer and let the kick fade like a calming
  heartbeat before the ambient coda.
- **Sharp 303** (sleeper_awakens — feedback on water_of_life: the acid
  sounded "flat"; real acid has sharper edges): the filter must SWEEP
  within every note. Filter the saw twice (bright = cutoff×3, dark =
  cutoff×0.75, both with `iirpeak(Q=11)` fed back 1.4–1.9×) and
  crossfade bright→dark with `exp(-t/0.055)` (accents: 0.10 — deeper,
  slower squelch); then `tanh(2.8x)`. Add SLIDE notes: pitch glides into
  the next note over the back half of the step (`f·(f2/f)^clip(...)`,
  phase via cumsum), dur 1.02×STEP for legato. Cache keyed
  (midi, cutoff//60, accent, slide_to).
- **Psy clap** (sleeper_awakens): four noise bursts 11 ms apart, bp
  900–5200 Hz; first three damped at 120/s, last rings at 26/s. Beats
  2 & 4 through drops, panned slightly L (beat 2) / R (beat 4).
- **Un-muting a groove** (feedback on water_of_life: "muted /
  suppressed"): brighten at every layer, not just the bus — kick click
  bandpassed 1.8–9 kHz at 0.45 (was raw noise 0.25), open hats HP
  6500 Hz decay 24 (longer ring) at commit 0.12 (was 0.08), darbuka tek
  bp up to 10 kHz, add the clap, then a master high-shelf
  (`mix += 0.22·sosfilt(butter(2, 3000, "high"), mix)` ≈ +1.7 dB).
  Verified: HF share (>3.5 kHz) of drop RMS went 4.2 % → 7.0 %.
- **Long drops** (feedback: "the drops are over too quickly"): 64-bar
  drops work if they evolve — change the acid riff/register every
  16 bars and cut 4-bar MINI-DIPS inside the drop (kick+acid only /
  bass+hats+riser / kick+chant only). The dips are what make ~106 s of
  drop feel like a ride instead of a loop; each one is a free re-drop.
- **Room-shake kick** (fall_of_arrakeen; two rounds of feedback — first
  "a beat which shakes the entire room", then "the BASS is still not
  there... a lot deeper and heavier"): a kick STACK plus three more
  levers. (1) The stack: punch (sine 150→44 Hz, rate 55, 0.8 ms attack,
  decay 9/s) + click (bp 1.8–9 kHz, 0.50) + a long SUB TAIL — sine
  55→37 Hz (D1 itself) over 0.42 s ≈ a full beat at 148, env decay 3/s,
  gain 1.15 into the stack. (2) A dedicated **sub-boom layer**: a pure
  50→37 Hz sine under EVERY 4-on-the-floor hit, sustaining the whole
  beat (`exp(-t·1.2)` + a hard release in the last 60 ms so booms never
  overlap/comb), committed as its OWN layer (weight ~0.30) so peak
  normalization can't trade it against the punch. (3) **Sidechain
  pump**: a precomputed gain curve that ducks 55 % at every kick and
  recovers over the beat (`1 − 0.55·exp(-t/0.10)`, floor 0.30), applied
  as `env=` to the bass and drone — the kick owns the sub alone, and
  the pumping is itself the wall-shake feel. (4) Master low shelves:
  `mix += 0.34·sosfilt(butter(2, 95, "low"), mix)` PLUS
  `0.30·butter(2, 55)` (~+5 dB below 55 Hz). Kick commit 0.50.
  Verified v1→v2: drop sub-60 Hz RMS 0.14→0.28 (double), per-beat sub
  pump ratio held at ~5× (deeper, not muddier).
- **Normalization-headroom theft** (fall_of_arrakeen v1 bug): transient
  stacks in builds (kick rolls + snare rolls + frame roll + riser
  peaking together) out-peaked the drops 0.86 vs 0.65 — and since the
  final mix is peak-normalized, one build instant stole headroom from
  the whole track. Fix: scale roll gains so builds peak BELOW the drop
  (×0.85), and add a gentle tanh bus limiter after the shelves:
  `tanh(1.35·mix/peak)/tanh(1.35)·0.88` — transients can't dominate the
  normalization and the slight saturation is the psy-master "glue".
- **War-track instruments** (fall_of_arrakeen): *field snare* = tone
  pair 185+330 Hz + bp 1.5–9 kHz noise; accents preceded by two-ghost
  buzz drags (-60/-30 ms); buzz-roll crescendos every 4th bar — a march
  pattern strong enough to be a section's identity. *War horn*
  (carnyx): 12 harmonics (1/k^0.7), pitch scoop 0.94→1.0 over 150 ms,
  31 Hz growl AM, + 0.6× of a 450–900 Hz formant bandpass. *Battle
  toms*: three pitches 165/110/80 Hz, pitch +40 % at attack, 300–1500 Hz
  skin noise; syncopated 2-bar pattern, descending 8-hit fill every 8th
  bar. *Shaker*: bp 3.5–9.5 kHz, 16ths with gain cycle [.9,.4,.65,.4].
  *Reverse cymbal*: HP 6 kHz noise with exp decay, time-flipped, placed
  so it ENDS exactly on the drop boundary.
- **Aftermath/death scenes** must be QUIETER than the intro (verify:
  per-section RMS, aftermath < march): duck the calm curve again after
  the death blow (×0.70-0.78), keep heartbeat/sinking-drone weights
  ≤0.09. Decelerating heartbeat: thump pairs with `gap ×= 1.085` until
  gap > 2.6 s (the heart stops). Sinking drone: pitch sags 6 % over the
  last half-minute + a faint flat-second partial (2^(1/12), 0.22 gain)
  — "the agony".
- **Seamless loop** (arrakis_winds_v3 — game background track): render
  `DURATION + XF` seconds (XF = 10 s), then equal-power-fold the tail
  into the head: `y[:nxf] = sin(½πu)·x[:nxf] + cos(½πu)·x[N:N+nxf]` —
  at u=0, y[0] = x[N], i.e. the loop's first sample continues EXACTLY
  where its last sample (x[N-1]) left off, and event/reverb tails that
  spill past N land in the head of the next pass. No fade-in/out.
  Schedule discrete events in `[XF+10, DURATION-12]` so none straddles
  the fold. Verified: end→start sample jump 1.3× the mean wind-noise
  step (inaudible), seam RMS match within 9 %. Caveat: mp3 encoder
  padding breaks gaplessness — ship WAV/OGG to the game engine.
- **Background-ambience pacing** (arrakis_winds_v3): for a loop meant to
  play for hours, keep per-minute RMS flat (0.15–0.18 here) and give
  each minute ONE small event; rotate three interest families (nature /
  human traces / menace) so no family repeats back-to-back. "Menace"
  reads best as pattern, not timbre: eight sub pulses spaced exactly
  0.9 s apart — too regular to be natural — is scarier than any horn.
- **Musical seamless loop** (spice_must_flow): when a loop has a beat
  grid, make `DURATION` an exact number of bars and the fold length an
  exact number of bars (2 here) — the tail being folded into the head is
  then IN PHASE with the head's groove, so the crossfade blends two
  copies of the same groove instead of smearing the beat. Pattern
  schedules indexed by bar (`(b // 8) % 2`) and gain waves
  (`sin(2π·b/24)`) must use periods that divide the bar count.
- **Harvester machine chug** (spice_must_flow): two band-limited squares
  (odd harmonics 1,3,5,7) on D2, detuned ×1.006 for ~0.4 Hz beating,
  lowpassed 420 Hz, then an 8th-note amplitude gate with pattern
  [1,.45,.72,.45,.88,.45,.72,.45] and an **idle floor of 0.18** (an
  engine never fully stops), `tanh(1.5x)` warmth. Soft footfalls (sine
  80→45 Hz, 20 ms attack — soft, this is work not war) on beats 1 & 3.
- **The listen-pause** (spice_must_flow — arrangement as storytelling):
  a precomputed `listen` envelope multiplied into every HUMAN layer
  (machine, clanks, thumps, santur) cuts to zero in 0.35 s shortly after
  a worm rumble starts, holds two bars, recovers over 1.8 s with a
  raised cosine. Nature layers (wind, drone, rumble) ignore it. A loop
  can't build to a drop (game logic may never deliver one) — sudden
  silence is the loop-safe substitute for tension.
- **Hammered santur** (spice_must_flow): struck Karplus-Strong — two
  strings per course at ±0.15 %, excitation smoothed by only a 2-tap
  average (hammer brightness vs the oud's 5-tap warm pick), damp 0.997,
  env `exp(-1.6t)`. Cache one note per pitch, place via `add_at`.
- **Thopter flyby** (spice_must_flow): descending detuned 5-sine cluster
  (300→170 Hz exp) with wing-flutter AM whose rate itself decelerates
  23→13 Hz via cumsum — reads unmistakably as ornithopter, friendly at
  low gain/slow descent, hostile at fast.
- **Tension loop = no builds** (stillsuit — the enemy-sighted state):
  a game-state loop can never build, because a build promises a drop
  that game logic may never deliver. Every variation must WANDER
  (`slow_noise` gain drift, here ±8 % on bass, 0.25–1.0 on strings) or
  cycle — never ramp. Verify with per-15s RMS: the linear trend should
  be ≈0. Tension carriers that work without building: a constant
  bone-dry tick (the night_pursuit clock at fixed gain — the one thing
  that never changes), an unresolved flat second that swells and fades
  WITHOUT resolving to the root, and the held minor-second string bed.
- **Stillsuit breathing** (stillsuit): mask-breath as a rhythm layer —
  bandpassed noise, bright inhale (500–1600 Hz, gaussian env on beats
  1–2) and darker exhale (250–900 Hz, beats 3–4), one cycle per bar.
  Pick the bar length so the breath rate is slightly too fast
  (24/min here) — subliminal unease. Keep it dry and centered: it is
  inside the player's own hood, not out in the room. Built from
  `np.mod(t, BAR)` phase, so it is loop-periodic for free.
- **Shepard wind** (sandstorm_coriolis): K whistle voices at spectral
  position `p = (t/T_trav + k/K) mod 1`, frequency `f_lo·2^(p·octaves)`,
  each a sine (+0.2 second harmonic) under random FM (1.8 % slow wander
  + 0.5 % fast jitter ≈ narrowband noise = wind whistle), loudness
  window `sin(πp)²` so voices are silent at both spectral edges — the
  wrap discontinuity is inaudible and the rise never arrives. Per-voice
  circular pan (`sin(2πt/T_rot + 2πk/K)`) = storm rotation. For a
  seamless loop make DURATION an integer multiple of T_trav and T_rot.
- **Overlay design rules** (sandstorm_coriolis — the engine fades it
  over ANY playing state track): no melody, no discrete events, no
  fade-in/out of its own, and only a faint root-note pedal as tonal
  content so it stays in tune with everything. **No lulls**: independent
  gust/flutter wanders occasionally align low, so floors alone don't
  guarantee it — add a slow AGC on the bus (zero-phase 0.5 Hz envelope
  via `sosfiltfilt`, gain = median(env)/env clipped 0.75–1.6x). It
  levels 1-s RMS (verify min/mean ≥ 0.8) while leaving 8–14 Hz flutter
  intact, because the follower is far below the flutter band.
- **Sung vowel voice / duet leads** (sihaya — the album's "vocalists"):
  the chant glottal source made melodic — `glide_curve` portamento at
  70 ms, vibrato blooming over 0.8 s (male 5 Hz/0.5 %, female 5.8 Hz/
  0.35 %) — sung through the litany vowel table (i/e/a/o/u f1+f2) as
  `iirpeak(Q=8)` pairs (f2 at 0.7 gain), one vowel PER NOTE crossfaded
  over 90 ms (a singer moving through a word, not a filter switch), each
  vowel's filtered signal RMS-equalized. Add a lowpassed chest layer
  (butter 750·scale on the raw source) or the fundamental vanishes under
  the resonances. Soft 'h' onset = the first vowel's formants on noise
  decaying at 25/s. Hum variant: all-"u", lp 1400, more chest. FEMALE =
  same engine one octave up, formants ×1.18, softer source (1/k^1.2),
  10 % breath (bp 2–5 kHz riding the env), lp 4800 vs male 3400. Keep
  leads fairly dry (wet 0.22) and panned ±0.12 — a close duet, not a
  hall. Caveat (user feedback): vowels-only works but reads as an
  invented language — fine for Fremen; real lyrics are the next step
  (see `more_ideas.md` C7).
- **Song form / question-and-answer** (sihaya — the fix for "short
  sections that lack coherence"): what made one track read as ONE song.
  (1) A per-bar `CHORD_MAP` for the whole track — one progression
  family, every layer reads its harmony from the same list. (2) Q/A at
  three levels: antecedent phrases end off-tonic, consequents resolve to
  D with the SAME rhythm; an instrument echoes every vocal tail,
  entering ON the singer's held final note (this is also what stitches
  phrases — no dead air); dark verses ask, the major-D chorus answers.
  (3) Repetition is the point: the hook sung 18×, refrain vowels
  identical every time (= "same words"), verses same tune / different
  vowel-words. (4) Every section boundary crossed by a pickup note, a
  ringing chord, or a fill — print a seam checklist plus per-section RMS
  and CHECK the ordering (verse < pre-chorus < chorus1 < chorus2 <
  chorus4 loudest; a pre-chorus louder than its chorus reads as a
  letdown — the rise vocals/strings needed ×0.7). (5) The pop
  silence-drop: one beat of near-silence before the final chorus with
  only a lone vocal pickup hanging in it — a composed event, not a seam.
  (6) The bridge strips ONE layer per bar (never all at once) and avoids
  the tonic chord so the final chorus lands as arrival.
- **Anti-tinnitus rule** (learned from arrakis v1): any sustained
  high-frequency tonal element MUST either pulse to true silence
  (`np.clip(sin,0,1)**2` envelopes, not `0.5+0.5·sin`) or fade out entirely
  within ~1 minute. Constant high tones fatigue the listener.

## Cross-track blending

`base_under_attack` opens with the **identical wind + drone code** as
`generate_arrakis.py` so the two tracks crossfade cleanly (arrakis ends with
an 18 s fade-out, attack opens with a 12 s fade-in, both on the same D root
and palette). When writing a sequel track, copy the opening layer code of the
predecessor verbatim and keep the same key (D) and mode (Phrygian dominant).

## Conventions

- **One script per track**, named `generate_<track>.py`, standalone
  (duplicate helpers; no shared module).
- **Revisions get a new WAV name** (`_v2`, …) — never overwrite a WAV the
  user has listened to. Update the script in place and change `OUT`.
- Print event times (rumbles, explosions, beat range) at the end of every
  script so the structure is verifiable without listening.
- **Scripts live in `/repos/dune/music` (tracked in git); generated WAVs go
  to `/workspace/music/` and are never committed** (~30 MB each). Every
  script sets `OUT_DIR = "/workspace/music"` and `os.makedirs(..., exist_ok=True)`.
- Stage new/changed scripts and docs with git but **do not commit or push
  without being asked**.
