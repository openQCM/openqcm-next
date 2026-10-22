#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
openQCM NEXT Application Launcher

Main entry point for the openQCM NEXT application.
Run with: python run.py

This wrapper provides a clean, single entry point that works both in
development and when packaged (e.g. with PyInstaller). The application
logic lives in the ``openQCM`` package (``openQCM/app.py``).

For development:
    cd software
    python run.py

For module execution:
    cd software
    python -m openQCM
"""


if __name__ == '__main__':
    # Imported here, not at module level: every process the acquisition spawns
    # re-runs this file as __mp_main__, and a top-level import made each of them
    # load the whole GUI (mainWindow, pyqtgraph) for nothing -- measured, about
    # 0.25 s of CPU and 27 MB per child per START.
    from openQCM.app import OPENQCM
    OPENQCM().run()
