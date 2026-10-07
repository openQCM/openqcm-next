# -*- coding: utf-8 -*-
"""
run_glucose.py — the 2024-05-29 dataset (second instrument, second crystal: air → water → glucose 5, 7.5, 10 % w/v,
three replicas per phase, overtones 1–9, software/firmware 0.1.5) through the same estimators as the 2026 data.

    python run_glucose.py [--npz PATH] [--root DIR]     (default: research/glucose-2024-05-29/data/sweep_raw_2024-05-29.npz)

Writes results/glucose_sweeps_<variant>.csv, glucose_phases_<variant>.csv, glucose_shifts_<variant>.csv (shifts vs air
and vs water), glucose_conc_<variant>.csv (concentration slopes, ρη relative to water), glucose_phi_<variant>.csv
(φ₀ − 360·f·τ decomposition), glucose_tables_<variant>.md, glucose_summary_<variant>.json. Kanazawa–Gordon only for water;
for the glucose solutions only liquid-constant-free quantities: the Newtonian ratio |Δf|/ΔΓ and ρη/(ρη)_water = (Δf/Δf_water)².
"""
import os, sys, json, argparse
import numpy as np, pandas as pd
import qcmchain as q, data
from run_estimators import analyse_sweep
from run_shifts import EST

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
N = np.array([1, 3, 5, 7, 9], float)


def load(args):
    if args.root:
        return data.glucose_0529(root=args.root)
    if args.npz:
        data.GLUC_NPZ = args.npz
    return data.glucose_0529()


def estimators(dumps, mt, variant, fix):
    rows = []
    for (s, n), (f, vm, vp) in sorted(dumps.items()):
        rr, _ = analyse_sweep(f, vm, vp, fix)
        ph = s.rsplit("_", 1)[0]
        for r in rr:
            r.update(set=s, phase=ph, n=n, replica=int(s[-2:]), conc=data.GLUC_CONC[ph], mtime=mt[(s, n)])
        rows += rr
        print(variant, s, n, "fold" if rr[0]["fold"] else "no fold", flush=True)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(R, "glucose_sweeps_%s.csv" % variant), index=False)
    return df


def lsq_line(x, y):
    """OLS with intercept: slope, intercept, R²; and slope through the origin."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ sol; ss = float(np.sum((y - y.mean()) ** 2)); r2 = 1 - float(np.sum((y - yhat) ** 2)) / ss if ss > 0 else np.nan
    k0 = float(np.sum(x * y) / np.sum(x * x)) if np.sum(x * x) > 0 else np.nan
    return float(sol[0]), float(sol[1]), r2, k0


def run(variant, d):
    g = d.groupby(["phase", "n", "estimator"]).agg(
        fres=("fres", "mean"), fres_sd=("fres", "std"), gamma=("gamma", "mean"), gamma_sd=("gamma", "std"),
        D_ppm=("D_ppm", "mean"), D_sd=("D_ppm", "std"), rms_rel=("rms_rel", "mean"), phi=("phi_deg", "mean"), phi_sd=("phi_deg", "std"),
        fold=("fold", "mean")).reset_index()
    g["conc"] = g.phase.map(data.GLUC_CONC)
    g.to_csv(os.path.join(R, "glucose_phases_%s.csv" % variant), index=False)
    f0 = float(g[(g.phase == "air") & (g.n == 1) & (g.estimator == "psl")].fres.iloc[0])
    kg_w = q.kanazawa_gordon(f0, N, **q.LIQUIDS["water"])
    rows = []
    for ref in ("air", "water"):
        for liq in ("water", "gluc05", "gluc075", "gluc10"):
            if liq == ref: continue
            for est in EST:
                a = g[(g.phase == ref) & (g.estimator == est)].set_index("n"); l = g[(g.phase == liq) & (g.estimator == est)].set_index("n")
                for i, n in enumerate(N):
                    n = int(n)
                    if n not in a.index or n not in l.index: continue
                    df = l.loc[n, "fres"] - a.loc[n, "fres"]; dG = l.loc[n, "gamma"] - a.loc[n, "gamma"]; dD = l.loc[n, "D_ppm"] - a.loc[n, "D_ppm"]
                    row = dict(variant=variant, ref=ref, liquid=liq, conc=data.GLUC_CONC[liq], n=n, estimator=est,
                               df=df, df_sd=np.hypot(a.loc[n, "fres_sd"], l.loc[n, "fres_sd"]), dG=dG, dG_sd=np.hypot(a.loc[n, "gamma_sd"], l.loc[n, "gamma_sd"]),
                               dD_ppm=dD, df_over_n=df / n, dG_over_n=dG / n, rho=abs(df) / dG if dG else np.nan)
                    if ref == "air" and liq == "water":
                        row.update(df_KG=kg_w[i], eps_f=df / kg_w[i] - 1.0, eps_G=dG / (-kg_w[i]) - 1.0, dD_KG_ppm=2e6 * (-kg_w[i]) / (n * f0))
                    rows.append(row)
    sh = pd.DataFrame(rows); sh.to_csv(os.path.join(R, "glucose_shifts_%s.csv" % variant), index=False)

    # concentration series: OLS of the shift vs air-referenced? No: vs WATER (0 %), points at 0, 5, 7.5, 10 % w/v
    conc_rows = []
    for est in EST:
        for n in N.astype(int):
            x, yf, yG, yD = [0.0], [0.0], [0.0], [0.0]
            for liq in ("gluc05", "gluc075", "gluc10"):
                s = sh[(sh.ref == "water") & (sh.liquid == liq) & (sh.estimator == est) & (sh.n == n)]
                if s.empty or not np.isfinite(s.df.iloc[0]): continue
                x.append(s.conc.iloc[0]); yf.append(s.df.iloc[0]); yG.append(s.dG.iloc[0]); yD.append(s.dD_ppm.iloc[0])
            if len(x) < 4: continue
            kf, bf, r2f, kf0 = lsq_line(x, yf); kG, bG, r2G, kG0 = lsq_line(x, yG); kD, bD, r2D, kD0 = lsq_line(x, yD)
            # rho*eta relative to water from the air-referenced shifts: (df_liq / df_water)^2
            rel = {}
            for liq in ("gluc05", "gluc075", "gluc10"):
                a = sh[(sh.ref == "air") & (sh.liquid == liq) & (sh.estimator == est) & (sh.n == n)]
                w = sh[(sh.ref == "air") & (sh.liquid == "water") & (sh.estimator == est) & (sh.n == n)]
                rel[liq] = float((a.df.iloc[0] / w.df.iloc[0]) ** 2) if len(a) and len(w) and w.df.iloc[0] else np.nan
                rel[liq + "_G"] = float((a.dG.iloc[0] / w.dG.iloc[0]) ** 2) if len(a) and len(w) and w.dG.iloc[0] else np.nan
            conc_rows.append(dict(variant=variant, estimator=est, n=n, k_df=kf, b_df=bf, r2_df=r2f, k0_df=kf0, k_dG=kG, b_dG=bG, r2_dG=r2G, k0_dG=kG0,
                                  k_dD=kD, b_dD=bD, r2_dD=r2D, k0_dD=kD0, resid5_df=yf[1] - (kf * x[1] + bf), resid5_dG=yG[1] - (kG * x[1] + bG), resid5_dD=yD[1] - (kD * x[1] + bD),
                                  rhoeta_rel_05=rel["gluc05"], rhoeta_rel_075=rel["gluc075"], rhoeta_rel_10=rel["gluc10"],
                                  rhoeta_relG_05=rel["gluc05_G"], rhoeta_relG_075=rel["gluc075_G"], rhoeta_relG_10=rel["gluc10_G"]))
    cc = pd.DataFrame(conc_rows); cc.to_csv(os.path.join(R, "glucose_conc_%s.csv" % variant), index=False)

    # phi decomposition phi = phi0 - 360 f tau, per phase, all n and n >= 3
    p = d[d.estimator == "psl"]; phi_rows = []
    for ph, s in p.groupby("phase"):
        m = s.groupby("n").agg(f=("fres", "mean"), phi=("phi_deg", "mean"), sd=("phi_deg", "std")).reset_index()
        for label, sel in (("n=1-9", m.n >= 1), ("n=3-9", m.n >= 3)):
            x = -360.0 * m.f[sel].values * 1e-9; y = m.phi[sel].values            # phi = phi0 + x*tau[ns]
            A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, y, rcond=None)
            rms = float(np.sqrt(np.mean((A @ sol - y) ** 2)))
            phi_rows.append(dict(variant=variant, phase=ph, fit=label, phi0_deg=float(sol[1]), tau_ns=float(sol[0]), rms_deg=rms,
                                 **{"phi_n%d" % int(n): float(v) for n, v in zip(m.n, m.phi)}, **{"sd_n%d" % int(n): float(v) for n, v in zip(m.n, m.sd)}))
    pf = pd.DataFrame(phi_rows); pf.to_csv(os.path.join(R, "glucose_phi_%s.csv" % variant), index=False)

    # eq. 8 on the 75 sweeps; gate
    p = p.copy(); p["resid"] = p.bias_meas - p.bias_pred
    eq8 = dict(mean=float(p.resid.mean()), sd=float(p.resid.std()), maxabs=float(p.resid.abs().max()), maxabs_over_gamma=float((p.resid / p.gamma).abs().max()))
    gate = dict(n=int(len(p)), accepted=int(p.gate_ok.sum()), converged=int(p.converged.sum()), rms_air=[float(p[p.phase == "air"].rms_rel.min()), float(p[p.phase == "air"].rms_rel.max())],
                rms_liquid=[float(p[p.phase != "air"].rms_rel.min()), float(p[p.phase != "air"].rms_rel.max())],
                fold_by_phase={ph: [int(v) for v in s.sort_values(["n", "replica"]).fold.values] for ph, s in p.groupby("phase")})

    # --- drift within each plateau (slope of f vs write time over the three replicas), time–concentration geometry
    tt = d.copy(); tt["t_min"] = (pd.to_datetime(tt.mtime) - pd.to_datetime(tt.mtime).min()).dt.total_seconds() / 60.0
    drift_rows = []
    for est in ("argmax_hh", "psl"):
        for ph in data.GLUC_PHASES:
            for n in N.astype(int):
                s = tt[(tt.estimator == est) & (tt.phase == ph) & (tt.n == n)].sort_values("t_min")
                if len(s) < 3: continue
                kf_, bf_, r2_, _ = lsq_line(s.t_min.values, s.fres.values); kG_, _, _, _ = lsq_line(s.t_min.values, s.gamma.values)
                drift_rows.append(dict(variant=variant, estimator=est, phase=ph, n=n, span_min=float(s.t_min.max() - s.t_min.min()), drift_f_Hz_per_min=kf_, drift_G_Hz_per_min=kG_,
                                       t_mean_min=float(s.t_min.mean())))
    dr = pd.DataFrame(drift_rows); dr.to_csv(os.path.join(R, "glucose_drift_%s.csv" % variant), index=False)
    # phase mean times vs concentration (liquids only): OLS t(c), residual of the 5 % phase
    tm = {ph: float(tt[(tt.estimator == "psl") & (tt.phase == ph)].t_min.mean()) for ph in ("water", "gluc05", "gluc075", "gluc10")}
    cx = np.array([0.0, 5.0, 7.5, 10.0]); ty = np.array([tm["water"], tm["gluc05"], tm["gluc075"], tm["gluc10"]])
    kt, bt, _, _ = lsq_line(cx, ty); dt5 = float(ty[1] - (kt * 5.0 + bt))        # minutes; negative = the 5 % plateau is early
    geom = dict(phase_mean_times_min=tm, t_slope_min_per_pct=kt, dt5_min=dt5)
    # drift needed to explain the 5 % residual by a time-linear drift alone, per estimator and overtone
    for est in ("argmax_hh", "psl"):
        for n in N.astype(int):
            i = cc[(cc.estimator == est) & (cc.n == n)].index
            if len(i): cc.loc[i, "drift_needed_Hz_per_min"] = cc.loc[i, "resid5_df"] / dt5
            glu = dr[(dr.estimator == est) & (dr.n == n) & (dr.phase != "air")]
            if len(i): cc.loc[i, "drift_measured_max_abs"] = float(glu.drift_f_Hz_per_min.abs().max()) if len(glu) else np.nan
    cc.to_csv(os.path.join(R, "glucose_conc_%s.csv" % variant), index=False)

    # --- clipped fit window on n = 7, 9: refit the PSL with a symmetric window limited by the sweep's right edge, and
    #     recompute the Gamma-based rho*eta ratio from those fits (both the liquid and the air reference refitted the same way)
    clip_rows = []
    fix = (variant == "fwfix")
    for n in (7, 9):
        refit = {}
        for ph in data.GLUC_PHASES:
            vals = []
            for r in data.GLUC_REPLICAS:
                f, vm, vp = dumps[("%s_%s" % (ph, r), n)]
                c = q.chain(f, vm, vp, firmware_fix=fix); e = q.argmax_halfheight(c["f"], c["G"])
                half = min(3.0 * e["gamma_hh"], float(c["f"][-1] - e["f_max"]), float(e["f_max"] - c["f"][0]))
                mask = np.abs(c["f"] - e["f_max"]) <= half
                p = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"], mask=mask)
                vals.append((p["fres"], p["gamma"], half / e["gamma_hh"], (c["f"][-1] - e["f_max"]) / e["gamma_hh"]))
            refit[ph] = np.array(vals).mean(axis=0)
        for liq in ("gluc05", "gluc075", "gluc10"):
            dG_l = refit[liq][1] - refit["air"][1]; dG_w = refit["water"][1] - refit["air"][1]; df_l = refit[liq][0] - refit["air"][0]; df_w = refit["water"][0] - refit["air"][0]
            full = cc[(cc.estimator == "psl") & (cc.n == n)].iloc[0]
            clip_rows.append(dict(variant=variant, n=n, liquid=liq, window_half_gamma=float(refit[liq][2]), right_edge_gamma=float(refit[liq][3]),
                                  rhoeta_relG_full=float(full["rhoeta_relG_%s" % {"gluc05": "05", "gluc075": "075", "gluc10": "10"}[liq]]), rhoeta_relG_sym=(dG_l / dG_w) ** 2,
                                  rhoeta_rel_full=float(full["rhoeta_rel_%s" % {"gluc05": "05", "gluc075": "075", "gluc10": "10"}[liq]]), rhoeta_rel_sym=(df_l / df_w) ** 2))
    cl = pd.DataFrame(clip_rows); cl.to_csv(os.path.join(R, "glucose_clipwindow_%s.csv" % variant), index=False)

    # ------------------------------------------------------------- markdown
    L = ["# Glucose series 2024-05-29 (second instrument, second crystal) — variant `%s`\n" % variant,
         "f0 (air, PSL) = %.0f Hz. Kanazawa–Gordon for water only (25 °C, ρ = 997.05 kg/m³, η = 0.890 mPa s). Glucose: no tabulated ρη used; ρη/(ρη)_water = (Δf/Δf_water)² from the air-referenced shifts.\n" % f0]
    L.append("## Per phase and overtone (mean ± sd over three replicas): A = max G + half height, P = phase-shifted Lorentzian\n")
    L.append("| phase | n | f (A) | f (P) | Γ (A) | Γ (P) | D (A) | D (P) | φ [°] | fold |\n|---|---|---|---|---|---|---|---|---|---|")
    for ph in data.GLUC_PHASES:
        for n in N.astype(int):
            a = g[(g.phase == ph) & (g.n == n) & (g.estimator == "argmax_hh")].iloc[0]; pp = g[(g.phase == ph) & (g.n == n) & (g.estimator == "psl")].iloc[0]
            L.append("| %s | %d | %.0f ± %.0f | %.0f ± %.0f | %.1f ± %.1f | %.1f ± %.1f | %.1f | %.1f | %.1f ± %.2f | %.0f/3 |" % (
                ph, n, a.fres, a.fres_sd, pp.fres, pp.fres_sd, a.gamma, a.gamma_sd, pp.gamma, pp.gamma_sd, a.D_ppm, pp.D_ppm, pp.phi, pp.phi_sd, 3 * pp.fold))
    L.append("\n## air → water against Kanazawa–Gordon\n")
    L.append("| n | estimator | Δf [Hz] | Δf/Δf_KG | ΔΓ [Hz] | ΔΓ/ΔΓ_KG | ρ = \\|Δf\\|/ΔΓ |\n|---|---|---|---|---|---|---|")
    for _, r in sh[(sh.ref == "air") & (sh.liquid == "water")].iterrows():
        L.append("| %d | %s | %.0f ± %.0f | %.3f | %.0f ± %.0f | %.3f | %.3f |" % (r.n, r.estimator, r.df, r.df_sd, r.eps_f + 1, r.dG, r.dG_sd, r.eps_G + 1, r.rho))
    L.append("\n## Newtonian ratio |Δf|/ΔΓ (air-referenced) per solution, overtones 3–9: range over n\n")
    L.append("| estimator | water | glucose 5 % | glucose 7.5 % | glucose 10 % |\n|---|---|---|---|---|")
    for est in EST:
        cells = []
        for liq in ("water", "gluc05", "gluc075", "gluc10"):
            s = sh[(sh.ref == "air") & (sh.liquid == liq) & (sh.estimator == est) & (sh.n >= 3)].rho
            cells.append("%.2f–%.2f" % (s.min(), s.max()) if s.notna().any() else "—")
        L.append("| %s | %s |" % (est, " | ".join(cells)))
    L.append("\n## Shifts relative to water (mean of three replicas) — A and P\n")
    L.append("| solution | n | Δf (A) | Δf (P) | ΔΓ (A) | ΔΓ (P) | ΔD (A) [10⁻⁶] | ΔD (P) [10⁻⁶] | ρ (A) | ρ (P) |\n|---|---|---|---|---|---|---|---|---|---|")
    for liq in ("gluc05", "gluc075", "gluc10"):
        for n in N.astype(int):
            a = sh[(sh.ref == "water") & (sh.liquid == liq) & (sh.estimator == "argmax_hh") & (sh.n == n)].iloc[0]
            pp = sh[(sh.ref == "water") & (sh.liquid == liq) & (sh.estimator == "psl") & (sh.n == n)].iloc[0]
            L.append("| %s | %d | %.0f ± %.0f | %.0f ± %.0f | %.0f ± %.0f | %.0f ± %.0f | %.1f | %.1f | %.2f | %.2f |" % (
                liq, n, a.df, a.df_sd, pp.df, pp.df_sd, a.dG, a.dG_sd, pp.dG, pp.dG_sd, a.dD_ppm, pp.dD_ppm, a.rho, pp.rho))
    L.append("\n## Concentration slopes (OLS with intercept on 0, 5, 7.5, 10 % w/v relative to water; k₀ = through the origin)\n")
    L.append("| estimator | n | k(Δf) [Hz/%] | R² | k₀(Δf) | k(ΔΓ) [Hz/%] | R² | k₀(ΔΓ) | k(ΔD) [10⁻⁶/%] | R² | residual of the 5 % point on Δf [Hz] | ρη/(ρη)_w at 5 / 7.5 / 10 % (from Δf) | same from ΔΓ |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in cc[cc.estimator.isin(["argmax_hh", "psl", "sym_lin"])].iterrows():
        L.append("| %s | %d | %.1f | %.3f | %.1f | %.1f | %.3f | %.1f | %.2f | %.3f | %+.0f | %.3f / %.3f / %.3f | %.3f / %.3f / %.3f |" % (
            r.estimator, r.n, r.k_df, r.r2_df, r.k0_df, r.k_dG, r.r2_dG, r.k0_dG, r.k_dD, r.r2_dD, r.resid5_df,
            r.rhoeta_rel_05, r.rhoeta_rel_075, r.rhoeta_rel_10, r.rhoeta_relG_05, r.rhoeta_relG_075, r.rhoeta_relG_10))
    L.append("\nρη/(ρη)_water, mean over n = 3–9 (from Δf): " + "; ".join(
        "%s: %.3f / %.3f / %.3f" % (est, cc[(cc.estimator == est) & (cc.n >= 3)].rhoeta_rel_05.mean(), cc[(cc.estimator == est) & (cc.n >= 3)].rhoeta_rel_075.mean(), cc[(cc.estimator == est) & (cc.n >= 3)].rhoeta_rel_10.mean())
        for est in ("argmax_hh", "psl")) + "\n")
    L.append("## The 5 % plateau against the concentration line (OLS with intercept), all overtones\n")
    L.append("| estimator | n | residual Δf [Hz] | residual ΔΓ [Hz] | residual ΔD [10⁻⁶] | drift needed [Hz/min] | max \\|drift\\| measured in the liquid plateaus [Hz/min] |\n|---|---|---|---|---|---|---|")
    for _, r in cc[cc.estimator.isin(["argmax_hh", "psl"])].iterrows():
        L.append("| %s | %d | %+.0f | %+.0f | %+.1f | %+.1f | %.2f |" % (r.estimator, r.n, r.resid5_df, r.resid5_dG, r.resid5_dD, r.drift_needed_Hz_per_min, r.drift_measured_max_abs))
    L.append("\nPhase mean write times [min from the first sweep]: %s; OLS time–concentration slope %.2f min per %%; the 5 %% plateau is %+.1f min off the time–concentration line, so a time-linear drift d maps into a 5 %%-point residual of d × (%.1f min).\n" % (
        ", ".join("%s %.1f" % kv for kv in geom["phase_mean_times_min"].items()), geom["t_slope_min_per_pct"], geom["dt5_min"], geom["dt5_min"]))
    L.append("## Drift within the plateaus (slope of f over the three replicas, PSL) [Hz/min]\n")
    L.append("| phase | span [min] | n = 1 | 3 | 5 | 7 | 9 |\n|---|---|---|---|---|---|---|")
    for ph in data.GLUC_PHASES:
        s = dr[(dr.estimator == "psl") & (dr.phase == ph)].set_index("n")
        L.append("| %s | %.1f | %s |" % (ph, s.span_min.iloc[0], " | ".join("%+.2f" % s.loc[n, "drift_f_Hz_per_min"] for n in N.astype(int))))
    L.append("\n## ρη/(ρη)_water from ΔΓ on n = 7, 9: full ±3Γ window (clipped by the sweep edge) against a symmetric window limited by the edge\n")
    L.append("| n | solution | right edge [Γ_hh] | symmetric half-window [Γ_hh] | from ΔΓ, full | from ΔΓ, symmetric | from Δf, full | from Δf, symmetric |\n|---|---|---|---|---|---|---|---|")
    for _, r in cl.iterrows():
        L.append("| %d | %s | %.2f | %.2f | %.3f | %.3f | %.3f | %.3f |" % (r.n, r.liquid, r.right_edge_gamma, r.window_half_gamma, r.rhoeta_relG_full, r.rhoeta_relG_sym, r.rhoeta_rel_full, r.rhoeta_rel_sym))
    L.append("\n## φ = φ₀ − 360·f·τ per phase\n")
    L.append("| phase | fit | φ₀ [°] | τ [ns] | rms [°] | φ(n=1…9) [°] |\n|---|---|---|---|---|---|")
    for _, r in pf.iterrows():
        L.append("| %s | %s | %.1f | %.2f | %.1f | %s |" % (r.phase, r.fit, r.phi0_deg, r.tau_ns, r.rms_deg, " / ".join("%.1f" % r["phi_n%d" % n] for n in N.astype(int))))
    L.append("\n## Eq. 8 on the 75 sweeps: measured − predicted = %+.0f ± %.0f Hz, max |.| = %.0f Hz (%.3f Γ)\n" % (eq8["mean"], eq8["sd"], eq8["maxabs"], eq8["maxabs_over_gamma"]))
    L.append("## Gate and fold\n```\n%s\n```" % json.dumps(gate, indent=1))
    open(os.path.join(R, "glucose_tables_%s.md" % variant), "w").write("\n".join(L) + "\n")
    json.dump(dict(f0=f0, eq8=eq8, gate=gate, geometry=geom, shifts=sh.to_dict(orient="records"), conc=cc.to_dict(orient="records"), phi=pf.to_dict(orient="records"), drift=dr.to_dict(orient="records"), clipwindow=cl.to_dict(orient="records")),
              open(os.path.join(R, "glucose_summary_%s.json" % variant), "w"), indent=1, default=float)
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--npz"); ap.add_argument("--root"); ap.add_argument("--variants", default="asis,fwfix")
    args = ap.parse_args(); dumps, mt = load(args)
    for variant in args.variants.split(","):
        d = estimators(dumps, mt, variant, variant == "fwfix")
        run(variant, d)
