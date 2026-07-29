"""
Peak Data View: what the Peak Detection actually saw.

Ported from openQCM Q-1 v3.0 (`ui/calibrationPlot.py`), extended from Q-1's plots
to NEXT's five overtones. It answers one question -- "is that really a resonance,
or did the detector latch onto a bump in the baseline?" -- and it answers it by
drawing the three things at once: the raw full-span sweep, the polynomial baseline
that was subtracted from it, and the corrected curve the peaks were found in.

It is a **snapshot, not a live view**. Peak Detection runs once and writes two
files; this window reads them when it opens and does not poll. So, unlike Raw Data
View, reading files is the right thing here -- there is nothing in memory to read,
and the files are the record of the calibration the instrument is currently using.

⚠️ The baseline is recomputed here, from `Constants.BASELINE_POLY_ORDER`, on the
same arrays and with the same estimator the detection used. That is the only way
to show a corrected curve, since only the peak frequencies are stored, not the
correction. It also means this window is wrong the moment the two orders differ --
hence the shared constant rather than a literal.

⚠️ `PeakFrequencies.txt` holds the amplitude peak twice (`np.column_stack([f, f])`
in Calibration.py), not amplitude and phase. The phase peak is therefore not
recorded anywhere and has to be re-derived here, as the maximum of the corrected
phase within PHASE_PEAK_HALF_WINDOW of each amplitude peak. Where the two markers
disagree by more than a few kHz, the resonance is worth a second look -- that
disagreement is the point of drawing both.
"""

import os

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from openQCM.core.constants import Constants
from openQCM.common.logger import Logger as Log
from openQCM.ui import theme
from openQCM.ui.plotMenu import PlotMenu

TAG = "[PeakDataView]"

# Same two accents the main window uses, so a curve means the same thing in both.
COLOR_BASELINE = "#DD8E6B"      # brown, as Dissipation
COLOR_PHASE = "#008EC0"         # blue, as Phase / Frequency
PEAK_FILL = (255, 0, 0, 220)
PEAK_BORDER = "#ffffff"

# Half-width of the window searched for the phase peak around each amplitude peak.
# Wide enough to catch the phase maximum of a resonance the detector accepted,
# narrow enough not to wander into the neighbouring overtone: the closest pair on a
# 5 MHz sensor is 10 MHz apart.
PHASE_PEAK_HALF_WINDOW = 200000.0

# Drawing order: raw at the back, then the baseline over it, the corrected curve
# over that, and the peak markers in front of everything.
Z_RAW, Z_BASELINE, Z_CORRECTED, Z_PEAK = 0, 5, 10, 20


def _harmonic(index):
    """1 for the fundamental, 3 for the next, ... -- what the label says."""
    return 2 * index + 1


def _qcm_type(fundamental):
    if 4e6 < fundamental < 6e6:
        return "5 MHz QCM"
    if 9e6 < fundamental < 11e6:
        return "10 MHz QCM"
    return "unknown sensor"


def latest_calibration_path():
    """The more recently written of the two calibration files, or None.

    Peak Detection writes whichever matches the sensor, and both may exist from
    different sessions, so the file to trust is the newest one rather than a fixed
    choice.
    """
    newest, newest_mtime = None, -1.0
    for candidate in (Constants.csv_calibration_path,
                      Constants.csv_calibration_path10):
        try:
            mtime = os.path.getmtime(candidate)
        except OSError:
            continue
        if mtime > newest_mtime:
            newest, newest_mtime = candidate, mtime
    return newest


class PeakDataViewDialog(QtWidgets.QDialog):
    """Non-modal snapshot of the last Peak Detection."""

    def __init__(self, theme_name="light", parent=None):
        super(PeakDataViewDialog, self).__init__(parent)
        self._theme = theme_name if theme_name in theme.PLOT else "light"
        palette = theme.PLOT[self._theme]

        self.setWindowTitle("Peak Data View - last Peak Detection")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(720, 520)
        self.resize(1040, 720)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.info = QtWidgets.QLabel("No calibration data loaded.")
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(palette["bg"])
        layout.addWidget(self.canvas, stretch=1)

        self.plt_amp = self.canvas.addPlot(row=0, col=0)
        self.plt_phase = self.canvas.addPlot(row=1, col=0)
        self.plt_amp.setTitle("Amplitude", color=palette["title"])
        self.plt_phase.setTitle("Phase", color=palette["title"])
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
            plot.showGrid(x=False, y=False)
            # 100001 samples per channel: clip to the view and downsample by peak,
            # or panning a full-span sweep is visibly slow. 'peak' keeps the
            # extremes, which is exactly what must not be smoothed away here.
            plot.setClipToView(True)
            plot.setDownsampling(mode="peak")
            plot.addLegend(offset=(10, 10))

        self.plt_phase.setXLink(self.plt_amp)

        # the shared right-click menu, as on every other plot panel
        self._menu = PlotMenu(self)
        self._menu.attach((self.plt_amp, self.plt_phase))

        self._curve_colour = palette["curve"]
        self._items = []

    ###########################################################################
    def load(self, calibration_path, peaks_path):
        """Read both files, correct the baseline and draw. True if it drew."""
        try:
            calibration = np.loadtxt(calibration_path)
            # atleast_2d so a single detected peak still has a row axis
            peaks = np.atleast_2d(np.loadtxt(peaks_path))
        except (OSError, ValueError) as error:
            self.info.setText("Could not read the calibration data: {}".format(error))
            Log.w(TAG, "could not read calibration data: {}".format(error))
            return False

        if calibration.ndim != 2 or calibration.shape[1] < 3:
            self.info.setText("Calibration file has no frequency/amplitude/phase "
                              "columns.")
            return False

        freq = calibration[:, 0]
        raw_mag = calibration[:, 1]
        raw_phase = calibration[:, 2]
        # column 1 duplicates column 0, so only the first is read; see the module
        # docstring
        peak_freqs = peaks[:, 0]

        order = Constants.BASELINE_POLY_ORDER
        baseline_mag = np.polyval(np.polyfit(freq, raw_mag, order), freq)
        baseline_phase = np.polyval(np.polyfit(freq, raw_phase, order), freq)
        corrected_mag = raw_mag - baseline_mag
        corrected_phase = raw_phase - baseline_phase

        # An empty overtone slot is written as 0, not omitted, so it has to be
        # filtered rather than trusted.
        valid = [(i, f) for i, f in enumerate(peak_freqs) if f > 0]
        if not valid:
            self.info.setText("The peak file holds no detected peak.")
            return False

        self._draw(freq, raw_mag, raw_phase, baseline_mag, baseline_phase,
                   corrected_mag, corrected_phase, valid)

        fundamental = valid[0][1]
        self.info.setText(
            "{}  |  {} peak(s) detected  |  baseline: polynomial of order {}  "
            "|  {}".format(_qcm_type(fundamental), len(valid), order,
                           os.path.basename(calibration_path)))
        return True

    def _draw(self, freq, raw_mag, raw_phase, baseline_mag, baseline_phase,
              corrected_mag, corrected_phase, valid):
        for plot in (self.plt_amp, self.plt_phase):
            plot.clear()

        raw_pen = pg.mkPen(None)
        baseline_pen = pg.mkPen(color=COLOR_BASELINE, width=1)
        peak_brush = pg.mkBrush(*PEAK_FILL)
        peak_pen = pg.mkPen(PEAK_BORDER, width=2)
        label_colour = theme.PLOT[self._theme]["title"]
        muted = (150, 150, 150) if self._theme == "dark" else (140, 140, 140)
        phase_muted = (127, 199, 224)

        indices = [i for i, _f in valid]
        peak_x = np.array([f for _i, f in valid], dtype=float)
        # sample both corrected channels at the detected frequency
        at = [int(np.abs(freq - f).argmin()) for f in peak_x]
        peak_amp = corrected_mag[at]
        peak_phase_at_amp = corrected_phase[at]

        # ---------------------------------------------------------- amplitude
        self._scatter(self.plt_amp, freq, raw_mag, muted, raw_pen, Z_RAW,
                      "raw sweep")
        self.plt_amp.plot(freq, baseline_mag, pen=baseline_pen,
                          name="baseline (poly {})".format(
                              Constants.BASELINE_POLY_ORDER),
                          skipFiniteCheck=True).setZValue(Z_BASELINE)
        self.plt_amp.plot(freq, corrected_mag,
                          pen=pg.mkPen(color=self._curve_colour, width=2),
                          name="baseline corrected",
                          skipFiniteCheck=True).setZValue(Z_CORRECTED)
        marker = pg.ScatterPlotItem(x=peak_x, y=peak_amp, symbol="o", size=12,
                                    brush=peak_brush, pen=peak_pen)
        marker.setZValue(Z_PEAK)
        self.plt_amp.addItem(marker)
        if self.plt_amp.legend is not None:
            self.plt_amp.legend.addItem(marker, "detected peak")
        self._label_peaks(self.plt_amp, indices, peak_x, peak_amp, label_colour)

        # -------------------------------------------------------------- phase
        self._scatter(self.plt_phase, freq, raw_phase, phase_muted, raw_pen,
                      Z_RAW, "raw sweep")
        self.plt_phase.plot(freq, baseline_phase, pen=baseline_pen,
                            name="baseline (poly {})".format(
                                Constants.BASELINE_POLY_ORDER),
                            skipFiniteCheck=True).setZValue(Z_BASELINE)
        self.plt_phase.plot(freq, corrected_phase,
                            pen=pg.mkPen(color=COLOR_PHASE, width=2),
                            name="baseline corrected",
                            skipFiniteCheck=True).setZValue(Z_CORRECTED)
        # where the amplitude peak sits in the phase channel: the reference the
        # phase peak below is compared against
        ref = pg.ScatterPlotItem(x=peak_x, y=peak_phase_at_amp, symbol="o",
                                 size=12, brush=peak_brush, pen=peak_pen)
        ref.setZValue(Z_PEAK)
        self.plt_phase.addItem(ref)
        if self.plt_phase.legend is not None:
            self.plt_phase.legend.addItem(ref, "at the amplitude peak")

        phase_x, phase_y = self._phase_peaks(freq, corrected_phase, peak_x)
        star = pg.ScatterPlotItem(x=phase_x, y=phase_y, symbol="star", size=18,
                                  brush=peak_brush, pen=peak_pen)
        star.setZValue(Z_PEAK)
        self.plt_phase.addItem(star)
        if self.plt_phase.legend is not None:
            self.plt_phase.legend.addItem(star, "phase maximum")
        self._label_peaks(self.plt_phase, indices, phase_x, phase_y, label_colour)

    ###########################################################################
    def _scatter(self, plot, x, y, colour, pen, z, name):
        """The raw sweep as dots, so the corrected line stays the dominant one."""
        item = pg.ScatterPlotItem(x=x, y=y, symbol="o", size=2,
                                  brush=pg.mkBrush(*colour, 200), pen=pen)
        item.setZValue(z)
        plot.addItem(item)
        # pyqtgraph does not always pick a ScatterPlotItem up automatically
        if plot.legend is not None:
            plot.legend.addItem(item, name)

    def _label_peaks(self, plot, indices, xs, ys, colour):
        for slot, x, y in zip(indices, xs, ys):
            text = pg.TextItem(text="F{}: {:.0f} Hz".format(_harmonic(slot), x),
                               color=colour, anchor=(0.5, 1.2))
            text.setPos(float(x), float(y))
            plot.addItem(text)

    def _phase_peaks(self, freq, corrected_phase, amplitude_peaks):
        """Maximum of the corrected phase near each amplitude peak.

        Re-derived because it is not recorded: see the module docstring. Returns
        the amplitude peak's own frequency for a slot with no samples in range, so
        the marker still lands somewhere meaningful instead of at zero.
        """
        xs, ys = [], []
        for centre in amplitude_peaks:
            window = ((freq >= centre - PHASE_PEAK_HALF_WINDOW)
                      & (freq <= centre + PHASE_PEAK_HALF_WINDOW))
            if not np.any(window):
                idx = int(np.abs(freq - centre).argmin())
                xs.append(freq[idx])
                ys.append(corrected_phase[idx])
                continue
            sub_freq = freq[window]
            sub_phase = corrected_phase[window]
            best = int(np.argmax(sub_phase))
            xs.append(sub_freq[best])
            ys.append(sub_phase[best])
        return np.array(xs, dtype=float), np.array(ys, dtype=float)
