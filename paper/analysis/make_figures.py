# -*- coding: utf-8 -*-
"""
make_figures.py — publication figures of the paper, regenerated from the raw
data and from results/*.csv. Every figure records its source dataset, script
and parameters in results/figure_provenance.md. Output: ../figures/figN_*.png
(300 dpi) and .pdf.
"""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import qcmchain as q, data

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
FIG = os.path.normpath(os.path.join(HERE, "..", "figures")); os.makedirs(FIG, exist_ok=True)
# categorical palette (dataviz reference instance, fixed order), text/grid tokens
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
PH = {"air": C[0], "water": C[1], "ipa": C[2]}
PHL = {"air": "air", "water": "water", "ipa": "isopropanol"}
EST_C = {"mag_argmax": C[7], "argmax_hh": C[0], "midpoint": C[4], "sym_lin": C[1], "sym": C[3], "psl": C[2], "circle": C[6]}
EST_L = {"mag_argmax": "magnitude max", "argmax_hh": "G max + half height", "midpoint": "half-height midpoint",
         "sym": "sym. Lorentzian", "sym_lin": "sym. Lorentzian + lin. bg", "psl": "phase-shifted Lorentzian", "circle": "BVD circle"}
TXT, TXT2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": TXT2, "axes.labelcolor": TXT, "xtick.color": TXT2, "ytick.color": TXT2,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 300, "lines.linewidth": 1.4, "axes.titlesize": 9, "axes.titleweight": "bold"})
PROV = []


def save(fig, name, source, params):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, "%s.%s" % (name, ext)), bbox_inches="tight")
    plt.close(fig)
    PROV.append(dict(figure=name, source=source, script="paper/analysis/make_figures.py", params=params))
    print("wrote", name)


dumps, mt = data.dumps_0911()
SW = pd.read_csv(os.path.join(R, "sweeps_asis.csv"))
SH = pd.read_csv(os.path.join(R, "shifts_asis.csv"))
FM = pd.read_csv(os.path.join(R, "forward_model.csv"))
BT = json.load(open(os.path.join(R, "bias_theory.json")))
GL = os.path.exists(os.path.join(R, "glucose_sweeps_asis.csv"))
if GL:
    GSW = pd.read_csv(os.path.join(R, "glucose_sweeps_asis.csv")); GSH = pd.read_csv(os.path.join(R, "glucose_shifts_asis.csv"))
    GCC = pd.read_csv(os.path.join(R, "glucose_conc_asis.csv")); GPH = pd.read_csv(os.path.join(R, "glucose_phi_asis.csv"))
    GPHS = pd.read_csv(os.path.join(R, "glucose_phases_asis.csv"))
GLC = {"water": C[1], "gluc05": C[3], "gluc075": C[4], "gluc10": C[6]}
GLL = {"air": "air (2024)", "water": "water (2024)", "gluc05": "glucose 5 %", "gluc075": "glucose 7.5 %", "gluc10": "glucose 10 %"}


def chain_of(s, n):
    f, vm, vp = dumps[(s, n)]
    c = q.chain(f, vm, vp); e = q.argmax_halfheight(c["f"], c["G"])
    p = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"]); sl = q.fit_symmetric(c["f"], c["G"], e["f_max"], e["gamma_hh"], linear=True)
    return c, e, p, sl


# ---------------------------------------------------------------- Fig 2: raw sweeps
def fig_raw():
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.2), sharex="col")
    for j, (s, n) in enumerate((("air_1", 1), ("air_1", 5), ("wat_1", 5))):
        f, vm, vp = dumps[(s, n)]
        x = (f - f[0]) / 1e3 - 12.0
        ax[0, j].plot(x, vm, color=PH[data.SETS and ("air" if s.startswith("air") else "water")], lw=0.8)
        ax[1, j].plot(x, vp, color=PH["air" if s.startswith("air") else "water"], lw=0.8)
        ax[1, j].axhline(q.V_PHS_ZERO, color=TXT2, lw=0.7, ls="--")
        ax[0, j].set_title("%s, n = %d (%.1f MHz)" % (PHL["air" if s.startswith("air") else "water"], n, f.mean() / 1e6))
        ax[1, j].set_xlabel("f − f_centre [kHz]")
        a2 = ax[1, j].twinx(); a2.set_ylim(*(q.phase_reading_deg(np.array(ax[1, j].get_ylim())))); a2.grid(False); a2.spines["right"].set_visible(True)
        if j == 2: a2.set_ylabel("|Δφ| reading [°]", color=TXT2)
        a2.tick_params(colors=TXT2)
    ax[0, 0].set_ylabel("V_MAG [V] (attenuator undone)"); ax[1, 0].set_ylabel("V_PHS [V]")
    ax[1, 0].annotate("1.8 V = 0°", (-11.5, q.V_PHS_ZERO), fontsize=7, color=TXT2, va="bottom")
    fig.tight_layout()
    save(fig, "fig02_raw_sweeps", "research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5)", "raw samples, no processing")


# ------------------------------------------------- Fig 3: reconstructed G, B and loci
def fig_GB():
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.6))
    for j, (s, n) in enumerate((("air_1", 1), ("air_1", 5), ("wat_1", 5))):
        c, e, p, sl = chain_of(s, n); ph = "air" if s.startswith("air") else "water"
        w = np.abs(c["f"] - e["f_max"]) <= 4 * e["gamma_hh"]
        x = (c["f"] - p["fres"]) / e["gamma_hh"]
        ax[0, j].plot(x[w], 1e3 * c["G"][w], color=PH[ph], label="G"); ax[0, j].plot(x[w], 1e3 * c["B"][w], color=C[6], label="B")
        ax[0, j].axvline(0, color=C[2], lw=0.8, ls="--"); ax[0, j].axvline((e["f_max"] - p["fres"]) / e["gamma_hh"], color=TXT2, lw=0.8, ls=":")
        ax[0, j].set_title("%s, n = %d%s" % (PHL[ph], n, "" if c["fold"] else " (no fold)")); ax[0, j].set_xlabel("(f − f_res) / Γ")
        ax[1, j].plot(1e3 * c["G"][w], 1e3 * c["B"][w], color=PH[ph], lw=1.0)
        i_r = int(np.argmin(np.abs(c["f"] - p["fres"]))); ax[1, j].plot(1e3 * c["G"][i_r], 1e3 * c["B"][i_r], "o", color=C[2], ms=5, label="f_res (PSL)")
        ax[1, j].plot(1e3 * c["G"][e["i_max"]], 1e3 * c["B"][e["i_max"]], "v", color=TXT, ms=5, label="max G")
        ax[1, j].set_xlabel("G [mS]"); ax[1, j].set_aspect("equal", adjustable="datalim")
    ax[0, 0].set_ylabel("G, B [mS]"); ax[1, 0].set_ylabel("B [mS]"); ax[0, 0].legend(loc="upper left", fontsize=7); ax[1, 0].legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    save(fig, "fig03_G_B_locus", "sweep_dumps_2026-09-11.npz (air_1/g1, air_1/g5, wat_1/g5)", "chain: SG 51/3 + spline s=0.001, fold rule, exact inversion; window ±4 Γ_hh; dotted = max G, dashed = PSL f_res")


# ----------------------------------------------- Fig 4: symmetric vs PSL residuals
def fig_fits():
    cases = (("air_1", 5), ("wat_1", 5), ("ipa_1", 9))
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.4), sharex="col", gridspec_kw=dict(height_ratios=[2.2, 1]))
    for j, (s, n) in enumerate(cases):
        c, e, p, sl = chain_of(s, n); ph = s[:3].replace("wat", "water")
        idx = p["idx"]; F = c["f"][idx]; G = 1e3 * c["G"][idx]; x = (F - p["fres"]) / 1e3
        ax[0, j].plot(x, G, ".", ms=2, color=TXT2, label="measured G")
        ax[0, j].plot(x, 1e3 * q.rotated_lorentzian(F, p["fres"], p["gamma"], p["phi_deg"], p["gmax"], p["g_off"]), color=C[2], label="phase-shifted Lorentzian")
        d = sl["fres"] - F; gs = sl["gamma"]
        ax[0, j].plot(x, 1e3 * (sl["gmax"] * gs * gs / (d * d + gs * gs) + sl["g_off"]) , color=C[1], ls="--", label="symmetric + lin. bg (shape)")
        ax[0, j].axvline(0, color=C[2], lw=0.8); ax[0, j].axvline((e["f_max"] - p["fres"]) / 1e3, color=TXT, lw=0.8, ls=":")
        ax[0, j].set_title("%s, n = %d: φ = %.1f°" % (PHL[ph], n, p["phi_deg"]))
        ax[1, j].plot(x, 100 * sl["residual"], color=C[1], lw=0.9, label="symmetric + lin. bg")
        ax[1, j].plot(x, 100 * p["residual"], color=C[2], lw=0.9, label="phase-shifted")
        ax[1, j].axhline(0, color=TXT2, lw=0.6); ax[1, j].set_xlabel("f − f_res [kHz]"); ax[1, j].set_ylim(-9, 9)
    ax[0, 0].set_ylabel("G [mS]"); ax[1, 0].set_ylabel("residual [% of range]")
    ax[0, 0].legend(fontsize=6.5, loc="upper left"); ax[1, 2].legend(fontsize=6.5, loc="upper right")
    fig.tight_layout()
    save(fig, "fig04_fits_residuals", "sweep_dumps_2026-09-11.npz (air_1/g5, wat_1/g5, ipa_1/g9)", "fits on ±3 Γ_hh around max G; symmetric model drawn without its linear term for shape; dotted = max G")


# ------------------------------------------------------- Fig 5: bias vs prediction
def fig_bias():
    p = SW[SW.estimator == "psl"]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1))
    for ph in ("air", "water", "ipa"):
        s = p[p.phase == ph]
        ax[0].plot(s.bias_pred, s.bias_meas, "o", ms=4, color=PH[ph], label=PHL[ph], mec="white", mew=0.5)
        ax[1].plot(s.gamma, (s.bias_meas - s.bias_pred) / s.gamma, "o", ms=4, color=PH[ph], mec="white", mew=0.5)
    if GL:
        gp = GSW[GSW.estimator == "psl"]
        ax[0].plot(gp.bias_pred, gp.bias_meas, "s", ms=3.5, mfc="none", color=TXT, label="2024 set (75 sweeps, 2nd instrument)", mew=0.6)
        ax[1].plot(gp.gamma, (gp.bias_meas - gp.bias_pred) / gp.gamma, "s", ms=3.5, mfc="none", color=TXT, mew=0.6)
    lim = [-760, 60]; ax[0].plot(lim, lim, color=TXT2, lw=0.8); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
    ax[0].set_xlabel("predicted Γ·tan(φ/2) [Hz]"); ax[0].set_ylabel("measured f_Gmax − f_res [Hz]"); ax[0].legend(fontsize=7); ax[0].set_title("Bias of the conductance maximum, 45 + 75 sweeps")
    ax[1].axhline(0, color=TXT2, lw=0.8); ax[1].set_xscale("log"); ax[1].set_xlabel("Γ (PSL) [Hz]"); ax[1].set_ylabel("(measured − predicted) / Γ"); ax[1].set_title("Residual of the closed form")
    fig.tight_layout()
    save(fig, "fig05_argmax_bias", "results/sweeps_asis.csv (psl rows)", "bias_meas = f_Gmax − f_res(PSL); bias_pred = Γ_PSL tan(φ_PSL/2)")


# ------------------------------------------------------------ Fig 6: phi vs overtone
def fig_phi():
    p = SW[SW.estimator == "psl"]
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for ph in ("air", "water", "ipa"):
        s = p[p.phase == ph]
        ax.plot(s.fres / 1e6, s.phi_deg, "o", ms=4.5, color=PH[ph], label="%s (3 replicas)" % PHL[ph], mec="white", mew=0.5)
    a03 = BT["air_0903"]
    ax.plot([a03[k]["fres"] / 1e6 for k in a03], [a03[k]["phi"] for k in a03], "s", ms=4.5, mfc="none", color=C[0], label="air, 2026-09-03")
    # the two-channel forward-model board phase of the repository (handoff-tables.md Table 7, air, mean of ranges)
    phib = {1: -7.65, 3: -13.75, 5: -19.85, 7: -22.05, 9: -20.4}
    fm = p[p.phase == "air"].groupby("n").fres.mean() / 1e6
    ax.plot([fm[n] for n in phib], [phib[n] for n in phib], "x", ms=6, color=TXT, label="φ_b, two-channel BVD forward model (repo Table 7)")
    f = np.linspace(3, 48, 50)
    for tau, ls in ((0.74, ":"), (1.10, "--")):
        ax.plot(f, -360 * f * 1e6 * tau * 1e-9, color=TXT2, lw=0.8, ls=ls, label="pure delay τ = %.2f ns (standards)" % tau)
    if GL:
        gp = GSW[GSW.estimator == "psl"]
        ax.plot(gp[gp.phase == "air"].fres / 1e6, gp[gp.phase == "air"].phi_deg, "D", ms=4, mfc="none", color=C[0], mew=0.8, label="air, 2024 (2nd instrument)")
        gl = gp[gp.phase != "air"]; ax.plot(gl.fres / 1e6, gl.phi_deg, "D", ms=4, mfc="none", color=C[1], mew=0.8, label="water + glucose, 2024")
        r24 = GPH[(GPH.phase == "air") & (GPH.fit == "n=1-9")].iloc[0]
        ax.plot(f, r24.phi0_deg - 360 * f * 1e6 * r24.tau_ns * 1e-9, color=C[0], lw=0.8, ls="-.", label="2024 air: φ₀ = %.1f°, τ = %.2f ns" % (r24.phi0_deg, r24.tau_ns))
        a26 = p[p.phase == "air"].groupby("n").agg(f=("fres", "mean"), phi=("phi_deg", "mean"))
        x = -360.0 * a26.f.values * 1e-9; A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, a26.phi.values, rcond=None)
        ax.plot(f, sol[1] - 360 * f * 1e6 * sol[0] * 1e-9, color=C[0], lw=0.8, ls="-", alpha=0.6, label="2026 air: φ₀ = %.1f°, τ = %.2f ns" % (sol[1], sol[0]))
    ax.set_xlabel("frequency [MHz]"); ax.set_ylabel("rotation angle φ [°]"); ax.legend(fontsize=6.3, loc="lower left"); ax.set_ylim(-48, 3)
    fig.tight_layout()
    save(fig, "fig06_phi_vs_frequency", "results/sweeps_asis.csv; results/bias_theory.json (air_0903, osl); handoff-tables.md Table 7" + ("; results/glucose_sweeps_asis.csv, glucose_phi_asis.csv" if GL else ""), "PSL φ per sweep; delay lines 360·f·τ with τ from the short/50 Ω standards; φ₀ − 360·f·τ least-squares lines on n = 1–9 for the two instruments")


# ------------------------------------------------------- Fig 7: shifts vs KG
def fig_shifts():
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.4), sharex=True)
    ests = ["argmax_hh", "sym_lin", "psl"]
    for j, liq in enumerate(("water", "ipa")):
        for i, (col, lab) in enumerate((("df_over_n", "−Δf_n / n [Hz]"), ("dG_over_n", "ΔΓ_n / n [Hz]"))):
            a = ax[i, j]
            s0 = SH[(SH.liquid == liq) & (SH.estimator == "psl")].sort_values("n")
            kg = -s0.df_KG.values / s0.n.values
            a.plot(s0.n, kg, color=TXT2, lw=1.2, label="Kanazawa–Gordon (25 °C)")
            for est in ests:
                s = SH[(SH.liquid == liq) & (SH.estimator == est)].sort_values("n")
                y = -s[col] if col == "df_over_n" else s[col]
                err = (s.df_sd if col == "df_over_n" else s.dG_sd) / s.n
                a.errorbar(s.n + {"argmax_hh": -0.12, "sym_lin": 0, "psl": 0.12}[est], y, yerr=err, fmt="o", ms=4.5, color=EST_C[est], label=EST_L[est], mec="white", mew=0.5, capsize=0, lw=0.8)
            a.set_ylabel(lab); a.set_xticks([1, 3, 5, 7, 9])
            if i == 0: a.set_title("air → %s" % PHL[liq])
            if i == 1: a.set_xlabel("overtone order n")
    ax[0, 0].legend(fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig07_shifts_vs_KG", "results/shifts_asis.csv", "shifts liquid − air, mean of 3 sweeps; error bars = quadrature sd of the two plateaus, divided by n")


# ------------------------------------------- Fig 8: estimator comparison (eps_f, eps_G, rho)
def fig_estimators():
    ests = ["mag_argmax", "argmax_hh", "midpoint", "sym_lin", "circle", "psl"]
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 3.2))
    for k, (col, lab, ref) in enumerate((("eps_f", "Δf / Δf_KG − 1", 0), ("eps_G", "ΔΓ / ΔΓ_KG − 1", 0), ("rho", "|Δf| / ΔΓ", 1))):
        a = ax[k]; a.axhline(ref, color=TXT2, lw=0.8)
        for i, est in enumerate(ests):
            for liq, mk in (("water", "o"), ("ipa", "s")):
                s = SH[(SH.liquid == liq) & (SH.estimator == est) & (SH.n >= 3)]
                a.plot(np.full(len(s), i) + (-0.12 if liq == "water" else 0.12), s[col], mk, ms=4, color=EST_C[est], mec="white", mew=0.4)
        a.set_xticks(range(len(ests))); a.set_xticklabels([EST_L[e].replace(" + ", "\n+ ").replace("phase-shifted ", "phase-shifted\n") for e in ests], rotation=60, ha="right", fontsize=6.3)
        a.set_ylabel(lab)
    ax[0].set_ylim(-0.15, 1.05); ax[1].set_ylim(-0.15, 0.4); ax[2].set_ylim(0.3, 1.6)
    ax[0].set_title("frequency shift error, n = 3–9"); ax[1].set_title("bandwidth shift error, n = 3–9"); ax[2].set_title("Newtonian ratio (KG: 1)")
    ax[2].plot([], [], "o", color=TXT2, label="water"); ax[2].plot([], [], "s", color=TXT2, label="isopropanol"); ax[2].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    save(fig, "fig08_estimator_errors", "results/shifts_asis.csv", "overtones 3–9, both liquids; magnitude 'Γ' = half of the −3 dB width of |H| where defined (eps_G off scale)")


# ------------------------------------------------------- Fig 9: repeatability
def fig_repeat():
    ests = ["argmax_hh", "sym_lin", "psl", "circle"]
    g = SW.groupby(["phase", "n", "estimator"]).agg(fsd=("fres", "std"), gsd=("gamma", "std")).reset_index()
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for k, (col, lab) in enumerate((("fsd", "sd of f over 3 sweeps [Hz]"), ("gsd", "sd of Γ over 3 sweeps [Hz]"))):
        for ph, mk in (("air", "o"), ("water", "s"), ("ipa", "^")):
            for i, est in enumerate(ests):
                s = g[(g.phase == ph) & (g.estimator == est)].sort_values("n")
                ax[k].plot(s.n + (i - 1.5) * 0.18, s[col].clip(lower=0.05), mk, ms=4, color=EST_C[est], mec="white", mew=0.4)
        ax[k].set_yscale("log"); ax[k].set_xticks([1, 3, 5, 7, 9]); ax[k].set_xlabel("overtone order n"); ax[k].set_ylabel(lab)
    for est in ests: ax[0].plot([], [], "o", color=EST_C[est], label=EST_L[est])
    for ph, mk in (("air", "o"), ("water", "s"), ("ipa", "^")): ax[1].plot([], [], mk, color=TXT2, label=PHL[ph])
    ax[0].legend(fontsize=6.5); ax[1].legend(fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig09_repeatability", "results/sweeps_asis.csv", "sd over the three plateau sweeps per phase, estimator and overtone")


# ---------------------------------------------------------- Fig 10: forward model
def fig_forward():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1))
    e = FM[FM.block == "E"]
    ax[0].plot(e.ratio, -e.err_argmax, "v", color=C[0], label="max of G"); ax[0].plot(e.ratio, -e.err_sym, "s", color=C[1], label="sym. Lorentzian + lin. bg")
    ax[0].plot(e.ratio, -e.err_psl, "o", color=C[2], label="phase-shifted Lorentzian")
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("R₁ / R₁₇"); ax[0].set_ylabel("−(f_est − f_s) [Hz]")
    ax[0].set_title("board phase φ_b = −20° on H; Γ = 1 kHz"); ax[0].legend(fontsize=6.5); ax[0].axvline(1, color=TXT2, lw=0.7, ls=":")
    a = FM[(FM.block == "A")]
    for case, mk, col in (("air n=1 like", "o", C[0]), ("air n=9 like", "s", C[0]), ("water n=5 like", "o", C[1]), ("ipa n=9 like", "^", C[2])):
        s = a[a.case == case].sort_values("phi_b")
        ax[1].plot(s.phi_b, s.err_psl / s.gamma, mk + "-", color=col, ms=4.5, lw=0.8, label=case.replace(" like", ""), mec="white", mew=0.4)
        ax[1].plot(s.phi_b, s.err_argmax / s.gamma, mk + ":", color=col, ms=3, lw=0.8, mfc="none")
    ax[1].axhline(0, color=TXT2, lw=0.7); ax[1].set_xlabel("board phase φ_b [°]"); ax[1].set_ylabel("(f_est − f_s) / Γ"); ax[1].set_title("solid: PSL; dotted: max of G"); ax[1].legend(fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig10_forward_model", "results/forward_model.csv (blocks A and E)", "BVD truth through divider, AD8302 laws with board phase on ∠H, ADC quantisation; same chain and estimators as the data")


# ---------------------------------------------------------- Fig 11: datalog run
def fig_datalog():
    imp, amp = data.datalogs_0911()
    t = (imp.t - imp.t.iloc[0]).dt.total_seconds() / 60
    fig, ax = plt.subplots(2, 1, figsize=(7.2, 4.4), sharex=True)
    for k in range(5):
        n = 2 * k + 1; f = imp["Frequency_%d" % k]; D = imp["Dissipation_%d" % k]
        f_air = f[t < 30].iloc[-20:].mean()
        ax[0].plot(t, (f - f_air) / n, ".", ms=2.5, color=C[k], label="n = %d" % n)
        ax[1].plot(t, D, ".", ms=2.5, color=C[k])
    for x0, x1, ph in ((0, 37.2, "air"), (37.3, 61.0, "water"), (61.1, 75.2, "ipa")):
        for a in ax: a.axvspan(x0, x1, color=PH[ph], alpha=0.07, lw=0)
    ax[0].set_ylabel("(f_n − f_n,air) / n [Hz]"); ax[1].set_ylabel("D [10⁻⁶]"); ax[1].set_xlabel("time [min]"); ax[0].legend(fontsize=6.5, ncol=5, loc="lower left")
    ax[0].set_title("Run 2026-09-11: air → water → isopropanol, instrument datalog (max of G, half-height Γ)")
    fig.tight_layout()
    save(fig, "fig11_datalog_run", "research/air-ipa-water-1920-2026-09-11/data/2026-09-11_12-14-42_multi.csv", "as logged; f_air = mean of the last 20 rows before 30 min")


# --------------------------------------------- Figs 12–14: the 2024 glucose series (second instrument)
def fig_gluc_shifts():
    liqs = ("water", "gluc05", "gluc075", "gluc10")
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 3.1))
    s0 = GSH[(GSH.ref == "air") & (GSH.liquid == "water") & (GSH.estimator == "psl")].sort_values("n")
    ax[0].plot(s0.n, -s0.df_KG / s0.n, color=TXT2, lw=1.2, label="Kanazawa–Gordon, water 25 °C"); ax[1].plot(s0.n, -s0.df_KG / s0.n, color=TXT2, lw=1.2)
    ax[2].plot(s0.n, s0.dD_KG_ppm, color=TXT2, lw=1.2)
    for liq in liqs:
        for est, mk, mfc in (("argmax_hh", "v", "none"), ("psl", "o", None)):
            s = GSH[(GSH.ref == "air") & (GSH.liquid == liq) & (GSH.estimator == est)].sort_values("n")
            kw = dict(ms=4.5, color=GLC[liq], mfc=mfc if mfc else GLC[liq], mew=0.8, lw=0)
            ax[0].plot(s.n + (-0.1 if est == "argmax_hh" else 0.1), -s.df_over_n, mk, **kw)
            ax[1].plot(s.n + (-0.1 if est == "argmax_hh" else 0.1), s.dG_over_n, mk, **kw)
            ax[2].plot(s.n + (-0.1 if est == "argmax_hh" else 0.1), s.dD_ppm, mk, **kw)
    for liq in liqs: ax[0].plot([], [], "s", color=GLC[liq], label=GLL[liq])
    ax[0].plot([], [], "v", mfc="none", color=TXT, label="max G + half height"); ax[0].plot([], [], "o", color=TXT, label="phase-shifted Lorentzian")
    ax[0].set_ylabel("−Δf_n / n [Hz]"); ax[1].set_ylabel("ΔΓ_n / n [Hz]"); ax[2].set_ylabel("ΔD_n [10⁻⁶]")
    for a in ax: a.set_xticks([1, 3, 5, 7, 9]); a.set_xlabel("overtone order n")
    ax[2].legend(*ax[0].get_legend_handles_labels(), fontsize=5.8, loc="upper right"); ax[0].set_title("2024 set: shifts from air", loc="left")
    fig.tight_layout()
    save(fig, "fig12_glucose_shifts_vs_n", "results/glucose_shifts_asis.csv (ref = air)", "mean of 3 replicas; KG for water only")


def fig_gluc_ratio():
    ests = ["mag_argmax", "argmax_hh", "midpoint", "sym_lin", "circle", "psl"]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
    for k, (dfx, title) in enumerate(((SH, "2026 set, board 1920 (water ○, isopropanol □)"), (GSH[GSH.ref == "air"], "2024 set, 2nd instrument (water ○, glucose 5/7.5/10 % □ ◇ △)"))):
        a = ax[k]; a.axhline(1, color=TXT2, lw=0.8)
        for i, est in enumerate(ests):
            liqs = (("water", "o"), ("ipa", "s")) if k == 0 else (("water", "o"), ("gluc05", "s"), ("gluc075", "D"), ("gluc10", "^"))
            for j, (liq, mk) in enumerate(liqs):
                s = dfx[(dfx.liquid == liq) & (dfx.estimator == est) & (dfx.n >= 3)]
                a.plot(np.full(len(s), i) + (j - (len(liqs) - 1) / 2) * 0.16, s.rho, mk, ms=3.6, color=EST_C[est], mec="white", mew=0.4)
        a.set_xticks(range(len(ests))); a.set_xticklabels([EST_L[e].replace(" + ", "\n+ ").replace("phase-shifted ", "phase-shifted\n") for e in ests], rotation=60, ha="right", fontsize=6.3)
        a.set_title(title, fontsize=7.5); a.set_ylim(0.3, 1.7)
    ax[0].set_ylabel("|Δf| / ΔΓ (Newtonian: 1), n = 3–9")
    fig.tight_layout()
    save(fig, "fig13_newtonian_ratio_two_instruments", "results/shifts_asis.csv; results/glucose_shifts_asis.csv (ref = air)", "overtones 3–9; magnitude estimator where its −3 dB width exists")


def fig_gluc_conc():
    fig, ax = plt.subplots(1, 4, figsize=(7.4, 2.9))
    conc = {"water": 0.0, "gluc05": 5.0, "gluc075": 7.5, "gluc10": 10.0}
    for k, n in enumerate((1, 3, 5, 7, 9)):
        for j, (col, lab) in enumerate((("df", "Δf vs water [Hz]"), ("dG", "ΔΓ vs water [Hz]"), ("dD_ppm", "ΔD vs water [10⁻⁶]"))):
            s = GSH[(GSH.ref == "water") & (GSH.estimator == "psl") & (GSH.n == n)].sort_values("conc")
            x = np.concatenate([[0.0], s.conc.values]); y = np.concatenate([[0.0], s[col].values])
            r = GCC[(GCC.estimator == "psl") & (GCC.n == n)].iloc[0]; kk, bb = {"df": (r.k_df, r.b_df), "dG": (r.k_dG, r.b_dG), "dD_ppm": (r.k_dD, r.b_dD)}[col]
            ax[j].plot(x, y, "o", ms=4, color=C[k], label="n = %d" % n, mec="white", mew=0.4); xx = np.array([0, 10.5]); ax[j].plot(xx, kk * xx + bb, color=C[k], lw=0.8)
            ax[j].set_xlabel("glucose [% w/v]"); ax[j].set_ylabel(lab)
        r = GCC[(GCC.estimator == "psl") & (GCC.n == n)].iloc[0]
        ax[3].plot([5, 7.5, 10], [r.rhoeta_rel_05, r.rhoeta_rel_075, r.rhoeta_rel_10], "o-", ms=4, color=C[k], lw=0.8, mec="white", mew=0.4)
        r2 = GCC[(GCC.estimator == "argmax_hh") & (GCC.n == n)].iloc[0]
        ax[3].plot([5, 7.5, 10], [r2.rhoeta_rel_05, r2.rhoeta_rel_075, r2.rhoeta_rel_10], "v", ms=3.5, mfc="none", color=C[k], mew=0.7)
    ax[3].set_xlabel("glucose [% w/v]"); ax[3].set_ylabel("ρη / (ρη)_water = (Δf/Δf_water)²"); ax[3].plot([], [], "v", mfc="none", color=TXT, label="max G"); ax[3].plot([], [], "o", color=TXT, label="PSL")
    ax[3].legend(fontsize=6, loc="upper left")
    h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, fontsize=6.5, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, "fig14_glucose_concentration", "results/glucose_shifts_asis.csv (ref = water, air); results/glucose_conc_asis.csv", "phase-shifted Lorentzian; lines = OLS with intercept on 0, 5, 7.5, 10 % w/v; ρη relative from the air-referenced Δf")


def fig_collapse():
    """Kanazawa–Gordon structure without liquid constants: −Δf_n/√n and ΔΓ_n/√n should be the same for every overtone."""
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.0), sharex=True)
    panels = ((SH[SH.liquid == "water"], "campaign 1, board 1920: water", PH["water"]), (SH[SH.liquid == "ipa"], "campaign 1: isopropanol", PH["ipa"]),
              (GSH[(GSH.ref == "air") & (GSH.liquid == "water")], "campaign 2, 2nd instrument: water", C[1]), (GSH[(GSH.ref == "air") & (GSH.liquid == "gluc10")], "campaign 2: glucose 10 % w/v", C[6]))
    for k, (dfx, title, col) in enumerate(panels):
        a = ax[k // 2, k % 2]
        for est, mk, mfc, lab in (("argmax_hh", "v", "none", "max G + half height"), ("psl", "o", None, "phase-shifted Lorentzian")):
            s = dfx[dfx.estimator == est].sort_values("n")
            a.plot(s.n - 0.08, -s.df / np.sqrt(s.n), mk, color=col, mfc=mfc if mfc else col, ms=5, mew=0.9, label="−Δf/√n, " + lab)
            a.plot(s.n + 0.08, s.dG / np.sqrt(s.n), mk, color=TXT2, mfc=mfc if mfc else TXT2, ms=5, mew=0.9, label="ΔΓ/√n, " + lab)
        s0 = dfx[dfx.estimator == "psl"].sort_values("n")
        if "df_KG" in s0 and s0.df_KG.notna().any():
            a.axhline(float((-s0.df_KG / np.sqrt(s0.n)).iloc[0]), color=TXT2, lw=1.0, ls="--", label="Kanazawa–Gordon (water, 25 °C)")
        a.set_title(title); a.set_xticks([1, 3, 5, 7, 9])
    ax[0, 0].set_ylabel("shift / √n [Hz]"); ax[1, 0].set_ylabel("shift / √n [Hz]"); ax[1, 0].set_xlabel("overtone order n"); ax[1, 1].set_xlabel("overtone order n")
    ax[0, 0].legend(fontsize=6, loc="upper right")
    fig.tight_layout()
    save(fig, "fig15_sqrt_n_collapse", "results/shifts_asis.csv; results/glucose_shifts_asis.csv (ref = air)", "−Δf_n/√n and ΔΓ_n/√n per overtone; a Newtonian liquid gives one horizontal line for both")


if __name__ == "__main__":
    fig_raw(); fig_GB(); fig_fits(); fig_bias(); fig_phi(); fig_shifts(); fig_estimators(); fig_repeat(); fig_forward(); fig_datalog()
    if GL:
        fig_gluc_shifts(); fig_gluc_ratio(); fig_gluc_conc(); fig_collapse()
    L = ["# Figure provenance\n", "| figure | source dataset | script | parameters |", "|---|---|---|---|"]
    for p in PROV:
        L.append("| %s | %s | %s | %s |" % (p["figure"], p["source"], p["script"], p["params"]))
    open(os.path.join(R, "figure_provenance.md"), "w").write("\n".join(L) + "\n")
