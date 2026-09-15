"""Block A of the validation plan (2026-09-15): the phase-shifted Lorentzian on G against the argmax estimator.

    cd software && PYTHONPATH=. python ../research/.../scripts/psl_validation.py <npz> <air_dump_2026-09-10_dir or -> <out_dir>

A1 bias formula on all 45 sweeps      A2 independence from the smoothing      A3 independence from the offset delta
A4 synthetic sweeps with known truth  A5 the air dump of 2026-09-10           A6 fit covariance vs replica scatter
A7 model variants (linear background, symmetric window where the sweep is clipped)   A8 phi against n and the board delay
"""
import sys, os, json, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from psl_lib import *
NPZ, AIR10, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True); Z = np.load(NPZ)
ALL = [(s, n) for sets in SETS.values() for s in sets for n in N]
L = []
def liq_of(s): return {"air": "air", "wat": "water", "ipa": "ipa"}[s[:3]]

# ------------------------------------------------------------------ A1: bias formula on all 45 sweeps
L += ["## A1 — the bias of argmax against the fit, all 45 sweeps\n", "For the rotated Lorentzian the maximum of G sits at f_argmax = f_res + Γ·tan(φ/2) (derivative of Re Y set to zero). Measured against predicted:\n",
      "| set | n | Γ [Hz] | φ [°] | argmax − f_res measured [Hz] | Γ·tan(φ/2) predicted [Hz] | difference [Hz] | difference / Γ |", "|---|---|---|---|---|---|---|---|"]
base = {}; pts = []
for s, n in ALL:
    c = chain(Z["%s/g%d" % (s, n)]); r = psl_G(c["fr"], c["G"], c["B"]); base[(s, n)] = (c, r)
    pred = r["gamma"] * np.tan(np.radians(r["phi_deg"]) / 2); meas = r["f_arg"] - r["fres"]; pts.append((s, n, r["gamma"], meas, pred))
    L.append("| %s | %d | %.0f | %+.1f | %+.0f | %+.0f | %+.0f | %+.3f |" % (s, n, r["gamma"], r["phi_deg"], meas, pred, meas - pred, (meas - pred) / r["gamma"]))
d = np.array([m - p for *_, m, p in pts]); g = np.array([x[2] for x in pts])
L.append("\nOver the 45 sweeps: difference measured − predicted, mean %+.0f Hz, sd %.0f Hz, max |.| %.0f Hz; in units of Γ mean %+.3f, max %.3f. The half-height Γ and the 1 Hz grid enter the measured value; the fitted Γ and φ the predicted one.\n" % (d.mean(), d.std(ddof=1), np.abs(d).max(), (d / g).mean(), np.abs(d / g).max()))
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
for liq, c_, mk in (("air", "#2a78d6", "o"), ("water", "#1baf7a", "s"), ("ipa", "#eb6834", "D")):
    sel = [x for x in pts if liq_of(x[0]) == liq]; ax[0].plot([x[4] for x in sel], [x[3] for x in sel], mk, color=c_, ms=6, mfc="none", label=liq); ax[1].plot([x[2] for x in sel], [(x[3] - x[4]) / x[2] for x in sel], mk, color=c_, ms=6, mfc="none", label=liq)
lim = [min(x[4] for x in pts) - 30, max(x[4] for x in pts) + 30]; ax[0].plot(lim, lim, "k--", lw=0.8, label="measured = predicted"); ax[0].set_xlabel("Γ·tan(φ/2) predicted [Hz]"); ax[0].set_ylabel("argmax G − f_res measured [Hz]"); ax[0].set_title("A1: the bias of argmax, 45 sweeps"); ax[0].legend(); ax[0].grid(alpha=0.25); ax[0].set_aspect("equal")
ax[1].axhline(0, color="k", lw=0.8); ax[1].set_xscale("log"); ax[1].set_xlabel("Γ [Hz]"); ax[1].set_ylabel("(measured − predicted) / Γ"); ax[1].set_title("residual of the formula in units of Γ"); ax[1].legend(); ax[1].grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "A1_bias_formula.png"), dpi=110); plt.close(fig)

# ------------------------------------------------------------------ A2: smoothing
L += ["## A2 — independence from the smoothing\n", "The fit on G built from the raw samples (no Savitzky–Golay, no spline), from SG 11/3 + spline, and from the chain's SG 51/3 + spline. Middle replicas.\n",
      "| set | n | f_res: raw / SG 11 / SG 51 [Hz, from chain's argmax] | Γ: raw / SG 11 / SG 51 [Hz] | φ: raw / SG 11 / SG 51 [°] | rms G raw / SG 11 / SG 51 [%] |", "|---|---|---|---|---|---|"]
a2 = {}
for s, n in [(x, n) for x in ("air_1", "wat_1", "ipa_1") for n in N]:
    g = Z["%s/g%d" % (s, n)]; c51, r51 = base[(s, n)]; fold = c51["fold"]; out = []
    for w in (0, 11, None):
        c = chain(g, window=w, fold=fold); rr = psl_G(c["fr"], c["G"], c["B"]); out.append(rr)
    a2[(s, n)] = out
    L.append("| %s | %d | %+.0f / %+.0f / %+.0f | %.0f / %.0f / %.0f | %+.1f / %+.1f / %+.1f | %.2f / %.2f / %.2f |" % (s, n, *[o["fres"] - r51["f_arg"] for o in out], *[o["gamma"] for o in out], *[o["phi_deg"] for o in out], *[100 * o["rmsG"] for o in out]))
dfr = [a2[k][0]["fres"] - a2[k][2]["fres"] for k in a2]; dga = [a2[k][0]["gamma"] - a2[k][2]["gamma"] for k in a2]; dph = [a2[k][0]["phi_deg"] - a2[k][2]["phi_deg"] for k in a2]
L.append("\nRaw minus chain over the 15 cases: f_res %+.0f…%+.0f Hz, Γ %+.0f…%+.0f Hz, φ %+.1f…%+.1f°.\n" % (min(dfr), max(dfr), min(dga), max(dga), min(dph), max(dph)))

# ------------------------------------------------------------------ A3: offset delta
L += ["## A3 — independence from the phase offset δ\n", "The chain's phase shifted by −5°, 0, +5° before the inversion (on top of the chain's own δ), fit on G on the same window. Middle replicas.\n",
      "| set | n | f_res shift for δ−5° / δ+5° [Hz] | Γ change [Hz] | φ change [°] | rms G [%] at −5 / 0 / +5 |", "|---|---|---|---|---|---|"]
a3 = []
for s, n in [(x, n) for x in ("air_1", "wat_1", "ipa_1") for n in N]:
    g = Z["%s/g%d" % (s, n)]; c0, r0 = base[(s, n)]; out = []
    for dx in (-5.0, 0.0, 5.0):
        c = chain(g, delta_extra=dx, fold=c0["fold"]); out.append(psl_G(c["fr"], c["G"], c["B"]))
    a3.append((s, n, out[0]["fres"] - out[1]["fres"], out[2]["fres"] - out[1]["fres"], out[0]["gamma"] - out[1]["gamma"], out[2]["gamma"] - out[1]["gamma"], out[0]["phi_deg"] - out[1]["phi_deg"], out[2]["phi_deg"] - out[1]["phi_deg"]))
    L.append("| %s | %d | %+.0f / %+.0f | %+.0f / %+.0f | %+.1f / %+.1f | %.2f / %.2f / %.2f |" % (s, n, *a3[-1][2:], *[100 * o["rmsG"] for o in out]))
L.append("\nA ±5° offset moves f_res by at most %.0f Hz and Γ by at most %.0f Hz over the 15 cases; φ moves by %+.1f…%+.1f° per +5°.\n" % (max(max(abs(x[2]), abs(x[3])) for x in a3), max(max(abs(x[4]), abs(x[5])) for x in a3), min(x[7] for x in a3), max(x[7] for x in a3)))

# ------------------------------------------------------------------ A4: synthetic sweeps
L += ["## A4 — synthetic sweeps with known truth\n", "A BVD motional branch Y_m = 1/(R1(1 + jx)), x = (f² − f_s²)/(f·2Γ), rotated by a known φ about the C0 offset (Y = e^{jφ}Y_m + jωC0), sent through the divider H = R17·Y/(1 + R17·Y) and the detector (V_MAG = 0.9 − 0.6·log10(M/R17), V_PHS = 1.8 − 0.01·(|arg H| − δ)), quantised on the ADC (3.3/4096 V, /2 and /1.5 op-amp gains) with 0.05° of noise, on the −12/+6 kHz window at 1 Hz; then the chain and both estimators. Truth in the first columns.\n",
      "| case | f_s [Hz] | Γ [Hz] | R1 [Ω] | φ [°] | δ [°] | fold | argmax − f_s [Hz] | Γ half height − Γ [Hz] | fit f_res − f_s [Hz] | fit Γ − Γ [Hz] | fit φ [°] | predicted argmax bias Γ·tan(φ/2) [Hz] |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
rng = np.random.default_rng(1)
def synth(fs, gam, R1, C0, phi_deg, delta_deg, noise_deg=0.05):
    f = np.arange(fs - 12000, fs + 6001, 1.0); x = (f ** 2 - fs ** 2) / (f * 2 * gam); Ym = 1 / (R1 * (1 + 1j * x)); Y = np.exp(1j * np.radians(phi_deg)) * Ym + 1j * 2 * np.pi * f * C0
    H = R17 * Y / (1 + R17 * Y); M = R17 / np.abs(H); Vmag = 0.9 - 0.6 * np.log10(M / R17); Vphs = 1.8 - 0.01 * (np.abs(np.degrees(np.angle(H))) - delta_deg)
    Vmag += rng.normal(0, 0.03 * 0.03, f.size); Vphs += rng.normal(0, 0.01 * noise_deg, f.size)          # 0.03 dB, 0.05 deg
    q = 3.3 / 4096; Vmag_adc = np.round((Vmag + Constants.V_MAG_DECADE_OFFSET) * 2 / q) * q / 2 - Constants.V_MAG_DECADE_OFFSET; Vphs_adc = np.round(Vphs * 1.5 / q) * q / 1.5
    return np.column_stack([f, Vmag_adc, Vphs_adc])
cases = [("air-like n=5", 24973700.0, 105.0, 94.0, 3.3e-12, 0.0, 6.4), ("air-like n=5", 24973700.0, 105.0, 94.0, 3.3e-12, -21.0, 6.4),
         ("water-like n=5", 24971700.0, 1600.0, 1800.0, 3.3e-12, 0.0, 0.0), ("water-like n=5", 24971700.0, 1600.0, 1800.0, 3.3e-12, -24.0, 0.0),
         ("water-like n=9", 44940700.0, 2100.0, 3250.0, 3.3e-12, -28.0, 0.0), ("ipa-like n=3", 14986800.0, 1700.0, 1800.0, 3.3e-12, -14.0, 0.0)]
a4 = []
for name, fs, gam, R1, C0, phi, dl in cases:
    g = synth(fs, gam, R1, C0, phi, dl); c = chain(g); r = psl_G(c["fr"], c["G"], c["B"])
    a4.append((name, fs, gam, R1, phi, dl, c["fold"], r["f_arg"] - fs, r["gam_hh"] - gam, r["fres"] - fs, r["gamma"] - gam, r["phi_deg"], gam * np.tan(np.radians(phi) / 2)))
    L.append("| %s | %.0f | %.0f | %.0f | %+.0f | %+.1f | %s | %+.0f | %+.0f | %+.0f | %+.0f | %+.1f | %+.0f |" % a4[-1])
L.append("\nWith φ = 0 both estimators recover f_s to the grid; with the rotation the argmax is off by the predicted Γ·tan(φ/2) while the fit recovers f_s, Γ and φ. The chain's fold decision is exercised on the air-like cases (δ = 6.4°, the reading dips below zero).\n")

# ------------------------------------------------------------------ A5: air dump of 2026-09-10
if AIR10 != "-" and os.path.isdir(AIR10):
    L += ["## A5 — the air dump of 2026-09-10 16:00, same board and sensor, the day before\n", "| n | f_res − argmax [Hz] | Γ [Hz] | φ [°] 2026-09-10 | φ [°] 2026-09-11 air (mean of three) | rms G [%] |", "|---|---|---|---|---|---|"]
    for n in N:
        g = np.loadtxt(os.path.join(AIR10, "g%d.txt" % n)); c = chain(g); r = psl_G(c["fr"], c["G"], c["B"]); phi11 = np.mean([base[(s, n)][1]["phi_deg"] for s in SETS["air"]])
        L.append("| %d | %+.0f | %.0f | %+.1f | %+.1f | %.2f |" % (n, r["fres"] - r["f_arg"], r["gamma"], r["phi_deg"], phi11, 100 * r["rmsG"]))
    L.append("")

# ------------------------------------------------------------------ A6: covariance vs replica scatter
L += ["## A6 — the fit's own uncertainty against the scatter of the three replicas\n", "| phase | n | sd(f_res) from the covariance, mean of three [Hz] | sd(f_res) over the three replicas [Hz] | sd(Γ) covariance [Hz] | sd(Γ) replicas [Hz] | sd(φ) replicas [°] |", "|---|---|---|---|---|---|---|"]
for liq, sets in SETS.items():
    for n in N:
        rr = [base[(s, n)][1] for s in sets]
        L.append("| %s | %d | %.1f | %.1f | %.1f | %.1f | %.2f |" % (liq, n, np.mean([r["sd_fres"] for r in rr]), np.std([r["fres"] for r in rr], ddof=1), np.mean([r["sd_gamma"] for r in rr]), np.std([r["gamma"] for r in rr], ddof=1), np.std([r["phi_deg"] for r in rr], ddof=1)))
L.append("\nThe covariance assumes independent residuals; the residual is structured (0.2–0.5 % of range, correlated over hundreds of hertz), so the replica scatter is the uncertainty to quote.\n")

# ------------------------------------------------------------------ A7: model variants
L += ["## A7 — model variants\n", "Fit on G with a linear background added (7 parameters), and — where the ±3Γ window is clipped by the sweep on the right — a symmetric window limited to the distance to the edge. Middle replicas; differences from the reference fit.\n",
      "| set | n | window clipped? | + linear background: Δf_res / ΔΓ / Δφ | symmetric window: half-width [Hz], Δf_res / ΔΓ / Δφ |", "|---|---|---|---|---|"]
for s, n in [(x, n) for x in ("air_1", "wat_1", "ipa_1") for n in N]:
    c, r = base[(s, n)]; fr, G, B = c["fr"], c["G"], c["B"]; mask = np.abs(fr - r["f_arg"]) <= 3 * r["gam_hh"]
    rl = fit(fr, G, B, mask, r["f_arg"], r["gam_hh"], "G", linear=True); clipped = r["f_arg"] + 3 * r["gam_hh"] > fr[-1]
    if clipped:
        hw = fr[-1] - r["f_arg"]; m2 = np.abs(fr - r["f_arg"]) <= hw; rs = fit(fr, G, B, m2, r["f_arg"], r["gam_hh"], "G"); sym = "%.0f, %+.0f / %+.0f / %+.1f" % (hw, rs["fres"] - r["fres"], rs["gamma"] - r["gamma"], rs["phi_deg"] - r["phi_deg"])
    else: sym = "—"
    L.append("| %s | %d | %s | %+.0f / %+.0f / %+.1f | %s |" % (s, n, "yes" if clipped else "no", rl["fres"] - r["fres"], rl["gamma"] - r["gamma"], rl["phi_deg"] - r["phi_deg"], sym))
L.append("")

# ------------------------------------------------------------------ A8: phi against n and the board delay
L += ["## A8 — φ against the overtone and the load\n", "| n | f [MHz] | φ air (mean ± sd of three) [°] | φ water [°] | φ isopropanol [°] | board delay 0.76–1.10 ns → [°] |", "|---|---|---|---|---|---|"]
for n in N:
    ph = {liq: [base[(s, n)][1]["phi_deg"] for s in sets] for liq, sets in SETS.items()}; fmhz = base[("air_1", n)][1]["fres"] / 1e6
    L.append("| %d | %.1f | %+.1f ± %.1f | %+.1f ± %.1f | %+.1f ± %.1f | %.1f–%.1f |" % (n, fmhz, np.mean(ph["air"]), np.std(ph["air"], ddof=1), np.mean(ph["water"]), np.std(ph["water"], ddof=1), np.mean(ph["ipa"]), np.std(ph["ipa"], ddof=1), 360e-9 * 0.76e-9 * 1e6 * fmhz * 1e6 / 1e6 * 1e3 / 1e3 if False else 0.76e-9 * fmhz * 1e6 * 360, 1.10e-9 * fmhz * 1e6 * 360))
L.append("\nφ grows with n but not linearly with frequency: 5 → 45 MHz gives ×9 in frequency and ×3 in φ. A pure delay of the board (0.76–1.10 ns measured on the short and load standards, 2026-09-03) would give 1.4–2.0° at 5 MHz and 12–18° at 45 MHz: the right order at the top, too small at the bottom, and it does not explain why air and liquid differ on n = 1 and 3.\n")

open(os.path.join(OUT, "psl_validation_tables.md"), "w").write("\n".join(L)); print("\n".join(L))
