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
    "window": "#f5f5f5",
    "panel": "#ffffff",
    "border": "#cccccc",
    "text": "#333333",
    "muted": "#777777",
    "field_bg": "#ffffff",
    "field_text": "#222222",
    "accent": "#008EC0",
    "accent_text": "#ffffff",
    "disabled_bg": "#e6e6e6",
    "disabled_text": "#9a9a9a",
}

DARK = {
    "name": "dark",
    "window": "#2b2b2b",
    "panel": "#3c3c3c",
    "border": "#555555",
    "text": "#e0e0e0",
    "muted": "#9a9a9a",
    "field_bg": "#323232",
    "field_text": "#e6e6e6",
    "accent": "#008EC0",
    "accent_text": "#ffffff",
    "disabled_bg": "#404040",
    "disabled_text": "#777777",
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

    QGroupBox {{ background: {panel}; border: 1px solid {border};
                 border-radius: 6px; margin-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px;
                        padding: 0 4px; color: {muted}; }}

    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 4px; padding: 2px 4px; }}
    QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background: {disabled_bg}; color: {disabled_text}; }}
    QComboBox QAbstractItemView {{ background: {panel}; color: {text};
        selection-background-color: {accent}; selection-color: {accent_text}; }}

    /* Live readout fields (frequency / dissipation / temperature) */
    QLabel#F0, QLabel#F3, QLabel#F5, QLabel#F7, QLabel#F9,
    QLabel#D0, QLabel#D3, QLabel#D5, QLabel#D7, QLabel#D9,
    QLabel#indicator_temperature {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border}; border-radius: 3px; padding: 2px; }}

    /* State banner keeps its inline light background; force dark text so it
       stays readable on the dark theme too. */
    QLabel#label_Temperature_state {{ color: #222222; }}

    QTabWidget::pane {{ border: 1px solid {border}; background: {panel}; }}
    QTabBar::tab {{ background: {window}; color: {muted}; border: 1px solid {border};
        border-bottom: none; padding: 4px 10px;
        border-top-left-radius: 5px; border-top-right-radius: 5px; }}
    QTabBar::tab:selected {{ background: {panel}; color: {text}; }}

    /* System Log console (theme-aware, monospace) */
    QTextEdit#systemLog {{ background: {field_bg}; color: {field_text};
        border: 1px solid {border};
        font-family: "Menlo", "Consolas", "Courier New", monospace; }}

    QMenuBar {{ background: {window}; color: {text}; }}
    QMenuBar::item:selected {{ background: {accent}; color: {accent_text}; }}
    QMenu {{ background: {panel}; color: {text}; border: 1px solid {border}; }}
    QMenu::item:selected {{ background: {accent}; color: {accent_text}; }}

    QProgressBar {{ background: {field_bg}; color: {text}; border: 1px solid {border};
        border-radius: 4px; text-align: center; }}
    QProgressBar::chunk {{ background: {accent}; }}

    QRadioButton, QCheckBox {{ background: transparent; color: {text}; }}
    QScrollArea {{ border: none; background: {window}; }}
    """.format(**p)
