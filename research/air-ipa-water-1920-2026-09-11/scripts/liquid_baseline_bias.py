"""Table 6 — the published half width in liquid: what the off-resonance baseline subtracts, how the half-height
Gamma compares with a Lorentzian with a free background, and whether +-3 Gamma fits inside the sweep window, on the
45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/liquid_baseline_bias.py

This one runs THE CHAIN, not fit_admittance: SG 51/3 + spline as the process, the fold decided by the peak depth
(_phase_fold_decision), delta = -min(r) on a fold, G from _G_exact, Gamma = _half_bandwidth_G_exact (HALF width,
baseline = mean of the first 100 samples). The Lorentzian is fit_admittance.fit2_lorentzian (linear background
free) on the same smoothed G over +-3 Gamma; its FWHM is halved for the comparison.
"""
import numpy as np
from scipy.interpolate import UnivariateSpline
from offline_fits_lib import sweeps, fa, rng, write, PHASES, N
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess

proc = MultiscanProcess(None)


def smooth(f, Vm, Vp):
    points = int(f[-1] - f[0]) + 1; xr = range(len(f)); xs = np.linspace(0, len(f) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order),
                                    s=Constants.SPLINE_FACTOR_G)(xs)
    return np.linspace(f[0], f[-1], points), sm(Vm), sm(Vp)


res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    fr, Vms, Vps = smooth(f, Vm, Vp)
    r = proc._phase_raw_V_phase(Vps); rmin = float(np.nanmin(r))
    decided, _ = proc._phase_fold_decision(fr, Vms, r)
    fold = bool(decided) if decided is not None else False
    R, X = proc._RX_exact(Vms, r + (-rmin if fold else 0.0)); G = proc._G_exact(R, X)
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G)
    hw = abs(band.bandwidth)
    base = float(np.average(G[:100])); peak = float(np.nanmax(G))
    w = np.abs(fr - f_arg) <= 3 * hw
    L2 = fa.fit2_lorentzian(fr, G, w, f_arg, 2 * hw)
    res[(phase, s, n)] = dict(fold=fold, hw=hw, base=100 * base / peak, bias=100 * (hw - L2["gamma"] / 2) / (L2["gamma"] / 2),
                              left=(f_arg - fr[0]) / hw, right=(fr[-1] - f_arg) / hw)

L = ["## Table 6 — the chain's half width, range over the three replicas", "",
     "| phase | n | fold | Γ half height [Hz] | baseline / G max [%] | Γ half height vs Lorentzian [%] | window left / right of f_r [Γ] |",
     "|---|---|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda k: [res[(phase, s, n)][k] for s in sets]
        folds = sorted(set("yes" if x else "no" for x in g("fold")))
        L.append("| %s | %d | %s | %s | %s | %s | %s / %s |" % (phase, n, "/".join(folds), rng(g("hw"), "%.0f"), rng(g("base")),
                                                             rng(g("bias"), "%+.1f"), rng(g("left")), rng(g("right"))))
write("table6_liquid_baseline.md", "\n".join(L))
