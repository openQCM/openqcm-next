## A1 — the bias of argmax against the fit, all 45 sweeps

For the rotated Lorentzian the maximum of G sits at f_argmax = f_res + Γ·tan(φ/2) (derivative of Re Y set to zero). Measured against predicted:

| set | n | Γ [Hz] | φ [°] | argmax − f_res measured [Hz] | Γ·tan(φ/2) predicted [Hz] | difference [Hz] | difference / Γ |
|---|---|---|---|---|---|---|---|
| air_0 | 1 | 66 | -7.9 | +2 | -5 | +6 | +0.096 |
| air_0 | 3 | 76 | -14.5 | -2 | -10 | +8 | +0.105 |
| air_0 | 5 | 103 | -20.6 | -11 | -19 | +8 | +0.073 |
| air_0 | 7 | 145 | -22.9 | -26 | -29 | +3 | +0.022 |
| air_0 | 9 | 190 | -26.8 | -47 | -45 | -2 | -0.011 |
| air_1 | 1 | 65 | -8.0 | +3 | -5 | +8 | +0.122 |
| air_1 | 3 | 76 | -14.5 | -2 | -10 | +8 | +0.104 |
| air_1 | 5 | 102 | -20.7 | -11 | -19 | +7 | +0.072 |
| air_1 | 7 | 149 | -22.8 | -30 | -30 | -0 | -0.000 |
| air_1 | 9 | 188 | -26.8 | -46 | -45 | -1 | -0.006 |
| air_2 | 1 | 66 | -8.0 | +3 | -5 | +7 | +0.113 |
| air_2 | 3 | 76 | -14.5 | -2 | -10 | +8 | +0.100 |
| air_2 | 5 | 102 | -20.5 | -11 | -19 | +8 | +0.074 |
| air_2 | 7 | 149 | -22.9 | -27 | -30 | +3 | +0.020 |
| air_2 | 9 | 188 | -26.8 | -47 | -45 | -2 | -0.009 |
| wat_0 | 1 | 939 | -5.1 | -81 | -41 | -40 | -0.042 |
| wat_0 | 3 | 1330 | -13.6 | -165 | -159 | -7 | -0.005 |
| wat_0 | 5 | 1647 | -23.9 | -362 | -349 | -13 | -0.008 |
| wat_0 | 7 | 1874 | -22.5 | -349 | -373 | +24 | +0.013 |
| wat_0 | 9 | 2136 | -27.7 | -471 | -526 | +55 | +0.026 |
| wat_1 | 1 | 934 | -5.0 | -85 | -41 | -44 | -0.048 |
| wat_1 | 3 | 1329 | -13.6 | -173 | -159 | -15 | -0.011 |
| wat_1 | 5 | 1646 | -24.0 | -335 | -349 | +14 | +0.009 |
| wat_1 | 7 | 1868 | -22.5 | -346 | -372 | +27 | +0.014 |
| wat_1 | 9 | 2135 | -27.9 | -485 | -531 | +46 | +0.022 |
| wat_2 | 1 | 931 | -5.0 | -82 | -41 | -41 | -0.044 |
| wat_2 | 3 | 1395 | -17.9 | -233 | -219 | -14 | -0.010 |
| wat_2 | 5 | 1644 | -24.0 | -356 | -349 | -7 | -0.004 |
| wat_2 | 7 | 1873 | -22.5 | -347 | -372 | +25 | +0.013 |
| wat_2 | 9 | 2119 | -28.1 | -454 | -531 | +77 | +0.036 |
| ipa_0 | 1 | 1296 | -5.0 | -101 | -57 | -44 | -0.034 |
| ipa_0 | 3 | 1718 | -14.3 | -230 | -216 | -14 | -0.008 |
| ipa_0 | 5 | 2172 | -24.6 | -512 | -474 | -37 | -0.017 |
| ipa_0 | 7 | 2571 | -21.3 | -444 | -485 | +41 | +0.016 |
| ipa_0 | 9 | 2920 | -27.2 | -698 | -707 | +9 | +0.003 |
| ipa_1 | 1 | 1297 | -5.0 | -101 | -56 | -44 | -0.034 |
| ipa_1 | 3 | 1720 | -14.4 | -231 | -217 | -14 | -0.008 |
| ipa_1 | 5 | 2176 | -24.6 | -511 | -474 | -36 | -0.017 |
| ipa_1 | 7 | 2567 | -21.3 | -447 | -484 | +37 | +0.014 |
| ipa_1 | 9 | 2918 | -27.2 | -701 | -705 | +4 | +0.002 |
| ipa_2 | 1 | 1297 | -5.0 | -100 | -56 | -44 | -0.034 |
| ipa_2 | 3 | 1718 | -14.0 | -228 | -212 | -16 | -0.010 |
| ipa_2 | 5 | 2153 | -24.9 | -494 | -475 | -19 | -0.009 |
| ipa_2 | 7 | 2571 | -21.5 | -453 | -489 | +36 | +0.014 |
| ipa_2 | 9 | 2939 | -27.3 | -679 | -713 | +34 | +0.011 |

Over the 45 sweeps: difference measured − predicted, mean +1 Hz, sd 28 Hz, max |.| 77 Hz; in units of Γ mean +0.016, max 0.122. The half-height Γ and the 1 Hz grid enter the measured value; the fitted Γ and φ the predicted one.

## A2 — independence from the smoothing

The fit on G built from the raw samples (no Savitzky–Golay, no spline), from SG 11/3 + spline, and from the chain's SG 51/3 + spline. Middle replicas.

| set | n | f_res: raw / SG 11 / SG 51 [Hz, from chain's argmax] | Γ: raw / SG 11 / SG 51 [Hz] | φ: raw / SG 11 / SG 51 [°] | rms G raw / SG 11 / SG 51 [%] |
|---|---|---|---|---|---|
| air_1 | 1 | -4 / -3 / -3 | 66 / 65 / 65 | -8.0 / -8.0 / -8.0 | 2.57 / 2.57 / 2.64 |
| air_1 | 3 | +2 / +2 / +2 | 76 / 76 / 76 | -14.5 / -14.5 / -14.5 | 1.53 / 1.54 / 1.59 |
| air_1 | 5 | +11 / +11 / +11 | 101 / 101 / 102 | -20.7 / -20.7 / -20.7 | 1.13 / 1.14 / 1.20 |
| air_1 | 7 | +30 / +30 / +30 | 148 / 148 / 149 | -22.9 / -22.9 / -22.8 | 0.94 / 0.95 / 0.99 |
| air_1 | 9 | +46 / +46 / +46 | 187 / 188 / 188 | -26.8 / -26.8 / -26.8 | 1.20 / 1.22 / 1.24 |
| wat_1 | 1 | +86 / +85 / +85 | 933 / 934 / 934 | -5.0 / -5.0 / -5.0 | 0.47 / 0.46 / 0.46 |
| wat_1 | 3 | +173 / +173 / +173 | 1329 / 1329 / 1329 | -13.6 / -13.6 / -13.6 | 0.32 / 0.29 / 0.29 |
| wat_1 | 5 | +333 / +334 / +335 | 1647 / 1646 / 1646 | -23.9 / -23.9 / -24.0 | 0.29 / 0.20 / 0.17 |
| wat_1 | 7 | +345 / +345 / +346 | 1862 / 1865 / 1868 | -22.5 / -22.5 / -22.5 | 0.52 / 0.41 / 0.37 |
| wat_1 | 9 | +488 / +486 / +485 | 2112 / 2132 / 2135 | -28.1 / -28.0 / -27.9 | 0.57 / 0.44 / 0.41 |
| ipa_1 | 1 | +101 / +101 / +101 | 1295 / 1296 / 1297 | -5.0 / -5.0 / -5.0 | 0.51 / 0.51 / 0.51 |
| ipa_1 | 3 | +231 / +231 / +231 | 1720 / 1720 / 1720 | -14.4 / -14.4 / -14.4 | 0.22 / 0.17 / 0.16 |
| ipa_1 | 5 | +512 / +511 / +511 | 2173 / 2174 / 2176 | -24.6 / -24.6 / -24.6 | 0.31 / 0.24 / 0.25 |
| ipa_1 | 7 | +449 / +447 / +447 | 2563 / 2567 / 2567 | -21.4 / -21.3 / -21.3 | 0.59 / 0.48 / 0.48 |
| ipa_1 | 9 | +696 / +704 / +701 | 2889 / 2910 / 2918 | -27.2 / -27.2 / -27.2 | 0.62 / 0.47 / 0.43 |

Raw minus chain over the 15 cases: f_res -5…+3 Hz, Γ -29…+1 Hz, φ -0.2…+0.1°.

## A3 — independence from the phase offset δ

The chain's phase shifted by −5°, 0, +5° before the inversion (on top of the chain's own δ), fit on G on the same window. Middle replicas.

| set | n | f_res shift for δ−5° / δ+5° [Hz] | Γ change [Hz] | φ change [°] | rms G [%] at −5 / 0 / +5 |
|---|---|---|---|---|---|
| air_1 | 1 | +2 / -1 | +10 / -7 | -0.0 / -0.0 | 3.74 / 2.64 / 1.95 |
| air_1 | 3 | +4 / -3 | +9 / -7 | -0.8 / +0.4 | 2.50 / 1.59 / 0.90 |
| air_1 | 5 | +4 / -3 | +10 / -8 | -0.5 / +0.2 | 1.82 / 1.20 / 0.71 |
| air_1 | 7 | +3 / -3 | +12 / -11 | -0.9 / +0.8 | 1.30 / 0.99 / 0.76 |
| air_1 | 9 | +5 / -4 | +12 / -11 | -2.0 / +1.9 | 1.41 / 1.24 / 1.14 |
| wat_1 | 1 | -4 / +2 | +62 / -56 | -0.6 / +0.7 | 0.60 / 0.46 / 0.37 |
| wat_1 | 3 | -18 / +14 | +37 / -37 | -2.3 / +2.5 | 0.33 / 0.29 / 0.27 |
| wat_1 | 5 | -8 / +7 | +13 / -14 | -3.7 / +3.8 | 0.17 / 0.17 / 0.18 |
| wat_1 | 7 | -4 / +4 | +4 / -3 | -4.2 / +4.2 | 0.35 / 0.37 / 0.39 |
| wat_1 | 9 | -6 / +3 | +21 / -20 | -4.3 / +4.3 | 0.41 / 0.41 / 0.41 |
| ipa_1 | 1 | -12 / +10 | +70 / -65 | -0.6 / +0.7 | 0.62 / 0.51 / 0.44 |
| ipa_1 | 3 | -21 / +17 | +35 / -35 | -2.6 / +2.7 | 0.16 / 0.16 / 0.18 |
| ipa_1 | 5 | -5 / +4 | +13 / -13 | -3.9 / +4.0 | 0.26 / 0.25 / 0.24 |
| ipa_1 | 7 | -16 / +15 | +6 / -7 | -4.0 / +3.9 | 0.48 / 0.48 / 0.49 |
| ipa_1 | 9 | -10 / +8 | +15 / -15 | -4.3 / +4.2 | 0.45 / 0.43 / 0.42 |

A ±5° offset moves f_res by at most 21 Hz and Γ by at most 70 Hz over the 15 cases; φ moves by -0.0…+4.3° per +5°.

## A4 — synthetic sweeps with known truth

A BVD motional branch Y_m = 1/(R1(1 + jx)), x = (f² − f_s²)/(f·2Γ), rotated by a known φ about the C0 offset (Y = e^{jφ}Y_m + jωC0), sent through the divider H = R17·Y/(1 + R17·Y) and the detector (V_MAG = 0.9 − 0.6·log10(M/R17), V_PHS = 1.8 − 0.01·(|arg H| − δ)), quantised on the ADC (3.3/4096 V, /2 and /1.5 op-amp gains) with 0.05° of noise, on the −12/+6 kHz window at 1 Hz; then the chain and both estimators. Truth in the first columns.

| case | f_s [Hz] | Γ [Hz] | R1 [Ω] | φ [°] | δ [°] | fold | argmax − f_s [Hz] | Γ half height − Γ [Hz] | fit f_res − f_s [Hz] | fit Γ − Γ [Hz] | fit φ [°] | predicted argmax bias Γ·tan(φ/2) [Hz] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| air-like n=5 | 24973700 | 105 | 94 | +0 | +6.4 | True | -3 | +5 | -0 | +4 | -0.3 | +0 |
| air-like n=5 | 24973700 | 105 | 94 | -21 | +6.4 | True | -15 | +8 | +2 | +4 | -21.2 | -19 |
| water-like n=5 | 24971700 | 1600 | 1800 | +0 | +0.0 | False | -2 | -24 | -1 | +4 | +0.0 | +0 |
| water-like n=5 | 24971700 | 1600 | 1800 | -24 | +0.0 | False | -331 | -53 | +0 | +0 | -24.0 | -340 |
| water-like n=9 | 44940700 | 2100 | 3250 | -28 | +0.0 | False | -552 | -119 | -4 | +5 | -27.9 | -524 |
| ipa-like n=3 | 14986800 | 1700 | 1800 | -14 | +0.0 | True | -214 | -66 | +0 | +2 | -14.3 | -209 |

With φ = 0 both estimators recover f_s to the grid; with the rotation the argmax is off by the predicted Γ·tan(φ/2) while the fit recovers f_s, Γ and φ. The chain's fold decision is exercised on the air-like cases (δ = 6.4°, the reading dips below zero).

## A6 — the fit's own uncertainty against the scatter of the three replicas

| phase | n | sd(f_res) from the covariance, mean of three [Hz] | sd(f_res) over the three replicas [Hz] | sd(Γ) covariance [Hz] | sd(Γ) replicas [Hz] | sd(φ) replicas [°] |
|---|---|---|---|---|---|---|
| air | 1 | 0.4 | 2.3 | 0.6 | 0.1 | 0.05 |
| air | 3 | 0.3 | 7.4 | 0.4 | 0.1 | 0.03 |
| air | 5 | 0.3 | 13.2 | 0.3 | 0.7 | 0.06 |
| air | 7 | 0.3 | 20.6 | 0.3 | 2.3 | 0.04 |
| air | 9 | 0.4 | 23.3 | 0.5 | 1.0 | 0.00 |
| water | 1 | 0.3 | 2.2 | 0.4 | 3.9 | 0.02 |
| water | 3 | 0.3 | 16.2 | 0.4 | 38.2 | 2.45 |
| water | 5 | 0.2 | 13.3 | 0.2 | 1.0 | 0.04 |
| water | 7 | 0.4 | 17.6 | 0.5 | 3.2 | 0.05 |
| water | 9 | 0.5 | 28.7 | 0.7 | 9.6 | 0.23 |
| ipa | 1 | 0.4 | 2.4 | 0.5 | 0.5 | 0.02 |
| ipa | 3 | 0.1 | 4.7 | 0.2 | 1.2 | 0.18 |
| ipa | 5 | 0.2 | 0.8 | 0.3 | 12.6 | 0.17 |
| ipa | 7 | 0.6 | 0.3 | 0.8 | 2.2 | 0.11 |
| ipa | 9 | 0.6 | 12.3 | 0.8 | 11.6 | 0.04 |

The covariance assumes independent residuals; the residual is structured (0.2–0.5 % of range, correlated over hundreds of hertz), so the replica scatter is the uncertainty to quote.

## A7 — model variants

Fit on G with a linear background added (7 parameters), and — where the ±3Γ window is clipped by the sweep on the right — a symmetric window limited to the distance to the edge. Middle replicas; differences from the reference fit.

| set | n | window clipped? | + linear background: Δf_res / ΔΓ / Δφ | symmetric window: half-width [Hz], Δf_res / ΔΓ / Δφ |
|---|---|---|---|---|
| air_1 | 1 | no | +8 / +1 / -11.5 | — |
| air_1 | 3 | no | +7 / +1 / -8.7 | — |
| air_1 | 5 | no | +8 / +2 / -7.0 | — |
| air_1 | 7 | no | +10 / +2 / -5.8 | — |
| air_1 | 9 | no | +13 / +3 / -6.3 | — |
| wat_1 | 1 | no | +0 / +0 / -0.0 | — |
| wat_1 | 3 | no | +4 / +1 / -0.3 | — |
| wat_1 | 5 | no | +2 / +0 / -0.1 | — |
| wat_1 | 7 | no | +19 / +5 / -1.0 | — |
| wat_1 | 9 | yes | +55 / +13 / -2.4 | 6042, +2 / -2 / -0.1 |
| ipa_1 | 1 | no | +15 / +0 / -1.1 | — |
| ipa_1 | 3 | no | +12 / +2 / -0.7 | — |
| ipa_1 | 5 | yes | -31 / -6 / +1.4 | 6000, -1 / +1 / +0.0 |
| ipa_1 | 7 | yes | +55 / -2 / -2.2 | 6004, +9 / -12 / -0.3 |
| ipa_1 | 9 | yes | +105 / -22 / -3.8 | 6003, +15 / -23 / -0.4 |

## A8 — φ against the overtone and the load

| n | f [MHz] | φ air (mean ± sd of three) [°] | φ water [°] | φ isopropanol [°] | board delay 0.76–1.10 ns → [°] |
|---|---|---|---|---|---|
| 1 | 5.0 | -8.0 ± 0.0 | -5.0 ± 0.0 | -5.0 ± 0.0 | 1.4–2.0 |
| 3 | 15.0 | -14.5 ± 0.0 | -15.0 ± 2.5 | -14.2 ± 0.2 | 4.1–5.9 |
| 5 | 25.0 | -20.6 ± 0.1 | -24.0 ± 0.0 | -24.7 ± 0.2 | 6.8–9.9 |
| 7 | 35.0 | -22.9 ± 0.0 | -22.5 ± 0.0 | -21.4 ± 0.1 | 9.6–13.8 |
| 9 | 44.9 | -26.8 ± 0.0 | -27.9 ± 0.2 | -27.2 ± 0.0 | 12.3–17.8 |

φ grows with n but not linearly with frequency: 5 → 45 MHz gives ×9 in frequency and ×3 in φ. A pure delay of the board (0.76–1.10 ns measured on the short and load standards, 2026-09-03) would give 1.4–2.0° at 5 MHz and 12–18° at 45 MHz: the right order at the top, too small at the bottom, and it does not explain why air and liquid differ on n = 1 and 3.
