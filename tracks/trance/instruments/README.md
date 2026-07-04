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

## Basses

| instrument | source | character / use |
|---|---|---|
| rolling 16th mono bass | `lost_v6.py:bass_note` (warmed lineage: lost_v4; variants in nachtkind_v3, ungeschrieben, unsung, farlight_v2, penumbra) | THE house bass: rolled-off saw stack, `iirpeak` Q 1.2 blend 0.3, half-freq sine sub, tanh 0.9; continuous 16ths on a pedal with octave jumps. Per-section cutoff tables |
| tide pulse bass | `adrift.py:bass_note` | the rolling bass retired: quarter/8th-note pulse instead (dream-era gait) |
| machine bass | `tech_noir_v3.py:bass_hit` — owned by tech_noir | the dry forward "DUN-dun" on the 13/16 grid |
| sustained sub | `farlight_v2.py`/`penumbra.py` (in-line) | 41 Hz sine under choruses; **must BLOOM** (0.25 s attack, per-bar entry ramp) — the v1 slam lesson |
| thud-bass (run-and-plant) | `eisgang.py:thud_bass` — owned by eisgang | percussive anti-rolling bass: sine + octave + 150–800 Hz knock, no saw; bounce–plant–REST, duty ≤ 0.6 |
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
| ~~hollow pulse lead~~ | `eisgang.py:lead_line` (v1) | odd-harmonics glide; **retired as a foreground voice** — read as a toy xylophone up high (the v1 listen verdict). Survives only as eisgang_v2's underglow |
| skyline piano | `eisgang_v2.py:piano_note` — owned by eisgang | the M1 piano de-gothed (hammer 0.14 @ 1200–3600, LP 5000, mid register, LH octaves); the chorus refrain voice |
| the underglow | `eisgang_v2.py` (lead_line, −12, LP 1600, quiet) | the D-50 trick: a dark sustain layer under the piano's attack; carries held notes piano decay can't |
| the signal | `adrift.py:make_signal` — owned by adrift | glide-whistle call (B5→F#5) on a long dotted-8th feedback trail; an FX-lead, once per chorus |

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
| snare roll + dark swell | `adrift/farlight_v2/penumbra/lost_v6:roll` + `swell` | the era build pair: 16th→32nd roll under a 250–2400 Hz bandlimited swell (never white noise) |
| noise riser | `lost_v6.py:riser` | lost's own; banned by construction in the era-strict tracks |
| cloud | `adrift.py:cloud` — owned by adrift | symmetric bandpassed wash that *passes by* (sin² envelope) — a non-riser |
| air bed | `ungeschrieben.py`/`eisgang.py` (in-line "air") | 150–1100 Hz breathing noise at the track's edges (and eisgang's freeze) |
| tom fill | `ungeschrieben.py:tom_fill`, `eisgang.py` | the era seam; ≤3 per track |
| the silent beat | `farlight_v2/lost_v6/nachtkind_v3/unsung:silent_beat` | the one composed drop-beat before a slam/final chorus |
| tide out / return | `adrift.py:tide_out` — owned by adrift | kick+bass exit under a still-ringing melody; the return lands mid-phrase |
| filter arc | `ungeschrieben.py`/`penumbra.py:cutoff_at` | development as a printable piecewise-linear cutoff curve, checked at boundaries |
| harmonic odometer / cell map / duty check | `eisgang.py` (verify block) | form checks for walking harmony, two-bar cells, and non-rolling bass |

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
  tick pair, the stamp, hammer stab, skyline piano + underglow, walking
  circle-of-fifths harmony, ladder/sigh refrain development
