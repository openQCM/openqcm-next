# TEST REPORT — openQCM-NEXT/TP-PTFE-A/F-15A

**Instrument ID:** 1920  
**Date:** 2026-09-10  
**Dataset:** `2026-09-10_17-10-06_impedance_multi_.csv`  
**Working temperature:** 24.9987 °C  
**Report level:** pro

## Test description

openQCM Next equipment is tested by monitoring frequency and dissipation variations using a 5 MHz AT-cut Au-coated quartz crystal resonator across multiple overtones. The fluidic module is temperature controlled (T = 24.9987 °C). The test is conducted by sequentially injecting pure water and isopropanol into the fluidic module; frequency and dissipation of the fundamental and overtones (n = 1, 3, 5, 7, 9) are monitored under static fluid conditions. Values are air-referenced: mean ± std over the quietest 50-point window of each phase; uncertainty combines baseline and phase std in quadrature.

## Protocol phases (full timeline)

| # | Phase | Start (s) | End (s) | Duration (s) |
|---|-------|-----------|---------|--------------|
| 1 | air | 20 | 744 | 723 |
| 2 | isopropanol | 752 | 1193 | 441 |
| 3 | water | 1202 | 1406 | 204 |

## Table 1 — Air → pure water

| Overtone | Δf (Hz) | ΔD (ppm) |
|----------|----------|-----------|
| Fundamental | -764.2 ± 0.4 | 317.5 ± 0.1 |
| 3rd Overtone | -1521.3 ± 0.8 | 167.3 ± 0.0 |
| 5th Overtone | -1966.5 ± 0.6 | 116.2 ± 0.0 |
| 7th Overtone | -2237.0 ± 1.0 | 94.9 ± 0.0 |
| 9th Overtone | -2558.5 ± 2.0 | 86.1 ± 0.2 |

## Table 2 — Air → isopropanol

| Overtone | Δf (Hz) | ΔD (ppm) |
|----------|----------|-----------|
| Fundamental | -987.0 ± 0.0 | 461.6 ± 0.0 |
| 3rd Overtone | -1907.1 ± 0.6 | 206.3 ± 0.0 |
| 5th Overtone | -2608.8 ± 1.0 | 148.6 ± 0.0 |
| 7th Overtone | -2958.2 ± 5.1 | 124.7 ± 0.0 |
| 9th Overtone | -3411.3 ± 6.3 | 112.1 ± 0.1 |

## Repeatability

The protocol comprises 1 water phases (W1–W1) and 1 isopropanol phases (I1–I1). SD is the standard deviation across repeated injections; SD% is relative to the mean absolute value.

### Repeatability of frequency Δf (Hz) per phase

| Overtone | W1 | SD | SD% | I1 | SD | SD% |
|---|---|---|---|---|---|---|
| Fundamental | -764.2 | nan | nan% | -987.0 | nan | nan% |
| 3rd Overtone | -1521.3 | nan | nan% | -1907.1 | nan | nan% |
| 5th Overtone | -1966.5 | nan | nan% | -2608.8 | nan | nan% |
| 7th Overtone | -2237.0 | nan | nan% | -2964.8 | nan | nan% |
| 9th Overtone | -2558.5 | nan | nan% | -3411.3 | nan | nan% |

### Repeatability of dissipation ΔD (ppm) per phase

| Overtone | W1 | SD | SD% | I1 | SD | SD% |
|---|---|---|---|---|---|---|
| Fundamental | 317.5 | nan | nan% | 461.6 | nan | nan% |
| 3rd Overtone | 167.3 | nan | nan% | 206.3 | nan | nan% |
| 5th Overtone | 116.2 | nan | nan% | 148.6 | nan | nan% |
| 7th Overtone | 94.9 | nan | nan% | 124.7 | nan | nan% |
| 9th Overtone | 86.1 | nan | nan% | 111.9 | nan | nan% |

## Figures

- `Test_Report_NEXT_ID-1920_impedance_2026-09-10.fig.png`: time series
- `Test_Report_NEXT_ID-1920_impedance_2026-09-10.fig2.png`: df, dD vs n
- `Test_Report_NEXT_ID-1920_impedance_2026-09-10.fig3.png`: dD/|df| per phase

---
*openQCM device is released as an open-source test equipment, and it is intended solely for use in SCIENTIFIC, RESEARCH and DEVELOPMENT APPLICATION, DEMONSTRATION, OR EVALUATION PURPOSES and is not considered to be a finished end-product fit for general consumer use.*