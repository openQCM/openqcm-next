"""Table 5 — where the sweep sits in the AD8302's window: divider ratio |V_INPA/V_INPB| in dB over the sweep and
at resonance, the resonance contrast, and the motional resistance R1 of FIT 1, on the 45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/dynamic_range.py

ratio = fit_admittance.ratio_dB(V_MAG) = (V_MAG - 0.9)/0.030 on the stored (attenuator-compensated) V_MAG; the
AD8302 is specified over +-30 dB. contrast = max - min of the ratio over the sweep. R1 = 1/(2 r) of FIT 1
(delta from the fold, mask, band 3). R17 = 52.3 ohm.
"""
import numpy as np
from offline_fits_lib import sweeps, analyse_arrays, rng, write, PHASES, N

res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    a = analyse_arrays(f, Vm, Vp)
    dB = a["dB"]; k = int(np.argmin(np.abs(f - a["fit1"]["fs"])))
    res[(phase, s, n)] = dict(lo=float(dB.min()), hi=float(dB.max()), at=float(dB[k]), contrast=float(dB.max() - dB.min()),
                              R1=a["fit1"]["R1"])

L = ["## Table 5 — divider ratio and motional resistance, range over the three replicas", "",
     "| phase | n | ratio over the sweep [dB] | ratio at f_s [dB] | contrast [dB] | R1 FIT 1 [Ω] |", "|---|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda k: [res[(phase, s, n)][k] for s in sets]
        L.append("| %s | %d | %s … %s | %s | %s | %s |" % (phase, n, rng(g("lo")), rng(g("hi")), rng(g("at")), rng(g("contrast")),
                                                         rng(g("R1"), "%.0f")))
L += ["", "| phase | ratio, whole sweep, all overtones [dB] | contrast [dB] | R1 [Ω] |", "|---|---|---|---|"]
for phase, _ in PHASES:
    v = [x for k, x in res.items() if k[0] == phase]
    L.append("| %s | %.1f … %.1f | %s | %s |" % (phase, min(x["lo"] for x in v), max(x["hi"] for x in v),
                                                rng([x["contrast"] for x in v]), rng([x["R1"] for x in v], "%.0f")))
write("table5_dynamic_range.md", "\n".join(L))
