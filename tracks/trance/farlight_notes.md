# Far Light — design notes (song form, the second original)

Composition document, reviewed (answers embedded below), for
`farlight.py` (→ `farlight.wav`). Title per answer 1: English, a new
naming direction — **Far Light**, the refrain's own image (the bell IS
the far light), and it matches answer 5: keep it light.

Per the roadmap in `idea.md`: **a second original in a proven shape**.
The shape is **song form** (the most-proven — lost, nachtkind), with its
own story, key, era, and centerpiece instrument. No blueprint doc this
time; the era reference is 1994/95 **Berlin/MFS melodic trance** (early
Paul van Dyk, *For an Angel* school) — the moment trance left Frankfurt.
That the scene itself moved cities is the point:

**The story**: the far light on the horizon, and the joy of setting
out toward it. Per answer 5 this is a LIGHT, HAPPY track — wanderlust
as glad anticipation, never ache. The verses are the familiar ground:
a harmonic shuttle that rocks in place, restless but bright. The
refrain is the far light — a glassy bell theme whose last note lands
home on the minor third every chorus: the pull felt, the departure
not yet taken. In the bridge the question is asked alone and gets no
answer. Then the final chorus takes the departure: the *identical*
refrain, its identical last note, re-lit once as the root of the
relative major. The tune never changes; the light does (lost's proven
device, used ONCE, as the story's single payoff). The happiness lives
in the execution: bouncy dotted rhythms in the tune, glittering
octave plucks, bright open pads, a spring in the groove.

- Tempo/key: **136 BPM, E natural minor** (free key — nachtkind owns
  G minor, tech_noir D minor, lost D/Bm, ungeschrieben F minor).
  Aeolian, no borrowed leading tone (that's nachtkind's color).
- Harmony: **i–VII–VI–VII (Em–D–C–D)** — the restless shuttle, a free
  progression family (nachtkind: i–VI–VII–V; ungeschrieben: i–VI–VII;
  lost: vi–IV–I–V rotations). One family throughout; the refrain's
  consequent supplies the only root cadences — Em in every chorus,
  **G major once** at the re-light.
- Seed: `np.random.default_rng(1995)  # the year trance left home`.
- Length ~160 bars ≈ 4:45 + tail (bar = 1.765 s) — the bars the
  material needs; no DJ intro, no padding.
- Output: `/workspace/music/farlight.wav` (+ mp3).

## How the song doctrine maps

1. **Refrain identity.** An 8-bar bell theme, Q/A at melody level:
   antecedent rising and hanging on F# (third of the D chord —
   off-tonic, leaning outward), consequent falling home to a final G
   note. The melody is IDENTICAL at every statement; the final G is
   harmonized as the minor third of Em in every chorus, and as the
   root of G major exactly once (final statement + bookend — see
   question 2). Re-light the tune with the harmony; never change its
   notes.
2. **Q/A at three levels.** Inside the melody (above); between
   instruments — the verse arpeggio asks, a counter-arp answers in
   verse 2, and in the final chorus the warm lead countermelody
   answers the bell phrase-by-phrase (the fusion); between sections —
   verses shuttle without cadence (ask), choruses cadence home
   (answer), the bridge asks the antecedent alone, unanswered, and the
   final chorus answers with the departure.
3. **Thesis early / bookend.** Solo bell states the refrain half-voice
   in the first ~7 s (4 bars, no groove). The outro bookend restates
   it solo after the kick stops — ending on the major light (q. 2).
4. **The fusion payoff.** Early choruses: bell alone carries the tune
   (the lead exists only in verse accompaniment). Final chorus — and
   only there — the warm lead countermelody sounds UNDER the bell
   refrain, phrase-interlocked. Printed as a duet-overlap ratio
   (reusing unsung's duet-separation check for an instrumental duet:
   early choruses near zero, final chorus substantially overlapped).
5. **Seams / this track's own vocabulary**: **snare rolls and noise
   swells** — era-authentic for 1995, and deliberately the opposite
   of ungeschrieben's 1992 ban (the era marker; per answer 4, with
   caution on the noise: dark bandlimited swells, never a white-noise
   wash) — plus bell pickup notes, ringing chords, and the one
   composed silent beat before the final chorus. No reverse cymbals
   or downsweeps (nachtkind's family), no tom fills
   (ungeschrieben's), no acid, ever.

## New instruments (the recipes this track adds)

1. **The bell / ice-glass lead** — the refrain voice and the track's
   identity (see question 3). Not a piano (nachtkind's), not the warm
   saw lead (lost's): a glassy digital bell. Sketch: 3–4 inharmonic
   partials (ratios ~1 / 2.76 / 5.40, falling gains — tubular-bell
   family), a soft mallet transient, a detuned pair (±0.06 %) for
   shimmer, fast attack + long exponential decay, long dark hall
   (wet ~0.5). Warmth rules still bind it: partial gains rolled off,
   no 2–4 kHz spike — glassy but *round*, never icy-shrill.
2. **The 1995 riser/roll kit** — 16th→32nd snare roll into a crest +
   a noise swell, the era's build furniture (sanctioned for this
   track only; per answer 4 the swell is DARK and bandlimited,
   250–2400 Hz, kept low in the mix — careful with the white noise).
   Short, always resolved by a crash on the downbeat.

Reused as-is (the corpus recipes): warmed rolling 16th mono bass on E
with octave jumps (lost_v4 `bass_note` school), the glassy-warm
arpeggio pluck for verses (lost's pluck, re-voiced on the shuttle),
warm detuned lead for the fusion countermelody (THE warmth recipe),
dark slow pads, 909 kit — kick slightly deeper/rounder than
ungeschrieben's raw 1992 dial (the era drift), 16th hats, offbeat open
hat, claps on 2&4. Dry drums / wet melodics, no sidechain pump.

## Structure (~160 bars + tail, bar = 1.765 s)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | thesis (4) | Solo bell, the refrain's question phrase half-voice in the hall — the hook inside ten seconds. |
| 4 | 0:07 | intro (16) | Kick enters on a bell pickup; 16th hats; the bass rolls in on E; the arp fades up. One element per 4 bars. |
| 20 | 0:35 | verse 1 (16) | The arp carries Q/A phrase pairs over the shuttle (Em–D–C–D); open hat joins at the midpoint. No cadence anywhere — restless. |
| 36 | 1:04 | build 1 (8) | First snare roll + noise riser, pads swell, bell pickup, crash → |
| 44 | 1:18 | CHORUS 1 (16) | The bell refrain ×2, full kit, pads open. Both statements end home: G note as the minor third of Em. Last chord rings across — |
| 60 | 1:46 | verse 2 (16) | Development: the counter-arp answers the arp's phrases, bass adds octave jumps, claps enter. |
| 76 | 2:14 | build 2 (8) | Longer roll, riser, and a one-bar drum dropout before the impact → |
| 84 | 2:28 | CHORUS 2 (16) | Refrain ×2 with octave doubling on the bell; brighter, bigger. Still ends home (Em). |
| 100 | 2:56 | bridge (16) | Teardown: kick out, pads + bass throb; the bell asks the ANTECEDENT ALONE twice — the question with no answer. Ends on the composed silent beat. |
| 116 | 3:25 | FINAL CHORUS (24) | The fusion: warm lead countermelody under the bell refrain ×3; mid-drop dip at bars 8–12, then the fullest wave (the long-drop lesson). The 3rd statement is THE RE-LIGHT: its final bar lands **G major** — the departure taken. Loudest section. |
| 140 | 4:07 | outro (16) | Kick stops (printed event); layers peel; the solo bell bookend states the full Q/A once more, ending on the major light. Hall rings out. |

## Verification (per ../VERIFY.md — song form)

- Section map (incl. the kick-stop event); seam checklist (roll +
  riser / crash / ringing chord / pickup / the silent beat).
- **Hook count**: full refrain statements — chorus 1: 2, chorus 2: 2,
  final: 3, bookend: 1 → target **>= 8**. The thesis and bridge
  antecedent-only fragments don't count.
- **The re-light, printed and checked** (from the score data, not
  audio): the final chord under the refrain's last note at every
  statement — Em for statements 1–7, **G major only at statement 8**
  (and the bookend, per q. 2). Exactly one re-light.
- **Duet overlap ratio** per chorus (bell refrain vs lead
  countermelody activity): chorus 1 ≈ 0, chorus 2 ≈ 0, final chorus
  substantially overlapped — the fusion earned, not default.
- Per-section RMS, standard song set: thesis < verse 1 < chorus 1;
  each chorus > its build; chorus 2 >= chorus 1; final chorus loudest;
  bridge is the trough (quieter than both neighbours); outro settles
  back toward the intro level.
- Banned-list audit (by construction, stated in the printout): no
  acid/resonant scream, no sidechain pump, no reverse cymbal, no
  borrowed leading tone, no supersaw stack (the lead stays the warm
  3-voice recipe).

## Open questions for review

1. **Title / story direction**: *Fernweh* (German, "the ache for
   elsewhere" — my recommendation; continues the nachtkind /
   ungeschrieben German lineage, and the story is the leaving) vs
   *Heimweh* (the mirror story: the refrain is home, the re-light is
   the return) vs English *Wanderlust*. The filename follows.
   Answer: Well. I think it's time to come up with a different concept for these names. They don't all have to be in German. Let's call it something in English. 

2. **The ending light**: I propose the re-light lands at the final
   refrain statement AND the outro bookend keeps it (the track
   leaves, and stays gone — hopeful ending). Alternative: the bookend
   falls back to Em (the departure imagined, never taken — the ache
   remains). The corpus already has a track that stays lost; my
   recommendation is the major ending.
   Answer: Yes, re-light. Let's keep it light.

3. **The refrain voice**: the new bell/ice-glass recipe (my
   recommendation — a sixth distinct centerpiece identity: piano /
   machine / warm five / rompler strings / voice / **bell**) vs
   carrying the refrain on the proven warm lead (safer, but collides
   with lost's identity and adds no new recipe).
   Answer: Yes, bell/ice recipe

4. **Sanctioning the 1995 build kit**: snare rolls + white-noise
   risers were explicitly banned in ungeschrieben as post-1992; for a
   1995 track they are era-authentic, and their presence IS the era
   marker between the two originals. Confirm sanctioning them for
   this track only (short, always crash-resolved) — otherwise the
   seam vocabulary falls back to crashes, pickups, and dropouts only.
   Answer: Well, let's be careful with the white-noise, shall we. But sure, era-authentic sounds good.

5. One more note: Let's make a light happy track. Homesickness sounds a bit sad... Let's keep it happy!

## v2 amendments (2026-07-03, after the first listen)

Feedback: the track is good but too short — instead of jumping to the
final chorus at 3:25 there should be "another full extended 3rd chorus,
and then it extends in a version, and then the final" (~6:00). And at
the 3:25 slam "the speaker gets a bit too much".
`farlight_v2.py` → `farlight_v2.wav` (v1 kept, never overwritten):

1. **The extended back half.** The post-bridge slam now lands
   **CHORUS 3** — full and extended (24 bars, refrain ×3: plain →
   +octave bells → +glitter), still bell-only, still Em. Then **THE
   VERSION** (16 bars): the refrain passes to the plucks ×2 (the
   performer handoff, a proven lost device), bells only *answering*
   the held notes; claps out, texture lighter — the breather that
   keeps the long drop alive. Then build 3 (roll + swell), and only
   then the FINAL fusion chorus (24 bars: fusion / dip / wave /
   re-light at 5:30). New length 6:07. Statement count 8 → 13
   (target >= 12); version statements count (any instrument), bell
   answers don't. New checks: chorus 3 >= chorus 2; THE VERSION is a
   breather (below choruses 3 and final); final chorus > build 3;
   choruses 1–3 all trade (overlap < 0.10).
2. **The slam no longer blasts the speaker.** Cause: the sustained
   sub (41 Hz sine) snapped on at FULL gain with a 50 ms attack at
   the same instant as kick + crash + bass, right out of silence.
   Fix: sub entries now BLOOM — 0.25 s attacks, per-bar entry ramp
   0.55→1.0 across each chorus's first three bars, a 0.3 s ease out
   of the silent beat, slam crash 1.0 → 0.85. Measured: slam-bar
   sub-100 Hz RMS 0.220 → 0.192, and 0.74× the settled chorus level
   (was 0.81×) — the weight arrives over three bars now.
