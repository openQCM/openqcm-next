"""The plateau at the fold: slope of the signed phase and of B at the zero crossing against +-Gamma/2.

    cd software && PYTHONPATH=. python ../research/.../scripts/fold_rounding.py <npz> <out_dir>

For a resonance the phase of H = R17/(Z_q + R17) is steepest where it crosses zero, and so is B: for
phi = -2 atan(x), slope(0)/slope(x) = 1 + x^2, i.e. 1.25 at half a half-width. The detector reads |phi| with a
response that bends within ~+-18 deg of zero (AD8302 data sheet, TPC 25-29); undoing the fold at the minimum
then leaves a PLATEAU in the signed phase and a shoulder in B. Measured here without any model of the flanks:
the slope at the fold over the slope at +-Gamma/2, the half-width of the region where the slope stays below
half its +-Gamma/2 value, and the reading at the edge of that region (how many degrees from zero the bend
starts). Every fold the chain takes: air n = 1..9, water and isopropanol n = 1; all three replicas.
"""
import sys, os, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software")); sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
SRC, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True); proc = MultiscanProcess(None); Z = np.load(SRC)
CASES = [("air_%d" % k, n) for k in (0, 1, 2) for n in (1, 3, 5, 7, 9)] + [("wat_%d" % k, 1) for k in (0, 1, 2)] + [("ipa_%d" % k, 1) for k in (0, 1, 2)]

def smooth(g):
    freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    return np.linspace(freq[0], freq[-1], points), sm(g[:, 1]), sm(g[:, 2])

def slope_at(fr, y, f, half=5):
    m = np.abs(fr - f) <= half; p = np.polyfit(fr[m], y[m], 1); return p[0]

rows = []; panels = []
for s, n in CASES:
    fr, Vm, Vp = smooth(Z["%s/g%d" % (s, n)]); r = proc._phase_raw_V_phase(Vp); i0 = int(np.nanargmin(r)); f0 = fr[i0]; rmin = float(r[i0])
    decided, _ = proc._phase_fold_decision(fr, Vm, r); flip = bool(decided) if decided is not None else False
    if not flip: continue
    corr = r - rmin; sg = corr.copy(); j = int(np.nanargmin(np.abs(corr))); sg[j:] *= -1
    R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X); Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb)
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth)
    hw = max(5.0, 0.03 * gam)                       # slope window: +-5 Hz in air, +-3 % of Gamma in liquid
    s0 = abs(slope_at(fr, sg, f0, hw)); sL = abs(slope_at(fr, sg, f0 - gam / 2, hw)); sR = abs(slope_at(fr, sg, f0 + gam / 2, hw)); sh = 0.5 * (sL + sR)
    b0 = abs(slope_at(fr, B, f0, hw)); bL = abs(slope_at(fr, B, f0 - gam / 2, hw)); bR = abs(slope_at(fr, B, f0 + gam / 2, hw)); bh = 0.5 * (bL + bR)
    # plateau: where |d sg/df| < 0.5 * slope at +-Gamma/2, contiguous around f0
    d = np.abs(np.gradient(sg, fr)); low = d < 0.5 * sh
    a = i0
    while a > 0 and low[a - 1]: a -= 1
    b = i0
    while b < len(fr) - 1 and low[b + 1]: b += 1
    plateau = fr[b] - fr[a]; edge_deg = 0.5 * (corr[a] + corr[b])          # |phi| (offset removed) at the plateau edges
    rows.append((s, n, gam, rmin, s0, sh, s0 / sh, b0, bh, b0 / bh, plateau, plateau / gam, edge_deg, f0 - f_arg))
    if s.endswith("_1"): panels.append((s, n, fr, corr, sg, B, G, f0, gam, f_arg, fr[a] - f0, fr[b] - f0))

L = ["| set | n | Γ [Hz] | reading min [°] | signed-phase slope at fold [°/Hz] | at ±Γ/2 [°/Hz] | ratio fold / ±Γ/2 (atan: 1.25) | B slope at fold [µS/Hz] | at ±Γ/2 | ratio | plateau width [Hz] | plateau / Γ | \\|φ\\| at plateau edge [°] | f(fold) − argmax G [Hz] |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for t in rows:
    L.append("| %s | %d | %.0f | %+.2f | %.3f | %.3f | **%.2f** | %.2f | %.2f | **%.2f** | %.0f | %.2f | %.1f | %+.0f |" % (t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7] * 1e6, t[8] * 1e6, t[9], t[10], t[11], t[12], t[13]))
open(os.path.join(OUT, "fold_rounding_tables.md"), "w").write("\n".join(L)); print("\n".join(L))

fig, ax = plt.subplots(len(panels), 3, figsize=(17, 3.4 * len(panels)))
for i, (s, n, fr, corr, sg, B, G, f0, gam, f_arg, pa, pb) in enumerate(panels):
    z = np.abs(fr - f0) <= 1.5 * gam; x = fr - f0
    a = ax[i, 0]; a.plot(x[z], corr[z], color="#2a78d6", lw=1.2, label="|φ| = reading + δ"); a.plot(x[z], sg[z], color="#eb6834", lw=1.2, label="signed phase (fold undone)")
    a.axvspan(pa, pb, color="#eb6834", alpha=0.15, label="plateau: slope < ½ of ±Γ/2"); a.axhline(0, color="k", lw=0.5); a.set_title("%s n=%d: phase through the fold" % (s, n), fontsize=9); a.set_xlabel("f − f(fold) [Hz]"); a.set_ylabel("deg"); a.grid(alpha=0.25); a.legend(fontsize=7)
    a = ax[i, 1]; a.plot(x[z], np.gradient(sg, fr)[z], color="#eb6834", lw=1.2, label="d(signed phase)/df"); a.axvspan(pa, pb, color="#eb6834", alpha=0.15)
    for xx in (-gam / 2, gam / 2): a.axvline(xx, color="#888", lw=0.6, ls=":")
    a.set_title("slope of the signed phase (dotted: ±Γ/2)", fontsize=9); a.set_xlabel("f − f(fold) [Hz]"); a.set_ylabel("deg/Hz"); a.grid(alpha=0.25); a.legend(fontsize=7)
    a = ax[i, 2]; a.plot(x[z], B[z] * 1e3, color="#2a78d6", lw=1.3, label="B (chain)"); a.plot(x[z], G[z] * 1e3 * 0.5, color="#888", lw=0.8, label="G/2"); a.axvspan(pa, pb, color="#eb6834", alpha=0.15); a.axvline(f_arg - f0, color="#d62728", lw=0.8, label="argmax G")
    a.set_title("B(f) through the fold", fontsize=9); a.set_xlabel("f − f(fold) [Hz]"); a.set_ylabel("mS"); a.grid(alpha=0.25); a.legend(fontsize=7)
fig.suptitle("The plateau at the fold: the signed phase and B flatten where the detector reads within a few degrees of zero (middle replicas)", fontsize=11, y=0.999)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fold_plateau.png"), dpi=90); plt.close(fig)
