# The instrument catalog — trance/

Every synth voice, drum and texture recipe that exists in the trance
generators, indexed so a new track can *pick* instruments without
re-reading every script. The catalog is documentation only — the code
convention stays **copy, don't import** (standalone scripts, duplicated
helpers, per `../CLAUDE.md`). The definitive source for each entry is
the named `script:function`; deep parameter recipes for the signature
instruments live in `../CLAUDE.md` ("Synthesis recipes") and are not
duplicated here.

## Rules of reuse

1. **Copy the function, keep the name** if unchanged; note the source
   script in a comment when re-voicing.
2. **The warmth recipe applies to every port** (`../CLAUDE.md`): rolled
   partials `1/k**1.3`, sine body, rounded attack, low lowpass, soft
   drive. Every harsh-sound complaint has been the same bug.
3. **Identity separation**: some sounds are a track's *signature*
   (marked "owned by" below). Reusing one is a deliberate, declared
   choice in the new track's notes doc — never default drift. Several
   scripts ban each other's signatures by construction.
4. Caches: pitched voices cache per `(midi, dur)` or per cutoff bucket
   — keep the cache when porting, renders are 10–50× faster.

## Drums & percussion

| instrument | source | character / use |
|---|---|---|
| 909 kick | every 4/4 script, `make_kick` (identical family) | falling sine 48+102·e^(−50t) + bandpassed click; punchy, NOT sub-heavy |
| closed hat (16th grid) | `lost_v6.py:make_hat` et al. | 7 kHz HP noise, 45 ms; the machine carpet. **Absent by design in eisgang** |
| open hat | same, `make_hat(open_=True)` | 120 ms; the offbeat "tss" |
| clap | `make_clap` everywhere | 900–4500 BP, 4 micro-delayed bursts; beats 2 & 4 |
| ride | `lost_v6.py:make_ride` et al. | two BP layers + 5.4 kHz ping; climax sections only, era discipline |
| shaker | `nachtkind_v3.py:make_shaker` | quiet motion layer |
| crash | `make_crash` everywhere | 5 kHz HP, 2 s; marks arrivals |
| snare | `adrift/farlight_v2/penumbra/lost_v6:make_snare` | exists for the ROLL (see builds) |
| 909 toms | `ungeschrieben.py:make_tom`, `eisgang.py` | falling sine + skin burst; **fills only**, ≤3 per track |
| gated 80s slam | `tech_noir_v3.py:make_slam` — owned by tech_noir | gate baked into the sample (cut dead at 140 ms); punctuation, never a groove |
| anvil | `tech_noir_v3.py:make_anvil` — owned by tech_noir | 6 inharmonic partials on 410 Hz + strike, big dark plate |
| tap | `tech_noir_v3.py:make_tap` | metallic 1280 Hz inharmonic tick |
| tick pair | `eisgang.py:make_tick` — owned by eisgang | rim/woodblock clicks (2.5/1.8 kHz, +3.4 kHz descant), hard-panned; the no-carpet top end |
| the stamp + boot | `eisgang.py` (STAMP_K, BOOT) — owned by eisgang | shortened-kick double on 4& + 85 Hz tom under it |
| heartbeat | `lost_v6.py:heart` | 32→68 Hz double thump; breaks only (the audible-heartbeat feedback) |
| reverse cymbal | `nachtkind_v3.py` (RCYM) — owned by nachtkind | crash flipped, swell ENDS on the bar line |
| psy kick | `maschinenherz.py:make_kick` (dune water_of_life lift; also silver_wire) | 150→45 Hz dive; harder/faster than the 909 kick; the psy house floor |
| psy clap | `maschinenherz.py:make_clap` (also silver_wire) | beats 2&4; tighter and brighter than the Frankfurt clap |
| psy zap | `maschinenherz.py:make_zap` (also silver_wire) | 8-bar phrase punctuation inside drops |

## Basses

| instrument | source | character / use |
|---|---|---|
| rolling 16th mono bass | `lost_v6.py:bass_note` (warmed lineage: lost_v4; variants in nachtkind_v3, ungeschrieben, unsung, farlight_v2, penumbra) | THE house bass: rolled-off saw stack, `iirpeak` Q 1.2 blend 0.3, half-freq sine sub, tanh 0.9; continuous 16ths on a pedal with octave jumps. Per-section cutoff tables |
| tide pulse bass | `adrift.py:bass_note` | the rolling bass retired: quarter/8th-note pulse instead (dream-era gait) |
| machine bass | `tech_noir_v3.py:bass_hit` — owned by tech_noir | the dry forward "DUN-dun" on the 13/16 grid |
| sustained sub | `farlight_v2.py`/`penumbra.py` (in-line) | 41 Hz sine under choruses; **must BLOOM** (0.25 s attack, per-bar entry ramp) — the v1 slam lesson |
| thud-bass (run-and-plant) | `eisgang.py:thud_bass` — owned by eisgang | percussive anti-rolling bass: sine + octave + 150–800 Hz knock, no saw; bounce–plant–REST, duty ≤ 0.6 |
| psy rolling bass | `maschinenherz.py:psy_bass_note` (also silver_wire) | K-b-b-b engine: kick on the beat, bass on 3 16ths after (gains .8/.7/.95); saw stack LP 350 Hz, short gate; NEVER on a kick 16th (the gap IS the rest — duty printed and checked) |
| sub-duty bass | `silver_wire_v2.py:sub_note` | pure sine + 0.3×2nd harmonic; drop-mode replacement when the 303 low register owns the mid-bass; no saw, no lowpass |
| ~~lost_v3 bass~~ | `lost_v3.py` | the harsh pre-warmth bass, kept only as the A/B reference — do not reuse |

## Leads

| instrument | source | character / use |
|---|---|---|
| warm detuned saw lead | `lost_v6.py:lead_phrase` (variants: adrift, farlight_v2, unsung) | THE warm lead: 3 saws det ±0.4 %, `1/k**1.3`, sine sub 0.3, LP 2600–2800; the refrain/duet voice |
| reed lead + ping-pong | `nachtkind_v3.py:lead_phrase` (inner `reed()`) | the soaring duet-over-piano voice, dotted-8th ping-pong delay, octave shimmer |
| Oberheim brass | `tech_noir_v3.py:brass_phrase` — owned by tech_noir | reciprocally detuned reed pair, pitch scoop, bloom vibrato, LP 1600 |
| love theme voice | `tech_noir_v3.py:love_phrase` | the warm answer/contour voice of the machine score |
| GATED lead | `penumbra.py:lead_bar` — owned by penumbra | the 16th trance gate (58 % duty, raised-cosine edges) BAKED into per-bar renders, cutoff-bucket cached; square-saw odd-weighted core |
| ungated free lead | `penumbra.py:lead_free` | the same voice singing free (breakdown only) |
| ~~hollow pulse lead~~ | `eisgang.py:lead_line` (v1) | odd-harmonics glide; **retired as a foreground voice** — read as a toy xylophone up high (listen verdict). Survives only as the underglow |
| ~~skyline piano~~ | `eisgang_v2.py:piano_note` (v2) | the de-gothed M1 piano; **also retired as a refrain voice** — still "pling-plong". THE LESSON (two strikes): percussive decaying attacks read as toys when they carry the tune; refrain voices need sustain + slow attack. Percussive = texture (stabs), not melody |
| skyline lead | `eisgang_v3.py:skyline_note` — owned by eisgang | the warm-lead family dialed darker + SUSTAINED: LP 2200, `1/k**1.35`, sine body, bloom attack scaled to note length, full sustain, bloom vibrato; the chorus refrain voice |
| the underglow | `eisgang_v3.py` (lead_line, −12, LP 1600, quiet) | the D-50 trick: a dark sustain bed under the refrain voice; carries held notes across the held V |
| the signal | `adrift.py:make_signal` — owned by adrift | glide-whistle call (B5→F#5) on a long dotted-8th feedback trail; an FX-lead, once per chorus |
| warmed 303 acid | `maschinenherz.py:acid_note` | psy-house base: rolled `1/k^1.3`, Q 4.5, fb 1.15/1.2, tanh(1.2), 0.30 sine body, within-note bright→dark sweep; cutoff from printable arc, never parked |
| silver wire lead 303 | `silver_wire_v2.py:acid_note` + `build_half` melody constructor — owned by silver_wire | one notch sharper: Q 6, fb 1.3/1.35, tanh(1.5); 16-bar refrain constructed from Q_STEPS/A_STEPS winding cells, every-3rd accent roll, anti-arc CUT_PROFILE |
| register-jump answers | `silver_wire_v2.py` — owned by silver_wire | the 303 answering itself an octave below; full-bar mini-runs in the acid grammar under the two refrain landmarks; both registers land A together |
| love-voice port | `maschinenherz.py:voice_phrase` (tech_noir `love_phrase` re-voiced) | sine + 3 rolled harmonics, 5.2 Hz late vibrato, LP 3000, long hall wet ~0.5; new melodies only — the Terminator tune is never quoted. Original owned by tech_noir; this borrow declared in maschinenherz_notes.md |

## Keys & bells

| instrument | source | character / use |
|---|---|---|
| M1 gothic piano | `nachtkind_v3.py:piano_note` (also lost_v6) | stretched-inharmonic partials, two detuned strings, hammer thunk; stately, very wet, a centerpiece |
| dirty dream piano | `adrift.py:piano_note` — owned by adrift | the M1 piano + sampler dirt: ×3 zero-order hold, 0.3 Hz wow, tanh; the 1996 dream-trance keys |
| bell | `farlight_v2.py:bell_note` — owned by farlight | partials 1/2/2.76/5.40 rolled off hard, mallet thunk, detuned shimmer pair; glassy but ROUND |
| answer bell | `penumbra.py:bell_note` | the tease/answer voice (one answered hang per statement) |

## Plucks, sequences & stabs

| instrument | source | character / use |
|---|---|---|
| glassy pluck arp | `lost_v6.py:pluck` (variants: adrift, farlight_v2) | the verse Q/A arpeggio voice, STEP×3 decay |
| resonant era sequence | `ungeschrieben.py:seq_pluck` — owned by ungeschrieben | Q 2.2 / blend 0.40 — THE sanctioned resonance exception, guardrailed (tanh 0.8, sine sub, cutoff always sweeping); cutoff-bucket cached against a printable filter arc |
| dark gated chord stab | `nachtkind_v3.py:make_stab` (re-voiced: `unsung.py:make_stab`, `penumbra.py:stab`) | band-limited saw triad, LP 900, gated ~50 ms, offbeat, panned alternately; the additive-layer element |
| hammer stab | `eisgang.py:stab_hit` — owned by eisgang | hollow pulse pluck, gated 16th retrigger with a per-16th gain cell (chatters, never carpets); dry and close |

## Pads, strings & choir

| instrument | source | character / use |
|---|---|---|
| dark sine pad | `pad_chord` in every script (params differ) | sine + 0.3·2nd harmonic, slow AM per voice, LP 750–900; the breakdown bed |
| Juno pad oscillation | `penumbra.py:pad_chord` | the harmony carrier of the static-modal track (the "light") |
| rompler strings | `ungeschrieben.py:strings_line/strings_chord` — owned by ungeschrieben | M1/D-50 sampled-strings: bow-noise layer, fast attack, 5.8 Hz sample-loop flutter; the reveal centerpiece |
| breath choir | `adrift.py:choir_voice` — owned by adrift | wordless choir: 3 drifting detuned voices, formants 650/1080 Q 5, chest+vowel blend, 8 % breath |
| cello | `lost_v6.py:cello_line` | solo bowed line, LP 1900; the octave-below duet partner |

## The voice (TTS)

| instrument | source | character / use |
|---|---|---|
| spoken-word drop | `ungeschrieben.py:get_voice` | edge-tts, cache-first to `/workspace/music/samples/`, sampler pitch-down ×0.94, dropped ONCE, `VOICE_GAIN` knob documented in-script |
| hybrid sung voice | `unsung.py:hybrid_note` etc. | consonant-graft + formant vowel at perfect pitch — **recorded DEAD END** (pitch-perfect but uncanny); don't rebuild without a genuinely new naturalness idea |

## Textures, builds & seam devices

| device | source | character / use |
|---|---|---|
| snare roll + dark swell | `adrift/farlight_v2/penumbra/lost_v6:roll` + `swell` (also silver_wire builds) | the era build pair: 16th→32nd roll under a 250–2400 Hz bandlimited swell (never white noise) |
| noise riser | `lost_v6.py:riser` | lost's own; banned by construction in the era-strict tracks |
| cloud | `adrift.py:cloud` — owned by adrift | symmetric bandpassed wash that *passes by* (sin² envelope) — a non-riser |
| air bed | `ungeschrieben.py`/`eisgang.py` (in-line "air") | 150–1100 Hz breathing noise at the track's edges (and eisgang's freeze) |
| tom fill | `ungeschrieben.py:tom_fill`, `eisgang.py` | the era seam; ≤3 per track |
| the silent beat | `farlight_v2/lost_v6/nachtkind_v3/unsung:silent_beat` (also maschinenherz / silver_wire builds) | the one composed drop-beat before a slam/final chorus |
| tide out / return | `adrift.py:tide_out` — owned by adrift | kick+bass exit under a still-ringing melody; the return lands mid-phrase |
| filter arc | `ungeschrieben.py`/`penumbra.py:cutoff_at` | development as a printable piecewise-linear cutoff curve, checked at boundaries |
| harmonic odometer / cell map / duty check | `eisgang.py` (verify block) | form checks for walking harmony, two-bar cells, and non-rolling bass |
| shiver stack (W1) | `maschinenherz.py:shiver_stab` — owned by maschinenherz | additive dissonance intro: one stab voice per 4 bars, layering DISSONANCE (octave → 2nd-clash → tritone → leading tone), first consonant chord lands with the kick |
| ice-crack seam (W8a) | `maschinenherz.py:ice_crack` — owned by maschinenherz | stab—silence—upward flick; the psy glitch transition (not tom fills, not reverse cymbals) |
| stutter ladder (W4a) | `maschinenherz.py:ladder_bars` — owned by maschinenherz | 303 locks one pitch per bar in 16th retrigger, climbing chromatically out of key into the drop; build 1 parks on dominant, build 2 ends on leading tone |
| zigzag arp (W2) | `maschinenherz.py:arp_bars` — owned by maschinenherz | chorus arp cell formula: root–oct–oct–5th / 5th–♭3–♭3–root, restated up chord tones; glassy pluck voice |
| anti-arc CUT_PROFILE | `silver_wire_v2.py` (CUT_PROFILE + `place_events`) | 16-entry per-bar cutoff multiplier, identical every statement; spread ~0 Hz, trend slope ~zero (both printed); the anti-arc device |

## Per-track signature summary (identity separation at a glance)

- **tech_noir** — anvil, slam, tap, machine bass, 13/16 limp, brass
- **nachtkind** — gothic piano, reverse cymbal, reed+ping-pong, F# color
- **lost** — warm five (lead/pluck/pads/piano/cello), heartbeat, rotation lights
- **ungeschrieben** — rompler strings, resonant sequence + filter arc, spoken drop, 909 tom fills
- **unsung** — the hybrid sung voice (dead end, reference only)
- **adrift** — dirty dream piano, breath choir, the signal, clouds, tide form
- **farlight** — the bell, the re-light (minor→major), sustained bloom-sub
- **penumbra** — the 16th gated lead, static-modal Juno pads, single-wave arc
- **eisgang** — thud-bass (run-and-plant — the listen verdict's keeper),
  tick pair, the stamp, hammer stab, skyline lead + underglow, walking
  circle-of-fifths harmony, ladder/sigh refrain development
- **maschinenherz** — warmed 303 acid + printable filter arc, psy kit
  (kick/clap/zap), K-b-b-b rolling bass, love-voice port (declared
  borrow), shiver stack (W1), stutter ladder (W4a), zigzag arp (W2),
  ice-crack seam (W8a), D# leading-tone color, dry-engine/wet-heart split
- **silver_wire** — silver wire lead 303 (acid melody grammar + anti-arc
  CUT_PROFILE), register-jump low answers, K-b-b-b / sub-duty bass split,
  psy/straight kit split, G# borrowed color, no break (composed trough)
