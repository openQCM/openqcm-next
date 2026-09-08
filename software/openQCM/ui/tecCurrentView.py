"""
Tec Current: the TEC drive current over time, live, in its own window.

Opens from Tools > Tec Current. It is the fourth auxiliary view and follows the
rules of the other three (`rawDataView.py`, `peakDataView.py`, the datalog
view): a non-modal QDialog, one instance at a time, closed with the main
window, painted from `theme.PLOT` like the main plots -- same background, same
axis and title colours, the theme's foreground curve colour, the shared
right-click menu of `ui/plotMenu.py` -- and an elapsed-time axis in
hh:mm:ss synchronised with the main window's through `set_start_time()`.

*It is pushed, not pulling.* Unlike Raw Data View, the main window hands it the
buffers from `_update_plot()` on every tick, which is what the old
`SecondWindow` did; the acquisition never waits on it. Nothing here reads a
file: the current comes from the worker's TEC-current buffer, filled by the
acquisition process from the controller's `A?` answer once per sweep.
"""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from openQCM.core.constants import Constants, ElapsedTimeAxis
from openQCM.ui import theme
from openQCM.ui.plotMenu import PlotMenu

TAG = "[TecCurrentView]"


class TecCurrentDialog(QtWidgets.QDialog):
    """Live TEC current, one curve, main-window look."""

    def __init__(self, theme_name="light", parent=None):
        super(TecCurrentDialog, self).__init__(parent)
        self._theme = theme_name if theme_name in theme.PLOT else "light"

        self.setObjectName("tecCurrentDialog")
        self.setWindowTitle("Tec Current - live")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(560, 360)
        self.resize(800, 520)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.canvas = pg.GraphicsLayoutWidget()
        layout.addWidget(self.canvas, stretch=1)

        # the same elapsed-time axis as the main window's real-time plots
        time_axis = ElapsedTimeAxis(orientation="bottom")
        time_axis.enableAutoSIPrefix(False)
        self.plot = self.canvas.addPlot(row=0, col=0, axisItems={"bottom": time_axis})
        # 'mA' is the unit, not a prefix to be scaled to 'kmA'
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.showGrid(x=False, y=False)
        self.curve = self.plot.plot()
        self.apply_theme(self._theme)

        self.lblValue = QtWidgets.QLabel("TEC current: — mA", self)
        self.lblValue.setObjectName("lbl_tec_current_value")
        self.lblValue.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.lblValue)

        self._menu = PlotMenu(self)
        self._menu.attach([self.plot])

    # ------------------------------------------------------------- public
    def apply_theme(self, theme_name):
        """Paint background, axes, title and curve from `theme.PLOT`.

        Called at construction and again by the main window when the theme
        changes while this window is open: the application QSS repaints the
        frame around the canvas, never the canvas itself.
        """
        self._theme = theme_name if theme_name in theme.PLOT else "light"
        palette = theme.PLOT[self._theme]
        self.canvas.setBackground(palette["bg"])
        self.plot.setTitle("Real-Time Plot: TEC current", color=palette["title"])
        self.plot.setLabel("left", "TEC current", units="mA", color=palette["axis"])
        self.plot.setLabel("bottom", "Time (hh:mm:ss)", color=palette["axis"])
        for side in ("left", "bottom"):
            axis = self.plot.getAxis(side)
            axis.setPen(palette["axis"])
            axis.setTextPen(palette["axis"])
        # the theme's foreground curve colour, as the temperature plot uses:
        # a fixed white pen vanishes on the light theme's background
        self.curve.setPen(pg.mkPen(color=palette.get("curve", palette["axis"]),
                                   width=Constants.plot_line_width))

    def update_plot(self, x_s, y_s, start_time=None):
        """New buffers from the main window; `start_time` in epoch µs, as the
        main window's elapsed-time axes take it."""
        if start_time is not None:
            self.plot.getAxis("bottom").set_start_time(start_time)
        self.curve.setData(x_s, y_s)

        # the buffers are newest-first, as everywhere in the main window
        try:
            last = y_s[0]
        except (IndexError, TypeError):
            last = float("nan")
        if last is None or np.isnan(last):
            self.lblValue.setText("TEC current: NaN mA")
        else:
            self.lblValue.setText("TEC current: {} mA".format(int(last)))
