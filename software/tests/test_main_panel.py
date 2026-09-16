# -*- coding: utf-8 -*-
"""The main-window impedance panel: G(f), B(f) and the admittance locus in one splitter.

    cd software && PYTHONPATH=. python -m unittest tests.test_main_panel -v

Restored on 2026-09-16 (Marco): the locus is the third pane of the vertical splitter,
every pane can be squashed by a handle, and the locus carries the same circle as the
live fit window (admittanceCircle). The update routine is exercised on a stub host
with the real pyqtgraph plots and the fit window's FakeWorker: the panel is built and
fed, never shown (HANDOFF §6).
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
import numpy as np

from PyQt5 import QtWidgets, QtCore

from openQCM.ui.mainWindow_ui import Ui_MainWindow
from openQCM.ui.mainWindow import MainWindow
from openQCM.ui import admittanceCircle
from tests.test_fit_window import FakeWorker

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _Host(object):
    """Just what _build_impedance_curves and _update_impedance_panel touch."""

    def __init__(self, ui, worker, n=5):
        for w in (ui.pltG, ui.pltSus, ui.pltLocus):
            w.clear()          # one host per test, same widgets
        self._pltG = ui.pltG.addPlot(row=0, col=0)
        self._pltSus = ui.pltSus.addPlot(row=0, col=0)
        self._pltLocus = ui.pltLocus.addPlot(row=0, col=0)
        self._pltLocus.setAspectLocked(True)
        for p in (self._pltG, self._pltSus, self._pltLocus):
            p.addLegend()
        self._pltLocus_framer = admittanceCircle.LocusFramer(self._pltLocus)
        self._overtones_number_all = n
        self._pltG_multiline = [None] * n
        self._pltSus_multiline = [None] * n
        self._pltLocus_multiline = [None] * n
        self._pltLocus_circle = [None] * n
        self._pltLocus_bounds = [None] * n
        self._impedance_panel_seq = [None] * n
        self._numpy_nan_sweep = np.array([np.nan])
        self._numpy_empty = np.array([], dtype=float)
        self.worker = worker
        self.scan_selector = [True] * n


class MainPanelTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mw = QtWidgets.QMainWindow()
        cls.ui = Ui_MainWindow()
        cls.ui.setupUi(cls.mw)

    def test_three_panes_in_one_vertical_splitter_and_every_one_can_be_squashed(self):
        sp = self.ui.impedanceSplitter
        self.assertEqual(sp.orientation(), QtCore.Qt.Vertical)
        self.assertEqual(sp.count(), 3)
        self.assertIs(sp.widget(0), self.ui.pltG)
        self.assertIs(sp.widget(1), self.ui.pltSus)
        self.assertIs(sp.widget(2), self.ui.pltLocus)          # the locus, after B(f)
        for i in range(3):
            self.assertTrue(sp.isCollapsible(i), "pane %d cannot be collapsed" % i)
        sp.setSizes([400, 300, 0])
        self.assertEqual(sp.sizes()[2], 0)

    def test_the_locus_is_not_the_centre_frequency_plot(self):
        self.assertIsNot(self.ui.pltLocus, self.ui.pltB)
        self.assertIsNot(self.ui.pltSus, self.ui.pltB)

    def _host(self, mode):
        w = FakeWorker()
        w.ship(0, 4995580.0, 22.0, -12.0, 60e-3, 3e-3, mode=mode)
        w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3, mode=mode)
        # a real locus is not a circle away from resonance: add a B drift that grows
        # with the distance from f_res, so a circle fitted on the tail differs from
        # one fitted on the ±Γ core and the test can tell WHERE it was anchored
        for idx, (fres, gam) in enumerate(((4995580.0, 22.0), (14988740.0, 76.0))):
            w.b[idx] = w.b[idx] + 0.4 * w.g[idx].max() * ((w.f[idx] - fres) / (3 * gam)) ** 2
        host = _Host(self.ui, w)
        MainWindow._build_impedance_curves(host)
        return host, w

    @staticmethod
    def _peaks(w):
        """peaks_mag as the panel receives it: the calibration centre of each sweep,
        which is NOT the published f_res. On the 2026-09-16 bench run it sat ~900 Hz
        from the resonance; anchoring the circle on it fitted the tail of the locus
        and gave a circle twice the fit window's. So the test feeds it off by 150 Hz
        and requires the circle of the published f_res regardless."""
        return [w.fr[i] + 150.0 for i in range(5)]

    def test_the_panel_draws_the_shipped_locus_and_a_circle_per_overtone(self):
        for mode in ("lorentzian", "argmax"):
            host, w = self._host(mode)
            MainWindow._update_impedance_panel(host, self._peaks(w))
            for idx in (0, 1):
                gx, bx = host._pltLocus_multiline[idx].getData()
                self.assertGreater(len(gx), 50, mode)
                # the points are the shipped G and B, decimated together
                step = max(1, len(w.g[idx]) // 250)
                np.testing.assert_array_equal(gx, w.g[idx][::step])
                np.testing.assert_array_equal(bx, w.b[idx][::step])
                cx, cy = host._pltLocus_circle[idx].getData()
                self.assertEqual(len(cx), 361, mode)
                # and the circle is the shared rule's circle for that sweep, anchored on
                # the PUBLISHED f_res -- the one the fit window draws, not one on peaks_mag
                c = admittanceCircle.circle_for(w.fit[idx], w.f[idx], w.g[idx], w.b[idx], w.fr[idx])
                wrong = admittanceCircle.circle_for(w.fit[idx], w.f[idx], w.g[idx], w.b[idx],
                                                    w.fr[idx] + 150.0)
                if mode == "argmax":
                    self.assertGreater(abs(wrong["r"] - c["r"]), 0.01 * c["r"],
                                       "the test cannot tell the two anchors apart")
                np.testing.assert_allclose(cx, c["x"]); np.testing.assert_allclose(cy, c["y"])
                self.assertEqual(c["kind"], admittanceCircle.KIND_PUBLISHED if mode == "lorentzian"
                                 else admittanceCircle.KIND_FITTED)
            # overtones never shipped stay empty
            x3 = host._pltLocus_circle[3].getData()[0]
            self.assertTrue(x3 is None or len(x3) == 0)

    def test_the_locus_is_framed_over_every_overtone_shown_points_and_circles(self):
        host, w = self._host("lorentzian")
        MainWindow._update_impedance_panel(host, self._peaks(w))
        framed = host._pltLocus_framer.framed
        self.assertIsNotNone(framed)
        pairs = []
        for idx in (0, 1):
            pairs.append((w.g[idx], w.b[idx]))
            pairs.append(host._pltLocus_circle[idx].getData())
        want = admittanceCircle.union_bounds(*pairs)
        for got, exp in zip(framed, want):
            self.assertAlmostEqual(got, exp, places=9)
        # hiding an overtone reframes on what is left
        host.scan_selector[0] = False
        MainWindow._update_impedance_panel(host, self._peaks(w))
        x0 = host._pltLocus_multiline[0].getData()[0]
        self.assertTrue(x0 is None or len(x0) == 0)
        want1 = admittanceCircle.union_bounds((w.g[1], w.b[1]), host._pltLocus_circle[1].getData())
        for got, exp in zip(host._pltLocus_framer.framed, want1):
            self.assertAlmostEqual(got, exp, places=9)

    def test_a_tick_with_no_new_sweep_redraws_nothing(self):
        host, w = self._host("argmax")
        MainWindow._update_impedance_panel(host, self._peaks(w))
        before = host._pltLocus_circle[1].getData()[0].copy()
        host._pltLocus_circle[1].setData(x=np.array([1.0]), y=np.array([1.0]))
        MainWindow._update_impedance_panel(host, self._peaks(w))
        self.assertEqual(len(host._pltLocus_circle[1].getData()[0]), 1)   # untouched: same seq
        w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3, mode="argmax")
        w.seq[1] += 1
        MainWindow._update_impedance_panel(host, self._peaks(w))
        self.assertEqual(len(host._pltLocus_circle[1].getData()[0]), len(before))


if __name__ == "__main__":
    unittest.main()
