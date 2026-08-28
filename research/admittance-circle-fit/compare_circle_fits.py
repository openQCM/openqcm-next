#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run both circle estimators on the same array, print the difference, plot it.

The GUI's impedance panel and the live admittance-fit window read the same three
buffers and draw two different circles. This script reproduces both on archived
sweeps so the difference can be measured instead of argued about, and draws the
four figures of research/admittance-circle-fit/ from the data it just measured.

    cd software
    python3 ../research/admittance-circle-fit/compare_circle_fits.py openQCM/sweep_data

The first argument is a directory of g<n>.txt written by the sweep dump, and
defaults to openQCM/sweep_data. Those are overwritten by every acquisition, so
pass a copy when the numbers have to stay put:

    cp openQCM/sweep_data/g*.txt ~/qcm_sweeps/air_2026-08-28/

Options:
    --overtone N   which overtone the locus and conductance panels show (default 1)
    --no-plot      table only
    --save DIR     write the figures to DIR instead of opening a window

The window is skipped automatically under QT_QPA_PLATFORM=offscreen, so the same
command line still works headless.

Qt is needed even for the table, because the GUI estimator is a static method on
MainWindow. Two traps, both already paid for: hold the QApplication in a name or
the process segfaults with no output at all, and import pyqtgraph before creating
it or it prints a graphics-system warning on every run.
"""
import argparse
import importlib.util
import os
import sys

import numpy as np
import pyqtgraph                                         # before QApplication
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])       # must stay referenced

# run by path, sys.path[0] is this file's directory, not software/
sys.path.insert(0, os.getcwd())

from openQCM.ui.mainWindow import MainWindow             # noqa: E402
from openQCM.core.constants import Constants             # noqa: E402

OVERTONES = (1, 3, 5, 7, 9)

# same three colours as the figures in the document
BLUE, RED, PURPLE, GREY, INK = "#008EC0", "#f44336", "#7b1fa2", "#bdbdbd", "#212121"


def _geometric(fa, x, y):
    """Orthogonal-distance circle fit, Taubin-seeded: what the fit window runs."""
    p, _cov, _d = fa.geometric_circle(x, y, list(fa.taubin_circle(x, y)),
                                      huber=None)
    return float(p[0]), float(p[1]), abs(float(p[2]))


def _load_fit_module():
    """Import the offline reference the same way the live window does."""
    path = os.path.join("openQCM", "sweep_data", "fit_admittance.py")
    spec = importlib.util.spec_from_file_location("fa", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def measure(sweep_dir):
    """Both estimators, plus the two mixed cases, on every overtone found.

    Returns one dict per overtone holding the decimated arrays and the four
    circles, so the caller can print or draw without redoing the work.

    The four fits are the 2x2 of domain against estimator. Only two of them run
    in the application - "geo_band" is the fit window and "tau_core" is the
    panel - but the mixed pair is what separates the cause: the difference
    between the two views is dominated by the domain, not by the algorithm.
    """
    fa = _load_fit_module()
    out = []
    for n in OVERTONES:
        path = os.path.join(sweep_dir, "g%d.txt" % n)
        if not os.path.exists(path):
            continue
        d = np.loadtxt(path)
        f, v_mag, v_phs = d[:, 0], d[:, 1], d[:, 2]
        Y, _delta, _rms = fa.admittance(f, v_mag, v_phs, offset="fold")

        # what MultiscanProcess publishes: masked, then clipped to +-3 half widths
        mask = fa.ratio_dB(v_mag) > fa.RATIO_DB_FLOOR
        if mask.sum() < 100:
            mask = np.ones_like(f, bool)
        fs_seed, hw = fa._seed(f, Y.real, mask)
        band = mask & (np.abs(f - fs_seed)
                       <= Constants.IMPEDANCE_PANEL_BAND_GAMMA * hw)
        f_b, Y_b = f[band], Y[band]

        # the fit window: decimate, then fit the WHOLE band, geometrically
        step = max(1, len(f_b) // Constants.IMPEDANCE_FIT_POINTS)
        f_w, Y_w = f_b[::step], Y_b[::step]
        win = fa.fit1_circle(f_w, Y_w, np.ones(len(f_w), bool))
        geo_band = (win["xc"] * 1e3, win["yc"] * 1e3, win["r"] * 1e3)

        # the GUI panel: decimate to ~250, keep the core, Taubin + trimming
        step2 = max(1, len(f_b) // 250)
        f_p = f_b[::step2]
        g_p, b_p = Y_b.real[::step2] * 1e3, Y_b.imag[::step2] * 1e3   # mS
        core = (np.abs(f_p - fs_seed)
                <= Constants.IMPEDANCE_PANEL_FIT_GAMMA * hw)

        res = np.hypot(g_p - geo_band[0], b_p - geo_band[1]) - geo_band[2]
        out.append(dict(
            n=n, f=f_p, g=g_p, b=b_p, core=core, fs=fs_seed, hw=hw,
            geo_band=geo_band,
            geo_core=_geometric(fa, g_p[core], b_p[core]),
            tau_band=MainWindow._fit_circle_taubin(g_p, b_p),
            tau_core=MainWindow._fit_circle_taubin(g_p[core], b_p[core]),
            n_band=len(f_w), n_core=int(core.sum()),
            residual=res,
            rms_rel=100.0 * float(np.sqrt(np.mean(res ** 2))) / geo_band[2]))
    return out


def print_table(rows):
    head = ("n", "r_win", "r_gui", "dr %", "R1_win", "R1_gui", "dR1 %",
            "n_win", "n_core")
    print("  ".join("%8s" % h for h in head))
    for r in rows:
        wr, gr = r["geo_band"][2], r["tau_core"][2]
        print("  ".join("%8s" % v for v in (
            r["n"], "%.3f" % wr, "%.3f" % gr, "%+.1f" % (100 * (gr - wr) / wr),
            "%.2f" % (1e3 / (2 * wr)), "%.2f" % (1e3 / (2 * gr)),
            "%+.1f" % (100 * (wr / gr - 1)), r["n_band"], r["n_core"])))


def plot(rows, overtone, save_dir=None):
    """The four figures of the analysis, in one window.

    Top row is the overtone asked for; the bottom row is all of them, which is
    where the two claims of the document live: the residual is systematic, and
    the disagreement scales with it.
    """
    import matplotlib
    if save_dir:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sel = next((r for r in rows if r["n"] == overtone), rows[0])
    g, b, core = sel["g"], sel["b"], sel["core"]
    th = np.linspace(0, 2 * np.pi, 361)

    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    fig.canvas.manager.set_window_title(
        "openQCM NEXT - two circle fits on one admittance locus")

    # (0,0) the locus and the three circles
    a = ax[0][0]
    a.plot(g, b, ".", ms=2.2, color=GREY, label="locus, band +-3 HW")
    a.plot(g[core], b[core], ".", ms=3.0, color=INK, label="core, +-1 HW")
    for key, st, col, lab in (("geo_band", "-", BLUE, "geometric, band (fit window)"),
                              ("tau_core", "--", RED, "Taubin + trim, core (panel)"),
                              ("geo_core", ":", PURPLE, "geometric, core")):
        xc, yc, r = sel[key]
        a.plot(xc + r * np.cos(th), yc + r * np.sin(th), st, lw=1.1, color=col,
               label=lab)
    a.set_aspect("equal")
    a.set_title("n = %d: admittance locus" % sel["n"], fontsize=9)
    a.set_xlabel("G (mS)"); a.set_ylabel("B (mS)")
    a.legend(frameon=False, fontsize=7)

    # (0,1) which points each estimator sees
    a = ax[0][1]
    a.plot(sel["f"] - sel["fs"], g, "-", lw=1.0, color=INK)
    a.axvspan(-3 * sel["hw"], 3 * sel["hw"], color=BLUE, alpha=0.12, lw=0)
    a.axvspan(-sel["hw"], sel["hw"], color=RED, alpha=0.16, lw=0)
    a.set_title("n = %d: the two fitting domains" % sel["n"], fontsize=9)
    a.set_xlabel("f - f_s (Hz)"); a.set_ylabel("G (mS)")

    # (1,0) the residual against the best-fit circle, every overtone
    a = ax[1][0]
    for r in rows:
        a.plot((r["f"] - r["fs"]) / r["hw"], 100 * r["residual"] / r["geo_band"][2],
               "-", lw=1.0, label="n = %d (rms %.1f %%)" % (r["n"], r["rms_rel"]))
    a.axhline(0, lw=0.5, color=INK)
    for v in (-1, 1):
        a.axvline(v, lw=0.5, ls=":", color=RED)
    a.set_title("radial residual: the locus is not a circle", fontsize=9)
    a.set_xlabel("(f - f_s) / half width"); a.set_ylabel("residual (% of r)")
    a.legend(frameon=False, fontsize=7)

    # (1,1) domain against estimator
    a = ax[1][1]
    w = 0.27
    x = np.arange(len(rows))
    for k, (key, col, lab) in enumerate(
            (("tau_band", "#90a4ae", "estimator alone: Taubin + trim, band"),
             ("geo_core", PURPLE, "domain alone: geometric, core"),
             ("tau_core", RED, "both: the panel"))):
        v = [100 * (r[key][2] - r["geo_band"][2]) / r["geo_band"][2] for r in rows]
        a.bar(x + (k - 1) * w, v, width=w, color=col, label=lab)
    a.axhline(0, lw=0.6, color=INK)
    a.set_xticks(x); a.set_xticklabels([str(r["n"]) for r in rows])
    a.set_title("what the difference is made of", fontsize=9)
    a.set_xlabel("overtone n"); a.set_ylabel("radius vs reference (%)")
    a.legend(frameon=False, fontsize=7, loc="lower left")

    fig.tight_layout()
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "compare_circle_fits.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print("figures written to", path)
    else:
        plt.show()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sweep_dir", nargs="?", default="openQCM/sweep_data")
    ap.add_argument("--overtone", type=int, default=1,
                    help="overtone shown in the top row (default 1)")
    ap.add_argument("--no-plot", action="store_true", help="table only")
    ap.add_argument("--save", metavar="DIR",
                    help="write the figures there instead of opening a window")
    args = ap.parse_args()

    rows = measure(args.sweep_dir)
    if not rows:
        print("no g<n>.txt found in", args.sweep_dir)
        return 1
    print_table(rows)

    # a window is meaningless under the offscreen platform, and asking for one
    # there is how a headless run ends up hanging instead of finishing
    headless = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    if args.no_plot or (headless and not args.save):
        if headless and not args.no_plot:
            print("\n(QT_QPA_PLATFORM=offscreen: no window. "
                  "Drop it to see the figures, or pass --save DIR.)")
        return 0
    plot(rows, args.overtone, args.save)
    return 0


if __name__ == "__main__":
    sys.exit(main())
