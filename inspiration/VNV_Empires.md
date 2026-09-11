# VNV Nation — *Empires* (1999): the track-by-track blueprint

*Third doc in the EBM set. `EBM_1990s.md` covers the genre and names
VNV as one of its two poles; `Apop_Soli_Deo_Gloria.md` pins the 1993
dark-electro Apop. This one pins **VNV's 1999 record** so its sound can
be captured on its own terms. Written 2026-09-11. Facts marked
**[verified]** come from the sources at the end (Wikipedia, the Discogs
public API, four reviews). Everything else is characterisation from
those reviews and from the gear — **no audio was measured**; §7 lists
the inspector runs that settle each open number.*

**Read §5 before writing a note doc from this.** *Empires* is the
record that named futurepop, and this repo has an explicit standing
warning about that DNA (`tracks/ebm/CLAUDE.md`, "the Frankfurt-trance
trap"). §5 splits the album into what to take and what to leave.

---

## 1. The record [verified]

| | |
|---|---|
| Released | 25 October 1999 (EU, Dependent, cat. **mind 008**, CD, Germany); 16 May 2000 (US, Metropolis) |
| Length | 50:58, 10 tracks |
| Recorded | **Polaris Studios, Hoxton, London — August–September 1999** |
| Produced | "Produced, Constructed By, Performed" — VNV Nation |
| Engineer | Paul Barton |
| Artwork | Fross / Nationhood; management Mindbase |
| Chart | US release peaked #6, CMJ RPM |
| Reception | AllMusic 4/5 · Almost Cool 7.5/10 · Metal.de 8/10 · Release Magazine 9/10 |

**The band.** Ronan Harris — writing, programming, production, vocals.
Mark Jackson — the live drummer from 1996; **[contested]** one source
states he never performed on the albums and was credited for "valued
input", while a review of *Empires* credits his drumming on *Darkangel*.
Treat the record as Harris alone at the machines until measured; do
**not** build a "live drummer" mechanism on this.

**Harris on the album.** He called making it "unforgettable" and
"intense", composed in spare time after work and at weekends, during a
period when he felt "lost and lacking direction" — the record served as
"artificial light to guide me". *"When I say to someone that this album
was my salvation, I don't mean that lightly."* On the closer: *Arclight*
names "the first use of electricity in lighthouses, where carbon arc
lighting created the most intensely bright artificial light yet seen."

**The frame.** Roman and Caesarian imagery throughout (*Rubicon*,
*Legion*, *Kingdom*, the title itself) over a cyclical-history theme —
one reviewer reads it as the narrative of someone at the head of a
radical movement they have lost control of, and concludes: *"This album
is not about creating Empires, it is about burning them."* Where Apop's
1993 frame was liturgical, this one is **imperial** — the same solemn
register, a different iconography. Worth knowing when titling.

---

## 2. The 1999 palette — what the gear forces [verified]

Nine machines, listed on the album's own credits:

> **Ensoniq ASR-10 · ARP 2600 · Sequential Circuits Pro One · Oberheim
> OB-1 · Access Virus · E-mu Proteus 2000 · Roland JV-1080 · Roland
> M-OC1 · Korg Trinity Rack**

That list is the whole design brief, and it splits cleanly into three
jobs:

- **Three analog monosynths do the engine.** Pro One, OB-1, ARP 2600 —
  all mono, all one-or-two oscillators with a resonant lowpass. The
  EBM bass in 1999 is *still one analog voice*, exactly as the SH-101
  was in 1993. Nothing here changed. (The Pro One is also the "old
  sequential synthesizer" Harris has said he used on every track of the
  1997 record — the through-line between the two albums.)
- **Four ROM modules do the orchestra.** Proteus 2000, JV-1080, M-OC1
  (Roland's orchestral module) and the Trinity Rack. **VNV's strings,
  brass and choir are sample-ROM patches, not an orchestra** — which is
  why they can be imitated honestly by synthesis, and why they sound
  *stiff and stacked* rather than breathing. This is the single most
  useful fact in the doc. `EBM_1990s.md` §7 guessed "JV-1080/Trinity
  rompler character" from genre knowledge; the credits confirm it.
- **The Virus does the gloss**, and **the ASR-10 does the sampling**.

**The one-knob difference from 1993.** Groth's EPS was 13-bit and mono
with almost no memory, and that grain *is* the *Soli Deo Gloria*
texture. The ASR-10 is 16-bit stereo with far more of it. So in repo
terms the 1999 dialect is the 1993 dialect **with the dirt turned
off**: `_common.dirt(..., hold=1)` and no 13-bit quantise, on every
sampled voice. Nothing else in the kit has to change to move era.

**What is NOT here:** a real orchestra, a guitar, a 303, sidechain
pump, a loudness-war master (1999 is pre-brickwall).

---

## 3. The songs

BPM values are algorithmic tags, **approximate**; §7 measures them.
Durations and order are the 1999 CD [verified].

### 1. Firstlight — 2:10
The overture. "A sickly rich synthetic beat" under an orchestral
composition; "inhuman and unnatural" as an introduction, which one
reviewer ties to the Roman motifs. No club engine.
- **Mechanism:** the thesis stated cold, on the ROM orchestra, at
  album scale — under two and a half minutes, no drums to speak of.
- **Repo shape:** this is `reliquary`'s job, already done once. The
  value here is the *pair* (§4), not another interlude.

### 2. Kingdom — 5:51 · ≈108 BPM
"Heavy bass-beats throb throughout", mechanical industrial weight,
strings over synthesized percussion — and then "the heavens emerge"
in the chorus. One reviewer calls the string writing natural-sounding
and uneasy at once.
- **Mechanism:** **the throb.** A slow, heavy, orchestral EBM song
  where the weight is in the low end and the release is the chorus
  opening upward into strings. The lift is *registral*, not harmonic —
  the chords need not go anywhere for "the heavens" to emerge; the
  orchestra simply arrives an octave up.
- **Repo shape:** ~108 is almost exactly `ruin`'s 109 (the Apop
  hammer, `tracks/ebm/ruin_notes.md`). **Do not build both.** If a
  VNV track comes from *Kingdom*, either space it well away from
  `ruin` in the set or take only its registral-lift device and put it
  on a different tempo.

### 3. Rubicon — 6:20
"Forceful wallop", strong percussion, "a pounding, akin to a heart"
driving it; the theme is the dread before an irrevocable decision.
Reviewers note "slight repetitiveness" across six minutes.
- **Mechanism:** **the heartbeat as the engine** — a percussion figure
  that is a pulse rather than a groove, carrying a long track. Also
  the warning: six minutes of it drew the repetitiveness complaint,
  which is this repo's standing failure mode too.
- **Repo shape:** a heartbeat kick figure (two blows, not four) with
  the phrase built into the filter, per the `ruin` counter-measure.
  Length capped at four minutes.

### 4. Saviour — 6:59
**The one to mine.** Nearly ninety seconds of instrumental ascension
open it; a "jet engine" build; then six minutes of relentless
momentum. The reviewer's phrase is the point: *"warm, compassionate
synthesizers conveying melody without vocals."* Ranked the album's
emotional centrepiece.
- **Mechanism:** **the ascent** — a long instrumental build whose
  melody, not a voice, is the emotional payload, and which then
  sustains momentum rather than dropping into verse/chorus alternation.
- **Repo shape:** this is the most valuable track on the record *for
  this repo specifically*, because the repo is instrumental by
  constitution and here VNV is too. A refrain carried by a warm pad
  stack with no vocal slot to fill or fake. See §6.

### 5. Fragments — 5:02
Aggressive and heavy, reaching back to the harsher 1995 debut; judged
the weakest fit against the album's more refined palette.
- **Mechanism:** the holdover — a harder, older track sitting inside a
  polished record. Low priority.

### 6. Distant (Rubicon II) — 3:15
The reprise: orchestral, pretty, brief; called an intermission, and
faulted for having less substance than its neighbours.
- **Mechanism:** **the second reprise pair** (§4) — a song returned
  later stripped to its orchestra. Note the criticism: a reprise that
  is only prettier, and not *resolved*, reads as filler.
- **Repo shape:** if a reprise is used, it must answer something the
  first statement left open — the rule `reliquary` → `procession`
  already follows.

### 7. Standing — 5:40 · ≈106 BPM
Pop-oriented, symphonic construction, strong progression, the most
mainstream-accessible thing here.
- **Repo shape:** **leave it.** This is the Frankfurt trap wearing a
  slow tempo (§5).

### 8. Legion — 5:11 · ≈134 BPM
Dance-floor: "coiling bass hooks, monk-like chants, and twinkling
synths", tension built and then released into momentum.
- **Mechanism worth keeping:** the **monk chant** — a wordless, static,
  chordal male choir used as a rhythmic-harmonic layer, not a pad. It
  is a ROM patch, so it is stiff and stacked, and that is imitable.
- **Repo shape:** take the chant, leave the club arrangement.

### 9. Darkangel — 5:28 · ≈139 BPM
The lead single (June 1999), aggressive harmony, the album's fastest
and most club-facing track.
- **Repo shape:** **leave it.** 139 with a sung chorus over an arp is
  precisely what `tracks/trance/` already builds nine times over.

### 10. Arclight — 5:00
The closer, and **"essentially the same composition" as *Firstlight***
— but where the opener is 2:10 and beatless, the closer runs five
minutes and grows "a delicate and deliberate house beat" under the same
orchestral material, resolving the record.
- **Mechanism:** the bookend, and specifically the *rule* for how the
  second statement differs: **same material, a beat added, more time.**
- **Repo shape:** §4.

---

## 4. The two pairs — the album as one piece

*Empires* bookends itself twice:

```
Firstlight ........................................... Arclight
  (2:10, orchestral, beatless)        (5:00, same music, + a beat, resolved)

              Rubicon ................. Distant (Rubicon II)
              (6:20, the pounding)     (3:15, orchestral, stripped)
```

One pair spans the whole record; the other spans its middle. Both are
the doctrine's thesis/bookend device (`tracks/trance/idea.md`), and the
Apop record does the same thing with *Like Blood From The Beloved* Part
1 and Part 2 — **two different 1990s EBM records, independently, build
themselves as a statement and its return.** That is now three
independent confirmations of the device this directory already uses.

The two pairs differ in how the return earns itself, and the reviews
are unanimous on which works:

| pair | what changes on the return | verdict in the reviews |
|---|---|---|
| Firstlight → Arclight | a beat arrives; the piece is given twice the length; it resolves | praised — "peaceful resolution to the emotional journey" |
| Rubicon → Distant | stripped to the orchestra, prettier, shorter | faulted — "insufficient substance" |

**The lesson, stated as a rule:** *a return must add a mechanism, not
subtract one.* `procession`'s bookend already does this (Part 1 ends
open on the V; the outro resolves to A) — this is the external
confirmation.

---

## 5. What to take and what to leave (read this first)

*Empires* is the record that named futurepop, and `tracks/ebm/CLAUDE.md`
carries a standing warning that futurepop DNA — arpeggiated sequence,
tenor lead with vibrato and chorus, updown contour, the ♭VII lift —
turns a dark EBM track into a Frankfurt trance track. That DNA is on
this album, concentrated in three songs. So:

**Take:**

1. **The ascent** (*Saviour*) — melody without vocals as the emotional
   centre. The repo's native shape, validated by the genre itself.
2. **The bookend rule** (*Firstlight* → *Arclight*) — same material,
   plus a mechanism, resolved.
3. **The ROM orchestra** (§2) — strings, brass and choir as stiff,
   stacked sample patches rather than a breathing ensemble.
4. **The registral lift** (*Kingdom*) — the chorus opens by moving the
   orchestra up an octave, not by moving the harmony to a ♭VII.
5. **The monk chant** (*Legion*) — static, wordless, chordal.
6. **The heartbeat engine** (*Rubicon*) — a pulse, not a four-on-floor.
7. **The imperial frame** — solemn and civic where Apop's was
   liturgical. Titles from Rome, ruin and cycles, not from the Mass.

**Leave:**

1. **The three club singles' arrangements** — *Darkangel* (139),
   *Legion* (134) and *Standing*'s pop construction. The tempos alone
   collide with nine tracks in `tracks/trance/`.
2. **The supersaw lead over a 16th arp.** The Virus is on the credits;
   its most era-typical patch is the trap.
3. **The sung-chorus destination.** This repo fills the vocal slot
   instrumentally, and *Saviour* proves the album itself can.
4. **Six-minute lengths.** Both long tracks drew repetitiveness
   complaints in the reviews; the directory's own last two verdicts
   said the same thing about its own tracks.

---

## 6. Translation to this repo

**Where it lives:** `tracks/ebm/`, as its **1999 dialect** — a third
alongside the 1993 dark-electro tracks and the futurepop hinge that has
never been built. Same conventions: the shared `instruments/` library,
`LISTENING.md` flags, printed verify per `tracks/VERIFY.md`, English
titles, FLAC + WAV to `/workspace/music/`, never commit audio.
Seeds, thematically: **1999**, **8** (cat. mind 008), **50**.

**The kit** — what already exists and what one 1999 track would need:

| element | library module | change for 1999 |
|---|---|---|
| bass | `sh101_bass` | as is, but voiced Pro One rather than SH-101: two oscillators, less resonance (Q ~1.8), **`hold=1`** |
| kick / snare / hats | `eps_kick`, `eps_snare`, `hats` | **dirt off** (`hold=1`, no 13-bit) — this alone moves the era |
| chopped hit | `eps_hit` | `hold=1`: a clean orchestral stab, not a truncated 13-bit one |
| pads, stabs, organ | `juno` | the Virus stands in: the same saw/pulse + SVF engine with `depth=0.0` (no Juno chorus) and a brighter cutoff. Declare the substitution rather than writing `virus.py` |
| refrain carrier | `dark_lead` | Harris is a baritone; the existing range already fits. For the *Saviour* shape, a warmer, more sustained variant — a knob, not a module |
| bed | `seethe` | as is |
| **the ROM orchestra** | `rom.py` | **written 2026-09-11**, one module with two entry points: `strings` (5 detuned saws per note, 0.3 s attack, a bright bow layer, no sample-loop flutter — `ungeschrieben`'s flutter is owned) and `choir` (the same stack through three formants, static and chordal, octave-doubled, **no drift and no breath** — `adrift`'s breath choir is owned). The detune phases are fixed, so the patch is stiff by construction. `juno.pad_loop` takes either voice unchanged |
| master | big-room chain | 1999 is pre-loudness-war: lighter duck (≤ 0.35), pads only, never the refrain carrier |

**One new module, written; everything else is a knob.** The blueprint
first called for two, but `strings` and `choir` share one detuned-stack
core, which is how `eps_hit` already handles its two kinds. No separate
warm-lead voice either: the ascent's refrain carrier is `strings` on a
single note until a probe says otherwise. `demo_rom.py` is the test of
the whole premise. That makes this the cheapest new dialect this
directory can open.

**Track archetypes, best first:**

| archetype | model | shape | why |
|---|---|---|---|
| **the ascent** | *Saviour* | a long instrumental build to a warm pad-stack refrain, then sustained momentum | the repo is instrumental; so is this track. The highest-value target on the record |
| **the throb** | *Kingdom* | ~108, heavy low end, chorus lifts the orchestra an octave | strong, but collides with `ruin` (109) — space them or move one |
| **the pulse** | *Rubicon* | a heartbeat figure carrying the engine, capped at four minutes | good device, proven failure mode; the cap is the fix |
| *(avoid)* | *Darkangel*, *Legion*, *Standing* | club singles | §5 |

**Verify additions** (on top of the standard set and the EBM checks in
`EBM_1990s.md` §12):

- **the dirt ledger** — every sampled voice's `hold` and `bits`
  printed, asserting `hold == 1` and no quantise. The receipt that a
  1999 track has not drifted back into 1993.
- **the bookend rule** — if the track uses a return, the return must
  add a named mechanism, printed (`Arclight` rule: same material, plus
  a beat, resolved).
- **the lift is registral** — the chorus's median orchestral pitch is
  at least an octave above the verse's, and the chord roots are
  unchanged (the anti-♭VII check, stated as a measurement).
- **no supersaw lead over a 16th arp in the same section** — a cheap
  structural assertion against the trap.
- **the instrumental centre** — for an *ascent* track, the refrain
  carrier is a pad or lead, and its first full statement lands inside
  the first third of the track.

---

## 7. Calibration — the inspector runs that settle the open numbers

No audio was measured. BPM tags found: *Kingdom* 108, *Standing* 106,
*Legion* 134, *Darkangel* 139; the album is tagged ~128 average across
a 76–144 range. Nothing else is known — no keys at all.

With files under `/workspace/music/refs/empires/`, from `/repos/music`:

```bash
for f in /workspace/music/refs/empires/*.flac; do
  n=$(basename "$f" .flac)
  python3 -m inspector.analyse "$f" --plots --out "inspiration/empires_refs/$n.md"
done

# the three archetypes, stems for the engine, the orchestra and the register
python3 -m inspector.analyse /workspace/music/refs/empires/04_saviour.flac --start 0 --end 100 --separate \
    --stems-out /workspace/music/refs/empires/saviour_stems --out inspiration/empires_refs/saviour_ascent.md
python3 -m inspector.analyse /workspace/music/refs/empires/02_kingdom.flac --start 60 --end 90 --separate \
    --stems-out /workspace/music/refs/empires/kingdom_stems --out inspiration/empires_refs/kingdom_chorus.md
python3 -m inspector.analyse /workspace/music/refs/empires/03_rubicon.flac --start 60 --end 90 --separate \
    --stems-out /workspace/music/refs/empires/rubicon_stems --out inspiration/empires_refs/rubicon_pulse.md
```

| track | tagged | measured BPM | key | bass cell | percussion figure | lead/vocal range |
|---|---|---|---|---|---|---|
| Firstlight | — | | | — | | — |
| Kingdom | 108 | | | | | |
| Rubicon | — | | | | | |
| Saviour | — | | | | | |
| Fragments | — | | | | | |
| Distant (Rubicon II) | — | | | — | | — |
| Standing | 106 | | | | | |
| Legion | 134 | | | | | |
| Darkangel | 139 | | | | | |
| Arclight | — | | | | | |

**The specific questions the stems answer:** (1) *Saviour*'s first 90
seconds — what actually carries the melody, and how many layers; (2)
whether *Kingdom*'s chorus lift is registral or harmonic (the §5 claim,
and the one most worth being wrong about); (3) *Rubicon*'s "heartbeat"
— the literal kick figure; (4) whether *Arclight* really is *Firstlight*
re-stated, note for note, plus a beat; (5) Harris's 1999 register
against `dark_lead`'s range; (6) whether the bass is one mono voice
throughout, as the three-monosynth credit implies.

---

## Sources

- Wikipedia, *Empires (VNV Nation album)*: release data, recording,
  the equipment list, the Harris quotes, reception.
- Discogs release 119437 (public API): tracklist with durations,
  label and catalogue number, credits, the Polaris London note.
- Vanyaland, *Ranking the songs of VNV Nation's 'Empires,' on its 15th
  anniversary* (2014): the per-track characterisations, the
  Firstlight/Arclight identity, the *Saviour* description.
- University Observer, *OTwo Reviews: Empires by VNV Nation* (Jonathan
  Daleo): the Roman/Caesarian frame, *Rubicon*'s heartbeat, the
  closing line quoted in §1.
- GetSongBPM / songbpm tags for the four BPM values (algorithmic —
  hence §7).
- Last.fm artist wiki and search results for the Mark Jackson credit
  question, flagged **[contested]** in §1.
