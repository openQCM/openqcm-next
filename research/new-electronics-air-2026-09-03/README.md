# Air sweeps — new electronics, 2026-09-03

Five raw sweeps in the `g<n>.txt` format (frequency [Hz], `V_MAG` [V], `V_PHS` [V]; see
`software/docs/DATA_FORMAT_sweep_data.md`), one per overtone, 18001 samples each, taken **in air**
on the board with the **new filters and the 150 MHz clock**.

**Why they are tracked.** Every number in the `CHANGELOG.md` entry *"the phase fold is decided by
the locus, not by a threshold"* and in `docs/impedance-analysis/ALGORITHM.md` §4.3 was measured on
these files: the `min(r)` values that straddle the 5° threshold, the peak depths of 0.918–1.025 that replaced
them, and the circle residuals reported alongside. Without them those numbers are unverifiable
prose.

⚠️ That is not hypothetical. The air/isopropanol datasets behind the July 2026 validation tables
were left in `software/openQCM/sweep_data/`, which is gitignored and overwritten on every
acquisition, and they are **gone** — so the ΔD figures derived from those tables cannot be checked
against the data any more. 6.8 MB is the price of not repeating that.

| file | overtone | f_r [MHz] | Γ [Hz] | `min(r)` [deg] |
|---|---|---|---|---|
| `g1.txt` | fundamental | 4.998967 | 72.5 | −2.20 |
| `g3.txt` | 3rd | 14.974607 | 28.6 | +2.45 |
| `g5.txt` | 5th | 24.951060 | 54.9 | +3.83 |
| `g7.txt` | 7th | 34.926342 | 75.9 | **+6.64** |
| `g9.txt` | 9th | 44.903123 | 130.3 | +4.80 |

The 7th is the overtone the old threshold misclassified; the others sat close enough to 5.0 to flip
between sweeps.

**What is still missing.** A **damped-load** dump from this board — isopropanol, or water on the
high overtones. Every sweep here, and the frozen water reference from the old board, comes out
"fold", so nothing available exercises the branch where the answer must be "no fold". Add it beside
this folder when it is measured, and update ALGORITHM.md §4.3 with what it shows.

Acquired with `OPENQCM_SWEEP_DUMP=1`, copied out of `sweep_data/` before the next acquisition
overwrote them.
