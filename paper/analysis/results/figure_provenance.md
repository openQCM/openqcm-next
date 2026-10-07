# Figure provenance

| figure | source dataset | script | parameters |
|---|---|---|---|
| fig02_raw_sweeps | research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5) | paper/analysis/make_figures.py | raw samples, no processing |
| fig03_G_B_locus | sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5) | paper/analysis/make_figures.py | chain: SG 51/3 + spline s=0.001, fold rule, exact inversion; window ±4 Γ_hh; dotted = max G, dashed = PSL f_res |
| fig04_fits_residuals | sweep_dumps_2026-09-11.npz (air_1/g5, wat_1/g5, ipa_1/g9) | paper/analysis/make_figures.py | fits on ±3 Γ_hh around max G; symmetric model drawn without its linear term for shape; dotted = max G |
| fig05_argmax_bias | results/sweeps_asis.csv (psl rows) | paper/analysis/make_figures.py | bias_meas = f_Gmax − f_res(PSL); bias_pred = Γ_PSL tan(φ_PSL/2) |
| fig06_phi_vs_frequency | results/sweeps_asis.csv; results/bias_theory.json (air_0903, osl); handoff-tables.md Table 7 | paper/analysis/make_figures.py | PSL φ per sweep; delay lines 360·f·τ with τ from the short/50 Ω standards; φ₀ − 360·f·τ least-squares lines on n = 1–9 for the two instruments |
| fig07_shifts_vs_KG | results/shifts_asis.csv | paper/analysis/make_figures.py | shifts liquid − air, mean of 3 sweeps; error bars = quadrature sd of the two plateaus, divided by n |
| fig08_estimator_errors | results/shifts_asis.csv | paper/analysis/make_figures.py | overtones 3–9, both liquids; magnitude 'Γ' = half of the −3 dB width of |H| where defined (eps_G off scale) |
| fig09_repeatability | results/sweeps_asis.csv | paper/analysis/make_figures.py | sd over the three plateau sweeps per phase, estimator and overtone |
| fig10_forward_model | results/forward_model.csv (blocks A and E) | paper/analysis/make_figures.py | BVD truth through divider, AD8302 laws with board phase on ∠H, ADC quantisation; same chain and estimators as the data |
| fig11_datalog_run | research/air-ipa-water-1920-2026-09-11/data/2026-09-11_12-14-42_multi.csv | paper/analysis/make_figures.py | as logged; f_air = mean of the last 20 rows before 30 min |
