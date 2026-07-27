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

from openQCM.app import OPENQCM


if __name__ == '__main__':
    OPENQCM().run()
