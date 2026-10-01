"""Table 4 — the -28 dB saturation mask (fit_admittance.RATIO_DB_FLOOR; Constants.IMPEDANCE_PANEL_MASK_SATURATED,
off in the process): how much of the +-3 half-width window it removes, and what it does to the circle and to the
split between the two Gamma estimators, on the 45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/saturation_mask.py

delta from the fold, raw samples, band 3. "removed" = samples of the window (taken around the unmasked seed) with
divider ratio at or below the floor, % of the window.
"""
import numpy as np
from offline_fits_lib import sweeps, analyse_arrays, window, fa, rng, write, PHASES, N

res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    off = analyse_arrays(f, Vm, Vp, use_mask=False)
    on = analyse_arrays(f, Vm, Vp, use_mask=True)
    w = window(f, off["fs_seed"], off["hw_seed"])
    removed = 100.0 * float(np.sum(w & (off["dB"] <= fa.RATIO_DB_FLOOR))) / float(w.sum())
    split = lambda a: 100 * abs(a["fit1"]["gamma"] - a["fit2"]["gamma"]) / a["fit2"]["gamma"]
    res[(phase, s, n)] = dict(removed=removed, rms_off=100 * off["fit1"]["rms_rel"], rms_on=100 * on["fit1"]["rms_rel"],
                              split_off=split(off), split_on=split(on))

L = ["## Table 4 — saturation mask at −28 dB, range over the three replicas", "",
     "| phase | n | window removed [%] | circle rms, mask off → on [%] | Γ split FIT1/FIT2, mask off → on [%] |",
     "|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda k: [res[(phase, s, n)][k] for s in sets]
        L.append("| %s | %d | %s | %s → %s | %s → %s |" % (phase, n, rng(g("removed")), rng(g("rms_off")), rng(g("rms_on")),
                                                          rng(g("split_off")), rng(g("split_on"))))
write("table4_saturation_mask.md", "\n".join(L))
