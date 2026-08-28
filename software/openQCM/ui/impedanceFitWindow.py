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

# Same fallback as mainWindow: this module is imported at module level there, so a
# hard PyQt5 import would take the whole application down on a PySide2 install.
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError:                                      # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from openQCM.core.constants import Constants
from openQCM.common.logger import Logger as Log
# one list of overtone labels for both live views, so the two windows cannot end
# up naming the same overtone differently
from openQCM.ui.rawDataView import OVERTONE_NAMES
from openQCM.ui.plotMenu import PlotMenu
from openQCM.ui import theme

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


COLUMNS = ("n", "delta [deg]", "masked [%]", "f_s FIT1 [Hz]", "Gamma [Hz]",
           "D [ppm]", "R1 [ohm]", "L1 [mH]", "rms [%r]", "f_s FIT2 [Hz]",
           "dGamma [%]", "df_s [Hz]")


def _overtone_label(idx):
    return (OVERTONE_NAMES[idx] if idx < len(OVERTONE_NAMES)
            else "overtone {}".format(2 * idx + 1))


# Colour of every fitted overlay: the circle, the Lorentzian and the f_s
# marker. Raw Data View paints the measured sweep in the overtone's colour and
# the quantities DERIVED from it in this red, and this window says the same
# thing about the same data, so it says it the same way.
FIT_COLOUR = "#f44336"


class _FitTab(QtWidgets.QWidget):
    """One overtone's three panels: G(f), B(f) beneath it, and the locus.

    One of these per tab. Building them all up front costs three empty plots per
    overtone and buys a tab switch that is instant and keeps each overtone's own
    zoom, which a single shared canvas cannot do.

    Styled from ui/theme.py exactly as Raw Data View is: the two live windows
    show the same sweep, and one of them painting it on a different background
    in a different palette is a difference the reader has to explain away.
    """

    def __init__(self, overtone_index, theme_name, parent=None):
        super(_FitTab, self).__init__(parent)
        palette = theme.PLOT[theme_name]
        colour = Constants.plot_color_multi[
            overtone_index % len(Constants.plot_color_multi)]

        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground(palette["bg"])

        self.pG = self.graph.addPlot(row=0, col=0)
        self.pG.setTitle("conductance G(f) — FIT 2", color=palette["title"])
        self.pG.setLabel('bottom', 'f - f_s', units='Hz', color=palette["title"])
        self.pG.setLabel('left', 'G', units='mS', color=palette["title"])
        self.pG.addLegend(offset=(-10, 10))
        self.curveG = self.pG.plot(
            pen=pg.mkPen(color=colour, width=Constants.plot_line_width),
            name="measured")
        self.curveG2 = self.pG.plot(pen=pg.mkPen(FIT_COLOUR, width=1,
                                                 style=QtCore.Qt.DashLine),
                                    name="FIT 2")

        # B against frequency, under G and sharing its x axis: the two channels
        # are read together, and a defect that is invisible in G (which is EVEN in
        # the phase) shows up here. The reverted roundness-fitted offset was
        # exactly that case - a step of up to 77 % of B's range that left G and the
        # fitted circle looking fine.
        self.pB = self.graph.addPlot(row=1, col=0)
        self.pB.setTitle("susceptance B(f) — FIT 1", color=palette["title"])
        self.pB.setLabel('bottom', 'f - f_s', units='Hz', color=palette["title"])
        self.pB.setLabel('left', 'B', units='mS', color=palette["title"])
        self.pB.setXLink(self.pG)
        self.pB.addLegend(offset=(-10, 10))
        self.zeroB = self.pB.plot(pen=pg.mkPen(palette["axis"], width=1,
                                               style=QtCore.Qt.DotLine))
        self.curveBf = self.pB.plot(
            pen=pg.mkPen(color=colour, width=Constants.plot_line_width),
            name="measured")
        self.curveBfit = self.pB.plot(pen=pg.mkPen(FIT_COLOUR, width=1,
                                                   style=QtCore.Qt.DashLine),
                                      name="FIT 1")

        # The locus spans both rows on the right: it is aspect-locked (a circle has
        # to look like one), so a wide, short box would dilate the G axis and leave
        # the circle a dot in the middle. A roughly square box avoids that.
        self.pC = self.graph.addPlot(row=0, col=1, rowspan=2)
        self.pC.setTitle("admittance plane — FIT 1", color=palette["title"])
        self.pC.setLabel('bottom', 'G', units='mS', color=palette["title"])
        self.pC.setLabel('left', 'B', units='mS', color=palette["title"])
        self.pC.setAspectLocked(True)
        self.pC.addLegend(offset=(-10, 10))
        # the locus is the same measurement as the two curves on the left, so it
        # carries the same overtone colour; only the fitted overlay is red
        self.curveB = self.pC.plot(pen=None, symbol='o', symbolSize=2.5,
                                   symbolPen=None, symbolBrush=colour,
                                   name="measured")
        self.curveFit = self.pC.plot(pen=pg.mkPen(FIT_COLOUR, width=1,
                                                  style=QtCore.Qt.DashLine),
                                     name="FIT 1 circle")
        self.markFs = self.pC.plot(pen=None, symbol='o', symbolSize=11,
                                   symbolPen=pg.mkPen(FIT_COLOUR, width=1.5),
                                   symbolBrush=None, name="f_s on the arc")

        # grid off by default, like every other plot panel in this GUI; it is
        # turned on per plot from the right-click menu
        for plot in self.plots():
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            plot.showGrid(x=False, y=False)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.graph)

    def plots(self):
        return (self.pG, self.pB, self.pC)


class ImpedanceFitWindow(QtWidgets.QWidget):
    """Live BVD circle + Lorentzian fit of the measured admittance."""

    def __init__(self, worker, overtones, theme_name="light", parent=None):
        super(ImpedanceFitWindow, self).__init__(parent)
        self.worker = worker
        self.overtones = int(overtones)
        # Given a parent, this widget would be laid out INSIDE it; the flag is
        # what keeps it a window of its own. Raw Data View does the same, and
        # the parent is the reason both inherit the application style sheet --
        # without it the frame and the table stay in the platform's own colours
        # while the rest of the GUI follows the theme.
        self.theme = theme_name if theme_name in theme.PLOT else "light"
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        # ⚠️ Its own sheet, not the parent's. The application sheet is set on the
        # main window and reaches this one, but its background rules are written
        # for QMainWindow / QDialog / #centralwidget and this is none of them:
        # the text colour arrived and the background did not, which is how the
        # window ended up pale-on-white. Naming it and setting the sheet here
        # covers both cases, the way ChevronComboBox does for its popup.
        self.setObjectName("impedanceFitWindow")
        self.setStyleSheet(theme.qss(theme.palette(self.theme)))
        self._palette = theme.palette(self.theme)
        self._seq = [None] * self.overtones
        self._theta = [None] * self.overtones        # rotation cache, per overtone
        self._last = [None] * self.overtones         # last fit result, per overtone
        self._cost_ms = 0.0
        self._paused = False

        self.setWindowTitle("openQCM NEXT — live admittance fit "
                            "(FIT 1 circle / FIT 2 Lorentzian)")
        self.resize(1180, 760)

        # ------------------------------------------------------------- controls
        self.chkPause = QtWidgets.QCheckBox("freeze")
        self.chkPause.setToolTip("stop refitting; the last fit stays on screen")
        self.chkPause.toggled.connect(self._on_pause)

        self.lblStatus = QtWidgets.QLabel("waiting for data")
        self.lblStatus.setStyleSheet("color: %s;" % self._palette["muted"])

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.chkPause)
        top.addStretch(1)
        top.addWidget(self.lblStatus)

        # ----------------------------------------------------------------- tabs
        # One tab per overtone, as in Raw Data View, so the two live windows are
        # navigated the same way. The overtone is no longer picked from a combo
        # box: the tab bar is the selector.
        self._tabs = QtWidgets.QTabWidget()
        # same right-click menu as the other plot panels, from ui/plotMenu.py:
        # Auto-scale, Reset zoom, pan/select, Show/Hide grid, Export
        self._menu = PlotMenu(self)
        self._panes = []
        for i in range(self.overtones):
            pane = _FitTab(i, self.theme)
            self._tabs.addTab(pane, _overtone_label(i))
            self._panes.append(pane)
            self._menu.attach(pane.plots())
        self._tabs.currentChanged.connect(self._force_redraw)

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
        # the table stays a single overview across all overtones -- that is the
        # point of it -- and clicking a row brings up that overtone's tab
        self.table.clicked.connect(
            lambda i: self._tabs.setCurrentIndex(i.row()))

        note = QtWidgets.QLabel(
            "Gamma is the FULL width at half maximum (the main window reports the "
            "half width; D is the same in both).  dGamma / df_s are FIT 2 minus "
            "FIT 1 — two independent estimators, so their disagreement is the "
            "honest error bar.  delta is the phase offset measured from the fold; "
            "\"no fold\" means the phase never crosses zero (damped load), so the "
            "reading is already the signed phase and no correction applies.  "
            "\"masked\" is how much of the band the AD8302 could not measure "
            "(below its usable ratio). It is the warning, not the rms: past ~20 % "
            "the surviving arc no longer pins FIT 2's background nor FIT 1's "
            "rotation, and the two Gamma estimates diverge while the circle "
            "residual still looks fine. The logged frequency and dissipation are "
            "computed BEFORE the mask, so they are unaffected either way.  "
            "C0 is not shown: the "
            "published spectra have a constant baseline removed, which is exactly "
            "what C0 does.")
        note.setWordWrap(True)
        note.setStyleSheet("color: %s; font-size: 11px;" % self._palette["muted"])

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self._tabs, 1)
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

    # Green / amber / red for a "is this trustworthy" reading. Two sets: the
    # dark table is #37393b, on which the light theme's inks are muddy.
    GRADES = {"light": ("#2e7d32", "#ef6c00", "#c62828"),
              "dark": ("#81c784", "#ffb74d", "#ef9a9a")}

    def _grade(self, value, good, fair):
        ok, warn, bad = self.GRADES[self.theme]
        return ok if value < good else warn if value < fair else bad

    def _current_index(self):
        """The overtone on screen: the current tab, or None if there is none."""
        idx = self._tabs.currentIndex()
        return idx if 0 <= idx < self.overtones else None

    def _force_redraw(self, *_args):
        idx = self._current_index()
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
        try:
            masked = float(self.worker.get_masked_G_buffer(idx))
        except Exception:
            masked = 0.0

        # fs_seed travels with the result: fit2's linear background is written
        # relative to it, so evaluating the curve against anything else shifts it
        self._last[idx] = dict(f=fb, Y=Y, a1=a1, a2=a2, delta=delta,
                               masked=masked, fs_seed=float(fs0))
        self._update_row(idx, a1, a2, delta, masked)
        return True

    # ------------------------------------------------------------------- view
    def _update_row(self, idx, a1, a2, delta, masked):
        vals = ("%d" % (2 * idx + 1),
                "no fold" if delta == 0.0 else "%+.2f" % delta,
                "-" if not masked else "%.0f" % masked,
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
        colour = self._grade(rms, 2.0, 5.0)
        self.table.item(idx, 8).setForeground(QtGui.QColor(colour))
        # and the masked fraction. Thresholds from measurement, not taste: at 20 %
        # dropped the two Gamma estimators already disagree by 20 % (air, 9th
        # overtone, 2026-07-28) because the surviving arc no longer pins FIT 2's
        # background nor FIT 1's rotation. The circle residual keeps looking fine
        # while that happens, so this column is the warning, not the rms.
        mcol = (self._palette["muted"] if not masked
                else self._grade(masked, 10.0, 20.0))
        self.table.item(idx, 2).setForeground(QtGui.QColor(mcol))

    def _draw_selected(self):
        """Draw the visible tab only.

        Every overtone is refitted on every tick because the table shows them all,
        but only one set of curves is ever updated: switching tab redraws from the
        cached fit rather than recomputing it.
        """
        idx = self._current_index()
        if idx is None or self._last[idx] is None:
            return
        pane = self._panes[idx]
        d = self._last[idx]
        f, Y, a1, a2 = d["f"], d["Y"], d["a1"], d["a2"]

        # G(f), x as the detuning from the fitted f_s
        pane.curveG.setData(x=f - a2["fs"], y=Y.real * 1e3)
        ff = np.linspace(f[0], f[-1], 400)
        pane.curveG2.setData(x=ff - a2["fs"],
                             y=fa.fit2_curve(ff, dict(fit2=a2,
                                             fs_seed=d["fs_seed"])) * 1e3)
        # separators, not runs of spaces: the title is rendered as HTML and
        # collapses them
        pane.pG.setTitle("FIT 2 &nbsp;|&nbsp; f_s = %.1f Hz &nbsp;|&nbsp; "
                         "Gamma = %.1f Hz (FWHM) &nbsp;|&nbsp; D = %.2f ppm"
                         % (a2["fs"], a2["gamma"], a2["D"] * 1e6))

        # B(f), with what FIT 1 predicts for it. The model comes from the circle's
        # own geometry - psi = -2*arctan(x) is the position on the arc - so the
        # dashed line is the same fit shown in the locus, read in the B channel.
        pane.curveBf.setData(x=f - a2["fs"], y=Y.imag * 1e3)
        x_det = (ff * ff - a1["fs"] ** 2) / (ff * max(a1["gamma"], 1e-9))
        psi = -2.0 * np.arctan(x_det)
        Bm = (a1["yc"] + a1["r"] * np.sin(psi + a1["theta"])) * 1e3
        pane.curveBfit.setData(x=ff - a2["fs"], y=Bm)
        pane.zeroB.setData(x=[f[0] - a2["fs"], f[-1] - a2["fs"]], y=[0.0, 0.0])
        # B is where a broken reconstruction shows up: report the largest step
        # between adjacent samples as a fraction of B's own range. A continuous
        # trajectory keeps this at a few per cent.
        Bmea = Y.imag * 1e3
        span = float(np.ptp(Bmea)) or 1.0
        jump = 100.0 * float(np.max(np.abs(np.diff(Bmea)))) / span
        pane.pB.setTitle("FIT 1 &nbsp;|&nbsp; B span = %.3f mS &nbsp;|&nbsp; "
                         "largest step between samples = %.1f %% of span"
                         % (span, jump))

        # the locus and the fitted circle
        pane.curveB.setData(x=Y.real * 1e3, y=Y.imag * 1e3)
        th = np.linspace(0.0, 2.0 * np.pi, 181)
        pane.curveFit.setData(x=(a1["xc"] + a1["r"] * np.cos(th)) * 1e3,
                              y=(a1["yc"] + a1["r"] * np.sin(th)) * 1e3)
        # psi = 0 on the arc is the fitted resonance; where it lands makes the
        # rotation the fit had to absorb visible
        pane.markFs.setData(x=[(a1["xc"] + a1["r"] * np.cos(a1["theta"])) * 1e3],
                            y=[(a1["yc"] + a1["r"] * np.sin(a1["theta"])) * 1e3])
        pane.pC.setTitle("FIT 1 &nbsp;|&nbsp; R1 = %.2f ohm &nbsp;|&nbsp; "
                         "rms = %.2f %% of r &nbsp;|&nbsp; theta = %+.1f deg"
                         % (a1["R1"], 100.0 * a1["rms_rel"],
                            np.rad2deg(a1["theta"])))
