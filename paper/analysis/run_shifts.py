# -*- coding: utf-8 -*-
"""
run_shifts.py — from results/sweeps_<variant>.csv to the physics tables:
per phase and overtone mean ± sd over the three replicas; air→liquid shifts
Δf_n, ΔΓ_n, Δf_n/n, ΔΓ_n/n; Kanazawa–Gordon at 25 °C; the three error metrics
    eps_f  = Δf/Δf_KG − 1,   eps_G = ΔΓ/ΔΓ_KG − 1,   rho = |Δf|/ΔΓ  (KG: 1),
√n slopes through the origin; repeatability; gate statistics. Writes
results/shifts_<variant>.csv, results/summary_<variant>.json and
results/tables_<variant>.md.
"""
import os, json, sys
import numpy as np, pandas as pd
import qcmchain as q

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
EST = ["mag_argmax", "argmax_hh", "midpoint", "sym", "sym_lin", "psl", "circle"]
LABEL = {"mag_argmax": "magnitude maximum (|H| dB)", "argmax_hh": "max G + half-height width",
         "midpoint": "midpoint of half-height crossings", "sym": "symmetric Lorentzian (4 par.)",
         "sym_lin": "symmetric Lorentzian + linear bg (5 par.)", "psl": "phase-shifted Lorentzian (5 par.)",
         "circle": "BVD admittance circle (repo FIT 1)"}
N = np.array([1, 3, 5, 7, 9], float)


def run(variant):
    d = pd.read_csv(os.path.join(R, "sweeps_%s.csv" % variant))
    g = d.groupby(["phase", "n", "estimator"]).agg(
        fres=("fres", "mean"), fres_sd=("fres", "std"), gamma=("gamma", "mean"), gamma_sd=("gamma", "std"),
        D_ppm=("D_ppm", "mean"), D_sd=("D_ppm", "std"), rms_rel=("rms_rel", "mean"), rms_max=("rms_rel", "max"),
        phi=("phi_deg", "mean"), phi_sd=("phi_deg", "std"), nrep=("fres", "count")).reset_index()
    f0 = float(g[(g.phase == "air") & (g.n == 1) & (g.estimator == "psl")].fres.iloc[0])   # fundamental in air, PSL
    f0_arg = float(g[(g.phase == "air") & (g.n == 1) & (g.estimator == "argmax_hh")].fres.iloc[0])
    rows = []
    for liq in ("water", "ipa"):
        kg = q.kanazawa_gordon(f0, N, **q.LIQUIDS[liq])
        for est in EST:
            a = g[(g.phase == "air") & (g.estimator == est)].set_index("n")
            l = g[(g.phase == liq) & (g.estimator == est)].set_index("n")
            for i, n in enumerate(N):
                n = int(n)
                if n not in a.index or n not in l.index:
                    continue
                df = l.loc[n, "fres"] - a.loc[n, "fres"]; dG = l.loc[n, "gamma"] - a.loc[n, "gamma"]
                rows.append(dict(variant=variant, liquid=liq, n=n, estimator=est,
                                 f_air=a.loc[n, "fres"], f_air_sd=a.loc[n, "fres_sd"], f_liq=l.loc[n, "fres"], f_liq_sd=l.loc[n, "fres_sd"],
                                 G_air=a.loc[n, "gamma"], G_air_sd=a.loc[n, "gamma_sd"], G_liq=l.loc[n, "gamma"], G_liq_sd=l.loc[n, "gamma_sd"],
                                 df=df, df_sd=np.hypot(a.loc[n, "fres_sd"], l.loc[n, "fres_sd"]), dG=dG, dG_sd=np.hypot(a.loc[n, "gamma_sd"], l.loc[n, "gamma_sd"]),
                                 df_over_n=df / n, dG_over_n=dG / n, df_KG=kg[i], dG_KG=-kg[i],
                                 eps_f=df / kg[i] - 1.0, eps_G=dG / (-kg[i]) - 1.0, rho=abs(df) / dG if dG else np.nan,
                                 dD_ppm=l.loc[n, "D_ppm"] - a.loc[n, "D_ppm"], dD_KG_ppm=2e6 * (-kg[i]) / (n * f0),
                                 rms_liq=l.loc[n, "rms_rel"], phi_air=a.loc[n, "phi"], phi_liq=l.loc[n, "phi"]))
    sh = pd.DataFrame(rows)
    sh.to_csv(os.path.join(R, "shifts_%s.csv" % variant), index=False)
    g.to_csv(os.path.join(R, "phases_%s.csv" % variant), index=False)

    # sqrt(n) slopes through the origin, all five overtones and n >= 3
    slopes = []
    for liq in ("water", "ipa"):
        kg_k = float(abs(q.kanazawa_gordon(f0, 1, **q.LIQUIDS[liq])))
        for est in EST:
            s = sh[(sh.liquid == liq) & (sh.estimator == est)].sort_values("n")
            if s.dG.isna().any() or s.df.isna().any():
                continue
            x = np.sqrt(s.n.values.astype(float))
            def k(y, sel):
                return float(np.sum(x[sel] * y[sel]) / np.sum(x[sel] ** 2))
            sel_all = np.ones(len(x), bool); sel_3 = s.n.values >= 3
            slopes.append(dict(variant=variant, liquid=liq, estimator=est, k_KG=kg_k,
                               k_df_all=k(-s.df.values, sel_all), k_dG_all=k(s.dG.values, sel_all),
                               k_df_n3=k(-s.df.values, sel_3), k_dG_n3=k(s.dG.values, sel_3)))
    sl = pd.DataFrame(slopes); sl.to_csv(os.path.join(R, "slopes_%s.csv" % variant), index=False)

    # gate / failure statistics
    p = d[d.estimator == "psl"]; sym = d[d.estimator == "sym"]
    gate = dict(psl_n=int(len(p)), psl_accepted=int(p.gate_ok.sum()), psl_converged=int(p.converged.sum()),
                psl_rms_max=float(p.rms_rel.max()), psl_rms_air=[float(p[p.phase == "air"].rms_rel.min()), float(p[p.phase == "air"].rms_rel.max())],
                psl_rms_liquid=[float(p[p.phase != "air"].rms_rel.min()), float(p[p.phase != "air"].rms_rel.max())],
                sym_converged=int(sym.converged.sum()), sym_rms_air=[float(sym[sym.phase == "air"].rms_rel.min()), float(sym[sym.phase == "air"].rms_rel.max())],
                sym_rms_liquid=[float(sym[sym.phase != "air"].rms_rel.min()), float(sym[sym.phase != "air"].rms_rel.max())],
                one_sided_hh=int(d[d.estimator == "argmax_hh"].one_sided.sum()), mag_w3_missing=int(d[d.estimator == "mag_argmax"].gamma.isna().sum()))

    # ------------------------------------------------------------- markdown
    L = ["# Estimator comparison on the 45 sweeps of 2026-09-11 — variant `%s`\n" % variant,
         "f0 (air, PSL) = %.0f Hz; f0 (air, argmax) = %.0f Hz. Kanazawa–Gordon with ρ_q = %.0f kg/m³, μ_q = %.3e Pa; water ρ = %.2f kg/m³, η = %.3f mPa·s; isopropanol ρ = %.1f kg/m³, η = %.3f mPa·s (25 °C).\n"
         % (f0, f0_arg, q.RHO_Q, q.MU_Q, q.LIQUIDS["water"]["rho"], 1e3 * q.LIQUIDS["water"]["eta"], q.LIQUIDS["ipa"]["rho"], 1e3 * q.LIQUIDS["ipa"]["eta"]),
         "Error metrics: eps_f = Δf/Δf_KG − 1; eps_Γ = ΔΓ/ΔΓ_KG − 1; ρ = |Δf|/ΔΓ (1 for a Newtonian liquid, independent of ρη). Shifts are liquid plateau minus air plateau, each the mean of three sweeps; sd = quadrature sum of the two replica sd.\n"]
    L.append("## Per phase and overtone (mean ± sd over three replicas)\n")
    L.append("| phase | n | estimator | f [Hz] | sd | Γ [Hz] | sd | D [ppm] | rms fit [% range] | φ [°] |\n|---|---|---|---|---|---|---|---|---|---|")
    for _, r in g.iterrows():
        L.append("| %s | %d | %s | %.0f | %.1f | %.1f | %.1f | %.1f | %s | %s |" % (
            r.phase, r.n, r.estimator, r.fres, r.fres_sd, r.gamma, r.gamma_sd, r.D_ppm,
            ("%.2f" % (100 * r.rms_rel)) if np.isfinite(r.rms_rel) else "—", ("%.1f ± %.1f" % (r.phi, r.phi_sd)) if np.isfinite(r.phi) else "—"))
    for liq in ("water", "ipa"):
        L.append("\n## air → %s against Kanazawa–Gordon\n" % liq)
        L.append("| n | estimator | Δf [Hz] | sd | Δf/n | Δf_KG | eps_f [%] | ΔΓ [Hz] | sd | ΔΓ/n | eps_Γ [%] | ρ = \\|Δf\\|/ΔΓ | ΔD [ppm] | ΔD_KG |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in sh[sh.liquid == liq].iterrows():
            L.append("| %d | %s | %.0f | %.0f | %.0f | %.0f | %+.1f | %.0f | %.0f | %.0f | %+.1f | %.3f | %.1f | %.1f |" % (
                r.n, r.estimator, r.df, r.df_sd, r.df_over_n, r.df_KG, 100 * r.eps_f, r.dG, r.dG_sd, r.dG_over_n, 100 * r.eps_G, r.rho, r.dD_ppm, r.dD_KG_ppm))
    L.append("\n## √n slopes through the origin [Hz/√n]\n")
    L.append("| liquid | estimator | k_KG | k(−Δf), n=1–9 | k(ΔΓ), n=1–9 | k(−Δf), n=3–9 | k(ΔΓ), n=3–9 |\n|---|---|---|---|---|---|---|")
    for _, r in sl.iterrows():
        L.append("| %s | %s | %.0f | %.0f | %.0f | %.0f | %.0f |" % (r.liquid, r.estimator, r.k_KG, r.k_df_all, r.k_dG_all, r.k_df_n3, r.k_dG_n3))
    L.append("\n## Summary of the error metrics on overtones 3–9 (range over n and both liquids)\n")
    L.append("| estimator | eps_f [%] | eps_Γ [%] | ρ | max \\|eps_f\\| | max \\|eps_Γ\\| |\n|---|---|---|---|---|---|")
    summ = {}
    for est in EST:
        s = sh[(sh.estimator == est) & (sh.n >= 3)]
        if s.empty or s.eps_f.isna().all():
            continue
        summ[est] = dict(eps_f=[float(s.eps_f.min()), float(s.eps_f.max())], eps_G=[float(s.eps_G.min()), float(s.eps_G.max())],
                         rho=[float(s.rho.min()), float(s.rho.max())], max_abs_eps_f=float(s.eps_f.abs().max()), max_abs_eps_G=float(s.eps_G.abs().max()))
        L.append("| %s | %+.1f … %+.1f | %+.1f … %+.1f | %.2f … %.2f | %.1f | %.1f |" % (
            est, 100 * s.eps_f.min(), 100 * s.eps_f.max(), 100 * s.eps_G.min(), 100 * s.eps_G.max(), s.rho.min(), s.rho.max(), 100 * s.eps_f.abs().max(), 100 * s.eps_G.abs().max()))
    L.append("\n## Fundamental (n = 1), both liquids\n")
    L.append("| estimator | liquid | eps_f [%] | eps_Γ [%] | ρ |\n|---|---|---|---|---|")
    for _, r in sh[sh.n == 1].iterrows():
        L.append("| %s | %s | %+.1f | %+.1f | %.2f |" % (r.estimator, r.liquid, 100 * r.eps_f, 100 * r.eps_G, r.rho))
    L.append("\n## Fit convergence and gate\n")
    L.append("```\n%s\n```" % json.dumps(gate, indent=1))
    open(os.path.join(R, "tables_%s.md" % variant), "w").write("\n".join(L) + "\n")
    json.dump(dict(f0=f0, f0_argmax=f0_arg, gate=gate, summary_n3_9=summ,
                   shifts=sh.to_dict(orient="records"), slopes=sl.to_dict(orient="records")),
              open(os.path.join(R, "summary_%s.json" % variant), "w"), indent=1, default=float)
    print("\n".join(L[-40:]))


if __name__ == "__main__":
    for v in (sys.argv[1:] or ("asis", "fwfix")):
        run(v)
