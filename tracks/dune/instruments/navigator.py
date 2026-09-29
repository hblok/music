"""Instruments unique to `generate_the_navigator.py` (not reused, or not
reused unchanged, elsewhere in the dune catalog): a 2-operator FM lead
with a bright-to-warm filter sweep, a pulsed multi-formant choir pad, a
short FM arp pluck, a tuned tom-like "tarang doum" (tabla tarang), a tiny
gas-bubble foley blip, and a long inharmonic-partial "stillpoint" bell
hit.

Each function below is extracted verbatim (module-level constants
inlined) from `generate_the_navigator.py`; none of them appear in any
other dune generator, so there is no variant table for this module --
see README.md for the one-line pointer back to the source track.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, norm, out_arg, write_wav

rng = np.random.default_rng(2001)   # generate_the_navigator.py's seed

_fm_cache: dict = {}


def fm_lead_note(midi, dur_s, idx0=4.0, idx1=0.8, ratio=3.0):
    """2-operator FM lead, two detuned voices (+0.4%) for width: FM index
    decays from `idx0` (bright attack) to `idx1` (warmer sustain) with an
    0.18s time constant, modulator:carrier ratio `ratio`, a light 5.5 Hz
    vibrato that blooms in over 0.4s, and a bright/warm dual-filter
    (with resonance bump) crossfaded by an 0.12s sweep envelope. Returns
    a stereo `(L, R)` pair, peak-normalized together."""
    key = (midi, round(dur_s, 3))
    if key in _fm_cache:
        return _fm_cache[key]
    f = midi_to_hz(midi)
    n = int((dur_s + 0.10) * SR)
    td = np.arange(n) / SR
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * td) * np.clip(td / 0.4, 0, 1)
    idx = idx0 * np.exp(-td / 0.18) + idx1 * (1 - np.exp(-td / 0.18))
    ph_c = 2 * np.pi * np.cumsum(f * vib) / SR
    ph_c2 = 2 * np.pi * np.cumsum(f * 1.004 * vib) / SR
    ph_m = 2 * np.pi * f * ratio * td
    y1 = np.sin(ph_c + idx * np.sin(ph_m))
    y2 = np.sin(ph_c2 + idx * np.sin(ph_m * 1.004))

    sos_hi = signal.butter(2, min(4200, SR // 2 - 100), "low", fs=SR, output="sos")
    sos_lo = signal.butter(2, 1500, "low", fs=SR, output="sos")
    bpk_hi, apk_hi = signal.iirpeak(min(3800, SR // 2 - 100), Q=8.0, fs=SR)
    bpk_lo, apk_lo = signal.iirpeak(1300, Q=7.0, fs=SR)

    def filt(y):
        yh = signal.sosfilt(sos_hi, y)
        yh += 1.2 * signal.lfilter(bpk_hi, apk_hi, yh)
        yl = signal.sosfilt(sos_lo, y)
        yl += 1.1 * signal.lfilter(bpk_lo, apk_lo, yl)
        sw = np.exp(-td / 0.12)
        return np.tanh(1.8 * (sw * yh + (1 - sw) * yl))

    y1 = filt(y1)
    y2 = filt(y2)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur_s - td) / 0.025, 0, 1)
    y1 *= env
    y2 *= env
    pk = max(np.max(np.abs(y1)), np.max(np.abs(y2)), 1e-12)
    result = (y1 / pk, y2 / pk)
    _fm_cache[key] = result
    return result


def choir_pad(notes_midi, dur, pulse_hz=0.065, seed_off=0):
    """Multi-formant ambient choir pad: each note is 6 detuned-phase
    harmonics (1/k**0.75) passed through three formant bands, plus two
    slightly-detuned low-passed sub-layers for width, all gated by a
    slow (0.065 Hz default) "true-zero" pulse envelope so it never drones
    at a fixed level (anti-tinnitus by design) and a 4s attack/release.
    Uses its own private `rng` seeded from `3000 + seed_off` so repeated
    calls with different `seed_off` give independent-sounding pads."""
    r2 = np.random.default_rng(3000 + seed_off)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes_midi:
        f = midi_to_hz(m)
        src = np.zeros(n)
        for k in range(1, 7):
            src += np.sin(2 * np.pi * k * f * tt +
                          r2.uniform(0, 2 * np.pi)) / k ** 0.75
        for (lo, hi), g in [((650, 760), 1.0),
                            ((1000, 1200), 0.60),
                            ((2400, 2800), 0.18)]:
            sos_f = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
            out += g * signal.sosfilt(sos_f, src)
        for det in (0.993, 1.007):
            src2 = np.zeros(n)
            for k in range(1, 5):
                src2 += np.sin(2 * np.pi * k * f * det * tt +
                               r2.uniform(0, 2 * np.pi)) / k
            sos_lo2 = signal.butter(2, 1500, "low", fs=SR, output="sos")
            out += 0.22 * signal.sosfilt(sos_lo2, src2)
    pulse = np.clip(np.sin(2 * np.pi * pulse_hz * tt), 0, 1) ** 2
    env = np.minimum(np.clip(tt / 4.0, 0, 1),
                      np.clip((dur - tt) / 4.0, 0, 1))
    out *= pulse * env
    return norm(out)


def arp_pluck(midi):
    """Short FM arp pluck: modulator:carrier ratio 1 ("warm" FM), a fast
    (32 ms) index decay, band-passed 900-8000 Hz, ~45 ms total length --
    the bright, quick pluck used to build the_navigator's arpeggio
    lines."""
    f = midi_to_hz(midi)
    n = int(0.13 * SR)
    td = np.arange(n) / SR
    idx = 2.0 * np.exp(-td / 0.032) + 0.22
    ph_m = 2 * np.pi * f * td
    ph_c = 2 * np.pi * f * td + idx * np.sin(ph_m)
    y = np.sin(ph_c)
    sos_bp = signal.butter(2, [900, 8000], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos_bp, y)
    env = np.exp(-td * 22.0) * (1 - np.exp(-td / 0.002))
    y *= env
    return norm(y)


def tarang_doum(root_midi=40, ring_midi=47, sub_hz0=50.0, sub_hz1=22.0):
    """Tuned tom / tabla-tarang "doum": a pitched thump gliding down two
    semitone-ish steps (root default E2/MIDI 40: 112->82 Hz), a short
    ringing overtone at `ring_midi` (default MIDI 47), and a sub-thump
    layer -- the melodic tuned-drum voice used to carry the_navigator's
    tabla-tarang runs."""
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    f_curve = midi_to_hz(root_midi) + 30.0 * np.exp(-td * 22.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring_b = 0.28 * np.sin(2 * np.pi * midi_to_hz(ring_midi) * td) * np.exp(-td * 26)
    f_sub = sub_hz0 + sub_hz1 * np.exp(-td * 18.0)
    sub = 0.35 * np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
    env = np.exp(-td * 11.0) * (1 - np.exp(-td * 400))
    x = (body + ring_b + sub) * env
    return norm(x)


def gas_bubble(dur_ms=22):
    """Tiny bandpassed-noise + fast pitch-drop foley blip -- a "gas
    bubble" texture accent, ~20 ms long."""
    n = int(dur_ms * SR / 1000)
    td = np.arange(n) / SR
    sos_b = signal.butter(2, [400, 3000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_b, rng.standard_normal(n))
    f_curve = 280.0 + 900.0 * np.exp(-td * 90.0)
    x += 0.55 * (np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 75.0))
    env = np.exp(-td * 55.0) * (1 - np.exp(-td * 900.0))
    x *= env
    return norm(x)


def stillpoint_hit(root_midi=52):
    """Long (9s) inharmonic-partial bell/gong hit -- 4 non-integer
    partial ratios (1, 2.756, 5.404, 8.933) at random phase, highpassed
    at 400 Hz, a slow (0.55 Np/s) decay -- the_navigator's "stillpoint"
    signature hit. Default root MIDI 52 = E3 (~164 Hz)."""
    n = int(9.0 * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(root_midi)
    partials = [(1.0, 1.0), (2.756, 0.52), (5.404, 0.32), (8.933, 0.18)]
    x = np.zeros(n)
    for ratio, amp in partials:
        x += amp * np.sin(2 * np.pi * f * ratio * td + rng.uniform(0, 2 * np.pi))
    sos_hi = signal.butter(2, 400, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_hi, x)
    env = (1 - np.exp(-td / 0.018)) * np.exp(-td * 0.55)
    x *= env
    return norm(x)


if __name__ == "__main__":
    out = out_arg("navigator")
    from _common import concat

    lead_l, lead_r = fm_lead_note(64, 0.6)
    pad = choir_pad([48, 55, 60], 3.0)
    arp = concat([arp_pluck(m) for m in (60, 64, 67, 72)], gap=0.02)
    doum = tarang_doum()
    bubble = gas_bubble()
    still = stillpoint_hit()[: int(2.5 * SR)]  # trim the 9s tail for the demo
    demo = concat([lead_l, pad, arp, doum, bubble, still], gap=0.25)
    write_wav(out, demo)
    for x in (lead_l, lead_r, pad, arp, doum, bubble, still):
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    print("navigator.py: peak/finite OK; FM lead/pad/arp/tarang/bubble/stillpoint rendered")
