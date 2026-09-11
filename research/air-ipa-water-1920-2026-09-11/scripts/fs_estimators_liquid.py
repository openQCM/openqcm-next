"""Four f_s estimators on the same exact G, air / water / isopropanol, board 1920, 2026-09-11.

    PYTHONPATH=software python fs_estimators_liquid.py <data_root> <out_dir>

<data_root> holds air_0..2, wat_0..2, ipa_0..2 (g<n>.txt dumps copied by hand on each
plateau of one acquisition) and the two datalogs of that acquisition. The chain is the
process's own -- MultiscanProcess methods, core.resonance, the offline fits of
sweep_data/fit_admittance.py -- nothing is re-implemented here. The fold decision is taken
on each sweep alone (the process latches it over two).
"""
import sys, os, json, glob, importlib.util, datetime
import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software"))
sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py"))
fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)

ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
N = (1, 3, 5, 7, 9); EST = ("argmax", "midpoint", "lorentz", "circle")
BAND = Constants.IMPEDANCE_PANEL_BAND_GAMMA            # +-3 Gamma, the live panel's window
RHO_Q, MU_Q = 2648.0, 2.947e10                          # as scripts/kanazawa_gordon.py
LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}
proc = MultiscanProcess(None)


def chain(path):
    """The published chain on one g<n>.txt: returns the axis, G, Y = G + jB and the fold info."""
    g = np.loadtxt(path); freq, Vmag, Vph = g[:, 0], g[:, 1], g[:, 2]
    points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    fr = np.linspace(freq[0], freq[-1], points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    Vmag_fit, Vph_fit = sm(Vmag), sm(Vph)
    folded = proc._phase_raw_V_phase(Vph_fit); p_min = float(np.nanmin(folded))
    decided, info = proc._phase_fold_decision(fr, Vmag_fit, folded)
    has_fold = bool(decided) if decided is not None else proc._phase_offset_fold(folded)[1]
    offset = -p_min if has_fold else 0.0
    corr = folded + offset
    R, X = proc._RX_exact(Vmag_fit, corr); G = proc._G_exact(R, X)
    signed = np.array(corr, dtype=float, copy=True)
    if has_fold:
        i = int(np.nanargmin(np.abs(corr))); signed[i:] = -signed[i:]
    Rb, Xb = proc._RX_exact(Vmag_fit, signed); B = proc._B_exact(Rb, Xb)
    return fr, G, G + 1j * B, dict(fold=has_fold, delta=offset, depth=info.get("depth"), why=info.get("why"), p_min=p_min)


def estimators(fr, G, Y):
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth)
    two_sided = band.f_left is not None and band.f_right is not None
    f_mid = 0.5 * (band.f_left + band.f_right) if two_sided else float("nan")
    mask = np.abs(fr - f_arg) <= BAND * gam
    lo = fa.fit2_lorentzian(fr, G, mask, f_arg, 2.0 * gam)        # gamma0 is the FULL width
    ci = fa.fit1_circle(fr, Y, mask)
    return dict(
        argmax=dict(fs=float(f_arg), gamma=float(gam)),
        midpoint=dict(fs=float(f_mid), gamma=float(gam)),
        lorentz=dict(fs=lo["fs"], gamma=lo["gamma"] / 2.0, sd_fs=lo["sd_fs"], rms_rel=lo["rms_rel"], ok=lo["success"]),
        circle=dict(fs=ci["fs"], gamma=ci["gamma"] / 2.0, sd_fs=ci["sd_fs"], rms_rel=ci["rms_rel"], theta_deg=np.degrees(ci["theta"]), R1=ci["R1"]),
        band=dict(f_left=band.f_left, f_right=band.f_right, two_sided=two_sided, n_mask=int(mask.sum()),
                  mask_clipped_right=bool(f_arg + BAND * gam > fr[-1]), mask_clipped_left=bool(f_arg - BAND * gam < fr[0])))


# ------------------------------------------------------------------ datalog, for the chain check
csv = sorted(glob.glob(os.path.join(ROOT, "*_multi.csv")))[0]
import pandas as pd
log = pd.read_csv(csv); log["t"] = pd.to_datetime(log.Date + " " + log.Time)


def published_at(mtime, n):
    """Published f (argmax) and D at the datalog row nearest the dump's write time."""
    t0 = pd.Timestamp(datetime.datetime.fromtimestamp(mtime)); i = int((log.t - t0).abs().idxmin())
    k = N.index(n); return float(log.loc[i, "Frequency_%d" % k]), float(log.loc[i, "Dissipation_%d" % k]), float((log.t[i] - t0).total_seconds())


# ------------------------------------------------------------------ run
res = {}; curves = {}
for liq, sets in SETS.items():
    for s in sets:
        res[s] = {}
        for n in N:
            p = os.path.join(ROOT, s, "g%d.txt" % n)
            fr, G, Y, fold = chain(p); e = estimators(fr, G, Y)
            fpub, Dpub, dt = published_at(os.path.getmtime(p), n)
            e["fold"] = fold; e["published"] = dict(f=fpub, D_ppm=Dpub, dt_s=dt, D_offline_ppm=2e6 * e["argmax"]["gamma"] / e["argmax"]["fs"])
            e["time"] = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%H:%M:%S")
            res[s][n] = e; curves[(s, n)] = (fr, G)
            print("%-6s n=%d %s fold=%-5s delta=%+6.2f depth=%s | argmax %.0f  mid %+7.1f  lor %+7.1f  cir %+7.1f | Gamma hh %.1f L %.1f C %.1f | two_sided=%s clipR=%s | pub f %.0f (d=%+.0f) D %.1f vs %.1f" % (
                s, n, e["time"], fold["fold"], fold["delta"], ("%.2f" % fold["depth"]) if fold["depth"] is not None else "n/a",
                e["argmax"]["fs"], e["midpoint"]["fs"] - e["argmax"]["fs"], e["lorentz"]["fs"] - e["argmax"]["fs"], e["circle"]["fs"] - e["argmax"]["fs"],
                e["argmax"]["gamma"], e["lorentz"]["gamma"], e["circle"]["gamma"], e["band"]["two_sided"], e["band"]["mask_clipped_right"],
                fpub, fpub - e["argmax"]["fs"], Dpub, e["published"]["D_offline_ppm"]))

# ------------------------------------------------------------------ air reference, shifts, Kanazawa-Gordon
def stat(liq, est, n, key):
    v = np.array([res[s][n][est][key] for s in SETS[liq]], float); return v.mean(), v.std(ddof=1), v


f0 = stat("air", "argmax", 1, "fs")[0]
kg = {}
for liq, (rho, eta) in LIQ.items():
    df = -np.sqrt(np.array(N)) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
    kg[liq] = dict(df=df, dGamma=np.abs(df))          # Newtonian: dGamma = |df|

summary = {"f0_air_argmax": f0, "kg": {k: dict(df=v["df"].tolist()) for k, v in kg.items()}, "shifts": {}}
lines = []
for liq in ("water", "ipa"):
    rho, eta = LIQ[liq]
    lines.append("\n### %s (rho = %.1f kg/m3, eta = %.3f mPa s at 25 degC), mean +- sd over three sweeps on the plateau\n" % (liq.upper(), rho, eta * 1e3))
    lines.append("| n | estimator | f air [Hz] | f liquid [Hz] | df [Hz] | df / df_KG | Gamma air [Hz] | Gamma liquid [Hz] | dGamma [Hz] | dGamma / dGamma_KG | **abs(df) / dGamma** |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    summary["shifts"][liq] = {}
    for i, n in enumerate(N):
        for est in EST:
            fa_m, fa_s, _ = stat("air", est, n, "fs"); fl_m, fl_s, _ = stat(liq, est, n, "fs")
            ga_m, ga_s, _ = stat("air", est, n, "gamma"); gl_m, gl_s, _ = stat(liq, est, n, "gamma")
            df = fl_m - fa_m; dG = gl_m - ga_m; ratio = abs(df) / dG if dG else float("nan")
            summary["shifts"][liq].setdefault(str(n), {})[est] = dict(f_air=fa_m, f_air_sd=fa_s, f_liq=fl_m, f_liq_sd=fl_s, df=df, gamma_air=ga_m, gamma_liq=gl_m, dGamma=dG,
                                                                     ratio=ratio, df_over_kg=df / kg[liq]["df"][i], dG_over_kg=dG / kg[liq]["dGamma"][i])
            lines.append("| %d | %s | %.0f ± %.0f | %.0f ± %.0f | %.0f | %.2f | %.1f | %.0f ± %.0f | %.0f | %.2f | **%.2f** |" % (
                n, est, fa_m, fa_s, fl_m, fl_s, df, df / kg[liq]["df"][i], ga_m, gl_m, gl_s, dG, dG / kg[liq]["dGamma"][i], ratio))
open(os.path.join(OUT, "tables.md"), "w").write("\n".join(lines)); print("\n".join(lines))
json.dump(dict(results={s: {str(n): e for n, e in d.items()} for s, d in res.items()}, summary=summary), open(os.path.join(OUT, "fs_estimators_liquid.json"), "w"), indent=1, default=float)

# ------------------------------------------------------------------ figures
COL = dict(argmax="#d62728", midpoint="#1f77b4", lorentz="#2ca02c", circle="#9467bd"); MK = dict(argmax="v", midpoint="o", lorentz="s", circle="D")
fig, ax = plt.subplots(5, 3, figsize=(15, 17))
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        fr, G = curves[(s, n)]; e = res[s][n]; f_arg = e["argmax"]["fs"]; gam = e["argmax"]["gamma"]
        a = ax[i, j]; w = np.abs(fr - f_arg) <= 4 * gam
        a.plot((fr[w] - f_arg), G[w] * 1e3, "k-", lw=0.8)
        for est in EST:
            fs = e[est]["fs"]
            if np.isfinite(fs):
                a.axvline(fs - f_arg, color=COL[est], lw=1.2, ls="--" if est != "argmax" else "-", label="%s %+.0f Hz" % (est, fs - f_arg))
        if e["band"]["f_left"] is not None and e["band"]["f_right"] is not None:
            a.axvspan(e["band"]["f_left"] - f_arg, e["band"]["f_right"] - f_arg, color="grey", alpha=0.12, label="half height, 2Γ = %.0f Hz" % (2 * gam))
        a.set_title("%s, n = %d, %s  (fold %s, δ %+.1f°)" % (liq, n, e["time"], e["fold"]["fold"], e["fold"]["delta"]), fontsize=9)
        a.set_xlabel("f − f_argmax [Hz]"); a.set_ylabel("G [mS]"); a.legend(fontsize=7, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "G_markers.png"), dpi=100); plt.close(fig)

fig, ax = plt.subplots(2, 2, figsize=(12, 8.5))
for j, liq in enumerate(("water", "ipa")):
    for est in EST:
        r = [summary["shifts"][liq][str(n)][est]["ratio"] for n in N]
        d = [summary["shifts"][liq][str(n)][est]["df_over_kg"] for n in N]
        # repeatability: sd of the three liquid sweeps on df, propagated to the ratio
        sd = [stat(liq, est, n, "fs")[1] / summary["shifts"][liq][str(n)][est]["dGamma"] for n in N]
        ax[0, j].errorbar(N, r, yerr=sd, marker=MK[est], color=COL[est], capsize=3, label=est)
        ax[1, j].plot(N, d, marker=MK[est], color=COL[est], label=est)
    for k, yl in ((0, "|Δf| / ΔΓ  (Newtonian: 1)"), (1, "Δf / Δf_KG  (theory: 1)")):
        ax[k, j].axhline(1.0, color="k", ls="--", lw=0.8); ax[k, j].set_xticks(N); ax[k, j].set_xlabel("overtone n"); ax[k, j].set_ylabel(yl); ax[k, j].legend(fontsize=8)
        ax[k, j].set_title("%s: %s" % (liq, "|Δf|/ΔΓ per estimator (bars: sd over 3 sweeps)" if k == 0 else "Δf against Kanazawa–Gordon"))
fig.tight_layout(); fig.savefig(os.path.join(OUT, "ratio_vs_n.png"), dpi=110); plt.close(fig)
print("written", OUT)
