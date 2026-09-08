"""
PID Control: the loop parameters of the TEC controller, in their own window.

Opens from Tools > PID Control. The four parameters -- cycling time and the P, I
and D shares -- are the ones the Thorlabs MTD415T takes over its serial line
(commands C, P, I, D, forwarded verbatim by the firmware), and the two presets
are the ones `Constants` has always carried: the controller's factory values and
the openQCM default.

*The dialog does not talk to the board.* It owns the widgets and emits
`apply_requested(C, P, I, D)` when Set PID is pressed; the main window decides
how the values reach the controller, because that depends on who holds the
serial port at that moment -- the GUI in Standby, or the acquisition process
during a measurement -- and only the main window knows. What came back from the
controller, or why nothing could, is handed back through `show_status()`.

⚠️ Values shown at open are the ones in `config.txt`, not the defaults: that
file is what the acquisition process reads and sends, so it is the only honest
answer to "what is the instrument set to".
"""

from PyQt5 import QtCore, QtWidgets

from openQCM.core.constants import Constants
from openQCM.ui import theme
from openQCM.ui.widgets import ChevronComboBox, ChevronSpinBox

TAG = "[PIDControl]"

# label, unit, minimum, maximum -- the same ranges the hidden sidebar widgets
# had, which are the MTD415T's own (C: 1-1000 ms, shares: 0-100000)
FIELDS = (
    ("Cycling time", "ms", 1, 1000),
    ("P share", "mA/K", 0, 100000),
    ("I share", "mA/(K·s)", 0, 100000),
    ("D share", "(mA·s)/K", 0, 100000),
)

CUSTOM_LABEL = "Custom"


def presets():
    """The preset table as a list of (name, (C, P, I, D)) from Constants."""
    return [
        (name, (Constants.cycling_time_setting[i], Constants.P_share_setting[i],
                Constants.I_share_setting[i], Constants.D_share_setting[i]))
        for i, name in enumerate(Constants.PID_default_settings)
    ]


class PIDControlDialog(QtWidgets.QDialog):
    """Non-modal editor for the TEC controller's PID parameters."""

    # C, P, I, D as the operator wants them sent
    apply_requested = QtCore.pyqtSignal(int, int, int, int)

    def __init__(self, values, theme_name="light", parent=None):
        super(PIDControlDialog, self).__init__(parent)
        self._theme = theme_name if theme_name in theme.PLOT else "light"
        self._presets = presets()

        self.setObjectName("pidControlDialog")
        self.setWindowTitle("PID Control - TEC controller")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumWidth(360)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ---------------------------------------------------------- presets
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Preset"))
        self.cBox_preset = ChevronComboBox(self)
        self.cBox_preset.setObjectName("cBox_pid_preset")
        for name, _vals in self._presets:
            self.cBox_preset.addItem(name)
        self.cBox_preset.addItem(CUSTOM_LABEL)
        row.addWidget(self.cBox_preset, stretch=1)
        layout.addLayout(row)

        # ------------------------------------------------------- parameters
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        self.spins = []
        for r, (label, unit, lo, hi) in enumerate(FIELDS):
            grid.addWidget(QtWidgets.QLabel(label), r, 0)
            spin = ChevronSpinBox(self)
            spin.setObjectName("spin_pid_{}".format(r))
            spin.setRange(lo, hi)
            spin.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(spin, r, 1)
            grid.addWidget(QtWidgets.QLabel(unit), r, 2)
            self.spins.append(spin)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        # ---------------------------------------------------------- actions
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.pButton_set = QtWidgets.QPushButton("Set PID", self)
        self.pButton_set.setObjectName("pButton_pid_set")
        self.pButton_set.setDefault(True)
        buttons.addWidget(self.pButton_set)
        layout.addLayout(buttons)

        # ----------------------------------------------------------- status
        self.lblStatus = QtWidgets.QLabel("", self)
        self.lblStatus.setObjectName("lbl_pid_status")
        self.lblStatus.setWordWrap(True)
        self.lblStatus.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.lblStatus.setMinimumHeight(40)
        layout.addWidget(self.lblStatus)

        # --------------------------------------------------------- wiring
        self.set_values(*values)
        self.cBox_preset.currentIndexChanged.connect(self._preset_chosen)
        for spin in self.spins:
            spin.valueChanged.connect(self._value_edited)
        self.pButton_set.clicked.connect(self._request_apply)

        self.set_device_connected(False)

    # ------------------------------------------------------------- public
    def values(self):
        """(C, P, I, D) as currently shown."""
        return tuple(int(spin.value()) for spin in self.spins)

    def set_values(self, cycling, p_share, i_share, d_share):
        """Show these four values and select the preset they match, if any."""
        vals = (int(cycling), int(p_share), int(i_share), int(d_share))
        for spin, v in zip(self.spins, vals):
            spin.blockSignals(True)
            spin.setValue(v)
            spin.blockSignals(False)
        self._select_matching_preset()

    def set_device_connected(self, connected):
        """Enable Set PID only when there is a board to send to."""
        self.pButton_set.setEnabled(bool(connected))
        if connected:
            self.show_status("Connected. Set PID sends the parameters to the "
                             "controller and reads them back.")
        else:
            self.show_status("Connect to the device to send the parameters. "
                             "The values shown are those in config.txt.")

    def show_status(self, text):
        self.lblStatus.setText(text)

    # ------------------------------------------------------------ internal
    def _select_matching_preset(self):
        current = self.values()
        index = len(self._presets)                       # "Custom"
        for i, (_name, vals) in enumerate(self._presets):
            if tuple(vals) == current:
                index = i
                break
        self.cBox_preset.blockSignals(True)
        self.cBox_preset.setCurrentIndex(index)
        self.cBox_preset.blockSignals(False)

    def _preset_chosen(self, index):
        if index < 0 or index >= len(self._presets):
            return                                       # "Custom": keep as is
        _name, vals = self._presets[index]
        for spin, v in zip(self.spins, vals):
            spin.blockSignals(True)
            spin.setValue(int(v))
            spin.blockSignals(False)

    def _value_edited(self, _value):
        # an edited value may still equal a preset; say so either way
        self._select_matching_preset()

    def _request_apply(self):
        c, p, i, d = self.values()
        self.show_status("Sending C{} P{} I{} D{} ...".format(c, p, i, d))
        self.apply_requested.emit(c, p, i, d)
