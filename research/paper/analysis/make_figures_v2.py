# -*- coding: utf-8 -*-
"""
make_figures_v2.py — figures of manuscript v2 (main text: ../figures_v2/figN_*.png|pdf; SI: ../figures_v2/si/figSN_*).
Figs. 3, 4, 6, 7, 8 are drawn by make_figures_v2b.py (revision of 2026-10-09), called from __main__ below.
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


# Figs. 3, 4, 6, 7, 8: make_figures_v2b.py (revision of 2026-10-09; the v0.2 versions of 2026-10-08 are in git history)


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
    fig2_estimators(); fig5_bias()
    import make_figures_v2b
    PROV.extend(make_figures_v2b.main(FIG)); PROV.sort(key=lambda p: p["figure"])
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
