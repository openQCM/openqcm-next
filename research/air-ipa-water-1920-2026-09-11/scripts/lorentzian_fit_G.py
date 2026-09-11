"""Lorentzian fit of the exact conductance, air / water / isopropanol, board 1920, 2026-09-11.

    cd software && PYTHONPATH=. python ../research/.../scripts/lorentzian_fit_G.py <data_root> <out_dir>

G is the process's own (Savitzky-Golay 51/3, spline s = 0.001, fold decision per sweep, exact inversion).
The fit is sweep_data/fit_admittance.fit2_lorentzian on the +-3 Gamma window around argmax G, model
G = Gmax / (1 + ((f^2 - fs^2)/(f*gamma))^2) + a + b*f, gamma = FULL width at half height; Gamma_L = gamma/2,
D_L = gamma/fs. Shifts are liquid minus air, same estimator on both, mean over the three replicas.
"""
import sys, os, json, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software")); sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py")); fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
proc = MultiscanProcess(None); N = (1, 3, 5, 7, 9)
SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
RHO_Q, MU_Q = 2648.0, 2.947e10; LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}; BAND = 3.0

def G_of(path):
    g = np.loadtxt(path); freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    fr = np.linspace(freq[0], freq[-1], points); Vm, Vp = sm(g[:, 1]), sm(g[:, 2])
    r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r)); decided, _ = proc._phase_fold_decision(fr, Vm, r)
    flip = bool(decided) if decided is not None else False; R, X = proc._RX_exact(Vm, r + (-rmin if flip else 0.0)); return fr, proc._G_exact(R, X)

def one(fr, G):
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth); mask = np.abs(fr - f_arg) <= BAND * gam
    lo = fa.fit2_lorentzian(fr, G, mask, f_arg, 2 * gam)
    return dict(f_arg=float(f_arg), gamma_hh=float(gam), fs=lo["fs"], sd_fs=lo["sd_fs"], gamma_L=lo["gamma"] / 2, sd_gamma_L=lo["sd_gamma"] / 2, D_L=lo["gamma"] / lo["fs"] * 1e6,
                rms_rel=lo["rms_rel"], n_fit=int(mask.sum()), clipped_right=bool(f_arg + BAND * gam > fr[-1]), clipped_left=bool(f_arg - BAND * gam < fr[0]), fit=lo, mask=mask)

res = {}; curves = {}
for liq, sets in SETS.items():
    for s in sets:
        for n in N:
            fr, G = G_of(os.path.join(ROOT, s, "g%d.txt" % n)); o = one(fr, G); res[(s, n)] = o; curves[(s, n)] = (fr, G)
def st(liq, n, key): v = np.array([res[(s, n)][key] for s in SETS[liq]], float); return v.mean(), v.std(ddof=1)

f0 = st("air", 1, "fs")[0]
L = ["### Lorentzian fit per phase, mean ± sd over the three replicas\n", "| phase | n | f_s [Hz] | Γ_L = gamma/2 [Hz] | D_L = gamma/f_s [ppm] | f_s − argmax G [Hz] | Γ_L / Γ half height | fit rms / Gmax [%] | points in ±3Γ | window clipped |", "|---|---|---|---|---|---|---|---|---|---|"]
for liq in ("air", "water", "ipa"):
    for n in N:
        fs, fs_s = st(liq, n, "fs"); gl, gl_s = st(liq, n, "gamma_L"); D, _ = st(liq, n, "D_L"); fa_, _ = st(liq, n, "f_arg"); gh, _ = st(liq, n, "gamma_hh"); rms, _ = st(liq, n, "rms_rel")
        clip = ", ".join(sorted({("right" if res[(s, n)]["clipped_right"] else "") + ("left" if res[(s, n)]["clipped_left"] else "") for s in SETS[liq]} - {""})) or "no"
        L.append("| %s | %d | %.0f ± %.0f | %.1f ± %.1f | %.1f | %+.0f | %.3f | %.2f | %d | %s |" % (liq, n, fs, fs_s, gl, gl_s, D, fs - fa_, gl / gh, 100 * rms, res[(SETS[liq][1], n)]["n_fit"], clip))
summary = {}
for liq in ("water", "ipa"):
    rho, eta = LIQ[liq]; kg = -np.sqrt(np.array(N)) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
    L += ["\n### air → %s: shifts from the Lorentzian fit, against Kanazawa–Gordon (25 °C), with argmax G beside\n" % liq,
          "| n | Δf_L [Hz] | Δf_L/Δf_KG | ΔΓ_L [Hz] | ΔΓ_L/ΔΓ_KG | ΔD_L [ppm] | **\\|Δf_L\\|/ΔΓ_L** | Δf argmax [Hz] | ΔΓ half height [Hz] | \\|Δf\\|/ΔΓ argmax |", "|---|---|---|---|---|---|---|---|---|---|"]
    summary[liq] = {}
    for i, n in enumerate(N):
        dfL = st(liq, n, "fs")[0] - st("air", n, "fs")[0]; dGL = st(liq, n, "gamma_L")[0] - st("air", n, "gamma_L")[0]; dDL = st(liq, n, "D_L")[0] - st("air", n, "D_L")[0]
        dfa = st(liq, n, "f_arg")[0] - st("air", n, "f_arg")[0]; dGh = st(liq, n, "gamma_hh")[0] - st("air", n, "gamma_hh")[0]
        sd = np.hypot(st(liq, n, "fs")[1], st("air", n, "fs")[1])
        summary[liq][n] = dict(dfL=dfL, dGL=dGL, ratioL=abs(dfL) / dGL, ratio_arg=abs(dfa) / dGh, df_kg=dfL / kg[i], dG_kg=dGL / abs(kg[i]), sd_ratio=sd / dGL, dfa_kg=dfa / kg[i], dGh_kg=dGh / abs(kg[i]))
        L.append("| %d | %.0f ± %.0f | %.2f | %.0f | %.2f | %.1f | **%.2f** | %.0f | %.0f | %.2f |" % (n, dfL, sd, dfL / kg[i], dGL, dGL / abs(kg[i]), dDL, abs(dfL) / dGL, dfa, dGh, abs(dfa) / dGh))
open(os.path.join(OUT, "lorentz_tables.md"), "w").write("\n".join(L)); print("\n".join(L))

# figure 1: G with the Lorentzian overlaid, middle replica, 5 x 3
fig, ax = plt.subplots(5, 3, figsize=(16, 17))
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        fr, G = curves[(s, n)]; o = res[(s, n)]; m = o["mask"]; a = ax[i, j]; x = fr - o["f_arg"]; w = np.abs(x) <= 4.5 * o["gamma_hh"]
        a.plot(x[w], G[w] * 1e3, color="#555", lw=1.0, label="G exact (chain)")
        a.plot(x[m], fa.fit2_curve(fr[m], {"fit2": o["fit"], "fs_seed": o["f_arg"]}) * 1e3, color="#2ca02c", lw=1.6, ls="--", label="Lorentzian, ±3Γ window")
        a.axvline(0, color="#d62728", lw=1, label="argmax G"); a.axvline(o["fs"] - o["f_arg"], color="#2ca02c", lw=1, label="f_s Lorentz %+.0f Hz" % (o["fs"] - o["f_arg"]))
        a.axvspan(-o["gamma_hh"], o["gamma_hh"], color="grey", alpha=0.1, label="±Γ half height")
        a.set_title("%s, n = %d: Γ_hh %.0f Hz, Γ_L %.0f Hz, rms %.2f%% of Gmax%s" % (liq, n, o["gamma_hh"], o["gamma_L"], 100 * o["rms_rel"], ", window clipped" if o["clipped_right"] or o["clipped_left"] else ""), fontsize=8.5)
        a.set_xlabel("f − argmax G [Hz]"); a.set_ylabel("G [mS]"); a.grid(alpha=0.25); a.legend(fontsize=7, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "G_lorentz_fit.png"), dpi=95); plt.close(fig)

# figure 2: residuals (G - fit) in the window, middle replica
fig, ax = plt.subplots(5, 3, figsize=(16, 15))
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        fr, G = curves[(s, n)]; o = res[(s, n)]; m = o["mask"]; a = ax[i, j]
        a.plot(fr[m] - o["f_arg"], (G[m] - fa.fit2_curve(fr[m], {"fit2": o["fit"], "fs_seed": o["f_arg"]})) / o["fit"]["Gmax"] * 100, color="#2ca02c", lw=1)
        a.axhline(0, color="k", lw=0.6); a.axvline(0, color="#d62728", lw=0.8); a.set_title("%s, n = %d: residual, %% of fitted Gmax" % (liq, n), fontsize=9); a.set_xlabel("f − argmax G [Hz]"); a.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "G_lorentz_residuals.png"), dpi=95); plt.close(fig)

# figure 3: ratios vs n, Lorentz against argmax
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
for liq, c, mk in (("water", "#2a78d6", "o"), ("ipa", "#eb6834", "s")):
    ax[0].errorbar(N, [summary[liq][n]["ratioL"] for n in N], yerr=[summary[liq][n]["sd_ratio"] for n in N], color=c, marker=mk, capsize=3, label="%s, Lorentzian" % liq)
    ax[0].plot(N, [summary[liq][n]["ratio_arg"] for n in N], color=c, marker=mk, mfc="none", ls=":", label="%s, argmax + half height" % liq)
    ax[1].plot(N, [summary[liq][n]["df_kg"] for n in N], color=c, marker=mk, label="%s: Δf_L/Δf_KG" % liq); ax[1].plot(N, [summary[liq][n]["dG_kg"] for n in N], color=c, marker=mk, mfc="none", ls=":", label="%s: ΔΓ_L/ΔΓ_KG" % liq)
for a, yl, tt in ((ax[0], "|Δf| / ΔΓ", "Lorentzian fit against argmax + half height"), (ax[1], "measured / Kanazawa–Gordon", "Lorentzian shifts over the theory")):
    a.axhline(1, color="k", ls="--", lw=0.8); a.set_xticks(N); a.set_xlabel("overtone n"); a.set_ylabel(yl); a.set_title(tt, fontsize=10); a.legend(fontsize=8); a.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "lorentz_ratios.png"), dpi=110); plt.close(fig)
json.dump({"%s_%d" % (k[0], k[1]): {kk: vv for kk, vv in v.items() if kk not in ("fit", "mask")} for k, v in res.items()}, open(os.path.join(OUT, "lorentz_results.json"), "w"), indent=1)
