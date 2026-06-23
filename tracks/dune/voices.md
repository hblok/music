# Dune RTS — Voice System Notes

Everything learned across the voice generation sessions: what works, what
doesn't, the technical tricks, and the final picks.

---

## Installation requirements

```bash
pip install gtts          # Google TTS — free, online, female voice
pip install edge-tts      # Microsoft Edge TTS — free, online, neural voices
# ffmpeg must be on PATH — both engines output MP3; we convert to WAV
# numpy, scipy — post-processing (already required by the music system)
```

Neither engine requires an API key. Both need internet at generation time.
The generated WAVs are cached on disk so the game itself is fully offline.

---

## The four chosen voices

| Tag | edge-tts voice ID | Gender | Character |
|-----|------------------|--------|-----------|
| `au_william_m` | `en-AU-WilliamMultilingualNeural` | Male | Warm but firm Australian. Natural authority, not stiff. |
| `au_natasha_f` | `en-AU-NatashaNeural` | Female | Clear, calm Australian female. Credible under pressure. |
| `us_aria_f` | `en-US-AriaNeural` | Female | Expressive American female. Good dynamic range. |
| `us_guy_m` | `en-US-GuyNeural` | Male | Classic American broadcast male. Authoritative, clean. |

**Generator:** `generate_voice_final.py` — all 16 lines × 4 voices × 3 effects.
**Output:** `/workspace/music/voice/final/`
**Naming:** `{cat}_{slug}_{voice_tag}_{effect}.wav`

---

## The three chosen effects

### `_benegesserit`
Sub-harmonic layer (octave below, 18% gain) + three detuned+delayed chorus
copies (−0.4/+0.6/−0.9 semitones at 8/15/23 ms) + 800–3000 Hz formant boost
+ short room reverb (wet=0.28) + 5 ms L/R stereo offset.

Sounds like the speaker occupies multiple registers simultaneously. Works best
on atmospheric lines ("The spice must flow.") and as a commanding overlay.
Also striking on alerts — feels like the voice is inside your head.

### `_bitcrush`
Downsample to 7350 Hz (SR/6), resample back → 8-bit quantise (128 levels)
→ add 3 kHz-lowpassed noise floor (σ=0.025) → 400–3000 Hz bandpass.

Sounds like a degraded or archival transmission. Good for damaged-comms
context, or to suggest distance/age. One of the most immediately
recognisable effects.

### `_ringmod`
Multiply signal by a 72 Hz sine carrier → 3500 Hz lowpass → blend 60% wet /
40% dry → short room reverb (wet=0.22) + 6 ms L/R offset.

Creates metallic sidebands — alien, mechanical. The 60/40 wet/dry blend
keeps the words intelligible while the timbre is noticeably non-human. Lower
carrier frequencies (below ~100 Hz) preserve intelligibility; higher
frequencies (~300+) become too garbled.

---

## The standard intercom chain (baseline, not in final batch)

Used in all non-final scripts as the default in-game flavour:

1. Butterworth bandpass 300–3400 Hz (telephone bandwidth)
2. Noise gate (threshold 0.010, 5 ms hold)
3. tanh overdrive — drive=4.5 for alerts/status, 3.0 for other categories
4. Radio click prepended (4 ms noise burst, 1200–8000 Hz) for alert lines only
5. Short room reverb (0.5 s IR, wet=0.38)
6. 7 ms L/R stereo offset for width

**Wet level sweet spot:** 0.38 for intercom, 0.48 for distant (with 1.2 s IR).
Below 0.20 sounds too flat/dry; above 0.72 with a 2.5 s IR sounds too echoey.

---

## The OLA pitch + speed trick

gTTS/edge-tts voices are too slow and "polite" at default. We want:
- **Lower pitch** → more authority
- **Faster delivery** → more urgency

These are opposing operations on a plain resample (faster = higher pitch).
The solution is **Overlap-Add (OLA) time-stretching**:

```
Step 1: resample(x, int(N / pitch_factor))
        → pitch drops, audio gets LONGER (1/pitch_factor × original)
Step 2: OLA compress back to target duration
        → duration restored, pitch stays shifted
```

OLA chops audio into overlapping Hann-windowed frames (1024 samples, 256 hop)
and reassembles at a different hop distance — changes duration without
affecting frequency content.

**Per-category settings:**

| Category | Semitones | Speed | Notes |
|----------|-----------|-------|-------|
| alert    | −3        | 1.25× | Fastest, most commanding |
| status   | −2        | 1.10× | Clipped, matter-of-fact |
| build    | −2        | 1.05× | Brisk but clear |
| order    | −2        | 1.00× | Unchanged speed, just pitched |
| atmo     | −3        | 0.95× | Slower for weight |

---

## Effects explored (all scripts in `/repos/dune/music/`)

| Effect | Verdict | Notes |
|--------|---------|-------|
| `_benegesserit` | ✅ Chosen | See above |
| `_bitcrush` | ✅ Chosen | See above |
| `_ringmod` | ✅ Chosen | See above |
| `_intercom` | ✅ Baseline | Standard in-game chain |
| `_distant` | ✅ Good | For off-map / echo-across-base context |
| `_chorus` | ⚠️ Situational | Too ghostly for alerts; good for atmo |
| `_megaphone` | ⚠️ Situational | Outdoor/field address; harsh |
| `_sardaukar` | ⚠️ Situational | Very aggressive, useful for enemy faction |
| `_whisper` | ⚠️ Situational | Intel reports, ominous asides |

---

## Voices explored and rejected

### espeak-ng
**Verdict: Rejected.** The robotic quality was explicitly unwanted. Even with
`en-gb+m3`, pitch=12, rate=118 the synthetic timbre was too obviously
non-human in a way that felt cheap rather than sci-fi. espeak may still work
for heavily processed effects (e.g. heavily ring-modded or bitcrushed) where
the source artefacts are masked, but not as a primary voice.

### gTTS `en-gb` (British female, `co.uk`)
**Verdict: Rejected as-is; useful as base for effects.**
Without processing: "sounds like a greeting to enter the doctor's office" —
too friendly, too polite, no urgency. With OLA pitch+speed processing it
becomes acceptable, but the neural edge-tts voices are clearly better.

### gTTS `en-gb` unprocessed (no OLA)
Simple pitch-down via resampling makes the voice too slow; speed-up raises
pitch. Without OLA these are inseparable. Always use OLA.

---

## Language / accent experiments

All outputs in `/workspace/music/voice/` and `/workspace/music/voice/showcase/`.
Script: `generate_voice_languages.py`, `generate_voice_showcase.py`.

| Language | Approach | Character | Dune fit |
|----------|----------|-----------|----------|
| German (`de`) | English text to German TTS | Clipped consonants, flat vowels | Enemy faction (Harkonnen) |
| Finnish (`fi`) | English text to Finnish TTS | Unusually even prosody, mechanical-sounding | AI/computer system |
| Japanese (`ja`) | Katakana phonetic transcription | Short mora timing, recognisably Japanese | Exotic/alien feel |
| Arabic (`ar`) | Arabic-script phonetic transliteration | Arabic vocal timbre saying English phonemes | **Most Dune-appropriate** — Fremen universe |
| gTTS US | `tld="com"` | American accent | Neutral, widely understood |
| gTTS AU | `tld="com.au"` | Australian | Similar to chosen edge voices |
| gTTS Indian | `tld="co.in"` | Indian English | Distinctive, interesting |
| gTTS Irish | `tld="ie"` | Irish lilt | Distinctive, uncommon in games |
| gTTS Canadian | `tld="ca"` | Near-neutral North American | Subtle difference from US |

**Arabic phonetic note:** Writing English pronunciation in Arabic script
(e.g. "آور بيس إز أندر أتاك" for "Our base is under attack") and feeding it
to `gtts(lang="ar")` produces Arabic vocal quality saying approximately
English words. Very fitting for a Fremen-inspired universe.

---

## Edge-tts voice shortlist (all tested in showcase)

Full list in `generate_voice_showcase.py`. Highlights beyond the four chosen:

| Voice | Notes |
|-------|-------|
| `en-IE-ConnorNeural` | Irish male — distinctive, uncommon in games |
| `en-ZA-LukeNeural` | South African male — very distinctive vowels |
| `en-NG-AbeoNeural` | Nigerian male — unusual cadence, potentially Fremen-like |
| `en-IN-NeerjaExpressiveNeural` | Indian female Expressive — more dynamic variation |
| `en-GB-RyanNeural` | British male — clean, professional |

---

## Generator scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `generate_ambient.py` | First ambient track | `ambient_track.wav` |
| `generate_arrakis.py` | Dune desert ambient | `arrakis_winds_v2.wav` |
| `generate_base_attack.py` | Battle track | `base_under_attack_v2.wav` |
| `generate_samples.py` | Sound-design glossary (25 samples) | `samples/` |
| `generate_voice_samples.py` | 16 lines, standard processing, `_intercom`/`_distant` | `voice/` |
| `generate_voice_fx.py` | 16 lines × 7 experimental effects | `voice/` |
| `generate_voice_languages.py` | 16 lines × 4 languages | `voice/` |
| `generate_voice_showcase.py` | 3 lines × 15 edge-tts voices + 5 gTTS accents | `voice/showcase/` |
| `generate_voice_final.py` | **16 lines × 4 chosen voices × 3 chosen effects** | `voice/final/` |

All scripts write to `/workspace/music/` (not committed). Scripts live in
`/repos/dune/music/` (tracked in git).
