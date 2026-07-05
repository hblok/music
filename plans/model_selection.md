# Which Claude model for which job (trance/ generators)

Advice for the three-stage workflow behind each track: write the musical
plan (`*_notes.md`), write the generator (`*.py`), keep the catalog +
instrument library (`instruments/README.md`) in sync. Model IDs are current
as of 2026-07 (see the claude-api skill's catalog for the live list).

## TL;DR

| Stage | Default | Reach for | Effort |
|---|---|---|---|
| Musical plan (`*_notes.md`) | **Opus 4.8** | Fable 5 for a genuinely new form/concept | high |
| Generator script (`*.py`) | **Opus 4.8** | Fable 5 for a from-scratch synthesis engine | xhigh |
| Catalog / instrument library | **Sonnet 4.6** | Haiku 4.5 for a one-line append | medium (low for appends) |

## Why

**Musical plan → Opus 4.8 (high).** The notes docs are the hard part: concept,
form (Q/A at three levels, seam devices, thesis/bookend), genre grammar, the
emotional read, and the open-questions-for-review block that the user answers
inline (see `silver_wire_v2_notes.md`). This is taste-heavy creative reasoning
plus an interactive back-and-forth — Opus 4.8's strengths (warmer/clearer prose,
a real thought partner that pushes back). The `idea.md` doctrine and per-track
identity separation are exactly the kind of constraints it holds well. Go to
**Fable 5** only when the leap is large — a brand-new song shape, not a variation
on song-form / machine-score / two-reveal — where "state the goal, it navigates
the ambiguity" pays off.

**Generator script → Opus 4.8 (xhigh).** Each `*.py` is ~30–47 KB / ~800–1200
lines of numpy+scipy DSP that must implement the notes doc's Verify paragraph
*exactly* and iterate on a FAIL ("fix the music, not the check"). That is the
flagship long-horizon agentic-coding case: one well-specified goal up front,
runs to a passing section-map/RMS/form check. xhigh is the coding sweet spot.
Use **Fable 5** when the track needs a synthesis engine that doesn't exist in
the catalog yet (a new voice family, not a re-voice of an owned instrument) —
its first-shot implementation of a well-specified system is the differentiator.
Both follow the "copy the function, don't import" convention if told to.

**Catalog / instrument library → Sonnet 4.6 (medium).** Indexing every
`script:function`, its character, and ownership, then deduping and grouping by
identity separation, is precise but not taste-heavy — Sonnet's speed/intelligence
balance fits, and it follows the literal "don't duplicate the deep recipes here"
rule well. Drop to **Haiku 4.5** for a trivial sync (append one row after a new
track lands); keep Sonnet for anything that re-groups or re-judges "owned by".

## Notes

- **The stages are a pipeline, not one model.** Plan and script are worth the
  Opus/Fable premium; the catalog is cheap upkeep. Don't run the indexing pass
  on the flagship model out of habit.
- **Effort matters more than the model tier here.** A generator at `medium` will
  under-verify; the plan at `xhigh` will over-elaborate the prose. Match effort
  to the table.
- **Fable 5 caveats for this repo:** its safety classifiers target bio/cyber, so
  music work won't trip them — but it needs 30-day data retention (no ZDR) and
  costs above Opus tier. Only pick it when the extra capability earns its price.
- **Reuse the plan across scripts cheaply.** When a `_vN` revision only tweaks
  one section, that's a narrow, well-specified edit — Sonnet 4.6 can carry it if
  the notes doc already froze the rest.
