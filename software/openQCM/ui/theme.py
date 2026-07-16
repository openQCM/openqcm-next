"""
VER 0.1.7 — Theme system for the openQCM NEXT GUI.

Minimalist scientific restyle (light + dark). Drop-in replacement for
ui/theme.py: same public API (``palette(name)``, ``qss(p)``, ``PLOT[name]``)
and the same object-name / property selectors the controller already uses, so
no controller changes are required for the styling itself.

What changed vs 0.1.6:
- refreshed light/dark palettes (softer surfaces, hairline borders)
- IBM Plex Sans (UI) + IBM Plex Mono (numeric readouts) typography
- rounder cards (11px), pill overtone chips (9px), taller accent Start button
- monospace tabular readouts (F0..D9, indicators, status-bar F/D/T/S)
- per-theme plot grid color exposed via PLOT[...]["grid"]

Fonts: bundle the IBM Plex .ttf files and register them at startup with
QFontDatabase.addApplicationFont(...) (see app.py snippet in the handoff).
If the fonts are missing, the stacks fall back to the platform UI font.
"""

# --- Typography -----------------------------------------------------------
FONT_SANS = '"IBM Plex Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_MONO = '"IBM Plex Mono", "SF Mono", "Menlo", "Consolas", monospace'

# --- Palettes -------------------------------------------------------------
LIGHT = {
    "name": "light",
    "window": "#f4f6f8",
    "panel": "#ffffff",
    "panel2": "#fafbfc",
    "border": "#e4e8ec",
    "hair": "#f0f2f5",
    "text": "#1c2126",
    "muted": "#6b7280",
    "faint": "#9aa0a6",
    "field_bg": "#f2f4f6",
    "field_text": "#1c2126",
    "accent": "#008ec0",
    "accent_hover": "#007aa5",
    "accent_text": "#ffffff",
    "disabled_bg": "#eceef1",
    "disabled_text": "#9aa0a6",
    "ok": "#2fa36b",
    "danger": "#d13438",
    "danger_hover": "#e03b3b",
    "warn": "#e0932f",
}

DARK = {
    "name": "dark",
    "window": "#161819",
    "panel": "#202325",
    "panel2": "#1a1d1f",
    "border": "#31363a",
    "hair": "#282d31",
    "text": "#e7eaec",
    "muted": "#9aa0a6",
    "faint": "#697077",
    "field_bg": "#2a2e31",
    "field_text": "#e7eaec",
    "accent": "#18a8d2",
    "accent_hover": "#3fb9dd",
    "accent_text": "#ffffff",
    "disabled_bg": "#2a2e31",
    "disabled_text": "#697077",
    "ok": "#47c08a",
    "danger": "#ef5350",
    "danger_hover": "#f4645f",
    "warn": "#e2a54c",
}

# --- pyqtgraph plot colors per theme -------------------------------------
# bg: GraphicsLayoutWidget background; axis: axis line + tick + label color;
# title: plot title color; grid: gridline color. Frequency (blue ramp) and
# dissipation (brown) curve colors live in Constants (see handoff note).
PLOT = {
    "light": {"bg": "w", "axis": "#8a9199", "title": "#1c2126", "grid": "#eef1f4"},
    "dark":  {"bg": (23, 25, 27), "axis": "#697077", "title": "#e7eaec", "grid": "#262b2f"},
}


def palette(name):
    """Return the palette dict for 'dark' or 'light' (default light)."""
    return DARK if name == "dark" else LIGHT


def qss(p):
    """Build the application-wide Qt Style Sheet for palette dict ``p``."""
    return """
    * {{ font-family: {sans}; }}
    QMainWindow, QWidget#centralwidget {{ background: {window}; }}
    QWidget {{ color: {text}; font-size: 13px; }}
    QLabel {{ background: transparent; color: {text}; }}
    QToolTip {{ background: {panel}; color: {text}; border: 1px solid {border};
        padding: 4px 6px; }}

    /* Generic buttons (theme-aware base; accented buttons override below) */
    QPushButton {{ background: {field_bg}; color: {text};
        border: 1px solid {border}; border-radius: 8px; padding: 7px 12px; }}
    QPushButton:hover {{ background: {panel}; }}
    QPushButton:pressed {{ background: {disabled_bg}; }}
    QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}

    /* Scroll bars */
    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px;
        min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {muted}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: {border}; border-radius: 5px;
        min-width: 30px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* Hairline separators follow the theme */
    QFrame[frameShape="4"] {{ background: {hair}; border: none; max-height: 1px; }}
    QSplitter::handle {{ background: {window}; }}
    QSplitter::handle:hover {{ background: {border}; }}

    /* Base group box */
    QGroupBox {{ background: {panel}; border: 1px solid {border};
                 border-radius: 11px; margin-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px;
                        padding: 0 4px; color: {faint}; }}

    /* Sidebar cards: bold title rendered inside the rounded card */
    QGroupBox#groupConnection, QGroupBox#groupSetup,
    QGroupBox#groupBox_data, QGroupBox#groupTempPID {{
        margin-top: 0px; padding: 10px; padding-top: 32px; }}
    QGroupBox#groupConnection::title, QGroupBox#groupSetup::title,
    QGroupBox#groupBox_data::title, QGroupBox#groupTempPID::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 14px; top: 11px; color: {faint};
        font-weight: 600; font-size: 11px; }}

    /* Menu-bar corner theme toggle */
    QToolButton#themeToggleButton {{ color: {muted}; background: {panel};
        border: 1px solid {border}; border-radius: 7px;
        padding: 4px 10px; margin: 3px 8px; }}
    QToolButton#themeToggleButton:hover {{ color: {text}; }}

    /* Inputs */
    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 8px; padding: 7px 10px;
        min-height: 20px; }}
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {accent}; }}
    QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background: {disabled_bg}; color: {disabled_text}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{ background: {panel}; color: {text};
        border: 1px solid {border};
        selection-background-color: {accent}; selection-color: {accent_text}; }}
    QSpinBox, QDoubleSpinBox {{ font-family: {mono}; }}

    /* Live readout values (borderless bold monospace, tabular) */
    QLabel#F0, QLabel#F3, QLabel#F5, QLabel#F7, QLabel#F9,
    QLabel#D0, QLabel#D3, QLabel#D5, QLabel#D7, QLabel#D9,
    QLabel#indicator_temperature, QLabel#time_indicator {{
        background: transparent; color: {field_text}; border: none;
        font-family: {mono}; font-weight: 500; padding: 2px; }}

    /* Big temperature indicator */
    QLabel#indicator_temperature {{ font-size: 22px; }}

    /* State banner: readable dark text on its light inline background */
    QLabel#label_Temperature_state {{ color: #1c2126; }}

    /* Tabs */
    QTabWidget::pane {{ border: 1px solid {border}; background: {panel};
        border-radius: 8px; top: -1px; }}
    QTabBar::tab {{ background: {window}; color: {muted}; border: 1px solid {border};
        border-bottom: none; padding: 6px 14px;
        border-top-left-radius: 8px; border-top-right-radius: 8px; }}
    QTabBar::tab:selected {{ background: {panel}; color: {accent}; font-weight: 600; }}

    /* Datalog filename label */
    QLabel#lblLogFile {{ color: {accent}; font-weight: 500; font-family: {mono}; }}

    /* System Log console */
    QTextEdit#systemLog {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 8px;
        font-family: {mono}; font-size: 12px; }}

    /* Menu bar */
    QMenuBar {{ background: {panel2}; color: {text}; padding: 3px 6px;
        border-bottom: 1px solid {border}; }}
    QMenuBar::item {{ padding: 5px 11px; border-radius: 6px; color: {muted}; }}
    QMenuBar::item:selected {{ background: {accent}; color: {accent_text}; }}
    QMenu {{ background: {panel}; color: {text}; border: 1px solid {border};
        border-radius: 8px; padding: 4px; }}
    QMenu::item {{ padding: 5px 12px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {accent}; color: {accent_text}; }}

    /* Progress bar */
    QProgressBar {{ background: {field_bg}; color: {text}; border: 1px solid {border};
        border-radius: 8px; text-align: center; font-family: {mono}; font-size: 11px; }}
    QProgressBar::chunk {{ background: {accent}; border-radius: 7px; }}

    /* Single Start/Stop toggle: accent when idle, red while running */
    QPushButton#pButton_Start {{ background: {accent}; color: {accent_text};
        border: none; border-radius: 10px; padding: 10px 12px;
        font-weight: 600; font-size: 15px; min-height: 26px; }}
    QPushButton#pButton_Start:hover {{ background: {accent_hover}; }}
    QPushButton#pButton_Start[running="true"] {{ background: {danger}; }}
    QPushButton#pButton_Start[running="true"]:hover {{ background: {danger_hover}; }}
    QPushButton#pButton_Start:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}

    /* Connection buttons: Connect = primary, Refresh = outline */
    QPushButton#pButton_Connect {{ background: {accent}; color: {accent_text};
        border: none; border-radius: 8px; padding: 8px 12px; font-weight: 600; }}
    QPushButton#pButton_Connect:hover {{ background: {accent_hover}; }}
    QPushButton#pButton_Refresh {{ background: transparent; color: {accent};
        border: 1px solid {accent}; border-radius: 8px; padding: 8px 12px; }}
    QPushButton#pButton_Refresh:hover {{ background: {field_bg}; }}
    QPushButton#pButton_Connect:disabled, QPushButton#pButton_Refresh:disabled {{
        background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}

    /* Overtone quick-select chips F0..F9 (pill) */
    QPushButton[overtoneBtn="true"] {{ background: {field_bg}; color: {text};
        border: 1px solid {border}; border-radius: 9px; padding: 6px 12px;
        min-width: 30px; font-weight: 500; }}
    QPushButton[overtoneBtn="true"]:hover {{ border-color: {accent}; }}
    QPushButton[overtoneBtn="true"]:checked {{ background: {accent}; color: {accent_text};
        border-color: {accent}; }}
    QPushButton[overtoneBtn="true"]:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}
    QPushButton[overtoneBtn="true"]:checked:disabled {{ background: {accent}; color: {accent_text}; }}

    QRadioButton, QCheckBox {{ background: transparent; color: {text}; }}
    QScrollArea {{ border: none; background: {window}; }}

    /* Sidebar container + scroll viewport follow the theme */
    QWidget#sidebarContainer {{ background: {panel2}; }}
    QScrollArea#sidebarScroll, QScrollArea#sidebarScroll > QWidget > QWidget {{
        background: {panel2}; }}

    /* Bottom status bar */
    QFrame#statusBarFrame {{ background: {panel2}; border-top: 1px solid {border}; }}
    QLabel#statusFreqValue, QLabel#statusDissValue,
    QLabel#statusTempValue, QLabel#statusSampValue {{
        color: {text}; font-weight: 500; font-family: {mono}; padding: 0 4px; }}
    QLabel#infobar {{ color: {muted}; }}
    QLabel#infostatus {{ font-weight: 500; }}
    """.format(sans=FONT_SANS, mono=FONT_MONO, **p)
