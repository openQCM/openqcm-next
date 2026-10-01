# The HANDOFF §4 tables on the dumps of 2026-09-11: the numbers as they come out

*Board 1920 (125 MHz clock, in specification), 5 MHz sensor, TEC at 25 °C, air → water → isopropanol. Nine dumps
(`data/sweep_dumps_2026-09-11.npz`, three per phase: air 12:25 / 12:46 / 12:50, water 12:57 / 13:08 / 13:15,
isopropanol 13:20 / 13:24 / 13:30), 45 sweeps over overtones 1–9. Written 2026-10-01 on Marco's request: the
tables in `HANDOFF.md` §4 of this branch came from the July 2026 offline campaign, whose raw data were never kept;
each one is re-derived here on data that are in the repo, with one script per table. This page shows the numbers;
what goes into HANDOFF is decided after Marco has read them.*

*Tools. `software/openQCM/sweep_data/fit_admittance.py`, the offline tool of the July campaign, unchanged: FIT 1
(BVD circle), FIT 2 (Lorentzian on G with a free linear background), the two phase-offset rules — `fold`
(δ = −min r, the published rule) and `circle` (δ fitted by roundness, reverted on 2026-07-28) — and the −28 dB
saturation mask. `scripts/offline_fits_lib.py` runs its `analyse()` recipe on arrays from the `.npz`. Raw samples, no
smoothing, ±3 half widths around the seed — except Table 6, which runs the process's chain. Γ from
`fit_admittance` is the FULL width; the chain's is the half width; each table says which.*

*Two differences from the process to keep in mind. `fit_admittance` decides the fold with the old 5° threshold on
min r; the process decides it by the depth of the phase peak (`_phase_fold_decision`). On these sweeps the two agree
except water n = 3, where the process alternates between the two branches (README, `raw-sweeps.md`). And the forward
model of Table 7 is new: the July script that fitted φ_b was never versioned, so this one is written from the model
HANDOFF states.*

Run from `software/`, e.g. `cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/delta_fold_vs_roundness.py`.
Each script writes its table to `figures/handoff/`.

---

## 1. δ from the fold against δ from the roundness fit — `scripts/delta_fold_vs_roundness.py`

*HANDOFF today ("The phase-channel offset δ"), from July, "11 datasets": max step of B 20–86 % (roundness) against
0.5–7.5 % (fold); circle residual in air 0.8–2.5 % against 1.2–7.9 %, in water 3.1–11.1 % against 3.8–19.8 %;
Γ split FIT 1 / FIT 2, median over 55 overtones, 5.03 % (roundness) against 3.78 % (fold).*

B step = largest jump of B between adjacent samples over the ±3 half-width window, % of the range of B there.
Circle rms = FIT 1 radial residual, % of the radius. Γ split = |Γ_FIT1 − Γ_FIT2| / Γ_FIT2.

#### Table 1a — per phase and overtone, range over the three replicas

| phase | n | δ fold [°] | δ roundness [°] | B step, fold [%] | B step, roundness [%] | circle rms, fold [%] | circle rms, roundness [%] |
|---|---|---|---|---|---|---|---|
| air | 1 | +4.0–+4.0 | +10.0–+10.3 | 2.2–2.6 | 48.1–50.4 | 3.5–3.6 | 1.1–1.1 |
| air | 3 | +4.8–+4.9 | +8.6–+8.8 | 1.9–2.2 | 24.6–25.9 | 2.7–2.7 | 1.4–1.4 |
| air | 5 | +6.8–+6.9 | +6.5–+6.6 | 1.8–2.0 | 1.8–2.0 | 1.2–1.2 | 1.2–1.2 |
| air | 7 | +5.8–+5.9 | +12.0–+12.0 | 1.4–1.7 | 28.7–29.1 | 3.3–3.4 | 1.3–1.3 |
| air | 9 | -0.4–-0.3 | +11.5–+11.6 | 1.1–1.1 | 52.0–52.8 | 6.5–6.5 | 1.3–1.3 |
| water | 1 | -0.2–-0.0 | +12.9–+13.4 | 0.4–0.5 | 44.6–46.4 | 4.2–4.3 | 1.6–1.7 |
| water | 3 | +0.0–+0.0 | +0.0–+0.0 | 0.8–1.1 | 0.8–1.1 | 6.0–6.2 | 6.0–6.2 |
| water | 5 | +0.0–+0.0 | +0.0–+0.0 | 1.5–1.5 | 1.5–1.5 | 3.6–3.6 | 3.6–3.6 |
| water | 7 | +0.0–+0.0 | +0.0–+0.0 | 3.3–3.5 | 3.3–3.5 | 5.3–5.3 | 5.3–5.3 |
| water | 9 | +0.0–+0.0 | +0.0–+0.0 | 2.0–2.2 | 2.0–2.2 | 6.6–6.8 | 6.6–6.8 |
| isopropanol | 1 | -3.6–-3.4 | +16.4–+17.1 | 0.4–0.5 | 61.5–63.2 | 5.3–5.3 | 3.0–3.0 |
| isopropanol | 3 | +0.0–+0.0 | +0.0–+0.0 | 0.8–1.0 | 0.8–1.0 | 1.0–1.1 | 1.0–1.1 |
| isopropanol | 5 | +0.0–+0.0 | +0.0–+0.0 | 1.6–2.2 | 1.6–2.2 | 2.5–2.7 | 2.5–2.7 |
| isopropanol | 7 | +0.0–+0.0 | +0.0–+0.0 | 2.7–3.8 | 2.7–3.8 | 4.4–4.5 | 4.4–4.5 |
| isopropanol | 9 | +0.0–+0.0 | +0.0–+0.0 | 2.5–3.1 | 2.5–3.1 | 5.0–5.2 | 5.0–5.2 |

δ roundness = 0.0 means the search was rejected by its own guards (optimum on a bound, or residual above 5 %),
and the rule then applies no offset and no flip.

#### Table 1b — summary, the shape of the HANDOFF table

| rule | B step [% of range], all phases | circle rms, air [%] | circle rms, water [%] | circle rms, isopropanol [%] |
|---|---|---|---|---|
| fold | 0.4–3.8 | 1.2–6.5 | 3.6–6.8 | 1.0–5.3 |
| circle | 0.8–63.2 | 1.1–1.4 | 1.6–6.8 | 1.0–5.2 |

#### Table 2 — Γ split between FIT 1 and FIT 2, % (independent of circularity)

| rule | median, 45 sweeps | median, fundamentals (9) | median, n ≥ 3 (36) | range, 45 sweeps |
|---|---|---|---|---|
| fold | 8.14 | 2.54 | 8.36 | 0.10–18.53 |
| circle | 8.36 | 8.30 | 8.36 | 0.17–26.94 |

As measured: the roundness search is accepted on all five overtones in air and on the fundamentals in water and
isopropanol; on the damped overtones its guards reject it and it applies nothing, like the fold rule. On air n = 5 it
lands within 0.4° of the fold and the two give the same locus. Elsewhere, where it is accepted, its δ sits 3.7–20.5°
above the fold's, its circle residual is lower (1.1–3.0 % against 2.7–6.5 %), and B jumps by 25–63 % of its range
inside the window; the fold rule's largest jump
on all 45 sweeps is 3.8 %. On the Γ split the fold rule is lower on the fundamentals (median 2.54 % against 8.30 %)
and the two are the same on n ≥ 3 (8.36 %).

## 2. FIT 1 against FIT 2 — `scripts/fit1_vs_fit2.py`

*HANDOFF today (roadmap item 9), from July: in clean air the two agree to 1.4–5.4 ppm on f_s and 2.5–6.4 % on Γ;
without band restriction the 9th overtone's Γ is wrong by 3–5×.*

δ from the fold, −28 dB mask, band 3.

#### Table 3 — FIT 1 against FIT 2, range over the three replicas

| phase | n | f_s FIT1 − FIT2 [ppm] | Γ FIT1 − FIT2 [% of FIT2] | σ f_s FIT1 / FIT2 [Hz] | Γ FIT1 all points / Γ FIT2 | samples in band / unmasked |
|---|---|---|---|---|---|---|
| air | 1 | +2.61–+2.64 | -2.5–-2.1 | 0.58–0.58 / 0.29–0.29 | 0.94–0.95 | 391–393 / 3557–3560 |
| air | 3 | +1.18–+1.20 | -1.1–-0.6 | 0.35–0.35 / 0.32–0.32 | 0.98–0.98 | 465–469 / 4179–4184 |
| air | 5 | +1.19–+1.21 | -0.8–-0.1 | 0.24–0.24 / 0.44–0.44 | 0.97–0.97 | 637–649 / 8245–8257 |
| air | 7 | +1.43–+1.47 | -2.5–-2.2 | 0.41–0.42 / 0.56–0.56 | 1.03–1.04 | 937–957 / 12489–12492 |
| air | 9 | +1.86–+1.86 | -13.1–-12.7 | 0.78–0.78 / 0.62–0.63 | 4.22–4.23 | 1050–1062 / 16962–16970 |
| water | 1 | -12.36–-11.89 | -2.6–-2.5 | 1.38–1.39 / 0.28–0.28 | 0.97–0.98 | 3028–3034 / 3028–3034 |
| water | 3 | -17.79–-17.29 | -8.4–-8.1 | 0.35–0.35 / 2.92–2.98 | 0.92–0.92 | 3274–3281 / 3274–3281 |
| water | 5 | +3.60–+4.09 | -0.2–+0.8 | 0.50–0.52 / 5.15–5.38 | 1.08–1.09 | 4630–4691 / 7984–8014 |
| water | 7 | +4.67–+5.28 | -12.9–-11.2 | 0.55–0.56 / 6.22–6.48 | 0.92–0.94 | 6670–6733 / 13406–13414 |
| water | 9 | +14.52–+14.71 | -6.0–-5.5 | 1.27–1.28 / 2.06–2.09 | 0.96–0.97 | 11999–12141 / 18001–18001 |
| isopropanol | 1 | -92.87–-92.44 | -11.8–-11.7 | 1.64–1.64 / 0.88–0.89 | 0.88–0.88 | 2561–2565 / 2561–2565 |
| isopropanol | 3 | -17.21–-14.92 | -13.8–-7.5 | 0.20–0.23 / 14.31–17.22 | 0.86–0.93 | 2419–2428 / 2419–2428 |
| isopropanol | 5 | +7.56–+8.32 | +13.3–+14.8 | 0.29–0.29 / 4.90–5.33 | 1.18–1.19 | 4971–5063 / 7475–7507 |
| isopropanol | 7 | +3.22–+3.92 | -18.5–-17.4 | 0.59–0.60 / 7.85–8.11 | 0.85–0.86 | 8731–8824 / 13877–13885 |
| isopropanol | 9 | +16.00–+16.82 | -15.8–-15.4 | 1.46–1.49 / 2.10–2.12 | 0.87–0.88 | 13813–14021 / 18001–18001 |

| phase | \|f_s split\| [ppm] | \|Γ split\| [%] | Γ all points / Γ FIT2 |
|---|---|---|---|
| air | 1.18–2.64 | 0.1–13.1 | 0.94–4.23 |
| water | 3.60–17.79 | 0.2–12.9 | 0.92–1.09 |
| isopropanol | 3.22–92.87 | 7.5–18.5 | 0.85–1.19 |

As measured: in air the two agree to 1.2–2.6 ppm on f_s and within 2.5 % on Γ on n = 1–7; on n = 9 FIT 1 is 13 % low,
and with every unmasked sample instead of the band its Γ is 4.2× FIT 2's. In liquid the f_s split grows to
3–18 ppm, and to 92 ppm on the isopropanol fundamental; the Γ split is 0.2–18.5 %.

## 3. The saturation mask at −28 dB — `scripts/saturation_mask.py`

*HANDOFF today (roadmap item 5), from July: at −28 dB the mask drops 35–63 % of the band in water and 20 % on the
9th overtone in air; water 3rd overtone circle residual 18.1 % → 4.7 %, the two Γ estimators −5.5 % → −0.6 % apart.*

"Window removed" = samples of the ±3 half-width window at or below −28 dB of divider ratio, % of the window.

#### Table 4 — saturation mask at −28 dB, range over the three replicas

| phase | n | window removed [%] | circle rms, mask off → on [%] | Γ split FIT1/FIT2, mask off → on [%] |
|---|---|---|---|---|
| air | 1 | 0.0–0.0 | 3.5–3.6 → 3.5–3.6 | 2.1–2.5 → 2.1–2.5 |
| air | 3 | 0.0–0.0 | 2.7–2.7 → 2.7–2.7 | 0.6–1.1 → 0.6–1.1 |
| air | 5 | 0.0–0.0 | 1.2–1.2 → 1.2–1.2 | 0.1–0.8 → 0.1–0.8 |
| air | 7 | 0.0–0.0 | 3.3–3.4 → 3.3–3.4 | 2.2–2.5 → 2.2–2.5 |
| air | 9 | 12.1–13.0 | 7.0–7.1 → 6.5–6.5 | 0.2–1.4 → 12.7–13.1 |
| water | 1 | 45.9–46.3 | 5.5–5.6 → 4.2–4.3 | 1.6–1.8 → 2.5–2.6 |
| water | 3 | 57.7–57.7 | 17.7–17.9 → 6.0–6.2 | 3.3–4.0 → 8.1–8.4 |
| water | 5 | 40.9–41.4 | 10.1–10.3 → 3.6–3.6 | 6.9–7.8 → 0.2–0.8 |
| water | 7 | 36.7–37.0 | 6.6–6.7 → 5.3–5.3 | 6.0–6.4 → 11.2–12.9 |
| water | 9 | 0.0–0.0 | 6.6–6.8 → 6.6–6.8 | 5.5–6.0 → 5.5–6.0 |
| isopropanol | 1 | 66.6–66.7 | 8.1–8.2 → 5.3–5.3 | 7.3–7.7 → 11.7–11.8 |
| isopropanol | 3 | 75.7–75.7 | 14.8–15.2 → 1.0–1.1 | 12.3–12.8 → 7.5–13.8 |
| isopropanol | 5 | 43.1–43.9 | 9.3–9.3 → 2.5–2.7 | 5.8–6.5 → 13.3–14.8 |
| isopropanol | 7 | 31.9–32.1 | 5.7–5.8 → 4.4–4.5 | 12.2–12.7 → 17.4–18.5 |
| isopropanol | 9 | 0.0–0.0 | 5.0–5.2 → 5.0–5.2 | 15.4–15.8 → 15.4–15.8 |

As measured: in air the mask touches only n = 9 (12–13 % of the window). In water it removes 37–58 % of the window
on n = 1–7, in isopropanol 32–76 %; n = 9 sits above the floor in both liquids and is untouched. Where it removes
samples the circle residual falls (water n = 3: 17.8 % → 6.1 %; isopropanol n = 3: 15.0 % → 1.0 %), while the Γ split
between FIT 1 and FIT 2 rises on 7 of the 9 rows where samples are removed (water n = 3: 3.3–4.0 % → 8.1–8.4 %),
falls on water n = 5 (6.9–7.8 % → 0.2–0.8 %) and goes either way across the replicas on isopropanol n = 3.

## 4. Where the sweep sits in the detector's window — `scripts/dynamic_range.py`

*HANDOFF today ("Standing limitations"), from July: R17 = 52.3 Ω against a liquid load of 0.8–3.4 kΩ puts the whole
sweep at −23 to −36 dB of divider ratio, against the AD8302's specified ±30 dB, with a resonance contrast of only
2–12 dB.*

Divider ratio = (V_MAG − 0.9)/0.030 dB on the stored V_MAG. R1 = 1/(2r) of FIT 1.

#### Table 5 — divider ratio and motional resistance, range over the three replicas

| phase | n | ratio over the sweep [dB] | ratio at f_s [dB] | contrast [dB] | R1 FIT 1 [Ω] |
|---|---|---|---|---|---|
| air | 1 | -36.4–-36.3 … -4.5–-4.5 | -4.5–-4.5 | 31.8–31.9 | 38–38 |
| air | 3 | -36.5–-36.5 … -6.0–-5.9 | -6.0–-6.0 | 30.6–30.6 | 54–54 |
| air | 5 | -36.0–-35.9 … -8.9–-8.9 | -9.0–-8.9 | 27.0–27.1 | 93–95 |
| air | 7 | -34.6–-34.5 … -12.2–-12.0 | -12.4–-12.1 | 22.4–22.5 | 168–173 |
| air | 9 | -29.5–-29.4 … -13.8–-13.7 | -14.4–-14.3 | 15.7–15.8 | 246–248 |
| water | 1 | -36.5–-36.4 … -22.2–-22.2 | -22.3–-22.2 | 14.2–14.3 | 723–730 |
| water | 3 | -35.4–-35.3 … -25.2–-25.2 | -25.3–-25.3 | 10.1–10.2 | 1320–1324 |
| water | 5 | -32.3–-32.3 … -25.5–-25.5 | -25.9–-25.9 | 6.8–6.8 | 1930–1939 |
| water | 7 | -29.0–-29.0 … -25.1–-25.1 | -25.7–-25.7 | 3.9–3.9 | 2349–2364 |
| water | 9 | -25.8–-25.8 … -23.7–-23.6 | -24.4–-24.4 | 2.1–2.1 | 3248–3266 |
| isopropanol | 1 | -36.6–-36.5 … -24.7–-24.7 | -25.2–-25.1 | 11.8–11.9 | 1149–1153 |
| isopropanol | 3 | -35.2–-35.1 … -26.9–-26.9 | -27.2–-27.2 | 8.2–8.3 | 1659–1664 |
| isopropanol | 5 | -31.8–-31.7 … -26.4–-26.4 | -27.0–-27.0 | 5.3–5.3 | 2487–2491 |
| isopropanol | 7 | -28.6–-28.6 … -25.6–-25.6 | -26.3–-26.2 | 3.0–3.0 | 3117–3132 |
| isopropanol | 9 | -25.6–-25.6 … -23.9–-23.9 | -24.6–-24.6 | 1.6–1.6 | 4378–4416 |

| phase | ratio, whole sweep, all overtones [dB] | contrast [dB] | R1 [Ω] |
|---|---|---|---|
| air | -36.5 … -4.5 | 15.7–31.9 | 38–248 |
| water | -36.5 … -22.2 | 2.1–14.3 | 723–3266 |
| isopropanol | -36.6 … -23.9 | 1.6–11.9 | 1149–4416 |

As measured: in liquid the sweep spans −36.6 to −22.2 dB on all overtones, the contrast is 1.6–14.3 dB, and FIT 1's
R1 is 0.72–3.3 kΩ in water and 1.1–4.4 kΩ in isopropanol. In air the ratio reaches −4.5 dB at resonance on the
fundamental and the contrast is 16–32 dB.

## 5. The published half width in liquid — `scripts/liquid_baseline_bias.py`

*HANDOFF today (roadmap item 6 and "Sweep window sized for air"), from July: in water Γ_FWHM is 1.9–5.0 kHz, the
baseline mean(G[:100]) subtracts 13 % of the peak on the 3rd overtone and 66 % on the 9th, and Γ is low by −2.5 % to
−13.9 % against the Lorentzian, growing with overtone; in isopropanol Γ reaches 2.5 kHz and ±3Γ no longer fits above
resonance on the 7th and 9th.*

The process's chain (SG 51/3 + spline, fold by peak depth, `_half_bandwidth_G_exact`: HALF width, baseline = mean of
the first 100 samples) against `fit2_lorentzian` on the same smoothed G over ±3 Γ (its FWHM halved). Window
left / right = distance from f_r to the first and last sample of the sweep, in half widths.

#### Table 6 — the chain's half width, range over the three replicas

| phase | n | fold | Γ half height [Hz] | baseline / G max [%] | Γ half height vs Lorentzian [%] | window left / right of f_r [Γ] |
|---|---|---|---|---|---|---|
| air | 1 | yes | 65–66 | -0.0–-0.0 | -1.2–-1.0 | 183.0–184.0 / 91.5–92.0 |
| air | 3 | yes | 78–78 | 0.3–0.3 | +1.3–+1.3 | 153.7–154.1 / 76.9–77.1 |
| air | 5 | yes | 107–109 | 1.9–1.9 | +3.8–+4.0 | 110.1–111.7 / 55.1–55.8 |
| air | 7 | yes | 156–160 | 4.6–4.8 | +5.5–+5.6 | 74.8–77.1 / 37.4–38.5 |
| air | 9 | yes | 203–205 | 12.0–12.0 | +5.2–+5.4 | 58.6–59.1 / 29.3–29.5 |
| water | 1 | yes | 934–940 | 1.3–1.4 | +0.1–+0.3 | 12.8–12.9 / 6.4–6.4 |
| water | 3 | no/yes | 1299–1356 | 11.1–18.0 | -2.5–-2.3 | 8.8–9.2 / 4.4–4.6 |
| water | 5 | no | 1580–1584 | 34.3–34.3 | -4.2–-3.8 | 7.6–7.6 / 3.8–3.8 |
| water | 7 | no | 1820–1826 | 48.0–48.1 | -3.1–-3.0 | 6.6–6.6 / 3.3–3.3 |
| water | 9 | no | 2099–2100 | 66.7–67.0 | -3.7–-3.5 | 5.7–5.7 / 2.9–2.9 |
| isopropanol | 1 | yes | 1285–1286 | 3.7–3.8 | -1.0–-1.0 | 9.3–9.3 / 4.7–4.7 |
| isopropanol | 3 | no | 1669–1672 | 14.8–14.9 | -3.1–-2.9 | 7.2–7.2 / 3.6–3.6 |
| isopropanol | 5 | no | 2020–2028 | 41.7–41.7 | -7.1–-6.5 | 5.9–5.9 / 3.0–3.0 |
| isopropanol | 7 | no | 2381–2385 | 56.1–56.1 | -11.3–-11.2 | 5.0–5.0 / 2.5–2.5 |
| isopropanol | 9 | no | 2706–2713 | 73.8–73.8 | -15.7–-15.3 | 4.4–4.4 / 2.2–2.2 |

As measured: the baseline is 1–74 % of G max in liquid, growing with overtone (water n = 9: 67 %, isopropanol
n = 9: 74 %), and 0–12 % in air. Against the Lorentzian the half-height Γ is −2 to −4 % in water on n = 3–9 and
−3 to −16 % in isopropanol, growing with overtone; in air it is −1 to +6 %. The sweep window holds more than 3 half
widths on both sides everywhere except on the right of water n = 9 (2.9) and isopropanol n = 7 and 9 (2.5, 2.2);
isopropanol n = 5 has exactly 3.0.

## 6. A board phase φ_b inside the absolute value — `scripts/board_phase_forward_model.py`

*HANDOFF today (end of "The phase-channel offset δ"), from July: fitting the forward model to both channels gives
φ_b = −12…−20°, reproducible to 0.2–0.4° across two acquisitions 83 minutes apart, and improves both channel
residuals 4–5×.*

BVD crystal through the divider, V_MAG = V_CP − 0.6·log10(M/R17) and r = |φ + φ_b| − δ, fitted to both channels in
volts at the detector over ±3 half widths. Model A has φ_b = 0, model B has it free. Where the phase never crosses
−φ_b the absolute value is only a sign, φ_b and δ enter as a difference, and the fit cannot separate them: marked
by the correlation ρ(φ_b, δ).

#### Table 7 — board phase φ_b from the forward model, range over the three replicas

| phase | n | φ_b [°] | δ, model B [°] | δ, model A (φ_b = 0) [°] | rms V_MAG A → B [mV] | rms V_PHS A → B [mV] | ρ(φ_b, δ) | identifiable |
|---|---|---|---|---|---|---|---|---|
| air | 1 | -7.7–-7.6 | +9.6–+9.7 | +9.3–+9.4 | 9.68–9.76 → 4.14–4.16 | 34.00–34.36 → 18.59–18.70 | +0.242–+0.247 | yes |
| air | 3 | -13.8–-13.7 | +8.7–+8.8 | +7.3–+7.4 | 14.70–14.88 → 3.63–3.66 | 54.70–55.31 → 12.94–13.13 | +0.393–+0.396 | yes |
| air | 5 | -19.9–-19.8 | +8.7–+8.7 | +6.3–+6.3 | 26.71–27.33 → 6.82–6.95 | 80.13–81.00 → 13.36–13.59 | +0.557–+0.559 | yes |
| air | 7 | -22.1–-22.0 | +10.0–+10.0 | +11.0–+11.3 | 42.21–42.35 → 7.77–7.84 | 83.93–85.06 → 15.54–15.74 | +0.729–+0.732 | yes |
| air | 9 | -20.6–-20.2 | +7.2–+7.4 | +15.1–+15.3 | 32.87–33.00 → 23.33–24.87 | 70.46–71.13 → 18.51–19.39 | +0.696–+0.704 | yes |
| water | 1 | -4.9–-4.7 | +5.7–+5.8 | +6.2–+6.3 | 8.56–8.79 → 5.59–5.86 | 19.76–20.17 → 14.59–14.83 | +0.285–+0.288 | yes |
| water | 3 | -0.0–+0.1 | +22.1–+22.2 | +22.1–+22.2 | 37.95–38.39 → 37.95–38.39 | 19.42–19.58 → 19.42–19.58 | +1.000–+1.000 | no |
| water | 5 | -2.5–+0.0 | +21.1–+23.7 | +23.6–+23.7 | 13.84–13.99 → 13.84–13.99 | 8.09–8.30 → 8.09–8.30 | +1.000–+1.000 | no |
| water | 7 | -7.8–+0.2 | +18.2–+26.3 | +26.0–+26.1 | 6.76–6.77 → 6.76–6.77 | 4.47–4.49 → 4.47–4.49 | +1.000–+1.000 | no |
| water | 9 | +1.4–+14.9 | +31.4–+45.0 | +30.1–+30.1 | 3.84–3.89 → 3.84–3.89 | 2.34–2.39 → 2.34–2.39 | +1.000–+1.000 | no |
| isopropanol | 1 | -5.5–-5.4 | +3.1–+3.2 | +3.2–+3.4 | 9.78–9.93 → 7.50–7.57 | 20.54–20.64 → 17.35–17.58 | +0.189–+0.203 | yes |
| isopropanol | 3 | -28.3–+16.2 | -1.5–+43.3 | +26.8–+27.1 | 17.76–17.86 → 17.76–17.86 | 14.74–14.83 → 14.74–14.83 | +1.000–+1.000 | no |
| isopropanol | 5 | -9.4–+0.0 | +14.6–+24.0 | +24.0–+24.1 | 9.35–9.54 → 9.35–9.54 | 5.85–6.17 → 5.85–6.17 | +1.000–+1.000 | no |
| isopropanol | 7 | -0.4–+1.7 | +25.6–+27.5 | +25.9–+26.0 | 5.10–5.15 → 5.10–5.15 | 3.79–3.82 → 3.79–3.82 | +1.000–+1.000 | no |
| isopropanol | 9 | -4.3–+0.0 | +25.6–+30.0 | +29.9–+30.0 | 2.60–2.66 → 2.60–2.66 | 1.94–1.95 → 1.94–1.95 | +1.000–+1.000 | no |

Replicas within a phase are 4–25 minutes apart (dump write times: air 12:25, 12:46, 12:50; water 12:57, 13:08, 13:15;
isopropanol 13:20, 13:24, 13:30).

As measured: φ_b is identifiable in air on all overtones and on the two liquid fundamentals, and nowhere else
(ρ = 1.000). In air φ_b = −7.6 … −22.1° from n = 1 to n = 7–9, the same to 0.4° across the three replicas (4–25
minutes apart), and model B lowers the V_MAG residual 1.4–5.5× and the V_PHS residual 1.8–6.0×. Model B still leaves
4–25 mV on V_MAG and 13–19 mV (1.3–1.9°) on V_PHS in air.

## What these data cannot give

- The **body and module swap** (excess motional resistance following the sensor module, "body 3", "three central
  bodies and three sensor modules"): one board and one sensor here.
- **φ_b applied as a rotation after unfolding** (July: continuity restored, roundness 4.3 % against 4.5 %): the July
  procedure was not recorded, and this page does not invent one.
- The **synthetic checks of the roundness estimator** (+12° injected and recovered): not a property of a dataset.

## Status

Numbers as measured, 2026-10-01. Read by Marco the same day; `HANDOFF.md` §4 cites these tables since then.
