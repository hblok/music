# Drums & Percussion

Canonical drum/percussion functions extracted from the trance generators.
Copy-don't-import (standalone scripts). Psy kit = maschinenherz / silver_wire.

## `make_kick` — 909 kick (canonical — identical family across all 4/4 scripts)

**Source:** `lost_v6.py:make_kick`  
**Character:** falling sine 48+102·e^(−50t) + bandpassed click; punchy, NOT sub-heavy

```python
def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 110.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (37 + 18 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.55 * sub + 0.45 * click * (1 - np.exp(-td / 0.0008))
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_hat` — closed / open hat

**Source:** `lost_v6.py:make_hat`  
**Character:** `make_hat()` = 7 kHz HP noise 45 ms; `make_hat(open_=True)` = 120 ms offbeat 'tss'

```python
def make_hat(open_=False):
    n = int((0.13 if open_ else 0.04) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7500, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * (26 if open_ else 120))
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_clap` — clap (Frankfurt, canonical)

**Source:** `lost_v6.py:make_clap`  
**Character:** 900–4500 BP, 4 micro-delayed bursts; beats 2 & 4

```python
def make_clap():
    n = int(0.32 * SR)
    td = np.arange(n) / SR
    sos = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 130.0), (1, 130.0), (2, 130.0), (3, 24.0)]:
        i0 = int(i * 0.011 * SR)
        x[i0:] += signal.sosfilt(sos, rng.standard_normal(n - i0)) * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_ride` — ride

**Source:** `lost_v6.py:make_ride`  
**Character:** two BP layers + 5.4 kHz ping; climax sections only — era discipline

```python
def make_ride():
    n = int(0.4 * SR)
    td = np.arange(n) / SR
    nz = rng.standard_normal(n)
    a = signal.butter(2, [4000, 7000], "bandpass", fs=SR, output="sos")
    b = signal.butter(2, [8000, 12000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(a, nz) * np.exp(-td * 9) + 0.7 * signal.sosfilt(b, nz) * np.exp(-td * 6)
    x += 0.18 * np.sin(2 * np.pi * 5400 * td) * np.exp(-td * 8)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_crash` — crash

**Source:** `lost_v6.py:make_crash`  
**Character:** 5 kHz HP, 2 s; marks arrivals

```python
def make_crash():
    n = int(2.2 * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 5000, "high", fs=SR, output="sos"),
                       rng.standard_normal(n)) * np.exp(-td * 2.0)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_snare` — snare (for rolls)

**Source:** `adrift.py:make_snare`  
**Character:** exists for the ROLL; also in farlight_v2, penumbra, lost_v6

```python
def make_snare():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 185 * td) + np.sin(2 * np.pi * 330 * td)) * np.exp(-td * 26)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 30)
    x = 0.6 * tone + noise
    x *= 1 - np.exp(-td / 0.0008)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_shaker` — shaker

**Source:** `nachtkind_v3.py:make_shaker`  
**Character:** quiet motion layer

```python
def make_shaker():
    n = int(0.06 * SR)
    td = np.arange(n) / SR
    sos_s = signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 70)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_tom` — 909 tom (fills only)

**Source:** `eisgang_v3.py:make_tom`  
**Character:** falling sine + skin burst; **fills only**, ≤3 per track

```python
def make_tom(f0):
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * 1.6 * np.exp(-td * 9.0) + f0
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 11.0)
    skin = signal.sosfilt(signal.butter(2, [400, 2500], "bandpass", fs=SR,
                                        output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 60)
    skin /= np.max(np.abs(skin)) + 1e-12
    x = body + 0.25 * skin
    x *= 1 - np.exp(-td / 0.001)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_tick` — tick pair — owned by eisgang

**Source:** `eisgang_v3.py:make_tick`  
**Character:** rim/woodblock clicks (2.5/1.8 kHz, +3.4 kHz descant), hard-panned; the no-carpet top end

```python
def make_tick(fc):
    # the tick pair: a rim/woodblock click — bandpassed snap + a tiny thump
    n = int(0.035 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [fc * 0.7, fc * 1.3], "bandpass", fs=SR,
                          output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 300)
    thump = 0.4 * np.sin(2 * np.pi * fc / 3 * td) * np.exp(-td * 180)
    x = click / (np.max(np.abs(click)) + 1e-12) + thump
    x *= 1 - np.exp(-td / 0.0004)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `heart` — heartbeat

**Source:** `lost_v6.py:heart`  
**Character:** 32→68 Hz double thump; breaks only (the audible-heartbeat requirement)

```python
def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)
    thud = signal.sosfilt(signal.butter(2, 220, "low", fs=SR, output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 28)
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud / (np.max(np.abs(thud)) + 1e-12)
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_slam` — gated 80s slam — owned by tech_noir

**Source:** `tech_noir_v3.py:make_slam`  
**Character:** gate baked into the sample (cut dead at 140 ms); punctuation, never a groove

```python
def make_slam():
    n = int(0.55 * SR)
    td = np.arange(n) / SR
    f_curve = 52.0 + 98.0 * np.exp(-td * 26.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 9.0)
    sos_n = signal.butter(2, [180, 2400], "bandpass", fs=SR, output="sos")
    burst = signal.sosfilt(sos_n, rng.standard_normal(n))
    burst /= np.max(np.abs(burst)) + 1e-12
    x = body + 0.55 * burst * np.exp(-td * 16.0) + 0.30 * burst * np.exp(-td * 3.0)
    gate = np.clip((0.140 - td) / 0.025, 0, 1)            # hard 80s gate
    x *= (1 - np.exp(-td / 0.0015)) * gate
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_anvil` — anvil — owned by tech_noir

**Source:** `tech_noir_v3.py:make_anvil`  
**Character:** 6 inharmonic partials on 410 Hz + strike, big dark plate

```python
def make_anvil():
    n = int(4.0 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    f0 = 410.0
    for i, (ratio, g) in enumerate(zip(
            [1.0, 2.71, 4.07, 5.43, 7.39, 9.21],
            [1.0, 0.78, 0.55, 0.40, 0.26, 0.16])):
        dec = 1.1 + 0.55 * i
        for det in (0.9991, 1.0009):
            x += g * np.sin(2 * np.pi * f0 * ratio * det * td +
                            rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_s = signal.butter(2, [2500, 9000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 280)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.7 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_tap` — tap — owned by tech_noir

**Source:** `tech_noir_v3.py:make_tap`  
**Character:** metallic 1280 Hz inharmonic tick

```python
def make_tap():
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for ratio, g in zip([1.0, 2.89, 5.12], [1.0, 0.5, 0.25]):
        x += g * np.sin(2 * np.pi * 1280.0 * ratio * td +
                        rng.uniform(0, 2 * np.pi)) * np.exp(-td * 14.0)
    sos_s = signal.butter(2, [4000, 10000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 220)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.5 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_kick` — psy kick — maschinenherz / silver_wire

**Source:** `maschinenherz.py:make_kick`  
**Character:** 150→45 Hz dive; harder/faster than the 909 kick; the psy house floor

```python
def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_clap` — psy clap — maschinenherz / silver_wire

**Source:** `maschinenherz.py:make_clap`  
**Character:** beats 2&4; tighter and brighter than the Frankfurt clap

```python
def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)
```

## `make_zap` — psy zap — maschinenherz / silver_wire

**Source:** `maschinenherz.py:make_zap`  
**Character:** 8-bar phrase punctuation inside drops

```python
def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)
```
