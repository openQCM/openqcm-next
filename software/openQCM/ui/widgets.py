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

    def __init__(self, *args, **kwargs):
        super(ChevronComboBox, self).__init__(*args, **kwargs)
        # The popup is TWO widgets: the QListView and a QFrame container holding
        # it. The container is what draws the platform frame -- on macOS a light
        # rounded border that stayed white on the dark theme -- and a style sheet
        # rule aimed at the view never reaches it. Take its frame away here, where
        # the object is in hand, instead of guessing at a selector; the view then
        # fills the container and the QSS colours are all that is left visible.
        container = self.view().parentWidget()
        if isinstance(container, QtWidgets.QFrame):
            container.setFrameShape(QtWidgets.QFrame.NoFrame)

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
