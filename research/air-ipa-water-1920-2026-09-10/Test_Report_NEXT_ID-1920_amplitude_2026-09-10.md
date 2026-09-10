# TEST REPORT — openQCM-NEXT/TP-PTFE-A/F-15A

**Instrument ID:** 1920  
**Date:** 2026-09-10  
**Dataset:** `2026-09-10_17-10-06_amplitude_multi_.csv`  
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
| Fundamental | -768.8 ± 0.4 | 390.2 ± 1.2 |
| 3rd Overtone | -1764.8 ± 1.0 | 723.8 ± 5.9 |
| 5th Overtone | -2516.2 ± 1.3 | 1199.5 ± 1.8 |
| 7th Overtone | -3161.1 ± 1.6 | 2022.8 ± 5.8 |
| 9th Overtone | -4104.4 ± 14.5 | 3796.8 ± 10.7 |

## Table 2 — Air → isopropanol

| Overtone | Δf (Hz) | ΔD (ppm) |
|----------|----------|-----------|
| Fundamental | -1002.2 ± 0.4 | 569.1 ± 0.8 |
| 3rd Overtone | -2371.8 ± 0.5 | 981.3 ± 0.7 |
| 5th Overtone | -3471.4 ± 1.9 | 1673.0 ± 1.7 |
| 7th Overtone | -4390.8 ± 2.5 | 3398.3 ± 11.6 |
| 9th Overtone | -5201.0 ± 1.6 | 6145.0 ± 6.2 |

## Repeatability

The protocol comprises 1 water phases (W1–W1) and 1 isopropanol phases (I1–I1). SD is the standard deviation across repeated injections; SD% is relative to the mean absolute value.

### Repeatability of frequency Δf (Hz) per phase

| Overtone | W1 | SD | SD% | I1 | SD | SD% |
|---|---|---|---|---|---|---|
| Fundamental | -768.8 | nan | nan% | -1002.2 | nan | nan% |
| 3rd Overtone | -1764.8 | nan | nan% | -2371.8 | nan | nan% |
| 5th Overtone | -2516.2 | nan | nan% | -3471.4 | nan | nan% |
| 7th Overtone | -3161.1 | nan | nan% | -4390.8 | nan | nan% |
| 9th Overtone | -4104.4 | nan | nan% | -5201.0 | nan | nan% |

### Repeatability of dissipation ΔD (ppm) per phase

| Overtone | W1 | SD | SD% | I1 | SD | SD% |
|---|---|---|---|---|---|---|
| Fundamental | 388.8 | nan | nan% | 569.3 | nan | nan% |
| 3rd Overtone | 729.1 | nan | nan% | 981.3 | nan | nan% |
| 5th Overtone | 1199.5 | nan | nan% | 1673.0 | nan | nan% |
| 7th Overtone | 2022.8 | nan | nan% | 3398.3 | nan | nan% |
| 9th Overtone | 3796.8 | nan | nan% | 6147.9 | nan | nan% |

## Figures

- `Test_Report_NEXT_ID-1920_amplitude_2026-09-10.fig.png`: time series
- `Test_Report_NEXT_ID-1920_amplitude_2026-09-10.fig2.png`: df, dD vs n
- `Test_Report_NEXT_ID-1920_amplitude_2026-09-10.fig3.png`: dD/|df| per phase

---
*openQCM device is released as an open-source test equipment, and it is intended solely for use in SCIENTIFIC, RESEARCH and DEVELOPMENT APPLICATION, DEMONSTRATION, OR EVALUATION PURPOSES and is not considered to be a finished end-product fit for general consumer use.*