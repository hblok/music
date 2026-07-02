# Lost v5 — design notes (the song treatment)

Composition document for review before writing `lost_v5.py`.
(Naming: `lost_v4.py` already renders `lost_v5.wav`, so this script
renders **`lost_v6.wav`** — the script/WAV offset carries forward.)

The emotional-trance journey — love, confusion, loss, dread, sadness,
hope — retold as a **song**. v4 already has the cohesion trinity (one
chord loop, one theme, one instrument set); what it lacks is the song
doctrine: a refrain with a fixed identity, question/answer composed at
every level, seam devices at every boundary, and the early thesis.

**The concept: one refrain, three lights.** The theme becomes a true
refrain — *identical melody* in every drop — and the emotion comes
entirely from how the harmony lights it. Bm–G–D–A shares all seven
notes between D major and B minor, so the same tune can land bright
(cadencing to D), sad (to Bm), or resolved (to D with the full band).
That existing trick stops being a background color and becomes the
song's engine:

- **LOVE** (chorus 1): refrain lands on D — bright.
- **DREAD** (chorus 2): *the same notes* land on Bm — the cathartic
  minor climax (sadness, not horror; warm lead + cello octave below,
  no acid, per the standing feedback).
- **HOPE** (chorus 3+4): D again, now with the fusion payoff.

Same tune, different light = the trance version of "same words, new
meaning".

- Length ~6:30–7:00, 130 BPM, 4/4 (flexible — take the bars needed).
- Key: D major / B minor, one loop: Bm–G–D–A (vi–IV–I–V).
- Seed: `np.random.default_rng(130)` (unchanged).
- Output: `/workspace/music/lost_v6.wav` (+ mp3).

## Question / answer — the three levels

1. **Inside the melody**: the refrain is rewritten as a Q/A cell —
   2-bar question rising to hang on A (the V — works over both
   resolutions), 2-bar answer with the same rhythm falling to D or B
   depending on the section's light. Verse phrases are Q/A pairs the
   same way.
2. **Between instruments**: the warm lead calls, the piano or cello
   answers the phrase tail — a composed echo entering on the lead's
   last note (roles swap in the second verse: piano leads, lead
   echoes). In the LOSS break the trade is bare: piano asks the theme,
   cello answers, no drums.
3. **Between sections**: breaks ask (fragments, off-tonic, thinning),
   drops answer (full refrain, cadence). The SADNESS break asks with
   the most broken fragment of the tune; HOPE answers it with the
   fusion.

## What v5 fixes over v4

1. **Thesis early**: solo piano states the refrain once in the first
   ~10 s (half-voice, wet) before the kick — replaces the 30 s
   settle-in. The outro bookends it: after the groove strips, solo
   piano plays the refrain once more, one ringing chord, fade.
2. **Refrain identity**: v4 "states the theme in every section" but
   varies it freely; v5 keeps drop statements *identical* (target ≥ 10
   statements) and pushes all variation into the verses and breaks.
3. **Seam devices**: pickup / ringing chord / fill / reverse cymbal at
   every boundary; the composed drop-silence beat only before HOPE.
4. **Motif development**: the glassy pluck arpeggio figure gets the
   state/vary/answer treatment across verses instead of being wallpaper.
5. **CONFUSION becomes verse development**: the major/minor flicker and
   borrowed Bb stay, reframed as "verse 2 — same tune losing its
   footing" rather than a separate scene.

## Structure (sketch, ~176 bars)

| t | section | what happens |
|------|---------|--------------|
| 0:00 | thesis (4) | Solo piano refrain, half-voice, wet. Last chord rings under the kick entry. |
| 0:10 | intro/verse 1 (16) | Groove assembles fast (kick, pluck, warm bass); lead sings verse Q/A pairs low, piano echoing tails. |
| 0:40 | pre-chorus (8) | Rising trade lead/piano, build fill → |
| 0:55 | **CHORUS 1 — LOVE** (16) | Refrain on the warm lead, bright D cadences; full groove. |
| 1:25 | verse 2 — CONFUSION (24) | Piano leads, lead echoes; D flickers maj/min, the borrowed Bb; the pluck figure varied. Groove never fully stops. |
| 2:10 | **LOSS** (break, 16) | Beat drops; piano asks / cello answers, bare; heartbeat; build. |
| 2:40 | **CHORUS 2 — DREAD** (24) | The refrain *identical* but landing on Bm: the sad climax — lead soaring, cello octave below, big minor pads, driving warm beat. Mid-drop dip, then fullest wave. |
| 3:25 | **SADNESS** (break, 16) | Aftermath: the most broken fragment on solo piano, cello answer; layers to near-nothing; rebuild + riser → drop-silence beat → |
| 3:55 | **CHORUS 3 — HOPE** (16) | Refrain back to D, full band slams in on beat 2. |
| 4:25 | **CHORUS 4 — fusion** (16) | The everything-chorus: refrain on lead, **cello counter-line under it** (the question sounding with its answer), glittering plucks, ride. Ritardando tail across the seam. |
| 4:55 | outro (16 + tail) | Deconstruction; solo piano bookend, final chord rings, fade. |

Verify (script prints): refrain count ≥ 10; RMS ordering — thesis <
verse1 < chorus1, chorus2 ≥ chorus1, chorus4 loudest, breaks are the
troughs, outro settles; seam checklist per boundary.

## The band (unchanged — the v4 five + kit)

Warm detuned lead (warmth recipe), glassy pluck arpeggio, pads, piano,
cello; kick/hats/claps groove and the warmed rolling octave bass from
v4. **No new timbres, no acid, no Dune palette, no vocals.**

## Open questions for review

1. **Emotional labels vs song sections**: keep the six emotion names in
   the code/printout (LOVE/CONFUSION/…) mapped onto the song form as
   above, or rename to plain verse/chorus/bridge? I recommend keeping
   the emotion names — they're the story, the song form is the
   skeleton.

2. **CONFUSION length**: 24 bars as sketched (room to develop the
   flicker) or trim to 16 to land nearer 6:00? I recommend 24 — v4's
   confusion is one of its best ideas and deserves the development
   space.

3. **The heartbeat in LOSS**: keep (it worked in v4 and reads as the
   one human sound in the break) or drop as clutter? I recommend keep.
