# Figure provenance — manuscript v2

| figure | source dataset | script | parameters |
|---|---|---|---|
| fig02_estimators_on_G | sweep_dumps_2026-09-11.npz (air_1/g5, wat_1/g5) | research/paper/analysis/make_figures_v2.py | chain SG 51/3 + spline; fits on ±3 Γ_hh around max G; dotted = max of G and its half-height crossings; solid = f_res of P |
| fig03_T4_time_traces | DS-2: 2026-09-11_12-14-42_multi.csv (A live) + sweep_dumps_2026-09-11.npz (P); DS-3: sweep_raw_2024-05-29.npz | research/paper/analysis/make_figures_v2.py | shifts relative to the air plateau of the same estimator (DS-2 datalog: last 10 min of air; sweeps: mean of the three air dumps); ΔΓ from the datalog = D·1e-6·f/2 |
| fig04_exp1_T5_KG1 | results/v2/asis/shifts.csv (DS-2 water, DS-3 water; A and P) | research/paper/analysis/make_figures_v2.py | T5 (rows 1–2) and KG-1 ratio (row 3); error bars: quadrature sd of the two plateaus (÷n), ratio sd propagated |
| fig05_argmax_bias | results/sweeps_asis.csv, results/glucose_sweeps_asis.csv (psl rows) | research/paper/analysis/make_figures_v2.py | bias_meas = f_Gmax − f_res(P); bias_pred = Γ_P tan(φ_P/2) |
| fig06_exp2_water_ipa | results/v2/asis/shifts.csv (DS-2, P) | research/paper/analysis/make_figures_v2.py | KG-3 panel: x = √(ρη) with water 997.05 kg/m³ · 0.890 mPa s and isopropanol 781.0 · 2.038 at 25 °C; air at the origin |
| fig07_exp3_glucose | results/v2/asis/shifts.csv, glucose_xrel.csv, glucose_resolution.csv, glucose_xrel_vs_conc.csv (DS-3, P) | research/paper/analysis/make_figures_v2.py | x_rel = mean over n = 3–9 of (−Δf_n + ΔΓ_n)/(−Δf_n,w + ΔΓ_n,w); KG line through the water point with slope mean_n(−Δf_n,w/√n); 3σ_x = 3·sd(replicas)/slope, worst overtone |
| fig08_phi_all_media | results/v2/asis/phi_all.csv | research/paper/analysis/make_figures_v2.py | P fit on every sweep; mean ± sd over the three replicas per medium; single sweeps for 2026-09-03 and 2026-07-28 |
| si/fig02_raw_sweeps | research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5) | research/paper/analysis/make_figures.py | raw samples, no processing |
| si/fig03_G_B_locus | sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5) | research/paper/analysis/make_figures.py | chain: SG 51/3 + spline s=0.001, fold rule, exact inversion; window ±4 Γ_hh; dotted = max G, dashed = PSL f_res |
| si/fig04_fits_residuals | sweep_dumps_2026-09-11.npz (air_1/g5, wat_1/g5, ipa_1/g9) | research/paper/analysis/make_figures.py | fits on ±3 Γ_hh around max G; symmetric model drawn without its linear term for shape; dotted = max G |
| si/fig09_repeatability | results/sweeps_asis.csv | research/paper/analysis/make_figures.py | sd over the three plateau sweeps per phase, estimator and overtone |
| si/fig10_forward_model | results/forward_model.csv (blocks A and E) | research/paper/analysis/make_figures.py | BVD truth through divider, AD8302 laws with board phase on ∠H, ADC quantisation; same chain and estimators as the data |
| si/figS_kg2_loglog | results/v2/asis/shifts.csv, kg2_slopes.csv | research/paper/analysis/make_figures_v2.py | log–log OLS on n = 3–9; lines drawn through the n = 3 point |
| si/figS_estimator_errors | results/v2/asis/shifts.csv | research/paper/analysis/make_figures_v2.py | n = 3–9; M's Γ = half of its −3 dB width where it exists (off scale) |
| si/figS_halfheight_width | results/v2/asis/bias_per_overtone.csv | research/paper/analysis/make_figures_v2.py | mean of three sweeps per medium and overtone |
| si/figS_datalogs_0911 | 2026-09-11_12-14-42_multi.csv and _multi_amplitude.csv | research/paper/analysis/make_figures_v2.py | as logged; f_air = mean over 27–37 min |
| si/figS_glucose_lines | results/v2/asis/phases.csv (DS-3, P) | research/paper/analysis/make_figures_v2.py | shifts relative to the water plateau; OLS with intercept on 0, 5, 7.5, 10 % w/v |
| si/figS_firmware_correction | results/v2/asis/shifts.csv, results/v2/fwfix/shifts.csv | research/paper/analysis/make_figures_v2.py | difference of the shifts between the two variants |
| si/figS_phi_vs_frequency | results/v2/asis/phi_all.csv; bias_theory.md (delays) | research/paper/analysis/make_figures_v2.py | φ against frequency with the phase of a pure delay for the two delays measured on the short / 50 Ω standards of 2026-09-03 |
