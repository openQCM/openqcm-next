# -*- coding: utf-8 -*-
"""
make_si.py — fills the tables of the Supporting Information from results/v2/asis/*.csv.
    manuscript/supporting_information.template.md  →  manuscript/supporting_information.md
Placeholders {{TABLE:<name>}} are replaced by Markdown tables generated here, so every number in the SI tables comes
from the same CSV files as the main-text figures.
"""
import os, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results", "v2", "asis")
MS = os.path.normpath(os.path.join(HERE, "..", "manuscript"))
N = [1, 3, 5, 7, 9]
LAB = {"mag_argmax": "M", "argmax_hh": "A", "midpoint": "MP", "sym": "S", "sym_lin": "S+", "psl": "P", "circle": "C"}
LIQ = {"water": "water", "ipa": "isopropanol", "gluc05": "glucose 5 %", "gluc075": "glucose 7.5 %", "gluc10": "glucose 10 %", "air": "air"}


def f(x, nd=1, sign=False):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return ("%+." + str(nd) + "f") % x if sign else ("%." + str(nd) + "f") % x


def table(header, rows):
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(r) + " |" for r in rows])


def t_phases():
    g = pd.read_csv(os.path.join(R, "phases.csv")); rows = []
    for ds in ("DS-2", "DS-3"):
        for ph in [p for p in ("air", "water", "ipa", "gluc05", "gluc075", "gluc10") if p in set(g[g.dataset == ds].phase)]:
            for n in N:
                a = g[(g.dataset == ds) & (g.phase == ph) & (g.n == n) & (g.estimator == "argmax_hh")].iloc[0]; p = g[(g.dataset == ds) & (g.phase == ph) & (g.n == n) & (g.estimator == "psl")].iloc[0]
                rows.append([ds, LIQ[ph], str(n), "%.0f ± %.0f" % (a.fres, a.fres_sd), "%.0f ± %.0f" % (p.fres, p.fres_sd), "%.1f ± %.1f" % (a.gamma, a.gamma_sd), "%.1f ± %.1f" % (p.gamma, p.gamma_sd), f(a.D_ppm), f(p.D_ppm), "%.1f ± %.2f" % (p.phi, p.phi_sd), "%.0f/3" % (3 * p.fold)])
    return table(["dataset", "medium", "n", "f (A) [Hz]", "f (P) [Hz]", "Γ (A) [Hz]", "Γ (P) [Hz]", "D (A) [10⁻⁶]", "D (P) [10⁻⁶]", "φ (P) [°]", "fold"], rows)


def t_shifts(ests):
    sh = pd.read_csv(os.path.join(R, "shifts.csv")); rows = []
    for _, r in sh[sh.estimator.isin(ests)].iterrows():
        rows.append([r.dataset, LIQ[r.liquid], str(int(r.n)), LAB[r.estimator], "%.0f ± %.0f" % (r.df, r.df_sd), f(r.df_over_n, 0), ("%.0f ± %.0f" % (r.dG, r.dG_sd)) if np.isfinite(r.dG) else "—", f(r.dG_over_n, 0),
                     f(r.df_KG, 0), f(100 * r.eps_f, 1, True), f(100 * r.eps_G, 1, True), f(r.r_KG1, 3), f(r.dD_ppm, 1)])
    return table(["dataset", "liquid", "n", "est.", "Δf [Hz]", "Δf/n", "ΔΓ [Hz]", "ΔΓ/n", "Δf_KG", "ε_f [%]", "ε_Γ [%]", "r = ΔΓ/(−Δf)", "ΔD [10⁻⁶]"], rows)


def t_summary():
    S = json.load(open(os.path.join(R, "summary.json")))["summary_n3_9"]; rows = []
    for ds in ("DS-2", "DS-3"):
        for est in ("mag_argmax", "argmax_hh", "midpoint", "sym", "sym_lin", "circle", "psl"):
            s = S[ds][est]
            rows.append([ds, LAB[est], "%s … %s" % (f(100 * s["eps_f"][0], 1, True), f(100 * s["eps_f"][1], 1, True)), "%s … %s" % (f(100 * s["eps_G"][0], 1, True), f(100 * s["eps_G"][1], 1, True)),
                         "%s … %s" % (f(s["r_KG1_water"][0], 2), f(s["r_KG1_water"][1], 2)), "%s … %s" % (f(s["r_KG1_all_liquids"][0], 2), f(s["r_KG1_all_liquids"][1], 2)), f(100 * s["max_abs_eps_f"], 1)])
    return table(["dataset", "estimator", "ε_f [%]", "ε_Γ [%]", "r_n (water)", "r_n (all liquids)", "max |ε_f| [%]"], rows)


def t_kg2():
    k = pd.read_csv(os.path.join(R, "kg2_slopes.csv")); rows = []
    for _, r in k[k.estimator.isin(("argmax_hh", "psl"))].sort_values(["dataset", "liquid", "estimator", "fit"]).iterrows():
        rows.append([r.dataset, LIQ[r.liquid], LAB[r.estimator], r.fit, f(r.b_df, 3), f(r.b_dG, 3), f(r.k_df, 0), f(r.k_dG, 0), f(r.k_KG, 0), f(100 * r.cv_df_sqrtn, 1), f(100 * r.cv_dG_sqrtn, 1)])
    return table(["dataset", "liquid", "est.", "fit", "b(Δf)", "b(ΔΓ)", "k(−Δf) [Hz/√n]", "k(ΔΓ)", "k_KG", "CV(−Δf/√n) [%]", "CV(ΔΓ/√n) [%]"], rows)


def t_rep():
    r = pd.read_csv(os.path.join(R, "exp1_reproducibility.csv")); rows = []
    for _, x in r.iterrows():
        rows.append([str(int(x.n)), f(x.DS2_A_df_over_n, 0), f(x.DS3_A_df_over_n, 0), f(x.DS2_P_df_over_n, 0), f(x.DS3_P_df_over_n, 0), f(x.DS2_A_dG_over_n, 0), f(x.DS3_A_dG_over_n, 0), f(x.DS2_P_dG_over_n, 0), f(x.DS3_P_dG_over_n, 0),
                     f(100 * x.DS2_P_eps_f, 1, True), f(100 * x.DS3_P_eps_f, 1, True), f(100 * x.DS2_P_eps_G, 1, True), f(100 * x.DS3_P_eps_G, 1, True), f(x.DS2_P_r, 2), f(x.DS3_P_r, 2), f(x.DS2_P_phi_liq, 1), f(x.DS3_P_phi_liq, 1),
                     f(100 * x.dl0911_A_eps_f, 1, True), f(100 * x.dl0910_A_eps_f, 1, True)])
    return table(["n", "Δf/n A DS-2", "DS-3", "Δf/n P DS-2", "DS-3", "ΔΓ/n A DS-2", "DS-3", "ΔΓ/n P DS-2", "DS-3", "ε_f P DS-2 [%]", "DS-3", "ε_Γ P DS-2 [%]", "DS-3", "r P DS-2", "DS-3", "φ_water DS-2 [°]", "DS-3", "ε_f A live 09-11 [%]", "09-10"], rows)


def t_claim():
    c = pd.read_csv(os.path.join(R, "claim_8pct.csv")); rows = []
    for _, r in c.iterrows():
        rows.append([r.dataset, LIQ[r.liquid], str(int(r.n)), f(100 * r.eps_f_P, 1, True), f(100 * r.eps_G_P, 1, True), f(100 * r.eps_f_A, 1, True), f(100 * r.eps_G_A, 1, True), "%s / %s" % ("yes" if r.P_f_within_8 else "no", "yes" if r.P_G_within_8 else "no"), "%s / %s" % ("yes" if r.A_f_within_8 else "no", "yes" if r.A_G_within_8 else "no")])
    return table(["dataset", "liquid", "n", "ε_f P [%]", "ε_Γ P [%]", "ε_f A [%]", "ε_Γ A [%]", "P within 8 % (f / Γ)", "A within 8 % (f / Γ)"], rows)


def t_bias():
    b = pd.read_csv(os.path.join(R, "bias_per_overtone.csv")); rows = []
    for _, r in b.iterrows():
        rows.append([r.dataset, LIQ[r.phase], str(int(r.n)), f(r.gamma, 0), f(r.phi, 1), "%+.0f ± %.0f" % (r.bias_meas, r.bias_meas_sd), f(r.bias_pred, 0, True), f(r.resid, 0, True), f(r.resid_over_gamma, 3, True), f(r.hh_meas, 3), f(r.hh_pred, 3)])
    return table(["dataset", "medium", "n", "Γ_P [Hz]", "φ [°]", "f_Gmax − f_res [Hz]", "Γ tan(φ/2) [Hz]", "meas − pred [Hz]", "(meas − pred)/Γ", "Γ_hh/Γ_P", "√(1+2tan²(φ/2))"], rows)


def t_phi():
    p = pd.read_csv(os.path.join(R, "phi_all.csv")); st = pd.read_csv(os.path.join(R, "phi_stability.csv")); bw = pd.read_csv(os.path.join(R, "phi_between.csv")); mo = pd.read_csv(os.path.join(R, "phi_monotonicity.csv"))
    rows = [[r.dataset, LIQ.get(r.medium, r.medium), str(int(r.n)), f(r.f_MHz, 3), f(r.phi, 1), f(r.phi_sd, 2), f(r.phi_min, 1), f(r.phi_max, 1), str(int(r.nrep))] for _, r in p.iterrows()]
    t1 = table(["dataset", "medium", "n", "f [MHz]", "φ [°]", "sd", "min", "max", "sweeps"], rows)
    rows = [[r.dataset, str(int(r.n)), f(r.phi_air, 1), "%.1f … %.1f" % (r.phi_liquid_min, r.phi_liquid_max), f(r.liquid_range, 1), f(r.air_minus_liquid_mean, 1, True), f(r.all_media_range, 1), f(r.replica_sd_max, 2)] for _, r in st.iterrows()]
    t2 = table(["dataset", "n", "φ air", "φ liquids (min … max)", "range over liquids", "air − mean(liquids)", "range over all media", "max replica sd"], rows)
    rows = [[str(int(r.n)), f(r.phi_air_DS2, 1), f(r.phi_air_0903, 1), f(r.phi_air_DS3, 1), f(r.d0903_minus_DS2, 1, True), f(r.DS3_minus_DS2, 1, True)] for _, r in bw.iterrows()]
    t3 = table(["n", "φ air DS-2 (board 1920, 09-11)", "air 2026-09-03", "φ air DS-3 (2024)", "09-03 − DS-2", "DS-3 − DS-2"], rows)
    rows = [[r.dataset, LIQ.get(r.medium, r.medium), r.phi_1_to_9, "yes" if r.monotonic else "no", f(r.max_nonmonotonic_step, 1)] for _, r in mo.iterrows()]
    t4 = table(["dataset", "medium", "φ(n = 1 … 9) [°]", "monotonic in n", "largest step in the wrong direction [°]"], rows)
    return "(a) every dataset and medium\n\n" + t1 + "\n\n(b) stability per overtone\n\n" + t2 + "\n\n(c) between boards and days, air\n\n" + t3 + "\n\n(d) monotonicity\n\n" + t4


def t_glucose():
    x = pd.read_csv(os.path.join(R, "glucose_xrel.csv")); c = pd.read_csv(os.path.join(R, "glucose_xrel_vs_conc.csv")); rs = pd.read_csv(os.path.join(R, "glucose_resolution.csv"))
    rows = [[LAB[r.estimator], LIQ[r.liquid], f(r.conc, 1), " / ".join("%.3f" % r["x_df_n%d" % n] for n in N), "%.3f ± %.3f" % (r.x_df_n3_9, r.x_df_sd_n), " / ".join("%.3f" % r["x_dG_n%d" % n] for n in N), "%.3f ± %.3f" % (r.x_dG_n3_9, r.x_dG_sd_n), " / ".join("%.3f" % r["x_both_n%d" % n] for n in N), "%.3f ± %.3f" % (r.x_both_n3_9, r.x_both_sd_n)] for _, r in x.iterrows()]
    t1 = table(["est.", "liquid", "% w/v", "x from Δf, n = 1…9", "mean 3–9 ± sd_n", "x from ΔΓ", "mean ± sd_n", "x from both", "mean ± sd_n"], rows)
    rows = [[LAB[r.estimator], r.quantity.replace("x_", "from ").replace("_n3_9", ", n = 3–9").replace("df", "Δf").replace("dG", "ΔΓ"), f(r.slope_per_pct, 5), f(r.intercept, 4), f(r.resid5, 4, True), f(r.rms, 4)] for _, r in c.iterrows()]
    t2 = table(["est.", "x_rel", "slope [per % w/v]", "intercept", "residual of the 5 % point", "rms"], rows)
    rows = []
    for _, r in rs.iterrows():
        rows.append([LAB[r.estimator], str(int(r.n)), f(r.sd_f_liquid, 1), f(r.sd_G_liquid, 1), f(r.slope_f_Hz_per_x, 0), f(r.slope_G_Hz_per_x, 0), f(r.res_x_f, 4), f(r.res_x_G, 4),
                     "%.3f (%.0f)" % (r.step_water_gluc05_dx_f, r.step_water_gluc05_sigma_f), "%.3f (%.0f)" % (r.step_water_gluc05_dx_G, r.step_water_gluc05_sigma_G),
                     "%.3f (%.0f)" % (r.step_gluc05_gluc075_dx_f, r.step_gluc05_gluc075_sigma_f), "%.3f (%.0f)" % (r.step_gluc05_gluc075_dx_G, r.step_gluc05_gluc075_sigma_G),
                     "%.3f (%.0f)" % (r.step_gluc075_gluc10_dx_f, r.step_gluc075_gluc10_sigma_f), "%.3f (%.0f)" % (r.step_gluc075_gluc10_dx_G, r.step_gluc075_gluc10_sigma_G)])
    t3 = table(["est.", "n", "sd f [Hz]", "sd Γ [Hz]", "slope f [Hz per x]", "slope Γ", "σ_x from f", "σ_x from Γ", "water→5 %: Δx_f (σ)", "Δx_Γ (σ)", "5→7.5 %: Δx_f (σ)", "Δx_Γ (σ)", "7.5→10 %: Δx_f (σ)", "Δx_Γ (σ)"], rows)
    return "(a) relative √(ρη) from the data, x = √(ρη)/√(ρη)_water\n\n" + t1 + "\n\n(b) x against concentration (least squares with intercept on 0, 5, 7.5, 10 % w/v)\n\n" + t2 + "\n\n(c) steps and resolution; σ_x = replica sd / slope, slope = the water shift of the same overtone\n\n" + t3


def t_datalog():
    d = pd.read_csv(os.path.join(R, "datalog_shifts.csv")); rows = []
    for _, r in d.iterrows():
        rows.append([r.dataset, LIQ[r.liquid], str(int(r.n)), "%.0f ± %.0f" % (r.df, r.df_sd), f(100 * r.eps_f, 1, True), "%.0f ± %.0f" % (r.dG, r.dG_sd), f(100 * r.eps_G, 1, True), f(r.r_KG1, 2)])
    return table(["run", "liquid", "n", "Δf [Hz]", "ε_f [%]", "ΔΓ [Hz]", "ε_Γ [%]", "r_n"], rows)


TABLES = {"phases": t_phases, "shifts_main": lambda: t_shifts(("argmax_hh", "psl")), "shifts_other": lambda: t_shifts(("mag_argmax", "midpoint", "sym", "sym_lin", "circle")),
          "summary": t_summary, "kg2": t_kg2, "rep": t_rep, "claim": t_claim, "bias": t_bias, "phi": t_phi, "glucose": t_glucose, "datalog": t_datalog}

if __name__ == "__main__":
    s = open(os.path.join(MS, "supporting_information.template.md")).read()
    for k, fn in TABLES.items():
        tag = "{{TABLE:%s}}" % k
        assert tag in s, tag
        s = s.replace(tag, fn())
    assert "{{TABLE:" not in s
    open(os.path.join(MS, "supporting_information.md"), "w").write(s)
    print("wrote supporting_information.md", len(s), "chars")
