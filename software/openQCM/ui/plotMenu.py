"""
The right-click menu shared by the plot panels.

pyqtgraph's own menu is switched off everywhere in this application and replaced
by a short, predictable one. That decision was made once and then implemented
twice -- in `mainWindow.py` and again in `rawDataView.py` -- with the same items in
the same order. This module is the one implementation, so a third panel wanting
the same menu does not become a third copy.

Two things about pyqtgraph that the menu has to work around, and that cost time to
find:

* the plots of one ``GraphicsLayoutWidget`` share a single ``QGraphicsScene``, so
  ``sigMouseClicked`` must be connected **once per scene** and the plot found by
  hit-testing the click position. Connecting per plot fires the handler once per
  plot on the same click.
* ``setMenuEnabled(False)`` has to be called on the ``PlotItem`` *and* on its
  ``ViewBox``; either one left enabled still pops pyqtgraph's menu up.

The grid state lives here because pyqtgraph offers no reliable read-back of it,
and the menu label has to say "Show grid" or "Hide grid".
"""

try:
    from PyQt5 import QtCore, QtGui
except ImportError:                                      # pragma: no cover
    from PySide2 import QtCore, QtGui
import pyqtgraph as pg

GRID_ALPHA = 0.3


class PlotMenu(object):
    """Owns the right-click menu, and the grid state, for a set of plots.

    :param owner: widget the ``QMenu`` is parented to.
    :param extra_actions: optional ``callable(menu, plot)`` invoked before the
        final separator, for items only one window has -- the main window's
        delta cursors, for instance.
    :param apply_grid: optional ``callable(plot, on)`` replacing the default
        ``showGrid``, for panels where more than one plot has to follow (the main
        window's phase twin overlays the amplitude plot and their grids must move
        together).
    """

    def __init__(self, owner, extra_actions=None, apply_grid=None):
        self._owner = owner
        self._extra = extra_actions
        self._apply_grid = apply_grid
        self.grid_on = {}
        self._targets = []
        self._scenes = []

    # ------------------------------------------------------------------ setup
    def attach(self, plots):
        """Take the right-click over on ``plots``; can be called more than once.

        Each call adds to the targets, so a window with one canvas per tab can
        attach tab by tab. A scene is only ever connected once, however often it
        appears.
        """
        for plot in plots:
            if plot is None:
                continue
            plot.setMenuEnabled(False)
            box = plot.getViewBox()
            if box is not None:
                box.setMenuEnabled(False)
            if not any(plot is p for p in self._targets):
                self._targets.append(plot)
            scene = plot.scene()
            if scene is not None and not any(scene is s for s in self._scenes):
                self._scenes.append(scene)
                scene.sigMouseClicked.connect(self._on_scene_clicked)

    # ------------------------------------------------------------------- grid
    def set_grid(self, plot, on):
        self.grid_on[plot] = bool(on)
        if self._apply_grid is not None:
            self._apply_grid(plot, bool(on))
        else:
            plot.showGrid(x=bool(on), y=bool(on), alpha=GRID_ALPHA)

    def set_grid_all(self, on):
        for plot in self._targets:
            self.set_grid(plot, on)

    def is_grid_on(self, plot):
        return self.grid_on.get(plot, False)

    # ------------------------------------------------------------------- menu
    def build_menu(self, plot):
        """The menu for ``plot``, not yet shown. Separated from :meth:`show` so
        the items can be inspected without entering a modal event loop."""
        menu = QtGui.QMenu(self._owner)
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
        on = self.is_grid_on(plot)
        menu.addAction("Hide grid" if on else "Show grid",
                       lambda: self.set_grid(plot, not on))
        if self._extra is not None:
            self._extra(menu, plot)
        # Export lived in pyqtgraph's scene menu, which is off now: keep it
        # reachable
        menu.addSeparator()
        menu.addAction("Export…", lambda: plot.scene().showExportDialog())
        return menu

    def show(self, plot, screen_pos):
        self.build_menu(plot).exec_(screen_pos)

    def _on_scene_clicked(self, event):
        """Right-click inside one of our plots: show OUR menu and nothing else."""
        if event.button() != QtCore.Qt.RightButton:
            return
        for plot in self._targets:
            box = plot.getViewBox()
            if box is not None and box.sceneBoundingRect().contains(
                    event.scenePos()):
                event.accept()
                self.show(plot, event.screenPos().toPoint())
                return
