"""
Datalog View: opens a log the instrument wrote and plots it.

File > "Open Log…" (Ctrl/Cmd+O), the same place openQCM Q-1 v3.0 puts it. Q-1's
viewer draws resonance frequency and dissipation against a hh:mm:ss time axis;
this one adds the temperature channel, which NEXT logs in the same file and which
is what a drift usually has to be read against.

⚠️ THE FILE FORMAT HAS A TRAP, and it is the reason this module parses defensively
instead of reading columns by name. `FileStorage.CSVsave_Multi` always writes a
14-column header -- Date, Time, Relative_time, Temperature, then Frequency_0 /
Dissipation_0 through Frequency_4 / Dissipation_4 -- but the data rows **skip**
every overtone whose frequency or dissipation is zero. A 10 MHz sensor with three
overtones therefore produces 10-column rows under a 14-column header, verified on
`2026-Jul-17_10-22-23_multi_.csv`: 210 rows, all of length 10. Trusting the header
would read two pairs that are not there.

So the pairs are taken **positionally** from each row, and their harmonic order is
**derived** from the frequency itself (the ratio to the first pair rounds to 1, 3,
5, …) because the file does not record which overtones were selected. Rows whose
length disagrees with the rest of the file are counted and skipped rather than
guessed at.
"""

import csv
import datetime
import os
import sys

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from openQCM.core.constants import Constants
from openQCM.core import logAnalysis
from openQCM.common.logger import Logger as Log
from openQCM.ui import theme
from openQCM.ui.plotMenu import PlotMenu

TAG = "[DatalogView]"

COLOR_TEMPERATURE = "#7fc7e0"

# Number of leading metadata columns: Date, Time, Relative_time, Temperature.
META_COLUMNS = 4

# The reference is the mean of this many samples from the cursor, not a single
# point: one sample carries its own noise, and adjacent samples of a real run
# differ by a few Hz.
REFERENCE_SAMPLES = 5

# Height of the controls / temperature row. Small on purpose: the two shift
# panels are what the window is for.
TOP_ROW_HEIGHT = 190

# Where the two analysis windows start out: the first and the last tenth of the
# run. A guess, but the useful one -- an experiment is normally read as "what
# changed between the state it settled into and the state it ended in".
DEFAULT_WINDOW_FRACTION = 0.10

# The shaded bands. Green opens the run, amber closes it; both are drawn under
# the curves and over the background.
COLOR_WINDOW_INITIAL = (76, 175, 80)
COLOR_WINDOW_FINAL = (255, 152, 0)


class RelativeTimeAxis(pg.AxisItem):
    """Seconds since the start of the run, shown as h:mm:ss.

    Constants.DateAxis is not reused here: it interprets its values as epoch
    microseconds, and a log records the relative time already in seconds. Scaling
    the data by 1e6 to fit that axis would leave the x values in a unit that
    nothing else in this window uses.
    """

    def tickStrings(self, values, scale, spacing):
        out = []
        for value in values:
            try:
                out.append(str(datetime.timedelta(seconds=int(float(value)))))
            except (ValueError, OverflowError):
                out.append("")
        return out


class LogContents(object):
    """What was read out of a log file."""

    def __init__(self, path, time_s, temperature, series, skipped, columns):
        self.path = path
        self.time_s = time_s
        self.temperature = temperature
        # [(harmonic order, frequency array, dissipation array), ...]
        self.series = series
        self.skipped = skipped
        self.columns = columns

    @property
    def multi(self):
        return len(self.series) > 1

    @property
    def duration_s(self):
        if self.time_s.size < 2:
            return 0.0
        return float(self.time_s[-1] - self.time_s[0])


def read_log(path):
    """Parse a NEXT datalog. Raises ValueError if it is not one."""
    with open(path, "r") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise ValueError("the file is empty")

    header = [c.strip() for c in rows[0]]
    if "Relative_time" not in header:
        raise ValueError("not an openQCM NEXT datalog (no Relative_time column)")

    # The row length is what tells the truth about how many overtone pairs are
    # present; the header always claims five. Use the most common length and
    # count what disagrees.
    lengths = {}
    for row in rows[1:]:
        if row:
            lengths[len(row)] = lengths.get(len(row), 0) + 1
    if not lengths:
        raise ValueError("the file holds a header and no data")
    width = max(lengths, key=lambda k: lengths[k])
    if width < META_COLUMNS + 2:
        raise ValueError("rows have {} columns, too few for a datalog".format(width))
    pairs = (width - META_COLUMNS) // 2

    time_s, temperature, skipped = [], [], 0
    values = [[] for _ in range(pairs)]
    for row in rows[1:]:
        if len(row) != width:
            skipped += 1
            continue
        try:
            t = float(row[2])
            temp = float(row[3])
            pair_values = [(float(row[META_COLUMNS + 2 * i]),
                            float(row[META_COLUMNS + 2 * i + 1]))
                           for i in range(pairs)]
        except (ValueError, IndexError):
            skipped += 1
            continue
        time_s.append(t)
        temperature.append(temp)
        for i, pv in enumerate(pair_values):
            values[i].append(pv)

    if not time_s:
        raise ValueError("no row could be read")

    time_s = np.asarray(time_s, dtype=float)
    temperature = np.asarray(temperature, dtype=float)

    # Derive the harmonic order from the frequencies: the first pair is the
    # lowest one logged, and the ratio to it rounds to 1, 3, 5, ... The file does
    # not record which overtones were selected, so this is inferred, not read.
    series = []
    first_mean = None
    for i in range(pairs):
        arr = np.asarray(values[i], dtype=float)
        freq, diss = arr[:, 0], arr[:, 1]
        mean = float(np.nanmean(freq))
        if first_mean is None or first_mean <= 0:
            first_mean = mean
            order = 1
        else:
            order = int(round(mean / first_mean))
            if order % 2 == 0:          # only odd harmonics exist here
                order = max(1, order - 1)
        series.append((order, freq, diss))

    return LogContents(path, time_s, temperature, series, skipped, len(header))

class DataLogViewDialog(QtWidgets.QDialog):
    """Non-modal view of one logged run, with a movable reference point.

    Frequency and dissipation are shown as the shift from a reference the user
    chooses: five overtones on one absolute axis span 5 to 45 MHz against a signal
    of a few hundred Hz, so absolute values hide the only thing worth reading. The
    reference is taken at a draggable cursor, starts on the first sample, and is
    the mean of REFERENCE_SAMPLES points rather than one -- a single sample carries
    its own noise, and on a real run adjacent samples differ by a few Hz.

    Temperature keeps its own small panel, in absolute degrees: it is what a drift
    is read against, and a delta would make it less legible, not more.
    """

    def __init__(self, theme_name="light", parent=None):
        super(DataLogViewDialog, self).__init__(parent)
        self._theme = theme_name if theme_name in theme.PLOT else "light"
        palette = theme.PLOT[self._theme]
        # The main window sets the QSS on itself, not on the application, so a
        # dialog only inherits it while it is parented there. Applying it here too
        # keeps the overtone pills looking like the main window's either way.
        self.setStyleSheet(theme.qss(theme.palette(self._theme)))

        self.setWindowTitle("Datalog View")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(860, 620)
        self.resize(1120, 800)

        self._log = None
        self._curves = []            # [(freq curve, diss curve), ...]
        self._pills = []
        self._value_labels = []      # [(freq label, diss label), ...]
        self._cursors = []
        self._regions = {"initial": [], "final": []}   # one band per shift panel
        self._moving_region = False   # guards a band against its own twin
        self._reference_index = 0
        self._moving_cursor = False  # guards the two cursors against each other

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.info = QtWidgets.QLabel("No log loaded.")
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info)

        # ---------------------------------------------- top row: controls | temp
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)
        layout.addLayout(top)

        self._controls = QtWidgets.QGroupBox("Reference")
        self._controls.setObjectName("datalogControls")
        self._controls_layout = QtWidgets.QVBoxLayout(self._controls)
        self._controls_layout.setContentsMargins(8, 6, 8, 6)
        self._controls_layout.setSpacing(4)

        self.lbl_reference = QtWidgets.QLabel("drag the cursor to move the zero")
        self._controls_layout.addWidget(self.lbl_reference)

        # per-overtone reference values, filled in on load
        self._grid = QtWidgets.QGridLayout()
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(2)
        self._controls_layout.addLayout(self._grid)

        # the overtone pills, same widgets and same QSS property as the main
        # window's quick-select row
        self._pill_row = QtWidgets.QHBoxLayout()
        self._pill_row.setSpacing(3)
        self._pill_row.setContentsMargins(0, 4, 0, 0)
        self._controls_layout.addLayout(self._pill_row)

        self.btn_analysis = QtWidgets.QPushButton("Two-window analysis")
        self.btn_analysis.setCheckable(True)
        self.btn_analysis.setFixedHeight(24)
        self.btn_analysis.setToolTip(
            "Compare a starting stretch of the run with a final one")
        self.btn_analysis.toggled.connect(self._set_analysis_visible)
        self._controls_layout.addWidget(self.btn_analysis)
        self._controls_layout.addStretch(1)
        top.addWidget(self._controls, stretch=3)

        self.temp_canvas = pg.GraphicsLayoutWidget()
        self.temp_canvas.setBackground(palette["bg"])
        self.temp_canvas.setFixedHeight(TOP_ROW_HEIGHT)
        top.addWidget(self.temp_canvas, stretch=4)
        self._controls.setFixedHeight(TOP_ROW_HEIGHT)

        self.plt_temp = self.temp_canvas.addPlot(
            row=0, col=0,
            axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})
        self.plt_temp.setTitle("Temperature", color=palette["title"])
        self.plt_temp.setLabel("left", "T", units="°C", color=palette["title"])

        # ------------------------------------------------- the two shift panels
        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(palette["bg"])

        # The analysis pane sits beside the plots and starts hidden: drawing the
        # run is this window's first job, and "what changed between these two
        # stretches" is a second question not every reader is asking.
        self._body = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self._body.addWidget(self.canvas)
        self._body.setStretchFactor(0, 1)
        self._body.setChildrenCollapsible(False)
        layout.addWidget(self._body, stretch=1)

        self.plt_freq = self.canvas.addPlot(
            row=0, col=0,
            axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})
        self.plt_diss = self.canvas.addPlot(
            row=1, col=0,
            axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})
        self.plt_freq.setTitle("Resonance frequency", color=palette["title"])
        self.plt_diss.setTitle("Dissipation", color=palette["title"])
        self.plt_freq.setLabel("left", "Frequency shift", units="Hz",
                               color=palette["title"])
        self.plt_diss.setLabel("left", "Dissipation shift", units="ppm",
                               color=palette["title"])
        self.plt_diss.setLabel("bottom", "Time (h:mm:ss)", color=palette["title"])

        for plot in self.plots():
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            plot.getAxis("bottom").enableAutoSIPrefix(False)
            plot.showGrid(x=False, y=False)
            plot.addLegend(offset=(10, 10))

        self.plt_diss.setXLink(self.plt_freq)
        self.plt_temp.setXLink(self.plt_freq)

        self._menu = PlotMenu(self)
        self._menu.attach(self.plots())

        self._build_analysis_panel()

    # ------------------------------------------------------------------ #
    def _build_analysis_panel(self):
        """The report pane. Empty until a log is loaded and the bands exist."""
        self._analysis = QtWidgets.QGroupBox("Two-window analysis")
        self._analysis.setObjectName("datalogAnalysis")
        box = QtWidgets.QVBoxLayout(self._analysis)
        box.setContentsMargins(8, 6, 8, 6)
        box.setSpacing(4)

        hint = QtWidgets.QLabel(
            "Drag the green and amber bands on the plots to choose the two "
            "stretches to compare.")
        hint.setWordWrap(True)
        box.addWidget(hint)

        self.txt_analysis = QtWidgets.QTextEdit()
        self.txt_analysis.setObjectName("datalogReport")   # theme.qss console rule
        self.txt_analysis.setReadOnly(True)
        self.txt_analysis.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        mono = QtGui.QFont("Menlo" if sys.platform == "darwin" else
                           "Consolas" if sys.platform.startswith("win") else
                           "Monospace")
        mono.setStyleHint(QtGui.QFont.TypeWriter)
        mono.setPointSize(10)
        self.txt_analysis.setFont(mono)
        box.addWidget(self.txt_analysis, stretch=1)

        self._analysis.setMinimumWidth(340)
        self._analysis.setVisible(False)
        self._body.addWidget(self._analysis)
        self._body.setStretchFactor(1, 0)

    def plots(self):
        return (self.plt_freq, self.plt_diss, self.plt_temp)

    ###########################################################################
    def load(self, path):
        """Read and draw ``path``. True if it drew."""
        try:
            log = read_log(path)
        except (OSError, ValueError) as error:
            self.info.setText("Could not read the log: {}".format(error))
            Log.w(TAG, "could not read {}: {}".format(path, error))
            return False

        self._log = log
        self._clear_view()

        for position, (order, freq, diss) in enumerate(log.series):
            # each panel keeps its own family: blue for frequency, brown for
            # dissipation, as in the main window
            colour_f = Constants.plot_color_multi[
                position % len(Constants.plot_color_multi)]
            colour_d = Constants.plot_color_multi_diss[
                position % len(Constants.plot_color_multi_diss)]
            name = "F{}".format(order)
            self._curves.append((
                self.plt_freq.plot(pen=pg.mkPen(color=colour_f,
                                                width=Constants.plot_line_width),
                                   name=name),
                self.plt_diss.plot(pen=pg.mkPen(color=colour_d,
                                                width=Constants.plot_line_width),
                                   name=name)))
            self._add_control_row(position, order, colour_f, colour_d)

        self.plt_temp.plot(log.time_s, log.temperature,
                           pen=pg.mkPen(color=COLOR_TEMPERATURE,
                                        width=Constants.plot_line_width))

        # One reference cursor, drawn on both shift panels and kept in step. It is
        # movable and snaps to a sample, because the reference is a mean of real
        # samples and a cursor resting between two of them would say otherwise.
        for plot in (self.plt_freq, self.plt_diss):
            line = pg.InfiniteLine(
                pos=log.time_s[0], angle=90, movable=True,
                pen=pg.mkPen("#f44336", width=1, style=QtCore.Qt.DashLine),
                hoverPen=pg.mkPen("#ff8a80", width=2))
            line.setZValue(50)
            line.sigPositionChanged.connect(self._on_cursor_moved)
            plot.addItem(line)
            self._cursors.append(line)

        self._build_windows(log.time_s)

        self.setWindowTitle("Datalog View - {}".format(os.path.basename(path)))
        orders = ", ".join("F{}".format(o) for o, _f, _d in log.series)
        text = "{}  |  {} points  |  {}  |  {}".format(
            os.path.basename(path), log.time_s.size,
            str(datetime.timedelta(seconds=int(log.duration_s))),
            "overtones {}".format(orders) if log.multi
            else "single overtone {}".format(orders))
        if log.skipped:
            text += "  |  {} row(s) skipped, unexpected width".format(log.skipped)
        self.info.setText(text)

        self._set_reference(0)
        return True

    ###########################################################################
    def _clear_view(self):
        for plot in self.plots():
            plot.clear()
        self._curves = []
        self._cursors = []
        # plot.clear() already took the band items off the scene
        self._regions = {"initial": [], "final": []}
        self._value_labels = []
        self.txt_analysis.setPlainText("")
        for pill in self._pills:
            pill.setParent(None)
        self._pills = []
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    @staticmethod
    def _swatch(colour):
        label = QtWidgets.QLabel()
        label.setFixedSize(11, 11)
        label.setStyleSheet("background: rgb({},{},{}); border-radius: 2px;"
                            .format(*colour[:3]))
        return label

    def _add_control_row(self, position, order, colour_f, colour_d):
        """Name and the two reference values, each beside its own curve colour.

        Two swatches, not one: the panels no longer share a colour, so a single
        swatch would claim a curve it does not match.
        """
        row = self._grid.rowCount()
        name = QtWidgets.QLabel("F{}".format(order))
        freq_value = QtWidgets.QLabel("-")
        diss_value = QtWidgets.QLabel("-")
        for label in (freq_value, diss_value):
            label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self._grid.addWidget(self._swatch(colour_f), row, 0)
        self._grid.addWidget(name, row, 1)
        self._grid.addWidget(freq_value, row, 2)
        self._grid.addWidget(self._swatch(colour_d), row, 3)
        self._grid.addWidget(diss_value, row, 4)
        self._value_labels.append((freq_value, diss_value))

        pill = QtWidgets.QPushButton("F{}".format(order))
        pill.setProperty("overtoneBtn", True)     # the main window's QSS rule
        pill.setCheckable(True)
        pill.setChecked(True)
        pill.setFixedHeight(24)
        pill.setToolTip("Show or hide overtone F{}".format(order))
        pill.toggled.connect(
            lambda checked, i=position: self._set_series_visible(i, checked))
        self._pill_row.addWidget(pill)
        self._pills.append(pill)

    def _set_series_visible(self, position, visible):
        for curve in self._curves[position]:
            curve.setVisible(bool(visible))

    ###########################################################################
    # Two-window analysis
    ###########################################################################
    def _build_windows(self, time_s):
        """One draggable band per window, mirrored on both shift panels.

        Mirrored rather than drawn once: the panels are x-linked, so a band on
        only one of them would leave the other reader guessing which stretch the
        report is about. The twins are kept in step the same way the reference
        cursors are, through a re-entry guard.
        """
        if time_s.size < 2:
            return
        first, last = float(time_s[0]), float(time_s[-1])
        span = (last - first) * DEFAULT_WINDOW_FRACTION
        bounds = {"initial": (first, first + span),
                  "final": (last - span, last)}
        colours = {"initial": COLOR_WINDOW_INITIAL, "final": COLOR_WINDOW_FINAL}

        for key in ("initial", "final"):
            r, g, b = colours[key]
            for plot in (self.plt_freq, self.plt_diss):
                band = pg.LinearRegionItem(
                    values=bounds[key], movable=True,
                    brush=pg.mkBrush(r, g, b, 38),
                    pen=pg.mkPen(r, g, b, 160))
                band.setZValue(-10)          # under the curves, over the panel
                band.sigRegionChanged.connect(
                    lambda item, k=key: self._on_window_changed(k, item))
                plot.addItem(band)
                self._regions[key].append(band)

        # a band is created visible; the panel may not be, and the two travel
        # together
        self._set_analysis_visible(self.btn_analysis.isChecked())

    def _set_analysis_visible(self, visible):
        """Show or hide the report pane and the bands together.

        Together on purpose: bands with no report say nothing, and a report the
        reader cannot see the extent of is worse than no report.
        """
        visible = bool(visible)
        self._analysis.setVisible(visible)
        for bands in self._regions.values():
            for band in bands:
                band.setVisible(visible)
        if visible:
            # the splitter would otherwise hand the pane half the window on its
            # size hint; the plots are what the window is for
            pane = max(self._analysis.minimumWidth(), 360)
            self._body.setSizes([max(self.width() - pane - 24, 400), pane])
            self._refresh_analysis()

    def _on_window_changed(self, key, item):
        if self._moving_region:
            return
        self._moving_region = True
        try:
            for band in self._regions[key]:
                if band is not item:
                    band.setRegion(item.getRegion())
        finally:
            self._moving_region = False
        self._refresh_analysis()

    def _window_bounds(self, key):
        """(start, duration) in seconds for one band."""
        bands = self._regions.get(key)
        if not bands:
            return None
        lo, hi = sorted(float(v) for v in bands[0].getRegion())
        return lo, hi - lo

    def _refresh_analysis(self):
        """Recompute the report from core/logAnalysis, never from here.

        Dissipation is scaled to ppm before it goes in, so the report carries the
        unit the panel is drawn in. The reference cursor is deliberately NOT
        applied: shift, std and Hadamard all survive a constant subtracted from
        the series, so the report says the same thing wherever the zero sits --
        which is what lets the cursor stay free.
        """
        # the button, not the widget: QWidget.isVisible() is about what is on
        # screen, and it is False for a dialog that has not been shown yet
        if self._log is None or not self.btn_analysis.isChecked():
            return
        initial, final = self._window_bounds("initial"), self._window_bounds("final")
        if initial is None or final is None:
            return
        series = [(order, freq, diss * 1e6)
                  for order, freq, diss in self._log.series]
        report = logAnalysis.analyse(self._log.time_s, series, initial, final)
        self.txt_analysis.setPlainText(logAnalysis.format_report(report))

    ###########################################################################
    def _on_cursor_moved(self, line):
        if self._moving_cursor or self._log is None:
            return
        index = int(np.abs(self._log.time_s - float(line.value())).argmin())
        if index == self._reference_index:
            # still the same sample: snap the line back onto it and stop
            self._sync_cursors(self._log.time_s[index])
            return
        self._set_reference(index)

    def _sync_cursors(self, x):
        self._moving_cursor = True
        try:
            for line in self._cursors:
                line.setValue(float(x))
        finally:
            self._moving_cursor = False

    def _set_reference(self, index):
        """Re-zero every curve on the mean of REFERENCE_SAMPLES from ``index``."""
        log = self._log
        if log is None or not self._curves:
            return
        index = max(0, min(int(index), log.time_s.size - 1))
        self._reference_index = index
        window = slice(index, min(index + REFERENCE_SAMPLES, log.time_s.size))

        for position, (order, freq, diss) in enumerate(log.series):
            ref_f = float(np.nanmean(freq[window]))
            ref_d = float(np.nanmean(diss[window]))
            curve_f, curve_d = self._curves[position]
            curve_f.setData(log.time_s, freq - ref_f)
            # ppm, as the main window's dissipation readout card reports it
            curve_d.setData(log.time_s, (diss - ref_d) * 1e6)
            label_f, label_d = self._value_labels[position]
            label_f.setText("{:.2f} Hz".format(ref_f))
            label_d.setText("{:.2f} ppm".format(ref_d * 1e6))

        self._sync_cursors(log.time_s[index])
        used = window.stop - window.start
        self.lbl_reference.setText(
            "zero at {}  (sample {} of {}, mean of {})".format(
                str(datetime.timedelta(seconds=int(log.time_s[index]))),
                index + 1, log.time_s.size, used))
