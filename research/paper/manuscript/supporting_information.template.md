---
title: "Supporting Information — QCM frequency and dissipation estimation using DDS excitation, gain–phase detection and complex-admittance reconstruction"
author:
  - "openQCM NEXT impedance-analysis working group"
date: "Draft v0.2 — 2026-10-08"
bibliography: ../literature/references.bib
---

*Every number in this document is regenerated from the raw data by the scripts in `research/paper/analysis/` (`run_estimators.py`, `run_glucose.py`, `run_v2.py`, `run_bias_theory.py`, `run_forward_model.py`, `make_figures_v2.py`, `make_si.py`); the tables below are written by `make_si.py` from `results/v2/asis/*.csv`. Variant "as acquired" unless stated; the firmware-corrected variant is in `results/v2/fwfix/` and Section S7.*

# S1. Literature comparison, full table

The full comparison table (hardware architecture, sweep method, measured quantities, phase measured, complex $Y/Z$ reconstructed, BVD fitting, Lorentzian fitting, frequency estimator, dissipation estimator, liquid validation, multi-overtone, real-time suitability, computational complexity, cost class), with the verification grade of each entry, is `research/paper/literature/comparison_table.md`; the literature review and the novelty assessment are `literature_review.md` and `novelty_assessment.md` in the same folder. The compact Table 1 of the main text is its first block.

# S2. Small-load approximation to Kanazawa–Gordon: sources and checks

The derivation of main-text Eqs. (1)–(4) was carried out twice independently (`notes/derivations.md` §6 and `notes/theory_sla_to_kg_check.md`). The points verified against the sources: (i) the SLA normalises the complex shift to the *fundamental* $f_F$ and is applied at the overtone frequency $f_n = nf_F$ inside the load impedance, which is what produces $\Delta f_n \propto \sqrt n$ [@Johannsmann2008; @Johannsmann2021]; (ii) with $\exp(i\omega t)$ the imaginary part of the shift is $+\Delta\Gamma$ and the Newtonian impedance is $(1+i)\sqrt{\omega\rho\eta/2}$, so $\Delta\Gamma_n = -\Delta f_n > 0$; (iii) for $n = 1$ Eq. (4) is the relation of Kanazawa and Gordon [@KanazawaGordon1985AC]. Numerical check with $\rho_q = 2648$ kg m⁻³, $\mu_q = 2.947\times10^{10}$ Pa ($Z_q = 8.83\times10^6$ kg m⁻² s⁻¹), $f_F$ = 5 004 596 Hz (DS-2) and 5 000 107 Hz (DS-3): coefficient 715.04 and 714.08 Hz per $\sqrt n$ per unit $\sqrt{\rho\eta}$; water ($\sqrt{\rho\eta}$ = 0.9420 kg m⁻² s⁻¹ᐟ², NIST Chemistry WebBook, IAPWS-95 density and IAPWS 2008 viscosity [@NISTWebBookWater]) 673.6 and 672.7 Hz·$\sqrt n$; isopropanol (1.2616, handbook values 781.0 kg m⁻³ and 2.038 mPa s; Kerscher et al. [@Kerscher2024] measure 780.9 and 2.07) 902.1 Hz·$\sqrt n$ (910 Hz with Kerscher's values). The 2021 tutorial writes the SLA as its Eq. (23) with $f_0$ the fundamental and derives its Eq. (29), $(-1+i)\sqrt n\sqrt{f_0}\sqrt{\rho\eta}/(\sqrt\pi Z_q)$, for the Newtonian liquid, which is Eq. (4) of the main text; the 2008 and 1985 primary texts were not reachable from this session and their equation numbers are not cited (see `notes/theory_sla_to_kg_check.md` for the grading). Temperature sensitivity of the prediction: $\partial\ln\sqrt{\rho\eta}/\partial T = -1.15$ %/K for water near 25 °C (NIST values at 23 and 27 °C) and $-1.6$ %/K for isopropanol [@Kerscher2024], so ±2 K on the unmeasured liquid temperature is ±2–3 % on $\Delta f_\mathrm{KG}$ and $\Delta\Gamma_\mathrm{KG}$ and nothing on KG-1 and KG-2. The water constants of the earlier internal document (1.102933 g cm⁻³, 0.010665 g cm⁻¹ s⁻¹) would raise the prediction by $\sqrt{1.102933\cdot1.0665/(0.99705\cdot0.890)} = 1.151$, i.e. by 15 %; they are not used.

# S3. The phase reading: fold detection, offset, sign, and the locus

**Model and rule.** $r(f) = |\phi(f) + \phi_b| - \delta$ (main text, Section 4). The instrument declares a fold when the reading's minimum reaches at least 88 % of the way from its off-resonance level to 0° and sits within 5 Γ of the conductance maximum; the decision is latched over two consecutive sweeps. With a fold, $\delta = -\min r$ is subtracted and the branch past the vertex is negated for $B$; without a fold the reading is used unsigned and uncorrected. On DS-2 the fold is present on all overtones in air (vertex from +0.6° at $n$ = 9 to −6.4° at $n$ = 5, i.e. δ = −0.6…+6.4°), on the fundamental in both liquids, and on none of the overtones $n \ge 3$ in liquid, where the minimum stays 9–45° above zero; on DS-3 the same, with the fold also on $n = 3$ in all four liquids. One sweep of 120 (DS-2, water, $n = 3$, third replica) has a minimum depth of 0.880, exactly at the threshold: the instrument's datalog shows the logged pair alternating between two states 105 Hz and 7.7 × 10⁻⁶ apart from 13:12 onwards, and the 0.2 % firmware correction flips its decision (Section S7). This is the fragility of the rule, and it is the one failure observed.

**Why $G$ is even in the sign and not in the offset.** $G$ depends on $\phi$ through $\cos\phi$ and $\sin^2\phi$ only, so the unsigned reading suffices for $G$ and for everything derived from it; $B$ depends on $\sin\phi$ and needs the sign. An additive $\delta$ is not removed: $\partial G/\partial\phi \propto \sin\phi$ vanishes at resonance and not on the flanks, so an uncorrected offset distorts the peak shape more than its position; the forward model (S6) gives ≤11 Hz on $f_\mathrm{res}$ (15 Hz where the offset triggers a spurious fold) and ≤7 Hz on Γ for ±5° in liquid, and an almost one-to-one entry of $\delta$ into the fitted angle, $\varphi_\mathrm{fit} \approx \phi_b - \delta$.

**What the rule must not do.** Flipping the sign on a damped load (no fold) splits the locus into two arcs (step of 28–89 % of the range of $B$); zeroing the minimum on a damped load subtracts 9–45° and takes $r_n$ to 0.5–0.8; estimating $\delta$ by making the locus round buys roundness by breaking the trajectory. The repository documents these three failed variants (`research/air-ipa-water-1920-2026-09-11/fold-hypothesis.md`). The locus $B(G)$ is a circle to 1–7 % of its radius in air and 5–18 % in liquid, visibly rotated with respect to the $G$ axis (Fig. S2); the out-of-roundness in liquid coincides with the divider ratio sitting at −22 to −37 dB, the edge of the AD8302's specified range, and with the Möbius distortion of a phase error (S6).

**Fold rounding.** The smoothing (Savitzky–Golay 51/3 + spline) rounds the V of the fold over 20–50 Hz; on synthetic air-like data the recovered $\delta$ is 1.0–1.8° more negative than the true offset, with no effect on $f_\mathrm{res}$ or Γ when a fold exists. The rounded fold under the narrow air peaks is what leaves the fit residual at 1–3 % of the range in air (Fig. S3) and the closed-form bias of the maximum 5–8 Hz short there (main text Fig. 5).

![Fig. S1. Raw detector voltages for the fundamental and the 5th overtone in air and for the 5th overtone in water (DS-2). Right axis: the unsigned phase reading. In air the reading folds at zero and overshoots it (the signature of δ); in water it does not reach zero.](../figures_v2/si/fig02_raw_sweeps.png)

![Fig. S2. Reconstructed conductance and susceptance (top) and admittance locus (bottom) on ±4 Γ for the sweeps of Fig. S1. Dotted: the maximum of $G$; marker: $f_\mathrm{res}$ of the phase-shifted fit.](../figures_v2/si/fig03_G_B_locus.png)

# S4. Closed-form biases of the simple estimators for a rotated Lorentzian

With $\Delta = f_\mathrm{res} - f$ and $G - G_\mathrm{off} = A(\Gamma\cos\varphi - \Delta\sin\varphi)/(\Delta^2 + \Gamma^2)$, $dG/d\Delta = 0 \iff \sin\varphi\,\Delta^2 - 2\Gamma\cos\varphi\,\Delta - \Gamma^2\sin\varphi = 0$, whose maximum is $\Delta_\mathrm{max} = \Gamma(\cos\varphi - 1)/\sin\varphi = -\Gamma\tan(\varphi/2)$, hence $f_{G\max} = f_\mathrm{res} + \Gamma\tan(\varphi/2)$. The peak height above $G_\mathrm{off}$ is $(A/\Gamma)\cos^2(\varphi/2)$ and the curve has a negative lobe $-(A/\Gamma)\sin^2(\varphi/2)$ at $\Delta = \Gamma/\tan(\varphi/2)$. The half-height crossings (level $G_\mathrm{off}$ + half the peak height, $c = \cos^2(\varphi/2)$) solve $c\Delta^2 + 2\Gamma\sin\varphi\,\Delta + \Gamma^2(c - 2\cos\varphi) = 0$, $\Delta_\pm = \Gamma[-\sin\varphi \pm \sqrt{c(2-c)}]/c$, so $\Gamma_\mathrm{hh} = (\Delta_+ - \Delta_-)/2 = \Gamma\sqrt{(2-c)/c} = \Gamma\sqrt{1 + 2\tan^2(\varphi/2)}$ and $f_\mathrm{mid} = f_\mathrm{res} + 2\Gamma\tan(\varphi/2)$. Checked on noise-free model curves on the 1 Hz grid (`results/closed_forms_check.csv`): argmax bias numerical/theory −3.0/−2.8 Hz (φ = −5°, Γ = 65 Hz) … −582/−582 Hz (−40°, 1600 Hz); Γ_hh/Γ 1.0014/1.0019 … 1.1198/1.1247; midpoint −5.7/−5.7 … −1048/−1165 Hz (the midpoint deviates from its closed form at large |φ| because the grid and the window truncate the far crossing). A symmetric Lorentzian with constant background fitted to a rotated one is biased by 1.9–2.1 Γ tan(φ/2) in frequency and over-estimates Γ by 2–35 % between −8° and −28°; with a linear background Γ is right to 0.2 % and the frequency bias is ≈1.25 Γ tan(φ/2).

**Sign convention.** Johannsmann et al. print Eq. 13 with $+\Delta\sin\varphi$ in $G$ and $+\Delta\cos\varphi$ in $B$; with one $\varphi$ in both lines that is not a single rotation (the lines correspond to $\varphi$ and $-\varphi$). Fitting $G$ alone, the two conventions are observationally identical and differ only in the sign quoted for $\varphi$; the main text uses the rotation form, in which the fitted angle is negative on both boards and the maximum of $G$ lies below $f_\mathrm{res}$. On the data the measured $f_{G\max} - f_\mathrm{res}$ is negative on every liquid sweep and on every air sweep with $n \ge 3$ (Table S8), as the convention requires.

![Fig. S3. Conductance (dots) with the phase-shifted Lorentzian (solid) and the symmetric Lorentzian with linear background (dashed) on ±3 Γ_hh for three sweeps of DS-2; below, the residuals in percent of the range of $G$.](../figures_v2/si/fig04_fits_residuals.png)

# S5. Fitting: window, initialisation, acceptance gate, fallback rate, residuals, repeatability

Window $|f - f_{G\max}| \le 3\Gamma_\mathrm{hh}$ (clipped by the sweep edge on the right for $n \ge 5$ in isopropanol, 2.2–3.0 Γ available, and at $n = 9$ in DS-3, 2.8–2.9 Γ in water and 2.5–2.6 Γ in the glucose solutions); seeds $f_{G\max}$, $\Gamma_\mathrm{hh}$, $\varphi = 0$, $G_\mathrm{off} = \min G$, $G_\mathrm{max}$ = range of $G$; frequencies scaled to kHz about the seed and conductances to mS; Levenberg–Marquardt with tolerances 10⁻¹². Gate (instrument constants): convergence, $f_\mathrm{res}$ inside the window, $0.3 \le \Gamma/\Gamma_\mathrm{hh} \le 3$, $|\varphi| \le 60^\circ$, rms residual ≤ 5 % of the range; the limits were set at about ten times the observed values on DS-2 and never fired: 45/45 fits of DS-2 and 75/75 of DS-3 converged and were accepted (fallback rate 0 %). Residuals (rms, percent of the range of $G$): phase-shifted 1.0–2.7 % in air and 0.15–0.65 % in liquid on DS-2, 0.9–1.4 % and 0.2–0.8 % on DS-3; symmetric Lorentzian with linear background 3.0–4.2 % and 0.8–3.5 % (DS-2), 1.8–4.2 % and 0.7–3.8 % (DS-3), always S-shaped (Fig. S3). The fit's covariance gives 0.1–0.8 Hz on $f_\mathrm{res}$, an order of magnitude below the replica scatter, because the residual is structured; the replica scatter is the number quoted. Repeatability over the three sweeps of a plateau (Fig. S4): DS-2, $f_\mathrm{res}$ 1.5–23 Hz in air (the air baseline was still drifting at −0.3 to −2 Hz/min) and 0.3–29 Hz in liquid, Γ ≤ 2.3 Hz in air and ≤ 38 Hz in liquid (the two-state sweep; ≤ 13 Hz otherwise); DS-3, $f_\mathrm{res}$ ≤ 2.4 Hz in air and ≤ 7.6 Hz in liquid, Γ ≤ 0.7 and ≤ 4.5 Hz. The magnitude estimator's −3 dB width is undefined inside the window on 15 of 45 (DS-2) and 33 of 75 (DS-3) sweeps; the half-height width of $G$ is two-sided on all 120.

![Fig. S4. Standard deviation over the three plateau sweeps of $f_\mathrm{res}$ (left) and Γ (right) per estimator, overtone and load, DS-2.](../figures_v2/si/fig09_repeatability.png)

# S6. Forward model, board phase, resistive standards

A board phase does not multiply the admittance; it multiplies the measured transfer function, $H_\mathrm{meas} = He^{j\phi_b}$. Inverting exactly with that phase gives $Y' = 1/[(Z_\mathrm{el} + R_{17})e^{-j\phi_b} - R_{17}]$, a Möbius transformation of $Y_\mathrm{el} = 1/Z_\mathrm{el}$ that reduces to the rotation $Y_\mathrm{el}e^{j\phi_b}$ only when $|Z_\mathrm{el}| \gg R_{17}$. A Butterworth–Van Dyke crystal of known $f_s$, Γ, $R_1$, $C_0$ was sent through the divider and the detector laws with a board phase on $\angle H$, an offset δ, the fold, the ADC quantisation and the firmware carry-over, and through the same chain and estimators (`run_forward_model.py`, `results/forward_model.md`). Findings: (i) the fitted angle equals the imposed board phase to 0.7° on the liquid-like cases and to 1° on the air-like ones, except the one case where the offset triggers a spurious fold; (ii) with $\phi_b = 0$ both estimators recover $f_s$ to the grid; (iii) with $\phi_b = -8$ to $-25^\circ$ the maximum of $G$ is off by −91 to −743 Hz on liquid-like cases, the phase-shifted fit by −9 to −59 Hz (≤2 % of Γ), the symmetric fit by −96 to −833 Hz; (iv) the residual of the phase-shifted fit scales as $\approx -0.34\,\Gamma\,(R_{17}/R_1)$ at $\phi_b = -20^\circ$: −344 Hz at $R_1 = R_{17}$ and −12 Hz at 1.6 kΩ for Γ = 1 kHz, so for air-like cases (Γ = 65–190 Hz, $R_1$ = 36–204 Ω) −12 to −39 Hz, a third to a half of the argmax bias for $R_1/R_{17} \ge 1.8$ and three quarters or more at $R_1/R_{17}$ = 0.7; (v) with a fold, δ is removed and does not move $f_\mathrm{res}$ or Γ (≤0.5 Hz for δ = −3…+7°); (vi) without a fold, ±5° of δ enters the fitted angle almost one to one and moves $f_\mathrm{res}$ by ≤11 Hz (15 Hz where a spurious fold is declared) and Γ by ≤7 Hz; (vii) ±5 % on the magnitude slope moves $f_\mathrm{res}$ by ≤17 Hz and Γ by ≤1 %, but $R_m = 1/G_\mathrm{max}$ by 6–16 %, and even with an ideal magnitude channel $R_m$ is 24–39 % low in liquid; (viii) the firmware carry-over moves $f_\mathrm{res}$ by ≈2 Hz; (ix) the smoothing widens a 65 Hz half-bandwidth by 6.5 Hz (+10 %) and a 190 Hz one by 3.5 Hz, negligible in liquid.

The repository's two-channel forward model, which fits a BVD crystal through the divider and the detector laws to $V_\mathrm{MAG}$ and $V_\mathrm{PHS}$ jointly with a board phase inside the modulus, gives $\phi_b = -7.6, -13.8, -19.9, -22.1, -20.4^\circ$ in air on board 1920, equal to the P angle within 0.4–0.8° on $n = 1$–7. The short and 50 Ω standards measured on the same front end (1–51 MHz) give phase slopes of 0.27–0.40° MHz⁻¹ (0.74–1.10 ns), i.e. 1.4–2.0° at 5 MHz and 12–18° at 45 MHz, and read $M$ 4–16 % low (8–14 % at 5 MHz); the fitted angle grows roughly as $f^{0.55}$ (Fig. S11). A least-squares decomposition $\varphi = \varphi_0 - 360^\circ f\tau$ gives $\varphi_0 = -7.0^\circ$, τ = 1.28 ns (rms 1.2°) for board 1920 in air and $\varphi_0 = -8.2^\circ$, τ = 1.31 ns (rms 2.6°) for the second instrument, an approximation whose parameters move when $n = 1$ is excluded.

![Fig. S5. Forward model. Left: error of three estimators against $R_1/R_{17}$ for a board phase of −20° on the transfer function (Γ = 1 kHz). Right: error in units of Γ against the board phase for four measured-like cases; solid: phase-shifted fit; dotted: maximum of $G$.](../figures_v2/si/fig10_forward_model.png)

# S7. Firmware carry-over

Firmware versions up to 0.1.5c did not reset the per-point sums, so each printed point carried 1/500 of the previous one (+0.2 % on the counts). The recursion is exact and was undone offline on the counts ($m_i = v_i - v_{i-1}/500$). On DS-2 it changes $f_\mathrm{res}$ by ≤2.2 Hz and Γ by ≤1.7 Hz on 43 of 45 sweeps with P and φ by ≤0.2°; the exceptions are the threshold sweep of S3, whose fold decision flips ($f_\mathrm{res}$ +37 Hz with P, +111 Hz with A; φ +4.3°), and one water sweep at $n$ = 9 (+10 Hz on $f_\mathrm{res}$, −18 Hz on Γ). With A the changes are larger (≤2 Hz on 21 of 45 sweeps, up to 111 Hz). On DS-3 it changes $f_\mathrm{res}$ by ≤2 Hz (P; ≤6 Hz with A), Γ by ≤2 Hz and φ by ≤0.2°. Over the 120 sweeps the fit moves by ≤2 Hz on 115 and by ≤4 Hz on 118. The A and P ranges of Table 2 move by ≤2 percentage points (the M rows by up to 3.4) (corrected variant: DS-2 P $\epsilon_f$ = −1.6…+7.8 %, $\epsilon_\Gamma$ = −4.3…+7.3 %; DS-3 P +6.0…+13.0 %, −4.4…+4.6 %); the bias law gives +14 ± 30 Hz on 120 sweeps. Fig. S6 shows the differences on the shifts.

![Fig. S6. Difference of the air-to-liquid shifts between the firmware-corrected and the as-acquired variants, both datasets, estimators A and P.](../figures_v2/si/figS_firmware_correction.png)

# S8. The raw-magnitude baseline and the production datalogs

**Magnitude-only estimator from the sweeps (M).** Maximum of the divider ratio in dB on the same grid and its −3 dB full width where it exists (Table S3 and Fig. S7): $\epsilon_f$ = +52…+92 % (DS-2) and +50…+116 % (DS-3) on $n$ = 3–9, growing with the overtone; the width is undefined inside the window for $n \ge 7$ in liquid and reaches 6 kHz at $n$ = 5. **Production datalog of board 1920** (same instants as the impedance datalog, Fig. S8): maximum of the baseline-corrected magnitude and its −0.3 dB width; on the last 10 min of each plateau of 2026-09-11 (95 of 486 rows were exact duplicates written in bursts and were dropped) $\epsilon_f$ = +51, +69, +76, +89 % (water, $n$ = 3–9) and +57, +74, +85, +90 % (isopropanol), against +23, +29, +22, +18 % and +22, +27, +22, +22 % for the live A estimator; the −0.3 dB width changes by 0.8–3.7 kHz (water) and 1.1–6.4 kHz (isopropanol) where the theory's ΔΓ is 1.2–2.7 kHz. The 2026-09-10 run (2.5 min plateaus, 36 of 175 rows duplicated) gives +51…+98 % and +22…+30 %. The live A estimator reproduces the offline analysis of the dumped sweeps within the plateau drift (Table S11).

![Fig. S7. Error metrics on overtones 3–9 for six estimators on both datasets: $\epsilon_f$, $\epsilon_\Gamma$ (water and isopropanol) and $r_n$ (all liquids).](../figures_v2/si/figS_estimator_errors.png)

![Fig. S8. The run of 2026-09-11 as logged by the instrument: the impedance chain (left; A live) and the production magnitude chain at the same instants (right); overtone-normalised frequency relative to the air plateau, dissipation factor, and the production −0.3 dB width.](../figures_v2/si/figS_datalogs_0911.png)

# S9. Glucose series: concentration lines, the 5 % offset, the fit window

Relative to water, the fitted resonance moves by −72 Hz (fundamental) to −307 Hz (9th) at 10 % w/v (−17 to −128 Hz at 5 %) and broadens by +94 to +379 Hz at 10 %; lines through the four concentrations have slopes −7.1, −13.8, −17.8, −24.7, −30.4 Hz per % w/v in $\Delta f_n$ and +9.2, +13.1, +16.6, +28.0, +37.8 Hz per % in $\Delta\Gamma_n$ (Fig. S9). The 5 % plateau is less loaded than the line on every overtone: +10 to +18 Hz in Δf and −9 to −14 Hz in ΔΓ, constant in hertz over $n$ rather than ∝ √n, so not an error of ρη. Drift cannot explain it: the slope of $f_\mathrm{res}$ over the three replicas is ≤0.4 Hz/min inside the glucose plateaus and −0.2 to −1.0 Hz/min in water, the 5 % plateau is 4.3 min off the line of plateau times against concentration, so a time-linear drift maps into at most ≈4 Hz, and explaining the residual by drift alone would need −2 to −4 Hz/min, three to sixteen times what is measured (`results/glucose_tables_asis.md`). Without a return to water between concentrations the experiment cannot tell a property of the first solution from a step of the instrument. The ratio $\rho\eta/(\rho\eta)_w$ from the bandwidth exceeds that from the frequency on $n$ = 7 and 9 (1.36 and 1.42 against 1.27 and 1.30 at 10 %); the ±3Γ fit window is clipped by the sweep edge there (2.5–2.6 Γ on the right at $n$ = 9), and refitting with a symmetric window limited by the edge moves the $n$ = 9 ratio from 1.418 to 1.395, a fifth of the gap, and nothing at $n$ = 7; the rest is unexplained. A roughness term, which in the Daikhin–Urbakh description adds to Δf without a counterpart in ΔΓ [@DaikhinUrbakh1996; @DaikhinUrbakh1997], would act in the opposite direction and is not supported.

![Fig. S9. Shifts relative to water of the fitted resonance frequency, half-bandwidth and dissipation against glucose concentration, one line per overtone (least squares with intercept).](../figures_v2/si/figS_glucose_lines.png)

![Fig. S10. The half-height width against the fitted Γ: rotation widens it (air, above the identity), the baseline on the skirt narrows it (liquid, below).](../figures_v2/si/figS_halfheight_width.png)

![Fig. S11. The rotation angle against frequency for air and water on both instruments, with the phase of a pure delay for the two delays measured on the resistive standards of board 1920.](../figures_v2/si/figS_phi_vs_frequency.png)

![Fig. S12. KG-2 on log–log axes: $-\Delta f_n/n$ and $\Delta\Gamma_n/n$ against $n$ for A and P with the fitted slopes on $n$ = 3–9 and the KG line of slope −1/2.](../figures_v2/si/figS_kg2_loglog.png)

# S10. Tables

**Table S1.** Resonance frequency, half-bandwidth, dissipation and rotation angle per dataset, medium and overtone (mean ± sd of three sweeps). A = maximum of $G$ + half height; P = phase-shifted Lorentzian; fold = number of sweeps on which the phase reading folds.

{{TABLE:phases}}

**Table S2.** Air-to-liquid shifts for A and P, all datasets and liquids, with the three tests. $\epsilon$ only where ρη is tabulated (water, isopropanol).

{{TABLE:shifts_main}}

**Table S3.** The same for the other estimators: M (magnitude maximum, Γ = half of the −3 dB width where defined), MP (midpoint of the half-height crossings), S (symmetric Lorentzian, constant background), S+ (symmetric + linear background), C (BVD admittance circle of the repository).

{{TABLE:shifts_other}}

**Table S4.** Summary on overtones 3–9 (range over $n$; over water and isopropanol for $\epsilon$; over all liquids for $r_n$), every estimator and dataset.

{{TABLE:summary}}

**Table S5.** KG-2: log–log slopes, √n slopes through the origin and coefficients of variation of the √n-normalised shifts, A and P, fits on $n$ = 1–9 and 3–9.

{{TABLE:kg2}}

**Table S6.** Experiment 1 reproducibility: the air → water step of DS-2 and DS-3 (A and P) and the live A estimator of board 1920 on two days.

{{TABLE:rep}}

**Table S7.** The '8 %' claim per overtone: P and A against KG.

{{TABLE:claim}}

**Table S8.** Bias of the conductance maximum and of the half-height width per dataset, medium and overtone (mean of three sweeps).

{{TABLE:bias}}

**Table S9.** The rotation angle: every dataset and medium; stability per overtone; between boards and days; monotonicity.

{{TABLE:phi}}

**Table S10.** Glucose: data-derived relative $\sqrt{\rho\eta}$, its dependence on concentration, steps between concentrations in units of the replica scatter, and the resolution.

{{TABLE:glucose}}

**Table S11.** Live datalogs of board 1920 (A as published by the instrument): plateau shifts against KG.

{{TABLE:datalog}}

# S11. Remaining experiments before submission

1. Reference impedance analyser on the same crystal, same day, air and water (thru configuration): absolute $f_\mathrm{res}$, Γ, $R_m$, and the reference's own φ (expected ≈ 0).
2. A dedicated air → water acquisition with raw sweeps on both instruments, with the liquid temperature logged at the interface, repeated on two days: the reproducibility of Experiment 1 without the confounding of a board and crystal change.
3. Two boards × two sensors in air and water, overtones 1–9: is φ(n) a board constant, and does the fundamental excess follow the sensor or the board.
4. Liquid temperature measured, or a water–glycerol series at controlled temperature with tabulated ρη: the absolute KG-3 test over a range, and the absolute ρη of the glucose solutions (literature values at 25 °C to be adopted and cited).
5. Bench calibration of the phase channel: a known phase ramp through 0° (δ and the fold rounding) and an RLC standard in the operating range (0.5–5 kΩ) for $\phi_b(f)$.
6. Long plateau (≥ 1 h) in water with the fit running live beside the conductance maximum: drift, noise, fallback rate, and the two-state behaviour of the 3rd overtone.
7. Larger or switchable divider resistor (0.5–1 kΩ) for liquids: the out-of-roundness and the residual frequency excess against the AD8302 operating point.
8. Sweep window scaled with Γ (±6 Γ): removes the clipping of the fit window and the baseline-on-skirt bias.
9. Re-acquisition with firmware 0.1.5d (no carry-over) and, for the concentration series, a return to water between solutions and a repeated 5 % point.
10. A third liquid (20–40 % glycerol) and a viscoelastic film: the estimator where $r_n \ne 1$ is expected.
