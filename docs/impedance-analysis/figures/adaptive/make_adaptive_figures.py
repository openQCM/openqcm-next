"""Figures of the README's "Adaptive conductance sweep" section.

Figures 1-4 are SIMULATED with the board of tests/test_adaptive.py: a Butterworth-Van Dyke crystal
behind the measuring divider whose motional admittance relaxes towards its steady state with the decay
time tau = 1/(2 pi Gamma) while the drive moves, read through the AD8302 transfer functions. The analysis
is this branch's own code: core/adaptive.py and the chain of MultiscanProcess.

Figure 5 is MEASURED: the wide peak-detection sweep of the openQCM Q-1 bench board 13131320 in air,
2026-10-25 (software/openQCM/Calibration_5MHz.txt, not tracked), against the resonances read by the
adaptive sweep in the first row of that run's datalog. If the file is missing, figure 5 is skipped.

    cd docs/impedance-analysis/figures/adaptive && python make_adaptive_figures.py

Environment: the branch's (Python 3.9.12, numpy 1.21, matplotlib 3.5.1).
"""
import contextlib
import io
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOFTWARE = REPO / "software"
sys.path.insert(0, str(SOFTWARE))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openQCM.core.constants import Constants                      # noqa: E402
from openQCM.core import adaptive as A                             # noqa: E402
from tests.test_adaptive import Board, Crystal, process, window   # noqa: E402

WIDE_SWEEP = SOFTWARE / "openQCM" / "Calibration_5MHz.txt"
# The bench run of 2026-10-25: the peaks the wide sweep stored, and f_res of the first datalog row
# (logged_data/2026-10-25_19-13-39_multi_lorentzian_adaptive.csv), F1..F9
STORED = [5_000_500, 14_969_000, 24_941_000, 34_910_000, 44_881_000]
ADAPTIVE = [4_998_339.36, 14_967_132.66, 24_937_397.93, 34_906_522.19, 44_877_374.79]

# ---------------------------------------------------------------- style (as figures/method)
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, GREEN, RED, GREY = "#2a78d6", "#e07b1a", "#2e9e5b", "#c8372d", "#9a9993"
SURFACE = "#ffffff"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "mathtext.fontset": "dejavusans",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.linewidth": 0.8, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "path",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
})


def title(ax, text):
    ax.set_title(text, loc="left", color=INK, fontsize=10, fontweight="bold", pad=8)


def save(fig, name):
    out = HERE / name
    fig.savefig(out, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out.relative_to(REPO))


def raw_g(proc, freq, bm, bp):
    """G (S) of every point, frequency-ordered: the exact inversion on the raw counts (as relocate)."""
    order = np.argsort(freq, kind="stable")
    vm, vp = A.volts(bm, bp)
    reading = proc._phase_raw_V_phase(vp)
    offset, _ = proc._phase_offset_fold(reading)
    g = proc._G_exact(*proc._RX_exact(vm, reading + offset))
    return np.asarray(freq, dtype=float)[order], g[order]


CRYSTAL = Crystal()                       # 5 MHz fundamental in air: fs 4 998 350 Hz, Gamma 41 Hz
FS, GAMMA = CRYSTAL.fs, CRYSTAL.fs / (2 * CRYSTAL.q)
START, STOP, _ = window(round(FS))


# ---------------------------------------------------------------- figure 1: the lag of the 1 Hz sweep
def figure_lag():
    freqs = np.arange(START, STOP + 1, 1.0)
    curves = {}
    for label, lag, order in (("quasi-static", False, freqs), ("swept up, 12 kHz/s", True, freqs),
                              ("swept down, 12 kHz/s", True, freqs[::-1])):
        board = Board(CRYSTAL, lag=lag)
        proc, _ = process(board)
        lines = board.points(order, [0] * len(order), substeps=4)
        counts = np.array([[float(x) for x in s.split(";")] for s in lines])
        f, g = raw_g(proc, order, counts[:, 0], counts[:, 1])
        # f and Gamma through the chain of the full sweep (AdaptiveSweep.locate: SG, spline onto
        # 1 Hz, fold, exact G, maximum, half height), on the points in frequency order
        idx = np.argsort(order, kind="stable")
        with contextlib.redirect_stdout(io.StringIO()):
            published = A.AdaptiveSweep(proc).locate(0, order[idx], counts[idx, 0], counts[idx, 1],
                                                     Constants.SG_WINDOW_SIZE, len(order))
        curves[label] = (f, g, published.fres, published.gamma)
    fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor=SURFACE)
    colours = {"quasi-static": INK, "swept up, 12 kHz/s": RED, "swept down, 12 kHz/s": BLUE}
    _, _, f0, g0 = curves["quasi-static"]
    rows = []
    for label, (f, g, fp, gp) in curves.items():
        rows.append((label, fp - f0, gp / g0 - 1))
        w = np.abs(f - f0) < 7 * GAMMA
        ax.plot(f[w] - f0, g[w] * 1e3, color=colours[label], lw=1.8 if label == "quasi-static" else 1.4,
                ls="-" if label == "quasi-static" else "--" if "up" in label else ":",
                label="%s: $f$ %+.0f Hz, $\\Gamma$ %+.0f %%" % (label, fp - f0, 100 * (gp / g0 - 1))
                if label != "quasi-static" else "quasi-static (reference)")
    ax.set_xlabel(r"$f - f_{res}$ (Hz)")
    ax.set_ylabel("G (mS)")
    title(ax, "The 1 Hz sweep is fast against the crystal's decay time")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left", bbox_to_anchor=(0, -0.17), ncol=1)
    ax.text(0.99, 0.95, "simulated: BVD crystal, $f_s$ = 4.998 MHz, $\\Gamma$ = %.0f Hz,\n"
            "$\\tau = 1/(2\\pi\\Gamma)$ = %.1f ms, 83.4 µs per point ($\\kappa$ = %.1f)"
            % (GAMMA, 1e3 / (2 * np.pi * GAMMA), (1 / 83.4e-6) / (2 * np.pi * GAMMA ** 2)),
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK2)
    save(fig, "fig1_sweep_lag.svg")
    return rows


# ---------------------------------------------------------------- figure 2: one adaptive sweep
def figure_plan():
    plan = A.SweepPlan.around(FS, GAMMA, START, STOP)
    t, f, kind = [], [], []
    clock = 0.0
    names = ["settle", "coarse", "coarse", "lead-in", "fine up", "fine down"]
    n = len(plan.segments)
    labels = names[:1] + ["coarse"] * (n - 4) + names[-3:]
    for i, (a, b, s, dwell) in enumerate(plan.segments):
        for x in plan.segment(i):
            clock += (Constants.ADAPTIVE_POINT_US + dwell) * 1e-6
            t.append(clock * 1e3)
            f.append(x - FS)
            kind.append(labels[i])
    t, f, kind = np.array(t), np.array(f), np.array(kind)
    colours = {"settle": ORANGE, "coarse": GREY, "lead-in": GREEN, "fine up": RED, "fine down": BLUE}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.6), gridspec_kw={"width_ratios": [1, 1.25]},
                                 facecolor=SURFACE)
    for k, c in colours.items():
        w = kind == k
        a1.plot(t[w], f[w] / 1e3, ".", ms=3 if k == "coarse" else 1.5, color=c, label=k)
        a2.plot(t[w], f[w], ".", ms=1.5, color=c)
    settle = plan.segments[0][3] * 1e-3
    a1.annotate("first point waits\n3τ = %.1f ms" % settle, xy=(t[0], f[0] / 1e3), xytext=(60, -10.5),
                fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    wc = kind == "coarse"
    a1.annotate("coarse, 100 Hz, no dwell:\n%d points in %.0f ms" % (wc.sum(), np.ptp(t[wc])),
                xy=(t[wc][-1], 3), xytext=(60, 3.2), fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    a1.set_xlabel("time (ms)")
    a1.set_ylabel(r"$f - f_{res}$ (kHz)")
    title(a1, "One Z command: the whole window")
    a1.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right", markerscale=4)
    w = np.abs(f) < 6 * GAMMA
    a2.set_xlim(t[w].min() - 15, t.max() + 10)
    a2.set_ylim(-6.5 * GAMMA, 6 * GAMMA)
    a2.axhspan(-GAMMA, GAMMA, color=INK, alpha=0.05, lw=0)
    a2.text(t[w].min() - 10, GAMMA * 1.15, r"$\pm\Gamma$", color=INK2, fontsize=8)
    wl = kind == "lead-in"
    a2.annotate("lead-in, 3τ", xy=(t[wl][-1], f[wl][-1]), xytext=(t[wl][-1] + 40, -230), fontsize=8,
                color=GREEN, arrowprops=dict(arrowstyle="-", color=GREEN, lw=0.8))
    a2.set_xlabel("time (ms)")
    a2.set_ylabel(r"$f - f_{res}$ (Hz)")
    title(a2, "The fine zone: up and straight back down")
    up = plan.segments[plan.fine[0]]
    rate = up[2] / ((Constants.ADAPTIVE_POINT_US + up[3]) * 1e-6)
    a2.text(0.98, 0.97, "±%.0f Hz in %d Hz steps, %.0f Hz/s = %.3f · 2π$\\Gamma^2$\n"
            "whole sweep %.0f ms (the full 1 Hz sweep: 1 500 ms)"
            % ((up[1] - up[0]) / 2, up[2], rate, rate / (2 * np.pi * GAMMA ** 2), plan.seconds() * 1e3),
            transform=a2.transAxes, fontsize=8, color=INK2, ha="right", va="top")
    save(fig, "fig2_adaptive_plan.svg")


# ---------------------------------------------------------------- the adaptive sweep, simulated
def adaptive_reading(lag, rate_k=Constants.ADAPTIVE_RATE_K, seed=1):
    """One adaptive sweep of the simulated crystal, planned around the true resonance (as after the
    locating sweep), through core/adaptive.py: the Reading and the plan."""
    board = Board(CRYSTAL, lag=lag, seed=seed)
    proc, _ = process(board)
    sweeper = A.AdaptiveSweep(proc, clock=board.now)
    plan = A.SweepPlan.around(FS, GAMMA, START, STOP, rate_k=rate_k)
    with contextlib.redirect_stdout(io.StringIO()):
        bm, bp, _ = proc._measure(0, plan.command(), len(plan.freqs), 600)
        reading = sweeper.process(0, plan, bm, bp)
    return reading, plan


def figure_passes():
    lagging, _ = adaptive_reading(True)
    still, _ = adaptive_reading(False)
    f_ref, g_ref = still.published.fres, still.published.gamma
    up, down = lagging.passes
    fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor=SURFACE)
    for p, c, ls, name in ((up, RED, "--", "up pass"), (down, BLUE, ":", "down pass")):
        ax.plot(p.fine - f_ref, p.g * 1e3, color=c, lw=1.4, ls=ls,
                label="%s: $f$ %+.2f Hz, $\\Gamma$ %+.2f %%"
                % (name, p.published.fres - f_ref, 100 * (p.published.gamma / g_ref - 1)))
    sp = still.passes[0]
    ax.plot(sp.fine - f_ref, sp.g * 1e3, color=INK, lw=1.8, label="quasi-static (reference)", zorder=1)
    m = lagging.published
    ax.axvline(m.fres - f_ref, color=GREEN, lw=1.2)
    ax.text(m.fres - f_ref + 3, ax.get_ylim()[0] + 0.05 * np.ptp(ax.get_ylim()),
            "mean of the two passes:\n$f$ %+.2f Hz, $\\Gamma$ %+.2f %%"
            % (m.fres - f_ref, 100 * (m.gamma / g_ref - 1)), color=GREEN, fontsize=8.5)
    ax.set_xlim(-4 * GAMMA, 4 * GAMMA)
    ax.set_xlabel(r"$f - f_{res}$ (Hz)")
    ax.set_ylabel("G (mS)")
    title(ax, "The residual lag of the two passes is equal and opposite")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left")
    save(fig, "fig3_two_passes.svg")
    return (up.published.fres - f_ref, down.published.fres - f_ref, m.fres - f_ref, m.gamma / g_ref - 1)


def figure_rate():
    ks = [0.03, 0.06, 0.125, 0.25, 0.5, 1.0, 2.0]
    rows = []
    for k in ks:
        lag, _ = adaptive_reading(True, rate_k=k)
        ref, _ = adaptive_reading(False, rate_k=k)
        up, down = lag.passes
        f0, g0 = ref.published.fres, ref.published.gamma
        rows.append((k, up.published.fres - f0, down.published.fres - f0, lag.published.fres - f0,
                     100 * (up.published.gamma / g0 - 1), 100 * (down.published.gamma / g0 - 1),
                     100 * (lag.published.gamma / g0 - 1), lag.passes and 0))
        print("kappa %.3f  f up %+.2f down %+.2f mean %+.2f Hz   Gamma up %+.2f down %+.2f mean %+.2f %%"
              % rows[-1][:7])
    r = np.array([row[:7] for row in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.4), facecolor=SURFACE)
    for ax, cols, unit, name in ((a1, (1, 2, 3), "Hz", r"$f$ error (Hz)"), (a2, (4, 5, 6), "%", r"$\Gamma$ error (%)")):
        ax.plot(r[:, 0], r[:, cols[0]], "o--", color=RED, ms=3.5, lw=1.2, label="up pass")
        ax.plot(r[:, 0], r[:, cols[1]], "o:", color=BLUE, ms=3.5, lw=1.2, label="down pass")
        ax.plot(r[:, 0], r[:, cols[2]], "o-", color=GREEN, ms=4, lw=1.6, label="mean (published)")
        ax.axvline(Constants.ADAPTIVE_RATE_K, color=MUTED, lw=1, ls=(0, (3, 2)))
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlabel(r"sweep rate $\kappa$ = rate / (2π$\Gamma^2$)")
        ax.set_ylabel(name)
    a1.text(Constants.ADAPTIVE_RATE_K * 1.08, a1.get_ylim()[1] * 0.85, "κ = 0.125\n(chosen)", fontsize=8,
            color=INK2)
    title(a1, "Resonance frequency")
    title(a2, "Half bandwidth")
    a1.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="upper left")
    save(fig, "fig4_rate.svg")
    return rows


# ---------------------------------------------------------------- figure 5: the wide sweep's lag, measured
def figure_peaks():
    if not WIDE_SWEEP.exists():
        print("skipped fig5: %s not found" % WIDE_SWEEP)
        return None
    d = np.loadtxt(WIDE_SWEEP)
    f, m, p = d.T
    # the baselines of CalibrationProcess.baseline_correction: one polynomial over 1-51 MHz
    mc = m - np.polyval(np.polyfit(f, m, Constants.BASELINE_POLY_ORDER), f)
    pc = p - np.polyval(np.polyfit(f, p, Constants.BASELINE_POLY_ORDER), f)
    fig, axes = plt.subplots(2, 5, figsize=(10.4, 4.4), sharex=True, facecolor=SURFACE,
                             gridspec_kw={"hspace": 0.12, "wspace": 0.35})
    rows = []
    for j, (fa, fs) in enumerate(zip(ADAPTIVE, STORED)):
        w = np.abs(f - fa) < 12_000
        x = (f[w] - fa) / 1e3
        for row, y, unit in ((0, mc[w], "dB"), (1, pc[w], "deg")):
            ax = axes[row, j]
            ax.plot(x, y, ".-", color=INK2, lw=0.8, ms=2.5)
            ax.axvline(0, color=GREEN, lw=1.4)
            ax.axvline((fs - fa) / 1e3, color=RED, lw=1.2, ls="--")
            if j == 0:
                ax.set_ylabel("magnitude (%s)" % unit if row == 0 else "phase (%s)" % unit)
        jp = int(np.argmax(pc[w]))
        rows.append(((fs - fa), f[w][jp] - fa))
        axes[0, j].set_title("F%d: stored %+.1f kHz" % (2 * j + 1, (fs - fa) / 1e3), loc="left",
                             fontsize=9, color=INK, fontweight="bold")
        axes[1, j].set_xlabel(r"$f - f_{res}$ (kHz)")
    axes[0, 0].legend(handles=[plt.Line2D([], [], color=GREEN, lw=1.4, label="$f_{res}$, adaptive sweep"),
                               plt.Line2D([], [], color=RED, lw=1.2, ls="--",
                                          label="magnitude peak stored by the wide sweep (500 Hz steps)")],
                      frameon=False, fontsize=7.5, labelcolor=INK2, loc="lower left",
                      bbox_to_anchor=(0, 1.12), ncol=3)
    save(fig, "fig5_peak_detection_lag.svg")
    return rows


if __name__ == "__main__":
    print("fig1 (f offset Hz, Gamma relative):", figure_lag())
    figure_plan()
    print("fig3 (up, down, mean Hz; Gamma rel):", figure_passes())
    figure_rate()
    print("fig5 (stored - adaptive, phase max - adaptive) Hz:", figure_peaks())
