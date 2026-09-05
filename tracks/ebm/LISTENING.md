# LISTENING.md — A/B and stem workflow for the ebm tracks

How to hear ONE change at a time. Two pieces: listening flags on the
track script, and `tools/ab.py` (repo root) that builds an ABAB file.
Written 2026-09-05 for `reliquary_v2.py`; new track scripts in this
directory should carry the same flags (copy the `argparse` block, the
`want()` guards and the output block).

## The flags (track script)

```
python3 reliquary_v2.py                          # the piece: full render, checks run
python3 reliquary_v2.py --solo lead              # only these layers, through the master
python3 reliquary_v2.py --solo lead,bass
python3 reliquary_v2.py --mute drums             # everything but these
python3 reliquary_v2.py --slice 24 32            # bars [24, 32) only (hook 1 alone)
python3 reliquary_v2.py --suffix _leadA          # output <NAME>_leadA.wav / .flac
python3 reliquary_v2.py --stems                  # + <NAME>_stems/<layer>.wav, one per layer
```

- Flags combine: `--solo lead --slice 24 32 --suffix _leadA` is the
  usual call.
- `NAME` is one constant near the top of the script (`reliquary_v3.3`
  today). Bump it once per iteration; WAV, FLAC, suffixes and the stems
  directory all follow it.
- Layer names: `bed pad strings arp bass drums lead hit fx` (the
  `LAYER_NAMES` list in the script; a wrong name fails fast).
- A partial render (any of solo / mute / slice) skips the verify
  checks and prints that it did. **The piece is the full render** —
  only that is judged by the checks.
- Solo renders skip the work of the other layers (the seethe bed is the
  slow one), so a solo slice takes ~5 s instead of ~19 s.
- Stems are post-reverb, weighted, **pre-master** — the master (HP,
  shelf, tanh glue) is applied to the sum only, so stems don't add up
  bit-for-bit to the mix. Right for judging a voice; use `--solo` if
  you want to hear it through the master.
- A solo render is peak-normalised on its own, so its absolute level is
  not the in-context level. That is what `ab.py`'s level matching is for.

## The tool: `tools/ab.py`

```
python3 ../../tools/ab.py A.wav B.wav                  # 2-bar chunks, 122 BPM
python3 ../../tools/ab.py A.wav B.wav --bars 4
python3 ../../tools/ab.py A.wav B.wav --bpm 147 --out /tmp/ab.wav
python3 ../../tools/ab.py A.wav B.wav --no-match       # keep each file's own level
```

Same timeline, alternating source: chunk 1 from A, chunk 2 from B, chunk
3 from A … — the music continues, only the source switches, so the
difference lands every `--bars` bars instead of you switching files.
B is RMS-matched to A by default; 5 ms crossfades at the switches;
prints the switch times; writes `<A>_AB_<B>.wav` next to A unless
`--out`. Mono inputs are widened to stereo; sample rates must match.

## The workflow

Changing a voice (say `dark_lead`):

```bash
cd tracks/ebm
python3 reliquary_v2.py --solo lead --slice 24 32 --suffix _leadA      # BEFORE the edit
# edit dark_lead
python3 reliquary_v2.py --solo lead --slice 24 32 --suffix _leadB      # AFTER
python3 ../../tools/ab.py /workspace/music/reliquary_v3.3_leadA.wav \
                          /workspace/music/reliquary_v3.3_leadB.wav --bars 2
```

Listen to the ABAB file: A for two bars, B for two bars, four times
over hook 1. If you can't hear the switch, the change is below the
noise floor of your attention — make it bigger or drop it.

Then the same edit in context:

```bash
python3 reliquary_v2.py --slice 24 32 --suffix _ctxB                   # full mix, hook 1 only
python3 ../../tools/ab.py /workspace/music/reliquary_v3.3_ctxA.wav /workspace/music/reliquary_v3.3_ctxB.wav
```

(render `_ctxA` before the edit the same way). And the "does it sit"
check: `--mute lead --slice 24 32` is the bed of everything else.

## Which part to listen to

The script's section map prints the bar and the time of every section
and composed event (`=== SECTION MAP ===`). For Reliquary:

| what | bars | `--slice` |
|---|---|---|
| the bed alone, arp entering | 0–8 | `0 8` |
| the groove (808, bass, arp, pad) | 8–24 | `8 24` |
| hook 1 (the lead's first statement) | 24–32 | `24 32` |
| hook 2 (pad + strings, the heavier chest) | 32–40 | `32 40` |
| the cut, the tag, the out | 40–48 | `40 48` |

Rule of thumb: slice the section where the changed layer is most
exposed (the lead in hook 1, the bass in the groove, the strings in
hook 2), solo it for the voice itself, then the same slice in full for
the balance.

## Housekeeping

- Everything under `/workspace/music/` is ephemeral and never committed;
  the `_leadA`, `_stems/`, `_AB_` files pile up — delete freely.
- Keep the kept renders (`reliquary.wav`, `reliquary_v2.wav`, …): the
  listen verdicts refer to them. New iterations get a new `NAME`.
- When a voice change is a keeper, promote it to
  `instruments/` (with its audition) and note it in
  `instruments/README.md`; the notes doc gets a dated amendment.
