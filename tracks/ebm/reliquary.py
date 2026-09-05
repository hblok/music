#!/usr/bin/env python3
"""Reliquary (Part 1) — the first tracks/ebm/ track.

A 1:36 interlude in the mould of Soli Deo Gloria's opener: the seethe
bed from the first sample to the last, a Juno arp that IS the hook's
skeleton, an 808 and the Juno bass for the groove, the hook sung twice
by the Juno lead, and an open ending on E minor for a Part 2 to answer.
Design notes: reliquary_notes.md (answers + amendments).  Built entirely
from instruments/ (the declared import exception).

Output: /workspace/music/reliquary.wav + .flac (44100 Hz stereo 16-bit).
Seed 1993.  Prints the VERIFY.md blocks; a FAIL never aborts the render.
"""
from __future__ import annotations

import pathlib
import sys
import wave

import numpy as np
import soundfile
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "instruments"))
import _common                                                            # noqa: E402
from _common import BAR, BEAT, SR, STEP                                   # noqa: E402

_common.seed(1993)
from eps_hit import hit                                                   # noqa: E402
from juno import AM, F, G, arp, bass, chorus, lead, noise_sweep, pad, strings  # noqa: E402
from kit808 import hat, kick, snare                                       # noqa: E402
from seethe import seethe                                                 # noqa: E402

# ------------------------------------------------------------- the piece
EM = (52, 55, 59)                       # the open chord: E minor (Aeolian v)
TOTAL_BARS = 48
END = TOTAL_BARS * BAR + 0.3
N = int(END * SR)
SECTIONS = [("BED", 0, 8), ("GROOVE", 8, 24), ("HOOK 1", 24, 32), ("HOOK 2", 32, 40), ("OUT", 40, 48)]
ARP_CUTOFF = {"BED": 400.0, "GROOVE": 600.0, "HOOK 1": 700.0, "HOOK 2": 700.0, "OUT": 500.0}
ROOT = {AM: 45, F: 41, G: 43, EM: 40}
NOTE = {"E4": 64, "G4": 67, "A4": 69, "B4": 71, "C5": 72, "D5": 74}

HOOK = ["A4 - A4 C5 - - B4 -", "A4 - - - . E4 G4 A4", "B4 - A4 G4 A4 - - -", "E4 - - - - - . .",
        "A4 - A4 C5 - - D5 -", "D5 - - C5 . C5 B4 C5", "B4 - C5 B4 A4 - - -", "A4 - - - - - . ."]
TAG = ["A4 - G4 - E4 - - -", "- - - - - - . ."]

CUT_BAR = 40            # 808 + bass stop dead here
ARP_OUT_BAR = 45


def bar_t(b):
    return b * BAR


def section_of(bar):
    return next(name for name, b0, b1 in SECTIONS if b0 <= bar < b1)


def chord_at(bar):
    if bar < 8:
        return AM
    if bar < 32:
        return (AM, F, G, AM)[(bar - 8) % 4]
    if bar < 40:
        return (AM, F, G, EM)[(bar - 32) % 4]
    return EM


def parse(lines):
    """8th-note token lines -> [(start_8th, midi, len_8ths)]."""
    out = []
    for b, line in enumerate(lines):
        for i, tok in enumerate(line.split()):
            if tok in NOTE:
                out.append([b * 8 + i, NOTE[tok], 1])
            elif tok == "-" and out:
                out[-1][2] += 1
    return [tuple(e) for e in out]


# ---------------------------------------------------------------- helpers
def fade(x, fin=0.004, fout=0.05):
    y = x.copy()
    ni, no = int(fin * SR), int(fout * SR)
    if ni:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return y


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    b, a = signal.butter(2, 4000 / (SR / 2), "low")
    ir = signal.lfilter(b, a, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(4.0, 1.2, 7)
IR_R = make_reverb_ir(4.0, 1.2, 11)


def reverb_pair(L, R, wet):
    if wet <= 0.0:
        return L, R
    wL = signal.fftconvolve(L, IR_L)[: len(L)]
    wR = signal.fftconvolve(R, IR_R)[: len(R)]
    for d, w in ((L, wL), (R, wR)):
        w *= (np.max(np.abs(d)) + 1e-12) / (np.max(np.abs(w)) + 1e-12)
    return (1 - wet) * L + wet * wL, (1 - wet) * R + wet * wR


def highpass(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "high", fs=SR, output="sos"), x)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    if i0 >= len(buf):
        return
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


def place(layer, x, t, gain=1.0, pan=0.0):
    """Constant-power pan of a mono event into a stereo layer pair."""
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def place_stereo(layer, dry, t, gain=1.0):
    """The Juno stereo chorus: modulation inverted between the channels."""
    add_at(layer[0], chorus(dry, 1.0, "I", phase=0.0), t, gain)
    add_at(layer[1], chorus(dry, 1.0, "I", phase=np.pi), t, gain)


LAYER_NAMES = ["bed", "pad", "strings", "arp", "bass", "drums", "lead", "hit", "fx"]
LAYERS = {k: [np.zeros(N), np.zeros(N)] for k in LAYER_NAMES}
WETS = {"bed": 0.0, "pad": 0.35, "strings": 0.4, "arp": 0.15, "bass": 0.0, "drums": 0.06,
        "lead": 0.45, "hit": 0.3, "fx": 0.3}
WEIGHTS = {"bed": 0.30, "pad": 0.22, "strings": 0.26, "arp": 0.26, "bass": 0.32, "drums": 0.40,
           "lead": 0.34, "hit": 0.28, "fx": 0.14}

HOOKS = 0
lead_events = []            # (t, midi, dur)
strings_events = []         # (bar, chord)
drum_times = []
arp_table = []              # (bar, section, cutoff, rate)

# ------------------------------------------------------------------- bed
BED = seethe(45, END, throb=0.0, grit=0.25)
place(LAYERS["bed"], BED, 0.0)

# ------------------------------------------------------------- pad / strings
for b in range(0, 32):
    place_stereo(LAYERS["pad"], pad(chord_at(b), BAR, depth=0.0), bar_t(b))
for b in range(32, 40):
    place_stereo(LAYERS["strings"], strings(chord_at(b), BAR, depth=0.0), bar_t(b))
    strings_events.append((b, chord_at(b)))
place_stereo(LAYERS["strings"], strings(EM, 6 * BAR, depth=0.0), bar_t(40))
strings_events.append((40, EM))

# ------------------------------------------------------------------- arp
for b in range(4, ARP_OUT_BAR):
    sec = section_of(b)
    rate = 2 if b >= CUT_BAR else 1
    x = arp(chord_at(b), bars=1, pattern="updown", octaves=2, rate=rate, cutoff=ARP_CUTOFF[sec])
    place(LAYERS["arp"], x[: int(BAR * SR) + int(0.3 * SR)], bar_t(b), pan=-0.25)
    arp_table.append((b, sec, ARP_CUTOFF[sec], rate))

# ------------------------------------------------------------------ bass
BASS_CELL = "x.x.x.x.x.x.x.o."
for b in range(8, CUT_BAR):
    root = ROOT[chord_at(b)]
    for s, ch in enumerate(BASS_CELL):
        if ch != ".":
            place(LAYERS["bass"], bass(root + (12 if ch == "o" else 0), STEP), bar_t(b) + s * STEP)

# ----------------------------------------------------------------- drums
KICK, SNARE, CH, OH = kick(decay=0.2), snare(), hat(), hat(open_=True)
KICK_A, KICK_B = "x...x...x...x...", "x...x...x...x.x."
SNARE_P = "....x.......x..."
OH_P = "......x.......x."
for b in range(8, CUT_BAR):
    hooks = b >= 24
    kp = KICK_B if b % 2 else KICK_A
    for s in range(16):
        t = bar_t(b) + s * STEP
        if kp[s] == "x":
            place(LAYERS["drums"], KICK, t, 1.0)
            drum_times.append(t)
        if SNARE_P[s] == "x":
            place(LAYERS["drums"], SNARE, t, 0.8)
            drum_times.append(t)
        if hooks and OH_P[s] == "x":
            place(LAYERS["drums"], OH, t, 0.4, pan=0.3)
            drum_times.append(t)
        elif hooks or s % 2 == 0:                       # 8ths in the groove, 16ths in the hooks
            place(LAYERS["drums"], CH, t, 0.35 * (1.0 if s % 4 == 0 else 0.7 if s % 2 == 0 else 0.5), pan=0.2)
            drum_times.append(t)

# ------------------------------------------------------------------ lead
def place_line(lines, bar0, count=True):
    global HOOKS
    for start, midi, ln in parse(lines):
        t = bar_t(bar0) + start * BEAT / 2
        dur = ln * BEAT / 2 * 0.95
        place_stereo(LAYERS["lead"], lead(midi, dur, depth=0.0), t)
        lead_events.append((t, midi, dur))
    if count:
        HOOKS += 1


for bar0 in (24, 32):
    t_pick = bar_t(bar0) - BEAT / 2                     # the pickup on the & of 4
    place_stereo(LAYERS["lead"], lead(64, BEAT / 2 * 0.9, depth=0.0), t_pick)
    lead_events.append((t_pick, 64, BEAT / 2 * 0.9))
    place_line(HOOK, bar0)
place_line(TAG, 40, count=False)

# ------------------------------------------------------------ hit / fx
HIT = hit()
for b in (8, 32):
    place(LAYERS["hit"], HIT, bar_t(b), pan=0.3)
place(LAYERS["fx"], noise_sweep(2 * BAR, 200.0, 6000.0, res=3.0), bar_t(30))

# ------------------------------------------------------------------- mix
MIX = [np.zeros(N), np.zeros(N)]
PRE = {}                                                # post-reverb, weighted (for the checks)
for name in LAYER_NAMES:
    L, R = LAYERS[name]
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
    if pk < 1e-9:
        continue
    L, R = reverb_pair(L / pk, R / pk, WETS[name])
    PRE[name] = (WEIGHTS[name] * L, WEIGHTS[name] * R)
    MIX[0] += PRE[name][0]
    MIX[1] += PRE[name][1]

for ch in (0, 1):                                       # the minimal master: HP, shelf, glue
    MIX[ch] = highpass(MIX[ch], 30)
    MIX[ch] = MIX[ch] + 0.22 * highpass(MIX[ch], 3000)
pk = max(np.max(np.abs(MIX[0])), np.max(np.abs(MIX[1]))) + 1e-12
for ch in (0, 1):
    MIX[ch] = np.tanh(1.12 * MIX[ch] / pk) / np.tanh(1.12) * 0.92
OUT = np.stack([fade(MIX[0], 0.002, 0.03), fade(MIX[1], 0.002, 0.03)], axis=1)

out_dir = pathlib.Path("/workspace/music")
out_dir.mkdir(parents=True, exist_ok=True)
wav_path = out_dir / "reliquary.wav"
with wave.open(str(wav_path), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes((np.clip(OUT, -1, 1) * 32767).astype(np.int16).tobytes())
flac_path = out_dir / "reliquary.flac"
soundfile.write(str(flac_path), OUT, SR)
print(f"Wrote {wav_path}  ({END:.1f} s)")
print(f"Wrote {flac_path}")

# ---------------------------------------------------------------- verify
fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        fails.append(name)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def rms_between(x, t0, t1):
    seg = x[int(t0 * SR):int(t1 * SR)]
    return float(np.sqrt(np.mean(seg ** 2)))


def sec_rms(b0, b1):
    return float(np.sqrt((rms_between(OUT[:, 0], bar_t(b0), bar_t(b1)) ** 2
                          + rms_between(OUT[:, 1], bar_t(b0), bar_t(b1)) ** 2) / 2))


def sub_share(b0, b1, hz=60.0):
    seg = OUT[int(bar_t(b0) * SR):int(bar_t(b1) * SR)].mean(axis=1)
    X = np.abs(np.fft.rfft(seg)) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return float(X[f < hz].sum() / X.sum())


print("\n=== SECTION MAP ===")
for name, b0, b1 in SECTIONS:
    print(f"  {mmss(bar_t(b0)):>6}  bar {b0:2d}  {name}")
for t, what in ((bar_t(4), "arp in (dark)"), (bar_t(8), "808 + bass + hit 1"),
                (bar_t(24) - BEAT / 2, "lead pickup"), (bar_t(30), "noise sweep"),
                (bar_t(32), "hit 2, strings replace the pad, harmony Am-F-G-Em"),
                (bar_t(CUT_BAR), "THE CUT: 808 + bass stop; the tag over it"),
                (bar_t(ARP_OUT_BAR), "arp out"), (END, "end (cold, on the bed)")):
    print(f"  {mmss(t):>6}  {what}")
print("  arp cutoff table:", " ".join(f"{sec}:{int(c)}{'/8ths' if r == 2 else ''}"
                                      for sec, c, r in sorted({(s, c, r) for _, s, c, r in arp_table})))

print(f"\n=== HOOK COUNT ===\n  full lead statements: {HOOKS} (target >= 2); pickups + tag uncounted")
check("hook count >= 2", HOOKS >= 2)

print("\n=== SEAM CHECKLIST ===")
bedL = LAYERS["bed"][0]
win = int(0.25 * SR)
bed_rms = [float(np.sqrt(np.mean(bedL[i:i + win] ** 2)))
           for i in range(int(0.5 * SR), int((END - 0.3) * SR) - win, win)]
bed_ok = min(bed_rms) > 1e-3
print(f"  bed continuous 0.5 s .. end-0.3 s: min 0.25 s RMS {min(bed_rms):.4f}")
for b0, device in ((8, "808 + bass enter ON the bar with hit 1"), (24, "lead pickup E4 on the & of 4"),
                   (32, "hit 2 + the noise sweep landing"), (40, "the ringing Em strings + the lead tag across the cut")):
    print(f"  bar {b0:2d}: bed unbroken + {device}")
check("bed unbroken at every seam", bed_ok)

print("\n=== PER-SECTION RMS (post-master) ===")
R = {name: sec_rms(b0, b1) for name, b0, b1 in SECTIONS}
for name, b0, b1 in SECTIONS:
    print(f"  {name:8s} {R[name]:.3f}   sub-60 share {sub_share(b0, b1):.2f}")
check("bed < groove < hook1 <= hook2", R["BED"] < R["GROOVE"] < R["HOOK 1"] <= R["HOOK 2"] * 1.0001)
check("hook2 is the loudest", R["HOOK 2"] == max(R.values()))
check("out < groove", R["OUT"] < R["GROOVE"])
db = 20 * np.log10(R["OUT"] / R["BED"])
check("out within 6 dB of the bed", abs(db) <= 6, f"({db:+.1f} dB)")

print("\n=== ENDS OPEN ===")
last_chord = strings_events[-1][1]
last_lead = max(lead_events)[1]
last_drum = max(drum_times)
print(f"  last strings chord root: midi {last_chord[0]} ({'E' if last_chord[0] % 12 == 4 else '?'})   "
      f"last lead note: midi {last_lead}   last drum: bar {last_drum / BAR:.2f}")
check("last chord root is E", last_chord[0] % 12 == 4)
check("last lead note is E4 or B4", last_lead in (64, 71))
check("no drum onset at/after the cut", last_drum < bar_t(CUT_BAR) - 1e-6, f"(bar {last_drum / BAR:.2f})")
i0 = int((END - 1.0) * SR)
bed_last = np.sqrt(np.mean(PRE["bed"][0][i0:] ** 2 + PRE["bed"][1][i0:] ** 2))
other_last = np.sqrt(np.mean(sum(PRE[k][0][i0:] ** 2 + PRE[k][1][i0:] ** 2 for k in PRE if k != "bed")))
check("last second is bed-only (others < 25 % of bed)", other_last < 0.25 * bed_last,
      f"(ratio {other_last / bed_last:.2f})")

print("\n=== THE HOOK SINGS (from the HOOK table) ===")
ev = parse(HOOK)
onsets = len(ev)
density = onsets / 128
held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
run = best = 0
for _, _, ln in ev:
    run = run + 1 if ln == 1 else 0
    best = max(best, run)
q_end = [e for e in ev if e[0] < 32][-1]
a_end = ev[-1]
print(f"  onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  longest 8th run {best} (<= 4)")
print(f"  Q ends midi {q_end[1]} len {q_end[2]} 8ths;  A ends midi {a_end[1]} len {a_end[2]} 8ths")
check("density window 0.20-0.50", 0.20 <= density <= 0.50)
check("held fraction >= 0.5", held >= 0.5)
check("run ceiling <= 4", best <= 4)
check("phrase ends held >= a half note", q_end[2] >= 4 and a_end[2] >= 4)
check("Q hangs on E4, A lands on A4", q_end[1] == 64 and a_end[1] == 69)

print("\n=== BED CHECK (tinnitus rule) ===")
w2 = int(2.0 * SR)
peaks = []
for i in range(0, N - w2, w2):
    seg = bedL[i:i + w2] * np.hanning(w2)
    X = np.abs(np.fft.rfft(seg))
    f = np.fft.rfftfreq(w2, 1 / SR)
    m = f > 20
    peaks.append(float(f[m][np.argmax(X[m])]))
print(f"  strongest peak per 2 s: min {min(peaks):.0f} Hz, max {max(peaks):.0f} Hz over {len(peaks)} windows")
check("bed's strongest peak < 120 Hz in every window", max(peaks) < 120)

print("\n=== MASTER GUARDRAILS ===")
tp = float(np.max(np.abs(OUT)))
h2 = OUT[int(bar_t(32) * SR):int(bar_t(40) * SR)]
crest = float(np.max(np.abs(h2)) / np.sqrt(np.mean(h2 ** 2)))
print(f"  true peak {tp:.3f}   hook-2 crest {crest:.2f}")
check("true peak < 1.0", tp < 1.0)
check("hook-2 crest >= 3.2", crest >= 3.2)
check("FLAC written", flac_path.exists())

print("\nall checks passed" if not fails else f"SOME CHECKS FAILED: {fails}")
