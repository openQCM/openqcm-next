"""Admittance circles under three phase-unfolding rules, air / water / isopropanol, board 1920, 2026-09-11.

    PYTHONPATH=software python fold_hypothesis_circles.py <data_root> <out_dir>

  chain : what the process does (fold + offset only when the peak-depth test passes)
  H1    : ALWAYS flip the sign at the minimum of the reading; offset only where the reading goes below 0 deg
  H2    : ALWAYS flip AND always bring the minimum of the reading to 0 deg (delta = -min r)
Same smoothing as the process (SG 51/3, spline s = 0.001); the circle fit is fit_admittance.fit1_circle on
the +-3 Gamma window of each variant's own G. Middle replica of each phase.
"""
import sys, os, json, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software")); sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py")); fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
proc = MultiscanProcess(None); N = (1, 3, 5, 7, 9); SETS = (("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))
VAR = ("chain", "H1", "H2"); COL = {"chain": "#2a78d6", "H1": "#eb6834", "H2": "#1baf7a"}

def smooth(path):
    g = np.loadtxt(path); freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    return np.linspace(freq[0], freq[-1], points), sm(g[:, 1]), sm(g[:, 2])

def variant(fr, Vm, Vp, which):
    r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r))
    if which == "chain":
        decided, _ = proc._phase_fold_decision(fr, Vm, r); flip = bool(decided) if decided is not None else False; delta = -rmin if flip else 0.0
    elif which == "H1":
        flip = True; delta = -rmin if rmin < 0 else 0.0
    else:
        flip = True; delta = -rmin
    corr = r + delta; R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X)
    sg = corr.copy()
    if flip:
        i = int(np.nanargmin(np.abs(corr))); sg[i:] *= -1
    Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb)
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth); mask = np.abs(fr - f_arg) <= 3 * gam
    c = fa.fit1_circle(fr, G + 1j * B, mask)
    step = float(np.nanmax(np.abs(np.diff(B[mask])))) / float(np.nanmax(B[mask]) - np.nanmin(B[mask])) * 100.0
    return dict(G=G, B=B, mask=mask, f_arg=f_arg, gamma=gam, flip=flip, delta=delta, rmin=rmin, fit=c, jumpB=step, D_ppm=2e6 * gam / f_arg)

res = {}
for liq, s in SETS:
    fig, ax = plt.subplots(5, 3, figsize=(15, 22))
    for i, n in enumerate(N):
        fr, Vm, Vp = smooth(os.path.join(ROOT, s, "g%d.txt" % n))
        for j, v in enumerate(VAR):
            o = variant(fr, Vm, Vp, v); res[(liq, n, v)] = o; a = ax[i, j]; m = o["mask"]; c = o["fit"]
            a.plot(o["G"] * 1e3, o["B"] * 1e3, color="#bbbbbb", lw=0.6, label="whole sweep")
            a.plot(o["G"][m] * 1e3, o["B"][m] * 1e3, color=COL[v], lw=1.6, label="±3Γ window (%d pts)" % m.sum())
            t = np.linspace(0, 2 * np.pi, 361); a.plot((c["xc"] + c["r"] * np.cos(t)) * 1e3, (c["yc"] + c["r"] * np.sin(t)) * 1e3, "k--", lw=0.8, label="circle fit")
            k = int(np.nanargmax(o["G"])); a.plot(o["G"][k] * 1e3, o["B"][k] * 1e3, "v", color="#d62728", ms=7, label="argmax G")
            a.set_aspect("equal", adjustable="datalim"); a.grid(alpha=0.25)
            a.set_title("%s n=%d  %s: flip=%s δ=%+.1f°\nR1=%.0f Ω  C0=%.1f pF  rms=%.1f%%  max ΔB step=%.0f%%" % (liq, n, v, o["flip"], o["delta"], c["R1"], c["C0"] * 1e12, 100 * c["rms_rel"], o["jumpB"]), fontsize=8)
            if i == 4: a.set_xlabel("G [mS]")
            if j == 0: a.set_ylabel("B [mS]")
            if i == 0 and j == 0: a.legend(fontsize=7, loc="best")
    fig.suptitle("%s (%s): admittance locus under three unfolding rules — chain / H1 always flip / H2 always flip and always zero the minimum" % (liq, s), fontsize=11, y=0.998)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "circles_%s.png" % liq), dpi=90); plt.close(fig)

# tables
L = ["| phase | n | rule | flip | δ [°] | argmax G [Hz] | Γ half height [Hz] | D [ppm] | R1 [Ω] | C0 [pF] | circle rms [% r] | largest step in B [% of range] |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for liq, s in SETS:
    for n in N:
        for v in VAR:
            o = res[(liq, n, v)]; c = o["fit"]
            L.append("| %s | %d | %s | %s | %+.1f | %.0f | %.1f | %.1f | %.0f | %.1f | %.1f | %.0f |" % (liq, n, v, o["flip"], o["delta"], o["f_arg"], o["gamma"], o["D_ppm"], c["R1"], c["C0"] * 1e12, 100 * c["rms_rel"], o["jumpB"]))
# shifts under each rule, against the air of the same rule
air = {(n, v): res[("air", n, v)] for n in N for v in VAR}
L2 = ["\n| liquid | n | rule | Δf (argmax G) [Hz] | ΔΓ [Hz] | \\|Δf\\|/ΔΓ |", "|---|---|---|---|---|---|"]
for liq in ("water", "ipa"):
    for n in N:
        for v in VAR:
            o = res[(liq, n, v)]; a = air[(n, v)]; df = o["f_arg"] - a["f_arg"]; dG = o["gamma"] - a["gamma"]
            L2.append("| %s | %d | %s | %.0f | %.0f | %.2f |" % (liq, n, v, df, dG, abs(df) / dG))
open(os.path.join(OUT, "fold_hypothesis_tables.md"), "w").write("\n".join(L + L2)); print("\n".join(L + L2))
