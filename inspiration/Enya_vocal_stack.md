# The Enya sound — one voice as a choir (technique note, 2026-09-08)

*A parked idea, not a track plan. Noted from a description of how Enya's
records are made; no audio measured. Filed here so it is found when a
voice track comes up (`tracks/ebm/VOCALS.md` points at it).*

## What she does

- **Multi-layering instead of a choir.** No backing singers: her own
  voice recorded again and again in separate takes — reportedly up to
  several hundred per song — and stacked. Every take differs a little
  in pitch, timing, vowel and breath, and the stack of those small
  differences is what reads as *many people*: a chorus effect made of
  real variation, not a modulated delay.
- **Acoustic space.** The stack goes into long, spacious reverb; the
  combination of hundreds of near-identical voices and a cathedral tail
  is the signature. The reverb is on the voices, not on the rhythm.

## Why it works (the mechanism to lift)

A chorus/doubler makes ONE signal wobble; a stack of takes gives N
*independent* small deviations. Sum N of them and the fundamentals
blur into a band a few cents wide, the consonants smear into a soft
onset, the breath becomes texture — a section, not a soloist. The
long reverb then fuses the band into one body. Two ingredients, both
cheap in this repo: independent variation per copy, and one long hall
on the sum.

## How it maps here

1. **The recorded-voice path** (`tracks/ebm/VOCALS.md`): when a take
   exists, ask for four to eight takes of the same line, not one — real
   double-tracking is already the plan; this is the same idea taken
   further. Sum them with nothing but level matching and the hall.
   Pyworld can manufacture extra "takes" from one recording (small f0
   and timing perturbations per copy, formants ±1–2 %), which is the
   honest synthetic version of the same mechanism.
2. **The synthesized version**: any sustained voice in the library
   (`juno.pad`, `dark_lead`, a formant choir) rendered N times with
   per-copy jitter — pitch ±3–8 cents, onset ±10–30 ms, formant/cutoff
   ±2 %, vibrato phase random — summed and sent to a long hall. This is
   the "cathedral choir" the EBM blueprint asks for (`EBM_1990s.md` §7)
   built from variation rather than from a formant pair; distinct from
   adrift's breath choir (which drifts *over time*; this drifts *across
   copies*).
3. **Where it would land**: the VNV-style chorus of a later ebm song
   (the wall behind the baritone), *Reliquary (Part 2)*'s resolution
   (the one place the album could open up), or an ambient piece.
   Not on the 1993 dark-electro tracks — the blueprint's "no long hall
   on everything" rule stands there.

Check to print when it is built: the per-copy deviations (cents, ms)
and the stack's spectral bandwidth around the fundamental versus a
single copy — the band should be measurably wider, the onset slower.
