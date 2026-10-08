# -*- coding: utf-8 -*-
"""
run_v2.py — the numbers of manuscript v2 (revision of 2026-10-08), regenerated from the raw data.

Inputs (all produced from the raw sweeps by run_estimators.py and run_glucose.estimators()):
    results/sweeps_<variant>.csv          45 sweeps of 2026-09-11 (DS-2: air → water → isopropanol, board 1920)
    results/glucose_sweeps_<variant>.csv  75 sweeps of 2024-05-29 (DS-3: air → water → glucose 5/7.5/10 % w/v, 2nd instrument)
plus the datalogs of 2026-09-11 (DS-2) and 2026-09-10 (replicate, air → isopropanol → water), the five air sweeps of
2026-09-03 and the frozen water reference sweep of 2026-07-28 (for the rotation angle only).

Outputs: results/v2/<variant>/*.csv, results/v2/<variant>/tables.md, results/v2/<variant>/summary.json.

Definitions (identical in every experiment):
    shift          liquid plateau minus air plateau of the same dataset, same estimator, mean of three sweeps;
                   sd = quadrature sum of the two replica standard deviations
    KG             Δf_n = −√n f_F^{3/2} √(ρη/(π ρ_q μ_q)), ΔΓ_n = −Δf_n, f_F = the air fundamental of the dataset (PSL)
    eps_f, eps_G   Δf/Δf_KG − 1 and ΔΓ/ΔΓ_KG − 1 (relative deviation from KG; water and isopropanol only)
    KG-1 ratio     r_n = ΔΓ_n / (−Δf_n)   (1 for a Newtonian liquid; independent of ρη and of n)
    KG-2 slope     b in log10(−Δf_n/n) = a + b log10 n (and for ΔΓ_n/n); KG: b = −1/2
    KG-3           eps_f, eps_G for water / isopropanol; for the glucose solutions only relative quantities (no tabulated ρη)
    x_rel          √(ρη)/√(ρη)_water of a liquid estimated from the data: mean over n = 3–9 of
                   (−Δf_n + ΔΓ_n)/(−Δf_n,w + ΔΓ_n,w) (both channels); also the Δf-only and ΔΓ-only versions
"""
import os, sys, json, math
import numpy as np, pandas as pd
import qcmchain as q, data

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
N = np.array([1, 3, 5, 7, 9]); NS = np.sqrt(N.astype(float))
EST = ["mag_argmax", "argmax_hh", "midpoint", "sym", "sym_lin", "psl", "circle"]
MAIN = ["argmax_hh", "psl"]
LAB = {"mag_argmax": "M: magnitude maximum", "argmax_hh": "A: max G + half height", "midpoint": "MP: half-height midpoint",
       "sym": "S: symmetric Lorentzian", "sym_lin": "S+: symmetric + linear bg", "psl": "P: phase-shifted Lorentzian",
       "circle": "C: BVD circle"}
DS2_LIQ = ("water", "ipa"); DS3_LIQ = ("water", "gluc05", "gluc075", "gluc10")
CONC = {"water": 0.0, "gluc05": 5.0, "gluc075": 7.5, "gluc10": 10.0}
RHOETA = {k: v["rho"] * v["eta"] for k, v in q.LIQUIDS.items()}            # kg² m⁻⁴ s⁻¹ ... (ρ in kg/m³, η in Pa s)
KG_COEF = lambda f0: f0 ** 1.5 / math.sqrt(math.pi * q.RHO_Q * q.MU_Q)   # Δf_n = −√n · KG_COEF · √(ρη)


# --------------------------------------------------------------------------- helpers
def stats(sw):
    g = sw.groupby(["phase", "n", "estimator"]).agg(
        fres=("fres", "mean"), fres_sd=("fres", "std"), gamma=("gamma", "mean"), gamma_sd=("gamma", "std"),
        D_ppm=("D_ppm", "mean"), D_sd=("D_ppm", "std"), nrep=("fres", "count"),
        phi=("phi_deg", "mean"), phi_sd=("phi_deg", "std"), phi_min=("phi_deg", "min"), phi_max=("phi_deg", "max"),
        rms=("rms_rel", "mean"), rms_max=("rms_rel", "max"), fold=("fold", "mean")).reset_index()
    return g


def shifts(g, ds, liquids, f0, kg_liquids):
    rows = []
    for liq in liquids:
        kg = q.kanazawa_gordon(f0, N, **q.LIQUIDS[liq]) if liq in kg_liquids else np.full(len(N), np.nan)
        for est in EST:
            a = g[(g.phase == "air") & (g.estimator == est)].set_index("n")
            l = g[(g.phase == liq) & (g.estimator == est)].set_index("n")
            for i, n in enumerate(N):
                n = int(n)
                if n not in a.index or n not in l.index:
                    continue
                df = l.loc[n, "fres"] - a.loc[n, "fres"]; dG = l.loc[n, "gamma"] - a.loc[n, "gamma"]
                sdf = float(np.hypot(a.loc[n, "fres_sd"], l.loc[n, "fres_sd"])); sdG = float(np.hypot(a.loc[n, "gamma_sd"], l.loc[n, "gamma_sd"]))
                r = dG / (-df) if df else np.nan
                r_sd = abs(r) * math.sqrt((sdG / dG) ** 2 + (sdf / df) ** 2) if (dG and df and np.isfinite(dG) and np.isfinite(df)) else np.nan
                rows.append(dict(dataset=ds, liquid=liq, conc=CONC.get(liq, np.nan), n=n, estimator=est,
                                 f_air=a.loc[n, "fres"], f_air_sd=a.loc[n, "fres_sd"], f_liq=l.loc[n, "fres"], f_liq_sd=l.loc[n, "fres_sd"],
                                 G_air=a.loc[n, "gamma"], G_air_sd=a.loc[n, "gamma_sd"], G_liq=l.loc[n, "gamma"], G_liq_sd=l.loc[n, "gamma_sd"],
                                 df=df, df_sd=sdf, dG=dG, dG_sd=sdG, df_over_n=df / n, dG_over_n=dG / n,
                                 df_over_sqrtn=df / math.sqrt(n), dG_over_sqrtn=dG / math.sqrt(n),
                                 dD_ppm=l.loc[n, "D_ppm"] - a.loc[n, "D_ppm"],
                                 df_KG=kg[i], dG_KG=-kg[i], eps_f=df / kg[i] - 1.0, eps_G=dG / (-kg[i]) - 1.0,
                                 r_KG1=r, r_KG1_sd=r_sd, dD_KG_ppm=2e6 * (-kg[i]) / (n * f0),
                                 phi_air=a.loc[n, "phi"], phi_liq=l.loc[n, "phi"], phi_liq_sd=l.loc[n, "phi_sd"]))
    return pd.DataFrame(rows)


def loglog_slope(n, y):
    """OLS of log10(y) on log10(n); returns slope, intercept, rms of the residual in log10 units."""
    n = np.asarray(n, float); y = np.asarray(y, float)
    ok = np.isfinite(y) & (y > 0)
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    x = np.log10(n[ok]); z = np.log10(y[ok])
    A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, z, rcond=None)
    return float(sol[0]), float(sol[1]), float(np.sqrt(np.mean((A @ sol - z) ** 2)))


def kg2(sh, ds):
    rows = []
    for (liq, est), s in sh.groupby(["liquid", "estimator"]):
        s = s.sort_values("n")
        for label, sel in (("n=1-9", s.n >= 1), ("n=3-9", s.n >= 3)):
            bf, af, rf = loglog_slope(s.n[sel], -s.df_over_n[sel]); bG, aG, rG = loglog_slope(s.n[sel], s.dG_over_n[sel])
            # √n slope through the origin (Hz per √n) for comparison with k_KG
            x = np.sqrt(s.n[sel].values.astype(float))
            kf = float(np.sum(x * (-s.df[sel].values)) / np.sum(x * x)); kG = float(np.sum(x * s.dG[sel].values) / np.sum(x * x)) if np.isfinite(s.dG[sel]).all() else np.nan
            # coefficient of variation of the √n-normalised shifts
            yf = -s.df[sel].values / x; yG = s.dG[sel].values / x
            rows.append(dict(dataset=ds, liquid=liq, estimator=est, fit=label, b_df=bf, b_dG=bG, rms_df=rf, rms_dG=rG,
                             k_df=kf, k_dG=kG, k_KG=float(-s.df_KG.iloc[0]) if np.isfinite(s.df_KG.iloc[0]) else np.nan,
                             cv_df_sqrtn=float(np.std(yf, ddof=1) / np.mean(yf)) if len(yf) > 1 else np.nan,
                             cv_dG_sqrtn=float(np.std(yG, ddof=1) / np.mean(yG)) if len(yG) > 1 and np.isfinite(yG).all() else np.nan))
    return pd.DataFrame(rows)


def datalog_plateaus(path, plateau_min, levels):
    """Phases by the level of the fundamental (levels: list of (name, lo, hi)); plateau = last `plateau_min` minutes of
    each phase; exact duplicate rows dropped. Returns per phase and overtone f (max of G), Γ = D·1e-6·f/2, D, and the
    phase windows. Datalog of the impedance chain (argmax + half height)."""
    d = pd.read_csv(path); d["t"] = pd.to_datetime(d.Date + " " + d.Time)
    cols = [c for c in d.columns if c.startswith(("Frequency", "Dissipation"))]
    dup = (d[cols].shift(1) == d[cols]).all(axis=1); nd = int(dup.sum()); d = d[~dup].reset_index(drop=True)
    out = {}
    for name, lo, hi in levels:
        sel = (d.Frequency_0 >= lo) & (d.Frequency_0 < hi)
        if not sel.any():
            continue
        t1 = d.t[sel].max(); win = sel & (d.t > t1 - pd.Timedelta(minutes=plateau_min))
        rec = dict(window=[str(d.t[win].min().time()), str(d.t[win].max().time())], rows=int(win.sum()),
                   T=[float(d.Temperature[win].min()), float(d.Temperature[win].max())])
        for k in range(5):
            f = d["Frequency_%d" % k][win].astype(float); D = d["Dissipation_%d" % k][win].astype(float)
            G = D * 1e-6 * f / 2
            rec[2 * k + 1] = dict(f=float(f.mean()), f_sd=float(f.std(ddof=1)), G=float(G.mean()), G_sd=float(G.std(ddof=1)), D=float(D.mean()))
        out[name] = rec
    return out, nd, len(d) + nd, d


def datalog_shifts(pl, ds, liquids, f0):
    rows = []
    for liq in liquids:
        kg = q.kanazawa_gordon(f0, N, **q.LIQUIDS[liq])
        for i, n in enumerate(N):
            n = int(n); a = pl["air"][n]; l = pl[liq][n]
            df = l["f"] - a["f"]; dG = l["G"] - a["G"]
            rows.append(dict(dataset=ds, liquid=liq, n=n, estimator="argmax_hh (live datalog)", df=df, df_sd=float(np.hypot(a["f_sd"], l["f_sd"])),
                             dG=dG, dG_sd=float(np.hypot(a["G_sd"], l["G_sd"])), df_over_n=df / n, dG_over_n=dG / n, df_KG=kg[i], dG_KG=-kg[i],
                             eps_f=df / kg[i] - 1, eps_G=dG / (-kg[i]) - 1, r_KG1=dG / (-df)))
    return pd.DataFrame(rows)


def fmt(x, nd=1, sign=False):
    if x is None or not np.isfinite(x):
        return "—"
    return ("%+." + str(nd) + "f") % x if sign else ("%." + str(nd) + "f") % x


# --------------------------------------------------------------------------- main
def run(variant):
    OUT = os.path.join(R, "v2", variant); os.makedirs(OUT, exist_ok=True)
    fix = variant == "fwfix"
    sw2 = pd.read_csv(os.path.join(R, "sweeps_%s.csv" % variant))
    sw3 = pd.read_csv(os.path.join(R, "glucose_sweeps_%s.csv" % variant))
    g2 = stats(sw2); g3 = stats(sw3)
    g2["dataset"] = "DS-2"; g3["dataset"] = "DS-3"
    f02 = float(g2[(g2.phase == "air") & (g2.n == 1) & (g2.estimator == "psl")].fres.iloc[0])
    f03 = float(g3[(g3.phase == "air") & (g3.n == 1) & (g3.estimator == "psl")].fres.iloc[0])
    sh2 = shifts(g2, "DS-2", DS2_LIQ, f02, ("water", "ipa")); sh3 = shifts(g3, "DS-3", DS3_LIQ, f03, ("water",))
    sh = pd.concat([sh2, sh3], ignore_index=True)
    k2 = pd.concat([kg2(sh2, "DS-2"), kg2(sh3, "DS-3")], ignore_index=True)
    pd.concat([g2, g3]).to_csv(os.path.join(OUT, "phases.csv"), index=False)
    sh.to_csv(os.path.join(OUT, "shifts.csv"), index=False); k2.to_csv(os.path.join(OUT, "kg2_slopes.csv"), index=False)

    # ---- the live datalogs of board 1920 (A estimator as published by the instrument): DS-2 and the 2026-09-10 replicate
    pl11, nd11, nrows11, dl11 = datalog_plateaus(os.path.join(data.D0911, "data", "2026-09-11_12-14-42_multi.csv"), 10.0,
                                                  [("air", 5004000, 5.1e6), ("water", 5003700, 5004000), ("ipa", 0, 5003700)])
    pl10, nd10, nrows10, dl10 = datalog_plateaus(os.path.join(data.D0910, "data", "2026-09-10_17-10-06_multi.csv"), 2.5,
                                                  [("air", 5004200, 5.1e6), ("water", 5003800, 5004200), ("ipa", 0, 5003800)])
    dsh = pd.concat([datalog_shifts(pl11, "DS-2 datalog 2026-09-11", DS2_LIQ, pl11["air"][1]["f"]),
                     datalog_shifts(pl10, "datalog 2026-09-10 (air → ipa → water)", DS2_LIQ, pl10["air"][1]["f"])], ignore_index=True)
    dsh.to_csv(os.path.join(OUT, "datalog_shifts.csv"), index=False)

    # ---- the bias of the conductance maximum and of the half-height width, per sweep (both datasets)
    p = pd.concat([sw2.assign(dataset="DS-2"), sw3.assign(dataset="DS-3")], ignore_index=True)
    p = p[p.estimator == "psl"].copy()
    p["resid"] = p.bias_meas - p.bias_pred; p["resid_over_gamma"] = p.resid / p.gamma
    bias = p.groupby(["dataset", "phase", "n"]).agg(gamma=("gamma", "mean"), phi=("phi_deg", "mean"), bias_meas=("bias_meas", "mean"), bias_meas_sd=("bias_meas", "std"),
                                                    bias_pred=("bias_pred", "mean"), resid=("resid", "mean"), resid_over_gamma=("resid_over_gamma", "mean"),
                                                    hh_meas=("hh_factor_meas", "mean"), hh_pred=("hh_factor_pred", "mean")).reset_index()
    bias.to_csv(os.path.join(OUT, "bias_per_overtone.csv"), index=False)
    bias_all = dict(n=int(len(p)), mean=float(p.resid.mean()), sd=float(p.resid.std()), maxabs=float(p.resid.abs().max()),
                    mean_over_gamma=float(p.resid_over_gamma.mean()), maxabs_over_gamma=float(p.resid_over_gamma.abs().max()),
                    by_dataset={ds: dict(n=int(len(s)), mean=float(s.resid.mean()), sd=float(s.resid.std()), maxabs=float(s.resid.abs().max())) for ds, s in p.groupby("dataset")})

    # ---- the rotation angle: every medium, every dataset, plus the 2026-09-03 air set and the 2026-07-28 reference sweep
    phi_rows = []
    for ds, s in p.groupby("dataset"):
        for (ph, n), ss in s.groupby(["phase", "n"]):
            phi_rows.append(dict(dataset=ds, medium=ph, n=int(n), f_MHz=float(ss.fres.mean() / 1e6), phi=float(ss.phi_deg.mean()), phi_sd=float(ss.phi_deg.std()),
                                 phi_min=float(ss.phi_deg.min()), phi_max=float(ss.phi_deg.max()), nrep=int(len(ss)), fold=float(ss.fold.mean())))
    for n, (f, vm, vp) in data.air_0903().items():
        c = q.chain(f, vm, vp, firmware_fix=fix); e = q.argmax_halfheight(c["f"], c["G"]); ps = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"])
        phi_rows.append(dict(dataset="air 2026-09-03 (board 1920 class)", medium="air", n=int(n), f_MHz=ps["fres"] / 1e6, phi=ps["phi_deg"], phi_sd=np.nan, phi_min=ps["phi_deg"], phi_max=ps["phi_deg"], nrep=1, fold=float(c["fold"])))
    f, vm, vp = data.reference_g1(); c = q.chain(f, vm, vp, firmware_fix=fix); e = q.argmax_halfheight(c["f"], c["G"]); ps = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"])
    phi_rows.append(dict(dataset="water 2026-07-28 (board not recorded)", medium="water", n=1, f_MHz=ps["fres"] / 1e6, phi=ps["phi_deg"], phi_sd=np.nan, phi_min=ps["phi_deg"], phi_max=ps["phi_deg"], nrep=1, fold=float(c["fold"])))
    phi = pd.DataFrame(phi_rows); phi.to_csv(os.path.join(OUT, "phi_all.csv"), index=False)
    # stability statistics per dataset and overtone: spread across media, air–liquid difference, replica sd
    phi_stat = []
    for ds in ("DS-2", "DS-3"):
        for n in N:
            s = phi[(phi.dataset == ds) & (phi.n == n)]
            air = float(s[s.medium == "air"].phi.iloc[0]); liq = s[s.medium != "air"]
            phi_stat.append(dict(dataset=ds, n=int(n), phi_air=air, phi_liquid_min=float(liq.phi.min()), phi_liquid_max=float(liq.phi.max()),
                                 liquid_range=float(liq.phi.max() - liq.phi.min()), air_minus_liquid_mean=air - float(liq.phi.mean()),
                                 all_media_range=float(s.phi.max() - s.phi.min()), replica_sd_max=float(s.phi_sd.max())))
    phi_stat = pd.DataFrame(phi_stat); phi_stat.to_csv(os.path.join(OUT, "phi_stability.csv"), index=False)
    # between boards (air): DS-2 vs DS-3; between days on board 1920 (air): 09-11 vs 09-03
    a2 = phi[(phi.dataset == "DS-2") & (phi.medium == "air")].set_index("n").phi; a3 = phi[(phi.dataset == "DS-3") & (phi.medium == "air")].set_index("n").phi
    a03 = phi[(phi.dataset.str.startswith("air 2026-09-03"))].set_index("n").phi
    phi_between = pd.DataFrame(dict(n=N, phi_air_DS2=[a2[n] for n in N], phi_air_DS3=[a3[n] for n in N], phi_air_0903=[a03[n] for n in N],
                                    DS3_minus_DS2=[a3[n] - a2[n] for n in N], d0903_minus_DS2=[a03[n] - a2[n] for n in N]))
    phi_between.to_csv(os.path.join(OUT, "phi_between.csv"), index=False)
    # monotonicity in frequency: sign of successive differences, per dataset and medium
    mono = []
    for (ds, med), s in phi.groupby(["dataset", "medium"]):
        s = s.sort_values("n")
        if len(s) < 5:
            continue
        d = np.diff(s.phi.values)
        mono.append(dict(dataset=ds, medium=med, phi_1_to_9=" / ".join("%.1f" % v for v in s.phi.values), monotonic=bool((d < 0).all() or (d > 0).all()),
                         max_nonmonotonic_step=float(np.max(d)) if (d > 0).any() else 0.0))
    mono = pd.DataFrame(mono); mono.to_csv(os.path.join(OUT, "phi_monotonicity.csv"), index=False)

    # ---- glucose: x_rel = √(ρη)/√(ρη)_water from the data, steps, resolution
    gl_rows = []
    for est in MAIN:
        w = sh3[(sh3.liquid == "water") & (sh3.estimator == est)].set_index("n")
        for liq in DS3_LIQ:
            l = sh3[(sh3.liquid == liq) & (sh3.estimator == est)].set_index("n")
            xf = {int(n): float(l.loc[n, "df"] / w.loc[n, "df"]) for n in N}
            xG = {int(n): float(l.loc[n, "dG"] / w.loc[n, "dG"]) for n in N}
            xb = {int(n): float((-l.loc[n, "df"] + l.loc[n, "dG"]) / (-w.loc[n, "df"] + w.loc[n, "dG"])) for n in N}
            sel = [3, 5, 7, 9]
            gl_rows.append(dict(estimator=est, liquid=liq, conc=CONC[liq],
                                x_df_n3_9=float(np.mean([xf[n] for n in sel])), x_df_sd_n=float(np.std([xf[n] for n in sel], ddof=1)),
                                x_dG_n3_9=float(np.mean([xG[n] for n in sel])), x_dG_sd_n=float(np.std([xG[n] for n in sel], ddof=1)),
                                x_both_n3_9=float(np.mean([xb[n] for n in sel])), x_both_sd_n=float(np.std([xb[n] for n in sel], ddof=1)),
                                **{"x_df_n%d" % n: xf[n] for n in N}, **{"x_dG_n%d" % n: xG[n] for n in N}, **{"x_both_n%d" % n: xb[n] for n in N}))
    gl = pd.DataFrame(gl_rows); gl.to_csv(os.path.join(OUT, "glucose_xrel.csv"), index=False)
    # steps and resolution in x_rel: sensitivity d(−Δf_n)/dx = −Δf_n,water (KG, exact for the water point); noise = replica sd in the liquid plateaus
    res_rows = []
    for est in MAIN:
        gi = g3[(g3.estimator == est)].set_index(["phase", "n"])
        w = sh3[(sh3.liquid == "water") & (sh3.estimator == est)].set_index("n")
        xs = gl[gl.estimator == est].set_index("liquid")
        for n in N:
            n = int(n)
            sd_f = float(np.median([gi.loc[(ph, n), "fres_sd"] for ph in DS3_LIQ])); sd_G = float(np.median([gi.loc[(ph, n), "gamma_sd"] for ph in DS3_LIQ]))
            slope_f = float(-w.loc[n, "df"]); slope_G = float(w.loc[n, "dG"])            # Hz per unit of x_rel
            row = dict(estimator=est, n=n, sd_f_liquid=sd_f, sd_G_liquid=sd_G, slope_f_Hz_per_x=slope_f, slope_G_Hz_per_x=slope_G,
                       res_x_f=sd_f / slope_f, res_x_G=sd_G / slope_G, res3_x_f=3 * sd_f / slope_f, res3_x_G=3 * sd_G / slope_G)
            for a, b in (("water", "gluc05"), ("gluc05", "gluc075"), ("gluc075", "gluc10")):
                dfs = gi.loc[(b, n), "fres"] - gi.loc[(a, n), "fres"]; dGs = gi.loc[(b, n), "gamma"] - gi.loc[(a, n), "gamma"]
                row["step_%s_%s_df" % (a, b)] = dfs; row["step_%s_%s_dG" % (a, b)] = dGs
                row["step_%s_%s_dx_f" % (a, b)] = -dfs / slope_f; row["step_%s_%s_dx_G" % (a, b)] = dGs / slope_G
                row["step_%s_%s_sigma_f" % (a, b)] = abs(dfs) / float(np.hypot(gi.loc[(a, n), "fres_sd"], gi.loc[(b, n), "fres_sd"]))
                row["step_%s_%s_sigma_G" % (a, b)] = abs(dGs) / float(np.hypot(gi.loc[(a, n), "gamma_sd"], gi.loc[(b, n), "gamma_sd"]))
            res_rows.append(row)
    res = pd.DataFrame(res_rows); res.to_csv(os.path.join(OUT, "glucose_resolution.csv"), index=False)
    # concentration slopes of x_rel (per % w/v), OLS with intercept on 0, 5, 7.5, 10, PSL and A
    conc_rows = []
    for est in MAIN:
        xs = gl[gl.estimator == est].sort_values("conc")
        for col in ("x_df_n3_9", "x_dG_n3_9", "x_both_n3_9"):
            A = np.column_stack([xs.conc.values, np.ones(len(xs))]); sol, *_ = np.linalg.lstsq(A, xs[col].values, rcond=None)
            resid = xs[col].values - A @ sol
            conc_rows.append(dict(estimator=est, quantity=col, slope_per_pct=float(sol[0]), intercept=float(sol[1]), resid5=float(resid[1]), rms=float(np.sqrt(np.mean(resid ** 2)))))
    conc = pd.DataFrame(conc_rows); conc.to_csv(os.path.join(OUT, "glucose_xrel_vs_conc.csv"), index=False)

    # ---- gate / fold / repeatability statistics
    gate = {}
    for ds, s in (("DS-2", sw2), ("DS-3", sw3)):
        pp = s[s.estimator == "psl"]; sy = s[s.estimator == "sym_lin"]
        gate[ds] = dict(sweeps=int(len(pp)), psl_converged=int(pp.converged.sum()), psl_gate_ok=int(pp.gate_ok.sum()),
                        psl_rms_air=[float(pp[pp.phase == "air"].rms_rel.min()), float(pp[pp.phase == "air"].rms_rel.max())],
                        psl_rms_liquid=[float(pp[pp.phase != "air"].rms_rel.min()), float(pp[pp.phase != "air"].rms_rel.max())],
                        sym_lin_rms_air=[float(sy[sy.phase == "air"].rms_rel.min()), float(sy[sy.phase == "air"].rms_rel.max())],
                        sym_lin_rms_liquid=[float(sy[sy.phase != "air"].rms_rel.min()), float(sy[sy.phase != "air"].rms_rel.max())],
                        fold_by_phase={ph: int(round(3 * v)) for ph, v in pp.groupby("phase").fold.mean().items()},
                        one_sided_hh=int(s[s.estimator == "argmax_hh"].one_sided.sum()), mag_w3_missing=int(s[s.estimator == "mag_argmax"].gamma.isna().sum()),
                        repeat_f_air_max=float(pp[pp.phase == "air"].groupby("n").fres.std().max()), repeat_f_liq_max=float(pp[pp.phase != "air"].groupby(["phase", "n"]).fres.std().max()),
                        repeat_G_air_max=float(pp[pp.phase == "air"].groupby("n").gamma.std().max()), repeat_G_liq_max=float(pp[pp.phase != "air"].groupby(["phase", "n"]).gamma.std().max()))

    # ---- summaries used in the text
    def rng(s, col):
        s = s[col].dropna(); return [float(s.min()), float(s.max())] if len(s) else [np.nan, np.nan]
    summ = {}
    for ds, s_ in (("DS-2", sh2), ("DS-3", sh3)):
        summ[ds] = {}
        for est in EST:
            s = s_[(s_.estimator == est) & (s_.n >= 3)]
            summ[ds][est] = dict(eps_f=rng(s[s.liquid.isin(("water", "ipa"))], "eps_f"), eps_G=rng(s[s.liquid.isin(("water", "ipa"))], "eps_G"),
                                 r_KG1_all_liquids=rng(s, "r_KG1"), r_KG1_water=rng(s[s.liquid == "water"], "r_KG1"),
                                 max_abs_eps_f=float(s[s.liquid.isin(("water", "ipa"))].eps_f.abs().max()) if len(s) else np.nan)
    # the "8 %" claim: per overtone and dataset, PSL |eps_f| and |eps_G| ≤ 8 %? and A values
    claim = []
    for ds, s_ in (("DS-2", sh2), ("DS-3", sh3)):
        for liq in (l for l in ("water", "ipa") if l in set(s_.liquid)):
            for n in N:
                pp = s_[(s_.liquid == liq) & (s_.estimator == "psl") & (s_.n == n)].iloc[0]; aa = s_[(s_.liquid == liq) & (s_.estimator == "argmax_hh") & (s_.n == n)].iloc[0]
                claim.append(dict(dataset=ds, liquid=liq, n=int(n), eps_f_P=pp.eps_f, eps_G_P=pp.eps_G, eps_f_A=aa.eps_f, eps_G_A=aa.eps_G,
                                  P_f_within_8=bool(abs(pp.eps_f) <= 0.08), P_G_within_8=bool(abs(pp.eps_G) <= 0.08), A_f_within_8=bool(abs(aa.eps_f) <= 0.08), A_G_within_8=bool(abs(aa.eps_G) <= 0.08)))
    claim = pd.DataFrame(claim); claim.to_csv(os.path.join(OUT, "claim_8pct.csv"), index=False)

    # ---- the reproducibility of the air → water step (Exp. 1): DS-2 vs DS-3 (sweeps), and the 2026-09-10 datalog (A only)
    rep = []
    for n in N:
        row = dict(n=int(n))
        for ds, s_ in (("DS2", sh2), ("DS3", sh3)):
            for est, tag in (("argmax_hh", "A"), ("psl", "P")):
                r = s_[(s_.liquid == "water") & (s_.estimator == est) & (s_.n == n)].iloc[0]
                row.update({"%s_%s_df_over_n" % (ds, tag): r.df_over_n, "%s_%s_dG_over_n" % (ds, tag): r.dG_over_n, "%s_%s_eps_f" % (ds, tag): r.eps_f,
                            "%s_%s_eps_G" % (ds, tag): r.eps_G, "%s_%s_r" % (ds, tag): r.r_KG1, "%s_%s_phi_liq" % (ds, tag): r.phi_liq if tag == "P" else np.nan,
                            "%s_%s_phi_air" % (ds, tag): r.phi_air if tag == "P" else np.nan})
        d10 = dsh[(dsh.dataset.str.startswith("datalog 2026-09-10")) & (dsh.liquid == "water") & (dsh.n == n)].iloc[0]
        d11 = dsh[(dsh.dataset.str.startswith("DS-2 datalog")) & (dsh.liquid == "water") & (dsh.n == n)].iloc[0]
        row.update(dl0910_A_eps_f=d10.eps_f, dl0910_A_eps_G=d10.eps_G, dl0910_A_r=d10.r_KG1, dl0911_A_eps_f=d11.eps_f, dl0911_A_eps_G=d11.eps_G, dl0911_A_r=d11.r_KG1)
        rep.append(row)
    rep = pd.DataFrame(rep); rep.to_csv(os.path.join(OUT, "exp1_reproducibility.csv"), index=False)

    # ---- T4 time traces: DS-2 datalog relative to its air plateau (A live) with PSL offline points; DS-3 sweep instants
    t4 = []
    air11 = pl11["air"]
    for _, r in dl11.iterrows():
        for k in range(5):
            n = 2 * k + 1; f = float(r["Frequency_%d" % k]); D = float(r["Dissipation_%d" % k]); G = D * 1e-6 * f / 2
            t4.append(dict(dataset="DS-2", source="datalog A (live)", t=str(r.t), n=n, df_over_n=(f - air11[n]["f"]) / n, dG_over_n=(G - air11[n]["G"]) / n, D_ppm=D))
    t4 = pd.DataFrame(t4); t4.to_csv(os.path.join(OUT, "t4_ds2_datalog.csv"), index=False)
    pts = []
    for ds, s_, g_ in (("DS-2", sw2, g2), ("DS-3", sw3, g3)):
        for est in MAIN:
            a = g_[(g_.estimator == est) & (g_.phase == "air")].set_index("n")
            for _, r in s_[s_.estimator == est].iterrows():
                pts.append(dict(dataset=ds, estimator=est, phase=r.phase, n=int(r.n), replica=int(r.replica), mtime=r.mtime,
                                df_over_n=(r.fres - a.loc[r.n, "fres"]) / r.n, dG_over_n=(r.gamma - a.loc[r.n, "gamma"]) / r.n, D_ppm=r.D_ppm))
    pts = pd.DataFrame(pts); pts.to_csv(os.path.join(OUT, "t4_sweep_points.csv"), index=False)

    # ---------------------------------------------------------------- markdown tables
    L = ["# Manuscript v2 numbers — variant `%s`\n" % variant,
         "f_F(DS-2, air, PSL) = %.0f Hz; f_F(DS-3, air, PSL) = %.0f Hz. KG with ρ_q = %.0f kg/m³, μ_q = %.3e Pa; water ρ = %.2f kg/m³, η = %.3f mPa·s; isopropanol ρ = %.1f kg/m³, η = %.3f mPa·s (25 °C). KG coefficient (Hz per √n per unit √(ρη)): %.4f (DS-2), %.4f (DS-3). √(ρη): water %.4f, isopropanol %.4f (kg m⁻² s⁻¹ᐟ²)\n"
         % (f02, f03, q.RHO_Q, q.MU_Q, q.LIQUIDS["water"]["rho"], 1e3 * q.LIQUIDS["water"]["eta"], q.LIQUIDS["ipa"]["rho"], 1e3 * q.LIQUIDS["ipa"]["eta"], KG_COEF(f02), KG_COEF(f03), math.sqrt(RHOETA["water"]), math.sqrt(RHOETA["ipa"]))]
    L.append("## Per phase and overtone, A and P (mean ± sd of three sweeps)\n")
    L.append("| dataset | phase | n | f (A) [Hz] | f (P) [Hz] | Γ (A) [Hz] | Γ (P) [Hz] | D (A) [ppm] | D (P) [ppm] | φ [°] ± sd | fold |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for ds, g_ in (("DS-2", g2), ("DS-3", g3)):
        for ph in (("air",) + (DS2_LIQ if ds == "DS-2" else DS3_LIQ)):
            for n in N:
                a = g_[(g_.phase == ph) & (g_.n == n) & (g_.estimator == "argmax_hh")].iloc[0]; pp = g_[(g_.phase == ph) & (g_.n == n) & (g_.estimator == "psl")].iloc[0]
                L.append("| %s | %s | %d | %.0f ± %.0f | %.0f ± %.0f | %.1f ± %.1f | %.1f ± %.1f | %.1f | %.1f | %.1f ± %.2f | %.0f/3 |" % (
                    ds, ph, n, a.fres, a.fres_sd, pp.fres, pp.fres_sd, a.gamma, a.gamma_sd, pp.gamma, pp.gamma_sd, a.D_ppm, pp.D_ppm, pp.phi, pp.phi_sd, 3 * pp.fold))
    L.append("\n## Shifts from air, all estimators (eps against KG where ρη is tabulated; r = ΔΓ/(−Δf))\n")
    L.append("| dataset | liquid | n | estimator | Δf [Hz] ± sd | Δf/n | ΔΓ [Hz] ± sd | ΔΓ/n | Δf_KG | eps_f [%] | eps_Γ [%] | r = ΔΓ/(−Δf) ± sd | ΔD [ppm] |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in sh.iterrows():
        L.append("| %s | %s | %d | %s | %.0f ± %.0f | %.0f | %s | %s | %s | %s | %s | %s ± %s | %s |" % (
            r.dataset, r.liquid, r.n, r.estimator, r.df, r.df_sd, r.df_over_n, "%.0f ± %.0f" % (r.dG, r.dG_sd) if np.isfinite(r.dG) else "—",
            fmt(r.dG_over_n, 0), fmt(r.df_KG, 0), fmt(100 * r.eps_f, 1, True), fmt(100 * r.eps_G, 1, True), fmt(r.r_KG1, 3), fmt(r.r_KG1_sd, 3), fmt(r.dD_ppm, 1)))
    L.append("\n## KG-2: log–log slopes b of −Δf_n/n and ΔΓ_n/n against n (KG: −0.5), √n slopes through the origin [Hz/√n] and CV of the √n-normalised shifts\n")
    L.append("| dataset | liquid | estimator | fit | b(Δf) | b(ΔΓ) | rms(Δf) [dex] | k(−Δf) | k(ΔΓ) | k_KG | CV(−Δf/√n) [%] | CV(ΔΓ/√n) [%] |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in k2.iterrows():
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (r.dataset, r.liquid, r.estimator, r.fit, fmt(r.b_df, 3), fmt(r.b_dG, 3), fmt(r.rms_df, 3), fmt(r.k_df, 0), fmt(r.k_dG, 0), fmt(r.k_KG, 0), fmt(100 * r.cv_df_sqrtn, 1), fmt(100 * r.cv_dG_sqrtn, 1)))
    L.append("\n## Summary on overtones 3–9 (range over n, and over water + isopropanol for eps)\n")
    L.append("| dataset | estimator | eps_f [%] | eps_Γ [%] | r = ΔΓ/(−Δf) water | r all liquids | max abs eps_f [%] |\n|---|---|---|---|---|---|---|")
    for ds in ("DS-2", "DS-3"):
        for est in EST:
            s = summ[ds][est]
            L.append("| %s | %s | %s … %s | %s … %s | %s … %s | %s … %s | %s |" % (ds, est, fmt(100 * s["eps_f"][0], 1, True), fmt(100 * s["eps_f"][1], 1, True), fmt(100 * s["eps_G"][0], 1, True), fmt(100 * s["eps_G"][1], 1, True),
                                                                            fmt(s["r_KG1_water"][0], 2), fmt(s["r_KG1_water"][1], 2), fmt(s["r_KG1_all_liquids"][0], 2), fmt(s["r_KG1_all_liquids"][1], 2), fmt(100 * s["max_abs_eps_f"], 1)))
    L.append("\n## The '8 %' claim, per overtone: P and A against KG (water; DS-2 also isopropanol)\n")
    L.append("| dataset | liquid | n | eps_f P [%] | eps_Γ P [%] | eps_f A [%] | eps_Γ A [%] | P within 8 % (f, Γ) | A within 8 % (f, Γ) |\n|---|---|---|---|---|---|---|---|---|")
    for _, r in claim.iterrows():
        L.append("| %s | %s | %d | %+.1f | %+.1f | %+.1f | %+.1f | %s, %s | %s, %s |" % (r.dataset, r.liquid, r.n, 100 * r.eps_f_P, 100 * r.eps_G_P, 100 * r.eps_f_A, 100 * r.eps_G_A, r.P_f_within_8, r.P_G_within_8, r.A_f_within_8, r.A_G_within_8))
    L.append("\n## Exp. 1 reproducibility of the air → water step: DS-2 (board 1920, 2026-09-11) against DS-3 (2nd instrument, 2024-05-29); live datalogs of board 1920 (A)\n")
    L.append("| n | Δf/n DS2 A | DS3 A | Δf/n DS2 P | DS3 P | ΔΓ/n DS2 A | DS3 A | ΔΓ/n DS2 P | DS3 P | eps_f DS2 P | DS3 P | eps_Γ DS2 P | DS3 P | r DS2 A | DS3 A | r DS2 P | DS3 P | φ_water DS2 | DS3 | φ_air DS2 | DS3 | eps_f A datalog 09-11 | 09-10 |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in rep.iterrows():
        L.append("| %d | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %+.1f | %+.1f | %+.1f | %+.1f | %.2f | %.2f | %.2f | %.2f | %.1f | %.1f | %.1f | %.1f | %+.1f | %+.1f |" % (
            r.n, r.DS2_A_df_over_n, r.DS3_A_df_over_n, r.DS2_P_df_over_n, r.DS3_P_df_over_n, r.DS2_A_dG_over_n, r.DS3_A_dG_over_n, r.DS2_P_dG_over_n, r.DS3_P_dG_over_n,
            100 * r.DS2_P_eps_f, 100 * r.DS3_P_eps_f, 100 * r.DS2_P_eps_G, 100 * r.DS3_P_eps_G, r.DS2_A_r, r.DS3_A_r, r.DS2_P_r, r.DS3_P_r, r.DS2_P_phi_liq, r.DS3_P_phi_liq, r.DS2_P_phi_air, r.DS3_P_phi_air,
            100 * r.dl0911_A_eps_f, 100 * r.dl0910_A_eps_f))
    L.append("\n## Bias of the conductance maximum and of the half-height width, per dataset, medium and overtone (mean of 3)\n")
    L.append("| dataset | medium | n | Γ_P [Hz] | φ [°] | f_Gmax − f_res meas [Hz] ± sd | Γ tan(φ/2) [Hz] | meas − pred [Hz] | (meas − pred)/Γ | Γ_hh/Γ_P meas | √(1+2tan²(φ/2)) |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in bias.iterrows():
        L.append("| %s | %s | %d | %.0f | %.1f | %+.0f ± %.0f | %+.0f | %+.0f | %+.3f | %.3f | %.3f |" % (r.dataset, r.phase, r.n, r.gamma, r.phi, r.bias_meas, r.bias_meas_sd, r.bias_pred, r.resid, r.resid_over_gamma, r.hh_meas, r.hh_pred))
    L.append("\nAll %d sweeps: measured − predicted = %+.0f ± %.0f Hz (sd), max |.| = %.0f Hz; in units of Γ mean %+.3f, max |.| %.3f. By dataset: %s\n" % (
        bias_all["n"], bias_all["mean"], bias_all["sd"], bias_all["maxabs"], bias_all["mean_over_gamma"], bias_all["maxabs_over_gamma"],
        "; ".join("%s: %+.0f ± %.0f Hz, max %.0f (%d sweeps)" % (k, v["mean"], v["sd"], v["maxabs"], v["n"]) for k, v in bias_all["by_dataset"].items())))
    L.append("## The rotation angle φ: every dataset and medium\n")
    L.append("| dataset | medium | n | f [MHz] | φ [°] | sd | min | max | sweeps | fold |\n|---|---|---|---|---|---|---|---|---|---|")
    for _, r in phi.iterrows():
        L.append("| %s | %s | %d | %.3f | %.1f | %s | %.1f | %.1f | %d | %.2f |" % (r.dataset, r.medium, r.n, r.f_MHz, r.phi, fmt(r.phi_sd, 2), r.phi_min, r.phi_max, r.nrep, r.fold))
    L.append("\n### Stability of φ per dataset and overtone\n")
    L.append("| dataset | n | φ air | φ liquids min … max | range over liquids | air − mean(liquids) | range over all media | max replica sd |\n|---|---|---|---|---|---|---|---|")
    for _, r in phi_stat.iterrows():
        L.append("| %s | %d | %.1f | %.1f … %.1f | %.1f | %+.1f | %.1f | %.2f |" % (r.dataset, r.n, r.phi_air, r.phi_liquid_min, r.phi_liquid_max, r.liquid_range, r.air_minus_liquid_mean, r.all_media_range, r.replica_sd_max))
    L.append("\n### Between boards and days (air)\n")
    L.append("| n | φ DS-2 (1920, 09-11) | φ 09-03 (125 MHz board) | φ DS-3 (2024) | 09-03 − DS-2 | DS-3 − DS-2 |\n|---|---|---|---|---|---|")
    for _, r in phi_between.iterrows():
        L.append("| %d | %.1f | %.1f | %.1f | %+.1f | %+.1f |" % (r.n, r.phi_air_DS2, r.phi_air_0903, r.phi_air_DS3, r.d0903_minus_DS2, r.DS3_minus_DS2))
    L.append("\n### Monotonicity of φ in the overtone order\n")
    L.append("| dataset | medium | φ(n = 1 … 9) | monotonic | largest step in the wrong direction [°] |\n|---|---|---|---|---|")
    for _, r in mono.iterrows():
        L.append("| %s | %s | %s | %s | %.1f |" % (r.dataset, r.medium, r.phi_1_to_9, r.monotonic, r.max_nonmonotonic_step))
    L.append("\n## Glucose: √(ρη)/√(ρη)_water from the data (x_rel), per overtone and averaged on n = 3–9\n")
    L.append("| estimator | liquid | % w/v | x from Δf (n=1,3,5,7,9) | mean n=3–9 ± sd_n | x from ΔΓ (n=1…9) | mean ± sd_n | x from both channels (n=1…9) | mean ± sd_n |\n|---|---|---|---|---|---|---|---|---|")
    for _, r in gl.iterrows():
        L.append("| %s | %s | %.1f | %s | %.3f ± %.3f | %s | %.3f ± %.3f | %s | %.3f ± %.3f |" % (
            r.estimator, r.liquid, r.conc, " / ".join("%.3f" % r["x_df_n%d" % n] for n in N), r.x_df_n3_9, r.x_df_sd_n,
            " / ".join("%.3f" % r["x_dG_n%d" % n] for n in N), r.x_dG_n3_9, r.x_dG_sd_n, " / ".join("%.3f" % r["x_both_n%d" % n] for n in N), r.x_both_n3_9, r.x_both_sd_n))
    L.append("\n### x_rel against concentration (OLS with intercept on 0, 5, 7.5, 10 % w/v)\n")
    L.append("| estimator | quantity | slope [per % w/v] | intercept | residual of the 5 % point | rms |\n|---|---|---|---|---|---|")
    for _, r in conc.iterrows():
        L.append("| %s | %s | %.5f | %.4f | %+.4f | %.4f |" % (r.estimator, r.quantity, r.slope_per_pct, r.intercept, r.resid5, r.rms))
    L.append("\n### Steps between consecutive concentrations in x_rel and in units of the replica scatter; resolution in x_rel (noise / slope)\n")
    L.append("| estimator | n | sd_f liquid [Hz] | sd_Γ [Hz] | slope f [Hz/x] | slope Γ [Hz/x] | σ_x from f | from Γ | 3σ_x from f | from Γ | water→5 %: Δx_f (σ) | Δx_Γ (σ) | 5→7.5: Δx_f (σ) | Δx_Γ (σ) | 7.5→10: Δx_f (σ) | Δx_Γ (σ) |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in res.iterrows():
        L.append("| %s | %d | %.1f | %.1f | %.0f | %.0f | %.4f | %.4f | %.4f | %.4f | %.3f (%.0f) | %.3f (%.0f) | %.3f (%.0f) | %.3f (%.0f) | %.3f (%.0f) | %.3f (%.0f) |" % (
            r.estimator, r.n, r.sd_f_liquid, r.sd_G_liquid, r.slope_f_Hz_per_x, r.slope_G_Hz_per_x, r.res_x_f, r.res_x_G, r.res3_x_f, r.res3_x_G,
            r.step_water_gluc05_dx_f, r.step_water_gluc05_sigma_f, r.step_water_gluc05_dx_G, r.step_water_gluc05_sigma_G,
            r.step_gluc05_gluc075_dx_f, r.step_gluc05_gluc075_sigma_f, r.step_gluc05_gluc075_dx_G, r.step_gluc05_gluc075_sigma_G,
            r.step_gluc075_gluc10_dx_f, r.step_gluc075_gluc10_sigma_f, r.step_gluc075_gluc10_dx_G, r.step_gluc075_gluc10_sigma_G))
    L.append("\n## Live datalogs of board 1920 (A as published by the instrument): plateau shifts against KG\n")
    L.append("| run | liquid | n | Δf [Hz] ± sd | eps_f [%] | ΔΓ [Hz] ± sd | eps_Γ [%] | r = ΔΓ/(−Δf) |\n|---|---|---|---|---|---|---|---|")
    for _, r in dsh.iterrows():
        L.append("| %s | %s | %d | %.0f ± %.0f | %+.1f | %.0f ± %.0f | %+.1f | %.2f |" % (r.dataset, r.liquid, r.n, r.df, r.df_sd, 100 * r.eps_f, r.dG, r.dG_sd, 100 * r.eps_G, r.r_KG1))
    L.append("\nDatalog 2026-09-11: %d rows, %d exact duplicates dropped; plateau windows: %s. Datalog 2026-09-10: %d rows, %d duplicates; windows: %s.\n" % (
        nrows11, nd11, {k: v["window"] for k, v in pl11.items()}, nrows10, nd10, {k: v["window"] for k, v in pl10.items()}))
    L.append("## Gate, fold, repeatability\n```\n%s\n```" % json.dumps(gate, indent=1))
    open(os.path.join(OUT, "tables.md"), "w").write("\n".join(L) + "\n")
    json.dump(dict(variant=variant, f0=dict(DS2=f02, DS3=f03), kg_coef=dict(DS2=KG_COEF(f02), DS3=KG_COEF(f03)), sqrt_rhoeta={k: math.sqrt(v) for k, v in RHOETA.items()},
                   summary_n3_9=summ, bias=bias_all, gate=gate, datalog=dict(d0911=dict(rows=nrows11, dup=nd11, plateaus={k: {kk: vv for kk, vv in v.items() if not isinstance(kk, int)} for k, v in pl11.items()}),
                                                                             d0910=dict(rows=nrows10, dup=nd10, plateaus={k: {kk: vv for kk, vv in v.items() if not isinstance(kk, int)} for k, v in pl10.items()}))),
              open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=float)
    print("\n".join(L[:3])); print("wrote", OUT)


if __name__ == "__main__":
    for v in (sys.argv[1:] or ("asis", "fwfix")):
        run(v)
