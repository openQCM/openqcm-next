# Number check of manuscript v0.2 (2026-10-08) against the regenerated results

Checked: `manuscript/manuscript.md` (abstract, Sections 2–9, Table 2) and the prose of `supporting_information.md` S2–S9 (plus S11 for completeness) against `analysis/results/v2/asis/{tables.md, *.csv, summary.json}`, `v2/fwfix/tables.md`, `results/{tables_asis.md, glucose_tables_asis.md, bias_theory.md, forward_model.md, datalogs.md, closed_forms_check.csv, sweeps_asis.csv, sweeps_fwfix.csv, glucose_sweeps_*.csv}` and `notes/theory_sla_to_kg_check.md`. Derived quantities (reproducibility percentages, isopropanol/water shift ratios, per-sweep firmware differences, fold vertices, window clipping) were recomputed from the CSVs. Variant "as acquired" unless stated. Rounding to the printed digits is accepted; "→" means "source value".

Summary: 206 confirmed, 34 discrepancies (4 moderate, the rest minor/trivial), 15 unverifiable.

---

## 1. CONFIRMED

### Abstract
1. "overshoots the KG frequency shift by 20–36 %" → A, n = 3–9: DS-2 +19.5…+29.5, DS-3 +20.2…+36.4 (summary table).
2. "half-height width is within 7 % of the KG bandwidth shift" → A ε_Γ: DS-2 −7.4…+6.3, DS-3 −4.5…−0.2 (7.4 rounds to 7).
3. "PSL brings the frequency shift to −1…+8 % on the first instrument and +6…+13 % on the second" → P ε_f −1.4…+8.2 / +6.1…+13.1.
4. "leaves the bandwidth within 5–9 %" → P ε_Γ max |.|: DS-2 9.3, DS-3 4.6.
5. "ratio ΔΓ/(−Δf) moves from 0.71–0.85 to 0.86–1.02" → A: 0.71…0.83 (DS-3), 0.75…0.85 (DS-2 all liquids); P: 0.92…1.02 (DS-2 all liquids), 0.86…0.99 (DS-3).
6. "f_Gmax − f_res = Γtan(φ/2) … verified on 120 sweeps to 0.12 Γ" → summary.json bias: n = 120, max |.|/Γ = 0.122.
7. "glucose steps of 2.5 % w/v, i.e. 4 % in √(ρη)" → x_both steps 0.039 (5 → 7.5 %) and 0.041 (7.5 → 10 %).
8. "resolved at 14 or more replica standard deviations" → min step/σ in frequency 14.0 on n = 3–9 (13.5 at n = 1, see D31).
9. "reproducible to 0.3° between sweeps" → max replica sd of φ excluding the threshold sweep: 0.23° (DS-2 water n = 9).
10. "independent of the liquid and of its concentration to 2° on overtones 3–9" → phi_stability liquid range max 2.0° (DS-3 n = 3).
11. "differs between air and liquid by 3–8° at the fundamental and by 4–5° on one overtone" → air − mean(liquids): n = 1: −3.0 (DS-2), −8.3 (DS-3); n = 5: +3.7 (DS-2), −5.0 (DS-3).
12. "up to 5° between boards" → phi_between DS-3 − DS-2: −5.2° at n = 3.

### Section 1
13. "overshoots the Kanazawa–Gordon frequency shift by 50–116 % on the overtones" → M ε_f: DS-2 +51.8…+91.9, DS-3 +49.5…+115.8.
14. "verified on 120 sweeps" → 45 + 75.
15. Table 1 "magnitude maximum, −0.3 dB width" (production) and "1–9" overtones → consistent with S8 and Table S1.

### Section 2
16. "ρ_q = 2648 kg m⁻³ and μ_q = 2.947×10¹⁰ Pa (Z_q = 8.83×10⁶)" → √(2648·2.947e10) = 8.834e6 (theory note §4).
17. "f_F = 5.0046 MHz the coefficient is 715 Hz per unit √(ρη) per √n" → 715.04 (DS-2, tables.md header).
18. "water at 25 °C (997.05 kg m⁻³, 0.890 mPa s) Δf_n = −673.6√n Hz" → 673.57.
19. "isopropanol (781.0 kg m⁻³, 2.038 mPa s) … −902.1√n Hz" → 902.11.
20. "Kerscher … 780.9 kg m⁻³ and 2.07 mPa s, +0.9 % on the coefficient" → 910.0 vs 902.1 = +0.9 % (theory note §5).
21. "fall by 1.2 %/K (water) and 1.6 %/K (isopropanol)" → −1.15 %/K and −1.60 %/K (theory note §4).
22. "±2 K uncertainty is ±2–3 %" → 2.3 % (water), 3.2 % (isopropanol).

### Section 3
23. "R_17 = 52.3 Ω" → forward_model.md "R17 = 52.3 Ω".
24. "averages 500 readings per frequency point" → consistent with the 1/500 carry-over (S7).
25. "18 001 points at 1 Hz step over −12 kHz/+6 kHz" → 18 kHz / 1 Hz + 1 = 18 001; bias_theory.md window "−12/+6 kHz".
26. "Savitzky–Golay, 51 points, order 3, then a smoothing spline" → S3 "Savitzky–Golay 51/3 + spline".

### Section 4
27. "V_MAG − 0.030·20log10K = V_MAG − 0.6107 V" → 0.030 × 20.3565 = 0.6107.
28. "the 0.36 dB by which K differs from one decade is 4 % on M" → 20.3565 − 20 = 0.356 dB; 10^(0.356/20) = 1.042.
29. "amplified by (1 + R_17/R_m), 2.5× in air" → R_m/R_17 = 0.7 for the air n = 1-like case (S6) gives 2.43.
30. "1.04× in liquid" → R_m/R_17 = 24 (S6 upper case) gives 1.04 (the liquid range 12–24 spans 1.04–1.08).
31. "damped crystal (liquid, n ≥ 3) … reading has a smooth minimum tens of degrees above zero, there is no fold" → sweeps_asis r_min 9.1–45.3° (DS-2 n ≥ 3 liquid), fold False (except the threshold sweep).

### Section 5
32. "maximum lies below the resonance by 0.07 Γ at −8° and 0.25 Γ at −28°" → tan(−4°) = −0.0699, tan(−14°) = −0.2493.
33. "half-height width over-estimates Γ by 0.5–6 %" → √(1+2tan²(φ/2)) = 1.0049 (−8°), 1.0603 (−28°); closed_forms_check hh_th 1.0049 / 1.0603.
34. "midpoint of the crossings is biased twice as much as the maximum" → f_mid = f_res + 2Γtan(φ/2); closed_forms mid_th = 2 × argmax_th.
35. "A symmetric Lorentzian fitted to a rotated one is biased by ≈1.25–2 Γtan(φ/2)" → closed_forms_check: sym (constant bg) 1.91–2.13×, sym+linear 1.25–1.33× over −8…−28°.
36. "five parameters of (8)" → G_max, Γ, φ, G_off, f_res.
37. Gate "0.3 ≤ Γ/Γ_hh ≤ 3, |φ| ≤ 60°, rms residual below 5 %" → S5 (same constants).
38. "phase-shifted one 0.15–0.8 % in liquid and 1–3 % in air" → summary.json psl_rms: liquid 0.147–0.652 % (DS-2), 0.227–0.842 % (DS-3); air 0.966–2.65 % (DS-2), 0.864–1.43 % (DS-3).

### Section 6
39. "one acquisition of 75 min" → t4_ds2_datalog 12:15:27 → 13:30:22.
40. "air 12:25, 12:46, 12:50; water 12:57, 13:08, 13:15; isopropanol 13:20, 13:24, 13:30" → sweeps_asis mtime 12:25:49, 12:46:32, 12:50:12; 12:57:32, 13:08:48, 13:15:26; 13:20:02, 13:24:12, 13:30:02.
41. "45 sweeps" / "75 sweeps" → summary.json gate sweeps 45 / 75.
42. "1/500 of the previous point into each point (+0.2 % on the counts)" → S7, 1/500 = 0.2 %.
43. "shifts are liquid minus air … standard deviation the quadrature sum" → tables_asis.md header.
44. "glucose √(ρη) relative to water … mean over n = 3–9 of (−Δf_n + ΔΓ_n)/(−Δf_{n,w} + ΔΓ_{n,w})" → glucose_xrel x_both_n3_9.

### Section 7.1 (first paragraph)
45. "+20 to +30 % on board 1920 and +20 to +36 % on the second" → A ε_f +19.5…+29.5 / +20.2…+36.4.
46. "within −7…+6 % and −5…0 %" → A ε_Γ −7.4…+6.3 / −4.5…−0.2.
47. "r_n is 0.71–0.85" → A r: 0.71…0.83 (DS-3), 0.75…0.85 (DS-2).
48. "−1…+8 % and +6…+13 %" → P ε_f −1.4…+8.2 / +6.1…+13.1.
49. "−4…+9 % and −4…+5 %" → P ε_Γ −3.9…+9.3 / −4.4…+4.6.
50. "r_n becomes 0.92–1.01 and 0.86–0.99" → P r water: 0.92…1.01 / 0.86…0.99.

### Table 2
51. DS-2 M: +52…+92; +40…+309 (undefined n ≥ 7); 0.92…2.40; b = −0.30 → +51.8…+91.9; +40.3…+309.2; "—" at n = 7, 9; 0.92…2.40; −0.297.
52. DS-2 A: +19.5…+29.5; −7.4…+6.3; 0.76…0.85; −0.54, −0.62 → exact; kg2 −0.5392, −0.6214.
53. DS-2 P: −1.4…+8.2; −3.9…+9.3; 0.92…1.01; −0.58, −0.62 → exact; kg2 −0.5757, −0.6246.
54. DS-3 M: +50…+116; +16…+300 (undefined n ≥ 7); 0.78…2.38; −0.17 → +49.5…+115.8; +16.4…+299.7; 0.78…2.38; −0.1716.
55. DS-3 A: +20.2…+36.4; −4.5…−0.2; 0.71…0.83; −0.41, −0.50 → exact; kg2 −0.4132, −0.4991.
56. DS-3 P: +6.1…+13.1; −4.4…+4.6; 0.86…0.99; −0.52, −0.52 → exact; kg2 −0.5155, −0.5169.

### Section 7.1 (KG-2 paragraph)
57. "frequency slope from −0.41 to −0.52" → DS-3 water A −0.413, P −0.515.
58. "spread of −Δf_n/√n … from 5.8 % to 2.6 %" → CV(−Δf/√n) DS-3 water n = 3–9: A 5.8, P 2.6.
59. "board 1920 … −0.54 (spread 3.4 %) and the fit −0.58 (4.1 %)" → DS-2 water A −0.539 / 3.4; P −0.576 / 4.1.
60. "bandwidth slope … −0.62 on board 1920 with both estimators" → A −0.621, P −0.625.
61. "ΔΓ_n/n in water falls from +9 % above the theory at n = 3 to −4 % below it at n = 9" → DS-2 P ε_Γ +9.3 (n = 3), −3.9 (n = 9).

### Section 7.1 (KG-3 paragraph)
62. "+6…+13 % on the second instrument" → DS-3 P ε_f +6.1…+13.1.
63. "the two-state sweep of n = 3 in water on board 1920 (+9 %, SI S5)" → DS-2 P ε_Γ n = 3 water +9.3.
64. "|ε_f| ≤ 8.2 % on every overtone 3–9 in water and isopropanol" → claim_8pct max 8.2 (DS-2 water n = 3).
65. "|ε_f| ≤ 8 % on n = 5 only; 10–13 % on n = 3, 7, 9" → DS-3 P 13.1, 6.1, 11.0, 10.1.

### Section 7.1 (bias paragraph)
66. "+1 ± 28 Hz on DS-2 and +21 ± 28 Hz on DS-3, at most 80 Hz" → summary.json bias by_dataset: +1.05 ± 28.1 (max 76.8), +20.7 ± 28.3 (max 79.9).
67. "0.02 Γ on average and 0.12 Γ at worst" → mean_over_gamma 0.0208, maxabs_over_gamma 0.122.
68. "by 2–47 Hz in air (0.03–0.25 Γ)" → bias_meas air n ≥ 3: −1.8 … −46.7 Hz; /Γ_P: 0.024 (DS-2 n = 3) … 0.247 (DS-2 n = 9).
69. "83–556 Hz in water (0.09–0.26 Γ)" (φ < 0 sweeps) → DS-2 n = 1 −82.8 Hz (0.089 Γ) … DS-3 n = 9 −556.5 Hz (0.261 Γ); DS-3 water n = 1 (φ = +0.7°) excluded by the φ < 0 condition.
70. "in liquid the residual is within ±0.05 Γ" → max |resid/Γ| in liquid: −0.045 (DS-2 water n = 1); per sweep −0.048.
71. "half-height width … in air (1.03–1.09 times Γ against 1.02–1.06 predicted)" → Γ_hh/Γ_P air n ≥ 3: 1.026–1.090; predicted 1.016–1.060.
72. "the two biases are of opposite sign and nearly cancel" → bias_theory half-height table (rotation factor > 1, baseline on skirt ratio < 1).

### Section 7.1 (reconstruction/rotation and reproducibility)
73. "(M → A) … +52…+92 % → +20…+30 %" → summary table.
74. "−3 dB width … does not exist inside the sweep window for n ≥ 7 in liquid" → M rows "—" at n = 7, 9 (all liquids) and n = 5 in ipa/glucose.
75. "−0.3 dB width grows to several kilohertz" → datalogs.md Δw up to 6.4 kHz (ipa n = 9).
76. "(A → P) removes the remaining +20…+36 % on frequency" → A ε_f range.
77. "agree, with P, to −1…+12 % on Δf_n/n … for n = 3–9 (SI Table S6)" → DS-3/DS-2 − 1 (P, water): +4.4, −0.9, +5.8, +11.6 %.
78. "(+4, −1, +6, +12 % on n = 3, 5, 7, 9)" → same.
79. "live A estimator … ε_f = +14…+29 % and +12…+30 %" → datalog 09-11 water +14.2…+29.3; 09-10 +12.1…+30.4.
80. "rotation angles in water differ between the instruments by 4–10°" → |φ_w DS-2 − DS-3|: 3.8, 9.5, 6.2, 4.0° (n = 3–9); 5.8° at n = 1.

### Section 7.2
81. "ε_f = +8.2, +7.0, +4.8, −1.4 % (water) and +7.9, +2.7, +4.8, −1.0 % (isopropanol)" → exact.
82. "ε_Γ = +9.3, +2.5, −3.3, −3.9 % and +5.1, +2.3, +1.5, +1.1 %" → exact.
83. "r_n = 1.01, 0.96, 0.92, 0.98 and 0.97, 1.00, 0.97, 1.02" → 1.011, 0.958, 0.923, 0.975; 0.974, 0.996, 0.969, 1.021.
84. "b = −0.58 and −0.56 for the frequency, −0.62 and −0.54 for the bandwidth" → kg2 psl n = 3–9: −0.576/−0.564; −0.625/−0.536.
85. "696 … Hz for −Δf (theory 674 and 902) and 669 and 920 Hz for ΔΓ" → k(−Δf) water 696; k_KG 674 / 902; k(ΔΓ) 669 / 920 (n = 3–9). (926: see D23.)
86. "tabulated √(ρη) of isopropanol is 1.339 times that of water" → 1.2616/0.9420 = 1.3393.
87. "measured ratio of the shifts is 1.29–1.35 in frequency and 1.29–1.41 in bandwidth on n = 3–9" → recomputed 1.286–1.346 / 1.288–1.410.
88. "residual overtone pattern of r_n (lowest at n = 7)" → water 0.923 at n = 7; ipa 0.969 at n = 7 (0.974 at n = 3).

### Section 7.3
89. "ε_f = +13.1, +6.1, +11.0, +10.1 % and ε_Γ = −1.7, +4.6, −4.4, −1.4 %" → exact.
90. "r_n = 0.87, 0.99, 0.86, 0.90 (water)" → 0.869, 0.986, 0.861, 0.895.
91. "0.88, 0.98, 0.88, 0.92 (5 %)" → 0.876, 0.980, 0.877, 0.921.
92. "0.88, 0.98, 0.89, 0.93 (7.5 %)" → 0.877, 0.980, 0.885, 0.930.
93. "0.88, 0.98, 0.89, 0.94 (10 %)" → 0.876, 0.981, 0.891, 0.936.
94. "same zig-zag … to ±0.02" → half-range across liquids per n: ≤0.021 (n = 9: 0.895–0.936).
95. "equal to it on n = 5" → r_5 = 0.98–0.99.
96. "b = −0.49…−0.52 (frequency) and −0.45…−0.52 (bandwidth)" → P n = 3–9: −0.490…−0.515; −0.454…−0.517.
97. "against −0.40…−0.41 for the frequency with the maximum of G" → A n = 3–9: −0.395…−0.413.
98. "spread of −Δf_n/√n over n = 3–9 is 2.4–2.9 % with P and 5.8–6.7 % with A" → CV: P 2.6, 2.4, 2.6, 2.9; A 5.8, 6.5, 6.5, 6.7.
99. "1.052, 1.091 and 1.132 at 5, 7.5 and 10 % w/v (both channels)" → x_both_n3_9 1.0521, 1.0908, 1.1319.
100. "1.046, 1.082, 1.121 from the frequency alone and 1.059, 1.101, 1.145 from the bandwidth alone" → x_df 1.0460, 1.0820, 1.1208; x_dG 1.0591, 1.1010, 1.1446.
101. "per-overtone values scatter by 1.7–2.6 % around these means" → sd_n of x_both 0.0167, 0.0210, 0.0263.
102. "separate on n = 7 and 9 (1.13–1.14 against 1.17–1.19 at 10 %)" → x_df n7/n9 1.126/1.138; x_dG 1.165/1.191.
103. "SI S9 tests the clipped fit window, which accounts for a fifth of it" → 1.418 → 1.395 against a gap of 0.122 (19 %).
104. "grows linearly with the concentration, 0.0131 per % w/v" → OLS slope x_both 0.01307.
105. "5 % point 0.008 below the line" → residual −0.0084.
106. "offset of 0.6 % w/v equivalent" → 0.0084/0.0131 = 0.64.
107. "constant in hertz over the overtones" → S9/glucose_tables: +10 … +18 Hz for P on n = 1–9.
108. "steps … 0.052, 0.039, 0.041" → 1.052 − 1; 1.091 − 1.052; 1.132 − 1.091.
109. "replica scatter … 0.3–1.7 Hz on f_res and 0.2–1.3 Hz on Γ with the fit" → glucose_resolution psl sd_f 0.32–1.70; sd_Γ 0.24–1.27.
110. "σ_x = 0.0004–0.0008 … from the frequency and 0.0001–0.0012 from the bandwidth" → res_x_f 0.00040–0.00076; res_x_G 0.00014–0.00123 (n = 1 included).
111. "i.e. 0.03–0.09 % w/v" → 0.0004/0.0131 = 0.031; 0.0012/0.0131 = 0.092.
112. "15 or more in bandwidth on every overtone" → min step/σ_Γ = 15.1 (n = 1).
113. "The maximum of G resolves the same steps at 4–31 σ" → A step/σ_f 4.5–31.3 (frequency channel).
114. "0.6 % w/v offset … an order of magnitude larger" → 0.6 vs 0.03–0.09.

### Section 7.4
115. "+6…+13 % (second instrument, water)" → DS-3 P.
116. "bandwidth within ±5 % on both (one sweep at +9 %)" → P ε_Γ max |.| 4.6 (DS-3), 3.9 (DS-2 excluding n = 3 water +9.3; ipa n = 3 +5.1 rounds to 5).
117. "r_n 0.92–1.02 and 0.86–0.99" → P r all liquids: DS-2 0.92…1.02; DS-3 0.86…0.99.
118. "uncertainty (±2–3 % for ±2 K)" → S2.
119. "agree to 1–12 % in frequency and 1–10 % in bandwidth on n = 3–9" → |DS-3/DS-2 − 1| P: f 0.9–11.6 %; Γ 1.3–10.2 %.
120. "linear in concentration to 0.008" → rms 0.0058, max residual −0.0084.
121. "Resolution: 0.0004–0.0012 in relative √(ρη), 0.03–0.09 % w/v" → as 110–111.
122. "r_1 = 1.27–1.31" → P water 1.265, ipa 1.310.
123. "dissipation in air (26 × 10⁻⁶) is three times that of the overtones" → D(P) air: 26.2 vs 10.1, 8.2, 8.4, 8.4.
124. "on the second crystal ε_Γ = +6.5 %, r_1 = 0.99" → DS-3 P n = 1 +6.5, 0.991.
125. "air dissipation is higher still (46 × 10⁻⁶)" → DS-3 air n = 1 D(P) 45.9.
126. "Across the liquids of a dataset … 0.1–1.1° (DS-2) and 0.2–2.0° (DS-3)" → phi_stability liquid_range 0.06–1.10; 0.20–2.01.
127. "across the three glucose concentrations by ≤1.4°" → max 1.39° (n = 3).
128. "from −7…−8° at 5 MHz to −27…−32° at 45 MHz" → φ air n = 1: −8.0, −7.3, −7.8; n = 9 all media: −26.8 … −31.9.
129. "monotonically in air on board 1920 on both days" → phi_monotonicity: DS-2 air True, 2026-09-03 air True.
130. "At the fundamental … 3° on board 1920 (−8.0° → −5.0°) and 8° on the second instrument (−7.3° → +0.7…+1.2°)" → exact.
131. "the third board's water sweep reads +2.2°" → water 2026-07-28 φ = 2.2.
132. "On the 5th overtone … +4° on board 1920 (−20.6° → −24.0…−24.7°) and −5° on the second instrument (−19.5° → −14.4…−14.6°)" → air − mean(liquids): +3.7, −5.0; values exact.
133. "and by 3° on n = 7 and 9 of the second instrument" → +2.7, +3.1.
134. "inversions of 1–3° between n = 5 and 7 on board 1920" → largest wrong-direction step: water 1.4, ipa 3.3.
135. "nor in air on the second (φ_3 ≈ φ_5)" → −19.7 / −19.5.
136. "Between boards the air values differ by 1–5°, most on n = 3" → DS-3 − DS-2: +0.7, −5.2, +1.1, −2.4, −1.1.
137. "between days on board 1920 by 0–3°" → 09-03 − DS-2: +0.2, −3.0, −2.0, −2.8, −2.0.
138. "not a load-independent constant to better than 3–8° at the fundamental and 4–5° on one overtone" → as 11.

### Section 8
139. "whole of the 20–36 % frequency excess … to 0.12 Γ on 120 sweeps" → as 1, 6.
140. "resistive standards of board 1920 give 0.7–1.1 ns, i.e. 1–2° at 5 MHz and 12–18° at 45 MHz, against −8° and −27°" → bias_theory: τ 0.74–1.10 ns; 1.4–2.0°; 12–18°; PSL −8° / −27°.
141. "closed-form bias 5–8 Hz short" (air) → bias resid +7.2, +7.8, +7.5 Hz (DS-2 n = 1–5), +7.1 … +7.7 (DS-3).
142. "the one unstable sweep of 120" → DS-2 water n = 3 replica 2 (fold flips).
143. "exact in liquid (R_m/R_17 = 12–24, residual ≤2 % of Γ)" → forward_model cases 12.0–23.8; PSL error −59 Hz on Γ ≈ 2.9 kHz.
144. "approximate in air (R_m/R_17 = 0.7–4)" → 0.7–3.9.
145. "fit window of ±3Γ is clipped by the sweep for n ≥ 5 in isopropanol and n = 9 in water" → sweeps window_right_gamma: ipa n = 5/7/9 2.96/2.52/2.21; water n = 9 2.86–2.88 (DS-2), 2.77–2.82 (DS-3).
146. "(f_res within 15 Hz, Γ within 1 % for ±5 % on the slope; SI S6)" → forward_model D: Γ ≤0.9 %; f see D18 (16.6 Hz in one case).
147. "divider ratio in liquid sits at −22 … dB" (lower end) → ratio_dB_peak liquid −21.8 … −27.3 dB.
148. "glucose ρη relative only; three sweeps per plateau" → consistent.

### Section 9
149. "52.3 Ω divider" → as 23.
150. "50–116 %", "20–36 %", "within 7 %", "−1…+8 %", "+6…+13 %", "within 5–9 %", "0.71–0.85 to 0.86–1.02", "0.12 Γ", "120 sweeps" → as 1–6, 13.
151. "log–log slopes −0.49 to −0.58" → P b(Δf) n = 3–9: −0.490 … −0.576.
152. "noise-equivalent resolution of 0.04–0.12 % in relative √(ρη)" → 0.0004–0.0012 (consistent with 7.4; inconsistent with the abstract, see D1).
153. "reproducible to 0.3°, … to 2° on overtones 3–9, growing from −8° to −30° between 5 and 45 MHz … 3–8° … 4–5° … up to 5°" → as 9–12, 128.

### SI S2
154. "f_F = 5 004 596 Hz (DS-2) and 5 000 107 Hz (DS-3)" → tables.md header.
155. "coefficient 715.04 and 714.08 Hz per √n per unit √(ρη)" → 715.0386, 714.0768.
156. "water (√(ρη) = 0.9420) 673.6 and 672.7 Hz·√n" → 715.04 × 0.9420 = 673.6; 714.08 × 0.9420 = 672.7.
157. "isopropanol (1.2616 …) 902.1 Hz·√n (910 Hz with Kerscher's values)" → theory note §5.
158. "−1.15 %/K for water … −1.6 %/K for isopropanol" → theory note §4.
159. "±2 K … ±2–3 %" → as 22.
160. "√(1.102933·1.0665/(0.99705·0.890)) = 1.151, i.e. by 15 %" → recomputed 1.1513; theory note §5.

### SI S3
161. "on none of the overtones n ≥ 3 in liquid, where the minimum stays 9–45° above zero" → r_min 9.1–45.3° (DS-2), 18.0–44.2° (DS-3 n ≥ 5).
162. "on DS-3 the same, with the fold also on n = 3 in all four liquids" → DS-3 n = 3 fold True, r_min −0.3 … +2.3°.
163. "One sweep of 120 (DS-2, water, n = 3, third replica) has a minimum depth of 0.880" → sweeps_asis depth 0.879, 0.878, 0.880 (replica 2 folds).
164. "logged pair alternating between two states 105 Hz and 7.7 × 10⁻⁶ apart from 13:12 onwards" → t4_ds2_datalog n = 3: from 13:12:31 alternates −1397…−1399 vs −1506…−1509 Hz (≈107–110 Hz from the rounded Δf/n; 7.7 × 10⁻⁶ in D exactly).
165. "no effect on f_res or Γ when a fold exists" → forward_model B: f_psl within 0.3 Hz over δ = −3…+7°.
166. "closed-form bias of the maximum 5–8 Hz short there" → as 141.

### SI S4
167. "argmax bias −3.0/−2.8 Hz (−5°, 65 Hz) … −582/−582 Hz (−40°, 1600 Hz)" → closed_forms_check.
168. "Γ_hh/Γ 1.0014/1.0019 … 1.1198/1.1247" → exact.
169. "midpoint −5.7/−5.7 … −1048/−1165 Hz" → exact.
170. "over-estimates Γ by 2–35 % between −8° and −28°" → sym_gamma 1.018–1.346.
171. "with a linear background Γ is right to 0.2 % and the frequency bias is ≈1.25 Γtan(φ/2)" → symlin_gamma ≤1.0018; symlin_bias/argmax_th 1.25–1.33.
172. "f_Gmax − f_res is negative on every liquid sweep and on every air sweep with n ≥ 3 (Table S8)" → bias_meas: all liquid rows negative (incl. DS-3 n = 1: −6…−9); air n ≥ 3 negative.

### SI S5
173. "clipped … for n ≥ 5 in isopropanol, 2.2–3.0 Γ available" → DS-2 ipa window_right 2.21–2.97 Γ.
174. "45/45 fits of DS-2 and 75/75 of DS-3 converged and were accepted (fallback rate 0 %)" → summary.json gate.
175. "phase-shifted 1.0–2.7 % in air and 0.15–0.65 % in liquid on DS-2, 0.9–1.4 % and 0.2–0.8 % on DS-3" → psl_rms exact.
176. "symmetric Lorentzian with linear background 3.0–4.2 % and 0.8–3.5 % (DS-2), 1.8–4.2 % and 0.7–3.8 % (DS-3)" → sym_lin_rms exact.
177. "DS-2, f_res 1.5–23 Hz in air … and 0.3–29 Hz in liquid, Γ ≤ 2.3 Hz in air and ≤ 38 Hz in liquid (… ≤ 13 Hz otherwise)" → repeat_f_air_max 23.3 (min 1.5 for A n = 1), repeat_f_liq_max 28.7 (min 0.3 ipa n = 7 P), repeat_G_air_max 2.31, repeat_G_liq_max 38.2; next largest Γ sd 12.6 (ipa n = 5 P).
178. "DS-3, f_res ≤ 2.4 Hz in air and ≤ 7.6 Hz in liquid, Γ ≤ 0.7 and ≤ 4.5 Hz" → 2.44, 7.57, 0.66, 4.52.
179. "−3 dB width is undefined … on 15 of 45 (DS-2) and 33 of 75 (DS-3) sweeps; the half-height width of G is two-sided on all 120" → mag_w3_missing 15 / 33; one_sided_hh 0 / 0.

### SI S6
180. "(ii) with φ_b = 0 both estimators recover f_s to the grid" → Table A: f_Gmax 0…−3 Hz, f_psl ≤0.8 Hz (fold cases).
181. "(iii) maximum of G off by −91 to −743 Hz on liquid-like cases … the symmetric fit by −96 to −833 Hz" → Table A liquid-like rows.
182. "(iv) ≈ −0.34 Γ (R_17/R_1) at φ_b = −20°: −344 Hz at R_1 = R_17 and −12 Hz at 1.6 kΩ" → Table E −344.2 / −12.5.
183. "(v) with a fold, δ is removed … (≤0.5 Hz for δ = −3…+7°)" → Table B.
184. "(vi) … Γ by ≤7 Hz" → Table C Γ changes ≤4.4 Hz.
185. "(vii) … Γ by ≤1 % … even with an ideal magnitude channel R_m is 24–39 % low in liquid" → Table D: R_m,est/R1 0.760 (water n = 5), 0.609 (ipa n = 9).
186. "(ix) … +10 % … a 190 Hz one by 3.5 Hz" → Table A air n = 9-like Γ_psl − Γ = +3.5 at φ_b = 0.
187. "phase slopes of 0.27–0.40° MHz⁻¹ (0.74–1.10 ns), i.e. 1.4–2.0° at 5 MHz and 12–18° at 45 MHz; … grows roughly as f^0.55; φ_0 = −7.0°, τ = 1.28 ns (rms 1.2°) … φ_0 = −8.2°, τ = 1.31 ns (rms 2.6°)" → bias_theory.md (0.2682/0.3969; 0.74/1.10; f^0.55; −7.0/1.28/1.2) and glucose_tables_asis.md (air n = 1–9: −8.2/1.31/2.6).

### SI S7 (confirmed parts)
188. "(f_res +37 Hz with P, +111 Hz with A; φ +4.3°)" → per-sweep DS-2 water n = 3 replica 2: +37.2 / +111.0 / +4.31°.
189. "corrected variant: DS-2 P ε_f = −1.6…+7.8 %, ε_Γ = −4.3…+7.3 %; DS-3 P +6.0…+13.0 %, −4.4…+4.6 %" → fwfix summary table.
190. "the bias law gives +14 ± 30 Hz on 120 sweeps" → fwfix "+14 ± 30 Hz".
191. "φ by ≤0.2°" (DS-2 excl. threshold sweep; DS-3) → max 0.19° / 0.22°.

### SI S8
192. "ε_f = +52…+92 % (DS-2) and +50…+116 % (DS-3) on n = 3–9, growing with the overtone" → M rows monotonic in n.
193. "reaches 6 kHz at n = 5" → M ΔΓ 6163 / 6012 Hz (Γ_M 6.3 kHz).
194. "95 of 486 rows were exact duplicates" → datalog d0911 rows 486, dup 95.
195. "ε_f = +51, +69, +76, +89 % (water) and +57, +74, +85, +90 % (isopropanol)" → datalogs.md mag: +51.3, +68.6, +76.2, +89.3; +56.5, +73.5, +85.0, +90.1.
196. "+23, +29, +22, +18 % and +22, +27, +22, +22 % for the live A estimator" → +23.1, +29.3, +21.7, +17.5; +21.9, +26.9, +21.8, +22.4.
197. "−0.3 dB width changes by 0.8–3.7 kHz (water) and 1.1–6.4 kHz (isopropanol) where the theory's ΔΓ is 1.2–2.7 kHz" → Δw 772–3720 / 1084–6387 Hz; KG ΔΓ n = 3–9 1167–2706 Hz.
198. "2026-09-10 run (2.5 min plateaus, 36 of 175 rows duplicated) gives +51…+98 % and +22…+30 %" → datalogs.md: mag +51.0…+98.2; A +22.4…+30.4.

### SI S9
199. "slopes −7.1, −13.8, −17.8, −24.7, −30.4 Hz per % w/v in Δf_n and +9.2, +13.1, +16.6, +28.0, +37.8 Hz per % in ΔΓ_n" → glucose_tables psl k.
200. "5 % plateau … +10 to +18 Hz in Δf and −9 to −14 Hz in ΔΓ" → residuals +12, +18, +10, +16, +15; −13, −14, −13, −14, −9.
201. "slope of f_res … ≤0.4 Hz/min inside the glucose plateaus and −0.2 to −1.0 Hz/min in water" → drift table: glucose max +0.36; water −0.17…−1.02.
202. "the 5 % plateau is 4.3 min off the line … at most ≈4 Hz" → −4.3 min; 1.0 × 4.3.
203. "1.36 and 1.42 against 1.27 and 1.30 at 10 %" → 1.358 / 1.418 vs 1.269 / 1.296.
204. "(2.5–2.6 Γ on the right at n = 9)" (glucose) → window_right 2.45–2.63 Γ.
205. "moves the n = 9 ratio from 1.418 to 1.395, a fifth of the gap, and nothing at n = 7" → clipwindow table (1.358 → 1.357 at n = 7).
206. "broadens by +94 to +379 Hz" (at 10 % w/v) → ΔΓ(P) vs water at 10 %: +94 (n = 1) … +379 (n = 9).

(206 confirmed items; a few lines group several numbers of one sentence.)

---

## 2. DISCREPANCIES

**D1 (moderate) — Abstract:** "a noise-equivalent resolution of 0.1–0.2 % in √(ρη)". Source: σ_x = 0.0004–0.0008 (frequency) / 0.0001–0.0012 (bandwidth), i.e. 0.04–0.12 %, which is what Section 7.4 ("0.0004–0.0012") and the Conclusion ("0.04–0.12 %") print. 0.1–0.2 % matches 3σ_x from the frequency on n = 3–9 (0.0012–0.0023). Correction: "0.04–0.12 %" (1σ), or say "3σ" explicitly.

**D2 (moderate) — Sections 7.1 (KG-3 paragraph), 7.2, 7.4, 8 (twice):** "+2…+8 % above the theory on board 1920" / "the absolute level is 2–8 % high for both liquids" / "frequency +2…+8 % (board 1920, two liquids)" / "residual frequency excess of 2–13 %" / "The residual +2…+13 % frequency excess". Source: DS-2 P ε_f on n = 3–9 = −1.4…+8.2 % (water −1.4 % and isopropanol −1.0 % at n = 9 are *below* the theory), as Table 2, the abstract and the conclusion print. Correction: "−1…+8 %" / "−1…+13 %"; "2–8 % high" is only true on n = 3–7.

**D3 (moderate) — Abstract, 7.2, 7.4, 9:** "reproduce the tabulated ratio of √(ρη) to 1–4 %" / "liquid constants are reproduced to 1–4 %". Source (recomputed from shifts.csv, P, n = 3–9): ratio of shifts / 1.339 − 1 = −0.3, −4.0, 0.0, +0.5 % (frequency) and −3.8, −0.1, +4.9, +5.3 % (bandwidth). Correction: "to 4 % in frequency and 5 % in bandwidth" (or "0–5 %").

**D4 (moderate) — Section 6 ("the difference is ≤2 Hz on 119 of 120 sweeps (SI S7)"), Section 8 Limitations ("corrected offline, ≤2 Hz"), SI S7 ("≤2.2 and ≤1.7 Hz on 44 of 45 sweeps"):** per-sweep fwfix − asis (P): DS-2 |Δf| ≤2 Hz on 40/45 (≤2.2 Hz on 41/45); besides the threshold sweep (+37 Hz) a second sweep, water n = 9 replica 1, moves by +10.0 Hz on f_res and −17.5 Hz on Γ, and the three ipa n = 3 sweeps by +2.2 Hz; DS-3 75/75 ≤2 Hz. Over 120 sweeps: 115 ≤2 Hz, 116 ≤2.2 Hz, 118 ≤4 Hz. With A the changes are far larger (DS-2: 21/45 ≤2 Hz, max 111/49/6 Hz; DS-3: 38/75, max 6 Hz). Correction: "≤2 Hz on 115 of 120 sweeps with P (≤4 Hz on 118), the two exceptions being the threshold sweep (+37 Hz) and one water n = 9 sweep (+10 Hz, −18 Hz on Γ)"; in S7 "on 43 of 45 sweeps".

**D5 (minor) — SI S7:** "On DS-3 it changes f_res by ≤4 Hz, Γ by ≤1 Hz and φ by ≤0.2°". Source: P: |Δf| ≤1.6 Hz, |ΔΓ| ≤1.8 Hz (n = 3, all liquids), |Δφ| ≤0.22°; A: |Δf| ≤6 Hz (n = 9), |ΔΓ| ≤1.8 Hz. Correction: "f_res by ≤2 Hz (P; ≤6 Hz with A), Γ by ≤2 Hz".

**D6 (minor) — SI S7:** "The summary ranges of Table 2 move by ≤2 percentage points". True for A and P (max 2.0 points, DS-2 ε_Γ +9.3 → +7.3); the M rows move by 2.8 (ε_f 91.9 → 94.7) and 3.4 points (ε_Γ 309.2 → 312.6). Correction: "the A and P ranges of Table 2 move by ≤2 percentage points".

**D7 (minor) — Section 5:** "the symmetric Lorentzian leaves an S-shaped residual of 2–4 % of the range on every sweep of this work". Source: sym + linear rms 3.0–4.2 % (air) and 0.7–3.8 % (liquid); sym with constant background 2.0–9.2 % (tables_asis). Correction: "0.7–4 % (linear background), 2–9 % (constant background)".

**D8 (minor) — SI S4:** "A symmetric Lorentzian with constant background … is biased by 1.3–2.1 Γtan(φ/2)". Source (closed_forms_check, −8…−28°): sym_bias/argmax_th = 1.91–2.13; 1.25–1.33 is the linear-background figure. Correction: "1.9–2.1 Γtan(φ/2)".

**D9 (minor) — Section 7.1:** "The symmetric Lorentzian … is worse than A on frequency (+23…+46 %, SI Fig. S6)". Source: S+ ε_f +22.4…+45.8 % (both datasets, n = 3–9); and the estimator-errors figure is Fig. S7 (Fig. S6 is the firmware-correction figure). Correction: "+22…+46 %, SI Fig. S7".

**D10 (minor) — Section 7.1, bias paragraph:** "(SI Fig. S9)" for the half-height width against Γ. Fig. S9 is the glucose concentration lines; the half-height figure is Fig. S10. Correction: "SI Fig. S10".

**D11 (minor) — SI S2:** "Z_q = 8.84×10⁶ kg m⁻² s⁻¹". Source: √(2648 × 2.947e10) = 8.834e6; the main text prints 8.83×10⁶ and the theory note §7 item 2 asks for 8.83. Correction: "8.83×10⁶".

**D12 (minor) — SI S3:** "On DS-2 the fold is present on all overtones in air (vertex −0.6° to −6.9°, i.e. δ = +0.6…+6.9°)". Source (sweeps_asis r_min, PSL): air vertices −4.0…−4.2 (n = 1), −4.8…−4.9 (3), −6.4 (5), −5.6…−5.7 (7) and +0.6 (n = 9, above zero), i.e. δ = −0.6…+6.4°. Correction: "vertex +0.6° (n = 9) to −6.4° (n = 5), i.e. δ = −0.6…+6.4°".

**D13 (minor) — SI S3 and S6 (vi):** "the forward model gives ≤10 Hz on f_res … for ±5° in liquid" / "moves f_res by ≤10 Hz". Source (forward_model Table C): 11.1 Hz (ipa n = 9-like, δ = −5°) and 14.5 Hz (water n = 5-like, δ = +5°, where a spurious fold is declared). Correction: "≤11 Hz (15 Hz where the offset triggers a spurious fold)".

**D14 (minor) — SI S3:** "on synthetic air-like data the recovered δ is 1.0–2.3° more negative than the true offset". Source (forward_model Table B, air-like): δ_found − δ = −1.78…−1.52 (n = 1), −1.65 (n = 5), −1.01…−1.02 (n = 9). Correction: "1.0–1.8°".

**D15 (minor) — Section 7.4 and SI S6 (i):** "the fitted angle equals the imposed board phase to 0.5° in the liquid regime" / "to 0.5° on every case". Source (forward_model Table A): liquid-like cases within 0.7° (water n = 9-like and ipa n = 9-like at φ_b = −25° give −25.7°); air n = 9-like at −25° gives −26.0° (1.0°); water n = 5-like at −25° gives −32.5° (spurious fold). Table E: within 0.6°. Correction: "to 0.7° (liquid), 1° (air), except the one case where the offset triggers a spurious fold".

**D16 (minor) — SI S6 (iv) and Section 8:** "−12 to −39 Hz, one third to one half of the argmax bias" / "the correction removes half to two thirds of a bias". Source (Tables A/B): air n = 5- and n = 9-like, yes (PSL/argmax 0.29–0.52); air n = 1-like (R_1/R_17 = 0.7): PSL −30.8 vs argmax −40 at −20° (0.77), and at −8° the fit (−12.4 Hz) is *worse* than the maximum (−11 Hz). Correction: qualify "for R_1/R_17 ≥ 1.8; at R_1/R_17 = 0.7 the fit removes a quarter or nothing".

**D17 (minor) — Section 8 and SI S6:** "the resistive standards read M 8–14 % low". Source (bias_theory, M at 5/25/45 MHz): short 44.8/44.2/49.7 Ω vs 52.3 (−14, −15, −5 %); 50 Ω load 93.7/95.3/98.2 vs 102.3 (−8, −7, −4 %). Correction: "4–16 % low (8–14 % at 5 MHz)".

**D18 (trivial) — SI S6 (vii):** "±5 % on the magnitude slope moves f_res by ≤15 Hz … but R_m = 1/G_max by 10–40 %". Source (Table D): f_psl 16.6 Hz for ipa n = 9-like at k = 0.95; R_m,est/R1 changes by 6–16 % (relative) for ±5 %; "10–40 %" is not in the table (the absolute R_m errors are 2–46 %). Correction: "≤17 Hz"; state what the 10–40 % refers to.

**D19 (trivial) — SI S6 (viii):** "the firmware carry-over moves f_res by ≤2 Hz" (model). Source (Table D): 2.3 Hz (ipa n = 9-like). Correction: "≤2.3 Hz" or "≈2 Hz".

**D20 (trivial) — SI S6 (ix):** "widens a 65 Hz half-bandwidth by 6.6 Hz". Source (Table A, air n = 1-like, φ_b = 0): Γ_psl − Γ = +6.5 Hz (Γ_hh +7.1). Correction: "6.5 Hz".

**D21 (trivial) — SI S6 (iii):** "the phase-shifted fit by −7 to −59 Hz" on liquid-like cases. Source: liquid-like PSL errors −9.3…−59.2 Hz (−7 is an air case). Correction: "−9 to −59 Hz".

**D22 (trivial) — SI S6:** "equal to the P angle within 0.3–0.8° on n = 1–7". Source: |−7.6 + 8.0| = 0.4, 0.7, 0.7, 0.8. Correction: "0.4–0.8°".

**D23 (trivial) — Section 7.2:** "926 … Hz for −Δf" (isopropanol). Source: through-origin slope on n = 3–9 is 925 Hz (926 is the n = 1–9 fit); the other three numbers in the sentence (696, 669, 920) are the n = 3–9 values. Correction: "925".

**D24 (trivial) — Section 7.3:** "the bandwidth 7–14 % short of the frequency shift on n = 3, 7 and 9". Source: 1 − r_n = 6.4 % (10 %, n = 9) … 13.9 % (water, n = 7). Correction: "6–14 %".

**D25 (minor) — Section 7.4, fundamental:** "its bandwidth shift is +29 % (water) and +37 % (isopropanol) above KG with every estimator". Source: A/P/MP/S/S+ give +29.0…+29.4 (water) and +35.3…+36.9 (isopropanol); M gives +15.6/+20.1 and C +31.5/+47.7; A gives +35 % for isopropanol. Correction: "+29 % and +35–37 % with the conductance estimators A, P and the symmetric fits (M and C differ)".

**D26 (trivial) — Section 7.1, bias paragraph:** "the opposite way in liquid (0.93–0.99)". Source: Γ_hh/Γ_P liquid n ≥ 3 = 0.926–1.004 (DS-3 water n = 7). Correction: "0.93–1.00".

**D27 (trivial) — Section 7.1, bias paragraph:** "narrow air peaks (+0.06…+0.11 Γ, 5–8 Hz)". Source: DS-3 air n = 3 is +0.085 Γ but 4.4 Hz; DS-2 air n = 7, 9 are +0.014/−0.009 Γ. Correction: "4–8 Hz" (or restrict to n = 1–5).

**D28 (trivial) — SI S9:** "explaining the residual by drift alone would need −2 to −6 Hz/min, five to fifteen times what is measured". Source (glucose_tables, P): drift needed −2.3…−4.3 Hz/min against measured max |drift| 0.17–1.02 Hz/min, ratios 3.4–16; −6.2 Hz/min is the A value at n = 3. Correction: "−2 to −4 Hz/min (P), three to sixteen times what is measured".

**D29 (trivial, wording) — SI S9:** "the fitted resonance moves by −17 to −72 Hz (fundamental) and −128 to −307 Hz (9th) at 10 % w/v". Source: −17/−128 are the 5 % values and −72/−307 the 10 % values; "at 10 % w/v" applies only to the broadening (+94 to +379 Hz). Correction: "moves by −72 Hz (fundamental) to −307 Hz (9th) at 10 % w/v (−17 to −128 Hz at 5 %)".

**D30 (trivial) — SI S5:** "for n = 9 in water, 2.5–2.6 Γ in DS-3". Source: DS-3 water n = 9 window_right = 2.77–2.82 Γ; 2.45–2.63 Γ are the glucose solutions at n = 9 (DS-2 water n = 9: 2.86–2.88). Correction: "2.8–2.9 Γ in water and 2.5–2.6 Γ in the glucose solutions at n = 9".

**D31 (trivial) — Section 7.3:** "every step is 14 or more replica standard deviations in frequency … on every overtone". Source: water → 5 % at n = 1 is 13.5 σ (rounds to 14); on n = 3–9 the minimum is 14.0. Correction: "14 or more on overtones 3–9 (13.5 at the fundamental)".

**D32 (trivial) — Section 7.1, reproducibility:** "−10…+3 % on ΔΓ_n/n". Source: −10.2, +2.0, −1.3, +2.5 %. Correction: "−10…+2 %" (or "+3" if rounding up is intended).

**D33 (trivial) — Section 7.1, KG-2 paragraph:** "The bandwidth slope is −0.50 on the second instrument … with both estimators". Source: A −0.499, P −0.517 (Table 2 prints −0.50 and −0.52). Correction: "−0.50 (A) and −0.52 (P)".

**D34 (trivial) — Section 7.4:** "Across the three replicas of a plateau the angle repeats to 0.00–0.25°". Source: max replica sd excluding the threshold sweep 0.23° (DS-2 water n = 9). Correction: "0.00–0.23°" (the abstract's 0.3° is fine).

Related cross-reference note (not a number): Section 7.1 "(SI Fig. S7)" for ΔΓ_n/n against the theory is correct (Fig. S7 shows ε_Γ); the two wrong references are D9 and D10.

---

## 3. UNVERIFIABLE (not in the listed sources)

1. Section 3: "K = (R_11+R_19)/R_19 = 10.419, 20.356 dB" — circuit constants; 20·log10(10.419) = 20.3565 is self-consistent, but K itself is not in the sources.
2. Section 4: "up to 22 % on the motional resistance in air" — `notes/derivations.md` line 23 asserts it ("verified by substitution in §3") but no number is in the listed results; simple propagation 4.2 % × (1 + R_17/R_m) with R_m = 36 Ω (air n = 1) gives 10 %, so the 22 % needs its R_m stated.
3. Section 3: "about 1.8 s per overtone".
4. Section 6: "logged 24.93–25.00 °C" (DS-2) and "24.95–25.02 °C" (DS-3) — the datalog CSVs in results carry no temperature column; datalogs.md shows 25.00 inside the plateau windows only.
5. Section 6: glucose solution provenance (AIC 029863065; 55 g L⁻¹ monohydrate / 50 g L⁻¹ anhydrous).
6. Section 8: "the divider ratio in liquid sits at −22 to −37 dB" — the peak ratio is −21.8…−27.3 dB (sweeps ratio_dB_peak); the −37 dB end (presumably off-resonance) is not in the sources.
7. Section 8: "the contrast of the divider ratio falls to 1.6 dB".
8. Section 8 / S3: "the fold is rounded over 20–50 Hz in air" — stated in S3, no numeric source in results.
9. S3: fold-rule constants ("88 % of the way", "within 5 Γ", "latched over two consecutive sweeps") — instrument constants, not in results (the 0.880 depth of the threshold sweep is confirmed).
10. S3: "step of 28–89 % of the range of B", "takes r_n to 0.5–0.8", "circle to 1–7 % of its radius in air and 5–18 % in liquid" — from `fold-hypothesis.md`, not among the listed sources ("subtracts 9–45°" matches r_min 9.1–45.3°).
11. S5: "Levenberg–Marquardt with tolerances 10⁻¹²"; "the fit's covariance gives 0.1–0.8 Hz on f_res"; "the air baseline was still drifting at −0.3 to −2 Hz/min".
12. S6: "two-channel forward model … gives φ_b = −7.6, −13.8, −19.9, −22.1, −20.4° in air on board 1920" — repository model, not in the listed results.
13. S6 (iv): "for air-like cases (Γ = 65–190 Hz, R_1 = 36–204 Ω) −12 to −39 Hz" — the −0.34 Γ R_17/R_1 formula with those bounds gives −17 to −32 Hz; Table A at −25° gives −21…−39 Hz, at −8° −7…−12 Hz; the exact pairing used for "−12 to −39" is not reproducible from the tables.
14. Section 2: "Z_q = 8.83×10⁶ … [@Johannsmann2021]" — the source prints 8.8×10⁶ (theory note); 8.83 is the computed value (fine, but the citation is for 8.8).
15. S2: "the 2008 and 1985 primary texts were not reachable" — consistent with the theory note; equation numbers of those sources remain ungraded.
