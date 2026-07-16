IBM Plex fonts (v0.1.7 GUI restyle)
===================================

Drop the following five .ttf files here so the GUI uses IBM Plex (UI) and
IBM Plex Mono (numeric readouts). They are registered at startup by
OPENQCM._load_fonts() in app.py.

    IBMPlexSans-Regular.ttf
    IBMPlexSans-Medium.ttf
    IBMPlexSans-SemiBold.ttf
    IBMPlexMono-Regular.ttf
    IBMPlexMono-Medium.ttf

Source (SIL Open Font License, redistributable): https://github.com/IBM/plex

If the files are absent the theme QSS font stacks fall back to the platform UI
font — the application still works, just without the IBM Plex typography.
