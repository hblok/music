# Sihaya — design notes (the song)

Composition document for review before writing `generate_sihaya.py`.
This is the album's first actual **song** — not a soundtrack cue, not a
psy arc: verse / chorus / bridge form, a refrain the listener can hum
after one listen, and question-and-answer running through every level of
the arrangement. Reference: *Inama Nushif* from the Children of Dune
miniseries — a sung piece in an invented language, sitting inside a
score, with a female vocal carrying a refrain. Ours is a **duet**.

*Sihaya* — "desert spring", Paul's name for Chani. He sings the verses;
she answers. The chorus is the two of them.

- Length ~5:50 (140 bars at 96 BPM, 4/4, bar = 2.5 s).
- Key: D Phrygian dominant. Verses lean on the dark side of the mode
  (Cm, Gm, the E♭); every chorus resolves home to the **major** D triad
  (D–F♯–A) — the question/answer built into the harmony itself.
- Seed: `np.random.default_rng(2)  # two voices, two moons`.
- Output: `/workspace/music/sihaya.wav`.

## Why this track (what it fixes)

Direct response to the standing feedback:

1. **Cohesion** — one chord-progression family, one fixed instrument
   palette, one hook. Sections differ by density, register and who is
   singing — never by swapping the musical language.
2. **Question and answer** — designed in at three levels (see below),
   not sprinkled on.
3. **Repetition** — the refrain is sung **four times** with identical
   melody and identical vowel-"lyrics"; the hook cell appears 12+ times
   across the track. Repetition is the point, not a failure of
   invention.
4. **No seams** — one continuous bar cursor from 0:00 to the end; every
   section boundary is crossed by a pickup, a ringing chord, or a fill.
   Nothing starts from silence, nothing stops dead (except the one
   deliberate silence-drop before the final chorus — a composed event,
   not a seam).
5. **Breath to develop** — verses are 16 bars, the bridge tears down
   *gradually* and builds back *gradually*. No 4-bar drive-by ideas:
   every motif that appears gets stated, varied, and answered.

## The two voices (the new instrument work)

Promote the litany's whispered vowel formants + the chant's glottal
source into **sung lead voices**. This is the track's one big new
recipe; everything else is reuse.

**PAUL (male lead)** — glottal source (14 harmonics, 1/k^0.8) like
`chant_note`, but *melodic*: per-note portamento (one-pole smoothed
pitch curve, ~70 ms — the duduk trick), vibrato blooming over ~0.8 s
(5 Hz, 0.5 %), phrase-shaped envelope. Formant filtering swaps the
chant's fixed dark "oh" for **vowel trajectories**: the litany VOWELS
table (i/e/a/o/u), f1/f2 **interpolated** between vowels across the
note — a singer moving through a word, not a filter switch. Register
D3–D4. Remove the 5.5 Hz guttural pulse (he sings, he doesn't chant).

**CHANI (female answer)** — same engine, one octave up (D4–D5),
formant frequencies scaled ×1.18 (shorter vocal tract), softer source
(1/k^1.2 — fewer high harmonics), +breath: 15 % of 2–5 kHz bandpassed
noise riding the same envelope (the ney's breath trick). Slightly
faster, shallower vibrato (5.8 Hz, 0.35 %). She reads as brighter, airier,
younger — unmistakably the *other* voice.

**"Lyrics"** — vowel sequences only, fixed per line so repeated lines
read as repeated *words*. Soft 'h' onsets for free by crossfading
breath-noise → voice over the first 60 ms of a phrase. No hard
consonants (out of scope — note as a future upgrade if the voices prove
out). The refrain "text" is the title: **i–a–a** ("si-ha-ya"), one
vowel per hook note, identical in all four choruses.

**Duet mixing** — Paul slightly left (pan −0.12), Chani slightly right
(+0.12), both fairly dry (wet ≤ 0.25 — they are close, this is
intimate); the 12-voice choir, when it enters, is wide and wet behind
them.

## Question / answer — the three levels

**Level 1 — inside the melody.** Every vocal phrase is an
antecedent/consequent pair: 2-bar *question* ending off-tonic (on A, or
hanging on the E♭), then 2 bars with the same rhythm and contour
*answering* onto D. The hook itself is a Q/A cell: `A–B♭–A–G (question)
/ F♯–E♭–D (answer)`.

**Level 2 — between performers.** After every sung line, an instrument
echoes the line's tail — a composed echo, not a delay: oud echoes Paul
in the verses, ney echoes Chani in the choruses, one octave up, entering
on the phrase's last note so the echo overlaps the singer's release
(this is also what stitches phrases together — no dead air between
lines). In verse 2 the roles swap: she leads, *he* echoes.

**Level 3 — between sections.** Verse (one voice, dark chords, low
register) *asks*; chorus (both voices, home-major resolution, high
register) *answers*. The bridge asks the album's oldest question —
Theme A, unresolved fragments — and the final double chorus answers it
with the full hook over Theme A as a counter-line.

## Harmony — one progression family

Reuse **Gurney's chorus progression** (this song and Gurney's Song are
the same songbook — the album's "performed" music):

- Verse: `D | Cm | D | Gm` ×2, second pass closing `E♭ | E♭ | Cm | D` —
  the half-close on Cm/Gm is the harmonic "question".
- Pre-chorus: `Gm | E♭ | Cm | E♭` — rising bass line G→E♭... tension
  that only the chorus D can release.
- Chorus: `D | E♭ | Gm | D` ×2 (the E♭ shimmer against the major D is
  the album's whole flavor in two chords) — closing `Cm | E♭ | D | D`.
- Bridge: oscillate `Cm | E♭` only — deliberately avoiding D so its
  return at the final chorus lands as *arrival*.

## Structure (140 bars, ~5:50)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | intro (4) | Baliset arpeggio on the chorus progression + low wind. Bar 3: Chani hums the hook once, half-voice ("i–a–a") — the song's thesis stated in the first 10 seconds. Her last note carries over the verse downbeat. |
| 4 | 0:10 | verse 1 (16) | Paul sings, two Q/A phrase-pairs; oud echoes each tail. Band: baliset fingerpicking, gated sub bass on roots, frame drum sparse (beats 1 & 3). Chani is silent — save her. |
| 20 | 0:50 | pre-chorus (8) | 1-bar trades: Paul asks / Chani answers, twice; then both voices rising together with the bass line. Frame-drum roll (the standard launch gesture) fills the last bar; her pickup note leads across the barline — |
| 28 | 1:10 | **CHORUS 1** (16) | The refrain. Hook sung 4× (Paul 2×, Chani answering 2× an octave up), ney echoing her tails. Full maqsum darbuka enters at chorus start, choir pad quiet underneath. Last chord rings across the verse-2 boundary. |
| 44 | 1:50 | verse 2 (16) | Roles swapped: **Chani leads**, Paul echoes (level-2 answer, inverted). New melody detail over the same progression = "second verse, different words". Darbuka stays but drops to half density — the groove never fully leaves after chorus 1. |
| 60 | 2:30 | pre-chorus (8) | As before, but voices in canon 1 bar apart instead of trading — a development, not a repeat. |
| 68 | 2:50 | **CHORUS 2** (16) | Bigger: both voices in parallel octaves the whole way, war-drum accents on phrase downbeats, choir now clearly audible. Hook count so far: ~10 statements. |
| 84 | 3:30 | bridge (20) | The teardown-and-build. Bars 84–91: layers strip one per bar (darbuka → bass → choir...) down to baliset + wind; **Theme A appears on the duduk** — the album's theme drifting through the song, quiet, in fragments that never resolve (the question). Bars 92–103: rebuild — bass returns, voices hum wordless Theme A fragments in alternation, riser + snare-buzz crescendo over the last 4 bars, ending in — |
| 104 | 4:20 | the drop-silence | **One beat of near-silence** (room tone only — the composed cut), then: |
| 104.25 | 4:21 | **CHORUS 3** (16) | Full band slams in on beat 2. Both voices in harmony (she a third above where the mode allows, octave elsewhere). |
| 120 | 4:41 | **CHORUS 4** (16) | The everything-chorus: hook doubled by choir, **Theme A on the duduk as counter-line** under the refrain (the album's question finally answered by the song's hook, sounding *together*), ney descant answers every line. Last line repeated with a ritardando tail (rubato warp on the final 2 bars). |
| 136 | 5:21 | outro (4+tail) | Layers strip fast; baliset arpeggio as the intro, Chani hums the hook once more, half-voice, unaccompanied — the bookend. Final D strum rings ~6 s into wind. ~10 s wind tail, fade. |

RMS shape to verify (print per-section): intro < verse1 < chorus1;
chorus2 > chorus1; bridge trough is the quietest point after the intro;
chorus4 is the loudest section of the track; outro back to intro level.
Also print the hook-statement count (target ≥ 12) and every section
boundary with what crosses it (pickup / ring / fill) — the no-dead-seams
checklist, verifiable without listening.

## The band (all reuse)

Fixed palette, present (in varying density) from verse 1 to the outro —
no instrument appears for one section only:

- **Baliset** (gurneys_song recipe, triple-course KS + body IR) —
  the song's harmonic bed, fingerpicked verses, strummed choruses.
- **Oud** — verse echo voice + chorus riff doubling.
- **Gated sub bass** (tanh-warmed, night_pursuit recipe) — roots,
  sidechain-free (this is a song, not psy; no pump).
- **Frame drum + maqsum darbuka** — sparse verse → full chorus. Fills
  are the section-boundary glue.
- **War drums** — chorus-2+ downbeat accents only.
- **Duduk** — Theme A carrier (bridge, final chorus counter-line).
- **Ney** — Chani's echo/descant.
- **12-voice choir** (`mass_chant_note`) — chorus pad, wide and wet.
- **Tremolo strings** — pre-chorus and bridge-build tension bed, low.
- **Wind + D drone** — album continuity at the frame (intro/outro,
  under the bridge trough). Drone kept LOW and quiet per the
  drone-bed rules — under a song it is set dressing, not a bed.

## Rules carried in

- One continuous bar cursor; slight rubato warp (±25 ms slow_noise on
  vocal onsets, ritardando only in the final chorus tail and outro).
- Anti-tinnitus: choir and strings pulse to silence; ney descant is
  phrase-length, never sustained.
- No vacuum-cleaner drone; verify the drone layer's RMS share stays
  small.
- Chorus vowel-lyrics identical every time; verse vowel-lyrics differ
  per verse (same rhythm) — "same tune, different words".
- Standalone script, duplicated helpers, seeded, WAV to
  /workspace/music/, stage in git, no commit without asking.

## Open questions for review

1. **Chorus melody**: new hook with Theme A as bridge/final-chorus
   counter-line (as planned above), or make Theme A itself the chorus?
   I recommend the new hook — Theme A has been stated in five tracks
   already; here it works better as the *answered question*, and the
   fusion of both in chorus 4 is the payoff.
   + User Answer: Yes, let's have a new hook with Theme A.


2. **Female voice register**: full octave above Paul (cleaner, more
   anthemic) vs. mostly a third/sixth above (warmer, more duet-like)?
   Planned: octave in choruses, thirds only in chorus 3–4 moments.
   + User Answer: let's go full octave above.

3. **Length**: 5:50 as planned, or trim verse 2 / bridge to land ~5:15
   if the vowel voices can't carry that much lead time?
   + user Answer: not strict limit or min/max time. Let's just take the time we need. If it's 6 min, that's fine.

4. Consonants: skip for now (vowels + breath-'h' only) — agreed?
   + User Answer: Yes, let's stick with vowels
   
