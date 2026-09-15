# Gemini CLI as a Fable alternative — setup notes (unexecuted)

Reference note, not a decision record. Nothing below has been run — no
`GEMINI.md` exists, `gemini-cli` is not installed. Captures the mechanism so
it doesn't need re-deriving if this ever comes up again. See
`model_selection.md` for the current Fable-cost tradeoffs this would touch.

## Setup steps (from a user-supplied blueprint, 2026-09-15)

```bash
npm install -g @google/gemini-cli   # node/npm already present in dev sandbox
gemini login                        # interactive browser OAuth, personal
                                     # Google account, free tier: 1,000 req/day
gemini setup github                 # optional: generates GH Actions workflows
```

A `GEMINI.md` at repo root gets auto-injected into every Gemini CLI query,
the same way `CLAUDE.md` is now.

## What would need porting first

This repo's `CLAUDE.md` (root + per-subsystem) only holds engineering
conventions — forge/inspector/soundmatch architecture, style rules. None of
the actual composition taste lives here; it's accumulated across many chat
sessions and isn't written down in the repo anywhere. Before a `GEMINI.md`
would be worth anything, it would need those rules transcribed into it,
e.g.:

- Genre-boundary rules (what reads as goa vs. country/western, when a lead
  is allowed to "sing" vs. just run)
- Mix/arrangement calibration (drone-bed depth, big-room master targets)
- Song-form rules (motif development, no dead seams, seam devices)
- Naming/branding rules (WERK 16 constraints)
- The per-genre don'ts accumulated from past listen verdicts

A generic "brutalist/microtonal/glitch-art" system-prompt persona (the
blueprint's own suggested `GEMINI.md` content) is a placeholder for this,
not a substitute — it would produce generic avant-garde flavor text, not
this catalog's specific house style.

## Open questions if revisited

- Does Gemini CLI's 1M-token context change anything about how those rules
  get organized (one big file vs. split like the per-subsystem CLAUDE.md
  files)?
- Fable's actual role today is the *high-effort ideation* stage only
  (`model_selection.md`) — generator scripts and catalog upkeep already run
  on Opus/Sonnet/Haiku. Any swap only needs to cover that one stage, not the
  whole pipeline.
</content>
