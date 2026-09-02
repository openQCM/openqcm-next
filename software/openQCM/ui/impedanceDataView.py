"""
Impedance Data View: the live conductance and susceptance spectra, one tab per
overtone, with the published resonance frequency and half bandwidth drawn on the
conductance.

Built to the same two rules as ui/rawDataView.py, and for the same reasons:

*It pulls, nobody pushes.* The dialog owns a timer and asks the acquisition
object for its buffers. There is no set_data(), no signal from the worker, no
registration. A closed dialog therefore costs exactly nothing -- no code path is
left running -- and the acquisition never waits on the GUI.

*It reads memory only.* Never a file.

⚠️ **And one rule it keeps more strictly than Raw Data View: it computes
nothing.** Raw Data View re-runs the fit in the GUI thread from core/resonance.py
and has to be careful to use the very parameters the acquisition used. Here G and
B are read straight out of the buffers the acquisition process filled -- the same
arrays the live impedance panel draws -- so this view *cannot* disagree with the
instrument. Do not add a local inversion of the divider here, however convenient:
that is precisely how a viewer starts showing a spectrum the datalog never saw.

The overlay is the measurement itself, not a fresh one:

* the peak marker sits at ``f_r`` from ``get_fr_G_buffer``;
* the band is drawn between the **two frequencies where the conductance actually
  crosses half height**, from ``get_band_G_buffer``, with a line at that height.

⚠️ **Those two crossings are not symmetric about f_r, and drawing them as if they
were is wrong on screen even when the number is right.** Γ is published as their
half-difference (Johannsmann, *Sensors* 2021, 21, 3490 §2), and the peak is
skewed by the residual C0 branch -- which is why the measurement went two-sided
in the first place. This view first drew ``f_r ∓ Γ``, and on a real fundamental
in air that put the markers at 16.5 S and 10.2 S against a half height of
13.49 S. The crossings now travel from the acquisition process along with Γ, so
the picture shows what was measured.

If the sweep window held no crossing on one side -- damped loads, where Γ reaches
kilohertz and the window is sized for air -- that side arrives as NaN and the
view falls back to ``f_r ∓ Γ`` for it, and says so in the header.
"""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from openQCM.core.constants import Constants
from openQCM.common.logger import Logger as Log
from openQCM.ui import theme
from openQCM.ui.plotMenu import PlotMenu

TAG = "[ImpedanceDataView]"

# How often the dialog asks the acquisition object for fresh buffers. Same
# cadence as Raw Data View: a sweep takes seconds, so this is already generous.
REFRESH_MS = 300

# Target number of points per drawn curve. The producer already clips the
# spectrum to a few Γ around resonance, so these arrays are short in air and
# shorter still in a liquid -- a fixed stride would leave too few points, which
# is why the live panel decimates adaptively and so does this.
PLOT_TARGET_POINTS = 600

# First framing of a tab, as a multiple of the published Γ either side of the
# peak, with a floor for a band that comes out implausibly narrow.
BAND_ZOOM_FACTOR = 12.0
MIN_ZOOM_HALF_SPAN_HZ = 200.0

OVERTONE_NAMES = ["Fundamental", "3rd overtone", "5th overtone",
                  "7th overtone", "9th overtone"]


def _as_sweep(values):
    """The buffers hold placeholders until the first sweep lands.

    Returns a 1-D float array, or None while there is nothing to draw.
    """
    if values is None or np.isscalar(values):
        return None
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 3:
        return None
    if not np.isfinite(array).any():
        return None
    return array


def _scalar(value):
    """One finite number out of a buffer that may hold a scalar or an array."""
    try:
        array = np.asarray(value, dtype=float).ravel()
    except (TypeError, ValueError):
        return None
    if array.size == 0:
        return None
    number = float(array[0])
    return number if np.isfinite(number) else None


class _OvertoneTab(QtWidgets.QWidget):
    """One tab: conductance over susceptance, X axes linked, overlay on G."""

    def __init__(self, overtone_index, theme_name, parent=None):
        super(_OvertoneTab, self).__init__(parent)
        self._index = overtone_index
        palette = theme.PLOT[theme_name]
        colour = Constants.plot_color_multi[
            overtone_index % len(Constants.plot_color_multi)]
        colour_b = Constants.plot_color_multi_diss[
            overtone_index % len(Constants.plot_color_multi_diss)]

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.info = QtWidgets.QLabel("Waiting for data...")
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(palette["bg"])
        layout.addWidget(self.canvas, stretch=1)

        self.plt_g = self.canvas.addPlot(row=0, col=0)
        self.plt_b = self.canvas.addPlot(row=1, col=0)
        self.plt_g.setTitle("Conductance G", color=palette["title"])
        self.plt_b.setTitle("Susceptance B", color=palette["title"])
        # ⚠️ mS, not S, and baseline-removed: that is what the acquisition
        # ships (Multiscan.elaborate_multi scales by 1000 and subtracts the
        # mean of the first 100 samples so the locus closes into a circle).
        # The axis said "S" while the numbers were milli, which is how a half
        # height of 13.4 mS could be read as 0.0134 and drawn on the floor.
        self.plt_g.setLabel("left", "G", units="mS", color=palette["title"])
        self.plt_b.setLabel("left", "B", units="mS", color=palette["title"])
        self.plt_b.setLabel("bottom", "Frequency", units="Hz",
                            color=palette["title"])
        for plot in (self.plt_g, self.plt_b):
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            # grid off by default, as everywhere else in this GUI. The default
            # pyqtgraph menus are switched off by PlotMenu.attach().
            plot.showGrid(x=False, y=False)

        # zoom and pan stay in step between the two panels
        self.plt_b.setXLink(self.plt_g)

        legend = self.plt_g.addLegend(offset=(10, 10))

        self.conductance = self.plt_g.plot(
            pen=pg.mkPen(color=colour, width=Constants.plot_line_width))
        legend.addItem(self.conductance, "G")

        self.band = pg.LinearRegionItem(
            values=[0, 0], movable=False,
            brush=pg.mkBrush(76, 175, 80, 40),
            pen=pg.mkPen("#4caf50", width=1, style=QtCore.Qt.DashLine))
        self.band.setZValue(-10)
        self.band.setVisible(False)
        self.plt_g.addItem(self.band)

        # the height at which the band was measured: with the crossings on it,
        # the whole construction can be checked by eye in one glance
        self.half_line = pg.InfiniteLine(
            pos=0, angle=0, movable=False,
            pen=pg.mkPen("#4caf50", width=1, style=QtCore.Qt.DotLine))
        self.half_line.setVisible(False)
        self.plt_g.addItem(self.half_line)

        # the two frequencies where G crosses half height
        self.band_points = pg.ScatterPlotItem(
            size=9, symbol="o", pen=pg.mkPen("#ffffff", width=1.0),
            brush=pg.mkBrush("#4caf50"))
        self.plt_g.addItem(self.band_points)
        legend.addItem(self.band_points, "half height")

        self.peak = pg.ScatterPlotItem(
            size=11, symbol="d", pen=pg.mkPen("#ffffff", width=1.2),
            brush=pg.mkBrush("#f44336"))
        self.plt_g.addItem(self.peak)
        legend.addItem(self.peak, "f_r")

        self.susceptance = self.plt_b.plot(
            pen=pg.mkPen(color=colour_b, width=Constants.plot_line_width))

        # set once, on the first overlay, then never again: see frame_once()
        self._framed = False

    def frame_once(self, f_res, gamma, f_lo, f_hi):
        """Frame the resonance the first time this tab has something to show.

        Only once: after that the axes belong to whoever is looking, and a view
        that re-framed itself every 300 ms would be unusable. The range is
        clamped to the data, because the acquisition already clips the spectrum
        to a few Γ around resonance and framing wider would only add empty axis.
        """
        if self._framed:
            return
        half = max(BAND_ZOOM_FACTOR * abs(gamma), MIN_ZOOM_HALF_SPAN_HZ)
        low = max(f_res - half, f_lo)
        high = min(f_res + half, f_hi)
        if high > low:
            self.plt_g.setXRange(low, high, padding=0)
            self._framed = True

    def plots(self):
        return (self.plt_g, self.plt_b)

    def clear_overlay(self):
        self.band.setVisible(False)
        self.half_line.setVisible(False)
        self.peak.setData(x=[], y=[])
        self.band_points.setData(x=[], y=[])


class ImpedanceDataViewDialog(QtWidgets.QDialog):
    """Non-modal live view of G and B, one tab per overtone."""

    def __init__(self, host, theme_name="light", parent=None):
        super(ImpedanceDataViewDialog, self).__init__(parent)
        self._host = host
        self._theme = theme_name if theme_name in theme.PLOT else "light"

        self.setWindowTitle("Impedance Data View - live conductance")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(720, 560)
        self.resize(1000, 720)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self._tabs = QtWidgets.QTabWidget()
        layout.addWidget(self._tabs)

        # the shared right-click menu: one connection per scene and the grid
        # state, both handled in ui/plotMenu.py
        self._menu = PlotMenu(self)

        self._panes = []
        for idx in range(len(Constants.overtone_dummy)):
            pane = _OvertoneTab(idx, self._theme)
            name = (OVERTONE_NAMES[idx] if idx < len(OVERTONE_NAMES)
                    else "overtone {}".format(2 * idx + 1))
            self._tabs.addTab(pane, name)
            self._panes.append(pane)
            self._menu.attach(pane.plots())

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(REFRESH_MS)

    ###########################################################################
    # Pull
    ###########################################################################
    def _refresh(self):
        """Read the buffers of the *current* acquisition object and redraw.

        The worker is looked up again on every tick and never cached: START and
        STOP replace the object, and a reference taken at construction would
        leave the view frozen with no indication that it had stopped following.
        """
        worker = getattr(self._host, "worker", None)
        if worker is None:
            return

        index = self._tabs.currentIndex()
        if index < 0 or index >= len(self._panes):
            return
        # only the visible tab is drawn: switching tab picks the new one up on
        # the next tick.
        self._update_pane(worker, index)

    def _update_pane(self, worker, index):
        pane = self._panes[index]
        try:
            freq = _as_sweep(worker.get_F_G_values_buffer(index))
            g = _as_sweep(worker.get_G_exact_buffer(index))
            b = _as_sweep(worker.get_B_exact_buffer(index))
            f_res = _scalar(worker.get_fr_G_buffer(index))
            gamma = _scalar(worker.get_gamma_G_buffer(index))
            try:
                f_left, f_right, half_level = worker.get_band_G_buffer(index)
            except (AttributeError, TypeError, ValueError, IndexError):
                # a worker from before the crossings travelled, or a buffer not
                # yet shaped. ⚠️ Caught HERE and not by the outer handler on
                # purpose: the crossings are an overlay, and losing them must
                # not stop G and B from being drawn -- letting this escape made
                # a missing band buffer blank the whole pane, including the
                # "waiting for data" message.
                f_left = f_right = half_level = float("nan")
        except (AttributeError, IndexError, TypeError) as error:
            # a worker that has been stopped, or a buffer list not yet sized
            Log.d(TAG, "buffers unavailable: {}".format(error))
            return

        if freq is None or g is None or freq.size != g.size:
            pane.clear_overlay()
            pane.info.setText("Waiting for data...")
            return

        # Adaptive decimation, like the live panel: the producer already clips
        # the spectrum to a few Γ, so a fixed stride would leave too few points.
        step = max(1, freq.size // PLOT_TARGET_POINTS)
        pane.conductance.setData(x=freq[::step], y=g[::step])
        if b is not None and b.size == freq.size:
            pane.susceptance.setData(x=freq[::step], y=b[::step])
        else:
            pane.susceptance.setData(x=[], y=[])

        if f_res is None or gamma is None or gamma <= 0:
            pane.clear_overlay()
            pane.info.setText(
                "G and B drawn; no published peak yet  |  {} samples".format(
                    freq.size))
            return

        # ⚠️ The band is drawn between the crossings the instrument MEASURED,
        # which are not symmetric about f_r. Only where a side is missing --
        # the window held no crossing there -- does it fall back to f_r ∓ Γ for
        # that side, and the header says so.
        guessed = []
        if not np.isfinite(f_left):
            f_left, _ = f_res - gamma, guessed.append("left")
        if not np.isfinite(f_right):
            f_right, _ = f_res + gamma, guessed.append("right")

        edges = np.array([f_left, f_right], dtype=float)
        g_peak = float(np.interp(f_res, freq, g))
        # heights: the measured level where it travelled, otherwise read off the
        # curve. Both are lookups on data already in hand, not a measurement.
        if np.isfinite(half_level):
            g_edges = np.array([half_level, half_level], dtype=float)
            pane.half_line.setValue(float(half_level))
            pane.half_line.setVisible(True)
        else:
            g_edges = np.interp(edges, freq, g)
            pane.half_line.setVisible(False)

        pane.peak.setData(x=[f_res], y=[g_peak])
        pane.band_points.setData(x=edges, y=g_edges)
        pane.band.setRegion([float(edges[0]), float(edges[1])])
        pane.band.setVisible(True)
        pane.frame_once(f_res, gamma, float(freq[0]), float(freq[-1]))

        notes = ""
        if guessed:
            notes += "  |  {} edge from f_r ∓ Γ (no crossing in window)".format(
                " and ".join(guessed))
        if edges[0] < freq[0] or edges[1] > freq[-1]:
            # Γ wider than the acquired window: happens on damped loads, where
            # the window is sized for air. Say so rather than draw a band edge
            # pinned to the end of the array.
            notes += "  |  BAND WIDER THAN THE ACQUIRED WINDOW"

        pane.info.setText(
            "f_r {:.1f} Hz  |  Γ {:.1f} Hz  |  D = 2Γ/f_r = {:.2f} ppm"
            "  |  G max {:.4g} mS  |  half {:.4g} mS  |  {} samples{}".format(
                f_res, gamma, 2.0 * gamma / f_res * 1e6, g_peak,
                g_edges[0], freq.size, notes))

    ###########################################################################
    def closeEvent(self, event):
        # stopping the timer is what makes a closed dialog free: no tick, no
        # buffer read, no redraw
        self._timer.stop()
        event.accept()
