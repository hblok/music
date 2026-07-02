# Muad'Dib — design notes (the anthem)

Composition document for review before writing `generate_muaddib.py`.
The companion song to *Sihaya*: same songbook, same voice engines, same
song-form doctrine — but **more energy**, and the intimacy inverted.
Sihaya was two people alone; this is the sietch singing one man's name.
A **call-and-response anthem**: the leader sings, the crowd answers.
Reference: the acclamation scenes in Dune (the crowd taking up
"Muad'Dib!"), work-song / shanty call-response structure, *Inama
Nushif*'s bigger choral moments.

Story: the first worm ride. The thumper is planted, the maker comes,
the young leader mounts — and the watching sietch sings him up.

- Length ~5:00 (148 bars at 124 BPM, 4/4, bar ≈ 1.94 s) — flexible, as
  agreed; take the bars the material needs.
- Key: D Phrygian dominant, chorus resolving to the major D triad (the
  Sihaya move). One progression family throughout.
- Seed: `np.random.default_rng(12)  # twelve voices in the crowd`.
- Output: `/workspace/music/muaddib.wav`.

## What this adds over Sihaya (the energy)

1. **Tempo + groove**: 124 BPM (vs 96) on an **ayyub-style gallop** —
   the classic Arabic "camel rhythm": DUM..ka DUM-tek driving pattern,
   doum landing on 1 and the and-of-2, teks answering. Momentum from
   bar 4; no settle-in.
2. **The crowd** (the one new instrument, see below): mass sung
   answers, not a chant pad. The chorus is *sung by everyone*.
3. **War drums from chorus 1** (Sihaya saved them for chorus 2), frame
   drum driving 8ths in the pre-choruses, battle-tom fills as the
   section glue instead of frame rolls alone.
4. **Thumper as the tick**: the album's bone-dry pulse element, in
   character — a dry knock at exactly half-time (the planted thumper),
   constant through the bridge the way night_pursuit's clock owns its
   breakdown.
5. Verses ride the full groove (only the bridge breathes) — the energy
   floor is a working groove, not fingerpicking.

## The crowd voice (new instrument work)

`sing_phrase` massed — the Choir of Sietch Tabr recipe applied to the
NEW singing engine instead of the chant: render one sung line 8–10×
with per-voice detune (±0.6 %), onset jitter (±50 ms), formant scatter
(±4 %), and mixed male/female engines (6 male low + 4 female octave),
spread wide L/R. Wet (0.5) and slightly dark — the crowd is around
you, the leader is close and dry. Cache per line; it is expensive.

**One small solo-voice upgrade — 'm' onsets**: start a note as the hum
variant (closed "u", lp 1400) and crossfade into the open vowel over
~80 ms — no new machinery, just windowing we already have. This makes
the hook word land: **"Muad'Dib" ≈ m(u)–a–i** — a real, recognizable
word from vowels + hum + the existing breath-'h'. (Full consonants
remain idea C7.)

## Lyrics & language — the ground rules

Recorded here so it carries into every vocal track from now on:

- **Names and nature only.** Hook words are canon names ("Muad'Dib",
  "Sihaya", "Shai-Hulud") and desert imagery — sand, wind, water, moon,
  the ride. Nothing liturgical, no battle slogans, no real-world
  religious or political phrases. (Specifically: the canon war cry
  "Ya hya chouhada" is real Arabic about martyrs — we do NOT set it.)
- Verses stay **vowel-language** (Fremen-ish, meaning-free) for now —
  per review, melody first; real semantic lyrics wait for the C7
  experiments, and when they come the same rules apply.
- The acclamation frame is safe by construction: a crowd singing a
  person's name is pop's oldest chorus.

## Question / answer — the three levels

1. **Inside the melody**: as Sihaya — every phrase an antecedent
   (ending off-tonic, here often on the ayyub's pushed and-of-2) and a
   consequent resolving to D, same rhythm both halves.
2. **Between performers — now literal call-and-response**: the leader
   sings a line, the CROWD answers it — in the verses an exact echo of
   his tail (the work-song move), in the choruses the full hook. Chani
   is the first answering voice: she leads the crowd in, one beat
   ahead of them (the lieutenant of the response). Instrument echoes
   (oud for him, ney for her) still stitch the phrase tails.
3. **Between sections**: solo verse asks, crowd chorus answers. The
   bridge asks with the album's oldest voices — the thumper knocks,
   the WORM RUMBLE answers from below (nature's reply), the leader
   calls alone — and Chani answers by quoting **the Sihaya hook**
   (their private song inside the public anthem) before the crowd
   returns with the biggest chorus.

## The hook

Chorus refrain on the name: **m(u)–a–i / m(u)–a–i / m(u)–a–a–i** —
"Muad'Dib, Muad'Dib, Mu-ad-di-b" — question half rising to hang on A/G,
answer half falling F#–E♭–D (the album cadence), sung by the crowd,
leader descanting above in the final choruses. Verse melodies low and
driving (D3–A3 leader register), same-rhythm Q/A pairs as Sihaya.

## Harmony — one progression family

Same chord set (D / E♭ / Cm / Gm, Gurney voicings):

- Verse: `D | D | Cm | D` ×2, second pass `Gm | E♭ | Cm | D` — more
  tonic-pedal than Sihaya's verse (anthems sit on the root and drive).
- Pre-chorus: `Gm | E♭ | Cm | E♭` (unchanged — the songbook's lift).
- Chorus: `D | E♭ | Gm | D` (unchanged — the Sihaya cell; the two
  songs share their chorus harmony deliberately: one songbook).
- Bridge: `Cm | E♭` oscillation, avoiding D until the return.

## Structure (148 bars, ~5:00)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | intro (4) | The thumper starts knocking. Wind low. Bar 2: the crowd hums the hook once, far off (wet, quiet) — the name before the man. Groove pickup fill in bar 3. |
| 4 | 0:08 | verse 1 (16) | Full ayyub groove + bass from the downbeat. The leader sings two Q/A pairs; the CROWD echoes each tail (2-beat exact echoes), oud doubling them. |
| 20 | 0:39 | pre-chorus (8) | Leader/Chani 1-bar trades over the rising bass line; frame drum to 8ths; tom fill + her pickup into — |
| 28 | 0:54 | **CHORUS 1** (16) | The crowd sings the hook 4×, leader answering the tails. War drums enter on the cell downbeats. |
| 44 | 1:25 | verse 2 (16) | Chani leads (varied tune, new vowel-words), the leader AND crowd echo alternate tails — the response grows. |
| 60 | 1:56 | pre-chorus (8) | Trades in canon (her one bar behind), both landing the pickup together. |
| 68 | 2:11 | **CHORUS 2** (16) | Leader + Chani in octaves over the crowd; battle toms; hook count ~10. |
| 84 | 2:42 | bridge (16) | Strip one layer per bar to thumper + wind + drone. The WORM RUMBLE answers the thumper from below (bars 88, 92 — approaching). The leader calls alone, unanswered — then **Chani quotes the Sihaya hook** (bars 94–97), the private answer. Strings + riser + tom roll build 98–99, cut on the last beat: |
| 100 | 3:13 | the silent beat | Near-silence; the crowd's lone pickup breath hangs in it ("mu—"), then: |
| 100.25 | 3:14 | **CHORUS 3** (16) | Everything slams on the downbeat — the ride begins. Ney descants answer every cell. |
| 116 | 3:44 | **CHORUS 4** (16) | The everything-chorus: crowd + leader + Chani; **Theme A on the duduk as counter-line** (the album theme under the name — same fusion move as Sihaya's chorus 4, now over a gallop); doubled war drums. Last line stretched ritardando across the seam. |
| 132 | 4:15 | outro (16 + tail) | The groove thins but RIDES OUT (he doesn't dismount — the gallop and thumper fade into distance over 8 bars rather than stopping); the crowd hums the name once more, far off, as at bar 2. Wind tail, fade. |

Verify (script prints): hook count ≥ 14; per-section RMS ordering —
verse1 < chorus1, chorus1 > pre-chorus1, chorus2 > chorus1, chorus4
loudest, bridge trough quietest, outro settling; seam checklist per
boundary (pickup / ring / fill / echo).

## The band (all reuse)

Thumper (new 2-line recipe: dry wood-knock — muffled frame-drum hit,
no reverb, half-time), ayyub darbuka + doum/tek/ka, frame drum, war
drums + battle toms, gated sub bass (busier pattern: root 8ths with
the ayyub push), oud (verse echoes + chorus riff), baliset (strummed
choruses only — this song doesn't fingerpick), duduk (Theme A,
chorus 4), ney (descants), leader voice + Chani (sihaya engines,
verbatim), the crowd (above), tremolo strings (pre-chorus/bridge),
wind + D drone frame, riser, worm rumble (arrakis recipe, bridge only).

## Rules carried in

All of Sihaya's: one continuous cursor + vocal wander; CHORD_MAP as
the single harmony source; identical refrain vowels every chorus;
seam device at every boundary; anti-tinnitus (crowd/strings pulse to
silence); drone low; standalone script, seeded, WAV to
/workspace/music, stage don't commit.

## Open questions for review

1. **Title/hook word**: "Muad'Dib" (m-onset makes it land; a name
   being acclaimed is the natural anthem) vs "Shai-Hulud" (a-i-u-u,
   darker — the song becomes about the worm, and the crowd part reads
   as awe rather than acclaim)? I recommend Muad'Dib.
   + User answer: Yes, Muad'Dib is good.

2. **Kick**: none (war drums + doum carry the low end — organic
   anthem, my recommendation) vs a soft 4-on-the-floor kick in
   choruses 3–4 only (pushes it toward the psy tracks, bigger but
   less "sung")?
   + User answer: Let's try a kick - makes it more powerful!

3. **Groove feel**: straight-4/4 ayyub gallop at 124 (recommended —
   fits the existing grid machinery) vs a true 12/8 triplet gallop
   (kanly's hoofbeat feel, more distinctive, but every pattern and
   the bar grid change)?
   + User answer: let's go 4/4.

4. **The Sihaya quote in the bridge** (Chani answering the lone call
   with their private hook): keep, or keep the bridge purely this
   song's material?
   + User answer: let's keep the bridge simple, not any new hook there.
