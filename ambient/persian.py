"""
Persian / Arabic ambient trance — inspired by Persian_Trance_LdGhQaBCbcE.mp3

C Phrygian Dominant (Maqam Hijaz / Dastgah Homayoun): C D♭ E F G A♭ B♭
96 BPM · 192 bars · 480 s ≈ 8 minutes

Output: /workspace/music/qasida.wav
Run:    python3 -m ambient.persian
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from forge.core.reverb import make_reverb_ir, reverb
from forge.core.mastering import master
from forge.instruments.voices import voice_phrase, choir
from forge.instruments.strings import pad_chord, santur, oud
from forge.instruments.bass import psy_bass_note
from forge.instruments.percussion import make_doum, make_tek
from forge.instruments.textures import wind, drone

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — INSTRUMENTS & EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

SR = 44100

# ── Timing ────────────────────────────────────────────────────────────────────
BPM    = 96
BEAT   = 60.0 / BPM          # 0.625 s
BAR    = 4 * BEAT             # 2.5 s
STEP   = BEAT / 4             # 0.15625 s  (16th note)
TOTAL  = 192 * BAR            # 480 s

# Section boundaries (seconds)
T_INTRO  = 0
T_RISE   = 32  * BAR   #  80 s
T_BUILD  = 64  * BAR   # 160 s
T_PEAK   = 96  * BAR   # 240 s
T_UNWIND = 160 * BAR   # 400 s
T_OUTRO  = 184 * BAR   # 460 s
T_END    = TOTAL        # 480 s

# ── Scale: C Phrygian Dominant ─────────────────────────────────────────────────
# MIDI constants; suffix = octave
C2, Db2, E2, F2, G2, Ab2, Bb2 = 36, 37, 40, 41, 43, 44, 46
C3, Db3, E3, F3, G3, Ab3, Bb3 = 48, 49, 52, 53, 55, 56, 58
C4, Db4, E4, F4, G4, Ab4, Bb4 = 60, 61, 64, 65, 67, 68, 70
C5, Db5, E5, F5, G5             = 72, 73, 76, 77, 79

# ── Reverb IRs (short instruments only; no reverb on drone/wind/pad) ──────────
IR_ROOM_L = make_reverb_ir(1.8, 1.4, seed=3,  sr=SR)
IR_ROOM_R = make_reverb_ir(1.8, 1.4, seed=5,  sr=SR)
IR_HALL_L = make_reverb_ir(2.5, 2.0, seed=7,  sr=SR)
IR_HALL_R = make_reverb_ir(2.5, 2.0, seed=11, sr=SR)

# ── Ney phrases (voice_phrase notes = [(midi, dur_s), ...]) ───────────────────
NEY_PHRASE_A = [
    (C4, 2.5), (G4, 2.0), (F4, 1.5), (E4, 0.5), (Db4, 2.0), (C4, 3.5)
]  # ~12 s — descending resolve

NEY_PHRASE_B = [
    (C5, 1.5), (Bb4, 0.5), (Ab4, 0.5), (G4, 2.5),
    (F4, 1.0), (E4, 0.5), (Db4, 1.5), (C4, 4.0)
]  # ~12 s — high entry, long fall

NEY_PHRASE_C = [
    (G4, 0.5), (Ab4, 0.5), (G4, 0.5), (F4, 0.5),
    (E4, 1.0), (Db4, 1.0), (C4, 1.0), (G4, 3.0), (C4, 3.0)
]  # ~11 s — ornamental turn

NEY_PHRASE_OUTRO = [
    (C4, 5.0), (Db4, 3.0), (C4, 7.0)
]  # 15 s — sparse farewell

# ── Oud phrases [(midi, t_offset_within_phrase, note_dur_s), ...] ─────────────
# Each tuple specifies when inside the phrase the note is plucked (overlapping).
OUD_PHRASE_A = [
    (C4,  0.0, 1.2), (Bb3, 0.5, 1.2), (G3,  1.0, 1.2),
    (E3,  1.5, 1.2), (Db3, 2.0, 1.8), (C3,  2.5, 3.5),
]  # ~6 s descending line

OUD_PHRASE_B = [
    (G3,  0.0, 1.2), (Ab3, 0.5, 1.2), (G3,  1.0, 1.2),
    (F3,  1.5, 1.2), (E3,  2.0, 1.2), (Db3, 2.5, 1.8), (C3, 3.5, 3.5),
]  # ~7 s upper-neighbour phrase

# ── Darbuka pattern — Maqsum-inspired, 16 steps per bar ──────────────────────
# Keys = step index (0–15); values = velocity (0–1)
_DOUM_STEPS  = {0: 0.85, 6: 0.55, 8: 0.70}
_TEK_STEPS   = {4: 0.70, 12: 0.65}
_GHOST_STEPS = {14: 0.28}   # ghost tek at step 14

# ── Pad chord ─────────────────────────────────────────────────────────────────
# Open 5th + min7 — no 3rd, ambiguous major/minor, very sustaining
_PAD_NOTES  = [C4, G4, Bb4]

# ── Choir chord (one octave lower, formant "oo") ──────────────────────────────
_CHOIR_NOTES = [C3, G3, Bb3]

# ── Santur ascending run pitches ──────────────────────────────────────────────
_SANTUR_PITCHES = [C4, E4, G4, Ab4, Bb4, C5]


# ── Render helpers ─────────────────────────────────────────────────────────────

def render_drone(rng: RngContext, dur: float) -> np.ndarray:
    """Sub-bass drone on C2; returns (N,2) stereo array."""
    ab = drone(
        {"duration": dur, "midi_root": C2, "breath_depth": 0.25,
         "breath_rate": 0.008, "beat_detune": 0.002},
        rng.spawn("drone").rng, sr=SR,
    )
    return ab.data


def render_wind(rng: RngContext, dur: float) -> np.ndarray:
    """Atmospheric wind noise; returns (N,2)."""
    ab = wind(
        {"duration": dur, "whoosh_lo": 80.0, "whoosh_hi": 600.0,
         "hiss_level": 0.15, "gust_rate": 0.18, "swell_rate": 0.07},
        rng.spawn("wind").rng, sr=SR,
    )
    return ab.data


def render_pad(rng: RngContext, dur: float) -> np.ndarray:
    """Sustained detuned-saw pad chord; returns (N,2). No reverb (too long)."""
    ab = pad_chord(
        {"midi_notes": _PAD_NOTES, "duration": dur,
         "attack": 4.0, "release": 6.0, "lp_cutoff": 1600.0, "detune": 0.0015},
        rng.spawn("pad").rng, sr=SR,
    )
    return ab.data


def render_choir(rng: RngContext, dur: float) -> np.ndarray:
    """Choir swell with hall reverb; returns (N,2)."""
    tail_s = 3.0
    ab = choir(
        {"midi_notes": _CHOIR_NOTES, "vowel": "oo", "duration": dur,
         "detune": 0.003, "n_harmonics": 8},
        rng.spawn("choir").rng, sr=SR,
    )
    L, R = ab.data[:, 0].copy(), ab.data[:, 1].copy()
    pad_L = np.concatenate([L, np.zeros(int(tail_s * SR))])
    pad_R = np.concatenate([R, np.zeros(int(tail_s * SR))])
    out_L = reverb(pad_L, IR_HALL_L, wet=0.45)[:len(L)]
    out_R = reverb(pad_R, IR_HALL_R, wet=0.45)[:len(R)]
    return np.column_stack([out_L, out_R])


def render_ney(phrase: list, rng: RngContext) -> np.ndarray:
    """Single ney phrase with room reverb; returns (N,) mono."""
    tail_s = 2.5
    ab = voice_phrase(
        {"notes": phrase, "ney_mode": True, "breath_level": 0.12,
         "vibrato_depth": 0.005, "vibrato_rate": 5.0, "vibrato_bloom": 1.5,
         "lp_cutoff": 2000.0, "n_harmonics": 4},
        rng.rng, sr=SR,
    )
    mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
    padded = np.concatenate([mono, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.38)[:len(mono)]
    R = reverb(padded, IR_ROOM_R, wet=0.38)[:len(mono)]
    return np.column_stack([L, R])


def render_oud_phrase(phrase: list, rng: RngContext) -> np.ndarray:
    """Overlapping oud notes assembled into one stereo array with room reverb."""
    total = max(t + d for _, t, d in phrase) + 1.0
    n = int(total * SR)
    buf = np.zeros(n)
    r = rng.rng
    for midi, t_off, dur in phrase:
        ab = oud(
            {"midi": midi, "duration": dur, "detune": 0.004, "damp": 0.499},
            r, sr=SR,
        )
        note_mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        i0 = int(t_off * SR)
        end = min(i0 + len(note_mono), n)
        buf[i0:end] += note_mono[:end - i0]

    tail_s = 2.0
    padded = np.concatenate([buf, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.32)[:n]
    R = reverb(padded, IR_ROOM_R, wet=0.32)[:n]
    return np.column_stack([L, R])


def render_santur_run(rng: RngContext) -> np.ndarray:
    """Ascending ornamental run; returns stereo (N,2)."""
    r = rng.rng
    buf = None
    pos = 0
    for midi in _SANTUR_PITCHES:
        ab = santur(
            {"midi": midi, "duration": 1.4, "detune": 0.0015,
             "damp": 0.997, "decay_rate": 1.8},
            r, sr=SR,
        )
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        if buf is None:
            buf = np.zeros(int((len(_SANTUR_PITCHES) * 0.35 + 1.4) * SR))
        i0 = int(pos * SR)
        end = min(i0 + len(mono), len(buf))
        buf[i0:end] += mono[:end - i0]
        pos += 0.35  # stagger

    tail_s = 2.0
    padded = np.concatenate([buf, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.40)[:len(buf)]
    R = reverb(padded, IR_ROOM_R, wet=0.40)[:len(buf)]
    return np.column_stack([L, R])


def render_bass_hit(midi: int, rng: RngContext) -> np.ndarray:
    """Single psy-bass note; returns (N,) mono."""
    ab = psy_bass_note(
        {"midi": midi, "duration": 0.55, "decay_mult": 5.0},
        rng.rng, sr=SR,
    )
    return (ab.data[:, 0] + ab.data[:, 1]) * 0.5


def render_darbuka_bar(rng: RngContext, humanise: float = 0.01) -> np.ndarray:
    """One bar of Maqsum-inspired darbuka; returns (N,) mono."""
    n = int(BAR * SR)
    buf = np.zeros(n)
    r = rng.rng
    for step, vel in _DOUM_STEPS.items():
        ab = make_doum({"f0": 140.0, "f1": 80.0, "duration": 0.45, "gain": vel},
                       r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    for step, vel in _TEK_STEPS.items():
        ab = make_tek({"ghost": False, "duration": 0.18}, r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5 * vel
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    for step, vel in _GHOST_STEPS.items():
        ab = make_tek({"ghost": True, "duration": 0.18}, r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5 * vel
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    return buf


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — COMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════

def compose(seed: int = 42) -> AudioBuffer:
    mix = AudioBuffer(int(TOTAL * SR), SR)
    rng = RngContext(seed)

    # ── DRONE & WIND (full track) ─────────────────────────────────────────────
    # The drone fades in over the first 20 s; no reverb needed — it's already
    # modal and spacious.  Wind enters at T_RISE and fades out at T_OUTRO.
    drone_data = render_drone(rng, TOTAL)
    fade_in = int(20.0 * SR)
    ramp = np.linspace(0, 1, fade_in)
    drone_data[:fade_in, 0] *= ramp
    drone_data[:fade_in, 1] *= ramp
    mix.add_at(drone_data, 0.0, gain=0.45)

    wind_dur = T_OUTRO - T_RISE + 10.0
    wind_data = render_wind(rng, wind_dur)
    fade_wind = int(8.0 * SR)
    wind_data[:fade_wind, 0] *= np.linspace(0, 1, fade_wind)
    wind_data[:fade_wind, 1] *= np.linspace(0, 1, fade_wind)
    wind_data[-fade_wind:, 0] *= np.linspace(1, 0, fade_wind)
    wind_data[-fade_wind:, 1] *= np.linspace(1, 0, fade_wind)
    mix.add_at(wind_data, T_RISE, gain=0.22)

    # ── PAD (intro through unwind) ────────────────────────────────────────────
    # Overlap two long pads so the crossfade stays smooth.
    pad_dur = T_UNWIND - T_INTRO + 8.0
    pad_data = render_pad(rng, pad_dur)
    mix.add_at(pad_data, T_INTRO, gain=0.30)

    # ── CHOIR (build → unwind, swells every 8 bars = 20 s) ───────────────────
    choir_rng = rng.spawn("choir_placements")
    choir_swell_dur = 8 * BAR + 4.0   # 24 s with slow release
    t = T_BUILD
    while t < T_UNWIND:
        ch = render_choir(choir_rng.spawn(f"ch_{t:.0f}"), choir_swell_dur)
        # fade edges so consecutive swells blend
        fade_ch = int(4.0 * SR)
        ch[:fade_ch, :] *= np.linspace(0, 1, fade_ch)[:, None]
        ch[-fade_ch:, :] *= np.linspace(1, 0, fade_ch)[:, None]
        mix.add_at(ch, t, gain=0.20)
        t += 16 * BAR   # every 16 bars (40 s)

    # ── NEY PHRASES (RISE → OUTRO) ────────────────────────────────────────────
    # Phrases appear every ~4 bars; rotate A/B/C; sparser in UNWIND section.
    ney_rng  = rng.spawn("ney")
    phrases  = [NEY_PHRASE_A, NEY_PHRASE_B, NEY_PHRASE_C]
    t        = T_RISE
    phrase_i = 0
    while t < T_OUTRO:
        ph = phrases[phrase_i % 3]
        ney_data = render_ney(ph, ney_rng.spawn(f"ney_{t:.0f}"))
        mix.add_at(ney_data, t, gain=0.50)
        # longer gap in unwind
        gap_bars = 8 if t < T_UNWIND else 12
        t += gap_bars * BAR + ney_rng.spawn(f"gap_{t:.0f}").rng.uniform(-BAR, BAR)
        phrase_i += 1

    # Outro: sparse farewell phrase
    ney_outro = render_ney(NEY_PHRASE_OUTRO, ney_rng.spawn("outro"))
    mix.add_at(ney_outro, T_OUTRO + 4 * BAR, gain=0.45)

    # ── OUD PHRASES (BUILD → UNWIND) ─────────────────────────────────────────
    # Two-phrase call-response pairs placed every 12 bars.
    oud_rng = rng.spawn("oud")
    t = T_BUILD
    alt = False
    while t < T_UNWIND:
        ph = OUD_PHRASE_B if alt else OUD_PHRASE_A
        oud_data = render_oud_phrase(ph, oud_rng.spawn(f"oud_{t:.0f}"))
        mix.add_at(oud_data, t, gain=0.38)
        t += 12 * BAR
        alt = not alt

    # ── SANTUR RUNS (PEAK only, every 8 bars) ─────────────────────────────────
    santur_rng = rng.spawn("santur")
    t = T_PEAK
    while t < T_UNWIND:
        run = render_santur_run(santur_rng.spawn(f"s_{t:.0f}"))
        mix.add_at(run, t, gain=0.28)
        t += 8 * BAR

    # ── SUB-BASS HITS (RISE → UNWIND, every beat on step 0 and step 8) ───────
    bass_rng = rng.spawn("bass")
    for bar_idx in range(int(T_RISE / BAR), int(T_UNWIND / BAR)):
        t_bar = bar_idx * BAR
        gain_bass = 0.65 if t_bar < T_PEAK else 0.50
        for step in (0, 8):
            midi = C2 if step == 0 else G2
            hit = render_bass_hit(midi, bass_rng.spawn(f"b_{bar_idx}_{step}"))
            mix.add_at(hit, t_bar + step * STEP, gain=gain_bass)

    # ── DARBUKA (RISE → UNWIND) ───────────────────────────────────────────────
    # Builds in gradually over 16 bars, fades out over the last 16.
    perc_rng   = rng.spawn("perc")
    n_bars     = int((T_UNWIND - T_RISE) / BAR)
    ramp_bars  = 16
    for i in range(n_bars):
        t_bar   = T_RISE + i * BAR
        fade_g  = min(i, ramp_bars) / ramp_bars                     # fade-in
        fade_g *= min(n_bars - i, ramp_bars) / ramp_bars            # fade-out
        bar_buf = render_darbuka_bar(perc_rng.spawn(f"p_{i}"))
        mix.add_at(bar_buf, t_bar, gain=0.55 * fade_g)

    # ── MASTER bus ────────────────────────────────────────────────────────────
    return master(mix, target=0.88, fade_out_s=4.0)


def main() -> None:
    out_path = Path("/workspace/music/qasida.wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("Composing qasida …")
    mix = compose(seed=42)
    sf.write(str(out_path), mix.data, SR, subtype="PCM_24")
    duration = len(mix.data) / SR
    print(f"Written {out_path}  ({duration:.0f} s, {SR} Hz, 24-bit PCM)")


if __name__ == "__main__":
    main()
