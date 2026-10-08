# Running list — verified facts, hypotheses, open questions, assumptions, limitations, reviewer objections

*Kept during the analysis (2026-10-06). Numbers refer to `research/paper/analysis/results/*.md` unless stated. "Repo" = the `impedance-analysis` branch documentation and code as of commit 37fce4b.*

## A. Verified facts (reproduced independently in this work)

1. **Constants.** R17 = 52.3 Ω; AD8302 30 mV/dB (600 mV/decade), 10 mV/°, centre 0.900 V, 1.8 V at 0° (data sheet Rev. B eqs. 8a, 9; `docs/datasheet/ad8302.pdf`). INPB attenuator (47.0 + 4.99)/4.99 = 10.4188 → 20.356 dB → 0.610692 V at 30 mV/dB. ADC 3.3 V / 4096; op-amp gains 2 (magnitude) and 1.5 (phase). All as in `core/constants.py` and `processors/Multiscan.py`.
2. **Inversion.** M = R17·10^((V_CP − V_MAG)/0.6), R_q = M cos φ − R17, X_q = −M sin φ, G = R_q/(R_q²+X_q²), B = −X_q/(R_q²+X_q²): re-derived from H = R17/(Z_q+R17) and the detector laws (`notes/derivations.md` §3), numerically identical to the repository's closed form.
3. **Independent re-implementation reproduces the instrument.** `research/paper/analysis/qcmchain.py` (written from the equations, sharing only the smoothing definition) reproduces `software/tests/data/psl_expected_2026-09-11.json` (f_Gmax, Γ_hh, PSL f_res, Γ, φ, rms) to all printed digits on every sweep checked.
4. **Argmax bias.** f_Gmax − f_res = Γ tan(φ/2) for the rotated Lorentzian (derivation §7); on the 45 sweeps measured − predicted = +1 ± 28 Hz (sd), max 77 Hz, mean +0.016 Γ.
5. **Half-height width of a rotated Lorentzian** = Γ √(1 + 2 tan²(φ/2)); midpoint bias = 2Γ tan(φ/2) (new closed forms, verified numerically to the 1 Hz grid).
6. **Estimator errors on overtones 3–9, both liquids, air→liquid shifts vs Kanazawa–Gordon at 25 °C** (`results/tables_asis.md`): magnitude maximum eps_f = +52…+92 %; max G + half height eps_f = +19.5…+29.5 %, eps_Γ = −7.4…+6.3 %; symmetric Lorentzian + linear background eps_f = +24.5…+34.4 %, eps_Γ = −3.0…+11.3 %; phase-shifted Lorentzian eps_f = −1.4…+8.2 %, eps_Γ = −3.9…+9.3 %, |Δf|/ΔΓ = 0.98–1.08; BVD circle eps_f = −2.5…+37.9 % (unstable on water n = 3).
7. **The repository's "8 % on overtones 3–9 where argmax was 20–30 % off" is correct for the frequency shift** (max |eps_f| = 8.2 % PSL vs 19.5–29.5 % argmax). **For the bandwidth shift it is not an improvement**: eps_Γ was already within ±7.4 % with the half-height width and is −3.9…+9.3 % with the PSL (the 9.3 % is water n = 3, the two-state sweep). The gain of the PSL is on frequency.
8. **Decomposition.** Admittance reconstruction alone (magnitude max → max of G) removes 2/3 of the frequency error (+52…+92 % → +20…+30 %) and gives a bandwidth with a physical definition (the magnitude channel's −3 dB width is undefined inside the sweep window for n ≥ 5 in liquid). The rotation correction removes the remaining +20…+30 % → ±8 %.
9. **φ is an instrument property on this board**: −8.0, −14.5, −20.6, −22.9, −26.8° (air, n = 1…9), sd ≤ 0.25° across replicas 4–25 min apart (water n = 3: 2.5°, fold flip), equal in air and liquid within 0.2–1.5° on n = 3–9 (n = 1: −8.0 vs −5.0; n = 5: −20.6 vs −24.0/−24.7), on another day (2026-09-03, 125 MHz board, air) −7.8, −17.5, −22.6, −25.7, −28.9°. It coincides with the board phase φ_b of the repository's two-channel BVD forward model in air (−7.6, −13.8, −19.9, −22.1, −20.4°) to 0.3–0.8° on n = 1–7. Forward model here: φ_fit = φ_b (to 0.5°) when a board phase is applied to ∠H.
10. **φ is not a pure delay**: 360·f·τ with τ = 0.74–1.10 ns (short/50 Ω standards) gives 1.4–2.0° at 5 MHz and 12–18° at 45 MHz; φ grows ≈ f^0.55.
11. **Residuals.** PSL rms 0.15–0.65 % of range in liquid, 1.0–2.7 % in air (the fold plateau under the peak); symmetric Lorentzian + linear background 2.0–3.5 % in liquid, 3.4–4.1 % in air; S-shaped residual = the missing dispersive term.
12. **Repeatability over three sweeps** (sd): f 1–23 Hz air, 1–29 Hz liquid (water n = 3: 16–52 Hz, two-state), Γ ≤ 3 Hz air, ≤ 13 Hz liquid (water n = 3 up to 38 Hz). PSL and argmax similar; PSL slightly better on n ≥ 5 in liquid.
13. **Gate / failure rate**: 45/45 PSL fits converge and pass the instrument's gate; 45/45 symmetric fits converge; the half-height width is two-sided on 45/45; the magnitude −3 dB width is undefined on 15/45 (liquid n ≥ 5, both sides beyond the window).
14. **Datalogs**: the live instrument (argmax, half height) reproduces the sweep analysis (2026-09-11: eps_f +17…+29 %, eps_Γ −7…+6 % on n = 3–9); the production magnitude chain logged at the same instants gives eps_f = +51…+90 % (2026-09-11) and +51…+98 % (2026-09-10) on n = 3–9, and a −0.3 dB width that reaches 3.7–6.4 kHz at n = 9 with no theoretical counterpart. Duplicate rows: 95/486 (09-11), 36/175 (09-10).
15. **Firmware 0.1.5c carry-over (+0.2 % on counts)**, undone offline: changes f by ≤ 2 Hz and Γ by ≤ 2 Hz on 44/45 sweeps for the PSL (≤ 1 Hz in air); φ by ≤ 0.2°. Exception: water n = 3 replica 3 (fold decision flips: f_PSL +37 Hz, φ +4.3°; argmax +111 Hz). The summary error ranges move by ≤ 2 percentage points.
16. **The fundamental is off for every estimator**: eps_Γ = +29 % (water) and +35–37 % (isopropanol) with |Δf|/ΔΓ = 0.76–0.89; air D = 26 ppm (09-11) and 19.6 ppm (09-10) against 9–10 and 5–6 on the overtones.
17. **Dynamic range**: in liquid the divider ratio at resonance is −22 to −27 dB with 1.6–14 dB contrast; AD8302 specified ±30 dB.
18. **Smoothing bias (new)**: on synthetic data the instrument's SG 51/3 + spline widens Γ by +6.6 Hz (+10 %) at Γ = 65 Hz and +3.5 Hz (+2 %) at 190 Hz; negligible in liquid. Air D at n = 1 is therefore over-estimated by ~10 % by the chain.
19. **Fold δ bias (new)**: smoothing rounds the V of the fold; the recovered δ is 1.0–2.3° more negative than the true offset on synthetic air-like data. No effect on f_res, Γ when a fold exists.
20. **Forward model limit (new)**: with a board phase on ∠H the exact inversion is a Möbius map, not a rotation; the PSL residual bias is ≈ −0.34 Γ (R17/R1) at φ_b = −20°: −12 Hz at R1 = 1.6 kΩ, −344 Hz at R1 = R17 (Γ = 1 kHz). For the real air cases −12…−39 Hz; liquid −7…−59 Hz (≤ 2 % of Γ) against −133…−743 Hz for argmax.

## A2. Verified facts from the second dataset (2024-05-29, second instrument and crystal; `results/glucose_*`)

21. **Cross-check.** The paper's independent chain reproduces the reference analysis of that dataset (instrument code, decimated PSL, firmware-corrected) on every quantity listed in the integration prompt: φ in air −7.3, −19.8, −19.5, −25.4, −28.1°; fold on all overtones in air and on n = 1, 3 in liquid, none on n = 5–9; 75/75 fits through the gate; Newtonian ratio 1.20–1.41 (argmax) / 1.01–1.16 (PSL); water Δf/Δf_KG 1.20–1.36 / 1.06–1.13, ΔΓ/ΔΓ_KG 0.96–1.05; eq. 8 +20 ± 28 Hz, max 0.095 Γ; concentration slopes to 0.1 Hz/%; ρη relative 1.094/1.171/1.256; φ₀ = −8.2°, τ = 1.31 ns, rms 2.6°. No discrepancy to explain. As-is vs firmware-corrected: f ≤ 4 Hz, Γ ≤ 1 Hz, φ ≤ 0.2°.
22. **Estimator ranking repeats** on four liquids (water, glucose 5/7.5/10 % w/v): argmax Newtonian ratio 1.20–1.41, PSL 1.01–1.16; midpoint 1.31–1.68; symmetric + linear 1.17–1.47; circle 0.90–1.16. Bandwidth right before the fit (ΔΓ/ΔΓ_KG 0.96–1.00 argmax).
23. **Residual zig-zag over n is instrumental**: PSL ρ_N = 1.15, 1.01, 1.16, 1.12 on n = 3, 5, 7, 9 in water and the same ±0.02 in the three glucose solutions; coincides with the φ anomaly of that board (|φ(5)| = 14.4° < |φ(3)| = 19–21° in liquid).
24. **φ on the second board**: air −7.3, −19.7, −19.5, −25.3, −27.9°; liquid +0.7…+1.2, −18.8…−20.8, −14.3…−14.6, −27.5…−28.7, −30.4…−31.9°; sd ≤ 0.13° (air n = 1) and ≤ 0.07° (liquid); independent of concentration within 2°. Agrees with board 1920 within 1–3° on n = 1, 5, 7, 9; differs by 5° on n = 3; **not monotonic in frequency**; sign on the liquid fundamental opposite (+1° vs −5°).
25. **φ₀ − 360fτ**: 2024 air φ₀ = −8.2°, τ = 1.31 ns (rms 2.6°; n = 3–9 only: −14.0°, 0.85 ns); 2026-09-11 air −7.0°, 1.28 ns (rms 1.2°; n ≥ 3: −9.4°, 1.09 ns); 2026-09-03 air −7.9°, 1.40 ns. An approximation (rms 1–5°), parameters sensitive to n = 1.
26. **The fundamental follows the theory on the second crystal**: ΔΓ₁/ΔΓ_KG = 1.04 (argmax) / 1.07 (PSL), ρ_N = 1.04 / 1.01, although its air dissipation is higher (44–46 ppm, Γ = 110–115 Hz) than the 2026 crystal's (26 ppm). The 2026 fundamental excess is therefore not a property of the method nor of the air damping as such.
27. **Concentration series** (PSL, OLS with intercept vs water): Δf slopes −7.1, −13.8, −17.8, −24.7, −30.4 Hz/% w/v; ΔΓ +9.2, +13.1, +16.6, +28.0, +37.8 Hz/%; ΔD 3.68, 1.75, 1.33, 1.60, 1.68 ppm/%; R² 0.91–0.94 on n = 1, 3 (5 % point 12–18 Hz below the line, replica scatter 0.3–3 Hz), 0.986–0.990 on n ≥ 5. ρη/(ρη)_water from Δf, mean n = 3–9: 1.094, 1.171, 1.256 (PSL) and 1.089, 1.171, 1.257 (argmax) — the two estimators agree on the ratio to 0.5 %. From ΔΓ: 1.08–1.18, 1.15–1.30, 1.22–1.42, growing with n (unexplained).
27b. **Checks requested on §6.6 (2026-10-07, regenerated with `qcmchain.py`, fwfix; `results/glucose_conc_fwfix.csv`, `glucose_drift_fwfix.csv`, `glucose_clipwindow_fwfix.csv`):**
    - the 5 % plateau is less loaded than the OLS line on every overtone: Δf residual +12, +18, +10, +16, +15 Hz (PSL; A: +11, +26, +15, +21, +21), ΔΓ −13, −14, −13, −14, −9 Hz (PSL) — ≈ constant in Hz, not ∝ √n, so not a ρη error;
    - drift inside the plateaus (slope of f over the three replicas, PSL): glucose ≤ 0.4 Hz/min (−0.08…+0.37), water −0.17…−1.02 Hz/min (n = 1…9), air +0.07…+0.59; the 5 % plateau is −4.3 min off the time–concentration line (plateau mean times 19.9, 34.5, 48.1, 63.3 min; 4.27 min per %), so a time-linear drift gives ≤ ~4 Hz at 5 %; drift needed to explain the residual: −2.3…−4.3 Hz/min (PSL), −2.7…−6.2 (A), i.e. 5–15× the measured one;
    - ρη from ΔΓ at 10 %: n = 3: 1.245 (Δf 1.224), n = 5: 1.225 (1.237), n = 7: 1.358 (1.268), n = 9: 1.418 (1.296); n = 1: 1.279 (1.210). Not monotonic; n = 5 agrees; at n = 9 the discrepancy is with P only (A: 1.307). Symmetric window limited by the sweep edge (2.45–2.62 Γ at n = 9; 2.92–3.12 at n = 7): n = 9 1.418 → 1.395 (≈ a fifth of the gap), n = 7 unchanged. Roughness term ∝ ρn (Daikhin–Urbakh) cited as an untestable hypothesis.
27c. **Claim checks for the second campaign (2026-10-07; `results/glucose_collapse_*.csv`, `glucose_resolution_*.csv`, `glucose_datalog_*.csv`):**
    - √n structure (CV of −Δf_n/√n over n = 3–9, no liquid constants): argmax 5.8–6.7 %, symmetric + linear 7.8–8.1 %, PSL 2.4–2.9 % on water and the three glucose solutions; ΔΓ_n/√n: half-height 1.9–2.0 %, PSL 3.1–3.8 %. **Campaign 1 differs**: Δf CV argmax 3.4 % (water) / 1.9 % (ipa), PSL 4.1 / 3.6 % — on board 1920 the rotation bias grows smoothly with n and does not spoil the collapse; the collapse improvement is board-specific, the level improvement is not.
    - Resolvability: every concentration step (5, 2.5, 2.5 % w/v) is ≥ 13.5 σ (f) and ≥ 15 σ (Γ) of the replica scatter with the PSL on every overtone, ≥ 4.5 σ with argmax; 3·sd/slope: PSL 0.10–0.17 % w/v (f), 0.03–0.29 (Γ); argmax 0.4–1.1 % (f). The 5 % plateau residual (+10…+18 Hz) is 0.5–1.7 % w/v equivalent: accuracy-limiting.
    - Production amplitude datalog of the 2024 session (software 0.1.5; plateaus = last 8 min; 75 duplicates of 541 rows): water Δf/Δf_KG = 1.17, 1.27, 1.22, 1.38, 1.42 (n = 1…9) — far less than board 1920's magnitude estimator (+51…+90 %) and close to this board's argmax G (+8…+36 %); −0.3 dB width changes 0.67–2.55 kHz. On this board the reconstruction alone buys little in frequency; the rotation correction carries the improvement.
28. **Repeatability 2024**: PSL sd ≤ 3 Hz air, ≤ 8 Hz liquid; argmax ≤ 36 Hz (water n = 9). Datalog: 541 rows, 75 duplicates, 14:22–16:01; replica write times are consistent with the datalog phases under a UTC+2 reading.

## B. Documentation / code discrepancies found

- **ALGORITHM.md §11 worked example uses raw samples, not the smoothed chain.** Its numbers (V_MAG 0.194775 V, r = 3.0015°, min r = 1.2597°, M = 783.2069 Ω, f = 4 998 012 Hz, hw = 953.124 Hz) are reproduced exactly from the raw file; the current chain (SG 51/3 + spline) on the same file gives V_MAG 0.194387 V, min r 1.388°, f_Gmax 4 998 002 Hz, Γ_hh 955.05 Hz, G_max 1.3653 mS. The example is a valid check of the inversion but not of the published numbers; it should say so.
- **`lorentzian.py` docstring**: "frequency and half-bandwidth shifts … both land on Kanazawa–Gordon within 8 % on overtones 3–9": ΔΓ reaches 9.3 % (water n = 3) and the half-height width was already within ±7.4 %. Frequency: correct.
- **Johannsmann eq. 13 sign**: the repository's note (G with −Δ sin φ) is right that eq. 13 as printed is not a single rotation; the manuscript must state the convention.
- **`core/resonance.py` uses `np.int` and `np.mat`**, removed in numpy ≥ 1.24 / 2.0; the pinned environment (numpy 1.21.5) works, the current numpy does not. Not a measurement issue.
- **ALGORITHM.md §1 circuit label**: the SVG labels a 4.99 Ω resistor; constants say R19 = 4.99 (Ω) in a 47.0/4.99 divider — consistent; the DATA_FORMAT doc and ALGORITHM agree.
- **Repository `conductance-calculation.md` and `openQCM_Next_G_Impedance_Analysis.md`** describe the obsolete approximate formula (|Z| ≈ R17(10^x) + R17 with the reading as the phase of Z) and the 0.600 V offset; superseded, flagged there, not used here.
- **The repository synthesis says "φ is a property of the instrument, not of the sample"**: true to 0.2–1.5° on n = 3–9, but φ differs by 3° between air and liquid at n = 1 and by 3–4° at n = 5; part of this is δ (uncorrectable in liquid) entering φ (forward model block C: φ_fit = φ_b − δ).

## C. Hypotheses (supported but not proven)

- H1. φ is dominantly an uncorrected phase error of the detector chain (board + cable + AD8302 phase-channel offset), not a property of the sensor: supported by (A9), (A10), the forward model (φ_fit = φ_b) and the OSL standards (non-zero phase on resistive loads).
- H2. The excess dissipation of the fundamental (D_air = 20–26 ppm; ΔΓ +29–37 % over KG) is a property of this crystal/holder (mounting losses that the liquid adds to), not of the method; no estimator moves it; it also has the largest smoothing bias (+10 %), which does not explain a 30 % excess in the *shift*.
- H3. The 5–18 % out-of-roundness of the admittance locus in liquid comes from the AD8302 operating at −22 to −37 dB divider ratio (near its specified limit) plus the Möbius distortion of a phase error; a larger R17 (or switchable) would test it.
- H6. The 10–18 Hz offset of the 5 % w/v plateau (constant in Hz over n, not drift) is a step of the instrument or of the first pour (e.g. incomplete mixing, temperature of the first solution), not a property of the solution; a protocol with a return to water between concentrations would decide.
- H5. The residual overtone zig-zag of the Newtonian ratio after the PSL (2024: 1.15/1.01/1.16/1.12; 2026: 0.99/1.04/1.08/1.03 water) is the part of the board's phase response that a single angle per overtone does not capture (Möbius residual + φ non-ideality), not a sample property: it is identical across four liquids.
- H4. Water n = 3's two-state behaviour (±50 Hz, fold decision at threshold) is a detector artefact (the phase peak grazing zero) and not a sample effect.

## D. Open questions

- (2024 set) Which board and sensor? (The three glucose solutions are pharmaceutical glucose for infusion, prepared in the same way; the 5 % is Galenica Senese AIC 029863065.) Was the 5 % point's departure from the line (n = 1, 3) a baseline drift or a real non-linearity (no return to water between concentrations)? Why does the ΔΓ-based ρη ratio grow with n faster than the Δf-based one?
- Is φ(n) of the 2024 board (non-monotonic, φ(3) ≈ φ(5) in air) reproducible on that board on another day, and what in its RF path makes n = 5 anomalous?

- Is φ the same on a second board and with a second sensor? (one board, one sensor here; the 2026-09-03 air set is probably the same board but this is not recorded; the 2026-07-28 frozen water sweep gives φ = +2.2°, opposite sign, board not recorded.)
- What is the liquid temperature at the interface? (TEC at 25.00 °C on the crystal; liquid poured at room temperature; ±2 K = ±2–3 % on KG.)
- Is the residual +2…+8 % frequency excess of the PSL on n = 3–9 a Möbius residual (forward model predicts ≤ 2 % of Γ), a ρη/temperature effect, surface roughness (which increases |Δf| but also ΔΓ), or the ±3 Γ window on a clipped sweep (window right edge at 2.2–3.0 Γ for n ≥ 5 in isopropanol)?
- Does the PSL hold over a long plateau (hundreds of sweeps) and across the air→liquid transient?
- Can δ be measured independently (phase ramp through zero on the bench) and φ_b from an RLC standard in the operating range?

## E. Assumptions made in this analysis

- Liquid properties at 25 °C: water ρ = 997.05 kg/m³, η = 0.890 mPa s; isopropanol ρ = 781.0 kg/m³, η = 2.038 mPa s. Quartz ρ_q = 2648 kg/m³, μ_q = 2.947·10¹⁰ Pa. Smooth, infinitely thick Newtonian liquid; no slip; no roughness.
- Kanazawa–Gordon normalised to the measured air fundamental f_F = 5 004 596 Hz (PSL; argmax 5 004 598).
- Plateau = the three sweeps dumped per phase (times in the dataset README) for the sweep analysis; last 10 min (2.5 min on 2026-09-10) for the datalogs; exact duplicate rows dropped and counted.
- The phase-shifted Lorentzian fit window is ±3 Γ_hh around the maximum of G, seeded as the instrument does; no other tuning.
- The "magnitude-only" estimator from the sweeps uses the uncompensated local baseline (no calibration polynomial, unavailable for these sweeps); the production datalog provides the actual production estimator at the same instants.

## F. Limitations

- (2024 set) one instrument, one crystal, one day; board, sensor, DDS clock and glucose preparation not recorded; no OSL sweeps of that board; liquid temperature not measured; production software 0.1.5 wrote the raw files (format verified).

- One board (1920), one 5 MHz AT-cut sensor, one day for the main dataset; three sweeps per plateau.
- Liquid temperature not measured.
- The firmware carry-over bias is in all raw data (corrected offline; effect shown to be negligible).
- Sweep window (−12/+6 kHz) sized for air clips the ±3 Γ fit window on the right for n ≥ 5 in isopropanol and n = 9 in water.
- The BVD circle estimator is the repository's implementation (not independent) and is unstable on one sweep.
- No reference impedance analyser measurement of the same crystal (absolute accuracy of f_res, Γ, R_m not established; only shifts against theory).
- The AD8302 dynamic range in liquid.
- R_m from 1/G_max is biased by the rotation (G_peak ∝ cos²(φ/2)) and by the magnitude scale (OSL standards read M 8–14 % low): R_m is not a validated output.

## G. Potential reviewer objections (and the answer the data support)

1. "The phase-shifted Lorentzian is Johannsmann's; nothing new." → Agreed and cited; the contribution is the full chain on this hardware, the closed-form bias relations, and the quantified comparison; φ is interpreted as the board phase (forward model).
2. "You compare with theory, not with a reference instrument." → True; the Newtonian ratio |Δf|/ΔΓ = 1 is used as a ρη-independent test; a reference analyser is listed as the first remaining experiment.
3. "8 % is not impressive." → The stated accuracy is limited by ρη/temperature (±2–3 %), the window clipping, the Möbius residual (≤ 2 %) and by the one-board dataset; the paper claims the removal of a 20–30 % *systematic*, not a 1 % absolute accuracy.
4. "The fundamental does not fit." → Reported as such, with the hypothesis H2 and the air D evidence.
5. "Fitting five parameters on a smoothed curve: are the uncertainties meaningful?" → Covariance understates (structured residual); replica scatter is quoted instead.
6. "Why not fit G and B jointly / use the circle?" → Shown in the repository and here: the joint fit degrades (locus not circular), the circle depends on a free rotation and is unstable on one sweep.
7. "The fold heuristic is ad hoc." → Presented as an implementation detail with its measured fragility (one sweep at threshold).
8. "Smoothing biases Γ in air." → Quantified (+10 % at 65 Hz); the paper reports it as a limitation.

## H. Remaining experiments before submission (ranked)

1. Same crystal measured on a calibrated impedance analyser (thru configuration) in air and water, same day: absolute f_res, Γ, R_m, and the true φ of the reference (expected ≈ 0).
2. Second board and second sensor: is φ(n) a board constant? (two boards × two sensors × air/water.)
3. Liquid temperature measured (thermistor in the cell); or a water–glycerol series at controlled T to test the √(ρη) law over a range.
4. Bench phase calibration: known phase ramp through 0° to measure δ and the fold rounding; an RLC standard in the operating range to measure φ_b(f).
5. Long plateau (≥ 1 h) with the PSL live beside argmax: drift, fallback rate, noise.
6. A larger (or switchable) R17 to move the liquid operating point into the AD8302's linear range; repeat the roundness and φ tests.
7. Sweep window scaled with Γ in liquid (removes the clipping and the baseline-on-skirt bias of the half-height width).
8. Firmware 0.1.5d re-acquisition of the air/water/isopropanol set (removes the carry-over caveat from the dataset of record).

---

## v0.2 revision (2026-10-08) — additions and corrections

*Numbers from `analysis/results/v2/asis/` (regenerated from the raw sweeps on 2026-10-08; per-sweep tables reproduce the 2026-10-07 ones to ≤0.07 Hz / ≤0.5 Hz / ≤0.05°).*

### A3. Verified facts added in v0.2

29. **KG-1 as ΔΓ/(−Δf)** (inverse of the ρ_N of §A): A 0.76–0.85 (DS-2), 0.71–0.83 (DS-3); P 0.92–1.01 (DS-2), 0.86–0.99 (DS-3), overtones 3–9, all liquids. The overtone pattern of r_n after P is identical across the liquids of each dataset (DS-3: 0.87–0.88, 0.98–0.99, 0.86–0.89, 0.90–0.94 on n = 3, 5, 7, 9 in four liquids).
30. **KG-2 as a log–log slope (n = 3–9; KG −0.5)**: Δf: A −0.54 (DS-2 water), −0.50 (DS-2 ipa), −0.41 (DS-3, all liquids); P −0.58, −0.56, −0.49…−0.52. ΔΓ: A −0.62, −0.59, −0.47…−0.50; P −0.62, −0.54, −0.45…−0.52. The fit improves KG-2 on the second instrument only; on board 1920 the bandwidth slope is −0.62 with both estimators (ΔΓ_n/n in water from +9 % above KG at n = 3 to −4 % at n = 9).
31. **KG-3 with two liquids (DS-2, P)**: measured ratio of the shifts ipa/water 1.29–1.35 (Δf) and 1.29–1.41 (ΔΓ) on n = 3–9 against √(ρη) ratio 1.339; absolute level +2…+8 % (f) for both liquids.
32. **The '8 %' claim per overtone**: P |ε_f| ≤ 8.2 % on every overtone 3–9 of DS-2 (water 8.2, 7.0, 4.8, 1.4; ipa 7.9, 2.7, 4.8, 1.0); on DS-3 only n = 5 (6.1 %), n = 3, 7, 9 at 13.1, 11.0, 10.1 %. Bandwidth within 8 % with A already (max 7.4 % DS-2, 4.5 % DS-3); with P 9.3 % on the two-state sweep.
33. **Bias law on 120 sweeps**: DS-2 +1 ± 28 Hz (max 77), DS-3 +21 ± 28 Hz (max 80); mean +0.02 Γ, max 0.12 Γ (air peaks, +0.06…+0.11 Γ). Sign as the convention requires on every liquid sweep. Γ_hh/Γ_P: air 1.03–1.09 (predicted 1.02–1.06), liquid 0.93–0.99 (baseline on the skirt).
34. **Exp. 1 reproducibility DS-2 vs DS-3 (P, water, n = 3–9)**: Δf_n/n DS-3/DS-2 − 1 = +4.4, −0.9, +5.8, +11.6 %; ΔΓ_n/n −10.2, +2.0, −1.3, +2.5 %; fundamental ΔΓ −17.6 % (the DS-2 excess). Live A of board 1920 on two days: ε_f +14…+29 % and +12…+30 %.
35. **Glucose, relative √(ρη) from both channels (P, n = 3–9)**: 1.052, 1.091, 1.132 (sd over n 0.017–0.026); from Δf 1.046/1.082/1.121; from ΔΓ 1.059/1.101/1.145 (Δf- and ΔΓ-derived separate on n = 7, 9). Linear in concentration: 0.0131 per % w/v (0.0119 from Δf, 0.0144 from ΔΓ), 5 % point −0.008 (0.6 % w/v) below the line. Steps 0.052, 0.039, 0.041; σ_x = sd/slope 0.0004–0.0008 (f), 0.0001–0.0012 (Γ), every step ≥ 14 σ (f) and ≥ 15 σ (Γ); A ≥ 4 σ.
36. **φ stability**: replica sd ≤ 0.25° (one exception 2.45°, the threshold sweep); across liquids ≤ 1.1° (DS-2), ≤ 2.0° (DS-3); across glucose concentrations ≤ 1.4°; air − liquid: n = 1 −3.0° (DS-2), −8.3° (DS-3, liquid value +0.7…+1.2°); n = 5 +3.7° (DS-2), −5.0° (DS-3); n = 7, 9 ≤ 3.1°; n = 3 ≤ 0.2°. Between boards (air) +0.7, −5.2, +1.1, −2.4, −1.1°; between days on the 1920 class +0.2, −3.0, −2.0, −2.8, −2.0°. Monotonic in n: air on board 1920 (both days) yes; liquids on either board no; air on DS-3 no (φ_3 ≈ φ_5).
37. **Theory check** (`notes/theory_sla_to_kg_check.md`): SLA eq. (23) of Sensors 2021 with f_0 the fundamental, Newtonian result eq. (29) ∝ √n; derivation reproduces Eq. (4) with no sign/prefactor discrepancy; Z_q = 8.834·10⁶; water k = 673.6 Hz (NIST values), isopropanol 902.1 Hz (handbook ρ, η) / 910.0 Hz (Kerscher 2024); d ln√(ρη)/dT = −1.15 %/K (water), −1.60 %/K (isopropanol); the old document's water constants inflate KG by ×1.151.

### B2. Corrections to v0.1

- Isopropanol coefficient 901.5 → 902.1 Hz·√n (Z_q had been rounded); Z_q (acoustic) vs Z_el (electrical) now distinct symbols; liquid constants cited (NIST WebBook; Kerscher et al. 2024); ρ_N renamed r_n = ΔΓ/(−Δf).
- v0.1's production-datalog numbers for the 2024 session (+17…+42 %) are not reproducible from the repository (full datalog gitignored and absent; only the 15:00–16:01 extract remains) and are no longer cited.

### D2. Open questions added

- Why φ at the fundamental differs between air and liquid by 3–8° (and changes sign on the second instrument) although a fold exists there and δ is corrected: the rounded fold under the peak (residual of the bias law −40…−45 Hz at the liquid fundamentals) is the candidate; not tested.
- Why r_n after P is 0.86–0.90 on n = 3, 7, 9 of the second instrument and 0.98–0.99 on n = 5, identically in four liquids: the overtone pattern follows |φ_5| < |φ_3| on that board; a per-overtone residual of the single-angle model, or the AD8302 phase non-linearity near 0°, are candidates.

### H2. Remaining experiments — see `notes/remaining_experiments.md` (updated 2026-10-08) and SI S11.
