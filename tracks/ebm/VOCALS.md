# VOCALS.md — the voice question for tracks/ebm

**Decision (2026-09-05, user): the instrumental-only rule is suspended
for this directory.** Not for the repo — for EBM specifically, and for
one reason: this is a vocal genre. Ronan Harris IS VNV Nation and
Stephan Groth IS Apoptygma Berzerk; the synths are the frame around a
person saying something. `../../inspiration/EBM_1990s.md` §0 already
says it in the genre DNA ("one organic element: the human voice —
everything else is synthetic"), and §8 then works around it. The
workaround held for *Reliquary* because an interlude has no vocal slot
to leave empty. It will not hold for a song: the 122 slam archetype
without a voice is a backing track.

Nothing here is built yet. This is the plan for the next track.

## What is already ruled out — do not retry

**TTS, in both flavours.** Recorded twice, in `../trance`:

- `unsung.py` — the hybrid graft (TTS consonants onto synthesized
  formant vowels at exact pitch). Measured pitch-perfect to 3 cents and
  still **sounds strange**. Dead end.
- `ungeschrieben.py` — a single edge-tts spoken-word drop, pitched down
  ×0.94. Shipped, but as one gesture, not a sung line.

The failure was never pitch. It was timbre and prosody — the uncanny
valley of a machine pretending. That is the thing a real voice does not
have to solve.

## The proposal: the user's own voice

The right answer, and the genre-authentic one. It also does not break
the repo's "everything synthesized, no samples" rule in spirit: that
rule is about instrument samples, drum hits and borrowed loops. Every
record in `Apop_Soli_Deo_Gloria.md` is 100 % synthesized instruments
plus one human being. Keeping the instruments synthetic and singing the
top line is exactly the arrangement the blueprint describes.

**The container has no audio input.** Recording happens on the user's
own machine (phone, laptop, DAW — anything); the file is dropped into
`/workspace/music/vocals/` and read from there.

### What makes this tractable

The dark vocabulary landed on in `reliquary_v2.py` is **much easier to
sing than a trance hook**: chant-like recitation on a repeated tonic,
descending, small steps, no leap above a 4th, in a comfortable baritone.
That is a spoken-adjacent delivery — closer to Harris than to a soaring
melody, and forgiving of an untrained voice. The genre also expects
heavy treatment, so the bar is character, not polish.

### Recording notes (for when we do it)

- **A guide track is the first deliverable.** The melody already exists
  as a table in the script (`HOOK` / `TAG`), so a script can render
  click + the lead playing the line + a bar count, for singing along.
  Build that before asking for a take.
- Close mic, dry, no processing, no reverb — all treatment happens
  here. A wardrobe full of clothes is a real vocal booth.
- **Sing it twice** (or four times). Real double-tracking beats every
  synthetic doubler; it is also how these records were made.
- Keep the takes; a comp is cheap and the alternates are useful.

## What we do to the voice

In descending order of how much it actually matters:

1. **The era treatment chain — most of the sound.** This is what turns
   a dry bedroom take into the record: the EPS `dirt()` (13-bit,
   `hold=2`) that every instrument here already uses, a lowpass, the
   hardware-sampler pitch-down character, light `tanh`, a plate, a
   tempo-synced dotted-8th delay on phrase tails, and the doubling.
   Groth and Harris are both drenched; a naked vocal would sound
   wrong.
2. **Tuning.** `librosa.pyin` measures f0 per syllable; the script
   already knows the target pitch of every note, so correction is a
   known-source-to-known-target nudge. Small corrections (< ~100 cents)
   preserve naturalness — that is what real pitch correction does.
   `unsung.py` has usable f0-estimation and resampling machinery to
   crib from.
3. **Doubling and harmony.** A detuned copy, an octave-below or
   fifth-above generated from the take (VNV's baritone frequently sits
   under an octave double), the second real take where one exists.
   Taken to its limit this is the Enya method — one voice stacked
   hundreds of times into a choir, then a cathedral hall: parked in
   `../../inspiration/Enya_vocal_stack.md` for a later track.
4. **Vocoder / talkbox** (optional). The voice as modulator against a
   Juno carrier. Genre-legitimate, more futurepop than 1993, and a
   useful middle path if the user would rather not be exposed —
   intelligibility without the naked voice.

## Tooling — installed and verified 2026-09-05

Installed with `pip install --break-system-packages`: **pyworld** 0.3.5,
**praat-parselmouth** 0.4.7, **pyloudnorm**, **noisereduce**. Alongside
what was already here: `librosa` 0.11 (`pyin`, `effects.pitch_shift`),
`soundfile`, `pydub`, `scipy`, `ffmpeg`, `demucs`.

**pyworld is the workhorse.** It decomposes a voice into three
independent parts — `harvest` (f0 contour), `cheaptrick` (spectral
envelope, i.e. the formants and the timbre), `d4c` (aperiodicity, the
breath) — lets you modify each on its own, and resynthesizes. Pitch,
formants and breathiness become separate knobs. That is exactly the
"modulate and tune it up" question, and it removes the earlier warning
about small shifts.

Verified on a **real sung human voice** (demucs-separated from the Black
Box track, 12 s), not on a synthetic test tone. Demos to listen to are
in `/workspace/music/vocaltest/`, numbered:

| finding | measured |
|---|---|
| analysis + resynthesis round trip | 2.79 dB mean mel-spectrogram distance. Phase is **not** preserved, so a waveform diff is meaningless — judge by ear on `01` |
| pitch +5 semitones, formants intact | pitch moved +4.77 st, F1/F2/F3 stayed within 1 % (`03` vs the naive `02` and the deliberate chipmunk `04`) |
| formant shift alone, pitch untouched | `warp(sp, r)` multiplies formant frequencies by **r**, measured in the envelope domain: 0.85 → 0.86, 1.15 → 1.14, 1.335 → 1.32. **r < 1 = deeper, bigger body; r > 1 = smaller, thinner** (`05`, `06`) |
| octave down, formants kept | `08`; and `09` = octave down with formants also down 8 % for a fuller body. **This is the "can I sound like a baritone" test** |
| autotune to A natural minor | median correction 40 cents, max 100 (`07`) |
| analysis cost | 4.3 s of CPU for 12 s of audio, once per take, cacheable |

**f0 trackers**, same 12 s, medians agreeing within 7 Hz (238–245 Hz):
Praat is effectively instant, `pyin` took 2.3 s, WORLD's `harvest` 4.3 s
(and calls the most frames voiced, 81 % vs 63–66 %). Use Praat for
analysis and range-finding; WORLD's own f0 for anything being
resynthesized.

**pyloudnorm** is useful beyond vocals, as a master guardrail:
`reliquary.wav` measures −14.2 LUFS and `reliquary_v3.3.wav` −14.9,
both close to the streaming target of about −14.

**noisereduce did not earn its place.** On the test signal it made SNR
*worse* in every mode: 15.9 dB in, 3.0 dB stationary, 3.4 dB
non-stationary, 7.4 dB at `prop_decrease=0.6`. The test source was
itself a demucs stem, so this is not a clean verdict on a real mic
recording — but do not plan around it. A highpass around 80 Hz and a
gate, written in numpy like everything else here, is the first thing to
try on a bedroom take.

**Not installed, one `apt` away if wanted** (sudo works here):
`rubberband-cli` + `pyrubberband`, for high-quality time-stretching if
syllables need pulling onto the grid. WORLD can time-stretch by
resampling its own frame sequence, so this is a convenience, not a gap.

**What this changes.** The earlier advice — "sing it where it will sit,
do not plan on singing tenor and rendering baritone" — is **withdrawn**.
Formant-preserving shifts of an octave are now a verified capability,
and formant shifting on its own is a separate knob for making a voice
bigger or smaller without touching the note. Sing where it is
comfortable; the register is adjustable afterwards. Listen to `08` and
`09` before deciding how much to lean on that.

## Key follows the singer

Still the right default, though less binding now that register is
adjustable after the fact. Record a comfortable range first, measure it
with Praat or `pyin`, then set the track's key from it. `EBM_1990s.md` §4 has the
two reference registers — Groth a tenor (hooks ~A3–A4, peaking C5),
Harris a baritone (~A2–E4) — and whichever the user's voice sits in
picks which record the track is chasing. *Reliquary v2*'s hook is
already written baritone (A2–B♭3), so it is the natural first test.

## Lyrics

Genre conventions, from the blueprints:

- **Short.** A chorus is one or two lines, repeated; the title is
  usually the hook. Verses are declamatory and brief. A whole song is
  maybe six to ten distinct lines, not a lyric sheet.
- **Apop / *Soli Deo Gloria*:** faith and doubt, mortality, blood,
  heretics, judgement, spiritual reality — Groth's own frame,
  life-and-death imagery.
- **VNV:** fate, honour, defiance, standing and falling, empires, grief
  turned into resolve. Hymn diction. Aspirational but grim.
- **Old-school EBM:** barked slogans, single phrases, imperative mood.
- Constraints: **English** (the 2026-07-10 rule), and never quote real
  lyrics from the sources.

*Reliquary* gives a lyrical world for free: a reliquary holds relics —
what is kept of the dead, fragments in a container, the cold chapel.
Preservation, remains, what is left of someone. Dark-EBM appropriate
without being cod-religious, and it matches the woodcut-and-liturgy
frame of the source album.

Approach: **the user's own words will sit better than mine** — a person
singing their own line is the whole point. Drafts are a starting point
to react to, not a deliverable. Register to aim at, for the chant-like
delivery (short, stressed, repeatable):

> *"what I keep of you / is bone and cold and true"*
> *"hold the door / I am not what I was before"*

## Pipeline

The pattern is already proven by `ungeschrieben.py` and documented in
`../trance/CLAUDE.md`:

- The take is **cached on disk** (`/workspace/music/vocals/<track>/`),
  read at render time, never committed (audio is never committed).
- **`VOICE_GAIN = 0.0` renders the track fully instrumental** with no
  file present. That knob is the contract: the script must run for
  anyone, on any machine, without the recording.
- Determinism: the synthesized layers stay seed-reproducible; the vocal
  is an input asset, so the render is reproducible *given the file*.
  Say so in the notes doc.
- Verify additions, per `../VERIFY.md`'s vocal-song variant: printed
  per-note pitch error in cents (target vs measured — still a useful
  check, it was never what failed on `unsung`), and the vocal/lead
  overlap ratio if there is a duet.

## Open questions (answer before the next track)

1. Sung, or half-spoken/declaimed (the Harris and old-school EBM mode)?
   The declaimed mode is easier, more era-authentic for 1993, and suits
   the chant vocabulary — recommended for the first attempt.
2. Which archetype gets the voice: the 122 slam (*Ashes to Ashes*), or
   a vocal on *Reliquary*'s existing hook as a low-risk test?
   Recommended: the test first — the melody and the render already
   exist, so only the voice is new.
3. Whose words — user-written, or drafts to react to?
4. How much treatment: naked-ish and dry (the vocal forward, exposed),
   or heavily doubled/delayed/sampled (the record's own answer)?
   Recommended: heavy, and back it off if it hides too much.
5. Vocoder on the table at all, or straight voice only?

## No Access (2026-09-06): the first slot is SPOKEN, not sung

The next track keeps the sung question open and uses the voice as a
sample instead: "No access" (three times, before each chorus and in the
break) and "Access granted" (once, on the final chorus) — spoken into a
phone, dry, dropped into `/workspace/music/vocals/no_access/` as
`no_access.wav` and `access_granted.wav`, and treated by
`instruments/machine.py` into a 1993 sampler speech snippet (band, crude
dirt, ring mod, retrigger). The speaker is never exposed; the SH-101 tick
phrase fills the slot while no take exists (`VOICE_GAIN = 0`). Probe 09
in `no_access_probe.py` proves the chain on a stand-in voice — verdict:
"the robot works surprisingly well; impossible to hear what it's saying,
but it sounds like a voice", which is all the slot needs. Design and
placement: `no_access_notes.md`.

**Amended 2026-09-08 (no_access v2).** No take yet ("still not ready"),
and the user chose a TTS voice for the slot instead: edge-tts
`en-GB-SoniaNeural`, cached once, through `machine.py` — the denials
ring-modulated (the robot), the grant clean. This narrows the "TTS is
ruled out" above to what it was always about: TTS *singing* and TTS as
a *performer*. A machine saying two words in a sample slot is the slot
working as designed. The own-take path is unchanged and takes priority
whenever a file appears in `/workspace/music/vocals/no_access/`.
