# Running list — verified facts, hypotheses, open questions, assumptions, limitations, reviewer objections

*Kept during the analysis (2026-10-06). Numbers refer to `paper/analysis/results/*.md` unless stated. "Repo" = the `impedance-analysis` branch documentation and code as of commit 37fce4b.*

## A. Verified facts (reproduced independently in this work)

1. **Constants.** R17 = 52.3 Ω; AD8302 30 mV/dB (600 mV/decade), 10 mV/°, centre 0.900 V, 1.8 V at 0° (data sheet Rev. B eqs. 8a, 9; `docs/datasheet/ad8302.pdf`). INPB attenuator (47.0 + 4.99)/4.99 = 10.4188 → 20.356 dB → 0.610692 V at 30 mV/dB. ADC 3.3 V / 4096; op-amp gains 2 (magnitude) and 1.5 (phase). All as in `core/constants.py` and `processors/Multiscan.py`.
2. **Inversion.** M = R17·10^((V_CP − V_MAG)/0.6), R_q = M cos φ − R17, X_q = −M sin φ, G = R_q/(R_q²+X_q²), B = −X_q/(R_q²+X_q²): re-derived from H = R17/(Z_q+R17) and the detector laws (`notes/derivations.md` §3), numerically identical to the repository's closed form.
3. **Independent re-implementation reproduces the instrument.** `paper/analysis/qcmchain.py` (written from the equations, sharing only the smoothing definition) reproduces `software/tests/data/psl_expected_2026-09-11.json` (f_Gmax, Γ_hh, PSL f_res, Γ, φ, rms) to all printed digits on every sweep checked.
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
- H4. Water n = 3's two-state behaviour (±50 Hz, fold decision at threshold) is a detector artefact (the phase peak grazing zero) and not a sample effect.

## D. Open questions

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
