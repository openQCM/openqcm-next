# -*- coding: utf-8 -*-
"""
run_estimators.py — every estimator on every sweep of 2026-09-11 (45 sweeps:
air / water / isopropanol × overtones 1–9 × 3 replicas), with and without the
firmware carry-over correction. Writes results/sweeps_<variant>.csv (one row
per sweep and estimator) and results/sweeps_<variant>.json (per-sweep detail
incl. fold diagnostics, gate verdicts, residuals summary).

Estimators (all on the same published conductance unless stated):
  mag_argmax   magnitude-only: maximum of the divider ratio (dB); "Γ" = half of
               the −3 dB full width of |H| (w3/2); the −0.3 dB width (main's
               definition) is also stored
  argmax_hh    maximum of G + two-sided half-height half width (the instrument's
               standard estimator)
  midpoint     midpoint of the two half-height crossings, same Γ as argmax_hh
  sym          symmetric Lorentzian, 4 parameters (constant background), ±3 Γ_hh
  sym_lin      symmetric Lorentzian + linear background, 5 parameters
  psl          phase-shifted Lorentzian on G, 5 parameters, ±3 Γ_hh (instrument's
               experimental estimator), with the instrument's gate verdict
  circle       BVD admittance-circle fit of the repository's offline tool
               (software/openQCM/sweep_data/fit_admittance.py, FIT 1), run on
               the published G + jB; reported for reference, not independent
"""
import os, sys, json, importlib.util
import numpy as np, pandas as pd
import qcmchain as q, data

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results"); os.makedirs(OUT, exist_ok=True)
_spec = importlib.util.spec_from_file_location("fa", os.path.join(data.ROOT, "software", "openQCM", "sweep_data", "fit_admittance.py"))
fa = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fa)


def phase_of(s):
    return {"air": "air", "wat": "water", "ipa": "ipa"}[s[:3]]


def analyse_sweep(f, vm, vp, firmware_fix):
    c = q.chain(f, vm, vp, firmware_fix=firmware_fix)
    F, G, B = c["f"], c["G"], c["B"]
    e = q.argmax_halfheight(F, G)
    f0, g0 = e["f_max"], e["gamma_hh"]
    mask = q.fit_window(F, f0, g0)
    f_lo, f_hi = float(F[mask].min()), float(F[mask].max())
    psl = q.fit_psl(F, G, f0, g0)
    ok, reason = q.psl_gate(psl, g0, f_lo, f_hi)
    sym = q.fit_symmetric(F, G, f0, g0)
    syml = q.fit_symmetric(F, G, f0, g0, linear=True)
    mag = q.magnitude_estimator(F, c["V_MAG"])
    try:
        circ = fa.fit1_circle(F, G + 1j * B, mask)
    except Exception as ex:
        circ = dict(fs=np.nan, gamma=np.nan, theta=np.nan, rms_rel=np.nan, R1=np.nan, C0=np.nan)
    rows = []
    def add(est, fres, gamma, **kw):
        rows.append(dict(estimator=est, fres=float(fres), gamma=float(gamma),
                         D_ppm=2e6 * gamma / fres if fres and np.isfinite(gamma) else np.nan, **kw))
    add("mag_argmax", mag["f_max"], mag["w3"] / 2.0 if np.isfinite(mag["w3"]) else np.nan, w03=mag["w03"], w3_mid=mag["w3_mid"])
    add("argmax_hh", f0, g0, one_sided=e["one_sided"], baseline_frac=e["baseline"] / (e["g_peak"] + e["baseline"]) if e["g_peak"] else np.nan)
    add("midpoint", e["f_mid"], g0)
    add("sym", sym["fres"], sym["gamma"], rms_rel=sym["rms_rel"], converged=sym["converged"], n_fit=sym["n_fit"])
    add("sym_lin", syml["fres"], syml["gamma"], rms_rel=syml["rms_rel"], converged=syml["converged"], n_fit=syml["n_fit"])
    add("psl", psl["fres"], psl["gamma"], phi_deg=psl["phi_deg"], rms_rel=psl["rms_rel"], converged=psl["converged"],
        n_fit=psl["n_fit"], gate_ok=ok, gate_reason=reason, gmax=psl["gmax"], g_off=psl["g_off"],
        bias_pred=q.argmax_bias(psl["gamma"], psl["phi_deg"]), bias_meas=f0 - psl["fres"],
        hh_factor_pred=q.halfheight_width_factor(psl["phi_deg"]), hh_factor_meas=g0 / psl["gamma"])
    add("circle", circ["fs"], circ["gamma"] / 2.0, theta_deg=np.degrees(circ["theta"]), rms_rel=circ["rms_rel"], R1=circ["R1"], C0=circ["C0"])
    common = dict(fold=c["fold"], delta=c["delta"], depth=c["fold_info"]["depth"], r_min=c["fold_info"]["r_min"],
                  baseline_deg=c["fold_info"]["baseline"], Gmax_mS=1e3 * (e["g_peak"] + e["baseline"]), Rm_ohm=1.0 / (e["g_peak"] + e["baseline"]),
                  ratio_dB_peak=(c["V_MAG"][e["i_max"]] - q.V_CP) / q.MAG_SLOPE, window_right_gamma=(F[-1] - f0) / g0, window_left_gamma=(f0 - F[0]) / g0)
    for r in rows:
        r.update(common)
    return rows, dict(psl_residual=psl.get("residual"), sym_residual=sym.get("residual"), idx=psl.get("idx"))


def main():
    dumps, mt = data.dumps_0911()
    for variant, fix in (("asis", False), ("fwfix", True)):
        allrows = []
        for (s, n), (f, vm, vp) in sorted(dumps.items()):
            rows, _ = analyse_sweep(f, vm, vp, fix)
            for r in rows:
                r.update(set=s, phase=phase_of(s), n=n, replica=int(s[-1]), mtime=mt[(s, n)])
            allrows += rows
            print(variant, s, n, "fold" if rows[0]["fold"] else "no fold", flush=True)
        df = pd.DataFrame(allrows)
        df.to_csv(os.path.join(OUT, "sweeps_%s.csv" % variant), index=False)
        print("wrote", "sweeps_%s.csv" % variant, len(df), "rows")


if __name__ == "__main__":
    main()
