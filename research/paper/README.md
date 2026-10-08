# `research/paper/` — manuscript project: QCM frequency and dissipation from DDS excitation, gain–phase detection and complex-admittance reconstruction

Work of 2026-10-06/07 on the `impedance-analysis` branch (analysis of commit `37fce4b`, second dataset added 2026-10-07). Nothing pre-existing under `research/` or `software/` was modified; the one addition is the new folder `research/glucose-2024-05-29/` (raw sweeps of a second instrument, 2024-05-29, with its datalog and provenance README), of which `research/paper/data/glucose-2024-05-29/` is an identical copy kept with the paper (the loader falls back to it). Every number here is regenerated from the raw data in `research/` by the scripts in `analysis/`.

| what | where |
|---|---|
| **Manuscript** (full scientific draft: methods, first campaign §6, second campaign §7, discussion, conclusion; Markdown with pandoc citations) | `manuscript/manuscript.md` |
| **arXiv-ready LaTeX source** (generated from the Markdown; not compiled here — no TeX in the environment) | `arxiv/main.tex`, `arxiv/references.bib`, `arxiv/figures/` |
| **Publication figures** (15, PNG 300 dpi + PDF) and their provenance | `figures/`, `analysis/results/figure_provenance.md` |
| **Numerical results and uncertainties** (per sweep, per phase, shifts, slopes, gate statistics; as-is and firmware-corrected) | `analysis/results/tables_asis.md`, `tables_fwfix.md`, `*.csv`, `*.json` |
| **Datalog analysis** (impedance chain vs production magnitude chain, two runs) | `analysis/results/datalogs.md` |
| **Bias theory, rotation angle, board delay** | `analysis/results/bias_theory.md` |
| **Forward model (falsification tests)** | `analysis/results/forward_model.md` |
| **Second instrument, 2024-05-29 (water, glucose 5/7.5/10 % w/v): estimators, shifts, concentration slopes, 5 %-plateau residual and drift checks, clipped-window check, φ decomposition** | `analysis/results/glucose_tables_asis.md`, `glucose_tables_fwfix.md`, `glucose_*.csv/json` |
| **Raw data of the second instrument (copy)** | `data/glucose-2024-05-29/` |
| **Complete derivation of the measurement equations** | `notes/derivations.md` |
| **Running list**: verified facts, doc/code discrepancies, hypotheses, open questions, assumptions, limitations, reviewer objections, remaining experiments | `notes/running_list.md` |
| **Literature review, comparison table, novelty assessment, BibTeX** | `literature/` |
| **Journal shortlist and submission notes** | `notes/journals_and_submission.md` |
| **Remaining experiments** | `notes/remaining_experiments.md` |

## Reproducing everything

```bash
pip install numpy scipy matplotlib pandas        # numpy 2.x works for research/paper/analysis (the instrument code itself needs numpy ≤ 1.23)
cd research/paper/analysis
python run_estimators.py      # 45 sweeps × 7 estimators, as-is and firmware-corrected  → results/sweeps_*.csv
python run_shifts.py          # phases, shifts, Kanazawa–Gordon, √n slopes, gate stats  → results/tables_*.md, summary_*.json
python run_datalogs.py        # the two datalogs, impedance vs magnitude chain          → results/datalogs.md
python run_bias_theory.py     # closed forms vs data, φ analysis, OSL delay             → results/bias_theory.md
python run_forward_model.py   # synthetic truth through the front end                   → results/forward_model.md
python run_glucose.py         # 2024-05-29 set, 75 sweeps × 7 estimators, as-is and fwfix  → results/glucose_*
python make_figures.py        # figures → ../figures, provenance → results/figure_provenance.md
```

`qcmchain.py` is an independent re-implementation of the chain written from the equations (it shares only the smoothing definition with the instrument); it reproduces `software/tests/data/psl_expected_2026-09-11.json` to all printed digits.

## Main findings in one paragraph

On overtones 3–9 in water and isopropanol the air-to-liquid frequency shifts deviate from Kanazawa–Gordon by +52…+92 % with the magnitude channel alone, +20…+30 % with the maximum of the reconstructed conductance and −1.4…+8.2 % with the phase-shifted Lorentzian; the bandwidth shifts are within ±7.4 % with the half-height width and −3.9…+9.3 % with the fit, so the fit's gain is on frequency. The 20–30 % excess is the closed-form bias Γ·tan(φ/2) of the conductance maximum for a resonance rotated by φ = −8…−27°, an instrument constant equal to the board phase. A forward model shows the rotation correction is exact only when R_m ≫ R17 (liquid). The fundamental is off by +29…+37 % in bandwidth with every estimator. A second campaign on a different instrument and crystal (water and glucose 5–10 % w/v, §7) repeats the ranking on four liquids (Newtonian ratio 1.20–1.41 → 1.01–1.16; water Δf +20…+36 % → +6…+13 %; √n collapse 6–7 % → 2.4–2.9 %), resolves 2.5 % w/v glucose steps at ≥ 13 σ (0.1–0.2 % w/v noise-equivalent; an unexplained 10–18 Hz offset of the 5 % plateau limits the accuracy to 0.5–1.7 % w/v), finds φ within 1–3° on four overtones but not monotonic in frequency, and a fundamental that follows the theory. Documented discrepancies with the repository: ALGORITHM.md §11 is computed on raw samples (not the smoothed chain); the "within 8 %" claim holds for frequency, not for bandwidth (already within ±7 % before the fit); the instrument's smoothing widens Γ by +10 % at the air fundamental.
