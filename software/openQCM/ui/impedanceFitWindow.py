#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VER 0.1.6G — live fit window: what the acquisition publishes, and nothing else.

Opens from Tools > "Impedance Fit (live)". One tab per overtone with, on the left,
the exact conductance G(f) the process shipped, the phase-shifted Lorentzian the
process FITTED to it (core/lorentzian.py) drawn from the parameters it shipped,
the published f_res, the maximum of G that is the fallback, the ±band·Γ window the
fit ran on, the residual, and the susceptance B(f) beneath; on the right the
admittance locus B vs G. A table with the numbers of every overtone: which
estimator was published, f_res, Γ, D, φ, rms, the fallback pair, the phase offset
δ the chain applied.

B and the locus are the measurement as shipped. One drawing aid is added on the
locus, and it is the only thing in this window that is not a shipped number: a
circle. In an EXPERIMENTAL run it is the circle of the PUBLISHED fit — the rotated
Lorentzian is a circle in the complex plane, of diameter G_max centred at
offset + (G_max/2)·e^{jφ} — with its one unfitted freedom, the vertical offset,
anchored on the measured B at f_res (the process fits G alone, so B_off was never
estimated). In a STANDARD run no model exists, so the circle is fitted HERE, in
closed form, on the ±Γ core of the measured locus, and the title says so: nothing
is ever published from it, it is there to show whether the locus closes. ⚠️ Their axes are not the same
frame — G travels with a constant baseline removed (the mean of its first 100
samples, which the Data View's half-height marker is defined on) and B travels as
the chain computed it, so the locus is the admittance circle translated along G.
Its shape, its closure and where the published f_res falls on it are all
unaffected; an absolute G read off it is not meaningful.

THE RULE (Marco, 2026-09-16): what this window shows is what the process used to
produce the logged numbers. So this window fits NOTHING. Every curve is either a
shipped array or the shipped model evaluated on the shipped axis; every number in
the table came out of the process. If the producer shipped no fit (an older
process, or Constants.IMPEDANCE_ESTIMATOR = "argmax") the window shows the
measured G with the maximum marked and says so.

What went away with the rewrite of 2026-09-16, on purpose: the BVD circle fit
(FIT 1), the symmetric Lorentzian refitted in the GUI (FIT 2), R1, L1, the
masked-percent column, and the import of the offline module
sweep_data/fit_admittance.py — the release tree no longer needs sweep_data/ for
any live view. B(f) and the locus came back on Marco's ask the same evening, as
measured curves with no fitted overlay. The research behind those is in research/air-ipa-water-1920-2026-09-11/.

Costs: its own timer, started on show and stopped on hide, so a closed window
costs nothing; per-overtone revision counter, so a tick with no new sweep does
nothing; the drawn curve is decimated to a few hundred points.
"""

import sys

import numpy as np

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError:                                      # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from openQCM.core.constants import Constants
from openQCM.core.lorentzian import rotated_lorentzian
from openQCM.common.logger import Logger as Log
from openQCM.ui.rawDataView import OVERTONE_NAMES
from openQCM.ui.plotMenu import PlotMenu
from openQCM.ui import theme
from openQCM.ui import admittanceCircle as circ

TAG = "[ImpedanceFit]"

COLUMNS = ("n", "published by", "f_res [Hz]", "Gamma [Hz]", "D [ppm]", "phi [deg]",
           "rms [% range]", "f argmax [Hz]", "Gamma half height [Hz]", "delta [deg]")

# Colour of everything DERIVED from the measurement (the fit, the published
# marker): Raw Data View paints the sweep in the overtone's colour and the
# derived quantities in this red, and this window says the same thing the same way.
FIT_COLOUR = circ.FIT_COLOUR
# points drawn per curve; the fit is evaluated on the same decimated axis
DRAW_POINTS = 600


def _overtone_label(idx):
    return (OVERTONE_NAMES[idx] if idx < len(OVERTONE_NAMES)
            else "overtone {}".format(2 * idx + 1))


class _FitTab(QtWidgets.QWidget):
    """One overtone: G(f) with the published fit on top, the residual beneath."""

    def __init__(self, overtone_index, theme_name, parent=None):
        super(_FitTab, self).__init__(parent)
        palette = theme.PLOT[theme_name]
        colour = Constants.plot_color_multi[
            overtone_index % len(Constants.plot_color_multi)]

        # Two graphics widgets under a movable divider: the curves G(f),
        # residual and B(f) stacked on the left, the locus on the right. The
        # locus is aspect locked, so the circle is as large as the SHORTER side
        # of its pane; a divider lets the pane be made square by hand, and the
        # default split below gives it about that at the default window size.
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground(palette["bg"])
        self.graphC = pg.GraphicsLayoutWidget()
        self.graphC.setBackground(palette["bg"])

        self.pG = self.graph.addPlot(row=0, col=0)
        self.pG.setTitle("conductance G(f)", color=palette["title"])
        self.pG.setLabel('bottom', 'f - f_res (published)', units='Hz', color=palette["title"])
        self.pG.setLabel('left', 'G', units='mS', color=palette["title"])
        # legends pinned to the top-left corner with a small inset: the default
        # anchor put them over the curve, and on a resonance the top left is the
        # one corner that is always empty
        self.pG.addLegend(offset=(8, 8))
        # the fit window the process used, drawn first so it sits under the data
        self.window = pg.LinearRegionItem(values=(0, 0), movable=False,
                                          brush=pg.mkBrush(128, 128, 128, 28),
                                          pen=pg.mkPen(None))
        self.window.setZValue(-10)
        self.pG.addItem(self.window)
        self.curveG = self.pG.plot(pen=None, symbol='o', symbolSize=3,
                                   symbolPen=None, symbolBrush=colour,
                                   name="G measured (shipped)")
        self.curveFit = self.pG.plot(pen=pg.mkPen(FIT_COLOUR, width=1.5,
                                                  style=QtCore.Qt.DashLine),
                                     name="phase-shifted Lorentzian (process)")
        self.markFres = pg.InfiniteLine(pos=0.0, angle=90,
                                        pen=pg.mkPen(FIT_COLOUR, width=1.5))
        self.markArg = pg.InfiniteLine(pos=0.0, angle=90,
                                       pen=pg.mkPen(colour, width=1,
                                                    style=QtCore.Qt.DotLine))
        self.pG.addItem(self.markFres)
        self.pG.addItem(self.markArg)
        # legend entries for the two markers (InfiniteLine has no legend of its own)
        self.pG.plot(pen=pg.mkPen(FIT_COLOUR, width=1.5), name="f_res published")
        self.pG.plot(pen=pg.mkPen(colour, width=1, style=QtCore.Qt.DotLine),
                     name="maximum of G (fallback)")

        self.pR = self.graph.addPlot(row=1, col=0)
        self.pR.setTitle("residual, measured - fit", color=palette["title"])
        self.pR.setLabel('bottom', 'f - f_res (published)', units='Hz', color=palette["title"])
        self.pR.setLabel('left', '% of range', color=palette["title"])
        self.pR.setXLink(self.pG)
        self.zeroR = self.pR.plot(pen=pg.mkPen(palette["axis"], width=1,
                                               style=QtCore.Qt.DotLine))
        self.curveR = self.pR.plot(pen=pg.mkPen(FIT_COLOUR, width=1))

        # susceptance B(f), under the residual and on the same x axis: B is where
        # a defect of the phase channel shows first -- the plateau at the fold, a
        # sign flip where the phase never crossed zero -- while G, even in the
        # phase, hides it. Measured only: the estimator fits G alone.
        self.pB = self.graph.addPlot(row=2, col=0)
        self.pB.setTitle("susceptance B(f) — measured", color=palette["title"])
        self.pB.setLabel('bottom', 'f - f_res (published)', units='Hz', color=palette["title"])
        self.pB.setLabel('left', 'B', units='mS', color=palette["title"])
        self.pB.setXLink(self.pG)
        self.zeroB = self.pB.plot(pen=pg.mkPen(palette["axis"], width=1,
                                               style=QtCore.Qt.DotLine))
        self.curveB = self.pB.plot(pen=pg.mkPen(colour, width=Constants.plot_line_width),
                                   name="B measured (shipped)")
        self.markFresB = pg.InfiniteLine(pos=0.0, angle=90,
                                         pen=pg.mkPen(FIT_COLOUR, width=1.5))
        self.pB.addItem(self.markFresB)

        # the admittance locus, spanning the three rows on the right: aspect
        # locked, because a circle has to look like one.
        self.pC = self.graphC.addPlot(row=0, col=0)
        self.pC.setTitle("admittance locus B vs G — measured", color=palette["title"])
        self.pC.setLabel('bottom', 'G', units='mS', color=palette["title"])
        self.pC.setLabel('left', 'B', units='mS', color=palette["title"])
        self.pC.setAspectLocked(True)
        self.pC.addLegend(offset=(8, 8))
        self.curveLocus = self.pC.plot(pen=None, symbol='o', symbolSize=2.5,
                                       symbolPen=None, symbolBrush=colour,
                                       name="measured (shipped)")
        # where the published resonance falls on the locus: read off the measured
        # arrays, not computed
        self.markLocusFres = self.pC.plot(pen=None, symbol='o', symbolSize=11,
                                          symbolPen=pg.mkPen(FIT_COLOUR, width=1.5),
                                          symbolBrush=None, name="f_res published")
        self.markLocusArg = self.pC.plot(pen=None, symbol='x', symbolSize=10,
                                         symbolPen=pg.mkPen(palette["axis"], width=1.5),
                                         symbolBrush=None, name="maximum of G")
        # the circle: the published fit's own in an experimental run, one fitted
        # here in a standard run (admittanceCircle -- display only)
        self.curveCircle = self.pC.plot(pen=pg.mkPen(FIT_COLOUR, width=1,
                                                     style=QtCore.Qt.DashLine),
                                        name="circle")
        # Vertical shares of the left column: G is the plot the fit is judged
        # on, B is a diagnostic, the residual is a strip. With 3/1/2 in a
        # 520 px pane the residual kept ~85 px including its title and axis and
        # the G pane was flat (Marco, 2026-09-16); 5/2/4 with a minimum height
        # on each plot keeps every axis readable and lets the window grow into
        # the curves rather than into the residual.
        self.graph.ci.layout.setRowStretchFactor(0, 5)
        self.graph.ci.layout.setRowStretchFactor(1, 2)
        self.graph.ci.layout.setRowStretchFactor(2, 4)
        self.pG.setMinimumHeight(180)
        self.pR.setMinimumHeight(90)
        self.pB.setMinimumHeight(150)
        # only the bottom plot carries the x label: the three share one axis
        # (linked) and the label repeated twice cost the curves 40 px
        self.pG.setLabel('bottom', '', color=palette["title"])
        self.pR.setLabel('bottom', '', color=palette["title"])
        self.pG.getAxis('bottom').setStyle(showValues=False)
        self.pR.getAxis('bottom').setStyle(showValues=False)
        self.pC.setMinimumSize(260, 260)

        for plot in self.plots():
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            plot.showGrid(x=False, y=False)

        self.split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.split.setObjectName("fitTabSplitter")
        self.split.addWidget(self.graph)
        self.split.addWidget(self.graphC)
        self.split.setCollapsible(0, False)
        self.split.setCollapsible(1, True)
        self.split.setStretchFactor(0, 4)
        self.split.setStretchFactor(1, 3)
        self.split.setSizes([640, 480])

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.split)

        # framing of the aspect-locked locus (shared rule, see admittanceCircle)
        self._framer = circ.LocusFramer(self.pC)

    @property
    def _framed(self):
        return self._framer.framed

    def frame_locus(self, xmin, xmax, ymin, ymax):
        """Frame the locus on the measurement AND the circle; see LocusFramer."""
        self._framer.frame(xmin, xmax, ymin, ymax)

    def plots(self):
        return (self.pG, self.pR, self.pB, self.pC)

    def clear(self):
        empty = np.array([], dtype=float)
        for c in (self.curveG, self.curveFit, self.curveR, self.zeroR,
                  self.curveB, self.zeroB, self.curveLocus, self.curveCircle,
                  self.markLocusFres, self.markLocusArg):
            c.setData(x=empty, y=empty)
        self.window.setRegion((0, 0))
        self._framer.reset()


class ImpedanceFitWindow(QtWidgets.QWidget):
    """The published estimator, live, per overtone."""

    def __init__(self, worker, overtones, theme_name="light", parent=None):
        super(ImpedanceFitWindow, self).__init__(parent)
        self.worker = worker
        self.overtones = int(overtones)
        self.theme = theme_name if theme_name in theme.PLOT else "light"
        # a window of its own even with a parent (the parent is what brings the
        # application style sheet); its own sheet because the application's
        # background rules name QMainWindow/QDialog, not a bare QWidget
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setObjectName("impedanceFitWindow")
        self.setStyleSheet(theme.qss(theme.palette(self.theme)))
        self._palette = theme.palette(self.theme)
        self._seq = [None] * self.overtones
        self._last = [None] * self.overtones
        self._paused = False

        self.setWindowTitle("openQCM NEXT — live fit (what the acquisition publishes)")
        # sized so that the locus pane is about square at the default split:
        # 1180 x 860 minus the toolbar and a 200 px table leaves ~600 px for the
        # plots, and the locus gets ~480 of the 1180 in width
        self.resize(1180, 860)

        self.chkPause = QtWidgets.QCheckBox("freeze")
        self.chkPause.setToolTip("stop following the acquisition; the last sweep stays on screen")
        self.chkPause.toggled.connect(self._on_pause)
        self.lblStatus = QtWidgets.QLabel("waiting for data")
        self.lblStatus.setStyleSheet("color: %s;" % self._palette["muted"])
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.chkPause)
        top.addStretch(1)
        top.addWidget(self.lblStatus)
        # ⚠️ In a STANDARD run (the Measurement Setup box unchecked) the process
        # runs no fit: this window then shows the measured G with the published
        # maximum, and the table says "STANDARD". The fit appears only in an
        # EXPERIMENTAL run, and only as the process shipped it.

        self._tabs = QtWidgets.QTabWidget()
        self._menu = PlotMenu(self)
        self._panes = []
        for i in range(self.overtones):
            pane = _FitTab(i, self.theme)
            self._tabs.addTab(pane, _overtone_label(i))
            self._panes.append(pane)
            self._menu.attach(pane.plots())
        self._tabs.currentChanged.connect(self._draw_selected)

        self.table = QtWidgets.QTableWidget(self.overtones, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setMaximumHeight(28 * (self.overtones + 1) + 8)
        mono = QtGui.QFont("Menlo" if sys.platform == "darwin" else
                           "Consolas" if sys.platform.startswith("win") else "Monospace")
        mono.setStyleHint(QtGui.QFont.TypeWriter)
        mono.setPointSize(10)
        self.table.setFont(mono)
        for row in range(self.overtones):
            for col in range(len(COLUMNS)):
                it = QtWidgets.QTableWidgetItem("-")
                it.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.table.setItem(row, col, it)
            self.table.item(row, 0).setText(str(2 * row + 1))
        self.table.clicked.connect(lambda i: self._tabs.setCurrentIndex(i.row()))

        lo, hi = Constants.PSL_GAMMA_RATIO
        note = QtWidgets.QLabel(
            "Everything here is what the acquisition process used: G as shipped (mS, constant "
            "baseline removed), the phase-shifted Lorentzian it fitted on the ±%.0fΓ window "
            "(dashed, evaluated from the shipped parameters; nothing is refitted here), the "
            "published f_res and the maximum of G, which is the fallback. Γ is the half width at "
            "half maximum; D = 2Γ/f_res.  THE GATE, Constants.PSL_*: the fit is published when "
            "rms ≤ %.0f %% of the range of G, |φ| ≤ %.0f° and Γ is within %.1f–%.1f× the half-height "
            "width; otherwise the maximum of G is published, the sweep is counted as a fallback and "
            "a line goes to the System Log. These three limits are parameters of the measurement.  "
            "δ is the phase offset the chain applied (\"no fold\": the phase never crossed zero)."
            % (Constants.PSL_BAND_GAMMA, 100.0 * Constants.PSL_RMS_MAX,
               Constants.PSL_PHI_MAX_DEG, lo, hi))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s; font-size: 11px;" % self._palette["muted"])

        # The table and its note sit under a movable divider, so the plots can be
        # given the whole window and the table dragged shut (Marco, 2026-09-16).
        self._below = QtWidgets.QWidget()
        below = QtWidgets.QVBoxLayout(self._below)
        below.setContentsMargins(0, 0, 0, 0)
        below.setSpacing(4)
        below.addWidget(self.table)
        below.addWidget(note)

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._splitter.setObjectName("fitSplitter")
        self._splitter.setChildrenCollapsible(True)
        self._splitter.addWidget(self._tabs)
        self._splitter.addWidget(self._below)
        # the plots keep the room when the window is resized; the table can be
        # collapsed to nothing by dragging the handle down
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, True)
        self._splitter.setSizes([600, 200])

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self._splitter, 1)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)

    # ----------------------------------------------------------------- events
    def showEvent(self, event):
        super(ImpedanceFitWindow, self).showEvent(event)
        if not self._paused:
            self._timer.start(Constants.IMPEDANCE_FIT_UPDATE_MS)

    def hideEvent(self, event):
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

    GRADES = {"light": ("#2e7d32", "#ef6c00", "#c62828"),
              "dark": ("#81c784", "#ffb74d", "#ef9a9a")}

    def _grade(self, value, good, bad):
        ok, warn, no = self.GRADES[self.theme]
        return ok if value < good else warn if value < bad else no

    def _current_index(self):
        idx = self._tabs.currentIndex()
        return idx if 0 <= idx < self.overtones else None

    # ------------------------------------------------------------------- work
    def _tick(self):
        """Pick up every overtone whose spectrum changed, refresh its row, and
        redraw the visible tab. Wrapped whole: a view must never disturb an
        acquisition."""
        if self.worker is None:
            return
        try:
            changed = 0
            visible = self._current_index()
            redraw = False
            for idx in range(self.overtones):
                try:
                    seq = self.worker.get_GB_seq(idx)
                except Exception:
                    continue
                if seq == self._seq[idx]:
                    continue
                self._seq[idx] = seq
                if self._collect(idx):
                    changed += 1
                    # the table holds every overtone, so each one is collected;
                    # only the tab on screen is worth redrawing
                    redraw = redraw or idx == visible
            if changed:
                if redraw:
                    self._draw_selected()
                seen = [d["fit"] for d in self._last if d is not None and d["fit"] is not None]
                standard = bool(seen) and all(f.get("mode") == "argmax" for f in seen)
                if standard:
                    # in a standard run no fit runs at all: counting them would read
                    # as "the fit keeps failing", which is not what is happening
                    self.lblStatus.setText("%d overtone(s) updated — STANDARD estimator, "
                                           "no fit in this run" % changed)
                else:
                    fits = sum(1 for f in seen if f.get("source") == "fit")
                    self.lblStatus.setText("%d overtone(s) updated — %d published by the fit"
                                           % (changed, fits))
        except Exception as e:
            self._timer.stop()
            print(TAG, "Warning: live fit view stopped:", e)
            Log.i(TAG, "Warning: live fit view stopped: %s" % e)
            self.lblStatus.setText("stopped: %s" % e)

    def _collect(self, idx):
        """Read one overtone from the worker: shipped arrays, published pair,
        fit fields. No computation beyond evaluating the shipped model."""
        g = self.worker.get_G_exact_buffer(idx)
        f = self.worker.get_F_G_values_buffer(idx)
        if not (isinstance(g, np.ndarray) and isinstance(f, np.ndarray)):
            return False
        if len(g) < 8 or len(f) != len(g):
            return False
        try:
            b = self.worker.get_B_exact_buffer(idx)
        except Exception:
            b = None
        if not (isinstance(b, np.ndarray) and len(b) == len(g)):
            b = None
        f_pub = float(self.worker.get_fr_G_buffer(idx))
        gam_pub = float(self.worker.get_gamma_G_buffer(idx))
        try:
            delta = float(self.worker.get_delta_G_buffer(idx))
        except Exception:
            delta = float("nan")
        try:
            fit = self.worker.get_fit_G_buffer(idx)
        except Exception:
            fit = None
        self._last[idx] = dict(f=np.asarray(f, dtype=float), g=np.asarray(g, dtype=float),
                               b=None if b is None else np.asarray(b, dtype=float),
                               f_pub=f_pub, gam_pub=gam_pub, delta=delta, fit=fit)
        self._update_row(idx, self._last[idx])
        return True

    def _update_row(self, idx, d):
        fit = d["fit"]
        f_pub, gam_pub = d["f_pub"], d["gam_pub"]
        D = 2.0 * gam_pub / f_pub * 1e6 if f_pub else float("nan")
        delta_txt = ("-" if not circ.finite(d["delta"]) else
                     "no fold" if d["delta"] == 0.0 else "%+.2f" % d["delta"])
        standard = fit is not None and fit.get("mode") == "argmax"
        if fit is None or standard:
            vals = ("%d" % (2 * idx + 1),
                    "STANDARD: maximum of G, half-height width" if standard
                    else "maximum of G (no fit shipped)",
                    "%.1f" % f_pub, "%.1f" % gam_pub, "%.2f" % D, "-", "-",
                    "%.1f" % f_pub, "%.1f" % gam_pub, delta_txt)
            colour = self._palette["text"] if standard else self._palette["muted"]
        else:
            src = ("fit  (%d fit / %d fallback)" % (fit["used"], fit["fallback"])
                   if fit["source"] == "fit" else
                   "FALLBACK: %s  (%d fit / %d fallback)"
                   % (fit["reason"], fit["used"], fit["fallback"]))
            vals = ("%d" % (2 * idx + 1), src,
                    "%.1f" % f_pub, "%.1f" % gam_pub, "%.2f" % D,
                    "%+.1f" % fit["phi_deg"] if circ.finite(fit["phi_deg"]) else "-",
                    "%.2f" % (100.0 * fit["rms_rel"]) if circ.finite(fit["rms_rel"]) else "-",
                    "%.1f" % fit["f_argmax"], "%.1f" % fit["gamma_hh"], delta_txt)
            colour = (self.GRADES[self.theme][0] if fit["source"] == "fit"
                      else self.GRADES[self.theme][2])
        for col, v in enumerate(vals):
            self.table.item(idx, col).setText(v)
        self.table.item(idx, 1).setForeground(QtGui.QColor(colour))
        self.table.item(idx, 1).setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if fit is not None and circ.finite(fit["rms_rel"]):
            rms = 100.0 * fit["rms_rel"]
            lim = 100.0 * Constants.PSL_RMS_MAX
            self.table.item(idx, 6).setForeground(QtGui.QColor(self._grade(rms, 0.4 * lim, lim)))
        if fit is not None and circ.finite(fit["phi_deg"]):
            self.table.item(idx, 5).setForeground(QtGui.QColor(
                self._grade(abs(fit["phi_deg"]), 0.5 * Constants.PSL_PHI_MAX_DEG,
                            Constants.PSL_PHI_MAX_DEG)))

    def model_curve(self, idx, f):
        """The shipped model on an axis, in mS of the shipped curve; None if the
        producer shipped no fit. Public so a test can compare it with
        core.lorentzian.rotated_lorentzian on the same parameters."""
        d = self._last[idx]
        if d is None or d["fit"] is None:
            return None
        fit = d["fit"]
        if not all(circ.finite(fit[k]) for k in ("fres", "gamma", "phi_deg", "gmax_mS", "g_off_mS")):
            return None
        return rotated_lorentzian(f, fit["fres"], fit["gamma"], fit["phi_deg"],
                                  fit["gmax_mS"], fit["g_off_mS"])

    def _draw_channels(self, pane, d, fx, gx, x):
        """B(f) and the locus: shipped arrays and two lookups on them, no model."""
        b = d["b"]
        fit = d["fit"]
        f_arg = None if not fit else fit.get("f_argmax")
        if b is None:
            for c in (pane.curveB, pane.zeroB, pane.curveLocus, pane.curveCircle,
                      pane.markLocusFres, pane.markLocusArg):
                c.setData(x=np.array([]), y=np.array([]))
            pane.pB.setTitle("susceptance B(f) — not shipped by the process")
            pane.pC.setTitle("admittance locus — B not shipped")
            return
        bx = b[::max(1, len(b) // DRAW_POINTS)][:len(x)]
        pane.curveB.setData(x=x[:len(bx)], y=bx)
        pane.zeroB.setData(x=[x[0], x[-1]], y=[0.0, 0.0])
        pane.markFresB.setPos(0.0)
        pane.curveLocus.setData(x=gx[:len(bx)], y=bx)
        # the published resonance and the maximum of G, READ OFF the measured
        # arrays (np.interp is a lookup between two samples, not an estimate)
        g_at = float(np.interp(d["f_pub"], d["f"], d["g"]))
        b_at = float(np.interp(d["f_pub"], d["f"], b))
        pane.markLocusFres.setData(x=[g_at], y=[b_at])
        if f_arg is not None and np.isfinite(f_arg):
            pane.markLocusArg.setData(x=[float(np.interp(f_arg, d["f"], d["g"]))],
                                      y=[float(np.interp(f_arg, d["f"], b))])
        else:
            pane.markLocusArg.setData(x=np.array([]), y=np.array([]))
        # B is where a broken phase reconstruction shows: the largest step between
        # adjacent samples, as a fraction of B's own range. A continuous
        # trajectory keeps this at a few per cent.
        span = float(np.ptp(bx)) or 1.0
        jump = 100.0 * float(np.max(np.abs(np.diff(bx)))) if len(bx) > 1 else 0.0
        pane.pB.setTitle("B(f) measured &nbsp;|&nbsp; span %.3f mS &nbsp;|&nbsp; "
                         "largest step between samples %.1f %% of span"
                         % (span, jump / span))
        self._draw_circle(pane, d, b)

    def _draw_circle(self, pane, d, b):
        """The circle over the locus: the published fit's own in an experimental
        run, one fitted HERE (display only) in a standard run. The geometry and
        the rule live in admittanceCircle, shared with the main panel, so the
        two views draw the same circle for the same sweep."""
        c = circ.circle_for(d["fit"], d["f"], d["g"], b, d["f_pub"])
        if c is None:
            pane.curveCircle.setData(x=np.array([]), y=np.array([]))
            pane.frame_locus(float(np.nanmin(d["g"])), float(np.nanmax(d["g"])),
                             float(np.nanmin(b)), float(np.nanmax(b)))
            pane.pC.setTitle("admittance locus, measured &nbsp;|&nbsp; no circle "
                             "(too few points)")
            return
        pane.curveCircle.setData(x=c["x"], y=c["y"])
        # the view has to hold the measurement AND the circle: see LocusFramer
        pane.frame_locus(*circ.union_bounds((d["g"], b), (c["x"], c["y"])))
        pane.pC.setTitle("locus &nbsp;|&nbsp; %s &nbsp;|&nbsp; ⚠️ G baseline-removed, B as "
                         "computed" % c["label"])

    def _draw_selected(self, *_args):
        idx = self._current_index()
        if idx is None or self._last[idx] is None:
            return
        pane = self._panes[idx]
        d = self._last[idx]
        f, g, f_pub = d["f"], d["g"], d["f_pub"]
        step = max(1, len(f) // DRAW_POINTS)
        fx, gx = f[::step], g[::step]
        x = fx - f_pub
        pane.curveG.setData(x=x, y=gx)
        pane.markFres.setPos(0.0)
        self._draw_channels(pane, d, fx, gx, x)
        model = self.model_curve(idx, fx)
        fit = d["fit"]
        if fit is not None and fit.get("mode") == "argmax":
            model = None                      # the standard run: no fit exists to draw
        if model is None:
            pane.curveFit.setData(x=np.array([]), y=np.array([]))
            pane.curveR.setData(x=np.array([]), y=np.array([]))
            pane.zeroR.setData(x=np.array([]), y=np.array([]))
            pane.window.setRegion((0, 0))
            pane.markArg.setPos(0.0)
            standard = fit is not None and fit.get("mode") == "argmax"
            pane.pG.setTitle("G(f) &nbsp;|&nbsp; %s: maximum of G %.1f Hz &nbsp;|&nbsp; "
                             "Γ half height %.1f Hz &nbsp;|&nbsp; D = %.2f ppm%s"
                             % ("STANDARD estimator" if standard else "published",
                                f_pub, d["gam_pub"], 2.0 * d["gam_pub"] / f_pub * 1e6,
                                "" if standard else " &nbsp;|&nbsp; no fit shipped by the process"))
            pane.pR.setTitle("residual: no fit in this run" if standard else "residual: no fit")
            return
        pane.curveFit.setData(x=x, y=model)
        span = float(np.ptp(gx)) or 1.0
        pane.curveR.setData(x=x, y=(gx - model) / span * 100.0)
        pane.zeroR.setData(x=[x[0], x[-1]], y=[0.0, 0.0])
        band = Constants.PSL_BAND_GAMMA * fit["gamma_hh"]
        pane.window.setRegion((fit["f_argmax"] - band - f_pub, fit["f_argmax"] + band - f_pub))
        pane.markArg.setPos(fit["f_argmax"] - f_pub)
        who = ("fit" if fit["source"] == "fit" else "FALLBACK (%s)" % fit["reason"])
        pane.pG.setTitle("published by the %s &nbsp;|&nbsp; f_res = %.1f Hz &nbsp;|&nbsp; "
                         "Γ = %.1f Hz &nbsp;|&nbsp; D = %.2f ppm &nbsp;|&nbsp; φ = %+.1f° "
                         "&nbsp;|&nbsp; maximum of G %+.0f Hz from f_res"
                         % (who, f_pub, d["gam_pub"], 2.0 * d["gam_pub"] / f_pub * 1e6,
                            fit["phi_deg"], fit["f_argmax"] - f_pub))
        pane.pR.setTitle("residual, measured − fit: rms %.2f %% of range (gate: ≤ %.0f %%) "
                         "&nbsp;|&nbsp; fit cost %.1f ms in the process"
                         % (100.0 * fit["rms_rel"], 100.0 * Constants.PSL_RMS_MAX, fit["cost_ms"]))
