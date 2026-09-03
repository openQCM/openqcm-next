# Air sweeps — 125 MHz board, 2026-09-03

Five raw sweeps in the `g<n>.txt` format (frequency [Hz], `V_MAG` [V], `V_PHS` [V]; see
`software/docs/DATA_FORMAT_sweep_data.md`), one per overtone, 18001 samples each, taken **in air**
with the DDS system clock at **125 MHz**.

⚠️ **125 MHz is the specified maximum at 3.3 V.** The datasheet's *Clock Input Characteristics*
gives 100 MHz at 2.7 V, **125 MHz at 3.3 V** and 180 MHz at 5.0 V, and the 6× multiplier does not
get around it — at 3.3 V the maximum REFCLK is 20.83 MHz, which is the same 125 MHz of system clock.
Anything above that on a 3.3 V board is outside the guaranteed range, whatever it appears to do on a
particular part at a particular temperature. **These sweeps are inside it**, which is why they are
the reference and not merely a measurement.

**Why they are tracked.** They are the in-specification evidence behind the fold criterion in
`docs/impedance-analysis/ALGORITHM.md` §4.3 — the phase baselines, the depths and the circle
residuals quoted there were measured on these files.

| file | overtone | f_r [MHz] | Γ [Hz] | baseline [deg] | δ [deg] | depth | circle rms |
|---|---|---|---|---|---|---|---|
| `g1.txt` | fundamental | 4.998907 | 67.2 | 86.2 | +4.23 | 1.049 | 2.79 % |
| `g3.txt` | 3rd | 14.974427 | 40.5 | 81.7 | +3.75 | 1.046 | 3.44 % |
| `g5.txt` | 5th | 24.950740 | 71.4 | 69.6 | +6.67 | 1.096 | 1.47 % |
| `g7.txt` | 7th | 34.925931 | 99.7 | 63.7 | +6.53 | 1.102 | 1.78 % |
| `g9.txt` | 9th | 44.902583 | 147.0 | 57.8 | −0.90 | 0.984 | 5.97 % |

⚠️ **The baseline is not a constant.** It falls from 86.2° at the fundamental to 57.8° at the 9th on
this one board, and δ ranges from −0.90° to +6.67°. That is the measurement that motivates a fold
criterion normalised by the sweep's own excursion rather than one expressed in absolute degrees —
an absolute threshold is being compared against a reference that moves by 28° across the overtones.

**Reproducibility.** Two consecutive runs on this board agree to ~0.3° in δ and ~0.5 points in
depth, with identical decisions on all five overtones.

**What is still missing.** A **damped-load** dump — isopropanol, or water on the high overtones.
Every sweep here comes out "fold", so nothing available exercises the branch where the answer must
be "no fold". Add it beside this folder when it is measured, and update ALGORITHM.md §4.3 with what
it shows.

Acquired with `OPENQCM_SWEEP_DUMP=1`, copied out of `sweep_data/` before the next acquisition
overwrote them — that directory is gitignored and rewritten on every sweep, and the datasets behind
the July 2026 validation tables were lost exactly that way.
