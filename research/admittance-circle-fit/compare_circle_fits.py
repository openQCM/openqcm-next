#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run both circle estimators on the same array and print the difference.

The GUI's impedance panel and the live admittance-fit window read the same three
buffers and draw two different circles. This script reproduces both on archived
sweeps so the difference can be measured instead of argued about.

    cd software
    python3 ../research/admittance-circle-fit/compare_circle_fits.py <dir-with-g1.txt...>

<dir> holds the g<n>.txt written by the sweep dump. COPY THEM OUT OF THE REPO
FIRST: openQCM/sweep_data/ is overwritten by every acquisition.

Qt is needed only because the GUI estimator is a static method on MainWindow;
nothing is shown. Run it headless with QT_QPA_PLATFORM=offscreen, and hold the
QApplication in a name or the process segfaults with no output at all.
"""
import importlib.util
import os
import sys

import numpy as np
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])       # must stay referenced

# run by path, sys.path[0] is this file's directory, not software/
sys.path.insert(0, os.getcwd())

from openQCM.ui.mainWindow import MainWindow             # noqa: E402
from openQCM.core.constants import Constants             # noqa: E402

OVERTONES = (1, 3, 5, 7, 9)


def _load_fit_module():
    """Import the offline reference the same way the live window does."""
    path = os.path.join("openQCM", "sweep_data", "fit_admittance.py")
    spec = importlib.util.spec_from_file_location("fa", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare(sweep_dir):
    fa = _load_fit_module()
    rows = []
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

        # (a) the fit window: decimate, then fit the WHOLE band, geometrically
        step = max(1, len(f_b) // Constants.IMPEDANCE_FIT_POINTS)
        f_w, Y_w = f_b[::step], Y_b[::step]
        win = fa.fit1_circle(f_w, Y_w, np.ones(len(f_w), bool))

        # (b) the GUI panel: decimate to ~250, keep the core, Taubin + trimming
        step2 = max(1, len(f_b) // 250)
        f_p = f_b[::step2]
        g_p, b_p = Y_b.real[::step2] * 1e3, Y_b.imag[::step2] * 1e3   # mS
        core = (np.abs(f_p - fs_seed)
                <= Constants.IMPEDANCE_PANEL_FIT_GAMMA * hw)
        gui = MainWindow._fit_circle_taubin(g_p[core], b_p[core])

        rows.append((n, win["xc"] * 1e3, win["yc"] * 1e3, win["r"] * 1e3,
                     win["R1"], gui[0], gui[1], gui[2], 1e3 / (2 * gui[2]),
                     len(f_w), int(core.sum())))
    return rows


def main():
    sweep_dir = sys.argv[1] if len(sys.argv) > 1 else "openQCM/sweep_data"
    rows = compare(sweep_dir)
    if not rows:
        print("no g<n>.txt found in", sweep_dir)
        return 1
    head = ("n", "r_win", "r_gui", "dr %", "R1_win", "R1_gui", "dR1 %",
            "n_win", "n_core")
    print("  ".join("%8s" % h for h in head))
    for (n, wx, wy, wr, wR1, gx, gy, gr, gR1, nw, nc) in rows:
        print("  ".join("%8s" % v for v in (
            n, "%.3f" % wr, "%.3f" % gr, "%+.1f" % (100 * (gr - wr) / wr),
            "%.2f" % wR1, "%.2f" % gR1, "%+.1f" % (100 * (gR1 - wR1) / wR1),
            nw, nc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
