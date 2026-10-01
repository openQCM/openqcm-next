"""Table 1 and 2 — the phase offset delta from the fold (published) against delta from the roundness fit
(reverted 2026-07-28), on the 45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/delta_fold_vs_roundness.py

Both rules are fit_admittance.admittance(offset="fold" | "circle"); raw samples, -28 dB mask and the +-3
half-width band as in fit_admittance.analyse().
  continuity  : largest step of B between adjacent samples over the +-3 half-width window, % of B's range there
  circle rms  : FIT 1 radial residual, % of the fitted radius
  Gamma split : |Gamma_FIT1 - Gamma_FIT2| / Gamma_FIT2, % (both FWHM) — the two estimators share nothing
"""
import numpy as np
from offline_fits_lib import sweeps, analyse_arrays, window, max_step_pct, rng, write, PHASES, N

RULES = ("fold", "circle")
res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    for rule in RULES:
        a = analyse_arrays(f, Vm, Vp, offset=rule)
        w = window(f, a["fs_seed"], a["hw_seed"])
        g1, g2 = a["fit1"]["gamma"], a["fit2"]["gamma"]
        res[(phase, s, n, rule)] = dict(delta=a["delta"], applied=bool(a["delta"]) or rule == "fold",
                                        step=max_step_pct(a["Y"].imag, w), rms=100 * a["fit1"]["rms_rel"],
                                        split=100 * abs(g1 - g2) / g2 if g2 > 0 else np.nan)

L = ["## Table 1a — per phase and overtone, range over the three replicas", "",
     "| phase | n | δ fold [°] | δ roundness [°] | B step, fold [%] | B step, roundness [%] | circle rms, fold [%] | circle rms, roundness [%] |",
     "|---|---|---|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda rule, k: [res[(phase, s, n, rule)][k] for s in sets]
        L.append("| %s | %d | %s | %s | %s | %s | %s | %s |" % (
            phase, n, rng(g("fold", "delta"), "%+.1f"), rng(g("circle", "delta"), "%+.1f"),
            rng(g("fold", "step")), rng(g("circle", "step")), rng(g("fold", "rms")), rng(g("circle", "rms"))))
L += ["", "δ roundness = 0.0 means the search was rejected by its own guards (optimum on a bound, or residual above 5 %),",
      "and the rule then applies no offset and no flip.", "",
      "## Table 1b — summary, the shape of the HANDOFF table", "",
      "| rule | B step [% of range], all phases | circle rms, air [%] | circle rms, water [%] | circle rms, isopropanol [%] |",
      "|---|---|---|---|---|"]
for rule in RULES:
    allr = [v for k, v in res.items() if k[3] == rule]
    ph = lambda p, key: [v[key] for k, v in res.items() if k[3] == rule and k[0] == p]
    L.append("| %s | %s | %s | %s | %s |" % (rule, rng([v["step"] for v in allr]), rng(ph("air", "rms")),
                                             rng(ph("water", "rms")), rng(ph("isopropanol", "rms"))))
L += ["", "## Table 2 — Γ split between FIT 1 and FIT 2, % (independent of circularity)", "",
      "| rule | median, 45 sweeps | median, fundamentals (9) | median, n ≥ 3 (36) | range, 45 sweeps |", "|---|---|---|---|---|"]
for rule in RULES:
    v = [x["split"] for k, x in res.items() if k[3] == rule]
    v1 = [x["split"] for k, x in res.items() if k[3] == rule and k[2] == 1]
    v3 = [x["split"] for k, x in res.items() if k[3] == rule and k[2] > 1]
    L.append("| %s | %.2f | %.2f | %.2f | %s |" % (rule, np.nanmedian(v), np.nanmedian(v1), np.nanmedian(v3), rng(v, "%.2f")))
write("table1_2_delta.md", "\n".join(L))
