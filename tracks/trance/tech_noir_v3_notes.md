# Tech Noir v3 — design notes (the doctrine without the pop form)

Composition document for review before writing `tech_noir_v3.py`
(→ **`tech_noir_v3.wav`** — v1/v2 both wrote `tech_noir.wav`).

The experiment of the three revisions: tech_noir is a Fiedel machine
score — 13/16 limp, dry forward bass, wet metal, no risers, no
sidechain, ends cold — and it is *not* dance music and *not* a song.
So v3 tests how much of the song doctrine survives contact with a
machine: **Q/A composition, refrain identity, the fusion payoff, and
seam discipline carry over; verse/chorus form does not.** There is no
drop, no bridge, no bookend hook — the machine locks in at ~0:20 and
never stops until the cold cut. That is the genre and it stays.

- Length ~4:30–5:00 (the middle grows to earn the fusion), 13/16
  grouped 3+3+3+2+2, ~100 BPM quarter pulse.
- Key: D minor, static/modal — tonic pedal under the fanfare,
  i–bVI–bVII under the love theme (unchanged).
- Seed: `np.random.default_rng(1984)` (unchanged).
- Output: `/workspace/music/tech_noir_v3.wav` (+ mp3).

## The two themes, composed as question and answer

v2 already has both halves — the warm Oberheim five-note **fanfare**
(alternate statements ending hollow, a fifth below) and the mournful
**love theme** (i–bVI–bVII) — but they live in separate sections and
never interact. v3 composes the relationship:

1. **The fanfare is the question.** Formalized: every statement ends
   off-tonic (the hollow fifth-below ending becomes the rule, not the
   alternate) — a machine asking the same thing over and over.
2. **The love theme is the answer.** Same rhythmic skeleton as the
   fanfare at contour level, resolving where the fanfare hangs. Its
   middle section is now literally the answer arriving — late,
   human, mournful — to the question the machine has been repeating.
3. **The fusion payoff**: the return section sounds them **together**
   for the first time — the love theme as counter-line *under* the
   octave-doubled fanfare, over the unchanged 13/16 ostinato. v2's
   return is just the fanfare intensified; v3's return is the point of
   the piece: the question and its answer over a machine that heard
   neither. Then the outro strips and it ends cold — the question wins.

Refrain identity: the fanfare melody is *identical* every statement
(target ≥ 8 statements, counted); variation budget goes to register,
doubling, and what answers it.

## Level-2 Q/A — the machine answers with metal

Composed echoes fit the score naturally: an **anvil clang answers each
fanfare phrase-end** (wet metal answering the warm brass — the plate
ring entering on the phrase's last note), and the gated slam
punctuates the love theme's cadences. The machine is the third voice:
it can only answer with noise.

## Seams — the machine IS the continuity

The doctrine's "one continuous cursor" is already this score's nature:
the ostinato never stops from 0:20. Section boundaries get the
existing punctuation vocabulary as formal seam devices — a slam, an
anvil ring, or a bass fill crossing every boundary; the checklist gets
printed like the song tracks. **No risers, no reverse cymbals, no
builds** — those are dance-music seams and stay banned here.

## What stays banned (the Fiedel rules)

13/16 limp never regularized; dry bass + wet metal; no hi-hats, no
four-on-the-floor; no filter sweeps, no sidechain, no risers; warm
brass per the warmth recipe; **ends cold** (one last slam + anvil
ring, hard stop — no bookend, no fade). The cold-open anvil clangs in
empty space are the thesis and stay exactly as they are.

## Structure (sketch)

| t | section | what happens |
|------|---------|--------------|
| 0:00 | cold open | Isolated anvil clangs; dark pad creeps in. (Unchanged.) |
| 0:20 | THE OSTINATO | 13/16 bass pulse + gated slams lock in, never stop. |
| 0:50 | the question (16 bars) | Fanfare states the refrain 4×, every ending hollow; anvil answers each phrase-end. |
| 1:40 | the answer (16 bars) | Love theme over i–bVI–bVII, slams pull back, pads warm; slam punctuates its cadences. Fanfare silent — the two never overlap yet. |
| 2:30 | interrogation (12 bars) | Development: fanfare fragments and love-theme fragments *trade* 2-bar calls over the machine — question, answer, question — metal taps thicken, clangs every 2 bars. |
| 3:10 | **THE FUSION** (16 bars) | Both together: octave-doubled fanfare + love theme as counter-line, slams doubled, the fullest the machine gets. |
| 4:05 | outro (bars) | Strip to bare pulse + metal; the fanfare asks once more, unanswered. |
| 4:30 | cold stop | One last slam and anvil ring out. |

Verify (script prints): fanfare statement count ≥ 8; RMS ordering —
fusion loudest, answer section warmer/quieter than question, outro
settling; seam checklist per boundary (slam / clang / fill).

## The band (all v2 reuse, zero new timbres)

Prophet-style saw bass pulse (13/16 DUN-dun grid), gated 80s drum
slams, anvil clangs + big dark plate, warm Oberheim fanfare
(`reed()` recipe), the love theme voice, dark pads, metal taps.

## Open questions for review

1. **How literal the Q/A**: strict same-rhythm antecedent/consequent
   between fanfare and love theme (maximum doctrine, but risks making
   the machine score too tidy) vs contour-level correspondence — the
   love theme answers where the fanfare hangs, without mirroring its
   rhythm (recommended: the limp thrives on things not lining up)?
   Answer: contour-level correspondence sounds more interesting. However, also keep in mind, that the Q/A technique is not an absolute rule which most presist at all cost. If it jeperdizes the music itself, it's better to let go, and find another way to express the theme. For example, in the original Terminator theme, the contrast was found between the melody and the bassline. It was not a direct mirror Q/A, but still a cohision between the two. In other words, there are endless ways of expressing the duality in any dimension of the music system.

2. **The interrogation section** (the 2-bar trades) is the one new
   structural idea. Keep it, or go straight from the answer section to
   the fusion and stay closer to v2's arc? I recommend keeping it —
   it's where the doctrine actually shows, and 12 bars is cheap.
   Answer: Ok, let's keep and try it out - however, see the answer above for friction in the rule vs. artistic freedom.

3. **Length**: ~4:30 as sketched vs stretching the fusion to 24 bars
   (~4:50)? I recommend 16 bars — this score's power is restraint;
   the fusion should end while it still surprises.
   Answer: length is not an absolute. If it takes longer to express the full idea, that's OK. However, if there is no need to expand, that's also OK. Duration in itself is not a goal nor a restriction.
   

