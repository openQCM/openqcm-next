# Derivations of the measurement equations

*Companion to the manuscript. Every equation here was re-derived independently of the repository documentation and checked numerically with `paper/analysis/qcmchain.py` (the §11 reference sweep and the 45 sweeps of 2026-09-11; see `paper/notes/running_list.md` for the checks and for the one discrepancy found).*

Notation: $j$ imaginary unit, $f$ excitation frequency, $\omega = 2\pi f$. $Z_q = R_q + jX_q$ quartz impedance, $Y_q = 1/Z_q = G + jB$. $R_{17} = 52.3\ \Omega$. $\Delta = f_\mathrm{res} - f$. $\Gamma$ = half bandwidth at half height (HWHM). $D = 2\Gamma/f_\mathrm{res}$.

## 1. The measuring divider

The sensor is the series element of a divider loaded by $R_{17}$ to ground; the AD8302 compares the node voltage $V_A$ (across $R_{17}$) with the drive $V_\mathrm{in}$, the latter through a resistive attenuator $K = (R_{11}+R_{19})/R_{19} = (47.0+4.99)/4.99 = 10.4188$ (20.356 dB):

$$H(f) = \frac{V_A}{V_\mathrm{in}} = \frac{R_{17}}{Z_q(f) + R_{17}}, \qquad \frac{V_\mathrm{INPA}}{V_\mathrm{INPB}} = K\,H(f).$$

## 2. The AD8302 laws (data sheet Rev. B, eqs. 8a and 9)

$$V_\mathrm{MAG} = V_\mathrm{CP} + V_\mathrm{SLP}\,\log_{10}\frac{|V_\mathrm{INPA}|}{|V_\mathrm{INPB}|},\quad V_\mathrm{SLP} = 0.600\ \mathrm{V/decade} = 30\ \mathrm{mV/dB},\ V_\mathrm{CP} = 0.900\ \mathrm{V}$$

$$V_\mathrm{PHS} = V_\mathrm{CP} - V_\Phi\left(\left|\angle V_\mathrm{INPA} - \angle V_\mathrm{INPB}\right| - 90^\circ\right),\quad V_\Phi = 10\ \mathrm{mV}/^\circ ,$$

so $V_\mathrm{PHS} = 1.8\ \mathrm{V}$ at $|\Delta\phi| = 0$ and $0.9\ \mathrm{V}$ at $90^\circ$. The data sheet specifies slopes of 29 mV/dB and 10 mV/° (typical, linear regression) and the detector output is the *modulus* of the phase difference: the sign is not available. The output stages on the board add gains of 2 (magnitude) and 1.5 (phase) before a 12-bit ADC with 3.3 V reference; the host converts counts to volts with those factors and removes the attenuator from $V_\mathrm{MAG}$:

$$V_\mathrm{MAG} \leftarrow \frac{\mathrm{counts}\cdot 3.3/4096}{2} - 20\log_{10}(K)\cdot 0.030 = \ldots - 0.610692\ \mathrm{V}.$$

The 0.3564 dB difference between $20\log_{10}K$ and 20 dB matters: it is 4 % on $M$ below and up to 22 % on $R_m$ in air (verified by substitution in §3).

## 3. Exact inversion

With $K$ removed, $V_\mathrm{MAG} = V_\mathrm{CP} + 0.6\log_{10}|H|$, and $1/|H| = |Z_q+R_{17}|/R_{17}$:

$$M \equiv |Z_q + R_{17}| = R_{17}\,10^{(V_\mathrm{CP} - V_\mathrm{MAG})/0.6}.$$

The phase of the divider is $\angle H = -\angle(Z_q + R_{17})$. Writing $\phi = -\angle H$ (the signed phase of $Z_q+R_{17}$... with the sign convention that $Z_q + R_{17} = M e^{-j\phi}$, i.e. $\phi = \angle H$),

$$R_q = M\cos\phi - R_{17},\qquad X_q = -M\sin\phi,$$

$$G = \frac{R_q}{R_q^2 + X_q^2} = \frac{M\cos\phi - R_{17}}{(M\cos\phi - R_{17})^2 + M^2\sin^2\phi},\qquad B = \frac{-X_q}{R_q^2+X_q^2} = \frac{M\sin\phi}{(M\cos\phi - R_{17})^2 + M^2\sin^2\phi}.$$

Checks: a short ($Z_q = 0$) gives $M = R_{17}$, $\phi = 0$, $R_q = 0$; an open gives $M\to\infty$, $\phi \to$ the phase of the stray capacitance. The closed form for $G$ in the repository is this expression; it was verified against a direct complex evaluation to machine precision.

**Sensitivity.** Near the series resonance of a lightly damped crystal $X_q \to 0$ and $M \to R_m + R_{17}$: $R_q$ is a difference of close numbers. $\partial R_q/\partial V_\mathrm{MAG} = -M\ln(10)/0.6 \approx -3.84\,M$ V$^{-1}$, so with $R_m = 12\ \Omega$ a 1 mV error on $V_\mathrm{MAG}$ moves $R_m$ by $3.84\times 64\ \Omega\times 10^{-3} \approx 0.25\ \Omega \approx 2\%$. A multiplicative error $k$ on $M$ changes $R_m$ by $(k-1)(1 + R_{17}/R_m)$: the amplification factor $(1+R_{17}/R_m)$ is 2.5 for $R_m = 36\ \Omega$ (air, fundamental) and 1.04 for $R_m = 1.2\ \mathrm{k}\Omega$ (liquid).

## 4. Why conductance is even in the sign of the phase and not in its offset

$G$ depends on $\phi$ only through $\cos\phi$ and $\sin^2\phi$: $G(-\phi) = G(\phi)$. $B$ depends on $\sin\phi$: $B(-\phi) = -B(\phi)$. Hence the unsigned detector reading is sufficient for $G$ and, through $G$, for $f_\mathrm{res}$ and $\Gamma$; the sign is needed only for $B$ (the locus). An additive error $\delta$ on the phase is not removed by the evenness: $G(\phi + \delta) \ne G(\phi)$; to first order $\partial G/\partial\phi = -\sin\phi\,(R_q^2 - X_q^2 + \ldots)$, which at resonance ($X_q \approx 0$, $\phi \approx 0$) vanishes, so a small offset affects $G$ mostly on the flanks and distorts the peak shape rather than its position (cf. the forward model, block B/C: $\pm5^\circ$ of uncorrected $\delta$ moves the PSL $f_\mathrm{res}$ by $\le 10$ Hz in liquid).

## 5. The phase reading: fold, offset, board phase

The detector returns $|\cdot|$ of a phase that, around the series resonance of a lightly damped crystal, crosses zero (inductive below $f_s$... for the divider phase, $\angle H$ passes through 0 when $X_q + \mathrm{Im}(\ldots) = 0$). The instrument model (repository, confirmed by the forward model here) is

$$r(f) = |\phi(f) + \phi_b| - \delta,$$

with $\phi_b$ a board/cable phase *inside* the modulus and $\delta$ a voltage offset of the phase channel *outside* it. Where the argument crosses zero, $r$ has a V-shaped minimum with $\min r = -\delta$: the offset is measured by the fold, not fitted. When the crystal is damped (liquid, $n \ge 3$ here) the argument never reaches zero, the reading has a smooth minimum tens of degrees above zero, there is no fold, $\delta$ is not identifiable from the sweep, and the reading is used as the signed phase (with $\phi_b - \delta$ left in it: this is what the rotation angle of §7 absorbs; forward model block C gives $\varphi_\mathrm{fit} \approx \phi_b - \delta$ to within 0.3°).

The fold decision of the instrument (depth of the reading's peak ≥ 0.88 of the way from its baseline to 0°, peak within 5 Γ of the conductance maximum) is a heuristic calibrated on this board's data. Two facts about it from this work: (i) one of the 45 sweeps (water, n = 3, replica 3) sits exactly on the threshold (depth 0.880), and the 0.2 % firmware carry-over correction flips its decision, moving the PSL $f_\mathrm{res}$ by 37 Hz and $\varphi$ by 4.3°; (ii) on synthetic data the instrument's smoothing (Savitzky–Golay 51/3 + spline) rounds the V and biases the recovered $\delta$ by $-1.0$ to $-2.3^\circ$ (narrow folds, air), which does not move $f_\mathrm{res}$ or $\Gamma$ when a fold exists (block B) but means the logged $\delta$ is not the detector offset to better than ~2°.

## 6. Kanazawa–Gordon with a consistent overtone convention

Small-load approximation (Johannsmann): $\Delta\tilde f_n / f_F = \dfrac{j}{\pi Z_q}\tilde Z_L(\omega_n)$, with $f_F$ the **fundamental** frequency, $Z_q = \sqrt{\rho_q\mu_q} = 8.84\times10^6$ kg m$^{-2}$ s$^{-1}$ ($\rho_q = 2648$ kg/m³, $\mu_q = 2.947\times10^{10}$ Pa). For a Newtonian semi-infinite liquid $\tilde Z_L = \sqrt{j\omega_n\rho\eta} = \sqrt{\omega_n\rho\eta/2}\,(1+j)$, so

$$\Delta f_n = -\sqrt{n}\, f_F^{3/2}\sqrt{\frac{\rho\eta}{\pi\rho_q\mu_q}},\qquad \Delta\Gamma_n = -\Delta f_n,\qquad \frac{\Delta f_n}{n} = -\frac{1}{\sqrt n}f_F^{3/2}\sqrt{\frac{\rho\eta}{\pi\rho_q\mu_q}}.$$

Sanity check against Sauerbrey: with $\tilde Z_L = j\omega_n m_f$ the same formula returns $\Delta f_n = -2nf_F^2 m_f/Z_q$. Consistency of the convention: $\Delta f_n \propto \sqrt n$ (so $\Delta f_n/n \propto 1/\sqrt n$); $\Delta D_n = 2\Delta\Gamma_n/(nf_F)$ carries the overtone scaling through $f_n$ and is not divided by $n$ again: $\Delta\Gamma_n/n = (f_F/2)\Delta D_n$. Values at 25 °C with $f_F = 5.0046$ MHz: water ($\rho = 997.05$ kg/m³, $\eta = 0.890$ mPa s) 673.6 Hz $\cdot\sqrt n$; isopropanol ($\rho = 781.0$ kg/m³, $\eta = 2.038$ mPa s) 901.5 Hz $\cdot\sqrt n$. The Newtonian prediction $|\Delta f_n|/\Delta\Gamma_n = 1$ is independent of $\rho\eta$ and of temperature; it is the cleanest test.

Temperature sensitivity (liquid properties): $\partial\ln\sqrt{\rho\eta}/\partial T \approx -1.1\ \%/\mathrm K$ for water near 25 °C ($\eta$: 0.932 → 0.851 mPa s from 23 to 27 °C) and $\approx -1.5\ \%/\mathrm K$ for isopropanol ($\eta \approx 2.37, 2.04, 1.77$ mPa s at 20, 25, 30 °C, literature values that scatter by a few %). The liquid temperature was not measured; the crystal was held at 25.00 °C by the TEC. A $\pm 2$ K uncertainty on the liquid is $\pm 2$–3 % on the predicted shifts.

## 7. The phase-shifted (rotated) Lorentzian and the biases of the simple estimators

Near a resonance the motional admittance is $Y_m \propto 1/(\Gamma - j\Delta)$ (Johannsmann eq. 9–10, $\Delta = f_\mathrm{res} - f$). A calibration error that multiplies the admittance by $e^{j\varphi}$ gives

$$Y = \frac{A e^{j\varphi}}{\Gamma - j\Delta} + Y_\mathrm{off},\qquad G = A\,\frac{\Gamma\cos\varphi - \Delta\sin\varphi}{\Delta^2 + \Gamma^2} + G_\mathrm{off},\qquad B = A\,\frac{\Gamma\sin\varphi + \Delta\cos\varphi}{\Delta^2+\Gamma^2} + B_\mathrm{off},$$

with $A = G_\mathrm{max}\Gamma$ in the repository's notation. Johannsmann et al. (Sensors 2021, eq. 13) print $+\Delta\sin\varphi$ in $G$ and $+\Delta\cos\varphi$ in $B$: with the same $\varphi$ in both lines that is not one rotation (the two lines correspond to $\varphi$ and $-\varphi$); the repository noticed this and uses the rotation form above, reporting $\varphi$ with the rotation's sign (negative on board 1920). Fitting $G$ alone with $\varphi \to -\varphi$ is observationally identical, so the convention only affects the sign quoted for $\varphi$.

**Maximum of G.** $dG/d\Delta = 0 \iff \sin\varphi\,\Delta^2 - 2\Gamma\cos\varphi\,\Delta - \Gamma^2\sin\varphi = 0 \iff \Delta = \Gamma(\cos\varphi \pm 1)/\sin\varphi$. The maximum is $\Delta_\mathrm{max} = \Gamma(\cos\varphi - 1)/\sin\varphi = -\Gamma\tan(\varphi/2)$, hence

$$f_{G\max} = f_\mathrm{res} + \Gamma\tan(\varphi/2).$$

With $\varphi < 0$ the maximum sits *below* $f_\mathrm{res}$, by 0.07 Γ at −8° and 0.25 Γ at −28°. The peak value is $G_\mathrm{peak} - G_\mathrm{off} = (A/\Gamma)\cos^2(\varphi/2)$ and the curve has a negative lobe $-(A/\Gamma)\sin^2(\varphi/2)$ at $\Delta = \Gamma/\tan(\varphi/2)$; the latter means a far-off-resonance "baseline" is not $G_\mathrm{off}$ on the side of the lobe.

**Half-height crossings** (level $G_\mathrm{off} + (G_\mathrm{peak}-G_\mathrm{off})/2$; $c = \cos^2(\varphi/2)$):

$$c\,\Delta^2 + 2\Gamma\sin\varphi\,\Delta + \Gamma^2(c - 2\cos\varphi) = 0 \ \Rightarrow\ \Delta_\pm = \frac{\Gamma\left[-\sin\varphi \pm \sqrt{c(2-c)}\right]}{c},$$

$$\Gamma_\mathrm{hh} = \frac{\Delta_+ - \Delta_-}{2} = \Gamma\sqrt{\frac{2-c}{c}} = \Gamma\sqrt{1 + 2\tan^2(\varphi/2)},\qquad f_\mathrm{mid} = f_\mathrm{res} + 2\Gamma\tan(\varphi/2).$$

So the half-height width *over*-estimates Γ by 0.5 % (−8°) to 6 % (−28°), and the midpoint of the crossings is biased *twice* as much as the maximum, in the same direction. Verified numerically to the 1 Hz grid (`results/closed_forms_check.csv`). On the real data the half-height width comes out *below* the fitted Γ in liquid (ratio 0.93–0.99) because the instrument's baseline (mean of the first 100 samples of a window sized for air) sits on the skirt of the broadened peak and raises the half level (baseline = 13–74 % of the peak on n ≥ 3 in liquid); the two biases have opposite signs and are both documented in `results/bias_theory.md`.

**Symmetric Lorentzian.** Fitting $G_\mathrm{sym} = G_\mathrm{max}\Gamma^2/(\Delta^2+\Gamma^2) + c$ (+ $b\Delta$) to a rotated Lorentzian has no closed form; numerically (noise-free, ±3 Γ_hh window) the 4-parameter fit is biased by 1.3–2.1 Γ tan(φ/2) in $f$ and over-estimates Γ by 2–35 % (−8° to −28°); with a linear background the Γ is right to 0.2 % but $f$ is still biased by ≈1.25 Γ tan(φ/2). The dispersive term $-\Delta\sin\varphi/(\Delta^2+\Gamma^2)$ is antisymmetric about $f_\mathrm{res}$ and is what a linear background partly, and a constant background not at all, absorbs.

## 8. Is the rotation exact for this front end? (what the forward model shows)

A board/cable phase enters the *measured transfer function*, not the admittance: $H_\mathrm{meas} = H e^{j\phi_b}$. Inverting exactly with that phase gives $Z' + R_{17} = (Z_q + R_{17})e^{-j\phi_b}$, i.e.

$$Y' = \frac{1}{(Z_q + R_{17})e^{-j\phi_b} - R_{17}},$$

a Möbius transformation of $Y_q$, which maps circles to circles but is a pure rotation $Y' \approx Y_q e^{j\phi_b}$ only when $|Z_q| \gg R_{17}$. In liquid ($R_m = 0.6$–$1.4$ kΩ, $R_m/R_{17} = 12$–24) the rotated Lorentzian is therefore an excellent model and the fitted $\varphi$ equals $\phi_b$ (block A: to 0.5°); in air ($R_m/R_{17} = 0.7$–4) it is approximate. The residual bias of the PSL under a board phase on $H$ (block E, Γ = 1 kHz, $\phi_b = -20^\circ$) scales as $\approx -0.34\,\Gamma\,(R_{17}/R_1)$ Hz: $-344$ Hz at $R_1 = R_{17}$, $-12$ Hz at 1.6 kΩ, against $-532$/$-199$ Hz for the maximum of G. For the air-like cases (Γ = 65–190 Hz) the PSL residual is $-12$ to $-39$ Hz, 1/3 to 1/2 of the argmax bias there. This is the limit of validity of the method: the rotated Lorentzian corrects the first-order effect of an uncalibrated phase, exactly in the high-impedance (liquid) regime and only partially when the sensor's motional resistance is comparable to the divider resistor.
