"""
Custom widgets for the openQCM NEXT GUI.

At the moment: a combo box that draws its own chevron. The platform arrow that Qt
gives a QComboBox is a square button with a hard divider, which is the dated look
this replaces.

⚠️ Why it is painted and not styled. The obvious pure-QSS route is
``QComboBox::down-arrow`` with the CSS-triangle trick -- zero width and height,
transparent left/right borders, a coloured top border. **Qt 5.9.7 does not honour
it**: it paints the box, so the arrow comes out as a small dark rectangle.
Measured on this exact build before choosing this route. The other route is an
image, which means one asset per theme times one per pixel density, all of which
have to be regenerated whenever a palette colour moves. Painting the glyph costs
about ten lines, follows the palette by itself and is sharp at any scale.

The colours are class attributes rather than QSS, because a stylesheet cannot
reach a paintEvent. ui/mainWindow.py sets them from the active palette in
_apply_theme, so every combo in the application follows the theme at once.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

CHEVRON_WEIGHT = 1.6      # stroke width
CHEVRON_WIDTH = 9         # glyph bounding box for a combo box
SPIN_CHEVRON_WIDTH = 7    # smaller: two of them share the field height


def paint_chevron(painter, colour, left, top, width, pointing_up=False):
    """Draw one chevron. Shared so a combo and a spin box cannot drift apart."""
    height = width * 0.55
    pen = QtGui.QPen(QtGui.QColor(colour))
    pen.setWidthF(CHEVRON_WEIGHT)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    painter.setPen(pen)
    path = QtGui.QPainterPath()
    if pointing_up:
        path.moveTo(left, top + height)
        path.lineTo(left + width / 2.0, top)
        path.lineTo(left + width, top + height)
    else:
        path.moveTo(left, top)
        path.lineTo(left + width / 2.0, top + height)
        path.lineTo(left + width, top)
    painter.drawPath(path)


class _Chevroned(object):
    """Colour pair, set from the palette by MainWindow._apply_theme."""

    chevron_colour = "#75797e"
    chevron_colour_disabled = "#c2c6ca"

    def _chevron_colour(self):
        return (self.chevron_colour if self.isEnabled()
                else self.chevron_colour_disabled)

    def _chevron_painter(self):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        return painter


class ChevronComboBox(_Chevroned, QtWidgets.QComboBox):
    """QComboBox drawing a thin chevron where the platform arrow used to be.

    The native arrow and its button are switched off in the style sheet
    (``::drop-down { width: 0 }``), so nothing is drawn underneath this.
    """

    _MARGIN = 12        # distance from the right edge; matches the QSS padding

    # popup styling, set from the palette by MainWindow._apply_theme
    popup_qss = ""
    popup_background = "#ffffff"

    def __init__(self, *args, **kwargs):
        super(ChevronComboBox, self).__init__(*args, **kwargs)
        self._style_popup()

    def showPopup(self):
        # re-applied on every open: Qt may rebuild the container, and a theme
        # switch while the list was closed would otherwise not reach it
        self._style_popup()
        super(ChevronComboBox, self).showPopup()

    def _style_popup(self):
        """Style the popup DIRECTLY, on the objects, not through inheritance.

        The popup is two widgets: the QListView and a QFrame container holding it.
        A rule written as ``QComboBox QAbstractItemView`` in the window's style
        sheet reaches the list but **not the container** -- the container is a
        separate top-level window, and on macOS it kept drawing its native light
        frame, which read as a white border once the theme went dark. Nothing in
        the dark palette is white, which is what gave it away.

        So the style sheet is set on the two objects, and the palette is set as
        well: a QPalette applies where a style sheet has not reached, and between
        the two there is no path left for the platform colour.
        """
        view = self.view()
        container = view.parentWidget() if view is not None else None
        colour = QtGui.QColor(self.popup_background)
        for widget in (container, view):
            if widget is None:
                continue
            if self.popup_qss:
                widget.setStyleSheet(self.popup_qss)
            palette = widget.palette()
            palette.setColor(QtGui.QPalette.Window, colour)
            palette.setColor(QtGui.QPalette.Base, colour)
            widget.setPalette(palette)
        if isinstance(container, QtWidgets.QFrame):
            container.setFrameShape(QtWidgets.QFrame.NoFrame)
            container.setAutoFillBackground(True)

    def paintEvent(self, event):
        super(ChevronComboBox, self).paintEvent(event)
        painter = self._chevron_painter()
        width = CHEVRON_WIDTH
        paint_chevron(painter, self._chevron_colour(),
                      self.width() - self._MARGIN - width,
                      (self.height() - width * 0.55) / 2.0, width,
                      # list open: point at where it will fold back to
                      pointing_up=self.view().isVisible())
        painter.end()


class _ChevronSpinMixin(_Chevroned):
    """Two stacked chevrons instead of the platform up/down buttons.

    The buttons themselves stay live -- they are only made invisible in the style
    sheet -- so clicking where the glyphs are still steps the value.
    """

    _MARGIN = 11

    def paintEvent(self, event):
        super(_ChevronSpinMixin, self).paintEvent(event)
        painter = self._chevron_painter()
        width = SPIN_CHEVRON_WIDTH
        height = width * 0.55
        left = self.width() - self._MARGIN - width
        centre = self.height() / 2.0
        gap = 3.0
        colour = self._chevron_colour()
        paint_chevron(painter, colour, left, centre - gap - height, width,
                      pointing_up=True)
        paint_chevron(painter, colour, left, centre + gap, width)
        painter.end()


class ChevronSpinBox(_ChevronSpinMixin, QtWidgets.QSpinBox):
    pass


class ChevronDoubleSpinBox(_ChevronSpinMixin, QtWidgets.QDoubleSpinBox):
    pass
