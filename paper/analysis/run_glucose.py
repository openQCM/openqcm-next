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
                                  k_dD=kD, b_dD=bD, r2_dD=r2D, k0_dD=kD0, resid5_df=yf[1] - (kf * x[1] + bf) if len(x) > 1 else np.nan,
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
    L.append("## φ = φ₀ − 360·f·τ per phase\n")
    L.append("| phase | fit | φ₀ [°] | τ [ns] | rms [°] | φ(n=1…9) [°] |\n|---|---|---|---|---|---|")
    for _, r in pf.iterrows():
        L.append("| %s | %s | %.1f | %.2f | %.1f | %s |" % (r.phase, r.fit, r.phi0_deg, r.tau_ns, r.rms_deg, " / ".join("%.1f" % r["phi_n%d" % n] for n in N.astype(int))))
    L.append("\n## Eq. 8 on the 75 sweeps: measured − predicted = %+.0f ± %.0f Hz, max |.| = %.0f Hz (%.3f Γ)\n" % (eq8["mean"], eq8["sd"], eq8["maxabs"], eq8["maxabs_over_gamma"]))
    L.append("## Gate and fold\n```\n%s\n```" % json.dumps(gate, indent=1))
    open(os.path.join(R, "glucose_tables_%s.md" % variant), "w").write("\n".join(L) + "\n")
    json.dump(dict(f0=f0, eq8=eq8, gate=gate, shifts=sh.to_dict(orient="records"), conc=cc.to_dict(orient="records"), phi=pf.to_dict(orient="records")),
              open(os.path.join(R, "glucose_summary_%s.json" % variant), "w"), indent=1, default=float)
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--npz"); ap.add_argument("--root"); ap.add_argument("--variants", default="asis,fwfix")
    args = ap.parse_args(); dumps, mt = load(args)
    for variant in args.variants.split(","):
        d = estimators(dumps, mt, variant, variant == "fwfix")
        run(variant, d)
