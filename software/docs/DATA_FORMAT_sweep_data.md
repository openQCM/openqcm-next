# openQCM NEXT — raw sweep files (`sweep_data/`)

> Specification of the raw per-overtone sweep spectra produced during acquisition.
> Intended to be handed to a tool or an AI so the files can be parsed and
> manipulated correctly. Location on disk: `software/openQCM/sweep_data/`.

## What they are
`openQCM/sweep_data/<n>.txt` are the **raw per-overtone frequency-sweep spectra**
captured during a multiscan acquisition. Each file is the full amplitude + phase
response of one resonance vs. frequency — the un-fitted data from which the
software later extracts resonance frequency and dissipation (the values that end
up in `logged_data/*_multi_.csv`).

Written by `openQCM/processors/Multiscan.py` via
`FileStorage.TXT_sweeps_save` (which calls `numpy.savetxt`).

## Filenames
`<n>.txt` where **n = 2·(overtone_index) + 1**, overtone_index = 0…4:

| file    | overtone index | harmonic          |
|---------|----------------|-------------------|
| `1.txt` | 0              | fundamental (1st) |
| `3.txt` | 1              | 3rd               |
| `5.txt` | 2              | 5th               |
| `7.txt` | 3              | 7th               |
| `9.txt` | 4              | 9th               |

> ⚠️ **These files are OVERWRITTEN on every acquisition cycle.** The name is fixed
> (no timestamp), so `sweep_data/` always holds only the **most recent** sweep of
> each overtone — it is a live snapshot, not a growing history. To keep a sweep,
> copy it out before the next cycle.

## File format
- **Plain text, no header, no index column.**
- **Whitespace-delimited** (single space), one sweep point per line.
- Every value in **scientific notation, full double precision** (`%.18e`,
  e.g. `4.986788000000000000e+06`). Decimal separator `.`.
- **Exactly 3 columns:**

| # | Column                | Unit    | Description                                                                 |
|---|-----------------------|---------|-----------------------------------------------------------------------------|
| 1 | Frequency             | Hz      | sweep frequency; monotonically increasing, **1 Hz step**                    |
| 2 | Amplitude / Magnitude | dB      | AD8302 VMAG output, converted (see below); the resonance appears as a peak/dip |
| 3 | Phase                 | degrees | AD8302 VPHS output, converted (see below)                                   |

- **Number of rows: 18001** — the sweep spans an 18 kHz window around the detected
  resonance (`LEFT = 12000` Hz below … `RIGHT = 6000` Hz above, at 1 Hz step ⇒
  18000 + 1 points). The absolute frequency range differs per overtone
  (≈5 MHz for `1.txt`, ≈15 MHz for `3.txt`, ≈25 MHz for `5.txt`, etc.).

## How columns 2 and 3 were derived (units provenance)
The stored values are already physical (dB / degrees), converted from the 12-bit
ADC reading of the AD8302 (Vref = 3.3 V, 4096 counts, VCP = 0.9 V; AD8302 slopes
30 mV/dB and 10 mV/°):

```
ADCtoVolt      = 3.3 / 4096
amplitude_dB   = ( adc_mag   * ADCtoVolt / 2.0 - 0.9 ) / 0.03
phase_degrees  = ( adc_phase * ADCtoVolt / 1.5 - 0.9 ) / 0.01
```

A reader does **not** need these formulas (values in the file are already dB/°);
they only explain the units.

## The `g<n>.txt` variant — raw AD8302 voltages (`impedance-analysis` branch)
On the `impedance-analysis` branch `Multiscan.py` writes a **second family** of
files next to the ones above, `g1.txt … g9.txt`, in the same directory and on the
same acquisition cycle (same `FileStorage.TXT_sweeps_save` call site). They are the
input of the conductance / impedance analysis (**Tools → Conductance Data**,
`sweep_data/plot_conductance.py`).

Identical in every structural respect — plain text, no header, whitespace-delimited,
`%.18e`, 18001 rows, same 1 Hz frequency grid — with **one difference: columns 2 and
3 are the raw AD8302 output voltages, not dB and degrees.**

| # | Column    | Unit | Description                                                     |
|---|-----------|------|-----------------------------------------------------------------|
| 1 | Frequency | Hz   | identical to `<n>.txt` — same sweep, same points                |
| 2 | V_MAG     | V    | AD8302 magnitude output, **absolute** divider level             |
| 3 | V_PHS     | V    | AD8302 phase output                                             |

```
ADCtoVolt = 3.3 / 4096
V_MAG     = adc_mag   * ADCtoVolt / 2.0 - Constants.V_MAG_DECADE_OFFSET
V_PHS     = adc_phase * ADCtoVolt / 1.5          # /1.5 op-amp gain
```

The `/2` and `/1.5` are the op-amp gains ahead of the ADC. The subtracted term undoes
the **INPB R11/R19 attenuator**, and its value is not what it looks like:

```
K_ATT               = (47.0 + 4.99) / 4.99 = 10.418838      # = 20.3564 dB
V_MAG_DECADE_OFFSET = 20 * log10(K_ATT) * 0.030 = 0.610692 V
```

⚠️ **It is 0.61069 V, not 0.600.** The attenuator is 20.3564 dB, not one clean decade,
and until 2026-07-28 the code subtracted a hardcoded `0.6`. The 0.3564 dB residue
understated `M` by 4.02 %, which the inversion below amplifies by `(1 + R17/R_m)`
because `R_q = M·cos φ − R17` is a difference of close numbers at resonance: up to
**−22 % on `R_m`** at the fundamental in air. A synthetic THRU (`Z_q = 0.001 Ω`) reads
`M` = 50.199 Ω with 0.600 against 52.301 Ω with the correct value, true 52.30 Ω.

Consequence for anyone reading archived data: **`g<n>.txt` written before 2026-07-28
carries a `V_MAG` that is 10.7 mV too high**, and gives `R_m` up to 22 % low.

With column 2 at the correct **absolute** level, the measuring divider inverts as:

```
M = |Z_q + R17| = R17 * 10**((0.9 - V_MAG) / 0.6)        # R17 = 52.3 ohm
phi             = (1.8 - V_PHS) / 0.01                   # degrees, magnitude only
```

⚠️ The `0.6` here is a different number that happens to look the same: it is the
AD8302's own decade (20 × 30 mV/dB), **not** the attenuator, which was already removed
when the file was written. Do not "unify" the two.

⚠️ Three traps, all found the hard way:
- **Do not baseline-correct V_MAG before this inversion.** Subtracting the
  calibration polynomial turns column 2 into a *relative* level and scales `M` by
  `10**(V_baseline/0.6)`, which drives `M(resonance)` below `R17` and yields negative
  resistance everywhere. The relative level is correct only for the *approximate*
  `G = cos(phi)/|Z|`.
- **Column 3 is |phase| minus an offset.** The AD8302 has no sign output, so the true
  phase is folded at its zero crossing — and the channel also carries a global
  per-overtone offset, which is why the reading goes *negative* around resonance.
  Where a fold exists it measures that offset exactly: `delta = -min(reading)`. Where
  there is none (damped load, phase never crosses zero) there is nothing to unfold and
  nothing to offset.
- **G is even in the SIGN of the phase but not in its OFFSET.** Skipping the offset
  "because G only needs cos φ" is wrong and was tried.

The full chain, step by step with a worked numerical example, is in
[`../../docs/impedance-analysis/ALGORITHM.md`](../../docs/impedance-analysis/ALGORITHM.md).

Real first line of a `g1.txt` written with the correct constant
(`docs/impedance-analysis/reference-sweep/g1.txt`):
```
4.986001000000000000e+06 -1.518578228517387663e-01 9.625483398437498783e-01
```
→ frequency = 4 986 001 Hz, V_MAG = −0.1519 V, V_PHS = 0.9625 V.

## Real example (first line of `1.txt`)
```
4.986788000000000000e+06 -1.378842773437500391e+01 1.203842773437498970e+01
```
→ frequency = 4 986 788 Hz, amplitude = −13.79 dB, phase = +12.04°.

## Recommended handling
- Load with any whitespace-delimited numeric reader
  (`numpy.loadtxt`, `pandas.read_csv(sep=r'\s+', header=None)`); assign columns
  `["freq_Hz", "amplitude_dB", "phase_deg"]`.
- Treat each file as **one spectrum of one overtone**; do not concatenate across
  files (different frequency ranges).
- Do not assume the files persist — snapshot them if you need a specific cycle.
- To locate the resonance: the peak in column 2 (amplitude). Dissipation-type
  analysis uses the peak width/phase; the production pipeline fits these with
  Savitzky–Golay smoothing + spline (`sweep_data/plot_sweep_spline.py` is a
  reference viewer).

## Minimal parsing snippet (Python)
```python
import numpy as np
freq, amp_db, phase_deg = np.loadtxt("openQCM/sweep_data/1.txt", unpack=True)
peak_idx = np.argmax(amp_db)          # resonance ≈ frequency of the amplitude peak
f_res = freq[peak_idx]
```

---
_Note: on the TEC-less TEST board the content of these files is identical (the
DDS/ADC sweep engine is unchanged); only the temperature field in the CSV logs is
simulated — the `sweep_data` spectra are unaffected._
