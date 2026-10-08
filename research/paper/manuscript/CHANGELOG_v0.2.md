# Change log — manuscript v0.2 (2026-10-08) against v0.1 (2026-10-07)

Revision carried out on the `impedance-analysis` branch following the revision prompt of 2026-10-08 (sections 1–5 of the prompt prevail over the v0.1 structure). The previous version is archived unchanged in `manuscript/archive/manuscript_v0.1_2026-10-07.md` and `archive/main_v0.1_2026-10-07.tex`.

## Decisions taken with the author (2026-10-08)

- No dedicated air → water dataset (DS-1) exists in the repository; Experiment 1 uses the air → water step of DS-2 (board 1920, 2026-09-11) and of DS-3 (second instrument, 2024-05-29). A dedicated acquisition is listed among the remaining experiments.
- No tabulated ρη is used for the glucose solutions: their √(ρη) relative to water is estimated from the data (both channels, overtones 3–9). An absolute KG-3 for glucose needs literature values at the experimental temperature and is listed among the remaining experiments.
- Liquid properties are taken at 25 °C (TEC set-point) with the liquid temperature unmeasured; the ±2 K sensitivity (±2–3 %) is stated in the Theory section and in the Discussion.

## Structure

- New Section 2 (Theory): derivation SLA → KG with the sign conventions, the normalisation to the fundamental and the overtone frequency inside the load impedance, the three tests KG-1, KG-2, KG-3, and the explicit note on the earlier document's symbols (η_q) and water constants. An independent derivation check with sources is in `notes/theory_sla_to_kg_check.md` (SI S2).
- Results restructured as three experiments with identical analyses: Exp. 1 air → water (A vs P, both datasets, templates T4 and T5, KG-1/2/3, bias law, reconstruction vs rotation, reproducibility); Exp. 2 air → water → isopropanol (P only; KG-3 against the tabulated √(ρη) of two liquids); Exp. 3 air → water → glucose (P only; relative KG-3, steps in √(ρη), resolution from noise/slope); Synthesis with the instrumental-φ hypothesis tested in one figure for every medium and dataset.
- Main text reduced to the results that carry the argument (8 figures, 2 tables); all per-overtone tables, fit diagnostics, residuals, fallback statistics, raw sweeps, fold/offset analysis, raw-magnitude baseline, forward model and secondary figures moved to a separate Supporting Information (`manuscript/supporting_information.md`, 11 sections, 11 tables, 12 figures).
- Literature comparison reduced to a compact Table 1 in the main text; the full table stays in `literature/comparison_table.md` (SI S1).
- Discussion reorganised under the headings requested (physical response vs instrumental rotation; detector limits; model assumptions; highly damped loads; calibration dependence; extension; limitations).

## Definitions changed

- KG-1 is reported as r_n = ΔΓ_n/(−Δf_n) (v0.1 reported its inverse, ρ_N = |Δf|/ΔΓ). All numbers were recomputed; e.g. v0.1's 1.17–1.34 (A, DS-2) becomes 0.76–0.85.
- KG-2 is now also reported as the log–log slope of −Δf_n/n and ΔΓ_n/n against n (expected −0.5), on n = 3–9 and 1–9, in addition to the √n slopes through the origin and the coefficient of variation of the √n-normalised shifts used in v0.1.
- The error definitions (ε_f, ε_Γ, r_n, b) are stated once in Methods and applied identically to every experiment.
- The electrical impedance of the crystal is written Z_el (R_el, X_el) to avoid the clash with the acoustic impedance Z_q of the SLA (v0.1 used Z_q for both).
- The isopropanol KG coefficient is 902.1 Hz·√n (v0.1: 901.5, computed with Z_q rounded to 8.84·10⁶); the water value 673.6 Hz·√n is unchanged. Liquid constants now carry sources (NIST WebBook for water; Kerscher et al. 2024 for the temperature sensitivity of isopropanol, whose measured viscosity is 1.7 % above the handbook value used).

## Numbers

- Every number was regenerated from the raw sweeps (`run_estimators.py`, `run_glucose.py` sweep stage, new `run_v2.py`); the regenerated per-sweep tables reproduce the committed v0.1 tables to ≤0.07 Hz on f_res, ≤0.5 Hz on Γ and ≤0.05° on φ (the differences are solver/platform rounding). The forward model and the closed-form checks were re-run (unchanged).
- New quantities not in v0.1: log–log KG-2 slopes; the per-overtone '8 %' claim table; the DS-2 vs DS-3 reproducibility table for the air → water step; the φ stability tables (across replicas, liquids, media, boards, days) and the monotonicity test; the relative √(ρη) of the glucose solutions from both channels, the steps between concentrations in √(ρη) and in units of the replica scatter, and the resolution in √(ρη) from noise/slope; the bias law on 120 sweeps per dataset, medium and overtone.
- The '8 %' claim of the repository is now stated per overtone and dataset: supported for the frequency on board 1920 (|ε_f| ≤ 8.2 % on every overtone 3–9 in water and isopropanol), not on the second instrument (10–13 % on n = 3, 7, 9), and not an improvement for the bandwidth (already within 7 % before the fit).
- The instrumental-φ hypothesis is now stated with its failures: 3–8° air–liquid difference at the fundamental (opposite sign in liquid on the second instrument), 4–5° on n = 5, non-monotonic in n in liquid on both boards and in air on the second, up to 5° between boards.
- Dropped from the main text: the production datalog of the 2024 session (its full file is not in the repository; only a 15:00–16:01 extract without the air phase is, so v0.1's +17…+42 % for that datalog could not be regenerated and is not cited); the two-channel BVD forward-model board phase and the resistive standards are kept in the SI only.

## Figures

- All main-text figures regenerated by `analysis/make_figures_v2.py` into `figures_v2/` (provenance in `analysis/results/v2/figure_provenance_v2.md`): Fig. 1 circuit (unchanged), Fig. 2 estimators on G (new, two panels), Fig. 3 template T4 for both datasets (new), Fig. 4 Exp. 1 T5 + KG-1 (new), Fig. 5 bias law on 120 sweeps (revised), Fig. 6 Exp. 2 T5/KG-1/KG-3 (new), Fig. 7 Exp. 3 T5/KG-1/relative KG-3/resolution (new), Fig. 8 φ for every medium and dataset (new). The v0.1 figures 2–4, 9, 10 are regenerated into the SI; v0.1 figures 6–8 and 11–15 are superseded.

## Literature (2026-10-08 verification pass)

- Full texts of the closest prior works were read (Sakti 2019, Horst 2022, Muñoz 2023/2026, Burda 2022a,b, Leppin 2020, Johannsmann 2021, the openQCM Q-1 v3.0 host source, rheoQCM, the AWSensors patent). Corrections that reach the main text: Horst et al. replaced the AD8302 by an AD8310 amplitude-only detector (v0.1 listed it as a gain/phase reuse); Sakti 2019 is air-only, |Z| and phase displayed separately, no admittance; Muñoz 2023/2026 are VNA-based. Table 1 rebuilt on these facts; the Introduction now cites the bioimpedance AD8302 inversions, the hardware resolutions of the AD8302 sign ambiguity, rheoQCM and the AWSensors patent as independent uses of the phase-shifted Lorentzian, and Gao 2008 for the microwave rotation angle. 59 BibTeX entries added (existing keys unchanged); novelty statement rewritten (`literature/novelty_assessment.md` (iii)).

## arXiv source

- `arxiv/main.tex` and `arxiv/si.tex` are generated from the Markdown by the new `analysis/md2tex.py` (pandoc is not available in the authoring environment); figures copied to `arxiv/figures/`. Compiled on 2026-10-08 with TeX Live 2026 (TinyTeX, user-level installation): `arxiv/main.pdf` (19 pages) and `arxiv/si.pdf` (34 pages, wide tables in landscape); no LaTeX errors, no undefined citations; logs in `arxiv/build/`.
- The number check of the whole text (`notes/number_check_v0.2.md`: 206 statements confirmed, 34 discrepancies, all applied) and the literature verification pass (`literature/`) were run as separate passes after the draft; both are incorporated.

## Open items for the author

- The full datalog of the 2024-05-29 session (`2024-May-29_14-21-38_multi_.csv`, 541 rows) is gitignored and no longer present in the worktree; only the extract is. If the archive supplied on 2026-10-07 is still available, restoring the file allows the SI to show the production estimator of DS-3 as well.
- Author list, affiliations, funding and conflict-of-interest statements.
- `literature/references.bib`: entries graded unverified in their `note` fields (see the changelog section of `literature/literature_review.md`).
- Literature items still graded (I)/(U) in `literature/literature_review.md` (see its changelog section).
