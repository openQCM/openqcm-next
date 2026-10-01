"""Table 3 — the two offline estimators against each other (FIT 1 BVD circle, FIT 2 Lorentzian on G), and what
the +-3 half-width band restriction does to FIT 1, on the 45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/fit1_vs_fit2.py

fit_admittance defaults: delta from the fold, -28 dB mask, band 3. f_s split in ppm of f_s; Gamma split in %
of Gamma_FIT2 (both FWHM). "all points" is FIT 1 on every unmasked sample of the 18 001-point sweep.
"""
import numpy as np
from offline_fits_lib import sweeps, analyse_arrays, fa, rng, write, PHASES, N

res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    a = analyse_arrays(f, Vm, Vp)
    f1, f2 = a["fit1"], a["fit2"]
    f1all = fa.fit1_circle(f, a["Y"], a["mask"])
    res[(phase, s, n)] = dict(dfs=1e6 * (f1["fs"] - f2["fs"]) / f2["fs"], dg=100 * (f1["gamma"] - f2["gamma"]) / f2["gamma"],
                              g_all=f1all["gamma"] / f2["gamma"], sd1=f1["sd_fs"], sd2=f2["sd_fs"],
                              n_band=int(a["band_mask"].sum()), n_mask=int(a["mask"].sum()))

L = ["## Table 3 — FIT 1 against FIT 2, range over the three replicas", "",
     "| phase | n | f_s FIT1 − FIT2 [ppm] | Γ FIT1 − FIT2 [% of FIT2] | σ f_s FIT1 / FIT2 [Hz] | Γ FIT1 all points / Γ FIT2 | samples in band / unmasked |",
     "|---|---|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda k: [res[(phase, s, n)][k] for s in sets]
        L.append("| %s | %d | %s | %s | %s / %s | %s | %s / %s |" % (
            phase, n, rng(g("dfs"), "%+.2f"), rng(g("dg"), "%+.1f"), rng(g("sd1"), "%.2f"), rng(g("sd2"), "%.2f"),
            rng(g("g_all"), "%.2f"), rng(g("n_band"), "%d"), rng(g("n_mask"), "%d")))
L += ["", "| phase | \\|f_s split\\| [ppm] | \\|Γ split\\| [%] | Γ all points / Γ FIT2 |", "|---|---|---|---|"]
for phase, _ in PHASES:
    v = [x for k, x in res.items() if k[0] == phase]
    L.append("| %s | %s | %s | %s |" % (phase, rng([abs(x["dfs"]) for x in v], "%.2f"), rng([abs(x["dg"]) for x in v]),
                                        rng([x["g_all"] for x in v], "%.2f")))
write("table3_fit1_fit2.md", "\n".join(L))
