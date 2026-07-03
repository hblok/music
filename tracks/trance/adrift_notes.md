# Adrift — design notes (dream trance, the tide form)

Composition document for review before writing `adrift.py`
(→ `adrift.wav`; filename follows the title — see question 1).

Per the roadmap: a third original, and the era moves forward again —
penumbra was 1994 Belgium, farlight 1995 Berlin; this is **1996 Italian
dream trance** (the *Children* school: Robert Miles, Zhi-Vago, DJ Dado)
— not a Robert Miles cover, but the era's signature triangle: the
**piano theme** carried on a slightly dirty sampled piano, the **airy
choir/vocal pad** above it, and the four-to-the-floor beat that never
stops being danceable underneath. No blueprint doc; the era reference
is the school itself.

**The story**: the sky, the ocean, clouds drifting by. The piano is
the drifting — once the theme starts moving it *never stops*, it
floats on through every seam like a cloud that doesn't care what the
ground does. The kick and bass are the tide — they go out and come
back **underneath the still-playing melody**. The choir pad is the sky
that hangs over everything. Serene but not sleepy: the beat is present
almost throughout, 4/4, danceable, energy intact — the calm lives in
the *melody's* indifference to the tide, not in a drop of energy.
Per the standing texture rule: the ocean and the clouds are *form and
texture* (the tide shape, slow pad swells, high air-shimmer), never
literal SFX — no wave samples, no seagulls, no wind noise.

- Tempo/key: **137 BPM, C♯ natural minor** (see question 2). Harmony:
  **C♯m–A–E–B (i–VI–III–VII)** — the dream-era progression shape
  (Am–F–C–G's shape, transposed off unsung's exact key), one family
  throughout. Bright-dark, open, dreamy.
- Seed: `np.random.default_rng(1996)  # the year the dream broke`.
- Length ~202 bars + tail ≈ 6:00 (bar = 1.752 s) — the farlight
  lesson: the back half earns its minutes.
- Output: `/workspace/music/adrift.wav` (+ mp3).

## Identity separation

- **vs unsung** (A minor, Am–F–C–G, 132, vocal): same progression
  *shape* — the era's lingua franca — but transposed, 137 BPM, and the
  voice here is a wordless pad texture, never a singer (question 3).
  Nothing of the TTS machinery returns except the salvaged vowel
  recipe (see instruments).
- **vs nachtkind** (the other piano track): nachtkind's piano is
  gothic, funereal, stately, G minor, drenched in the dark hall.
  This piano is *bright, dirty, upfront* — a worn sampler patch, not
  a cathedral instrument — and it carries a floating major-leaning
  Aeolian tune, not a dirge. Reverse cymbals stay banned (nachtkind's
  signature).
- **vs farlight** (the other bright track): farlight bounces — dotted
  rhythms, glittering bell, the departure story. Adrift *floats* —
  even note values, sustained tones, the staying story. The bell does
  not appear here at all.
- **vs penumbra** (the other 6:00 single-wave): penumbra develops one
  filter arc with no re-entry drama; adrift's whole point is the
  tide — the beat *leaves and returns*. No trance gate here.

## How the song doctrine maps onto the tide form

1. **The refrain is the piano theme** — 8 bars, Q/A at melody level:
   antecedent floats up and hangs on the B (♭7 — Aeolian, it hangs
   rather than leads), consequent falls home to C♯. Identical melody
   at every statement, dream-simple (mostly quarters and halves —
   the *Children* register: plaintive, singable, unhurried).
2. **Thesis early / bookend.** The dirty piano states the full
   refrain solo over one pad swell + air shimmer in the first bars
   (hook inside ten seconds). The outro bookend restates it solo
   after the kick stops, drifting off unresolved into the hall.
3. **THE DRIFT / THE RETURN — this track's signature device.** From
   chorus 2 to the end of the return, the piano plays *continuously*:
   the tide goes out (kick+bass exit under a ringing chord) and the
   theme keeps going, weightless over the choir; then the piano
   starts a fresh statement alone, and **the kick lands on bar 5 of
   that statement** — mid-phrase, the beat rejoining the dream rather
   than the melody arriving on the beat. Both facts are printed and
   checked: no gap in the piano lane across either seam, and the
   re-entry offset is mid-statement, not a downbeat handover.
4. **Q/A between instruments**: the verse pluck-arp asks and a
   counter-arp answers (verse 2); the choir pad holds harmony only
   until the final wave, where it *answers the refrain's B-hangs*
   with single held vowel tones (question 3); the warm lead
   countermelody joins under the refrain only in the wave — the
   fusion, earned, duet-overlap printed.
5. **Seams**: snare rolls + dark bandlimited swells (the 1995 kit,
   still era-authentic in '96; white noise stays careful per the
   farlight answer), crashes, ringing chords, piano pickups — and
   the piano continuity itself, which is the seam device for the
   two tide boundaries. No reverse cymbals, no toms, no composed
   full silence (the drift never actually stops — the one dropped
   beat lives inside the return slam's bar).

## New instruments (the recipes this track adds)

1. **The dirty dream piano** — the centerpiece. Base is the proven
   M1-era piano (stretched inharmonic partials `fk = f·k·√(1+B·k²)`,
   B≈3.5e-4, two detuned strings, hammer thunk, per-(pitch,dur)
   cache), re-voiced bright (`1/k**1.15`, hammer up) and then made
   *dirty* — the worn-sampler character (question 4 sets the dial):
   zero-order-hold resample to an effective ~18–22 kHz (the aliasing
   sheen every 90s rompler had), a slow wow ±0.04 % at ~0.3 Hz (the
   worn-sample drift), soft `tanh(0.9)`, lowpass ~7.5 kHz. Upfront in
   the mix: dry-ish center, long hall on the tail only (wet ~0.4) —
   a dream piano is *close*, not buried.
2. **The breath choir** — the "soft vocals, kept instrumental":
   a wordless "aah" pad, the one salvageable part of unsung's vowel
   machinery with all the TTS grafting discarded. Rolled-off harmonic
   source (`1/k**1.4`), 3 detuned copies (±0.4 %), two `iirpeak`
   formants for the vowel (ah ≈ 650/1080 Hz, Q ~5 — vocal color
   needs the Q; the guardrails: moderate blend, a lowpassed chest
   layer so the fundamental survives, and the formants never sweep),
   ~8 % breath noise (1.5–4 kHz) riding the envelope, slow ~0.8 s
   raised-cosine attack, very wet (≥ 0.55), wide. Reads as a rompler
   choir patch — era-authentic and safely on the instrument side of
   the vocal rule.
3. **Cloud swells + air shimmer** — the "space sounds", textural
   (question 6): the dark string-pad recipe slowed further (~1.5 s
   attacks) with a very slow bandpass drift for the swell shape, plus
   a high air layer — soft detuned sine cluster (2–4 kHz), slowly
   panning, felt more than heard. No beating mid-tones (the standing
   drone rule), no white-noise wash.

Reused as-is: warmed rolling 16th mono bass with octave bounce
(lost_v4 school) on the chord roots; the glassy pluck arp for verses
(lost's pluck on the new progression); the warm detuned lead as the
fusion countermelody (THE warmth recipe); 909 kit rounder and deeper
still (the era drift continues — kick fatter than farlight's), 16th
hats, offbeat open hat, claps on 2&4, ride in the wave; snare-roll +
dark-swell build kit; dry drums / wet melodics, no sidechain pump.

## Structure (~202 bars + tail, bar = 1.752 s)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | thesis (8) | Solo dirty piano states the full refrain over one cloud swell + air shimmer. The hook inside ten seconds. |
| 8 | 0:14 | intro (16) | Kick enters on a piano pickup; bass rolls in on C♯; 16th hats; one element per 4 bars. |
| 24 | 0:42 | verse 1 (16) | The pluck arp carries Q/A pairs over C♯m–A–E–B; open hat at the midpoint. |
| 40 | 1:10 | build 1 (8) | Snare roll + dark swell, piano pickup, crash → |
| 48 | 1:24 | CHORUS 1 (16) | The piano refrain ×2, full kit, pads open. |
| 64 | 1:52 | verse 2 (16) | Counter-arp answers the arp; claps enter; **the choir fades in** — harmony only, the sky arriving. |
| 80 | 2:20 | build 2 (8) | Longer roll, swell, one-bar drum dropout → |
| 88 | 2:34 | CHORUS 2 (16) | Refrain ×2 under the choir sky. The piano does not stop again until the wave is over. Last chord rings into — |
| 104 | 3:02 | THE DRIFT (20) | The tide goes out: kick+bass exit under the ring. Refrain ×2 weightless — piano + choir + cloud swells only. Bars 16–20: the piano begins statement 3 *alone* — |
| 124 | 3:37 | THE RETURN (12) | — and the kick lands on **bar 5 of that statement**, mid-phrase; bass and kit bloom under the unbroken piano (eased sub — the farlight speaker lesson), the statement completes, then one more full-arrangement statement. |
| 136 | 3:58 | dip (4) | Claps/ride out, one breath (the long-drop lesson). |
| 140 | 4:05 | THE WAVE (24) | The fusion: refrain ×3 with the warm lead countermelody underneath and the choir answering every B-hang. Fullest, loudest section. |
| 164 | 4:47 | ride-out (16) | Layers peel in reverse; choir recedes to pure pad; the kick keeps four-on-the-floor — danceable to the edge. |
| 180 | 5:15 | outro (16) | Kick stops ~bar 184 (printed event); solo piano bookend over choir breath; hall rings. |
| 196 | 5:43 | tail (6) | Last pad, air shimmer, one piano note. ~6:00. |

## Verification (per ../VERIFY.md — song form + the tide devices)

- Section map (incl. the kick stop); seam checklist (roll + swell /
  crash / ringing chord / pickup / **piano continuity** at the two
  tide seams).
- **Hook count**: thesis 1, chorus 1 ×2, chorus 2 ×2, drift ×2, the
  straddled statement 1, return full statement 1, wave ×3, bookend 1
  → target **≥ 12**. Full 8-bar statements only.
- **The unbroken drift, printed and checked** (from the score data):
  maximum piano inter-onset gap from chorus 2 bar 0 through the end
  of the return < 1 bar — no gap at either tide seam.
- **The mid-phrase return**: kick re-entry offset within the active
  statement printed; check `offset == 4` bars (bar 5 of 8) — the
  beat rejoins the dream, it does not restart it.
- **Choir discipline**: zero choir before verse 2; harmony-only
  (no melodic tones) before the wave; hang-answers in the wave only;
  presence-checked.
- **Duet overlap** (lead countermelody vs refrain): ≈ 0 before the
  wave, substantially overlapped in the wave — the fusion earned.
- **The dirt knobs printed**: effective sample rate, wow depth/rate,
  drive — the receipt for question 4's dial.
- Per-section RMS, standard song set: thesis < verse 1 < chorus 1;
  each chorus > its build; chorus 2 ≥ chorus 1; **THE DRIFT is the
  trough**; THE WAVE loudest; ride-out descends; outro settles near
  intro level. Sub entries bloom, never snap — the return slam gets
  the eased sub explicitly.
- Banned-list audit (by construction, printed): no supersaw, no
  sidechain pump, no acid resonance, no reverse cymbal, no toms, no
  white-noise wash (dark bandlimited swells only), **no literal SFX**
  (no wave/seagull/wind samples), no trance gate (penumbra's), no
  bell (farlight's); all pitches diatonic to C♯ natural minor
  (pc-set check).

## Open questions for review

1. **Title**: *Adrift* (my recommendation — the piano drifting through
   the tide IS the form; ocean and clouds in one word) vs *Cirrus*
   (the high drifting cloud — sky-only, cooler) vs *Halcyon* (the
   mythic calm sea — but it collides with Orbital's classic of that
   name, which I'd rather not touch). Filename follows.
   Answer: Adrift works.

2. **Key**: (a) **C♯ natural minor, C♯m–A–E–B** (my recommendation —
   the dream-era progression shape in a key no track owns; Zhi-Vago's
   neighborhood, bright-dark and open), vs (b) reclaim **A minor,
   Am–F–C–G** (the era's literal home key — unsung is a dead end, but
   it did render in exactly this key and family, so the identity
   collision is real), vs (c) **F♯ natural minor, F♯m–D–A–E** (same
   shape, sits a touch darker/heavier in the bass register).
   Answer: Difficult. I'm torn between C# minor and A minor. I'm probably leaning towards the former.

3. **The choir's melodic license** — how vocal may the "soft vocals"
   get: (a) **pad + hang-answers** (my recommendation — harmony
   throughout, and in the wave it answers the refrain's held B with
   single sustained vowel tones; a voice-like presence that never
   becomes a singer), vs (b) the choir takes one full refrain
   statement in the drift (the performer handoff — maximum dream, but
   it walks right up to the unsung dead-end line), vs (c) strictly
   harmonic pad, never a melodic tone (safest, least vocal).
   Answers: yes, harmonic throughout

4. **How dirty is the piano**: (a) subtle grit — ~22 kHz ZOH + wow +
   soft drive, felt as warmth and age more than heard, vs (b) **openly
   dirty** (my recommendation, since "dirty piano" was the brief —
   ~16–18 kHz effective rate, the aliasing sheen clearly audible on
   the high notes, wow ±0.05 %; musical lo-fi, not bitcrush novelty),
   vs (c) clean M1 brightness, detune only. The knobs print either
   way, easy to re-dial after the first listen.
   Answers: let's keep it warm

5. **The tide count**: (a) **one big tide** (my recommendation — the
   classic dream form: one drift, one return, maximum weight on the
   single moment), vs (b) two tides (a small early drift of 8 bars
   after chorus 1, foreshadowing the big one — more ocean-like, but
   it spends the device's surprise early).
   Answers: one tide count

6. **Space sounds scope**: (a) **textural only** (my recommendation —
   cloud swells + air shimmer, per the no-literal-SFX rule), vs (b)
   also one recurring "signal" motif — a soft echo-blip with long
   feedback delay answering the piano once per chorus (the DJ Dado /
   X-Files school; a fourth voice, at the cost of palette economy).
   Answer: Ah, yes! X-Files. Briliant. That's an excellent reference. so I guest long feedback delay.

Extra: In almost all the other tracks, the baseline has been an oschilating 303 like bass. I think we've tried that many times now. It's time to come up with something else. Especially, since we're leaving the proto-trance behind here, and going into a slightly different era. Now, "Children" had a very soft bass line. With BBE's 7 days, there's something in the middle.
But if we look at U96 - Love sees no colour (more techno than dream trance, but still), there we have an intereting more dirty beat. It's almost like scratched record (not skipping, but smeared out). Maybe that could work.
