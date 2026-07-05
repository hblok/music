# Plucks, Sequences & Stabs

Short-attack voices: arps, sequences, and punchy stabs.

## `pluck` — glassy pluck arp (canonical)

**Source:** `lost_v6.py:pluck`  
**Character:** the verse Q/A arpeggio voice, STEP×3 decay

```python
def pluck(midi, dur=STEP * 3):
    if midi in pluck_cache:
        return pluck_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for det in (0.998, 1.0, 1.002):
        for k in range(1, min(12, int(7000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td) / k ** 1.2
    v = signal.sosfilt(signal.butter(2, 3800, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.003)) * np.exp(-td * 9.0)
    pluck_cache[midi] = v / (np.max(np.abs(v)) + 1e-12)
    return pluck_cache[midi]
```

## `seq_pluck` — resonant era sequence — owned by ungeschrieben

**Source:** `ungeschrieben.py:seq_pluck`  
**Character:** Q 2.2 / blend 0.40 — THE sanctioned resonance exception, guardrailed (tanh 0.8, sine sub, cutoff always sweeping); cutoff-bucket cached against a printable filter arc

```python
def seq_pluck(midi, cutoff, dur=0.42):
    key = (midi, int(cutoff // 40))
    if key in seq_cache:
        return seq_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.1      # bright analog pluck
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(min(cutoff, 5000), Q=2.2, fs=SR)
    y = y + 0.40 * signal.lfilter(bpk, apk, y)              # the era resonance
    y += 0.25 * np.sin(2 * np.pi * (f / 2) * td)            # sub for body
    y = np.tanh(0.8 * y)                                    # soft, never acid
    y *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 9.0)
    seq_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return seq_cache[key]
```

## `make_stab` — dark gated chord stab (canonical)

**Source:** `nachtkind_v3.py:make_stab`  
**Character:** band-limited saw triad, LP 900, gated ~50 ms, offbeat, panned alternately; the additive-layer element

```python
def make_stab():
    dur = STEP * 1.6
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in (55, 58, 62):
        f = midi_to_hz(m)
        for k in range(1, min(12, int(2500 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k
    sos_s = signal.butter(2, 900, "low", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `stab_hit` — hammer stab — owned by eisgang

**Source:** `eisgang_v3.py:stab_hit`  
**Character:** hollow pulse pluck, gated 16th retrigger with a per-16th gain cell (chatters, never carpets); dry and close

```python
def stab_hit(midi, dur=0.20):
    if midi in stab_cache:
        return stab_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    k = 1
    while k * f < 5200:
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.25
        k += 2                                     # odd only: hollow
    x += 0.28 * np.sin(2 * np.pi * f * td)
    y = signal.sosfilt(signal.butter(2, 2000, "low", fs=SR, output="sos"), x)
    y = np.tanh(0.85 * y)
    y *= (1 - np.exp(-td / 0.0015)) * np.exp(-td * 15.0)
    stab_cache[midi] = y / (np.max(np.abs(y)) + 1e-12)
    return stab_cache[midi]
```

## `stab` — stab — penumbra variant

**Source:** `penumbra.py:stab`  
**Character:** penumbra's re-voiced stab (function named `stab` not `make_stab` in this script)

```python
def stab(voicing):
    if voicing in stab_cache:
        return stab_cache[voicing]
    dur = 0.15
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in voicing[1:]:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(4000 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 6)) / k ** 1.15
    x = signal.sosfilt(signal.butter(2, 900, "low", fs=SR, output="sos"), x)
    x = np.tanh(0.9 * x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    stab_cache[voicing] = x / (np.max(np.abs(x)) + 1e-12)
    return stab_cache[voicing]
```
