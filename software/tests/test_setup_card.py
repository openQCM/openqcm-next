# -*- coding: utf-8 -*-
"""The Measurement Setup card: no two widgets in one cell, and the estimator box is there.

    cd software && PYTHONPATH=. python -m unittest tests.test_setup_card -v

⚠️ Why this exists: on 2026-09-16 the estimator checkbox was added at row 5 of `gridSetup`, where the
elapsed-time block already was. A QGridLayout draws two items of one cell ON TOP of each other, and
"Time elapsed (sec)" and the checkbox came out overprinted in the sidebar. Nothing failed, nothing
warned; only the screen said so. This test is the numeric observable that a cell is used twice.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest

from PyQt5 import QtWidgets

from openQCM.ui.mainWindow_ui import Ui_MainWindow

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _cells(grid):
    """{(row, col): [names]} of everything in a QGridLayout, spans expanded."""
    used = {}
    for i in range(grid.count()):
        item = grid.itemAt(i)
        r, c, rs, cs = grid.getItemPosition(i)
        w = item.widget()
        name = w.objectName() or w.__class__.__name__ if w is not None else (
            item.layout().objectName() or "layout" if item.layout() is not None else "spacer")
        for rr in range(r, r + max(rs, 1)):
            for cc in range(c, c + max(cs, 1)):
                used.setdefault((rr, cc), []).append(name)
    return used


class SetupCardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mw = QtWidgets.QMainWindow()
        cls.ui = Ui_MainWindow()
        cls.ui.setupUi(cls.mw)

    def test_no_cell_of_the_setup_grid_holds_two_items(self):
        clashes = {k: v for k, v in _cells(self.ui.gridSetup).items() if len(v) > 1}
        self.assertEqual(clashes, {}, "cells used twice: %s" % clashes)

    def test_the_estimator_box_is_in_the_setup_card_and_off(self):
        chk = self.ui.chk_ExperimentalFit
        self.assertIs(chk.parent(), self.ui.groupSetup)
        self.assertGreaterEqual(self.ui.gridSetup.indexOf(chk), 0)
        self.assertFalse(chk.isChecked())
        self.assertTrue(chk.toolTip())

    def test_its_label_fits_the_sidebar(self):
        """The card is ~290 px wide and a QCheckBox neither wraps nor elides."""
        chk = self.ui.chk_ExperimentalFit
        # offscreen has no real fonts (HANDOFF §6), so this bounds the TEXT, not its pixels:
        # 27 characters at the ~7.6 px/char measured on the real platform is ~205 px plus the
        # ~22 px indicator, inside the ~250 px the card leaves for it.
        self.assertLessEqual(len(chk.text()), 30, chk.text())
        self.assertIn("Experimental", chk.text())


if __name__ == "__main__":
    unittest.main()
