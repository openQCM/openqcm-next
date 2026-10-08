# -*- coding: utf-8 -*-
"""
run_bias_theory.py — closed-form biases of the simple estimators for a rotated
Lorentzian, checked on the 45 sweeps; the rotation angle φ across overtones,
loads, replicas and days; the board delay from the open/short/load sweeps.

Closed forms (derived in research/paper/notes/derivations.md), Δ = f_res − f:
  G(Δ) = A (Γ cos φ − Δ sin φ)/(Δ² + Γ²) + G_off
  maximum at Δ = −Γ tan(φ/2)   →  f_Gmax = f_res + Γ tan(φ/2)
  G_peak − G_off = (A/Γ) cos²(φ/2);  minimum G_min − G_off = −(A/Γ) sin²(φ/2)
  half-height crossings (level G_off + (G_peak−G_off)/2):
      Δ± = Γ[−sin φ ± √(c(2−c))]/c,  c = cos²(φ/2)
      Γ_hh = (Δ+ − Δ−)/2 = Γ √(1 + 2 tan²(φ/2))
      midpoint  f_mid = f_res + 2Γ tan(φ/2)
Also: the symmetric-Lorentzian fit of a rotated Lorentzian has no closed form;
its bias is computed numerically on noise-free model curves (±3 Γ_hh window).
"""
import os, json
import numpy as np, pandas as pd
import qcmchain as q, data

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
L = ["# Rotation bias: theory against the 45 sweeps; the angle φ; the board delay\n"]


def check_closed_forms():
    """Numerical verification of the closed forms on noise-free model curves."""
    rows = []
    for phi in (-5, -8, -15, -20, -25, -28, -40):
        for gamma in (65.0, 1600.0):
            fres = 10e6; f = np.arange(fres - 12000, fres + 6001, 1.0)
            G = q.rotated_lorentzian(f, fres, gamma, phi, 1e-3, 1e-4)
            e = q.argmax_halfheight(f, G, n_base=100)
            # the baseline here is taken far from resonance (the window is wide), so G_off is recovered
            sym = q.fit_symmetric(f, G, e["f_max"], e["gamma_hh"]); syml = q.fit_symmetric(f, G, e["f_max"], e["gamma_hh"], linear=True)
            rows.append(dict(phi=phi, gamma=gamma, bias_argmax_num=e["f_max"] - fres, bias_argmax_th=float(q.argmax_bias(gamma, phi)),
                             hh_num=e["gamma_hh"] / gamma, hh_th=float(q.halfheight_width_factor(phi)),
                             mid_num=e["f_mid"] - fres, mid_th=float(q.midpoint_bias(gamma, phi)),
                             sym_bias=sym["fres"] - fres, sym_gamma=sym["gamma"] / gamma, symlin_bias=syml["fres"] - fres, symlin_gamma=syml["gamma"] / gamma))
    t = pd.DataFrame(rows); t.to_csv(os.path.join(R, "closed_forms_check.csv"), index=False)
    L.append("## Closed forms against noise-free rotated Lorentzians (1 Hz grid, window −12/+6 kHz, ±3 Γ_hh fits)\n")
    L.append("| φ [°] | Γ [Hz] | argmax bias num / theory [Hz] | Γ_hh/Γ num / theory | midpoint bias num / theory [Hz] | sym. Lorentzian f bias [Hz] (Γ ratio) | sym.+linear f bias [Hz] (Γ ratio) |\n|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        L.append("| %d | %.0f | %.1f / %.1f | %.4f / %.4f | %.1f / %.1f | %.1f (%.3f) | %.1f (%.3f) |" % (
            r.phi, r.gamma, r.bias_argmax_num, r.bias_argmax_th, r.hh_num, r.hh_th, r.mid_num, r.mid_th, r.sym_bias, r.sym_gamma, r.symlin_bias, r.symlin_gamma))
    return t


def check_on_data():
    d = pd.read_csv(os.path.join(R, "sweeps_asis.csv"))
    p = d[d.estimator == "psl"].copy()
    m = d[d.estimator == "midpoint"][["set", "n", "fres"]].rename(columns={"fres": "f_mid"})
    s = d[d.estimator == "sym_lin"][["set", "n", "fres", "gamma"]].rename(columns={"fres": "f_sym", "gamma": "g_sym"})
    p = p.merge(m, on=["set", "n"]).merge(s, on=["set", "n"])
    p["mid_meas"] = p.f_mid - p.fres; p["mid_pred"] = q.midpoint_bias(p.gamma, p.phi_deg)
    p["resid_bias"] = p.bias_meas - p.bias_pred; p["resid_bias_gamma"] = p.resid_bias / p.gamma
    L.append("\n## On the 45 sweeps: f_Gmax − f_res (measured) against Γ·tan(φ/2) (from the fitted Γ, φ)\n")
    L.append("| set | n | Γ [Hz] | φ [°] | f_Gmax − f_res [Hz] | Γ tan(φ/2) [Hz] | diff [Hz] | diff/Γ | Γ_hh/Γ meas | √(1+2tan²(φ/2)) | f_mid − f_res meas / pred [Hz] | f_sym − f_res [Hz] |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in p.iterrows():
        L.append("| %s | %d | %.0f | %.1f | %+.0f | %+.0f | %+.0f | %+.3f | %.3f | %.3f | %+.0f / %+.0f | %+.0f |" % (
            r.set, r.n, r.gamma, r.phi_deg, r.bias_meas, r.bias_pred, r.resid_bias, r.resid_bias_gamma, r.hh_factor_meas, r.hh_factor_pred, r.mid_meas, r.mid_pred, r.f_sym - r.fres))
    stats = dict(bias_diff_mean=float(p.resid_bias.mean()), bias_diff_sd=float(p.resid_bias.std()), bias_diff_maxabs=float(p.resid_bias.abs().max()),
                 bias_diff_over_gamma_mean=float(p.resid_bias_gamma.mean()), bias_diff_over_gamma_maxabs=float(p.resid_bias_gamma.abs().max()),
                 n1_liquid_diff=p[(p.n == 1) & (p.phase != "air")].resid_bias.tolist())
    L.append("\nOver 45 sweeps: measured − predicted bias = %+.0f ± %.0f Hz (sd), max |.| = %.0f Hz; in units of Γ: mean %+.3f, max |.| %.3f. The liquid fundamentals (n = 1, water and isopropanol) carry the largest residual (−40…−45 Hz): there the fold plateau of the phase channel sits under the peak.\n"
             % (stats["bias_diff_mean"], stats["bias_diff_sd"], stats["bias_diff_maxabs"], stats["bias_diff_over_gamma_mean"], stats["bias_diff_over_gamma_maxabs"]))
    # half-height width: rotation (+) vs baseline-on-the-skirt (−)
    L.append("## The half-height half width Γ_hh against the fitted Γ: two opposite biases\n")
    L.append("Rotation widens the half-height width by √(1+2tan²(φ/2)) (+0.5 % at φ = −8°, +6 % at −28°). The instrument's baseline (mean of the first 100 samples of a window sized for air) sits on the skirt of a liquid-broadened peak and raises the half level, which narrows the measured width. Measured ratio per phase:\n")
    L.append("| phase | n | Γ_hh/Γ_psl (mean of 3) | rotation factor | baseline / G_peak [%] |\n|---|---|---|---|---|")
    a = d[d.estimator == "argmax_hh"][["set", "n", "baseline_frac"]].rename(columns={"baseline_frac": "bl_frac"})
    pp = p.merge(a, on=["set", "n"])
    for (ph, n), gq in pp.groupby(["phase", "n"]):
        L.append("| %s | %d | %.3f | %.3f | %.1f |" % (ph, n, gq.hh_factor_meas.mean(), gq.hh_factor_pred.mean(), 100 * gq.bl_frac.mean()))
    return p, stats


def phi_analysis(p):
    L.append("\n## The rotation angle φ (PSL on G) by overtone, load and replica\n")
    L.append("| n | f [MHz] | φ air (3 replicas) | φ water | φ isopropanol | sd within phase (max) | air − liquid [°] |\n|---|---|---|---|---|---|---|")
    out = {}
    for n, g in p.groupby("n"):
        a = g[g.phase == "air"].phi_deg; w = g[g.phase == "water"].phi_deg; i = g[g.phase == "ipa"].phi_deg
        out[int(n)] = dict(air=a.tolist(), water=w.tolist(), ipa=i.tolist())
        L.append("| %d | %.1f | %s | %s | %s | %.2f | %+.1f / %+.1f |" % (n, g.fres.mean() / 1e6, " / ".join("%.1f" % v for v in a), " / ".join("%.1f" % v for v in w),
                                                                     " / ".join("%.1f" % v for v in i), max(a.std(), w.std(), i.std()), a.mean() - w.mean(), a.mean() - i.mean()))
    # another day: air sweeps of 2026-09-03 (125 MHz board), same chain
    L.append("\n### Air sweeps of 2026-09-03 (research/board-125MHz-air-2026-09-03, same chain)\n")
    L.append("| n | f_Gmax [Hz] | Γ_hh [Hz] | fold | δ [°] | depth | PSL f_res − f_Gmax [Hz] | Γ_psl [Hz] | φ [°] | rms [%] | φ on 2026-09-11 air (mean) |\n|---|---|---|---|---|---|---|---|---|---|---|")
    air03 = {}
    for n, (f, vm, vp) in data.air_0903().items():
        c = q.chain(f, vm, vp); e = q.argmax_halfheight(c["f"], c["G"]); ps = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"])
        air03[n] = dict(f_max=e["f_max"], gamma_hh=e["gamma_hh"], fold=c["fold"], delta=c["delta"], depth=c["fold_info"]["depth"], fres=ps["fres"], gamma=ps["gamma"], phi=ps["phi_deg"], rms=ps["rms_rel"])
        L.append("| %d | %.0f | %.1f | %s | %+.2f | %.3f | %+.1f | %.1f | %.1f | %.2f | %.1f |" % (
            n, e["f_max"], e["gamma_hh"], c["fold"], c["delta"], c["fold_info"]["depth"], ps["fres"] - e["f_max"], ps["gamma"], ps["phi_deg"], 100 * ps["rms_rel"], np.mean(out[n]["air"])))
    # frozen water reference of 2026-07-28 (fundamental, another day)
    f, vm, vp = data.reference_g1(); c = q.chain(f, vm, vp); e = q.argmax_halfheight(c["f"], c["G"]); ps = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"])
    ref = dict(f_max=e["f_max"], gamma_hh=e["gamma_hh"], fres=ps["fres"], gamma=ps["gamma"], phi=ps["phi_deg"], rms=ps["rms_rel"], fold=c["fold"], delta=c["delta"])
    L.append("\nFrozen water reference sweep of 2026-07-28 (fundamental, docs/impedance-analysis/reference-sweep/g1.txt): f_Gmax = %.0f Hz, Γ_hh = %.1f Hz, PSL f_res − f_Gmax = %+.1f Hz, Γ = %.1f Hz, φ = %.1f°, rms %.2f %% (2026-09-11 water n = 1: φ = %.1f°). ⚠️ The board of that sweep is not recorded.\n"
             % (e["f_max"], e["gamma_hh"], ps["fres"] - e["f_max"], ps["gamma"], ps["phi_deg"], 100 * ps["rms_rel"], np.mean(out[1]["water"])))
    return out, air03, ref


def phi0_tau(p):
    """phi = phi0 - 360 f tau fitted to the mean phi per overtone (2026-09-11 per phase; 2026-09-03 air), all n and n >= 3."""
    rows = []
    sets = {ph: p[p.phase == ph].groupby("n").agg(f=("fres", "mean"), phi=("phi_deg", "mean")).reset_index() for ph in ("air", "water", "ipa")}
    a03 = BT_AIR03 = None
    for name, m in list(sets.items()):
        for label, sel in (("n=1-9", m.n >= 1), ("n=3-9", m.n >= 3)):
            x = -360.0 * m.f[sel].values * 1e-9; y = m.phi[sel].values
            A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, y, rcond=None)
            rows.append(dict(set="2026-09-11 " + name, fit=label, phi0_deg=float(sol[1]), tau_ns=float(sol[0]), rms_deg=float(np.sqrt(np.mean((A @ sol - y) ** 2)))))
    return rows


def osl_delay():
    """Phase of the short and 50 Ω standards against frequency: a resistive load has
    zero true phase, so the reading is the instrument. Fit |Δφ| = a + 360 f τ on 3–50 MHz."""
    o = data.osl(); res = {}
    L.append("\n## Board phase from the resistive standards (open/short/50 Ω sweeps of 2026-09-03, 1–51 MHz)\n")
    L.append("| standard | fit range | slope [°/MHz] | delay τ [ns] | intercept [°] | rms [°] | |Δφ| at 5 / 15 / 25 / 35 / 45 MHz [°] | M at 5 / 25 / 45 MHz [Ω] (ideal %s) |\n|---|---|---|---|---|---|---|---|" % "52.3 / 102.3")
    for name in ("short", "load50"):
        f, vm, vp = o[name]; r = q.phase_reading_deg(vp); M = q.divider_magnitude(vm)
        sel = (f >= 3e6) & (f <= 50e6)
        A = np.column_stack([np.ones(sel.sum()), f[sel] / 1e6]); sol, *_ = np.linalg.lstsq(A, r[sel], rcond=None)
        rms = float(np.sqrt(np.mean((A @ sol - r[sel]) ** 2)))
        at = [float(np.interp(x, f, r)) for x in (5e6, 15e6, 25e6, 35e6, 45e6)]
        Mat = [float(np.interp(x, f, M)) for x in (5e6, 25e6, 45e6)]
        res[name] = dict(slope_deg_per_MHz=float(sol[1]), delay_ns=float(sol[1] / 360.0 * 1e3), intercept_deg=float(sol[0]), rms_deg=rms, reading_at=at, M_at=Mat)
        L.append("| %s | 3–50 MHz | %.4f | %.2f | %+.2f | %.2f | %s | %s |" % (name, sol[1], sol[1] / 360 * 1e3, sol[0], rms, " / ".join("%.1f" % v for v in at), " / ".join("%.1f" % v for v in Mat)))
    L.append("\nA pure delay τ gives a phase 360°·f·τ: with τ = 0.76–1.10 ns, 1.4–2.0° at 5 MHz and 12–18° at 45 MHz. The PSL angle is −8° at 5 MHz and −27° at 45 MHz: same order at the top of the band, 4× larger at the bottom, and it grows roughly as f^0.55 rather than linearly. ⚠️ The resistive standards also read a non-zero phase at low frequency (intercept) and their own fixturing contributes an unknown delay.\n")
    return res


if __name__ == "__main__":
    t = check_closed_forms()
    p, stats = check_on_data()
    phis, air03, ref = phi_analysis(p)
    pt = phi0_tau(p)
    m = pd.DataFrame([dict(f=air03[n]["fres"], phi=air03[n]["phi"], n=n) for n in air03])
    for label, sel in (("n=1-9", m.n >= 1), ("n=3-9", m.n >= 3)):
        x = -360.0 * m.f[sel].values * 1e-9; y = m.phi[sel].values; A = np.column_stack([x, np.ones_like(x)]); sol, *_ = np.linalg.lstsq(A, y, rcond=None)
        pt.append(dict(set="2026-09-03 air", fit=label, phi0_deg=float(sol[1]), tau_ns=float(sol[0]), rms_deg=float(np.sqrt(np.mean((A @ sol - y) ** 2)))))
    L.append("\n## φ = φ₀ − 360·f·τ fitted to the mean φ per overtone (board 1920 and the 2026-09-03 air set)\n")
    L.append("| set | fit | φ₀ [°] | τ [ns] | rms [°] |\n|---|---|---|---|---|")
    for r in pt:
        L.append("| %s | %s | %.1f | %.2f | %.1f |" % (r["set"], r["fit"], r["phi0_deg"], r["tau_ns"], r["rms_deg"]))
    L.append("\nA constant plus a delay is an approximation (rms 1–3° here) and both parameters move when n = 1 is excluded; it is reported for comparison with the 2024 set, not as a model of φ.\n")
    osl = osl_delay()
    open(os.path.join(R, "bias_theory.md"), "w").write("\n".join(L) + "\n")
    json.dump(dict(bias_stats=stats, phi=phis, air_0903=air03, reference_0728=ref, osl=osl, phi0_tau=pt), open(os.path.join(R, "bias_theory.json"), "w"), indent=1, default=float)
    print("\n".join(L))
