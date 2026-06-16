# reference/ — baseline renders

This directory holds WAV renders produced from the legacy generator scripts
*before* any refactoring. They are the listening-approved baseline against
which forge reproductions are compared.

## What goes here

One WAV per track listed in `forge/INVENTORY.md` (see "Reference renders
manifest"), plus a `stats.json` produced by:

```
cd /repos/music
python -m forge.tools.collect_stats reference/ reference/stats.json
```

`stats.json` records duration, peak, RMS, and per-section RMS for each WAV.

## How to produce the renders

The legacy scripts write to `/workspace/music/` by default. Before running
them, either:

- Set `OUT_DIR` at the top of each script to point here, or
- Symlink `/workspace/music` → this directory, or
- Run each script and copy the output here.

WAV files are **not** tracked in git (they are large binaries). Add them
locally and commit only `stats.json` as the machine-readable record of what
the reference sounds like.

## stats.json schema

```json
{
  "script_name.wav": {
    "duration": 270.0,
    "sr": 44100,
    "n_channels": 2,
    "peak": 0.85,
    "rms": 0.12,
    "section_rms": [0.11, 0.12, ...]
  }
}
```
