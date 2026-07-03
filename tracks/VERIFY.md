# VERIFY.md — the form-check standard

Every generator script verifies its own composition and prints the result
after rendering, so a track's *form* can be checked — and re-checked after
any edit — without listening. The render is deterministic (seeded RNG), so
the printout is reproducible: same script, same numbers, same PASS/FAIL.

The flow is always: the design-notes doc states what will be verified (its
"Verify (script prints)" paragraph, reviewed with the open questions) →
the script implements exactly that → the printout is the receipt. The
checks encode the *intent agreed in the notes*; they are not generic
loudness lint.

Reference implementations: `dune/generate_sihaya.py`,
`dune/generate_muaddib.py`, `trance/lost_v6.py`.

## The five blocks (songs and story tracks)

Printed in this order, after the WAV/mp3 creation lines:

1. **Section map** — one line per section: start time (s), start bar,
   name. Include composed events that aren't sections (the kick stop, a
   bookend, a false ending).
2. **Hook count** — a counter (`HOOKS += 1`) incremented at every
   placement of the refrain/hook, printed against the target from the
   notes doc (e.g. `Refrain statements: 19 (target >= 10)`). Count full
   statements only, on any instrument/voice; fragments don't count.
3. **Seam checklist** — one line per section boundary naming what crosses
   it. The vocabulary: pickup note, ringing chord/note, fill, roll +
   riser, reverse cymbal, downsweep, echo overlap, unbroken groove, the
   composed silent beat. A boundary with *nothing* crossing it is a dead
   seam — that's a bug in the music, not in the checklist.
4. **Per-section RMS** — RMS of the mastered mix bus between section
   boundaries. Always measured post-master (shelves + tanh), because
   that's what the listener hears.
5. **Form checks** — `[PASS]`/`[FAIL]` lines with a one-line summary at
   the end (`all checks passed` / `SOME CHECKS FAILED`). A FAIL must not
   abort the render or the WAV write — the audio is still wanted for
   listening either way.

## The standard check set

The default set for a song-form track (trim or extend per the notes doc,
never silently):

1. `intro/thesis < verse 1 < chorus 1` — the opening ascends.
2. `chorus > its pre-chorus/build` — the drop actually lands.
3. later choruses `>=` earlier ones — development adds, never subtracts.
4. the final (everything-)chorus is the loudest section of the track.
5. every break/bridge is a trough — quieter than both its neighbours.
6. the outro settles — below the final chorus, back toward intro level.
7. hook count `>=` the target from the notes doc.

## Reference computation

```python
def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)

checks = [("chorus4 is the loudest section", R["CHORUS 4"] == max(R.values())),
          # ... the set agreed in the notes doc ...
          ]
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
```

**Rebalancing tip** (learned on lost_v6): `commit()` peak-normalizes each
layer, so making one section louder *within* a layer partly self-defeats —
the layer's peak rises and the whole layer scales down. To move a
section's RMS, change what *plays* there (sub weight, pad gain, density,
an octave doubling) rather than pushing one layer's commit weight; and
remember the low shelf makes sub content the strongest RMS lever.

## Variants by track type

Not everything is a song. Keep blocks 1, 3 and 4 always; swap the check
set for what the form actually promises:

- **Machine scores / no pop form** (tech_noir): hook count becomes the
  motif statement count; chorus checks are replaced by piece-specific
  ordering (e.g. the fusion section loudest, the answer section quieter
  than the question section, outro settling) plus "ends cold": the last
  audio event is a hard stop, no fade tail.
- **Two-reveal form** (ungeschrieben): the promise is that the theme is
  a *reveal*, so the thesis check flips — **zero** full statements
  before reveal 1 (one drowned foreshadow fragment allowed, uncounted).
  Ordering: the reduction is the trough between the reveals, reveal 2
  is the loudest section, the outro lands back near the intro. When the
  development lives in an automation curve (the filter arc), print the
  curve's value at every boundary and check its shape from the curve
  itself, not the audio (rise / global max inside the peak section /
  return to the opening value).
- **Vocal songs** (unsung): the standard song-form set, plus two checks
  the voice itself must pass. **Vocal pitch**: for every sung note the
  script re-measures the f0 of the *rendered* syllable and prints target
  vs measured in cents; median |error| <= 35 cents, max <= 60. **Duet
  separation**: printed overlap ratio of refrain vs countermelody
  activity per chorus — early choruses near zero (they trade), the
  fusion chorus substantially overlapped (earned, not default). The
  `VOICE_MODE`/`VOICE_GAIN` knobs are printed; in "instrumental" mode
  the hook-count target still holds (lead-carried statements count
  instead) and the pitch check is skipped, not failed.
- **Seamless state loops** (stillsuit, arrakis_winds_v3,
  spice_must_flow): the promise is *nothing ever builds*. Check a flat
  RMS trend — 1-second RMS series, first half vs second half within a few
  percent (or fitted slope ~0) — and print the loop-fold parameters
  (fold length, grid alignment). No ordering checks: there is no arc.
- **Overlays** (sandstorm_coriolis): the promise is *no lulls*. Check
  min/mean of 1-second RMS above the agreed floor (0.8 there).

(The loop/overlay figures are currently recorded in `dune/README.md` from
development-time measurement; when those scripts are next revised, move
the measurement into the script printout like the song tracks.)

## Developing the checks

- **Notes doc first.** A new check is proposed in the track's design
  notes, reviewed (the open-questions flow), then implemented. The
  printout should match the notes' Verify paragraph line for line.
- **A FAIL means fix the music** — density, register, sub weight — not
  delete the check. If the piece genuinely wants a different shape (the
  standing principle: the rules serve the music, not the other way
  around), change the notes doc *and* the check together, in the same
  commit, so the receipt still matches the intent.
- Checks must need no ears and no luck: post-master signal only, explicit
  thresholds, seeded RNG.
- When revising an old track (`_vN`), bring its printout up to this
  standard as part of the revision.
