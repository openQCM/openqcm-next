"""
Raw Data View: live amplitude and phase sweeps, one tab per overtone, with the
resonance peak and the dissipation band drawn on top.

Two properties are deliberate, and both come from the design that was proven on
openQCM Q-1:

*It pulls, nobody pushes.* The dialog owns a timer and asks the acquisition
object for its buffers. There is no set_data(), no signal from the worker, no
registration. So when the dialog is closed it costs exactly nothing -- there is
no code path left running -- and the acquisition never waits on the GUI.

*It reads memory only.* Never a file. The sweep dump under sweep_data/ is a
separate development tool; deleting it entirely leaves this dialog working and
unchanged, because the two share no state and no code.

The analysis is recomputed here, in the GUI thread, from core/resonance.py --
the same function the acquisition measures with, at full sample resolution, so
the band drawn is the band logged. Only the arrays handed to the plot are
decimated, exactly as the main window already does for its sweep panel.
"""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.common.logger import Logger as Log
from openQCM.ui import theme

TAG = "[RawDataView]"

# How often the dialog asks the acquisition object for fresh buffers.
REFRESH_MS = 300

# A sweep wider than this many points would mean a spline of that size in the
# GUI thread on every tick. The fit is skipped rather than shortened: shortening
# it would silently draw a band that differs from the measured one, and a viewer
# that quietly disagrees with the instrument is the thing this whole module
# exists to prevent.
MAX_FIT_POINTS = 200000

# Savitzky-Golay window and spline smoothing factor per overtone, read from the
# very constants the acquisition reads (getMultiscanParameters_5Mhz/_10Mhz).
# Today every entry resolves to Constants.SG_WINDOW_SIZE / SPLINE_FACTOR, but
# reading them individually means the dialog follows if one is ever retuned.
_FIT_5MHZ = [
    (Constants.SG_window_size5_fundamental, Constants.Spline_factor5_fundamental),
    (Constants.SG_window_size5_3th_overtone, Constants.Spline_factor5_3th_overtone),
    (Constants.SG_window_size5_5th_overtone, Constants.Spline_factor5_5th_overtone),
    (Constants.SG_window_size5_7th_overtone, Constants.Spline_factor5_7th_overtone),
    (Constants.SG_window_size5_9th_overtone, Constants.Spline_factor5_9th_overtone),
]
_FIT_10MHZ = [
    (Constants.SG_window_size10_fundamental, Constants.Spline_factor10_fundamental),
    (Constants.SG_window_size10_3th_overtone, Constants.Spline_factor10_3th_overtone),
    (Constants.SG_window_size10_5th_overtone, Constants.Spline_factor10_5th_overtone),
]

OVERTONE_NAMES = ["Fundamental", "3rd overtone", "5th overtone",
                  "7th overtone", "9th overtone"]


def _fit_parameters(overtone_index, centre_frequency):
    """(sg_window, spline_factor) for this overtone.

    The sensor family is decided from the sweep itself -- dividing the centre of
    the sweep by the harmonic order lands near the fundamental -- so the dialog
    needs neither the calibration file nor anything from the host.
    """
    order = 2 * overtone_index + 1
    fundamental = float(centre_frequency) / order
    table = _FIT_5MHZ if fundamental < 8e6 else _FIT_10MHZ
    if overtone_index < len(table):
        return table[overtone_index]
    return Constants.SG_WINDOW_SIZE, Constants.SPLINE_FACTOR


def _as_sweep(values):
    """The buffers hold 0 until the first sweep lands; return None until then."""
    if values is None or np.isscalar(values):
        return None
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 3:
        return None
    if not np.isfinite(array).any():
        return None
    return array


class _OvertoneTab(QtWidgets.QWidget):
    """One tab: amplitude over phase, X axes linked, peak and band overlaid."""

    def __init__(self, overtone_index, theme_name, parent=None):
        super(_OvertoneTab, self).__init__(parent)
        self._index = overtone_index
        palette = theme.PLOT[theme_name]
        colour = Constants.plot_color_multi[
            overtone_index % len(Constants.plot_color_multi)]

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.info = QtWidgets.QLabel("Waiting for data...")
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(palette["bg"])
        layout.addWidget(self.canvas, stretch=1)

        self.plt_amp = self.canvas.addPlot(row=0, col=0)
        self.plt_phase = self.canvas.addPlot(row=1, col=0)
        self.plt_amp.setTitle("Amplitude sweep", color=palette["title"])
        self.plt_phase.setTitle("Phase sweep", color=palette["title"])
        self.plt_amp.setLabel("left", "Amplitude", units="dB",
                              color=palette["title"])
        self.plt_phase.setLabel("left", "Phase", units="deg",
                                color=palette["title"])
        self.plt_phase.setLabel("bottom", "Frequency", units="Hz",
                                color=palette["title"])
        for plot in (self.plt_amp, self.plt_phase):
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            # grid off by default, as everywhere else in this GUI
            plot.showGrid(x=False, y=False)
            # silences the PlotItem menu AND the ViewBox one; the dialog
            # installs its own on the scene
            plot.setMenuEnabled(False)
            plot.getViewBox().setMenuEnabled(False)

        # zoom and pan stay in step between the two panels
        self.plt_phase.setXLink(self.plt_amp)

        legend = self.plt_amp.addLegend(offset=(10, 10))

        self.samples = pg.ScatterPlotItem(
            size=3, pen=None, brush=pg.mkBrush(palette["curve"]))
        self.plt_amp.addItem(self.samples)
        legend.addItem(self.samples, "samples")

        self.fit = self.plt_amp.plot(
            pen=pg.mkPen(color=colour, width=Constants.plot_line_width))
        legend.addItem(self.fit, "filtered + spline")

        self.band = pg.LinearRegionItem(
            values=[0, 0], movable=False,
            brush=pg.mkBrush(76, 175, 80, 40),
            pen=pg.mkPen("#4caf50", width=1, style=QtCore.Qt.DashLine))
        self.band.setZValue(-10)
        self.band.setVisible(False)
        self.plt_amp.addItem(self.band)

        self.threshold = pg.InfiniteLine(
            pos=0, angle=0, movable=False,
            pen=pg.mkPen("#4caf50", width=1, style=QtCore.Qt.DotLine))
        self.threshold.setVisible(False)
        self.plt_amp.addItem(self.threshold)

        self.peak = pg.ScatterPlotItem(
            size=11, symbol="d", pen=pg.mkPen("#ffffff", width=1.2),
            brush=pg.mkBrush("#f44336"))
        self.plt_amp.addItem(self.peak)

        self.phase = self.plt_phase.plot(
            pen=pg.mkPen(color=colour, width=Constants.plot_line_width))

    def plots(self):
        return (self.plt_amp, self.plt_phase)

    def clear_overlay(self):
        self.band.setVisible(False)
        self.threshold.setVisible(False)
        self.peak.setData(x=[], y=[])


class RawDataViewDialog(QtWidgets.QDialog):
    """Non-modal live view of the raw sweeps, one tab per overtone."""

    def __init__(self, host, theme_name="light", parent=None):
        super(RawDataViewDialog, self).__init__(parent)
        self._host = host
        self._theme = theme_name if theme_name in theme.PLOT else "light"

        self.setWindowTitle("Raw Data View - live sweep")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(720, 560)
        self.resize(1000, 720)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self._tabs = QtWidgets.QTabWidget()
        layout.addWidget(self._tabs)

        self._panes = []
        for idx in range(len(Constants.overtone_dummy)):
            pane = _OvertoneTab(idx, self._theme)
            name = (OVERTONE_NAMES[idx] if idx < len(OVERTONE_NAMES)
                    else "overtone {}".format(2 * idx + 1))
            self._tabs.addTab(pane, name)
            self._panes.append(pane)
            # one connection per scene, then a hit test to find the plot: the
            # plots of one GraphicsLayoutWidget share a single QGraphicsScene,
            # so connecting per plot would fire the menu once per plot
            pane.canvas.scene().sigMouseClicked.connect(self._on_scene_clicked)

        self._grid_on = {}

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
        # only the visible tab is analysed: one spline per tick, not one per
        # overtone. Switching tab picks the new one up on the next tick.
        self._update_pane(worker, index)

    def _update_pane(self, worker, index):
        pane = self._panes[index]
        try:
            freq = _as_sweep(worker.get_F_Sweep_values_buffer(index))
            amp = _as_sweep(worker.get_A_values_buffer(index))
            phase = _as_sweep(worker.get_P_values_buffer(index))
        except (AttributeError, IndexError, TypeError) as error:
            # a worker that has been stopped, or a buffer list not yet sized
            Log.d(TAG, "buffers unavailable: {}".format(error))
            return

        if freq is None or amp is None or freq.size != amp.size:
            pane.info.setText("Waiting for data...")
            return

        step = max(1, int(Constants.FREQ_STEP_PLOT))
        pane.samples.setData(x=freq[::step], y=amp[::step])
        if phase is not None and phase.size == freq.size:
            pane.phase.setData(x=freq[::step], y=phase[::step])

        # Same points the acquisition fits: int(span) + 1 over the sweep's own
        # axis is exactly the spline_points the processes derive from the
        # calibration, so no parameter has to be plumbed across the processes.
        span = float(freq[-1] - freq[0])
        points = int(span) + 1
        if points < 10:
            pane.clear_overlay()
            pane.info.setText("Sweep too narrow to fit ({} points)".format(points))
            return
        if points > MAX_FIT_POINTS:
            pane.clear_overlay()
            pane.info.setText(
                "Fit skipped: {} points exceeds the {} limit".format(
                    points, MAX_FIT_POINTS))
            return

        centre = 0.5 * (freq[0] + freq[-1])
        sg_window, spline_factor = _fit_parameters(index, centre)

        try:
            freq_fit, amp_fit, band = resonance.analyze_sweep(
                freq, amp, sg_window, Constants.SG_order, spline_factor,
                points, Constants.THRESHOLD_DB)
        except (ValueError, TypeError, IndexError) as error:
            # narrow on purpose: in Q-1 a bare `except Exception` here hid the
            # fact that the fit was allocating hundreds of megabytes
            pane.clear_overlay()
            pane.info.setText("Fit failed: {}".format(error))
            Log.w(TAG, "fit failed on overtone {}: {}".format(index, error))
            return

        pane.fit.setData(x=freq_fit[::step], y=amp_fit[::step])

        level = band.peak_value - Constants.THRESHOLD_DB
        pane.peak.setData(x=[band.peak_frequency], y=[band.peak_value])
        pane.band.setRegion([band.leading_frequency, band.trailing_frequency])
        pane.band.setVisible(True)
        pane.threshold.setValue(level)
        pane.threshold.setVisible(True)

        truncated = ""
        if band.err_left or band.err_right:
            sides = []
            if band.err_left:
                sides.append("left")
            if band.err_right:
                sides.append("right")
            truncated = "  |  BAND TRUNCATED ({})".format(", ".join(sides))

        pane.info.setText(
            "peak {:.1f} Hz  |  band {:.3f} Hz @ peak - {} dB  |  "
            "D = {:.9f}  |  {} samples{}".format(
                band.peak_frequency, band.bandwidth, Constants.THRESHOLD_DB,
                band.bandwidth / 1e6, freq.size, truncated))

    ###########################################################################
    # Right-click menu, matching the main window's
    ###########################################################################
    def _on_scene_clicked(self, event):
        if event.button() != QtCore.Qt.RightButton:
            return
        for pane in self._panes:
            for plot in pane.plots():
                box = plot.getViewBox()
                if box is not None and box.sceneBoundingRect().contains(
                        event.scenePos()):
                    event.accept()
                    self._show_plot_menu(plot, event.screenPos().toPoint())
                    return

    def _show_plot_menu(self, plot, screen_pos):
        menu = QtGui.QMenu(self)
        menu.addAction("Auto-scale", lambda: plot.enableAutoRange())
        menu.addAction("Reset zoom", lambda: plot.autoRange())
        box = plot.getViewBox()
        if box.state.get("mouseMode") == pg.ViewBox.RectMode:
            menu.addAction("Mouse: pan mode",
                           lambda: box.setMouseMode(pg.ViewBox.PanMode))
        else:
            menu.addAction("Mouse: select/zoom mode",
                           lambda: box.setMouseMode(pg.ViewBox.RectMode))
        menu.addSeparator()
        on = self._grid_on.get(plot, False)
        menu.addAction("Hide grid" if on else "Show grid",
                       lambda: self._set_grid(plot, not on))
        menu.addSeparator()
        menu.addAction("Export…", lambda: plot.scene().showExportDialog())
        menu.exec_(screen_pos)

    def _set_grid(self, plot, on):
        self._grid_on[plot] = on
        plot.showGrid(x=on, y=on, alpha=0.3)

    ###########################################################################
    def closeEvent(self, event):
        # stopping the timer is what makes a closed dialog free: no tick, no
        # buffer read, no fit
        self._timer.stop()
        event.accept()
