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
    "disabled_bg": "#3f4143",
    "disabled_text": "#7c8085",
}

# --- pyqtgraph plot colors per theme -------------------------------------
# bg: GraphicsLayoutWidget background; axis: axis line + tick + label color;
# title: plot title color. Frequency (blue) / dissipation (brown) curve colors
# are theme-independent and live in Constants.
PLOT = {
    "light": {"bg": "w", "axis": "#666666", "title": "#333333"},
    "dark": {"bg": (43, 43, 43), "axis": "#c8c8c8", "title": "#e0e0e0"},
}


def palette(name):
    """Return the palette dict for 'dark' or 'light' (default light)."""
    return DARK if name == "dark" else LIGHT


def qss(p):
    """Build the application-wide Qt Style Sheet for palette dict ``p``."""
    return """
    QMainWindow, QWidget#centralwidget {{ background: {window}; }}
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
    QGroupBox#groupBox_data, QGroupBox#groupTempPID {{
        margin-top: 0px; padding: 6px; padding-top: 28px; }}
    QGroupBox#groupConnection::title, QGroupBox#groupSetup::title,
    QGroupBox#groupBox_data::title, QGroupBox#groupTempPID::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 12px; top: 8px; color: {text};
        font-weight: bold; font-size: 13px; }}

    /* R2: menu-bar corner theme toggle */
    QToolButton#themeToggleButton {{ color: {muted}; background: {panel};
        border: 1px solid {border}; border-radius: 4px;
        padding: 2px 8px; margin: 2px 6px; }}

    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 6px; padding: 4px 8px;
        min-height: 20px; }}
    QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background: {disabled_bg}; color: {disabled_text}; }}
    QComboBox QAbstractItemView {{ background: {panel}; color: {text};
        selection-background-color: {accent}; selection-color: {accent_text}; }}

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

    /* System Log console (theme-aware, monospace) */
    QTextEdit#systemLog {{ background: {field_bg}; color: {field_text};
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
        border: none; border-radius: 8px; padding: 8px 12px;
        font-weight: bold; font-size: 14px; }}
    QPushButton#pButton_Start:hover {{ background: #007aa5; }}
    QPushButton#pButton_Start[running="true"] {{ background: #d32f2f; }}
    QPushButton#pButton_Start[running="true"]:hover {{ background: #e03b3b; }}
    QPushButton#pButton_Start:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}

    /* Connection buttons (3e, R2 polish): Connect = primary, Refresh = outline */
    QPushButton#pButton_Connect {{ background: {accent}; color: {accent_text};
        border: none; border-radius: 6px; padding: 5px 12px; font-weight: bold; }}
    QPushButton#pButton_Connect:hover {{ background: #007aa5; }}
    QPushButton#pButton_Refresh {{ background: transparent; color: {accent};
        border: 1px solid {accent}; border-radius: 6px; padding: 5px 12px; }}
    QPushButton#pButton_Refresh:hover {{ background: {field_bg}; }}
    QPushButton#pButton_Connect:disabled, QPushButton#pButton_Refresh:disabled {{
        background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}

    /* Overtone quick-select chips F0..F9 (3b, R2 mockup look) */
    QPushButton[overtoneBtn="true"] {{ background: {field_bg}; color: {text};
        border: 1px solid {border}; border-radius: 11px; padding: 3px 12px; min-width: 28px; }}
    QPushButton[overtoneBtn="true"]:checked {{ background: {accent}; color: {accent_text};
        border-color: {accent}; }}
    QPushButton[overtoneBtn="true"]:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}
    QPushButton[overtoneBtn="true"]:checked:disabled {{ background: {accent}; color: {accent_text}; }}

    QRadioButton, QCheckBox {{ background: transparent; color: {text}; }}
    QScrollArea {{ border: none; background: {window}; }}

    /* R2: the sidebar container and the scroll-area viewport must follow the
       theme too (they defaulted to the platform palette on the dark theme) */
    QWidget#sidebarContainer {{ background: {window}; }}
    QScrollArea#sidebarScroll, QScrollArea#sidebarScroll > QWidget > QWidget {{
        background: {window}; }}

    /* Bottom status bar (R2) */
    QFrame#statusBarFrame {{ background: {panel}; border-top: 1px solid {border}; }}
    QLabel#statusFreqValue, QLabel#statusDissValue,
    QLabel#statusTempValue, QLabel#statusSampValue {{
        color: {text}; font-weight: bold; padding: 0 4px; }}
    QLabel#infobar {{ color: {muted}; }}
    """.format(**p)
