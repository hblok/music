# Spice Agony (Reverend Mother Mix) — design notes (2026-07-31)

The B2 idea from `more_ideas.md`, promoted to a track: a **downtempo / dub
remake of `generate_water_of_life.py`**. "We have never gone slow and
heavy." The album's *morning-after* listening track — Massive Attack /
the slower Juno Reactor cuts as reference. A DUB MIX of an existing track,
so it should read as a recognisable rework of water_of_life, not a new
piece in the same palette.

## Declared up front (settled from B2 + the Dune conventions)

- **~85 BPM, half-time feel, D Phrygian dominant** (water_of_life's key
  and mode — a mix keeps the key). ~6–7 min. Seed 10193.
- **Standalone** `generate_spice_agony.py`, conventions per
  `CLAUDE.md` here (numpy+scipy, stdlib `wave`, seeded rng, `commit()`
  bus, printed per-section RMS + form checks) + FLAC alongside the WAV
  (the newer repo default). WAV to `/workspace/music/`, never commit audio.
- **The room-shake kick, half-time** — the fall_of_arrakeen two-round
  feedback stack, but one hit every half-note with air around it (the
  spec: it hits HARDER with more space). This is the heavy in slow-and-heavy.
- **The dune acid stays the dune acid** (NOT claimed by the psy 303 ban —
  that's tracks/psy/; this is the album's own): the sharp-303 recipe
  (sweep within every note), here playing **one note per bar with a
  full-bar filter sweep** — the dub-tempo acid.
- **Dark + modal + hypnotic** (the genre DNA — the anti-Meridian; see
  `../psy/CLAUDE.md`'s genre-boundary note). No major lift, no sung lead.

## The new recipe (the reusable deliverable): TAPE-ECHO

A feedback delay where **each repeat is lowpassed a little darker and
pitch-wobbled by a slow LFO** — an `lfilter` chain per repeat (dub's
signature dub-siren / melting-echo). Drives the "rolling bass stretched
to dotted-eighth skanks" and the chant tails. This is what makes it dub
rather than just slow. Goes into `CLAUDE.md` once proven.

## Open questions for review

1. **Structure — DUB form vs song form.** DUB (recommended): loop-based,
   the mixing-desk arrangement — elements drop in and out, echo-drenched
   breakdowns, no big song-form drop/chorus; hypnotic and spacious (the
   "morning after"). vs the song form we've used lately (thesis /
   verses / choruses / bridge / payoff) — more shape, less genuinely dub.

2. **How much of water_of_life to quote.** A recognisable REMIX
   (recommended): reuse its actual rolling-bass riff, its main theme, and
   its 303 line — slowed, dubbed, re-echoed — so a listener hears "that's
   Water of Life, dubbed". vs new material in the same palette (safer, but
   then it isn't really a "Mix" of anything).

3. **The Sardaukar chant.** Dubbed chant fragments (recommended): reuse
   the throat chant, chopped to short fragments drenched in the tape-echo
   (very dub — the voice as echo texture). vs instrumental only. (No new
   TTS/vocal work either way — the unsung dead-end stands.)

4. **Heaviness vs spaciousness.** The dub balance: heavy sub + kick, but
   lots of air and long echo tails (recommended — slow AND heavy AND
   spacious). vs push the heaviness (denser, less "morning after"). "Slow
   and heavy" and "morning after" pull in opposite directions — which wins
   when they conflict?

5. **Length.** ~7 min (the spec — dub wants room to breathe) vs a tighter
   ~5–6 min. 

6. **Name.** *Spice Agony (Reverend Mother Mix)* (recommended — ties it to
   the ceremony and signals it's a mix) vs just *Spice Agony* vs something
   else. Filename `generate_spice_agony.py` either way.

7. **Inspiration doc first?** Option A (recommended): build from this plan
   — the palette is the Dune album's own, fully understood, and the tape-
   echo is a clear DSP recipe. Option B: analyse a Massive Attack / dub
   reference via inspector first (costs a session). (phototaxis + the
   others went A.)
