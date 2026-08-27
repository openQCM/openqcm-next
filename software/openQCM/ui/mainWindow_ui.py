# -*- coding: utf-8 -*-
"""
Programmatic UI builder for openQCM NEXT (GUI redesign, replaces the
Qt-Designer generated ``mainWindow_new_ui.py``). Hand-written in the style of
openQCM Q-1 v3.0's ``Ui_Main``.

Contract: exposes the same attribute names the controller (ui/mainWindow.py)
already uses via ``self.ui.<name>``, plus the widgets that were previously
created at runtime (Connect/Refresh buttons, overtone quick-select buttons,
System Log, datalog-filename label) and the single-window structure that
``_build_shell()`` used to obtain by re-parenting the Designer grid:

    QSplitter [ sidebar pane (scrollable cards + fixed Start/Stop) | center tabs ]
    + File / View / Tools / Help menu skeleton

The controller keeps all behaviour: it only wires signals to these widgets.
Legacy widgets that the logic still expects (pButton_Stop, the overtone
radios) are created but hidden.
"""

import os

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import GraphicsLayoutWidget

from openQCM.ui.widgets import (ChevronComboBox, ChevronSpinBox,
                                ChevronDoubleSpinBox)

# Application icon, resolved absolutely from this module (robust to the launch
# working directory — the old relative "favicon.png" only loaded from cwd).
APP_ICON = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "res", "icon", "favicon.png"))


class Ui_MainWindow(object):

    # ------------------------------------------------------------------ #
    # small helpers                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hline(parent, name):
        line = QtWidgets.QFrame(parent)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setObjectName(name)
        return line

    def _label(self, parent, name, text=""):
        lbl = QtWidgets.QLabel(parent)
        lbl.setObjectName(name)
        if text:
            lbl.setText(text)
        setattr(self, name, lbl)
        return lbl

    # ------------------------------------------------------------------ #
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 980)
        icon = QtGui.QIcon()
        if os.path.exists(APP_ICON):
            icon.addPixmap(QtGui.QPixmap(APP_ICON),
                           QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setWindowTitle("openQCM NEXT - version 0.1.6 DEVELOPMENT")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self._build_menubar(MainWindow)
        self._build_sidebar()
        self._build_center()
        self._build_impedance_panel()
        self._build_statusbar()

        # --- main splitter: [ sidebar | center tabs | impedance ] ------- #
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal,
                                                self.centralwidget)
        self.mainSplitter.setObjectName("mainSplitter")
        self.mainSplitter.addWidget(self.sidebarPane)
        self.mainSplitter.addWidget(self.centerTabs)
        self.mainSplitter.addWidget(self.impedancePanel)
        self.mainSplitter.setCollapsible(0, True)
        self.mainSplitter.setCollapsible(1, False)
        self.mainSplitter.setCollapsible(2, True)
        self.mainSplitter.setStretchFactor(0, 0)
        self.mainSplitter.setStretchFactor(1, 1)
        self.mainSplitter.setStretchFactor(2, 0)
        self.mainSplitter.setSizes([280, 700, 380])

        outer = QtWidgets.QVBoxLayout(self.centralwidget)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.addWidget(self.mainSplitter, 1)   # splitter takes all extra space
        outer.addWidget(self.statusBarFrame)    # thin fixed-height bar

    # ------------------------------------------------------------------ #
    # right panel: live impedance (exact formula)                        #
    # ------------------------------------------------------------------ #
    def _build_impedance_panel(self):
        """VER 0.1.6G right-hand dock with the two live impedance views:
        the exact conductance spectrum G(f) and the admittance locus B vs G,
        both with all overtones overlaid in the standard per-overtone colours.

        Display only — these are computed with the exact complex-divider
        inversion, while the logged frequency/dissipation still come from the
        approximate formula in parameters_finder_impedance().
        """
        self.impedancePanel = QtWidgets.QWidget()
        self.impedancePanel.setObjectName("impedancePanel")
        self.impedancePanel.setMinimumWidth(260)

        lay = QtWidgets.QVBoxLayout(self.impedancePanel)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        # The two views sit in a card, like every other plot in this GUI. The
        # header that used to float above them is the card's title, so the panel
        # carries one label instead of two. `cardCompact` is the property hook in
        # theme.qss; it is set HERE, before the style sheet reaches the widget,
        # because Qt evaluates property selectors at polish time.
        self.groupImpedance = QtWidgets.QGroupBox("Impedance — exact formula")
        self.groupImpedance.setObjectName("groupImpedance")
        self.groupImpedance.setProperty("cardCompact", True)
        card = QtWidgets.QVBoxLayout(self.groupImpedance)
        card.setContentsMargins(4, 4, 4, 4)
        card.setSpacing(4)
        lay.addWidget(self.groupImpedance, 1)

        # conductance spectrum G(f), all overtones
        self.pltG = GraphicsLayoutWidget(self.groupImpedance)
        self.pltG.setObjectName("pltG")
        self.pltG.setAntialiasing(True)

        # admittance locus B vs G, all overtones
        self.pltGB = GraphicsLayoutWidget(self.groupImpedance)
        self.pltGB.setObjectName("pltGB")
        self.pltGB.setAntialiasing(True)

        # vertical splitter so either view can be given the whole panel
        self.impedanceSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.impedanceSplitter.setObjectName("impedanceSplitter")
        self.impedanceSplitter.addWidget(self.pltG)
        self.impedanceSplitter.addWidget(self.pltGB)
        self.impedanceSplitter.setCollapsible(0, True)
        self.impedanceSplitter.setCollapsible(1, True)
        self.impedanceSplitter.setStretchFactor(0, 1)
        self.impedanceSplitter.setStretchFactor(1, 1)
        self.impedanceSplitter.setSizes([340, 340])
        card.addWidget(self.impedanceSplitter, 1)

    # ------------------------------------------------------------------ #
    # bottom status bar (R2)                                             #
    # ------------------------------------------------------------------ #
    def _build_statusbar(self):
        """Full-width bottom status bar: state pill + message on the left,
        compact live readings (T/S) and the progress bar on the right."""
        self.statusBarFrame = QtWidgets.QFrame(self.centralwidget)
        self.statusBarFrame.setObjectName("statusBarFrame")
        self.statusBarFrame.setFixedHeight(36)
        bar = QtWidgets.QHBoxLayout(self.statusBarFrame)
        bar.setContentsMargins(8, 3, 8, 3)
        bar.setSpacing(8)
        # Q-1 v3.0's shape: the machine state is carried by the COLOUR of a single
        # dot, and the two text labels beside it stay plain. Colouring the text as
        # well -- which is what the pill background and the <font> tags used to do
        # -- says the same thing twice and makes the message harder to read.
        self._label(self.statusBarFrame, "statusIndicator", "●")
        self.statusIndicator.setFixedWidth(16)
        bar.addWidget(self.statusIndicator)
        self._label(self.statusBarFrame, "infostatus", "Standby")
        bar.addWidget(self.infostatus)
        self._label(self.statusBarFrame, "infobar", "Ready")
        bar.addWidget(self.infobar, 1)
        # Only temperature and sampling time. The per-overtone frequency and
        # dissipation readouts that used to sit here are a Q-1 inheritance: on NEXT
        # every overtone is measured at once, so a single F/D pair in a status bar
        # can only ever show one of them and invites reading it as "the" value.
        for name, text in (("statusTempValue", "T: --"),
                           ("statusSampValue", "S: --")):
            bar.addWidget(self._label(self.statusBarFrame, name, text))
        self.progressBar = QtWidgets.QProgressBar(self.statusBarFrame)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setFixedWidth(160)
        self.progressBar.setFixedHeight(20)
        bar.addWidget(self.progressBar)

    # ------------------------------------------------------------------ #
    # menu bar: File / View / Tools / Help skeleton                      #
    # ------------------------------------------------------------------ #
    def _build_menubar(self, MainWindow):
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        # R2: keep the menu inside the window (mockup layout) — on macOS the
        # native system menu bar would otherwise swallow it, hiding the
        # corner theme toggle too.
        self.menuBar.setNativeMenuBar(False)
        MainWindow.setMenuBar(self.menuBar)

        # File
        self.menuFile = QtWidgets.QMenu("File", self.menuBar)
        self.menuFile.setObjectName("menuFile")
        # open a datalog the instrument wrote; same place Q-1 v3.0 puts it
        self.actionOpenLog = QtWidgets.QAction("Open Log…", MainWindow)
        self.actionOpenLog.setObjectName("actionOpenLog")
        self.actionOpenLog.setShortcut(QtGui.QKeySequence.Open)
        self.menuFile.addAction(self.actionOpenLog)
        self.menuFile.addSeparator()
        self.actionQuit = QtWidgets.QAction("Quit", MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionQuit.setShortcut("Ctrl+Q")
        self.actionQuit.triggered.connect(MainWindow.close)
        self.menuFile.addAction(self.actionQuit)

        # View (populated by the controller: Theme submenu, panels)
        self.menuView = QtWidgets.QMenu("View", self.menuBar)
        self.menuView.setObjectName("menuView")

        # Tools (existing actions re-homed from the old Add-On menu)
        self.menuTools = QtWidgets.QMenu("Tools", self.menuBar)
        self.menuTools.setObjectName("menuTools")
        # live view, reads the acquisition buffers in memory
        self.actionRawDataView = QtWidgets.QAction("Raw Data View", MainWindow)
        self.actionRawDataView.setObjectName("actionRawDataView")
        # snapshot of the last Peak Detection, read from the calibration files
        self.actionPeakDataView = QtWidgets.QAction("Peak Data View", MainWindow)
        self.actionPeakDataView.setObjectName("actionPeakDataView")
        # the older viewer, which reads the sweep dump under sweep_data/
        self.actionRaw_Data = QtWidgets.QAction("Raw Data (from sweep files)",
                                                MainWindow)
        self.actionRaw_Data.setObjectName("actionRaw_Data")
        self.actionTEC_current = QtWidgets.QAction("Tec Current", MainWindow)
        self.actionTEC_current.setObjectName("actionTEC_current")
        # VER 0.1.6G conductance / impedance offline view (branch impedance-analysis)
        self.actionConductance_Data = QtWidgets.QAction("Conductance Data", MainWindow)
        self.actionConductance_Data.setObjectName("actionConductance_Data")
        # VER 0.1.6G live BVD circle + Lorentzian fit window
        self.actionImpedance_Fit = QtWidgets.QAction("Impedance Fit (live)", MainWindow)
        self.actionImpedance_Fit.setObjectName("actionImpedance_Fit")
        self.menuTools.addAction(self.actionRawDataView)
        self.menuTools.addAction(self.actionPeakDataView)
        self.menuTools.addAction(self.actionRaw_Data)
        self.menuTools.addAction(self.actionConductance_Data)
        self.menuTools.addAction(self.actionImpedance_Fit)
        self.menuTools.addAction(self.actionTEC_current)

        # Help (existing actions re-homed from the old Info menu)
        self.menuHelp = QtWidgets.QMenu("Help", self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        self.actionHelp = QtWidgets.QAction("Help", MainWindow)
        self.actionHelp.setObjectName("actionHelp")
        self.actionFirmware = QtWidgets.QAction("Firmware Info", MainWindow)
        self.actionFirmware.setObjectName("actionFirmware")
        self.actionSoftware = QtWidgets.QAction("Software Info", MainWindow)
        self.actionSoftware.setObjectName("actionSoftware")
        self.menuHelp.addAction(self.actionHelp)
        self.menuHelp.addAction(self.actionFirmware)
        self.menuHelp.addAction(self.actionSoftware)

        for menu in (self.menuFile, self.menuView, self.menuTools, self.menuHelp):
            self.menuBar.addAction(menu.menuAction())

        # R2: light/dark quick toggle in the menu-bar corner (mockup top-right)
        self.themeToggleButton = QtWidgets.QToolButton(self.menuBar)
        self.themeToggleButton.setObjectName("themeToggleButton")
        self.themeToggleButton.setText("◐ theme")
        self.themeToggleButton.setToolTip("Toggle light/dark theme")
        self.themeToggleButton.setAutoRaise(True)
        self.menuBar.setCornerWidget(self.themeToggleButton,
                                     QtCore.Qt.TopRightCorner)

    # ------------------------------------------------------------------ #
    # left sidebar                                                       #
    # ------------------------------------------------------------------ #
    def _build_sidebar(self):
        self.sidebarContainer = QtWidgets.QWidget()
        self.sidebarContainer.setObjectName("sidebarContainer")
        sb = QtWidgets.QVBoxLayout(self.sidebarContainer)
        sb.setContentsMargins(8, 8, 8, 8)
        sb.setSpacing(10)

        # --- brand header (groupBox_2) --------------------------------- #
        self.groupBox_2 = QtWidgets.QGroupBox(self.sidebarContainer)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.label.setMaximumSize(QtCore.QSize(45, 45))
        self.label.setPixmap(QtGui.QPixmap(APP_ICON))
        self.label.setScaledContents(True)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.label_2.setText(
            '<html><head/><body><p>'
            '<span style=" font-size:16pt; font-weight:600;">openQCM NEXT</span><br/>'
            '<span style=" color:#8a8a8a;">Quartz Crystal Microbalance</span>'
            '</p></body></html>')
        # allow wrapping so the rich-text brand does not force a wide minimum
        # width on the whole sidebar (it was pinning ~459 px otherwise)
        self.label_2.setWordWrap(True)
        self.gridLayout_8.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout_8.addWidget(self.label_2, 0, 1, 1, 1)
        sb.addWidget(self.groupBox_2)

        # --- Serial Connection card (R2) -------------------------------- #
        self.groupConnection = QtWidgets.QGroupBox("Serial Connection",
                                                   self.sidebarContainer)
        self.groupConnection.setObjectName("groupConnection")
        self.gridLayout = QtWidgets.QGridLayout(self.groupConnection)
        self.gridLayout.setObjectName("gridLayout")
        self._label(self.groupConnection, "l1", "Serial COM Port")
        self._label(self.groupConnection, "label_COM_status", "Disconnected")
        # a long "Connected: <port>" must NOT widen the sidebar: ignore the
        # label's content width (it clips/keeps the full text in the tooltip)
        self.label_COM_status.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                            QtWidgets.QSizePolicy.Preferred)
        self.label_COM_status.setMinimumWidth(0)
        self.cBox_Port = ChevronComboBox(self.groupConnection)
        self.cBox_Port.setObjectName("cBox_Port")
        self.cBox_Port.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLength)
        self.pButton_Refresh = QtWidgets.QPushButton("Refresh", self.groupConnection)
        self.pButton_Refresh.setObjectName("pButton_Refresh")
        self.pButton_Connect = QtWidgets.QPushButton("Connect", self.groupConnection)
        self.pButton_Connect.setObjectName("pButton_Connect")
        conn_row = QtWidgets.QHBoxLayout()
        conn_row.addWidget(self.pButton_Refresh)
        conn_row.addWidget(self.pButton_Connect)
        conn_row.addStretch(1)   # buttons keep their natural (label) width
        self.gridLayout.addWidget(self.l1, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.label_COM_status, 0, 1, 1, 1)
        # GUI lightening: the "Serial COM Port" caption and the "Connected: ..."
        # status label are hidden (kept alive for the controller). The port
        # combo, the Connect/Disconnect button colour and the bottom status bar
        # already convey the connection state.
        self.l1.hide()
        self.label_COM_status.hide()
        self.gridLayout.addWidget(self.cBox_Port, 1, 0, 1, 2)
        self.gridLayout.addLayout(conn_row, 2, 0, 1, 2)
        sb.addWidget(self.groupConnection)

        # --- Measurement Setup card (R2) -------------------------------- #
        self.groupSetup = QtWidgets.QGroupBox("Measurement Setup",
                                              self.sidebarContainer)
        self.groupSetup.setObjectName("groupSetup")
        self.gridSetup = QtWidgets.QGridLayout(self.groupSetup)
        self.gridSetup.setObjectName("gridSetup")
        self._label(self.groupSetup, "info11", "Operation mode")
        self.cBox_Source = ChevronComboBox(self.groupSetup)
        self.cBox_Source.setObjectName("cBox_Source")
        self._label(self.groupSetup, "l2", "Frequency (single mode)")
        self.cBox_Speed = ChevronComboBox(self.groupSetup)
        self.cBox_Speed.setObjectName("cBox_Speed")
        # kept for structural compatibility (hidden separator of the old grid)
        self.line = self._hline(self.groupSetup, "line")
        self.line.hide()
        self.gridSetup.addWidget(self.info11, 0, 0, 1, 2)
        self.gridSetup.addWidget(self.cBox_Source, 1, 0, 1, 2)
        self.gridSetup.addWidget(self.l2, 2, 0, 1, 2)
        self.gridSetup.addWidget(self.cBox_Speed, 3, 0, 1, 2)
        # GUI lightening: hide the "Operation mode" / "Frequency (single mode)"
        # captions (kept alive) — the combos are self-describing.
        self.info11.hide()
        self.l2.hide()
        sb.addWidget(self.groupSetup)

        # frequency / dissipation readouts moved out of the sidebar into
        # horizontal cards above their plots (see _build_readout_card, called
        # from _build_center). Keep the overtone list for the selector below.
        # The widget names keep the historical F0 for the fundamental: the
        # controller reaches radioBtn_F0 / overtoneBtn_F0 / F0 / D0 by string, so
        # renaming them is a separate job with nothing to show for it. What the
        # user reads is the label below, and the fundamental is the FIRST
        # harmonic, not the zeroth.
        overtones = ("F0", "F3", "F5", "F7", "F9")
        overtone_labels = ("F1", "F3", "F5", "F7", "F9")

        # --- overtone selector row (gridLayout_D) ----------------------- #
        self.gridLayout_D = QtWidgets.QGridLayout()
        self.gridLayout_D.setObjectName("gridLayout_D")
        self.line_2 = self._hline(self.sidebarContainer, "line_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        # tight row so the 5 chips take the least horizontal room possible
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        radio_texts = ("1st", "3rd", "5th", "7th", "9th")
        self.overtone_buttons = []
        for name, label, rtext in zip(overtones, overtone_labels, radio_texts):
            # legacy radio: hidden, still the source of truth for scan_selector
            radio = QtWidgets.QRadioButton(rtext, self.sidebarContainer)
            radio.setObjectName("radioBtn_" + name)
            radio.setAutoExclusive(False)
            radio.hide()
            setattr(self, "radioBtn_" + name, radio)
            self.horizontalLayout_2.addWidget(radio)
            # quick-select proxy button (Phase 3b)
            btn = QtWidgets.QPushButton(label, self.sidebarContainer)
            btn.setObjectName("overtoneBtn_" + name)
            btn.setProperty("overtoneBtn", True)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setToolTip("Overtone " + label)
            setattr(self, "overtoneBtn_" + name, btn)
            self.horizontalLayout_2.addWidget(btn)
            self.overtone_buttons.append(btn)
        self.gridLayout_D.addWidget(self.line_2, 3, 0, 1, 2)
        self.gridLayout_D.addLayout(self.horizontalLayout_2, 4, 0, 1, 2)
        # R2: the overtone quick-select row belongs to the Measurement Setup card
        self.line_2.hide()
        self.gridSetup.addLayout(self.gridLayout_D, 4, 0, 1, 2)

        # --- datalog sampling / elapsed time (gridLayout_5) ------------- #
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self._label(self.sidebarContainer, "sampling_time_lbl",
                    "Datalog Sampling Time (sec) ")
        self.cBox_sampling_time = ChevronComboBox(self.sidebarContainer)
        self.cBox_sampling_time.setObjectName("cBox_sampling_time")
        self._label(self.sidebarContainer, "time_lbl", "Time elapsed (sec)")
        self._label(self.sidebarContainer, "time_indicator", "0")
        self.gridLayout_5.addWidget(self.sampling_time_lbl, 0, 0, 1, 1)
        self.gridLayout_5.addWidget(self.cBox_sampling_time, 1, 0, 1, 1)
        self.gridLayout_5.addWidget(self.time_lbl, 2, 0, 1, 1)
        self.gridLayout_5.addWidget(self.time_indicator, 3, 0, 1, 1)
        # Fine-tuning: hide the datalog sampling-time selector from the GUI for
        # now (kept created and functional — the controller still reads/enables
        # it; acquisition uses the default sampling time). "Time elapsed" stays.
        self.sampling_time_lbl.hide()
        self.cBox_sampling_time.hide()
        # R2: datalog sampling settings live in the Measurement Setup card
        self.gridSetup.addLayout(self.gridLayout_5, 5, 0, 1, 2)

        # kept for structural compatibility, cards replace the separators
        self.line_3 = self._hline(self.sidebarContainer, "line_3")
        self.line_3.hide()

        # --- Temperature & PID card wrapping the tabs (R2) --------------- #
        self._build_temperature_tabs()
        self.groupTempPID = QtWidgets.QGroupBox("Temperature",
                                                self.sidebarContainer)
        self.groupTempPID.setObjectName("groupTempPID")
        _tpid = QtWidgets.QVBoxLayout(self.groupTempPID)
        _tpid.setContentsMargins(4, 4, 4, 4)
        _tpid.addWidget(self.tab)   # controls directly in the card (no tab box)
        sb.addWidget(self.groupTempPID)

        # --- Plot Controls card (Autoscale · Set/Clear Reference · Clear) --- #
        self.groupPlotControls = QtWidgets.QGroupBox("Plot Controls",
                                                     self.sidebarContainer)
        self.groupPlotControls.setObjectName("groupPlotControls")
        # compact horizontal row: buttons keep their natural (label) width,
        # left-aligned via a trailing stretch (same rule as the other groups)
        _pc = QtWidgets.QHBoxLayout(self.groupPlotControls)
        _pc.setSpacing(6)
        self.pButton_Autoscale = QtWidgets.QPushButton("AUTO",
                                                       self.sidebarContainer)
        self.pButton_Autoscale.setObjectName("pButton_Autoscale")
        self.pButton_Reference = QtWidgets.QPushButton("SET REF",
                                                       self.sidebarContainer)
        self.pButton_Reference.setObjectName("pButton_Reference")
        self.pButton_Clear = QtWidgets.QPushButton("CLEAR",
                                                   self.sidebarContainer)
        self.pButton_Clear.setObjectName("pButton_Clear")
        # Divide every plotted frequency by its harmonic order, so the overtones
        # can be read against one another. A toggle, not a one-shot: it changes
        # what the panel means for as long as it is pressed.
        self.pButton_NScale = QtWidgets.QPushButton("N-SCALE",
                                                    self.sidebarContainer)
        self.pButton_NScale.setObjectName("pButton_NScale")
        self.pButton_NScale.setCheckable(True)
        self.pButton_NScale.setToolTip(
            "Divide each overtone by its harmonic order (display only — the "
            "datalog keeps the measured values)")
        for _b in (self.pButton_Autoscale, self.pButton_Reference,
                   self.pButton_Clear, self.pButton_NScale):
            _pc.addWidget(_b)
        _pc.addStretch(1)
        sb.addWidget(self.groupPlotControls)

        # Plot Controls is the last top-anchored card; this stretch pushes the
        # datalog filename + Start/Stop toggle to the bottom of the sidebar.
        sb.addStretch(1)

        # legacy buttons kept alive (hidden) for the controller logic:
        # Clear Reference is merged into the Set/Clear Reference toggle, and
        # Stop is superseded by the single Start/Stop toggle (Phase 3a).
        self.pButton_Reference_Not = QtWidgets.QPushButton("Clear Reference ",
                                                           self.sidebarContainer)
        self.pButton_Reference_Not.setObjectName("pButton_Reference_Not")
        self.pButton_Reference_Not.hide()
        self.pButton_Stop = QtWidgets.QPushButton("Stop", self.sidebarContainer)
        self.pButton_Stop.setObjectName("pButton_Stop")
        self.pButton_Stop.hide()


        # Card titles must be bold. Qt ignores font-weight on QGroupBox::title,
        # so set the bold weight on the groupbox widget font (the native title
        # uses it); the theme QSS resets the card content back to normal weight.
        for _card in (self.groupConnection, self.groupSetup,
                      self.groupTempPID, self.groupPlotControls):
            _cf = _card.font()
            _cf.setBold(True)
            _card.setFont(_cf)
        # infostatus / infobar / progressBar live in the bottom status bar
        # (R2) — created in _build_statusbar().

        # --- scroll wrapper --------------------------------------------- #
        self.sidebarScroll = QtWidgets.QScrollArea()
        self.sidebarScroll.setObjectName("sidebarScroll")
        self.sidebarScroll.setWidgetResizable(True)
        self.sidebarScroll.setWidget(self.sidebarContainer)
        self.sidebarScroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.sidebarScroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        # --- datalog filename + Start/Stop toggle (3a/3d/3e, R2) --------- #
        # OUTSIDE the scroll area, pinned under it: Start/Stop must stay reachable
        # however short the window gets. Inside the scrolling content it was the
        # last widget, so shrinking the window vertically pushed it out of sight
        # and starting an acquisition needed a scroll first.
        self.sidebarPane = QtWidgets.QWidget()
        self.sidebarPane.setObjectName("sidebarPane")
        pane = QtWidgets.QVBoxLayout(self.sidebarPane)
        pane.setContentsMargins(0, 0, 0, 0)
        pane.setSpacing(6)
        pane.addWidget(self.sidebarScroll, 1)      # only this scrolls

        # The pinned block gets the SAME horizontal inset as the cards, which are
        # laid out inside sidebarContainer with 8 px margins. Without it the button
        # is 16 px wider than every card above it and visibly sticks out. The inset
        # cannot go on `pane`, or the scroll area would be indented too and the
        # cards would end up doubly inset.
        bottom = QtWidgets.QVBoxLayout()
        bottom.setContentsMargins(8, 0, 8, 8)
        bottom.setSpacing(6)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblLogFile = QtWidgets.QLabel(self.sidebarPane)
        self.lblLogFile.setObjectName("lblLogFile")
        self.lblLogFile.hide()
        self.verticalLayout.addWidget(self.lblLogFile)
        bottom.addLayout(self.verticalLayout)
        self.pButton_Start = QtWidgets.QPushButton("▷  Start", self.sidebarPane)
        self.pButton_Start.setObjectName("pButton_Start")
        self.pButton_Start.setMinimumHeight(40)
        bottom.addWidget(self.pButton_Start)
        pane.addLayout(bottom)

        # Default width 300 px (set on the splitter below): shows the whole
        # sidebar content without clipping. Kept resizable — min/max instead of
        # a fixed width — so the splitter handle can smoothly drag it, not just
        # snap open/closed. On the pane now, since that is what the splitter holds.
        self.sidebarPane.setMinimumWidth(260)
        self.sidebarPane.setMaximumWidth(400)

    # ------------------------------------------------------------------ #
    # Temperature control card                                           #
    # ------------------------------------------------------------------ #
    def _build_temperature_tabs(self):
        # Temperature Control widgets go directly into the groupTempPID card
        # (no inner QTabWidget wrapper / extra bordered box). `self.tab` is a
        # plain, borderless container holding gridLayout_4; it is added straight
        # to the card in _build_sidebar. The PID widgets live on a hidden,
        # standalone `tab_2` (kept alive for the controller — the advanced
        # temperature/PID window will reuse them).
        self.tab = QtWidgets.QWidget(self.sidebarContainer)
        self.tab.setObjectName("tab")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.line_4 = self._hline(self.tab, "line_4")
        self.line_4.hide()   # card border/title already separates the section
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self._label(self.tab, "label_Temperature_state", "Temperature Control")
        # minimize the state indicator: wrap long state text instead of forcing
        # the card wider, and don't let it dictate a large minimum width
        self.label_Temperature_state.setWordWrap(True)
        self.label_Temperature_state.setMinimumWidth(0)
        self.pButton_Tswitch_ON = QtWidgets.QPushButton("ON", self.tab)
        self.pButton_Tswitch_ON.setObjectName("pButton_Tswitch_ON")
        self.pButton_Tswitch_OFF = QtWidgets.QPushButton("OFF", self.tab)
        self.pButton_Tswitch_OFF.setObjectName("pButton_Tswitch_OFF")
        self.pButton_TEC_Reset = QtWidgets.QPushButton("RESET", self.tab)
        self.pButton_TEC_Reset.setObjectName("pButton_TEC_Reset")
        self.pButton_Temperature_Set = QtWidgets.QPushButton("T SET",
                                                             self.tab)
        self.pButton_Temperature_Set.setObjectName("pButton_Temperature_Set")
        self.doubleSpinBox_Temperature = ChevronDoubleSpinBox(self.tab)
        self.doubleSpinBox_Temperature.setObjectName("doubleSpinBox_Temperature")
        self.doubleSpinBox_Temperature.setDecimals(0)
        self.doubleSpinBox_Temperature.setMinimum(5.0)
        self.doubleSpinBox_Temperature.setMaximum(45.0)
        self.doubleSpinBox_Temperature.setValue(25.0)
        self.doubleSpinBox_Temperature.setMinimumWidth(70)
        self._label(self.tab, "label_Temperature", "Temperature (° C)")
        self._label(self.tab, "indicator_temperature", "0")
        self.gridLayout_4.addWidget(self.label_Temperature_state, 0, 0, 1, 4)
        # Temperature toggle + RESET on a single compact row, left-aligned at
        # their natural width (trailing stretch so they don't fill the sidebar)
        _tec_btns = QtWidgets.QHBoxLayout()
        _tec_btns.setSpacing(4)
        for _b in (self.pButton_Tswitch_ON, self.pButton_Tswitch_OFF,
                   self.pButton_TEC_Reset):
            _tec_btns.addWidget(_b)
        _tec_btns.addStretch(1)
        self.gridLayout_4.addLayout(_tec_btns, 1, 0, 1, 4)
        # T SET on the left, setpoint spinbox pushed to the right margin with an
        # expanding gap between them (mirrors the temperature readout row below).
        _tset_row = QtWidgets.QHBoxLayout()
        _tset_row.setSpacing(4)
        _tset_row.addWidget(self.pButton_Temperature_Set)
        _tset_row.addStretch(1)
        _tset_row.addWidget(self.doubleSpinBox_Temperature)
        self.gridLayout_4.addLayout(_tset_row, 2, 0, 1, 4)
        # temperature readout: label left, live value aligned to the right margin
        _treadout = QtWidgets.QHBoxLayout()
        _treadout.addWidget(self.label_Temperature)
        _treadout.addStretch(1)
        _treadout.addWidget(self.indicator_temperature)
        self.gridLayout_4.addLayout(_treadout, 3, 0, 1, 4)
        self.gridLayout_6.addLayout(self.gridLayout_4, 0, 0, 1, 1)

        # PID Control — hidden, standalone (kept alive for the controller)
        self.tab_2 = QtWidgets.QWidget(self.sidebarContainer)
        self.tab_2.setObjectName("tab_2")
        self.tab_2.hide()
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.pButton_PID_Set = QtWidgets.QPushButton("PID Set", self.tab_2)
        self.pButton_PID_Set.setObjectName("pButton_PID_Set")
        self.cBox_PID = ChevronComboBox(self.tab_2)
        self.cBox_PID.setObjectName("cBox_PID")
        self._label(self.tab_2, "label_Cycling_Time", "Cycling Time [msec]")
        self.spinBox_Cycling_Time = ChevronSpinBox(self.tab_2)
        self.spinBox_Cycling_Time.setObjectName("spinBox_Cycling_Time")
        self.spinBox_Cycling_Time.setMinimum(1)
        self.spinBox_Cycling_Time.setMaximum(1000)
        self.spinBox_Cycling_Time.setValue(50)
        self._label(self.tab_2, "label_P_Share", "P Share [mA/K]")
        self.spinBox_P_Share = ChevronSpinBox(self.tab_2)
        self.spinBox_P_Share.setObjectName("spinBox_P_Share")
        self.spinBox_P_Share.setMaximum(100000)
        self.spinBox_P_Share.setValue(1000)
        self._label(self.tab_2, "label_I_Share", "I Share [mA/(K*sec)]")
        self.spinBox_I_Share = ChevronSpinBox(self.tab_2)
        self.spinBox_I_Share.setObjectName("spinBox_I_Share")
        self.spinBox_I_Share.setMaximum(100000)
        self.spinBox_I_Share.setSingleStep(0)
        self.spinBox_I_Share.setValue(200)
        self._label(self.tab_2, "label_D_Share", "D Share [(mA*s)/K]")
        self.spinBox_D_Share = ChevronSpinBox(self.tab_2)
        self.spinBox_D_Share.setObjectName("spinBox_D_Share")
        self.spinBox_D_Share.setMaximum(100000)
        self.spinBox_D_Share.setValue(100)
        self.gridLayout_3.addWidget(self.pButton_PID_Set, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.cBox_PID, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.label_Cycling_Time, 1, 0, 1, 1)
        self.gridLayout_3.addWidget(self.spinBox_Cycling_Time, 1, 1, 1, 1)
        self.gridLayout_3.addWidget(self.label_P_Share, 2, 0, 1, 1)
        self.gridLayout_3.addWidget(self.spinBox_P_Share, 2, 1, 1, 1)
        self.gridLayout_3.addWidget(self.label_I_Share, 3, 0, 1, 1)
        self.gridLayout_3.addWidget(self.spinBox_I_Share, 3, 1, 1, 1)
        self.gridLayout_3.addWidget(self.label_D_Share, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.spinBox_D_Share, 4, 1, 1, 1)
        # PID section stays hidden (tab_2.hide() above). Advanced temperature/PID
        # control will move to a dedicated window (see HANDOFF).

    # ------------------------------------------------------------------ #
    # center: tabs [ Plots | System Log ]                                #
    # ------------------------------------------------------------------ #
    def _build_readout_card(self, obj_name, title, kind):
        """Horizontal per-overtone readout card (kind 'F' or 'D') shown above
        the matching plot. Creates label_<kind><n>_col (color swatch),
        label_<kind><n> (name) and <kind><n> (value) — the same attribute names
        the controller updates (F0..F9 / D0..D9 values; label_F*_col /
        label_D*_col swatches)."""
        card = QtWidgets.QGroupBox(title)
        card.setObjectName(obj_name)
        row = QtWidgets.QHBoxLayout(card)
        row.setSpacing(14)
        # n names the widget (F0..F9, label_F0_col..), harmonic is what is read:
        # the fundamental is the 1st harmonic and the card now says so.
        for n, harmonic in zip(("0", "3", "5", "7", "9"),
                               ("1", "3", "5", "7", "9")):
            cell = QtWidgets.QWidget(card)
            ch = QtWidgets.QHBoxLayout(cell)
            ch.setContentsMargins(0, 0, 0, 0)
            ch.setSpacing(4)
            sw = self._label(cell, "label_%s%s_col" % (kind, n))
            sw.setFixedSize(11, 11)
            ch.addWidget(sw)
            ch.addWidget(self._label(cell, "label_%s%s" % (kind, n),
                                     "%s%s" % (kind, harmonic)))
            ch.addWidget(self._label(cell, "%s%s" % (kind, n), "0"))
            row.addWidget(cell)
        row.addStretch(1)
        return card

    def _build_center(self):
        self.centerTabs = QtWidgets.QTabWidget()
        self.centerTabs.setObjectName("centerTabs")

        # Plots tab (three pyqtgraph canvases, same names/order as before)
        self.tabPlots = QtWidgets.QWidget()
        self.tabPlots.setObjectName("tabPlots")
        self.verticalLayout_plt = QtWidgets.QVBoxLayout(self.tabPlots)
        self.verticalLayout_plt.setObjectName("verticalLayout_plt")
        self.verticalLayout_plt.setContentsMargins(0, 0, 0, 0)
        self.groupBox_plt = QtWidgets.QGroupBox(self.tabPlots)
        self.groupBox_plt.setObjectName("groupBox_plt")
        self.groupBox_plt.setTitle("")
        _plots = QtWidgets.QVBoxLayout(self.groupBox_plt)
        _plots.setContentsMargins(4, 4, 4, 4)

        # pyqtgraph canvases
        self.plt = GraphicsLayoutWidget(self.groupBox_plt)   # amplitude/phase + temperature
        self.plt.setObjectName("plt")
        self.pltB = GraphicsLayoutWidget(self.groupBox_plt)  # resonance frequency
        self.pltB.setObjectName("pltB")
        self.pltD = GraphicsLayoutWidget(self.groupBox_plt)  # dissipation
        self.pltD.setObjectName("pltD")

        # horizontal per-overtone readout cards above the freq / diss plots
        self.groupFreqReadout = self._build_readout_card(
            "groupFreqReadout", "Frequency (Hz)", "F")
        self.groupDissReadout = self._build_readout_card(
            "groupDissReadout", "Dissipation (ppm)", "D")

        # bottom pane: freq readout + freq plot + diss readout + diss plot
        _bottom = QtWidgets.QWidget()
        _bv = QtWidgets.QVBoxLayout(_bottom)
        _bv.setContentsMargins(0, 0, 0, 0)
        _bv.setSpacing(4)
        _bv.addWidget(self.groupFreqReadout)
        _bv.addWidget(self.pltB, 1)
        _bv.addWidget(self.groupDissReadout)
        _bv.addWidget(self.pltD, 1)

        # vertical splitter (the "slider"): amplitude + temperature on top can be
        # collapsed/hidden by dragging the handle up.
        self.plotSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.plotSplitter.setObjectName("plotSplitter")
        self.plotSplitter.addWidget(self.plt)
        self.plotSplitter.addWidget(_bottom)
        self.plotSplitter.setCollapsible(0, True)   # hide amplitude + temperature
        self.plotSplitter.setCollapsible(1, False)
        self.plotSplitter.setStretchFactor(0, 1)
        self.plotSplitter.setStretchFactor(1, 2)
        self.plotSplitter.setSizes([220, 520])
        _plots.addWidget(self.plotSplitter)

        self.verticalLayout_plt.addWidget(self.groupBox_plt)
        self.centerTabs.addTab(self.tabPlots, "Plots")

        # System Log tab (stdout/stderr mirror, fed by the controller)
        self.tabLog = QtWidgets.QWidget()
        self.tabLog.setObjectName("tabLog")
        log_layout = QtWidgets.QVBoxLayout(self.tabLog)
        log_layout.setContentsMargins(0, 0, 0, 0)
        self.systemLog = QtWidgets.QTextEdit(self.tabLog)
        self.systemLog.setObjectName("systemLog")
        self.systemLog.setReadOnly(True)
        log_layout.addWidget(self.systemLog)
        self.centerTabs.addTab(self.tabLog, "System Log")
