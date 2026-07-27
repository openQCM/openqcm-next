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
V_MAG     = adc_mag   * ADCtoVolt / 2.0 - 0.6   # /2 op-amp gain; -0.6 V divider offset
V_PHS     = adc_phase * ADCtoVolt / 1.5         # /1.5 op-amp gain
```

The `-0.6 V` term compensates the INPB ×10 input attenuation (one decade at
600 mV/decade), so column 2 is at the correct **absolute** level for inverting the
measuring divider:

```
M = |Z_q + R17| = R17 * 10**((0.9 - V_MAG) / 0.6)        # R17 = 52.3 ohm
phi                = (1.8 - V_PHS) / 0.01                # degrees, magnitude only
```

⚠️ Two traps, both found the hard way:
- **Do not baseline-correct V_MAG before this inversion.** Subtracting the
  calibration polynomial turns column 2 into a *relative* level and scales `M` by
  `10**(V_baseline/0.6)`, which drives `M(resonance)` below `R17` and yields negative
  resistance everywhere. The relative level is correct only for the *approximate*
  `G = cos(phi)/|Z|`.
- **Column 3 is |phase|.** The AD8302 has no sign output: the true phase is folded at
  its zero crossing. Recovering the signed phase needs an unfold, and the unfold is
  only valid when the phase actually crosses zero (air / low damping) — see
  `_phase_signed()` in `plot_conductance.py` and
  `docs/impedance-analysis/conductance-calculation.md`.

Real first line of `g1.txt`:
```
4.986928000000000000e+06 -1.354903564453125431e-01 9.438354492187498446e-01
```
→ frequency = 4 986 928 Hz, V_MAG = −0.1355 V, V_PHS = 0.9438 V.

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
