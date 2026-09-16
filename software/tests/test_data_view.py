# -*- coding: utf-8 -*-
"""Headless test of the Impedance Data View's band (T5): f_r ± Γ when the fit was published, the
measured crossings otherwise. Built and fed, not shown (offscreen segfault of HANDOFF §6)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest

import numpy as np
from PyQt5 import QtWidgets

from openQCM.ui import impedanceDataView as V
from tests.test_fit_window import FakeWorker

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class BandWorker(FakeWorker):
    def __init__(self):
        super(BandWorker, self).__init__(5)
        self.band = [(float("nan"), float("nan"), float("nan"))] * 5

    def get_band_G_buffer(self, idx): return self.band[idx]


class Host(object):
    def __init__(self, worker): self.worker = worker


class DataViewBandTests(unittest.TestCase):

    def setUp(self):
        self.w = BandWorker()
        # overtone 2: published by the fit; 3: fallback with measured crossings; 4: no fit shipped
        self.w.ship(2, 24972090.0, 1646.0, -24.0, 0.5e-3, 0.3e-3)
        self.w.ship(3, 34955750.0, 1868.0, -22.5, 0.4e-3, 0.45e-3, source="fallback", reason="rms 7.3 % of range > 5 %")
        self.w.band[3] = (34955750.0 - 1700.0, 34955750.0 + 2000.0, 0.31)
        self.w.ship(4, 44941160.0, 2130.0, -27.9, 0.25e-3, 0.7e-3, with_fit=False)
        self.w.band[4] = (44941160.0 - 2100.0, float("nan"), 0.2)
        self.view = V.ImpedanceDataViewDialog(Host(self.w), theme_name="dark")

    def tearDown(self):
        self.view.close()

    def _pane(self, idx):
        self.view._tabs.setCurrentIndex(idx)
        self.view._update_pane(self.w, idx)
        return self.view._panes[idx]

    def test_fit_published_draws_fr_plus_minus_gamma(self):
        pane = self._pane(2)
        lo, hi = pane.band.getRegion()
        self.assertAlmostEqual(lo, 24972090.0 - 1646.0, places=6)
        self.assertAlmostEqual(hi, 24972090.0 + 1646.0, places=6)
        self.assertFalse(pane.half_line.isVisible())
        self.assertIn("published by the fit", pane.info.text())
        self.assertIn("φ -24.0°", pane.info.text())
        self.assertIn("f_r 24972090.0 Hz", pane.info.text())
        self.assertIn("Γ 1646.0 Hz", pane.info.text())

    def test_fallback_published_draws_the_measured_crossings(self):
        pane = self._pane(3)
        lo, hi = pane.band.getRegion()
        self.assertAlmostEqual(lo, 34955750.0 - 1700.0, places=6)
        self.assertAlmostEqual(hi, 34955750.0 + 2000.0, places=6)
        self.assertIn("published by the FALLBACK", pane.info.text())
        self.assertIn("rms 7.3", pane.info.text())

    def test_no_fit_shipped_behaves_as_before(self):
        pane = self._pane(4)
        lo, hi = pane.band.getRegion()
        self.assertAlmostEqual(lo, 44941160.0 - 2100.0, places=6)
        self.assertAlmostEqual(hi, 44941160.0 + self.w.gam[4], places=6)     # right edge guessed from f_r + Γ
        self.assertIn("right edge from f_r ∓ Γ", pane.info.text())
        self.assertNotIn("published by", pane.info.text())

    def test_the_view_imports_no_processing(self):
        src = open(V.__file__, encoding="utf-8").read()
        code = "\n".join(l for l in src.splitlines() if l.strip() and not l.strip().startswith("#"))
        self.assertNotIn("core.resonance", code)
        self.assertNotIn("core.lorentzian", code)
        self.assertNotIn("processors", code)


if __name__ == "__main__":
    unittest.main()
