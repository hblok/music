# Musical analysis of "L'Inverno" (Winter), RV 297 — Antonio Vivaldi

Op. 8 No. 4 from *Il cimento dell'armonia e dell'inventione* (Amsterdam,
Le Cène, 1725), for solo violin, strings and continuo. This is the
"wear-warned" candidate from `tracks/trance/idea.md` — and the warning
is about the *piece*, not the *material*. Everything done to Winter so
far (Richter's recomposition, Orbit's version, the piano/violin covers)
replays the composition whole. Nobody has mined it the way we work:
lift a cell, a riff, a chord crawl, and build a new track on it. That's
what this document is for — a motif catalog with exact pitches, not a
cover blueprint.

**The full score is included** in `Winter_Vivaldi_score/`:
`winter-score-a4.pdf` (full score), `winter-solo-a4.pdf` (solo part),
the complete LilyPond sources (`winter-lys/` — the machine-readable
score all pitches below were read from), and rendered MIDIs
(`winter-score.mid` = mvt I, `winter-score-1.mid` = mvt II,
`winter-score-2.mid` = mvt III). Source: Mutopia project #351, typeset
from the Performers' Facsimiles edition, CC BY-SA 3.0. Every motif
transcription below was cross-checked against the MIDI note stream.

---

## 1. Genre & Style

High-baroque programme concerto, 1725. Each movement paints lines of a
sonnet (printed in the original edition, possibly Vivaldi's own); the
sonnet fragments are engraved *in the parts* at the exact bars they
depict — texture as picture. The reason this piece mines so well: to
paint weather, Vivaldi abandons melody-first writing and builds nearly
everything from **short repeating pictorial cells** — ostinati, pedals,
one-pitch hammering, sequences. It is loop-thinking, three centuries
before the sequencer.

Wear status, honestly: movement I's opening shiver and the solo
cascades are the famous, claimed bits (film trailers, Richter). The
**Largo is known but not dance-worn**, and **movement III's cells are
essentially unmined** — nobody's floor track uses the ice-walk,
ice-crack, or Borea material.

## 2. Tempo & Key

- **Mvt I** — Allegro non molto, 4/4, **F minor**. Recordings ≈ ♩ 56–69.
- **Mvt II** — Largo, 4/4, **E♭ major**. Recordings ≈ ♩ 40–50.
- **Mvt III** — Allegro, 3/8, **F minor**. Recordings ≈ ♩. 50–60.

Practical mapping: at 132–136 BPM one Vivaldi 4/4 bar ≈ two trance
bars (his shiver 8ths become quarter-note stabs); the Largo melody sits
naturally in half-time over the same grid, its pizzicato 16ths landing
as an offbeat pluck. **Key collision**: F minor is ungeschrieben's
identity — keep or transpose is a notes-doc decision.

## 3. Song Structure

Rehearsal marks are this edition's; sonnet lines sit at exact bars.

**Mvt I (63 bars, ~3:10–3:45)**
- **A, b1–11** — *Aggiacciato tremar trà nevi algenti* (frozen,
  trembling amid icy snows): the shiver stack, motif W1.
- **B, b12–21** — *Al Severo Spirar d'orrido Vento* (the horrid wind):
  solo cascades (W2) alternating with tutti freeze bars.
- **C, b22–46** — *Correr battendo i piedi ogni momento* (running,
  stamping feet): octave-bounce sequence (W3); b33–38 the stutter
  ladder (W4a); cadence figures.
- **D, b47–63** — *E pel Soverchio gel batter i denti* (teeth
  chattering): piano-dynamics trough (W4b), tremolo crawl, F fermata.

**Mvt II (18 bars, ~1:45–2:30)** — *Passar al foco i di quieti e
contenti / Mentre la pioggia fuor bagna ben cento* (quiet days by the
fire while rain soaks a hundred outside). One texture throughout (W6):
8-bar question (half cadence on B♭) + 8-bar answer (full cadence) +
2-bar dissolve on a held E♭. The theme is W5.

**Mvt III (~153 bars of 3/8, ~3:00–3:40)**
- **F, b1–24** — *Caminar Sopra'l giaccio* (walking on the ice):
  gliding six-note cells (W7a).
- **G, b25–39** — *à passo lento, per timor di cader* (slow steps, for
  fear of falling): tutti sighs + chromatic riser (W7b).
- **H, b40–50** — *Gir forte, Sdruzziolar, cader à terra* (going hard,
  slipping, falling): 32nd-note slips, the two-bar fall.
- **I, b51–88** — *Di nuovo ir Sopra 'l giaccio e correr forte*
  (running hard on the ice again): staccato 16th run cells, register
  leaps, triplet cascade.
- **L, b89–100** — *Sin ch'il giaccio Si rompe, e Si disserra* (until
  the ice cracks open): stab–silence–flick fragments (W8a).
- **M, b101–119** — *Sentir uscir dalle ferrate porte* (hearing, from
  their iron gates…): Il Vento Sirocco — a Lento island, warm waves.
- **N, b120–149** — *Sirocco, Borea, e tutti i Venti in guerra* (all
  the winds at war): the storm (W8b).
- **b150–153** — *Quest'è 'l verno, mà tal, che gioja apporte* (this is
  winter — but such as brings joy): cadence to a bare unison F, cold stop.

## 4. Melody & Harmony — the motif catalog

The heart of the document. Pitches in scientific notation (C4 = middle
C), all verified against the MIDI.

### W1 — The shiver stack (I, b1–11)

Voices enter one per bar, each repeating staccato slurred-pair 8th
notes on a single pitch, and the pile is dissonant from bar 2:

| bar | cello | viola | vln 2 | vln 1 + solo | chord |
|-----|-------|-------|-------|--------------|-------|
| 1 | F | — | — | — | bare tonic pulse |
| 2 | F | G4 | — | — | major-2nd clash |
| 3 | F | G4 | D♭5 | — | |
| 4 | F | G4 | D♭5 | B♭5 (trilled) | **Gø7 over F pedal** |
| 5 | **E** | G4 | D♭5 | B♭5 | **E°7** |
| 6 | F | A♭4 | C5 | A♭5 | **Fm — first consonance** |
| 7 | F | F4 | B♭4 | D♭5 | B♭m/F |
| 8 | F | **A♮4** | C5 | E♭5 | **F7** |
| 9 | F | B♮3/G3 | B♮4 | D5 | G7/F |
| 10 | **F♯** | A4 | C5 | E♭5 | **F♯°7** |
| 11 | G | G4 | C5→B♮4 | D5 | Csus/G → **G major** |

Eleven bars, one unbroken 8th pulse, and the first consonant chord
arrives in **bar 6**. Then the harmony crawls out by semitone steps —
mostly one voice moving per bar — and cadences *away*, into C minor
(v) at mark B. Restlessness achieved purely by harmony over a pedal.

**Trance translation:** this is the additive trance intro as written —
one repeated-note voice per N bars, except each layer *increases
dissonance* instead of density. Also a filter-morph stab-bed
progression over a drone. The solo's trills on top = ornament that maps
to a fast gate/retrigger. Per idea.md: texture engine, **not** the
foreground hook (this is the claimed bit).

### W2 — Orrido Vento cascades (I, b12–21, solo)

Three waves, each the same 3-bar cell stated on rising chord tones of
C minor (C → E♭ → G). Wave 1, exact (32nd notes):

```
b12:  C5 C6 C6 G5 | G5 E♭5 E♭5 C5 | (×2)          — octave-leap zigzag
b13:  C5 C6 B♭5 A♭5 | G5 F5 E♭5 D5 | (×2)          — scalar collapse
b14:  C5 G4 C5 E♭5 (×4)                            — low rocking turn
b14:  C4 held, trilled                              — landing
```

The zigzag formula — root, octave, octave, fifth / fifth, ♭3, ♭3,
root — is verbatim a sequencer arp pattern. The wave plan (identical
cell restated up the triad) is motif development for free: state,
restate higher, restate higher, cadence.

### W3 — Stamping feet (I, mark C, b22–26)

Two interlocking components, sequencing down the circle of fifths
(F→B♭→E♭→A♭→D♭→G→C→F):

- **Upper**: one bar hammering a single pitch in 32nds (G5), next bar
  oscillating a wide interval in 16ths (A♭5–C5); then hammer D♭5,
  oscillate G5–D♭5; hammer C5, oscillate F5–C5; hammer B♭4, oscillate
  E5–B♭4.
- **Bass**: octave-bounce 16ths — F3 F2 F3 F2 → B♭; E♭3 E♭2 → A♭;
  D♭3 D♭2 → G; C3 C2 → F.

**Trance translation:** the octave-bounce bass IS the classic trance
octave bass, here already welded to a hammer+oscillation stab loop, and
the whole thing loops through a full circle-of-fifths cycle — rich
harmony that still behaves like a loop. Probably the most directly
liftable groove cell in the piece.

### W4 — Chattering teeth (I, two forms)

**(a) The stutter ladder (b33–38).** Solo and tutti trade bars: the
orchestra plays a turning figure, the solo locks onto ONE pitch and
repeats it in 32nds for a full bar — then the exchange repeats a step
higher. Verified stutter pitches, in order: vln 1 **E4**, solo **A5 →
B♮5 → D5 → E♭5 → D5** (16 hits each). A♮ and B♮ are alien to F minor —
the ladder climbs *out* of the key, tension by wrong-note stutter.

**(b) Batter li denti (mark D, b47–56).** Marked *piano* — the
movement's composed trough. Violins whisper repeated 16ths stepping
down (C6 ×16 → B♭5 ×16 → A♭5 ×16 → …) while the solo crawls in
measured-tremolo double-stops (E♭6+C6, D6+C6, D♭6+B♭5 …) over it.

**Trance translation:** (a) is a gate/stutter lead riff with a built-in
build (chromatic ladder); (b) is the breakdown texture — tremolo pad +
whispered stutter, dynamics dropped, exactly our bridge-trough move.

### W5 — THE LARGO THEME (II, b1–8 + 9–16) — the refrain candidate

E♭ major, solo violin, cantabile. The rhythmic signature is a lilt of
8th + two 16ths. Question phrase, exact (rhythm in parentheses):

```
b1:  E♭5(8)  B♭5 A♭5(16s)  G5(8)  F5 E♭5(16s)  F5(8) B♭4(8)  r  B♭4(8)
b2:  A♭5 G5 F5 E♭5(16s)  D5(8) A♭5(8)  A♭5(8) G5(8)  r  G5(8)
b3:  F5(8) G5 A♭5(16s)  B♭5(8) C6 D6(16s)  E♭5(8) F5 G5(16s)  A♭5(8) B♭5 C6(16s)
b4:  D5(8) E♭5 F5(16s)  G5(8) A♭5 B♭5(16s)  C5(8) D5 E♭5(16s)  F5(8) G5 E♭5(16s)
b5:  D5(4~) D5 B♭4 A♮4 B♭4(16s)   F5(4~) F5 B♭4 A♮4 B♭4(16s)
b6:  G5(4~) G5 B♭4 A♮4 B♭4(16s)   A♮5(4~) A5 F5 E♭5 F5(16s)
b7:  B♭5(8) B♭4(8)  r  B♭5(8)   B♭5 A♭5 G5 F5 E♭5 D5 C5 B♭4 (slurred 16th pairs)
b8:  C5(4., trilled) B♭4(8)  B♭4(4)  r      ← half cadence on V
```

What's inside it, move by move: **b1–2** the singing descent — high
B♭ falling stepwise to E♭, answered by a drop to the low register
(instant call-and-response within one voice). **b3–4** the double
ladder: a two-beat climbing cell (8th + two 16ths) chained four times
up, then four times restated — pure sequence, pure build. **b5–6**
the sighs: a held note, then a written-out turn below it, four times
at rising pitches (D→F→G→A♮), the A♮ — raised 4th, a Lydian flicker /
secondary dominant — is what makes it ache. **b7–8** collapse down two
octaves' worth of scale into a trilled half cadence.

The answer phrase (b9–16) restates the same rhythm-shape starting a
4th lower (B♭4 F5–E♭5 D5 C5–B♭4 …), revisits the ladder, and closes on
the tonic; b17–18 dissolve on a held E♭5 while the rain keeps falling.
**Textbook antecedent/consequent — doctrine rule 2 for free.** A
16-bar Q/A refrain with its own internal build, hummable at any tempo.

### W6 — The rain machine (II, accompaniment)

The most remarkable finding in the score. The Largo's backing is,
role for role, a trance arrangement *as written in 1725*, with mix
instructions:

- **Violin 1, "Pizziccati forte"** (marked *La Pioggia* — the rain):
  broken-chord 16ths — `E♭5 G5 B♭5 G5 | E♭5 G5 B♭5 G5 | D5 F5 B♭5 F5…`
- **Violin 2, pizzicato**: the same figure interlocked a third below
  and rhythmically offset — `B♭4 E♭5 G5 E♭5 | B♭4 E♭5 G5 B♭4…`
- **Viola, "Pianissimo con l'arco"**: the ONLY bowed accompaniment —
  long tied notes (B♭4 held across bars 1–3…). A pad, mixed low.
- **Cello, "Sempre piano"**: soft repeated 8ths on roots —
  `E♭ E♭ E♭ E♭ | B♭ B♭ B♭ B♭ …`, walking E♭→B♭→D→C→B♭→A♭→**A♮**→B♭
  (a chromatic passing bass in bar 4!).

Pluck arp ×2 (interlocked), pad, soft 8th-pulse bass, lead on top —
and dynamic markings that amount to a mix spec (plucks forte, pad
pianissimo, bass piano). Lift the *texture* wholesale; it needs no
translation at all.

### W7 — Ice cells (III, marks F–G)

**(a) The gliding cell (b1–24).** Six slurred 16ths per 3/8 bar:
`C5 (A♭5 G5 F5 E♮5 F5)` — leap up a minor 6th, fall stepwise onto the
chromatic lower neighbour E♮, bounce back. Stated **four times
unchanged**, then developed by interval-swap with the rhythm constant:
`C5 (D♭5 C5 B♭4 C5 D♭5)`, then from F4… Hypnotic, self-similar, and in
3/8 — over a 4/4 grid it becomes a cross-rhythm rolling arp (or the
track borrows a 12/16 shuffle feel; cf. nachtkind's limp).

**(b) Sighs + the chromatic riser (b25–39).** Tutti: descending
slurred 3-note steps `B♭4 A♭4 G4 | A♭4 G4 F4` (twice more), then the
riser — three hammered 8ths per bar, one pitch per bar, climbing
chromatically: **A♭4 → A♮4 → B♭4 → B♮4 → C5**, and C5 (the dominant)
hammers on for *four full bars* before releasing. A written-out build
ramp: chromatic ascent, dominant parked, tension held by repetition.

### W8 — The break and the storm (III, marks L–N)

**(a) The ice cracks (b89–100).** Fragmented seam: low 8th stab —
silence — upward 32nd flick (`F5 · r · B3 C4 D4 | F3 · r · D4 E♭4 F4 |
G3 · r …`), three times, then three rising 8ths; the solo answers with
downward arpeggio flicks (`C5 G4 E♭4 C4`, `D5 B4 G4 D4`…) over a G
pedal. A composed glitch/stutter fill — a seam device from 1725.

**(b) Sirocco / Borea (b101–149).** Sirocco: a Lento island — warm
rocking 8th waves `G5 (F5 E♭5) | D5 (E♭5 F5)` decaying into hocketed
fragments with rests. Borea: 32nd-note scale storms
(`E♭5 B♭4 C5 D5 E♭5 F5 G5 A♭5 B♭5 A♭5 G5 F5…`), bars locked on a
single repeated pitch (F5 ×12), a chromatic churn
(`E5 F5 G5 F5 | E5 F5 E5 D5 | C5 D5 C5 B4…`), and then the closing
engine — bass pedal under a falling upper pulse:
`A♭3 F5 F5 F5 | G3 F5 F5 F5 | G3 E♮5 E5 E5` (twice around), resolving
to a **bare unison F with a fermata**. No picardy, no warmth — the
machine stops cold (tech_noir precedent: ends cold).

## 5. Bassline

Four distinct bass behaviours, all liftable: (1) **pedal** — the
11-bar F pedal under W1, storm pedals under W8b; (2) **octave
bounce** — W3's F3–F2 16ths walking the circle of fifths; (3) **soft
8th pulse** — the Largo's sempre-piano root 8ths with chromatic
passing notes (A♭→A♮→B♭); (4) **doubling the storm** — cello joins the
32nd-note runs in mvt III. The `winter*f.ly` files carry the original
figured bass — the 1725 chord chart, useful when re-harmonising.

## 6. Drums & Percussion

None — but the pulse roles are cast: the shiver's staccato 8ths are
the hat/stab grid, W3's hammered 32nds are the snare-roll analog, W4's
stutters are gate patterns, and the two fermata stops (end of I, end
of II into III) are composed drop-silences. The piece supplies motion
patterns, not kit sounds; the kit stays whatever the track's genre
rules say.

## 7. Synths & Sound Design (the mapping)

| Vivaldi | role | trance voice |
|---------|------|--------------|
| tutti shiver 8ths (W1) | dissonant pulse bed | icy closed-filter stab/pluck bed |
| solo violin | lead / narrator | main lead — warm, per genre rules |
| Largo pizzicato violins (W6) | interlocked arp | offbeat pluck arps, L/R pair |
| Largo viola tied notes | pad | dark low pad, mixed under |
| Largo cello 8ths | bass pulse | soft 8th bass |
| trills | ornament | fast gate/retrigger on note tails |
| measured tremolo (W4b) | trough texture | breakdown tremolo pad |
| figured bass | harmony source | chord chart, never literal |

Everything synthesized, as always — we take form and theme, never a
sampled recording.

## 8. Samples & Vocals

None in the source, and the instrumental rule stands. The concerto's
"text" is the sonnet — usable as programme, section names, and title
material (*Ferrate Porte*, *Borea*, *Sirocco*, *Gioja*, *Quest'è 'l
verno*). Full sonnet with the movement mapping:

> Aggiacciato tremar trà nevi algenti / Al Severo Spirar d'orrido
> Vento, / Correr battendo i piedi ogni momento; / E pel Soverchio gel
> batter i denti; *(mvt I — frozen trembling, the horrid wind, stamping
> feet, chattering teeth)*
>
> Passar al foco i di quieti e contenti / Mentre la pioggia fuor bagna
> ben cento; *(mvt II — quiet days by the fire while the rain soaks a
> hundred outside)*
>
> Caminar Sopra'l giaccio, e à passo lento / Per timor di cader gersene
> intenti; / Gir forte Sdruzziolar, cader à terra, / Di nuovo ir Sopra
> 'l giaccio e correr forte / Sin ch'il giaccio Si rompe, e Si
> disserra; / Sentir uscir dalle ferrate porte / Sirocco, Borea, e
> tutti i Venti in guerra / Quest'è 'l verno, mà tal, che gioja
> apporte. *(mvt III — walking the ice, slipping, falling, the ice
> cracking, the winds at war — "this is winter, but such as brings joy")*

## 9. Effects & Production Techniques (era analogues)

The 1725 toolkit maps onto ours almost one-to-one: **terraced
dynamics** (solo/tutti alternation) = arrangement-level filter
open/close; **ritornello returns** = refrain identity — the tutti
comes back like a chorus; **sequences** (W2's waves, W5's ladder, W3's
circle of fifths) = the era's automation ramps — builds written in
notes instead of CC data; **fermatas** = drop-silence beats;
**piano/forte block contrast** (mark D) = the composed trough. Nothing
here needs inventing — it needs *assigning*.

## 10. Emotional Tone & Energy Arc

Cold–warm–cold, ending in defiant joy: I shivers and hardens into the
stamping panic; II is the emotional center — warmth *surrounded by*
rain, safety with the cold still audible in the plucks; III plays on
the ice, falls through it, survives the war of winds, and closes with
the sonnet's turn: *this is winter, but such as brings joy*. The
coldness is never horror (dread = sadness, per the genre rules), and
the two temperatures — icy verse machinery, warm singing center — are
exactly the trance dark-verse / warm-chorus duality. The concerto even
ends the way tech_noir does: unison, cold, done.

---

## What to take, what to leave

- **Take as foreground**: W5 (the refrain — hummable, Q/A built in,
  not dance-worn) + W6 (the texture, needs zero translation).
- **Take as engines**: W1 (intro/verse dissonance bed — texture only,
  it's the claimed bit), W3 (groove cell + octave bass), W7b (the
  build ramp), W8a (seam device), W4 (gate riff + trough).
- **Leave**: replaying any movement's full form; the mvt I opening as
  a foreground hook (Richter territory); sampled anything.

## Open questions → for the notes doc

1. **Key**: source F minor collides with ungeschrieben's identity —
   transpose the whole design, or is sharing F minor acceptable? And
   where does the Largo's E♭ sit inside one progression family
   (relative-major A♭ instead? keep the i↔♭VII swing?).
2. **Tempo/meter**: 132–136 with one source bar = two trance bars? Does
   the 3/8 ice cell become cross-rhythm or a shuffle?
3. **Refrain size**: keep W5's full 16-bar Q/A or compress to 8?
4. **Shape**: song form (per idea.md) with W1 as the verse engine and
   W6 carrying the chorus — confirm or revise once sketching starts.

## Files & provenance

`Winter_Vivaldi_score/` — full score + solo part PDFs, LilyPond
sources, MIDIs. Mutopia #351 (2010), typeset from Performers'
Facsimiles, CC BY-SA 3.0. The typesetter's comments in the .ly files
note a few editorial accidental fixes vs. Vivaldi's manuscript (e.g.
naturals in mvt III bars 120/126) — trust this edition's pitches; the
MIDI cross-check above confirms them.
