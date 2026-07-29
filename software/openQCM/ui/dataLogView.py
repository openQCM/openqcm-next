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

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from openQCM.core.constants import Constants
from openQCM.common.logger import Logger as Log
from openQCM.ui import theme
from openQCM.ui.plotMenu import PlotMenu

TAG = "[DatalogView]"

COLOR_TEMPERATURE = "#7fc7e0"

# Number of leading metadata columns: Date, Time, Relative_time, Temperature.
META_COLUMNS = 4


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
    """Non-modal view of one logged run."""

    def __init__(self, theme_name="light", parent=None):
        super(DataLogViewDialog, self).__init__(parent)
        self._theme = theme_name if theme_name in theme.PLOT else "light"
        palette = theme.PLOT[self._theme]

        self.setWindowTitle("Datalog View")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(760, 560)
        self.resize(1040, 760)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.info = QtWidgets.QLabel("No log loaded.")
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(palette["bg"])
        layout.addWidget(self.canvas, stretch=1)

        self.plt_freq = self.canvas.addPlot(
            row=0, col=0, axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})
        self.plt_diss = self.canvas.addPlot(
            row=1, col=0, axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})
        self.plt_temp = self.canvas.addPlot(
            row=2, col=0, axisItems={"bottom": RelativeTimeAxis(orientation="bottom")})

        self.plt_freq.setTitle("Resonance frequency", color=palette["title"])
        self.plt_diss.setTitle("Dissipation", color=palette["title"])
        self.plt_temp.setTitle("Temperature", color=palette["title"])
        self.plt_freq.setLabel("left", "Frequency shift", units="Hz",
                               color=palette["title"])
        self.plt_diss.setLabel("left", "Dissipation", color=palette["title"])
        self.plt_temp.setLabel("left", "Temperature", units="°C",
                               color=palette["title"])
        self.plt_temp.setLabel("bottom", "Time (h:mm:ss)", color=palette["title"])

        for plot in self.plots():
            for axis in ("left", "bottom"):
                plot.getAxis(axis).setPen(palette["axis"])
                plot.getAxis(axis).setTextPen(palette["axis"])
            plot.getAxis("bottom").enableAutoSIPrefix(False)
            plot.showGrid(x=False, y=False)
            plot.addLegend(offset=(10, 10))

        # one time base for the three panels
        self.plt_diss.setXLink(self.plt_freq)
        self.plt_temp.setXLink(self.plt_freq)

        self._menu = PlotMenu(self)
        self._menu.attach(self.plots())

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

        for plot in self.plots():
            plot.clear()

        for position, (order, freq, diss) in enumerate(log.series):
            colour = Constants.plot_color_multi[
                position % len(Constants.plot_color_multi)]
            pen = pg.mkPen(color=colour, width=Constants.plot_line_width)
            # Frequency is drawn as the SHIFT from the first logged sample, not
            # as the absolute value. Five overtones on one absolute axis span
            # 5 to 45 MHz, against a signal of a few hundred Hz: the panel then
            # shows five flat lines and hides the only thing worth reading. The
            # starting frequency is not lost -- it goes in the legend, so the
            # panel carries both. Same reason the main window has SET REF.
            start = float(freq[0]) if freq.size else 0.0
            self.plt_freq.plot(log.time_s, freq - start, pen=pen,
                               name="F{}  (from {:.0f} Hz)".format(order, start))
            self.plt_diss.plot(log.time_s, diss,
                               pen=pg.mkPen(color=colour,
                                            width=Constants.plot_line_width),
                               name="F{}".format(order))

        self.plt_temp.plot(log.time_s, log.temperature,
                           pen=pg.mkPen(color=COLOR_TEMPERATURE,
                                        width=Constants.plot_line_width),
                           name="temperature")

        self.setWindowTitle("Datalog View - {}".format(os.path.basename(path)))
        orders = ", ".join("F{}".format(o) for o, _f, _d in log.series)
        text = ("{}  |  {} points  |  {}  |  {}".format(
            os.path.basename(path), log.time_s.size,
            str(datetime.timedelta(seconds=int(log.duration_s))),
            "overtones {}".format(orders) if log.multi else "single overtone {}"
            .format(orders)))
        if log.skipped:
            # said out loud: a row of the wrong width is the format trap in the
            # module docstring showing up, not noise to hide
            text += "  |  {} row(s) skipped, unexpected width".format(log.skipped)
        self.info.setText(text)
        return True
