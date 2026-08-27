"""
VER 0.1.6 — Theme system for the openQCM NEXT GUI (Phase 0 of the GUI redesign).

Provides two palettes (light / dark) and a single parameterised Qt Style Sheet
builder plus per-theme pyqtgraph plot colors. Adapted from the openQCM Q-1 v3.0
theme system, but kept self-contained so the rest of the app only needs to call
``theme.qss(palette)`` and ``theme.PLOT[name]``.

Design notes:
- Accent stays openQCM blue (#008EC0) and dissipation brown (#DD8E6B) on both
  themes (matches Q-1), so those two are not part of the light/dark swap.
- State-coloured labels (infostatus, label_Temperature_state) keep their inline
  background colours (yellow/red/green/white) set at runtime; the QSS only forces
  readable dark text on label_Temperature_state (its backgrounds are always light).
"""

# --- Palettes -------------------------------------------------------------
LIGHT = {
    "name": "light",
    "window": "#f2f4f7",
    "panel": "#ffffff",
    "border": "#dfe3e8",
    "text": "#2f3337",
    "muted": "#75797e",
    "field_bg": "#f5f6f8",
    "field_text": "#222222",
    "accent": "#008EC0",
    "accent_text": "#ffffff",
    "brown": "#DD8E6B",
    "brown_hover": "#cf7f5c",
    "disabled_bg": "#eceef1",
    "disabled_text": "#9aa0a6",
}

DARK = {
    "name": "dark",
    "window": "#2b2b2b",
    "panel": "#37393b",
    "border": "#4d4f52",
    "text": "#e0e0e0",
    "muted": "#9a9a9a",
    "field_bg": "#2f3133",
    "field_text": "#e6e6e6",
    "accent": "#008EC0",
    "accent_text": "#ffffff",
    "brown": "#DD8E6B",
    "brown_hover": "#cf7f5c",
    "disabled_bg": "#3f4143",
    "disabled_text": "#7c8085",
}

# --- pyqtgraph plot colors per theme -------------------------------------
# bg: GraphicsLayoutWidget background; axis: axis line + tick + label color;
# title: plot title color. Frequency (blue) / dissipation (brown) curve colors
# are theme-independent and live in Constants.
# The plot panels inherit the interface's own window grey rather than carrying
# their own colours: the dark panel was already (43,43,43) = DARK["window"], and
# the light one was pure white, which is the only place the two disagreed. On
# white the palest overtone of each series all but vanished.
PLOT = {
    "light": {"bg": LIGHT["window"], "axis": "#666666", "title": "#333333",
              "curve": "#333333"},
    "dark": {"bg": DARK["window"], "axis": "#c8c8c8", "title": "#e0e0e0", "curve": "#e0e0e0"},
}


def palette(name):
    """Return the palette dict for 'dark' or 'light' (default light)."""
    return DARK if name == "dark" else LIGHT


def popup_qss(p):
    """Style sheet for a combo box popup, to be set ON the popup widgets.

    Separate from :func:`qss` because the popup container is a top-level window
    that the main window's style sheet does not reach: see
    ChevronComboBox._style_popup. Selectors are unqualified for that reason -- the
    sheet is applied to the container and the list themselves.
    """
    return """
    QFrame {{ background: {panel}; border: 1px solid {border}; }}
    QAbstractItemView {{ background: {panel}; color: {text};
        border: none; padding: 4px; outline: none;
        selection-background-color: {accent}; selection-color: {accent_text}; }}
    QAbstractItemView::item {{ min-height: 24px; padding: 3px 8px;
        border-radius: 5px; }}
    QAbstractItemView::item:selected {{ background: {accent};
        color: {accent_text}; }}
    """.format(**p)


def qss(p):
    """Build the application-wide Qt Style Sheet for palette dict ``p``."""
    return """
    /* QDialog is here because the auxiliary views (Raw Data View, Peak Data
       View, Datalog View) are dialogs: without it their pyqtgraph canvases went
       dark while the window around them stayed at the platform default, which
       left the grey info label on top of them barely readable. */
    QMainWindow, QDialog, QWidget#centralwidget {{ background: {window}; }}
    QWidget {{ color: {text}; }}
    QLabel {{ background: transparent; color: {text}; }}

    /* Generic buttons (theme-aware base; accented buttons override below) */
    QPushButton {{ background: {field_bg}; color: {text};
        border: 1px solid {border}; border-radius: 4px; padding: 4px 10px; }}
    QPushButton:hover {{ background: {panel}; }}
    QPushButton:pressed {{ background: {disabled_bg}; }}
    QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}

    /* Scroll bars (native ones stay light on the dark theme otherwise) */
    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px;
        min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {muted}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: {border}; border-radius: 5px;
        min-width: 30px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* Horizontal separator lines follow the theme */
    QFrame[frameShape="4"] {{ background: {border}; border: none; max-height: 1px; }}

    QSplitter::handle {{ background: {border}; }}

    QGroupBox {{ background: {panel}; border: 1px solid {border};
                 border-radius: 10px; margin-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px;
                        padding: 0 4px; color: {muted}; }}

    /* R2 mockup cards: bold title rendered inside the rounded card */
    QGroupBox#groupConnection, QGroupBox#groupSetup,
    QGroupBox#groupBox_data, QGroupBox#groupTempPID,
    QGroupBox#groupPlotControls {{
        margin-top: 0px; padding: 6px; padding-top: 28px; }}
    QGroupBox#groupConnection::title, QGroupBox#groupSetup::title,
    QGroupBox#groupBox_data::title, QGroupBox#groupTempPID::title,
    QGroupBox#groupPlotControls::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 12px; top: 8px; color: {text}; font-size: 14px; }}
    /* Qt ignores font-weight on ::title, so the bold weight is set on the
       QGroupBox widget font in the builder; reset the card CONTENT to normal
       so only the title is bold. */
    QGroupBox#groupConnection QWidget, QGroupBox#groupSetup QWidget,
    QGroupBox#groupBox_data QWidget, QGroupBox#groupTempPID QWidget,
    QGroupBox#groupPlotControls QWidget {{ font-weight: normal; }}

    /* Compact cards that sit directly on a plot: the frequency / dissipation
       readouts, and anything that opts in with the cardCompact property. The
       property selector is there so a card this file does not know the name of
       -- one built on a branch, say -- can take the same look without adding a
       dead #name selector here. ⚠️ Qt evaluates a property selector when the
       sheet is applied: set the property BEFORE the style sheet reaches the
       widget, or unpolish/polish it afterwards, or nothing happens. */
    QGroupBox#groupFreqReadout, QGroupBox#groupDissReadout,
    QGroupBox[cardCompact="true"] {{
        margin-top: 0px; padding: 4px; padding-top: 20px; }}
    QGroupBox#groupFreqReadout::title, QGroupBox#groupDissReadout::title,
    QGroupBox[cardCompact="true"]::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 10px; top: 3px; color: {muted}; font-weight: bold; font-size: 11px; }}

    /* R2: menu-bar corner theme toggle */
    QToolButton#themeToggleButton {{ color: {muted}; background: {panel};
        border: 1px solid {border}; border-radius: 4px;
        padding: 2px 8px; margin: 2px 6px; }}

    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 8px; padding: 6px 10px;
        min-height: 20px; }}
    QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background: {disabled_bg}; color: {disabled_text};
        border-color: {disabled_bg}; }}

    /* Combo boxes: the platform arrow is a square button with a hard divider,
       which is the dated part. It is switched off here and ui/widgets.py's
       ChevronComboBox paints a thin chevron in its place -- Qt 5.9.7 ignores the
       CSS-triangle trick on ::down-arrow, so a painted glyph is the only route
       that needs no per-theme, per-density image asset. The right padding leaves
       room for it. */
    QComboBox {{ padding-right: 30px; }}
    QComboBox:hover {{ border-color: {muted}; }}
    QComboBox:focus, QComboBox:on {{ border-color: {accent}; }}
    QComboBox::drop-down {{ width: 0px; border: none; background: transparent; }}
    QComboBox::down-arrow {{ image: none; width: 0px; height: 0px; }}

    /* Spin boxes get the same treatment, since they sit in the same cards and the
       platform up/down pair is the same dated chrome. The buttons stay CLICKABLE:
       only their border and arrow are removed, so pressing where the painted
       glyphs are still steps the value. */
    QSpinBox, QDoubleSpinBox {{ padding-right: 26px; }}
    QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {muted}; }}
    QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {accent}; }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-origin: border; width: 22px; border: none;
        background: transparent; }}
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        subcontrol-position: top right; }}
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-position: bottom right; }}
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: none; width: 0px; height: 0px; }}

    /* The open list. SQUARE corners on purpose: the popup is an opaque window and
       a rounded background leaves the window's own colour showing at the four
       corners -- white on macOS, which is exactly the frame that showed up on the
       dark theme. The items keep their radius, which is where it reads. The
       container QFrame is covered too, belt and braces with the setFrameShape in
       ui/widgets.py. */
    QComboBox QFrame {{ background: {panel}; border: none; }}
    QComboBox QAbstractItemView {{ background: {panel}; color: {text};
        border: 1px solid {border}; border-radius: 0px; padding: 4px;
        outline: none;
        selection-background-color: {accent}; selection-color: {accent_text}; }}
    QComboBox QAbstractItemView::item {{ min-height: 24px; padding: 3px 8px;
        border-radius: 5px; }}
    QComboBox QAbstractItemView::item:selected {{ background: {accent};
        color: {accent_text}; }}

    /* Live readout values (mockup look: borderless bold text) */
    QLabel#F0, QLabel#F3, QLabel#F5, QLabel#F7, QLabel#F9,
    QLabel#D0, QLabel#D3, QLabel#D5, QLabel#D7, QLabel#D9,
    QLabel#indicator_temperature, QLabel#time_indicator {{
        background: transparent; color: {field_text}; border: none;
        font-weight: bold; padding: 2px; }}

    /* State banner keeps its inline light background; force dark text so it
       stays readable on the dark theme too. */
    QLabel#label_Temperature_state {{ color: #222222; }}

    QTabWidget::pane {{ border: 1px solid {border}; background: {panel};
        border-radius: 6px; top: -1px; }}
    QTabBar::tab {{ background: {window}; color: {muted}; border: 1px solid {border};
        border-bottom: none; padding: 5px 12px;
        border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {panel}; color: {accent}; font-weight: bold; }}

    /* Datalog filename label (Phase 3d) */
    QLabel#lblLogFile {{ color: {accent}; font-weight: bold; }}

    /* Monospace consoles: the System Log, and Datalog View's analysis report.
       Named rather than a property selector -- both widgets live in this repo
       and this file can see their names, so there is nothing to generalise. */
    QTextEdit#systemLog, QTextEdit#datalogReport {{
        background: {field_bg}; color: {field_text};
        border: 1px solid {border};
        font-family: "Menlo", "Consolas", "Courier New", monospace; }}

    QMenuBar {{ background: {window}; color: {text}; padding: 2px 4px; }}
    QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
    QMenuBar::item:selected {{ background: {accent}; color: {accent_text}; }}
    QMenu {{ background: {panel}; color: {text}; border: 1px solid {border}; }}
    QMenu::item:selected {{ background: {accent}; color: {accent_text}; }}

    QProgressBar {{ background: {field_bg}; color: {text}; border: 1px solid {border};
        border-radius: 8px; text-align: center; }}
    QProgressBar::chunk {{ background: {accent}; border-radius: 7px; }}

    /* Single Start/Stop toggle (3a, R2): accent blue when idle (mockup),
       red while running */
    QPushButton#pButton_Start {{ background: {accent}; color: {accent_text};
        border: none; border-radius: 8px; padding: 10px 12px;
        font-weight: normal; font-size: 17px; }}
    QPushButton#pButton_Start:hover {{ background: #007aa5; }}
    QPushButton#pButton_Start[running="true"] {{ background: {brown}; }}
    QPushButton#pButton_Start[running="true"]:hover {{ background: {brown_hover}; }}
    QPushButton#pButton_Start:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}

    /* Secondary "outline" buttons — the standard look for secondary-importance
       controls (less invasive; width adapts to the label). Covers Connect/
       Disconnect, Refresh, the plot controls (AUTO / SET REF / CLEAR) and the
       temperature toggle + TEC Reset. Blue outline by default; brown when a
       toggle is in its "deactivate" state (Disconnect, temperature OFF); grey
       when disabled. */
    QPushButton#pButton_Connect, QPushButton#pButton_Refresh,
    QPushButton#pButton_Autoscale, QPushButton#pButton_Reference,
    QPushButton#pButton_Reference_Not, QPushButton#pButton_Clear,
    QPushButton#pButton_Tswitch_ON, QPushButton#pButton_TEC_Reset,
    QPushButton#pButton_Temperature_Set, QPushButton#pButton_NScale {{
        background: transparent; color: {accent}; border: 1px solid {accent};
        border-radius: 6px; padding: 4px 10px; min-width: 0px; }}
    QPushButton#pButton_Connect:hover, QPushButton#pButton_Refresh:hover,
    QPushButton#pButton_Autoscale:hover, QPushButton#pButton_Reference:hover,
    QPushButton#pButton_Reference_Not:hover, QPushButton#pButton_Clear:hover,
    QPushButton#pButton_Tswitch_ON:hover, QPushButton#pButton_TEC_Reset:hover,
    QPushButton#pButton_Temperature_Set:hover {{
        background: {field_bg}; }}
    QPushButton#pButton_Connect[connected="true"] {{ color: {brown}; border-color: {brown}; }}
    QPushButton#pButton_Tswitch_ON[tecOn="true"] {{ color: {brown}; border-color: {brown}; }}
    /* N-SCALE reads the other way round from the two above, and deliberately:
       it is a checkable state, not a "press me to undo" affordance, so brown
       marks the plots showing measured hertz and blue marks them divided by n.
       Same reading as the overtone chips, where accent means engaged. */
    QPushButton#pButton_NScale {{ color: {brown}; border-color: {brown}; }}
    QPushButton#pButton_NScale:checked {{ color: {accent}; border-color: {accent}; }}
    QPushButton#pButton_Connect:disabled, QPushButton#pButton_Refresh:disabled,
    QPushButton#pButton_Autoscale:disabled, QPushButton#pButton_Reference:disabled,
    QPushButton#pButton_Reference_Not:disabled, QPushButton#pButton_Clear:disabled,
    QPushButton#pButton_Tswitch_ON:disabled, QPushButton#pButton_TEC_Reset:disabled,
    QPushButton#pButton_Temperature_Set:disabled, QPushButton#pButton_NScale:disabled {{
        background: transparent; color: {disabled_text}; border-color: {border}; }}

    /* Overtone quick-select chips F0..F9. ⚠️ No min-width here: the width is
       set on the widget (mainWindow_ui.OVERTONE_CHIP_WIDTH) and a style sheet
       min-width overrides the widget's minimum, so `min-width: 0px` silently
       let the layout squeeze them back down to their label. */
    QPushButton[overtoneBtn="true"] {{ background: {field_bg}; color: {text};
        border: 1px solid {border}; border-radius: 7px; padding: 2px 3px; }}

    /* (Temperature toggle + TEC Reset share the secondary-outline rule above.) */
    QPushButton[overtoneBtn="true"]:checked {{ background: {accent}; color: {accent_text};
        border-color: {accent}; }}
    QPushButton[overtoneBtn="true"]:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}
    QPushButton[overtoneBtn="true"]:checked:disabled {{ background: {accent}; color: {accent_text}; }}

    QRadioButton, QCheckBox {{ background: transparent; color: {text}; }}
    QScrollArea {{ border: none; background: {window}; }}

    /* R2: the sidebar container and the scroll-area viewport must follow the
       theme too (they defaulted to the platform palette on the dark theme) */
    QWidget#sidebarContainer {{ background: {window}; }}
    QWidget#sidebarPane,
    QScrollArea#sidebarScroll, QScrollArea#sidebarScroll > QWidget > QWidget {{
        background: {window}; }}

    /* Bottom status bar (R2) */
    QFrame#statusBarFrame {{ background: {panel}; border-top: 1px solid {border}; }}
    QLabel#statusTempValue, QLabel#statusSampValue {{
        color: {text}; font-weight: bold; padding: 0 4px; }}
    /* The message is the only place a warning or an error is written now that the
       coloured pill and the <font> tags are gone, so it sits at full contrast
       rather than muted -- Q-1 gives its statusMessage the plain text colour for
       the same reason. */
    QLabel#infobar {{ color: {text}; }}
    /* default for the state dot, before any state has been set */
    QLabel#statusIndicator {{ color: {muted}; font-size: 14px; }}
    """.format(**p)
