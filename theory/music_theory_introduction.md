# An Introduction to Music Theory

For people who think clearly about systems and have little or no prior
musical experience.

---

## 1. The Raw Material: Pitch

Sound is vibration. Pitch is how fast the vibration is — its frequency.
Faster vibration = higher pitch. Slower = lower.

Humans can hear roughly 20 Hz to 20,000 Hz. But music doesn't use the
whole range arbitrarily. It uses a small, carefully chosen set of
frequencies — **notes** — and the relationships between them is what
music theory is about.

---

## 2. The Octave: The Most Important Relationship

If you double a frequency, the result sounds uncannily similar to the
original — just "higher". This relationship is called an **octave**.

- 110 Hz → feels like one pitch
- 220 Hz → feels like the "same" pitch, one octave up
- 440 Hz → same again, one octave higher still
- 880 Hz → and again

This doubling relationship is so fundamental that every musical culture
independently discovered it. Notes an octave apart are considered
*equivalent* — they have the same name and the same role in music.

The distance between 110 Hz and 220 Hz, and between 220 Hz and 440 Hz,
are both "one octave" — even though the first spans 110 Hz and the second
spans 220 Hz. Octaves are a *ratio*, not a difference. The ear hears
ratios.

---

## 3. Dividing the Octave: The 12 Notes

Western music divides each octave into **12 equal steps**. These steps
are called **semitones** (or half steps). Because the ear hears ratios,
"equal" here means each step is the same *multiplying factor*:

```
Each semitone = multiply frequency by 2^(1/12) ≈ 1.05946
```

Twelve of these steps gets you exactly back to double the frequency —
one octave higher.

These 12 steps have names. Seven get letter names (A B C D E F G), and
the five in between are called **sharps** (#) or **flats** (b),
depending on context:

```
C  C#  D  D#  E  F  F#  G  G#  A  A#  B  C
   Db     Eb        Gb     Ab     Bb
```

The sequence repeats — after B comes C again, one octave up.

A few things to notice:
- There is no sharp/flat between E and F, and none between B and C.
  Those pairs are naturally only one semitone apart.
- C# and Db refer to the *same frequency* — the name depends on context.
- The pattern repeats identically in every octave.

---

## 4. Naming Specific Notes: Octave Numbers

To refer to a specific pitch, not just a note class, you add an octave
number: **C4** is "middle C", the C near the middle of a piano.
**A4** = 440 Hz is the standard tuning reference.

Going up: C4, D4, E4, F4, G4, A4, B4, C5, D5 … (the octave number
increments at C).

---

## 5. Intervals: The Distance Between Notes

The distance between any two notes is an **interval**, measured in
semitones. Intervals have traditional names:

| Semitones | Name | Example |
|-----------|------|---------|
| 0 | Unison | C → C |
| 1 | Minor 2nd | C → C# |
| 2 | Major 2nd | C → D |
| 3 | Minor 3rd | C → Eb |
| 4 | Major 3rd | C → E |
| 5 | Perfect 4th | C → F |
| 6 | Tritone | C → F# |
| 7 | Perfect 5th | C → G |
| 8 | Minor 6th | C → Ab |
| 9 | Major 6th | C → A |
| 10 | Minor 7th | C → Bb |
| 11 | Major 7th | C → B |
| 12 | Octave | C → C (next) |

The names are old and somewhat arbitrary, but they come up constantly
in musical descriptions so they're worth learning by the numbers.

**Why do intervals matter?** Because two notes played together sound
consonant (pleasant, stable) or dissonant (tense, unstable) based on
their interval. The most consonant intervals are the octave (12), the
perfect fifth (7), and the perfect fourth (5). The tritone (6) is the
most dissonant — it was historically called *diabolus in musica*
(the devil in music).

---

## 6. Scales: Choosing a Subset of the 12

Playing all 12 notes has no particular character — it's chromatic, flat,
undifferentiated. Music gains character by choosing a **subset** of the
12 notes to work within: a **scale**.

A scale is defined by a pattern of intervals (semitone steps) starting
from a chosen root note. The two most important scales:

### The Major Scale

**Pattern:** 2 – 2 – 1 – 2 – 2 – 2 – 1 (semitone steps between consecutive notes)

Starting from C:
```
C   D   E   F   G   A   B   C
  2   2   1   2   2   2   1
```

The major scale sounds bright, resolved, "happy" to most listeners.
This is the "do re mi fa sol la ti do" scale.

### The Natural Minor Scale

**Pattern:** 2 – 1 – 2 – 2 – 1 – 2 – 2

Starting from A:
```
A   B   C   D   E   F   G   A
  2   1   2   2   1   2   2
```

The minor scale sounds dark, melancholic, unresolved. Starting from D:
```
D   E   F   G   A   Bb  C   D
  2   1   2   2   1   2   2
```
This is D minor — D, E, F, G, A, Bb, C.

### The Key

The starting note is called the **tonic** or **root**, and gives the scale
its name. When a piece of music is "in D minor", it mostly uses those seven
notes, and most phrases feel like they want to return to D as home.

A **key** and a **scale** are almost the same concept: the scale is the
abstract pattern, the key is the pattern anchored to a specific note.

---

## 7. Relative Major and Minor

Here is something elegant: every major scale and one specific minor scale
share *exactly the same set of notes* — only the starting point differs.

**C major** uses: C D E F G A B  
**A minor** uses: A B C D E F G

Same seven notes. The difference is only which note feels like "home".
In C major, C is home; in A minor, A is home.

This pair is called **relative** major and minor. To find the relative
minor of any major key, go down 3 semitones (or equivalently, up 9 semitones).

**Why does this matter in practice?** A piece of music can slide between
C major and A minor without introducing any new notes, just by shifting
where it *resolves* (lands). This creates the ability to move between
"bright" (resolving to C) and "melancholic" (resolving to A) with zero
change in the note vocabulary.

---

## 8. Chords: Notes Stacked Together

A **chord** is three or more notes played simultaneously. The most
fundamental chord type is the **triad** — three notes.

### Building a Triad

A triad is built from the root by stacking two intervals called **thirds**.
A third spans either 3 semitones (minor third) or 4 semitones (major third).

Four combinations give four triad types:

| Type | Intervals | Sound |
|------|-----------|-------|
| **Major** | Major 3rd (4) + Minor 3rd (3) | Bright, stable |
| **Minor** | Minor 3rd (3) + Major 3rd (4) | Dark, stable |
| **Diminished** | Minor 3rd (3) + Minor 3rd (3) | Tense, unstable |
| **Augmented** | Major 3rd (4) + Major 3rd (4) | Eerie, unstable |

Example — **G minor triad**: G (root) + Bb (3 semitones up) + D (7 semitones up total).

### Chords Built From a Scale

Every note in a scale can be the root of a triad built *using only notes
from that scale*. This produces seven chords, one per scale degree.

In **C major**:

| Degree | Chord | Notes | Type |
|--------|-------|-------|------|
| 1 | C | C – E – G | Major |
| 2 | Dm | D – F – A | Minor |
| 3 | Em | E – G – B | Minor |
| 4 | F | F – A – C | Major |
| 5 | G | G – B – D | Major |
| 6 | Am | A – C – E | Minor |
| 7 | Bdim | B – D – F | Diminished |

The pattern of chord types (Major, minor, minor, Major, Major, minor,
diminished) is the same in *every* major key — only the note names change.

---

## 9. Roman Numeral Notation

Chords are named by their **scale degree** using Roman numerals. Uppercase
= major chord, lowercase = minor:

```
Major key:   I  ii  iii  IV  V   vi  vii°
Minor key:   i  ii° III  iv  v   VI  VII
```

This is scale-agnostic: `I–V–vi–IV` describes the same *type* of
progression in any key. In C major: C–G–Am–F. In G major: G–D–Em–C.

Some important chords and what they feel like:

- **I** (the tonic): Home. Stable, resolved. Where music rests.
- **V** (the dominant): Tension. Strongly wants to resolve back to I.
  The V→I move is the strongest resolution in Western music.
- **IV** (the subdominant): Gentle tension, less urgent than V.
- **vi** (the relative minor in a major key): Melancholic colour.

### Common Progressions

| Progression | Description | Famous examples |
|-------------|-------------|-----------------|
| I – IV – V – I | The most fundamental. | Countless folk, blues, rock. |
| I – V – vi – IV | Modern pop backbone. | Enormous number of hit songs. |
| vi – IV – I – V | Same chords, different start point — sounds more melancholic. | |
| i – VI – VII – V | Minor key, gothic/emotional feel. | Trance, film scores. |
| i – VI – III – VII | Minor, circular, hypnotic. | Many trance and electronic tracks. |

---

## 10. The Feeling of Tension and Resolution

Music is essentially *controlled tension and release*. Understanding this
is more useful than memorizing chord names.

**Consonance** = stability, rest. The I chord. The perfect fifth. The octave.

**Dissonance** = tension, wanting to move. The V chord, the tritone,
the major 7th interval.

The most powerful move in tonal music: **V → I**. The V chord contains
a tritone (between its 3rd and 7th) that strongly wants to collapse inward.
When it does, landing on I feels like relief.

**Cadence**: A chord progression that closes a phrase — like a musical
full stop. The V→I cadence is the "perfect cadence". IV→I is a "plagal
cadence" (the "Amen" sound).

---

## 11. Melody: Scales in Time

A **melody** is a sequence of single notes over time — a scale used
*horizontally* rather than *vertically* (as chords are).

Melodies tend to:
- Mostly stay within the scale of the current key
- Move by small steps (2 semitones or less) most of the time
- Occasionally jump by larger intervals for drama
- Have a shape — rise and fall, with a peak and a resolution

**Motif**: A short melodic fragment (3–5 notes) that can be repeated,
transposed, or varied. Effective melodies are built from a small motif
developed throughout the piece.

---

## 12. Harmony: Chords Beneath a Melody

**Harmony** is the relationship between the melody notes and the
underlying chords. When a melody note belongs to the current chord,
it sounds stable (**consonant tone**). When it doesn't, it creates
momentary tension (**passing tone** or **non-chord tone**) that usually
resolves to a chord tone on the next beat.

Good harmonic writing uses this tension and release constantly at the
small scale (within phrases) even while the large-scale chord progression
is also creating its own arcs.

---

## 13. Borrowing: Reaching Outside the Key

A **borrowed chord** is a chord taken from a different key — usually the
parallel minor (same root, different scale). In C major, the parallel minor
is C minor. Borrowing chords from C minor into a C major piece introduces
unexpected, colourful moments.

**Example**: In G minor, the V chord (built on D) would naturally be D minor.
But composers frequently use D **major** instead — borrowing the F# from
outside G minor. This single note (the raised 7th) creates a strong pull
back to G and has a characteristic "gothic" brightness against the surrounding
minor chords. This technique is called the **harmonic minor** inflection.

Borrowed chords don't break the key — they colour it. The ear accepts them
as temporary visits, not modulations.

---

## 14. Modulation: Changing Key

**Modulation** is a genuine, sustained change to a new tonic — not just
a borrowed chord. Pieces modulate to add variety or escalate energy.

The most common modulation is to the **dominant** (V of the current key —
7 semitones up). Moving from C major to G major raises the energy slightly
because G major contains an F# where C major had an F natural.

Relative major/minor modulation (e.g. C major ↔ A minor) is the smoothest
possible change because no new notes are introduced — only the perceived
home changes.

---

## 15. Rhythm and Meter

**Meter** is the regular grouping of beats into bars (also called measures).

**4/4 time**: Four beats per bar; the quarter note gets one beat. The most
common meter in Western popular music. Think of a steady "1 – 2 – 3 – 4"
count, with emphasis on beats 1 and 3.

**3/4 time**: Three beats per bar — the waltz. "1 – 2 – 3 / 1 – 2 – 3".

**Asymmetric meters** (5/4, 7/8, 13/16): The bar doesn't divide evenly
into equal groups. This creates a characteristic "limp" or rolling feel —
the listener can't find the comfortable, predictable landing point. Progressive
rock and film scores use these frequently.

**Syncopation**: Placing emphasis on beats that aren't normally stressed.
In 4/4, beats 2 and 4 are weak — emphasising them creates the "backbeat"
that drives rock and pop. Placing accents *between* the main beats creates
a floating, off-kilter feel.

---

## 16. Tempo and Feel

**Tempo** is the speed of the beat, measured in BPM (beats per minute).

Some common tempo ranges and their associations:

| BPM | Name | Common use |
|-----|------|------------|
| 60–80 | Largo / Adagio | Slow, ballad, emotional |
| 90–110 | Andante / Moderato | Walking pace, mid-tempo pop |
| 120–130 | Allegro | Upbeat dance, house music |
| 138–145 | — | Trance, techno |
| 160–180 | — | Drum and bass, hardcore |

Tempo affects feel more than genre alone. A chord progression in D minor
at 70 BPM sounds funereal; the same progression at 140 BPM sounds urgent
and driving.

---

## 17. Timbre: Why Instruments Sound Different

Two instruments can play the exact same note at the exact same volume and
sound completely different. This difference in sound quality is **timbre**
(pronounced "TAM-ber").

Timbre is determined by:
- Which harmonics are present (and at what relative levels)
- How the sound begins (the attack)
- How it decays over time
- Any vibrato, noise, or texture layered in

A flute is mostly pure fundamental (few harmonics). A violin has many
strong harmonics. A clarinet emphasises odd harmonics. These spectral
fingerprints are what the brain uses to identify instruments.

In synthesis, controlling timbre means controlling the harmonic content
and the envelope shape — which is exactly what the warmth recipe in the
first document is doing.

---

## 18. Texture: How Many Things Are Happening

**Texture** describes how many musical lines are present and how they
relate:

- **Monophonic**: One melodic line, nothing else (e.g. a solo flute).
- **Homophonic**: One melody with chordal accompaniment beneath it.
  The most common texture in popular music.
- **Polyphonic**: Multiple independent melodic lines happening simultaneously,
  each of equal importance. Bach fugues are the prime example.

In electronic music the texture usually evolves across the track — the
classic trance structure adds one layer every 16 bars, building from a
single rhythmic element to full homophonic texture, then strips elements
back down to create dynamic contrast.

---

## 19. Dynamics and Arrangement

**Dynamics** is the variation in loudness over time. A track that stays at
the same loudness for its entire duration is fatiguing. Music breathes by
getting louder and softer.

**Arrangement** is the decision about which instruments play when.
The same chord progression and melody can feel intimate (solo piano) or
enormous (full band + strings + reverb), depending entirely on arrangement.

A key technique: **drops and builds**. Electronic music regularly strips
the arrangement down to almost nothing ("the drop" or "breakdown") and
rebuilds it, making the return of the full texture feel like a release of
tension even if nothing in the harmony has changed.

---

## 20. Quick Reference: The Most Useful Facts

**The 12 notes:**
```
C  C#/Db  D  D#/Eb  E  F  F#/Gb  G  G#/Ab  A  A#/Bb  B
```
No sharp/flat between E–F and B–C.

**Major scale pattern:** 2–2–1–2–2–2–1 (semitone steps)

**Natural minor scale pattern:** 2–1–2–2–1–2–2

**Relative minor:** Start 3 semitones below the major tonic (C major → A minor).

**Triad types:**
- Major = 4 + 3 semitones (bright)
- Minor = 3 + 4 semitones (dark)

**Key interval feelings:**
- Unison / Octave / Perfect 5th: Stable, open
- Major 3rd / Major 6th: Warm, bright consonance
- Minor 3rd / Minor 6th: Darker consonance
- Tritone: Maximum tension

**The strongest move in tonal music:** V → I (tension to release).

**Borrowed raised 7th in minor:** Playing the major V chord in a minor
key introduces a note one semitone below the tonic, creating a strong
pull home. This is the "gothic" or "Hitchcock" sound.
