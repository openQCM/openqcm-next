# -*- coding: utf-8 -*-
"""
make_figures_v2.py — figures of manuscript v2 (main text: ../figures_v2/figN_*.png|pdf; SI: ../figures_v2/si/figSN_*).
Inputs: results/v2/asis/*.csv (run_v2.py), results/sweeps_asis.csv, results/glucose_sweeps_asis.csv, the raw dumps,
the datalogs, results/forward_model.csv. Provenance: results/v2/figure_provenance_v2.md.
Templates: T4 = time traces, two stacked panels, Δf_n/n (top) and ΔΓ_n/n (bottom), one curve per overtone;
           T5 = Δf_n/n and ΔΓ_n/n against n with the Kanazawa–Gordon curves. KG-1 = ΔΓ_n/(−Δf_n) against n.
"""
import os, json, math
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import qcmchain as q, data
import make_figures as mf          # v1 figure functions reused for the SI (raw sweeps, G/B locus, fits, repeatability, forward model)

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results"); V2 = os.path.join(R, "v2", "asis")
FIG = os.path.normpath(os.path.join(HERE, "..", "figures_v2")); SI = os.path.join(FIG, "si"); os.makedirs(SI, exist_ok=True)
C = mf.C; TXT, TXT2, GRID = mf.TXT, mf.TXT2, mf.GRID
NC = {1: C[0], 3: C[1], 5: C[2], 7: C[3], 9: C[6]}                      # one colour per overtone
MED = {"air": "#9a9a9a", "water": C[0], "ipa": C[2], "gluc05": C[3], "gluc075": C[1], "gluc10": C[7]}
MEDL = {"air": "air", "water": "water", "ipa": "isopropanol", "gluc05": "glucose 5 % w/v", "gluc075": "glucose 7.5 % w/v", "gluc10": "glucose 10 % w/v"}
N = [1, 3, 5, 7, 9]
PROV = []

PH = pd.read_csv(os.path.join(V2, "phases.csv")); SH = pd.read_csv(os.path.join(V2, "shifts.csv")); K2 = pd.read_csv(os.path.join(V2, "kg2_slopes.csv"))
BIAS = pd.read_csv(os.path.join(V2, "bias_per_overtone.csv")); PHI = pd.read_csv(os.path.join(V2, "phi_all.csv"))
XR = pd.read_csv(os.path.join(V2, "glucose_xrel.csv")); RES = pd.read_csv(os.path.join(V2, "glucose_resolution.csv")); XC = pd.read_csv(os.path.join(V2, "glucose_xrel_vs_conc.csv"))
T4D = pd.read_csv(os.path.join(V2, "t4_ds2_datalog.csv")); T4P = pd.read_csv(os.path.join(V2, "t4_sweep_points.csv"))
SW2 = pd.read_csv(os.path.join(R, "sweeps_asis.csv")); SW3 = pd.read_csv(os.path.join(R, "glucose_sweeps_asis.csv"))
SUMM = json.load(open(os.path.join(V2, "summary.json")))
KGC = SUMM["kg_coef"]; SQ = SUMM["sqrt_rhoeta"]


def save(fig, name, source, params, si=False):
    d = SI if si else FIG
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(d, "%s.%s" % (name, ext)), bbox_inches="tight")
    plt.close(fig)
    PROV.append(dict(figure=("si/" if si else "") + name, source=source, script="research/paper/analysis/make_figures_v2.py", params=params))
    print("wrote", name)


def sel(ds, liq, est):
    return SH[(SH.dataset == ds) & (SH.liquid == liq) & (SH.estimator == est)].sort_values("n")


# ------------------------------------------------------------------ Fig 2: G(f), the two estimators, residuals
def fig2_estimators():
    dumps, _ = data.dumps_0911()
    cases = (("air_1", 5), ("wat_1", 5))
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 4.3), sharex="col", gridspec_kw=dict(height_ratios=[2.2, 1]))
    for j, (s, n) in enumerate(cases):
        f, vm, vp = dumps[(s, n)]
        c = q.chain(f, vm, vp); e = q.argmax_halfheight(c["f"], c["G"]); p = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"]); sl = q.fit_symmetric(c["f"], c["G"], e["f_max"], e["gamma_hh"], linear=True)
        idx = p["idx"]; F = c["f"][idx]; G = 1e3 * c["G"][idx]; x = (F - p["fres"]) / 1e3
        ph = "air" if s.startswith("air") else "water"
        ax[0, j].plot(x, G, ".", ms=2, color=TXT2, label="reconstructed G")
        ax[0, j].plot(x, 1e3 * q.rotated_lorentzian(F, p["fres"], p["gamma"], p["phi_deg"], p["gmax"], p["g_off"]), color=C[2], label="P: phase-shifted Lorentzian")
        d = sl["fres"] - F; gs = sl["gamma"]
        ax[0, j].plot(x, 1e3 * (sl["gmax"] * gs * gs / (d * d + gs * gs) + sl["g_off"]), color=C[1], ls="--", lw=1, label="symmetric Lorentzian (+ linear bg)")
        ax[0, j].axvline(0, color=C[2], lw=0.8); ax[0, j].axvline((e["f_max"] - p["fres"]) / 1e3, color=TXT, lw=0.9, ls=":", label="A: maximum of G")
        # half-height crossings of the A estimator
        for fx in (e["f_left"], e["f_right"]):
            ax[0, j].axvline((fx - p["fres"]) / 1e3, color=TXT, lw=0.6, ls=":", alpha=0.6)
        ax[0, j].set_title("%s, n = %d: Γ = %.0f Hz, φ = %.1f°\nf_Gmax − f_res = %+.0f Hz" % (MEDL[ph], n, p["gamma"], p["phi_deg"], e["f_max"] - p["fres"]), fontsize=8)
        ax[1, j].plot(x, 100 * sl["residual"], color=C[1], lw=0.9, label="symmetric"); ax[1, j].plot(x, 100 * p["residual"], color=C[2], lw=0.9, label="phase-shifted")
        ax[1, j].axhline(0, color=TXT2, lw=0.6); ax[1, j].set_xlabel("f − f_res [kHz]"); ax[1, j].set_ylim(-8, 8)
    ax[0, 0].set_ylabel("G [mS]"); ax[1, 0].set_ylabel("residual [% of range]"); ax[0, 0].legend(fontsize=6.3, loc="upper left"); ax[1, 1].legend(fontsize=6.3, loc="upper right")
    fig.tight_layout()
    save(fig, "fig02_estimators_on_G", "sweep_dumps_2026-09-11.npz (air_1/g5, wat_1/g5)", "chain SG 51/3 + spline; fits on ±3 Γ_hh around max G; dotted = max of G and its half-height crossings; solid = f_res of P")


# ------------------------------------------------------------------ Fig 3: T4 time traces, DS-2 (datalog + P points) and DS-3 (sweep instants)
def fig3_t4():
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 5.0), sharex="col")
    # DS-2
    t0 = pd.to_datetime(T4D.t).min()
    tt = (pd.to_datetime(T4D.t) - t0).dt.total_seconds() / 60
    for n in N:
        s = T4D[T4D.n == n]
        ax[0, 0].plot(tt[s.index], s.df_over_n, ".", ms=1.8, color=NC[n], alpha=0.55)
        ax[1, 0].plot(tt[s.index], s.dG_over_n, ".", ms=1.8, color=NC[n], alpha=0.55)
    pts = T4P[(T4P.dataset == "DS-2") & (T4P.estimator == "psl")]
    tp = (pd.to_datetime(pts.mtime) - t0).dt.total_seconds() / 60
    for n in N:
        s = pts[pts.n == n]
        ax[0, 0].plot(tp[s.index], s.df_over_n, "o", ms=4.5, color=NC[n], mec="white", mew=0.6, label="n = %d" % n)
        ax[1, 0].plot(tp[s.index], s.dG_over_n, "o", ms=4.5, color=NC[n], mec="white", mew=0.6)
    for x0, x1, ph in ((0, 37.2, "air"), (37.3, 61.0, "water"), (61.1, 75.3, "ipa")):
        for a in ax[:, 0]: a.axvspan(x0, x1, color=MED[ph], alpha=0.08, lw=0)
    ax[0, 0].set_title("DS-2 (board 1920): air → water → isopropanol", fontsize=8.5)
    ax[0, 0].set_ylabel("Δf_n / n [Hz]"); ax[1, 0].set_ylabel("ΔΓ_n / n [Hz]"); ax[1, 0].set_xlabel("time [min]")
    ax[0, 0].legend(fontsize=6.5, ncol=5, loc="lower left", handletextpad=0.2, columnspacing=0.8)
    ax[0, 0].text(0.02, 0.96, "dots: instrument datalog, A (max of G, half height)\ncircles: P (phase-shifted Lorentzian) on the dumped sweeps", transform=ax[0, 0].transAxes, fontsize=6.3, va="top")
    # DS-3
    p3 = T4P[T4P.dataset == "DS-3"].copy(); t03 = pd.to_datetime(p3.mtime).min(); p3["tm"] = (pd.to_datetime(p3.mtime) - t03).dt.total_seconds() / 60
    for n in N:
        for est, mk, mfc in (("argmax_hh", "v", "none"), ("psl", "o", None)):
            s = p3[(p3.n == n) & (p3.estimator == est)].sort_values("tm")
            kw = dict(ms=4.5 if est == "psl" else 4, color=NC[n], mfc=(mfc if mfc else NC[n]), mec=("white" if est == "psl" else NC[n]), mew=0.6 if est == "psl" else 0.8, lw=0.6 if est == "psl" else 0, alpha=1 if est == "psl" else 0.7)
            ax[0, 1].plot(s.tm, s.df_over_n, mk + ("-" if est == "psl" else ""), **kw); ax[1, 1].plot(s.tm, s.dG_over_n, mk + ("-" if est == "psl" else ""), **kw)
    bounds = p3.groupby("phase").tm.agg(["min", "max"])
    order = ["air", "water", "gluc05", "gluc075", "gluc10"]
    for k, ph in enumerate(order):
        x0 = bounds.loc[ph, "min"] - 1.5; x1 = (bounds.loc[order[k + 1], "min"] - 1.5) if k + 1 < len(order) else bounds.loc[ph, "max"] + 1.5
        for a in ax[:, 1]: a.axvspan(x0, x1, color=MED[ph], alpha=0.08, lw=0)
        ax[0, 1].text(0.5 * (x0 + x1), ax[0, 1].get_ylim()[1] if False else -40, MEDL[ph].replace("glucose ", "gl. ").replace(" w/v", ""), fontsize=6, ha="center", va="top", color=TXT2)
    ax[0, 1].set_title("DS-3 (second instrument): air → water → glucose", fontsize=8.5)
    ax[1, 1].set_xlabel("time [min]"); ax[0, 1].plot([], [], "v", mfc="none", color=TXT, label="A"); ax[0, 1].plot([], [], "o", color=TXT, label="P"); ax[0, 1].legend(fontsize=6.5, loc="lower left")
    ax[0, 1].text(0.98, 0.04, "three dumped sweep sets per plateau", transform=ax[0, 1].transAxes, fontsize=6.3, va="bottom", ha="right")
    fig.tight_layout()
    save(fig, "fig03_T4_time_traces", "DS-2: 2026-09-11_12-14-42_multi.csv (A live) + sweep_dumps_2026-09-11.npz (P); DS-3: sweep_raw_2024-05-29.npz",
         "shifts relative to the air plateau of the same estimator (DS-2 datalog: last 10 min of air; sweeps: mean of the three air dumps); ΔΓ from the datalog = D·1e-6·f/2")


# ------------------------------------------------------------------ Fig 4: Exp. 1 — T5 + KG-1 for A and P, DS-2 water and DS-3 water
def fig4_exp1():
    fig, ax = plt.subplots(3, 2, figsize=(7.2, 6.6), sharex=True)
    for j, ds in enumerate(("DS-2", "DS-3")):
        s0 = sel(ds, "water", "psl")
        ax[0, j].plot(s0.n, -s0.df_KG / s0.n, color=TXT2, lw=1.2, label="Kanazawa–Gordon, water 25 °C"); ax[1, j].plot(s0.n, -s0.df_KG / s0.n, color=TXT2, lw=1.2)
        ax[2, j].axhline(1.0, color=TXT2, lw=1.2)
        for est, mk, mfc, lab, dx in (("argmax_hh", "v", "none", "A: max of G + half height", -0.12), ("psl", "o", None, "P: phase-shifted Lorentzian", 0.12)):
            s = sel(ds, "water", est); col = MED["water"]
            kw = dict(ms=5, color=col, mfc=(mfc if mfc else col), mew=0.9, lw=0.8, capsize=0)
            ax[0, j].errorbar(s.n + dx, -s.df_over_n, yerr=s.df_sd / s.n, fmt=mk, label=lab, **kw)
            ax[1, j].errorbar(s.n + dx, s.dG_over_n, yerr=s.dG_sd / s.n, fmt=mk, **kw)
            ax[2, j].errorbar(s.n + dx, s.r_KG1, yerr=s.r_KG1_sd, fmt=mk, **kw)
        ax[0, j].set_title("%s: air → water" % ({"DS-2": "DS-2, board 1920", "DS-3": "DS-3, second instrument"}[ds]), fontsize=8.5)
        ax[2, j].set_xlabel("overtone order n"); ax[2, j].set_xticks(N); ax[2, j].set_ylim(0.6, 1.35)
    ax[0, 0].set_ylabel("−Δf_n / n [Hz]"); ax[1, 0].set_ylabel("ΔΓ_n / n [Hz]"); ax[2, 0].set_ylabel("KG-1: ΔΓ_n / (−Δf_n)")
    ax[0, 0].legend(fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig04_exp1_T5_KG1", "results/v2/asis/shifts.csv (DS-2 water, DS-3 water; A and P)", "T5 (rows 1–2) and KG-1 ratio (row 3); error bars: quadrature sd of the two plateaus (÷n), ratio sd propagated")


# ------------------------------------------------------------------ Fig 5: the bias of the conductance maximum, 120 sweeps
def fig5_bias():
    p = pd.concat([SW2.assign(dataset="DS-2"), SW3.assign(dataset="DS-3")]); p = p[p.estimator == "psl"]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1))
    for ds, mk in (("DS-2", "o"), ("DS-3", "s")):
        for ph in ("air", "water", "ipa", "gluc05", "gluc075", "gluc10"):
            s = p[(p.dataset == ds) & (p.phase == ph)]
            if s.empty: continue
            kw = dict(ms=4, color=MED[ph], mec="white", mew=0.5) if ds == "DS-2" else dict(ms=3.8, color=MED[ph], mfc="none", mew=0.8)
            ax[0].plot(s.bias_pred, s.bias_meas, mk, **kw); ax[1].plot(s.gamma, (s.bias_meas - s.bias_pred) / s.gamma, mk, **kw)
    lim = [-760, 60]; ax[0].plot(lim, lim, color=TXT2, lw=0.8); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
    ax[0].set_xlabel("Γ tan(φ/2) from the P fit [Hz]"); ax[0].set_ylabel("f_Gmax − f_res [Hz]"); ax[0].set_title("bias of the conductance maximum, 45 + 75 sweeps", fontsize=8.5)
    ax[1].axhline(0, color=TXT2, lw=0.8); ax[1].set_xscale("log"); ax[1].set_xlabel("Γ (P) [Hz]"); ax[1].set_ylabel("(measured − predicted) / Γ"); ax[1].set_title("residual of Eq. (bias)", fontsize=8.5)
    for ph in ("air", "water", "ipa", "gluc05", "gluc075", "gluc10"): ax[0].plot([], [], "s", color=MED[ph], label=MEDL[ph])
    ax[0].plot([], [], "o", color=TXT, label="DS-2 (filled)"); ax[0].plot([], [], "s", mfc="none", color=TXT, label="DS-3 (open)")
    ax[0].legend(fontsize=5.8, loc="upper left", ncol=2)
    fig.tight_layout()
    save(fig, "fig05_argmax_bias", "results/sweeps_asis.csv, results/glucose_sweeps_asis.csv (psl rows)", "bias_meas = f_Gmax − f_res(P); bias_pred = Γ_P tan(φ_P/2)")


# ------------------------------------------------------------------ Fig 6: Exp. 2 — DS-2 water + isopropanol, P: T5, KG-1, KG-3
def fig6_exp2():
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.9))
    for liq, mk in (("water", "o"), ("ipa", "s")):
        s = sel("DS-2", liq, "psl"); col = MED[liq]
        ax[0].plot(s.n, -s.df_KG / s.n, color=col, lw=1.0, alpha=0.6)
        ax[0].errorbar(s.n - 0.1, -s.df_over_n, yerr=s.df_sd / s.n, fmt=mk, ms=4.5, color=col, mec="white", mew=0.5, lw=0.8, capsize=0, label="−Δf/n, %s" % MEDL[liq])
        ax[0].errorbar(s.n + 0.1, s.dG_over_n, yerr=s.dG_sd / s.n, fmt=mk, ms=4.5, color=col, mfc="none", mew=0.9, lw=0.8, capsize=0, label="ΔΓ/n, %s" % MEDL[liq])
        ax[1].errorbar(s.n, s.r_KG1, yerr=s.r_KG1_sd, fmt=mk + "-", ms=4.5, color=col, mec="white", mew=0.5, lw=0.8, capsize=0, label=MEDL[liq])
        x = SQ[liq]
        for n in N:
            r = s[s.n == n].iloc[0]
            ax[2].plot(x, -r.df_over_sqrtn, "o", ms=4.5, color=NC[n], mec="white", mew=0.5); ax[2].plot(x, r.dG_over_sqrtn, "o", ms=4.5, color=NC[n], mfc="none", mew=0.9)
    xx = np.array([0, 1.35]); ax[2].plot(xx, KGC["DS2"] * xx, color=TXT2, lw=1.0, label="Kanazawa–Gordon")
    ax[2].plot(0, 0, "o", color=MED["air"], ms=5)
    ax[2].set_xlabel("√(ρη) at 25 °C [kg m⁻² s⁻¹ᐟ²]"); ax[2].set_ylabel("−Δf_n/√n (filled), ΔΓ_n/√n (open) [Hz]"); ax[2].set_xlim(-0.05, 1.4); ax[2].set_ylim(-30, 1000)
    for n in N: ax[2].plot([], [], "o", color=NC[n], label="n = %d" % n)
    ax[2].legend(fontsize=5.8, loc="upper left"); ax[2].set_title("KG-3", fontsize=8.5)
    ax[0].set_xlabel("overtone order n"); ax[0].set_xticks(N); ax[0].set_ylabel("[Hz]"); ax[0].legend(fontsize=5.8); ax[0].set_title("T5 (lines: KG)", fontsize=8.5)
    ax[1].axhline(1, color=TXT2, lw=1.0); ax[1].set_xlabel("overtone order n"); ax[1].set_xticks(N); ax[1].set_ylabel("ΔΓ_n / (−Δf_n)"); ax[1].set_ylim(0.85, 1.35); ax[1].legend(fontsize=6.5); ax[1].set_title("KG-1", fontsize=8.5)
    fig.tight_layout()
    save(fig, "fig06_exp2_water_ipa", "results/v2/asis/shifts.csv (DS-2, P)", "KG-3 panel: x = √(ρη) with water 997.05 kg/m³ · 0.890 mPa s and isopropanol 781.0 · 2.038 at 25 °C; air at the origin")


# ------------------------------------------------------------------ Fig 7: Exp. 3 — DS-3 water + glucose, P: T5, KG-1, KG-3 (relative), resolution
def fig7_exp3():
    fig, ax = plt.subplots(1, 4, figsize=(7.6, 2.9))
    liqs = ("water", "gluc05", "gluc075", "gluc10"); mks = {"water": "o", "gluc05": "s", "gluc075": "D", "gluc10": "^"}
    s0 = sel("DS-3", "water", "psl"); ax[0].plot(s0.n, -s0.df_KG / s0.n, color=TXT2, lw=1.0, label="KG, water 25 °C")
    xr = XR[XR.estimator == "psl"].set_index("liquid")
    for liq in liqs:
        s = sel("DS-3", liq, "psl"); col = MED[liq]; mk = mks[liq]
        ax[0].plot(s.n - 0.1, -s.df_over_n, mk, ms=4, color=col, mec="white", mew=0.5); ax[0].plot(s.n + 0.1, s.dG_over_n, mk, ms=4, color=col, mfc="none", mew=0.9)
        ax[1].errorbar(s.n, s.r_KG1, yerr=s.r_KG1_sd, fmt=mk + "-", ms=4, color=col, mec="white", mew=0.5, lw=0.7, capsize=0, label=MEDL[liq])
        x = xr.loc[liq, "x_both_n3_9"]
        for n in N:
            r = s[s.n == n].iloc[0]
            ax[2].plot(x, -r.df_over_sqrtn, "o", ms=4, color=NC[n], mec="white", mew=0.5); ax[2].plot(x, r.dG_over_sqrtn, "o", ms=4, color=NC[n], mfc="none", mew=0.9)
    yw = float(np.mean(-s0[s0.n >= 3].df_over_sqrtn)); xx = np.array([0, 1.2]); ax[2].plot(xx, yw * xx, color=TXT2, lw=1.0, label="KG through the water point")
    ax[2].plot(0, 0, "o", color=MED["air"], ms=5)
    ax[2].set_xlabel("√(ρη) / √(ρη)_water (from the data)"); ax[2].set_ylabel("−Δf_n/√n (filled), ΔΓ_n/√n (open) [Hz]"); ax[2].set_xlim(-0.03, 1.2); ax[2].set_ylim(-20, 900)
    ax[2].set_title("KG-3 (relative)", fontsize=8.5); ax[2].legend(fontsize=5.8, loc="upper left")
    for n in N: ax[2].plot([], [], "o", color=NC[n], label="n = %d" % n)
    ax[2].legend(fontsize=5.5, loc="upper left")
    # resolution panel: x_rel vs concentration, per overtone from both channels, with the OLS line and the 3σ band
    for n in N:
        xs = [xr.loc[l, "x_both_n%d" % n] for l in liqs]; cc = [0, 5, 7.5, 10]
        ax[3].plot(cc, xs, "o", ms=3.5, color=NC[n], mec="white", mew=0.4)
    r = XC[(XC.estimator == "psl") & (XC.quantity == "x_both_n3_9")].iloc[0]; cline = np.array([0, 10.5]); ax[3].plot(cline, r.slope_per_pct * cline + r.intercept, color=TXT2, lw=0.9, label="OLS, %.4f per %% w/v" % r.slope_per_pct)
    s3 = RES[RES.estimator == "psl"]; res3 = float(s3.res3_x_f.max())
    ax[3].fill_between(cline, r.slope_per_pct * cline + r.intercept - res3, r.slope_per_pct * cline + r.intercept + res3, color=TXT2, alpha=0.15, lw=0, label="±3σ_x (worst n)")
    ax[3].set_xlabel("glucose [% w/v]"); ax[3].set_ylabel("√(ρη) / √(ρη)_water"); ax[3].set_title("resolution", fontsize=8.5); ax[3].legend(fontsize=5.3, loc="lower right")
    ax[0].set_xlabel("overtone order n"); ax[0].set_xticks(N); ax[0].set_ylabel("−Δf_n/n (filled), ΔΓ_n/n (open) [Hz]"); ax[0].set_title("T5", fontsize=8.5)
    for liq in liqs: ax[0].plot([], [], mks[liq], color=MED[liq], label=MEDL[liq])
    ax[0].legend(fontsize=5.3, loc="lower left", handletextpad=0.3)
    ax[1].axhline(1, color=TXT2, lw=1.0); ax[1].set_xlabel("overtone order n"); ax[1].set_xticks(N); ax[1].set_ylabel("ΔΓ_n / (−Δf_n)"); ax[1].set_ylim(0.8, 1.1); ax[1].set_title("KG-1", fontsize=8.5); ax[1].legend(fontsize=5.5, loc="lower center")
    fig.tight_layout()
    save(fig, "fig07_exp3_glucose", "results/v2/asis/shifts.csv, glucose_xrel.csv, glucose_resolution.csv, glucose_xrel_vs_conc.csv (DS-3, P)",
         "x_rel = mean over n = 3–9 of (−Δf_n + ΔΓ_n)/(−Δf_n,w + ΔΓ_n,w); KG line through the water point with slope mean_n(−Δf_n,w/√n); 3σ_x = 3·sd(replicas)/slope, worst overtone")


# ------------------------------------------------------------------ Fig 8: the rotation angle, every medium and dataset
def fig8_phi():
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    styles = {("DS-2", "air"): dict(marker="o", ls="-", mfc=MED["air"], color=MED["air"]), ("DS-2", "water"): dict(marker="s", ls="-", mfc=MED["water"], color=MED["water"]),
              ("DS-2", "ipa"): dict(marker="^", ls="-", mfc=MED["ipa"], color=MED["ipa"]),
              ("DS-3", "air"): dict(marker="o", ls="--", mfc="none", color=MED["air"]), ("DS-3", "water"): dict(marker="s", ls="--", mfc="none", color=MED["water"]),
              ("DS-3", "gluc05"): dict(marker="D", ls="--", mfc="none", color=MED["gluc05"]), ("DS-3", "gluc075"): dict(marker="D", ls="--", mfc="none", color=MED["gluc075"]), ("DS-3", "gluc10"): dict(marker="D", ls="--", mfc="none", color=MED["gluc10"])}
    for (ds, med), st in styles.items():
        s = PHI[(PHI.dataset == ds) & (PHI.medium == med)].sort_values("n")
        ax.errorbar(s.n + (0.0 if ds == "DS-2" else 0.15), s.phi, yerr=s.phi_sd.fillna(0), ms=4.5, mew=0.9, lw=0.8, capsize=0, label="%s %s" % (ds, MEDL[med]), **st)
    s = PHI[PHI.dataset.str.startswith("air 2026-09-03")].sort_values("n"); ax.plot(s.n - 0.15, s.phi, "x", ms=6, color=TXT, label="air 2026-09-03, board 1920 class")
    s = PHI[PHI.dataset.str.startswith("water 2026-07-28")]; ax.plot(s.n - 0.3, s.phi, "*", ms=8, color=MED["water"], mec=TXT, mew=0.5, label="water 2026-07-28, board not recorded")
    ax.axhline(0, color=TXT2, lw=0.6); ax.set_xticks(N); ax.set_xlabel("overtone order n"); ax.set_ylabel("rotation angle φ of the P fit [°]"); ax.set_ylim(-36, 6)
    ax.legend(fontsize=5.8, ncol=2, loc="lower left"); ax.set_title("φ_n per medium and dataset (error bars: sd over 3 sweeps; filled = board 1920, open = second instrument)", fontsize=7.5)
    fig.tight_layout()
    save(fig, "fig08_phi_all_media", "results/v2/asis/phi_all.csv", "P fit on every sweep; mean ± sd over the three replicas per medium; single sweeps for 2026-09-03 and 2026-07-28")


# ------------------------------------------------------------------ SI figures
def si_kg2():
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.9))
    panels = (("DS-2", "water", "DS-2 water"), ("DS-2", "ipa", "DS-2 isopropanol"), ("DS-3", "water", "DS-3 water"))
    for k, (ds, liq, title) in enumerate(panels):
        a = ax[k]
        for est, mk, mfc in (("argmax_hh", "v", "none"), ("psl", "o", None)):
            s = sel(ds, liq, est); col = MED[liq]
            a.plot(s.n, -s.df_over_n, mk, color=col, mfc=mfc if mfc else col, ms=4.5, mew=0.9); a.plot(s.n, s.dG_over_n, mk, color=TXT2, mfc=mfc if mfc else TXT2, ms=4.5, mew=0.9)
            r = K2[(K2.dataset == ds) & (K2.liquid == liq) & (K2.estimator == est) & (K2.fit == "n=3-9")].iloc[0]
            nn = np.array([2.5, 10.0])
            a.plot(nn, 10 ** (r.b_df * np.log10(nn) + (np.log10(-s[s.n == 3].df_over_n.iloc[0]) - r.b_df * np.log10(3))), ls=("--" if est == "psl" else ":"), color=col, lw=0.8, label="b(Δf) = %.2f (%s)" % (r.b_df, "P" if est == "psl" else "A"))
            a.plot(nn, 10 ** (r.b_dG * np.log10(nn) + (np.log10(s[s.n == 3].dG_over_n.iloc[0]) - r.b_dG * np.log10(3))), ls=("--" if est == "psl" else ":"), color=TXT2, lw=0.8, label="b(ΔΓ) = %.2f (%s)" % (r.b_dG, "P" if est == "psl" else "A"))
        s0 = sel(ds, liq, "psl"); a.plot(s0.n, -s0.df_KG / s0.n, color=C[7], lw=1.0, alpha=0.7, label="KG: b = −0.5")
        a.set_xscale("log"); a.set_yscale("log"); a.set_xticks(N); a.set_xticklabels([str(n) for n in N]); a.set_xlabel("overtone order n"); a.set_title(title, fontsize=8.5); a.legend(fontsize=5.3)
    ax[0].set_ylabel("−Δf_n/n (coloured), ΔΓ_n/n (grey) [Hz]")
    fig.tight_layout()
    save(fig, "figS_kg2_loglog", "results/v2/asis/shifts.csv, kg2_slopes.csv", "log–log OLS on n = 3–9; lines drawn through the n = 3 point", si=True)


def si_estimator_errors():
    ests = ["mag_argmax", "argmax_hh", "midpoint", "sym_lin", "circle", "psl"]
    labs = {"mag_argmax": "M", "argmax_hh": "A", "midpoint": "MP", "sym_lin": "S+", "circle": "C", "psl": "P"}
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 3.0))
    for k, (col, lab, ref) in enumerate((("eps_f", "Δf / Δf_KG − 1 (water, isopropanol)", 0), ("eps_G", "ΔΓ / ΔΓ_KG − 1", 0), ("r_KG1", "ΔΓ / (−Δf), all liquids", 1))):
        a = ax[k]; a.axhline(ref, color=TXT2, lw=0.8)
        for i, est in enumerate(ests):
            for ds, mk, off in (("DS-2", "o", -0.15), ("DS-3", "s", 0.15)):
                s = SH[(SH.dataset == ds) & (SH.estimator == est) & (SH.n >= 3)]
                if col != "r_KG1": s = s[s.liquid.isin(("water", "ipa"))]
                a.plot(np.full(len(s), i) + off, s[col], mk, ms=3.6, color=mf.EST_C[est], mec="white", mew=0.4, mfc=(mf.EST_C[est] if ds == "DS-2" else "none"))
        a.set_xticks(range(len(ests))); a.set_xticklabels([labs[e] for e in ests]); a.set_ylabel(lab)
    ax[0].set_ylim(-0.2, 1.3); ax[1].set_ylim(-0.2, 0.6); ax[2].set_ylim(0.4, 1.3)
    ax[2].plot([], [], "o", color=TXT2, label="DS-2 (filled)"); ax[2].plot([], [], "s", mfc="none", color=TXT2, label="DS-3 (open)"); ax[2].legend(fontsize=6.5)
    fig.suptitle("Error metrics on overtones 3–9 for six estimators; M: magnitude maximum, A: max G + half height, MP: midpoint, S+: symmetric + linear bg, C: BVD circle, P: phase-shifted Lorentzian", fontsize=6.8)
    fig.tight_layout()
    save(fig, "figS_estimator_errors", "results/v2/asis/shifts.csv", "n = 3–9; M's Γ = half of its −3 dB width where it exists (off scale)", si=True)


def si_hh_width():
    fig, ax = plt.subplots(figsize=(4.4, 3.0))
    for ds, mk in (("DS-2", "o"), ("DS-3", "s")):
        for ph in ("air", "water", "ipa", "gluc05", "gluc075", "gluc10"):
            s = BIAS[(BIAS.dataset == ds) & (BIAS.phase == ph)]
            if s.empty: continue
            ax.plot(s.hh_pred, s.hh_meas, mk, ms=5, color=MED[ph], mfc=(MED[ph] if ds == "DS-2" else "none"), mew=0.9, label="%s %s" % (ds, MEDL[ph]))
    ax.plot([0.99, 1.09], [0.99, 1.09], color=TXT2, lw=0.8); ax.set_xlabel("√(1 + 2 tan²(φ/2))"); ax.set_ylabel("Γ_hh / Γ_P"); ax.legend(fontsize=5.5, ncol=2, loc="lower right")
    ax.set_title("half-height width: rotation widens it (air, above the line);\nthe baseline on the skirt narrows it (liquid, below)", fontsize=7.5)
    fig.tight_layout()
    save(fig, "figS_halfheight_width", "results/v2/asis/bias_per_overtone.csv", "mean of three sweeps per medium and overtone", si=True)


def si_datalogs():
    imp, amp = data.datalogs_0911()
    t = (imp.t - imp.t.iloc[0]).dt.total_seconds() / 60; ta = (amp.t - amp.t.iloc[0]).dt.total_seconds() / 60
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 4.8), sharex=True)
    for k in range(5):
        n = 2 * k + 1
        f = imp["Frequency_%d" % k]; D = imp["Dissipation_%d" % k]; f_air = f[(t > 27) & (t < 37)].mean()
        ax[0, 0].plot(t, (f - f_air) / n, ".", ms=2, color=NC[n], label="n = %d" % n); ax[1, 0].plot(t, D, ".", ms=2, color=NC[n])
        fa = amp["Frequency_%d" % k]; w = amp["Dissipation_%d" % k] * 1e6; fa_air = fa[(ta > 27) & (ta < 37)].mean()
        ax[0, 1].plot(ta, (fa - fa_air) / n, ".", ms=2, color=NC[n]); ax[1, 1].plot(ta, w, ".", ms=2, color=NC[n])
    for x0, x1, ph in ((0, 37.2, "air"), (37.3, 61.0, "water"), (61.1, 75.3, "ipa")):
        for a in ax.flat: a.axvspan(x0, x1, color=MED[ph], alpha=0.08, lw=0)
    ax[0, 0].set_title("impedance chain (this work): A live", fontsize=8.5); ax[0, 1].set_title("production magnitude chain, same instants", fontsize=8.5)
    ax[0, 0].set_ylabel("(f_n − f_n,air)/n [Hz]"); ax[1, 0].set_ylabel("D [10⁻⁶]"); ax[1, 1].set_ylabel("width at −0.3 dB [Hz]"); ax[1, 0].set_xlabel("time [min]"); ax[1, 1].set_xlabel("time [min]")
    ax[0, 0].legend(fontsize=6.5, ncol=5, loc="lower left"); ax[1, 1].set_yscale("log")
    fig.tight_layout()
    save(fig, "figS_datalogs_0911", "2026-09-11_12-14-42_multi.csv and _multi_amplitude.csv", "as logged; f_air = mean over 27–37 min", si=True)


def si_glucose_lines():
    g = PH[(PH.dataset == "DS-3")]
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.8))
    conc = {"water": 0.0, "gluc05": 5.0, "gluc075": 7.5, "gluc10": 10.0}
    for n in N:
        w = g[(g.phase == "water") & (g.n == n) & (g.estimator == "psl")].iloc[0]
        for j, (col, lab) in enumerate((("fres", "Δf vs water [Hz]"), ("gamma", "ΔΓ vs water [Hz]"), ("D_ppm", "ΔD vs water [10⁻⁶]"))):
            x, y = [], []
            for liq, c in conc.items():
                r = g[(g.phase == liq) & (g.n == n) & (g.estimator == "psl")].iloc[0]; x.append(c); y.append(r[col] - w[col])
            x = np.array(x); y = np.array(y); A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, y, rcond=None)
            ax[j].plot(x, y, "o", ms=4, color=NC[n], mec="white", mew=0.4, label="n = %d: %.1f per %%" % (n, sol[0])); xx = np.array([0, 10.5]); ax[j].plot(xx, sol[0] * xx + sol[1], color=NC[n], lw=0.8)
            ax[j].set_xlabel("glucose [% w/v]"); ax[j].set_ylabel(lab)
    for a in ax: a.legend(fontsize=5.3)
    fig.tight_layout()
    save(fig, "figS_glucose_lines", "results/v2/asis/phases.csv (DS-3, P)", "shifts relative to the water plateau; OLS with intercept on 0, 5, 7.5, 10 % w/v", si=True)


def si_fwfix():
    a = pd.read_csv(os.path.join(R, "v2", "asis", "shifts.csv")); f = pd.read_csv(os.path.join(R, "v2", "fwfix", "shifts.csv"))
    m = a.merge(f, on=["dataset", "liquid", "n", "estimator"], suffixes=("_asis", "_fwfix")); m = m[m.estimator.isin(("argmax_hh", "psl"))]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for est, mk in (("argmax_hh", "v"), ("psl", "o")):
        s = m[m.estimator == est]
        ax[0].plot(s.df_asis, s.df_fwfix - s.df_asis, mk, ms=4, color=mf.EST_C[est], mec="white", mew=0.4, label=mf.EST_L[est]); ax[1].plot(s.dG_asis, s.dG_fwfix - s.dG_asis, mk, ms=4, color=mf.EST_C[est], mec="white", mew=0.4)
    ax[0].set_xlabel("Δf as acquired [Hz]"); ax[0].set_ylabel("Δf(corrected) − Δf(as acquired) [Hz]"); ax[1].set_xlabel("ΔΓ as acquired [Hz]"); ax[1].set_ylabel("ΔΓ(corrected) − ΔΓ(as acquired) [Hz]"); ax[0].legend(fontsize=6.5)
    fig.suptitle("Effect of undoing the firmware carry-over (1/500 of the previous point) on the shifts, both datasets", fontsize=8)
    fig.tight_layout()
    save(fig, "figS_firmware_correction", "results/v2/asis/shifts.csv, results/v2/fwfix/shifts.csv", "difference of the shifts between the two variants", si=True)


def si_phi_vs_frequency():
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for (ds, med), st in (( ("DS-2", "air"), dict(marker="o", color=MED["air"])), (("DS-3", "air"), dict(marker="o", color=MED["air"], mfc="none")), (("DS-2", "water"), dict(marker="s", color=MED["water"])), (("DS-3", "water"), dict(marker="s", color=MED["water"], mfc="none"))):
        s = PHI[(PHI.dataset == ds) & (PHI.medium == med)].sort_values("n"); ax.plot(s.f_MHz, s.phi, ls="none", ms=5, mew=0.9, label="%s %s" % (ds, med), **st)
    f = np.linspace(3, 48, 50)
    for tau, ls in ((0.74, ":"), (1.10, "--")): ax.plot(f, -360 * f * 1e6 * tau * 1e-9, color=TXT2, lw=0.8, ls=ls, label="pure delay τ = %.2f ns (resistive standards)" % tau)
    ax.set_xlabel("frequency [MHz]"); ax.set_ylabel("φ [°]"); ax.legend(fontsize=5.8, loc="lower left"); ax.set_ylim(-40, 5)
    fig.tight_layout()
    save(fig, "figS_phi_vs_frequency", "results/v2/asis/phi_all.csv; bias_theory.md (delays)", "φ against frequency with the phase of a pure delay for the two delays measured on the short / 50 Ω standards of 2026-09-03", si=True)


if __name__ == "__main__":
    fig2_estimators(); fig3_t4(); fig4_exp1(); fig5_bias(); fig6_exp2(); fig7_exp3(); fig8_phi()
    # SI: v1 functions redirected to the SI folder
    mf.FIG = SI; mf.PROV.clear()
    mf.fig_raw(); mf.fig_GB(); mf.fig_fits(); mf.fig_repeat(); mf.fig_forward()
    for p in mf.PROV:
        p["figure"] = "si/" + p["figure"]; PROV.append(p)
    si_kg2(); si_estimator_errors(); si_hh_width(); si_datalogs(); si_glucose_lines(); si_fwfix(); si_phi_vs_frequency()
    L = ["# Figure provenance — manuscript v2\n", "| figure | source dataset | script | parameters |", "|---|---|---|---|"]
    for p in PROV:
        L.append("| %s | %s | %s | %s |" % (p["figure"], p["source"], p["script"], p["params"]))
    open(os.path.join(R, "v2", "figure_provenance_v2.md"), "w").write("\n".join(L) + "\n")
    # the circuit figure of v1 is reused as Fig. 1
    import shutil
    for ext in ("png", "svg"):
        src = os.path.join(HERE, "..", "figures", "fig01_measurement_circuit." + ext)
        if os.path.exists(src): shutil.copy(src, os.path.join(FIG, "fig01_measurement_circuit." + ext))
