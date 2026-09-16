#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VER 0.1.6G — live fit window: what the acquisition publishes, and nothing else.

Opens from Tools > "Impedance Fit (live)". One tab per overtone with the exact
conductance G(f) the process shipped, the phase-shifted Lorentzian the process
FITTED to it (core/lorentzian.py) drawn from the parameters it shipped, the
published f_res, the maximum of G that is the fallback, the ±band·Γ window the
fit ran on, and the residual beneath. A table with the numbers of every
overtone: which estimator was published, f_res, Γ, D, φ, rms, the fallback pair,
the phase offset δ the chain applied.

THE RULE (Marco, 2026-09-16): what this window shows is what the process used to
produce the logged numbers. So this window fits NOTHING. Every curve is either a
shipped array or the shipped model evaluated on the shipped axis; every number in
the table came out of the process. If the producer shipped no fit (an older
process, or Constants.IMPEDANCE_ESTIMATOR = "argmax") the window shows the
measured G with the maximum marked and says so.

What went away with the rewrite of 2026-09-16, on purpose: the BVD circle fit
(FIT 1), the symmetric Lorentzian refitted in the GUI (FIT 2), the B(f) and locus
panels, R1, L1, the masked-percent column, and the import of the offline module
sweep_data/fit_admittance.py — the release tree no longer needs sweep_data/ for
any live view. The research behind those is in research/air-ipa-water-1920-2026-09-11/.

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

TAG = "[ImpedanceFit]"

COLUMNS = ("n", "published by", "f_res [Hz]", "Gamma [Hz]", "D [ppm]", "phi [deg]",
           "rms [% range]", "f argmax [Hz]", "Gamma half height [Hz]", "delta [deg]")

# Colour of everything DERIVED from the measurement (the fit, the published
# marker): Raw Data View paints the sweep in the overtone's colour and the
# derived quantities in this red, and this window says the same thing the same way.
FIT_COLOUR = "#f44336"
# points drawn per curve; the fit is evaluated on the same decimated axis
DRAW_POINTS = 600


def _overtone_label(idx):
    return (OVERTONE_NAMES[idx] if idx < len(OVERTONE_NAMES)
            else "overtone {}".format(2 * idx + 1))


def _finite(x):
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


class _FitTab(QtWidgets.QWidget):
    """One overtone: G(f) with the published fit on top, the residual beneath."""

    def __init__(self, overtone_index, theme_name, parent=None):
        super(_FitTab, self).__init__(parent)
        palette = theme.PLOT[theme_name]
        colour = Constants.plot_color_multi[
            overtone_index % len(Constants.plot_color_multi)]

        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground(palette["bg"])

        self.pG = self.graph.addPlot(row=0, col=0)
        self.pG.setTitle("conductance G(f)", color=palette["title"])
        self.pG.setLabel('bottom', 'f - f_res (published)', units='Hz', color=palette["title"])
        self.pG.setLabel('left', 'G', units='mS', color=palette["title"])
        self.pG.addLegend()
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
        self.graph.ci.layout.setRowStretchFactor(0, 3)
        self.graph.ci.layout.setRowStretchFactor(1, 1)

        for plot in self.plots():
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            plot.showGrid(x=False, y=False)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.graph)

    def plots(self):
        return (self.pG, self.pR)

    def clear(self):
        empty = np.array([], dtype=float)
        for c in (self.curveG, self.curveFit, self.curveR, self.zeroR):
            c.setData(x=empty, y=empty)
        self.window.setRegion((0, 0))


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
        self.resize(1080, 720)

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

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self._tabs, 1)
        lay.addWidget(self.table)
        lay.addWidget(note)

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
            if changed:
                self._draw_selected()
                fits = sum(1 for d in self._last if d is not None and d["fit"] is not None
                           and d["fit"]["source"] == "fit")
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
                               f_pub=f_pub, gam_pub=gam_pub, delta=delta, fit=fit)
        self._update_row(idx, self._last[idx])
        return True

    def _update_row(self, idx, d):
        fit = d["fit"]
        f_pub, gam_pub = d["f_pub"], d["gam_pub"]
        D = 2.0 * gam_pub / f_pub * 1e6 if f_pub else float("nan")
        delta_txt = ("-" if not _finite(d["delta"]) else
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
                    "%+.1f" % fit["phi_deg"] if _finite(fit["phi_deg"]) else "-",
                    "%.2f" % (100.0 * fit["rms_rel"]) if _finite(fit["rms_rel"]) else "-",
                    "%.1f" % fit["f_argmax"], "%.1f" % fit["gamma_hh"], delta_txt)
            colour = (self.GRADES[self.theme][0] if fit["source"] == "fit"
                      else self.GRADES[self.theme][2])
        for col, v in enumerate(vals):
            self.table.item(idx, col).setText(v)
        self.table.item(idx, 1).setForeground(QtGui.QColor(colour))
        self.table.item(idx, 1).setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if fit is not None and _finite(fit["rms_rel"]):
            rms = 100.0 * fit["rms_rel"]
            lim = 100.0 * Constants.PSL_RMS_MAX
            self.table.item(idx, 6).setForeground(QtGui.QColor(self._grade(rms, 0.4 * lim, lim)))
        if fit is not None and _finite(fit["phi_deg"]):
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
        if not all(_finite(fit[k]) for k in ("fres", "gamma", "phi_deg", "gmax_mS", "g_off_mS")):
            return None
        return rotated_lorentzian(f, fit["fres"], fit["gamma"], fit["phi_deg"],
                                  fit["gmax_mS"], fit["g_off_mS"])

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
