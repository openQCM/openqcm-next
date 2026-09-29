"""Figure of the README's "Impedance Measurement Method": G(f) and the admittance locus of one
measured sweep, processed by the chain of ALGORITHM.md §§4-8.

The sweep is the 5th overtone in air of 2026-09-11, board 1920 (dump "air_1/g5" of
research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz). It was chosen as the most
circular locus among the 61 sweeps in the repository: 1.17 % rms of the radius on the ±3Γ core, against
4.1 % for the frozen reference sweep in water.

The chain is written out here so the figure depends on nothing but numpy and matplotlib. Before plotting,
it is run on the frozen reference sweep (docs/impedance-analysis/reference-sweep/g1.txt) and must reproduce
the worked example of ALGORITHM.md §11 (f_res = 4 998 012 Hz, half bandwidth 953.124 Hz).

    cd docs/impedance-analysis/figures/method && python make_conductance_figure.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REFERENCE = REPO / "docs" / "impedance-analysis" / "reference-sweep" / "g1.txt"
DUMPS = REPO / "research" / "air-ipa-water-1920-2026-09-11" / "data" / "sweep_dumps_2026-09-11.npz"
SWEEP_KEY = "air_1/g5"

R = 52.3                 # divider resistor (ohm)
V_CP = 0.9               # AD8302 centre point (V)
FOLD_DEPTH_MIN = 0.88    # Constants.PHASE_FOLD_DEPTH_MIN


def process(f, v_mag, v_phs):
    """G, B, f_res, Γ and the half-height crossings of one sweep."""
    r = (1.8 - v_phs) / 0.010                      # |phase| reading, degrees
    i_v = int(np.nanargmin(r))
    base = np.median(r[:100])
    if (base - r[i_v]) / base >= FOLD_DEPTH_MIN:   # the phase crosses zero: offset and sign
        phi_abs = r - r[i_v]
        phi_signed = phi_abs.copy()
        phi_signed[i_v:] = -phi_signed[i_v:]
    else:                                          # damped load: the reading is the signed phase
        phi_abs = phi_signed = r

    M = R * 10.0 ** ((V_CP - v_mag) / 0.6)

    def admittance(phi_deg):
        p = np.deg2rad(phi_deg)
        Rq = M * np.cos(p) - R
        Xq = -M * np.sin(p)
        den = Rq**2 + Xq**2
        return Rq / den, -Xq / den

    G, _ = admittance(phi_abs)        # G is even in the sign of phi
    _, B = admittance(phi_signed)     # B needs the sign

    i_max = int(np.argmax(G))
    g_base = np.mean(G[:100])
    Gb = G - g_base
    half = Gb[i_max] / 2
    i = np.where(Gb[:i_max] < half)[0][-1]
    f_left = f[i] + (half - Gb[i]) * (f[i + 1] - f[i]) / (Gb[i + 1] - Gb[i])
    j = i_max + np.where(Gb[i_max:] < half)[0][0]
    f_right = f[j - 1] + (half - Gb[j - 1]) * (f[j] - f[j - 1]) / (Gb[j] - Gb[j - 1])
    return dict(G=G, B=B, i_max=i_max, f_res=f[i_max], gamma=(f_right - f_left) / 2,
                f_left=f_left, f_right=f_right, g_half=half + g_base)


def taubin(x, y):
    """Algebraic circle fit (Taubin), for the dashed guide only."""
    xm, ym = x.mean(), y.mean()
    u, v = x - xm, y - ym
    z = u * u + v * v
    zm = z.mean()
    _, _, Vt = np.linalg.svd(np.column_stack([(z - zm) / (2 * np.sqrt(zm)), u, v]), full_matrices=False)
    a0 = Vt[2, 0] / (2 * np.sqrt(zm))
    a1, a2, a3 = Vt[2, 1], Vt[2, 2], -zm * a0
    rad = np.sqrt(a1 * a1 + a2 * a2 - 4 * a0 * a3) / (2 * abs(a0))
    return xm - a1 / (2 * a0), ym - a2 / (2 * a0), rad


# the chain must reproduce ALGORITHM.md §11 before it is trusted with the figure
ref = process(*np.loadtxt(REFERENCE, unpack=True))
assert ref["f_res"] == 4998012.0, ref["f_res"]
assert abs(ref["gamma"] - 953.124) < 1e-3, ref["gamma"]

f, v_mag, v_phs = np.load(DUMPS)[SWEEP_KEY].T
s = process(f, v_mag, v_phs)
f_res, gamma = s["f_res"], s["gamma"]
D = 2 * gamma / f_res
core = np.abs(f - f_res) <= 3 * gamma
xc, yc, rad = taubin(s["G"][core], s["B"][core])
rms = np.sqrt(np.mean((np.hypot(s["G"][core] - xc, s["B"][core] - yc) - rad) ** 2)) / rad
print(f"{SWEEP_KEY}: f_res = {f_res:.0f} Hz, Gamma = {gamma:.1f} Hz, D = {D*1e6:.2f} x 1e-6, "
      f"circle rms = {rms*100:.2f} % of the radius")

# ---------------------------------------------------------------- figure
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SERIES = "#2a78d6"
SURFACE = "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "mathtext.fontset": "dejavusans",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.linewidth": 0.8, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "path",
})

x = f - f_res                          # Hz from the resonance
Gm, Bm = s["G"] * 1e3, s["B"] * 1e3    # mS
i_max = s["i_max"]
g_half = s["g_half"] * 1e3
xl, xr = s["f_left"] - f_res, s["f_right"] - f_res
XW = 6 * gamma                          # G(f) window: ±6Γ

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.7), gridspec_kw={"width_ratios": [1.35, 1]},
                               facecolor=SURFACE)
fig.subplots_adjust(left=0.075, right=0.985, bottom=0.14, top=0.86, wspace=0.28)

# G(f)
ax1.set_facecolor(SURFACE)
ax1.grid(True, color=GRID, lw=0.6)
ax1.set_axisbelow(True)
w1 = np.abs(x) <= XW
ax1.plot(x[w1], Gm[w1], color=SERIES, lw=2)
ax1.axvspan(xl, xr, color=SERIES, alpha=0.08, lw=0)
ax1.hlines(g_half, xl, xr, color=INK2, lw=1, ls=(0, (3, 2)))
ax1.vlines(0, g_half * 0.86, Gm[i_max], color=INK2, lw=1, ls=(0, (3, 2)))
ax1.plot([0], [Gm[i_max]], "o", ms=6, mfc=SURFACE, mec=INK, mew=1.4)
ax1.plot([xl, xr], [g_half, g_half], "o", ms=4.5, mfc=INK2, mec=INK2)
ax1.annotate(r"$f_{res}$ : maximum of $G$", (0, Gm[i_max]), xytext=(0.9 * gamma, Gm[i_max] * 0.99),
             color=INK, fontsize=9, va="center",
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax1.annotate("", (xl, g_half * 0.86), (xr, g_half * 0.86),
             arrowprops=dict(arrowstyle="<->", color=INK, lw=1, shrinkA=0, shrinkB=0))
ax1.text(xr + 0.3 * gamma, g_half * 1.03, "half height", va="center", color=INK2, fontsize=8.5)
ax1.text(xr + 0.3 * gamma, g_half * 0.84, r"$2\Gamma$ : full width", va="center", color=INK, fontsize=9)
ax1.set_xlim(-XW, XW)
ax1.set_ylim(0, Gm[i_max] * 1.1)
ax1.set_xlabel(r"$f - f_{res}$  (Hz)")
ax1.set_ylabel(r"conductance $G$  (mS)")
ax1.set_title("Conductance spectrum", loc="left", color=INK, fontsize=10, fontweight="bold", pad=8)

# locus B vs G over the whole sweep, with the circle fitted on the ±3Γ core as a guide
ax2.set_facecolor(SURFACE)
ax2.grid(True, color=GRID, lw=0.6)
ax2.set_axisbelow(True)
t = np.linspace(0, 2 * np.pi, 400)
ax2.plot((xc + rad * np.cos(t)) * 1e3, (yc + rad * np.sin(t)) * 1e3, color=MUTED, lw=1,
         ls=(0, (4, 3)), label="circle fit, ±3Γ")
ax2.plot(Gm, Bm, color=SERIES, lw=2, label="measured")
ax2.plot([Gm[i_max]], [Bm[i_max]], "o", ms=6, mfc=SURFACE, mec=INK, mew=1.4)
ax2.annotate(r"$f_{res}$", (Gm[i_max], Bm[i_max]), xytext=(-26, 8), textcoords="offset points",
             color=INK, fontsize=9)
ax2.set_aspect("equal", adjustable="datalim")
ax2.set_xlabel(r"conductance $G$  (mS)")
ax2.set_ylabel(r"susceptance $B$  (mS)")
ax2.set_title("Admittance locus", loc="left", color=INK, fontsize=10, fontweight="bold", pad=8)
ax2.legend(loc="center", frameon=False, fontsize=8.5, labelcolor=INK2, handlelength=2.2)

fig.text(0.075, 0.955,
         f"5th overtone in air:  $f_{{res}}$ = {f_res/1e6:.6f} MHz,  $\\Gamma$ = {gamma:.1f} Hz,  "
         f"$D = 2\\Gamma/f_{{res}}$ = {D*1e6:.2f}$\\times10^{{-6}}$,  circle rms {rms*100:.1f} % of the radius",
         color=INK2, fontsize=9, va="center")

out = HERE / "conductance_measured_sweep.svg"
fig.savefig(out, facecolor=SURFACE)
print("written", out)
