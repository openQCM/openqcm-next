#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VER 0.1.6G — live admittance-fit window.

Opens from Tools > "Impedance Fit (live)" and runs the SAME two fits as the
offline reference `sweep_data/fit_admittance.py`, on the spectra the acquisition
is already publishing:

  FIT 1  Butterworth-Van Dyke circle on the complex admittance, with f_s and
         Gamma read off the arc geometry by linear least squares
  FIT 2  Levenberg-Marquardt Lorentzian on G(f), linear background free

The module is imported from its file path rather than as a package, on purpose:
the offline script must stay standalone (it is run straight from the sweep_data
directory on archived g<n>.txt), and importing the very same file is what
guarantees the live numbers and the offline numbers cannot drift apart.

WHAT THIS WINDOW COSTS, and why it is built the way it is:
  * It owns its own timer, started on show and stopped on hide, so a closed
    window costs exactly nothing.
  * It refits only when the per-overtone revision counter moves - once per sweep,
    not once per repaint.
  * The rotation search reuses the previous sweep's angle as a bracket instead of
    re-running the 181-point grid. Measured on five overtones of a real air sweep:
    123 ms for the first fit, 13 ms for every one after it, against a sweep that
    takes seconds. A tick with no new sweep costs 2 microseconds.

WHAT THE NUMBERS MEAN HERE, one caveat. The published spectra have a constant
baseline removed (mean of the first 100 samples) before shipping, which
TRANSLATES the admittance circle. f_s, Gamma, D and R1 are unaffected - a
translation is exactly what C0 does, and the circle fit separates it - but the
fitted offset is no longer the physical omega*C0, so C0 is not reported. Run the
offline script on g<n>.txt when C0 is what you are after.
"""

import importlib.util
import os
import sys
import time

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from openQCM.core.constants import Constants
from openQCM.common.logger import Logger as Log

TAG = "[ImpedanceFit]"


# ---------------------------------------------------------------------------
# import the offline reference module by path (see the note in the docstring)
def _load_fit_module():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(here), "sweep_data", "fit_admittance.py")
    spec = importlib.util.spec_from_file_location("openqcm_fit_admittance", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    fa = _load_fit_module()
except Exception as e:                                   # pragma: no cover
    fa = None
    print(TAG, "Warning: offline fit module not available:", e)


COLUMNS = ("n", "delta [deg]", "f_s FIT1 [Hz]", "Gamma [Hz]", "D [ppm]",
           "R1 [ohm]", "L1 [mH]", "rms [%r]", "f_s FIT2 [Hz]",
           "dGamma [%]", "df_s [Hz]")


class ImpedanceFitWindow(QtWidgets.QWidget):
    """Live BVD circle + Lorentzian fit of the measured admittance."""

    def __init__(self, worker, overtones, parent=None):
        super(ImpedanceFitWindow, self).__init__(parent)
        self.worker = worker
        self.overtones = int(overtones)
        self._seq = [None] * self.overtones
        self._theta = [None] * self.overtones        # rotation cache, per overtone
        self._last = [None] * self.overtones         # last fit result, per overtone
        self._cost_ms = 0.0
        self._paused = False

        self.setWindowTitle("openQCM NEXT — live admittance fit "
                            "(FIT 1 circle / FIT 2 Lorentzian)")
        self.resize(1180, 760)

        # ------------------------------------------------------------- controls
        self.cboOvertone = QtWidgets.QComboBox()
        for i in range(self.overtones):
            self.cboOvertone.addItem("overtone %d  (n = %d)" % (i, 2 * i + 1), i)
        self.cboOvertone.currentIndexChanged.connect(self._force_redraw)

        self.chkPause = QtWidgets.QCheckBox("freeze")
        self.chkPause.setToolTip("stop refitting; the last fit stays on screen")
        self.chkPause.toggled.connect(self._on_pause)

        self.lblStatus = QtWidgets.QLabel("waiting for data")
        self.lblStatus.setStyleSheet("color: #888;")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("plot:"))
        top.addWidget(self.cboOvertone)
        top.addWidget(self.chkPause)
        top.addStretch(1)
        top.addWidget(self.lblStatus)

        # ---------------------------------------------------------------- plots
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground(Constants.plot_background_color)

        self.pG = self.graph.addPlot(row=0, col=0, title="conductance G(f) — FIT 2")
        self.pG.showGrid(x=True, y=True, alpha=0.2)
        self.pG.setLabel('bottom', 'f - f_s', units='Hz')
        self.pG.setLabel('left', 'G', units='mS')
        self.pG.addLegend(offset=(-10, 10))
        self.curveG = self.pG.plot(pen=pg.mkPen('#1f77b4', width=1),
                                   name="measured")
        self.curveG2 = self.pG.plot(pen=pg.mkPen('#d62728', width=1,
                                                 style=QtCore.Qt.DashLine),
                                    name="FIT 2")

        # Side by side, not stacked: pC is aspect-locked (a circle has to look
        # like one), so in a wide, short box Qt dilates the G axis and the circle
        # ends up a dot in the middle. Two roughly square boxes avoid that.
        self.pC = self.graph.addPlot(row=0, col=1,
                                     title="admittance plane — FIT 1")
        self.pC.showGrid(x=True, y=True, alpha=0.2)
        self.pC.setLabel('bottom', 'G', units='mS')
        self.pC.setLabel('left', 'B', units='mS')
        self.pC.setAspectLocked(True)
        self.pC.addLegend(offset=(-10, 10))
        self.curveB = self.pC.plot(pen=None, symbol='o', symbolSize=2.5,
                                   symbolPen=None, symbolBrush='#1f77b4',
                                   name="measured")
        self.curveFit = self.pC.plot(pen=pg.mkPen('#d62728', width=1,
                                                  style=QtCore.Qt.DashLine),
                                     name="FIT 1 circle")
        self.markFs = self.pC.plot(pen=None, symbol='o', symbolSize=11,
                                   symbolPen=pg.mkPen('#d62728', width=1.5),
                                   symbolBrush=None, name="f_s on the arc")

        # ---------------------------------------------------------------- table
        self.table = QtWidgets.QTableWidget(self.overtones, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        self.table.setMaximumHeight(28 * (self.overtones + 1) + 8)
        mono = QtGui.QFont("Menlo" if sys.platform == "darwin" else
                           "Consolas" if sys.platform.startswith("win") else
                           "Monospace")
        mono.setStyleHint(QtGui.QFont.TypeWriter)
        mono.setPointSize(10)
        self.table.setFont(mono)
        for row in range(self.overtones):
            for col in range(len(COLUMNS)):
                it = QtWidgets.QTableWidgetItem("-")
                it.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.table.setItem(row, col, it)
            self.table.item(row, 0).setText(str(2 * row + 1))
        self.table.clicked.connect(
            lambda i: self.cboOvertone.setCurrentIndex(i.row()))

        note = QtWidgets.QLabel(
            "Gamma is the FULL width at half maximum (the main window reports the "
            "half width; D is the same in both).  dGamma / df_s are FIT 2 minus "
            "FIT 1 — two independent estimators, so their disagreement is the "
            "honest error bar.  delta is the measured phase offset; 0.00 means "
            "the estimate was rejected on this sweep.  C0 is not shown: the "
            "published spectra have a constant baseline removed, which is exactly "
            "what C0 does.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 11px;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.graph, 1)
        lay.addWidget(self.table)
        lay.addWidget(note)

        # ---------------------------------------------------------------- timer
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)

        if fa is None:
            self.lblStatus.setText("offline fit module missing — cannot fit")

    # ----------------------------------------------------------------- events
    def showEvent(self, event):
        super(ImpedanceFitWindow, self).showEvent(event)
        if fa is not None and not self._paused:
            self._timer.start(Constants.IMPEDANCE_FIT_UPDATE_MS)

    def hideEvent(self, event):
        # a window nobody is looking at must cost nothing
        self._timer.stop()
        super(ImpedanceFitWindow, self).hideEvent(event)

    def closeEvent(self, event):
        self._timer.stop()
        event.accept()

    def _on_pause(self, paused):
        self._paused = bool(paused)
        if self._paused:
            self._timer.stop()
        elif self.isVisible():
            self._timer.start(Constants.IMPEDANCE_FIT_UPDATE_MS)

    def _force_redraw(self):
        idx = self.cboOvertone.currentData()
        if idx is not None:
            self._seq[idx] = None            # make the next tick refit this one
        self._draw_selected()

    # ------------------------------------------------------------------- work
    def _tick(self):
        """Refit every overtone whose spectrum changed, then redraw the selected
        one. Wrapped whole: a diagnostic view must never disturb an acquisition.
        """
        if self.worker is None:
            return
        try:
            t0 = time.perf_counter()
            done = 0
            for idx in range(self.overtones):
                try:
                    seq = self.worker.get_GB_seq(idx)
                except Exception:
                    continue
                if seq == self._seq[idx]:
                    continue
                self._seq[idx] = seq
                if self._fit_one(idx):
                    done += 1
            if done:
                self._cost_ms = 1e3 * (time.perf_counter() - t0)
                self._draw_selected()
                self.lblStatus.setText(
                    "%d overtone(s) refitted in %.0f ms" % (done, self._cost_ms))
        except Exception as e:
            self._timer.stop()
            print(TAG, "Warning: live fit stopped:", e)
            Log.i(TAG, "Warning: live fit stopped: %s" % e)
            self.lblStatus.setText("stopped: %s" % e)

    def _fit_one(self, idx):
        g = self.worker.get_G_exact_buffer(idx)
        b = self.worker.get_B_exact_buffer(idx)
        f = self.worker.get_F_G_values_buffer(idx)
        if not (isinstance(g, np.ndarray) and isinstance(b, np.ndarray)
                and isinstance(f, np.ndarray)):
            return False
        if len(g) < 32 or len(b) != len(g) or len(f) != len(g):
            return False

        # The producer already clipped to +-IMPEDANCE_PANEL_BAND_GAMMA half
        # widths, which is the offline default band, so the whole array is the
        # fit window. Decimate only to bound the cost.
        step = max(1, len(f) // Constants.IMPEDANCE_FIT_POINTS)
        fb = np.asarray(f[::step], dtype=float)
        Y = np.asarray(g[::step], dtype=float) / 1e3 \
            + 1j * np.asarray(b[::step], dtype=float) / 1e3      # mS -> S
        keep = np.isfinite(fb) & np.isfinite(Y.real) & np.isfinite(Y.imag)
        if keep.sum() < 32:
            return False
        fb, Y = fb[keep], Y[keep]
        all_true = np.ones(len(fb), dtype=bool)

        try:
            a1 = fa.fit1_circle(fb, Y, all_true, theta0=self._theta[idx])
            self._theta[idx] = a1["theta"]
            fs0, hw = fa._seed(fb, Y.real, all_true)
            a2 = fa.fit2_lorentzian(fb, Y.real, all_true, fs0, 2.0 * hw)
        except Exception as e:
            # a single bad sweep must not kill the window or poison the cache
            self._theta[idx] = None
            print(TAG, "Warning: fit failed on overtone %d: %s" % (idx, e))
            return False

        try:
            delta = float(self.worker.get_delta_G_buffer(idx))
        except Exception:
            delta = float('nan')

        # fs_seed travels with the result: fit2's linear background is written
        # relative to it, so evaluating the curve against anything else shifts it
        self._last[idx] = dict(f=fb, Y=Y, a1=a1, a2=a2, delta=delta,
                               fs_seed=float(fs0))
        self._update_row(idx, a1, a2, delta)
        return True

    # ------------------------------------------------------------------- view
    def _update_row(self, idx, a1, a2, delta):
        vals = ("%d" % (2 * idx + 1),
                "rejected" if delta == 0.0 else "%+.2f" % delta,
                "%.2f" % a1["fs"],
                "%.2f" % a1["gamma"],
                "%.2f" % (a1["D"] * 1e6),
                "%.2f" % a1["R1"],
                "%.2f" % (a1["L1"] * 1e3),
                "%.2f" % (100.0 * a1["rms_rel"]),
                "%.2f" % a2["fs"],
                "%+.1f" % (100.0 * (a2["gamma"] - a1["gamma"]) / a1["gamma"]
                           if a1["gamma"] else float('nan')),
                "%+.1f" % (a2["fs"] - a1["fs"]))
        for col, v in enumerate(vals):
            self.table.item(idx, col).setText(v)
        # colour the circle residual: it is the single best "do I trust this"
        # indicator on screen. 2 % is the clean-air figure, 5 % is the
        # acceptance threshold the offset estimator itself uses.
        rms = 100.0 * a1["rms_rel"]
        colour = ("#2e7d32" if rms < 2.0 else
                  "#ef6c00" if rms < 5.0 else "#c62828")
        self.table.item(idx, 7).setForeground(QtGui.QColor(colour))

    def _draw_selected(self):
        idx = self.cboOvertone.currentData()
        if idx is None or self._last[idx] is None:
            return
        d = self._last[idx]
        f, Y, a1, a2 = d["f"], d["Y"], d["a1"], d["a2"]

        # G(f), x as the detuning from the fitted f_s
        self.curveG.setData(x=f - a2["fs"], y=Y.real * 1e3)
        ff = np.linspace(f[0], f[-1], 400)
        self.curveG2.setData(x=ff - a2["fs"],
                             y=fa.fit2_curve(ff, dict(fit2=a2,
                                             fs_seed=d["fs_seed"])) * 1e3)
        # separators, not runs of spaces: the title is rendered as HTML and
        # collapses them
        self.pG.setTitle("FIT 2 &nbsp;|&nbsp; f_s = %.1f Hz &nbsp;|&nbsp; "
                         "Gamma = %.1f Hz (FWHM) &nbsp;|&nbsp; D = %.2f ppm"
                         % (a2["fs"], a2["gamma"], a2["D"] * 1e6))

        # the locus and the fitted circle
        self.curveB.setData(x=Y.real * 1e3, y=Y.imag * 1e3)
        th = np.linspace(0.0, 2.0 * np.pi, 181)
        self.curveFit.setData(x=(a1["xc"] + a1["r"] * np.cos(th)) * 1e3,
                              y=(a1["yc"] + a1["r"] * np.sin(th)) * 1e3)
        # psi = 0 on the arc is the fitted resonance; where it lands makes the
        # rotation the fit had to absorb visible
        self.markFs.setData(x=[(a1["xc"] + a1["r"] * np.cos(a1["theta"])) * 1e3],
                            y=[(a1["yc"] + a1["r"] * np.sin(a1["theta"])) * 1e3])
        self.pC.setTitle("FIT 1 &nbsp;|&nbsp; R1 = %.2f ohm &nbsp;|&nbsp; "
                         "rms = %.2f %% of r &nbsp;|&nbsp; theta = %+.1f deg"
                         % (a1["R1"], 100.0 * a1["rms_rel"],
                            np.rad2deg(a1["theta"])))
