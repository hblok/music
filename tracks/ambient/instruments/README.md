# The ambient instrument library -- tracks/ambient/instruments/

Voices extracted from `../lost.py` and `../persian.py` / `../persian_opus.py`
(plus one effect from `../../dune/generate_ambient.py`). **No track script was
modified.** `lost.py` is a top-level render script (importing it would render
the whole track), which is why its voices are copied here rather than
imported; `persian*.py` keep working exactly as before.

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
from lost_ambient import piano, cello_line
from persian import render_ney, render_drone
```

```bash
cd tracks/ambient/instruments
python3 lost_ambient.py            # -> auditions/lost_ambient.wav (gitignored scratch)
python3 persian.py --out /tmp/persian.wav
```

Each `__main__` renders every function with gaps and asserts finite /
non-silent / peak bound (`_common.run_audition`).

| module | functions |
|---|---|
| `_common.py` | `SR`, `midi_to_hz`, `add_at`, `write_wav`, `run_audition` (accepts mono, `(L, R)`, or `(N, 2)`) |
| `lost_ambient.py` (verbatim from `lost.py`, seed 1893) | `piano`, `harp` (Karplus-Strong), `cello`, `cello_line`, `flute`, `choir`, `bell`, `heart`, `chirp`, `swell` (stereo), `feedback_delay` (from `dune/generate_ambient.py`) |
| `persian.py` (from `persian_opus.py`, seed 42) | `render_drone`, `render_air`, `render_pad`, `render_choir`, `render_ney`, `render_oud_phrase`, `render_santur_run`, `render_bass_hit`, `render_darbuka_bar(fill=)`, `render_riq_hit`; and the earlier `persian.py` parameter sets as `render_drone_qasida`, `render_wind_qasida`, `render_pad_qasida`, `render_ney_qasida`, `render_santur_run_qasida`, `render_darbuka_bar_qasida` |

## Notes

- **`persian.py` depends on forge.** The qasida/opus `render_*` functions are
  parameter recipes + reverb treatment over `forge.instruments.*`, not
  standalone DSP, so the module imports forge (repo root added to `sys.path`,
  as the scripts do). The `RngContext` argument was replaced by a
  module-level `np.random.default_rng(42)`; `rng.spawn("x").rng` /
  `rng.rng` both became that generator. Signatures otherwise unchanged minus
  the `rng` parameter. `render_choir`, `render_oud_phrase`, `render_bass_hit`
  are identical in both scripts, hence no `_qasida` twin.
- Overlap check with `tracks/dune/instruments` (`duduk_ney`, `strings`,
  `darbuka`, `frame_drum`): those are separate standalone implementations;
  the persian renderers call forge, so nothing was merged or duplicated.
- `render_*` outputs are not peak-normalized (like the scripts, `master()`
  does it later); the audition allows peaks up to 3.0.
- `lost_ambient.heart` is the same recipe as
  `tracks/trance/instruments/drums.py:heart`; `glide_curve` (tau 0.06) came
  along with `cello_line` / `flute`.
- Not extracted: `compose()`/`main()`, section machinery
  (`lay_chords`, `arpeggiate`, `harp_offset`, `commit`), gains -- arrangement.
