# The goa/psy instrument library -- tracks/psy/instruments/

Single sounds extracted from the three goa scripts in `../`
(`meridian.py`, `phototaxis.py`, `phototaxis_v2.py`) as importable modules.
**No track script was modified** -- they stay standalone ("copy, don't
import", `../CLAUDE.md`); this directory is the same deliberate departure
that `tracks/dune/instruments`, `tracks/ebm/instruments` and
`tracks/trance/instruments` made. Read `../CLAUDE.md` first: the goa
freshness contract (FM/PM only, zero saw stacks, zero `iirpeak`) applies to
every voice here, and the **glint** is a listen-confirmed keeper.

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
from leads import gurgle_note_v2, glint_note
from drums import goa_kick
```

```bash
cd tracks/psy/instruments
python3 leads.py                 # -> auditions/leads.wav (gitignored scratch)
python3 fx.py --out /tmp/fx.wav
```

Each module's `__main__` renders every function with gaps between hits and
asserts finite / non-silent / peak <= 1.5 (`_common.run_audition`).

## Modules

| module | functions (public name <- source) |
|---|---|
| `_common.py` | `SR`, `BPM=147`/`BEAT`/`SIXT`/`BAR`, `midi_to_hz`, `add_at`, shared DSP primitives `lowpass`, `highpass`, `rc_attack`, `pm_core`, `slow_noise`, `make_reverb_ir` (byte-identical in all three scripts), audition helpers |
| `leads.py` | `gurgle_note_v2` (phototaxis_v2), `gurgle_note` (phototaxis v1), `fizz_note` (phototaxis v1/v2), `fizz_note_meridian`, `glint_note`, `murk_note` (identical in all three), `lead_note` (meridian) |
| `bass.py` | `bass_note` (phototaxis_v2), `bass_note_v1`, `bass_note_meridian` |
| `pads.py` | `pad_bed`, `underglow_chord` (stereo), `pool_drone` (phototaxis), `pool_drone_meridian` |
| `drums.py` | `goa_kick` (phototaxis), `goa_kick_meridian`, `open_hat`, `closed_hat`, `snare` |
| `fx.py` | `chatter_burst`, `bubble_rise` (phototaxis), `snap`, `tape_flutter`, `harmonic_bloom` (meridian) |

## Reconciliation (which script differs)

Survey by hashing each function's source across the three scripts:

| function | result |
|---|---|
| `pm_core`, `rc_attack`, `lowpass`, `highpass`, `slow_noise`, `make_reverb_ir`, `glint_note`, `murk_note`, `open_hat`, `closed_hat`, `snare` | identical in all three |
| `gurgle_note` | v1 vs v2 differ (v2: held notes ring 0.22 s); not in meridian |
| `fizz_note`, `pool_drone`, `goa_kick` | phototaxis v1 == v2; meridian differs -> `*_meridian` |
| `bass_note` | three different versions |
| `pad_bed` | v2 == meridian (not in v1) |
| `underglow_chord`, `chatter_burst`, `bubble_rise`, `snap` | phototaxis v1 == v2 (not in meridian) |
| `tape_flutter`, `harmonic_bloom`, `lead_note` | meridian only |

The unsuffixed name is the current (phototaxis_v2) version unless said
otherwise in the module docstring.

## Layer-writing functions converted

`chatter_burst`, `bubble_rise`, `tape_flutter`, `harmonic_bloom` write into
a caller-supplied stereo `layer` pair at an absolute time in the scripts.
Here they **return a stereo `(L, R)` pair** and the caller places it (using
its own `add_at`, as with every other voice). Offsets:

- `chatter_burst()` -> place at the burst start `t0` (blip times were `t0 + ...`).
- `bubble_rise()` -> length `2 * BAR`; place at `t_end - 2 * BAR`.
- `tape_flutter(dur, root_midi)` -> place at `t0`.
- `harmonic_bloom(root_midi, major)` -> length `2 * BAR`; place at `t_end - 2 * BAR`.

The DSP bodies are unchanged; the `place(layer, ...)` pan helper is kept and
now targets a local `(L, R)` buffer. `place`, `SCALE_PCS`, `MORPH_HZ` and the
per-module `_cache` dicts came along verbatim with the functions that need
them (caches are never shared between different source scripts).

## Notes

- **`lead_note` is a recorded dead end** as a *goa* lead (meridian's verdict:
  "country/western harmonica"); it is here because it is a complete,
  working morphing-FM voice, not because it is a model for new goa tracks.
- Tempo: `BAR`/`SIXT` follow `_common.BPM = 147`. Meridian ran 145 BPM.
- Not extracted: `render_lead`, `deg2midi`, swarm cells, verification
  helpers -- composition / arrangement, not instruments.
