# -*- coding: utf-8 -*-
"""Headless test of the live fit window (T4): it draws what the process shipped and computes nothing.

    cd software && PYTHONPATH=. python -m unittest tests.test_fit_window -v

Runs on the offscreen Qt platform WITHOUT showing the window: a QTabWidget full of GraphicsLayoutWidgets
segfaults offscreen when shown (HANDOFF §6, the known list), so the tests build the window, feed it and read
its items back. Set SCREENSHOT=/path.png on the real platform (QT_QPA_PLATFORM unset) to also show it and
save a capture.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest

import numpy as np
from PyQt5 import QtWidgets

from openQCM.core import lorentzian as L
from openQCM.core.constants import Constants
from openQCM.ui import impedanceFitWindow as W

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class FakeWorker(object):
    """The worker's getters, fed with one shipped sweep per overtone."""

    def __init__(self, n=5):
        self.n = n
        self.seq = [0] * n
        self.f = [None] * n
        self.g = [None] * n
        self.fr = [0.0] * n
        self.gam = [0.0] * n
        self.delta = [0.0] * n
        self.fit = [None] * n

    def ship(self, idx, fres, gamma, phi_deg, gmax_S, g_off_S, source="fit", reason="ok",
             used=7, fallback=0, with_fit=True):
        f = np.arange(fres - 12000.0, fres + 6001.0, 1.0)
        G = L.rotated_lorentzian(f, fres, gamma, phi_deg, gmax_S, g_off_S)
        G = G + np.random.default_rng(idx).normal(0.0, 0.002 * gmax_S, f.size)
        f_arg = float(f[np.argmax(G)]); gam_hh = gamma * 0.98
        # what the process ships: the +-3 Gamma clip in mS with the edge baseline removed
        G_mS = G * 1e3; baseline = float(np.mean(G_mS[:100])); keep = np.abs(f - f_arg) <= 3 * gam_hh
        self.f[idx] = f[keep]; self.g[idx] = (G_mS - baseline)[keep]
        pub_f, pub_g = (fres, gamma) if source == "fit" else (f_arg, gam_hh)
        self.fr[idx] = pub_f; self.gam[idx] = pub_g; self.delta[idx] = 4.1 if idx < 3 else 0.0
        self.fit[idx] = None if not with_fit else dict(
            f_argmax=f_arg, gamma_hh=gam_hh, fres=fres, gamma=gamma, phi_deg=phi_deg,
            rms_rel=0.0021, gmax_mS=gmax_S * 1e3, g_off_mS=g_off_S * 1e3 - baseline, cost_ms=1.3,
            source=source, used=used, fallback=fallback, reason=reason)
        self.seq[idx] += 1

    def get_GB_seq(self, idx): return self.seq[idx]
    def get_G_exact_buffer(self, idx): return self.g[idx]
    def get_F_G_values_buffer(self, idx): return self.f[idx]
    def get_fr_G_buffer(self, idx): return self.fr[idx]
    def get_gamma_G_buffer(self, idx): return self.gam[idx]
    def get_delta_G_buffer(self, idx): return self.delta[idx]
    def get_fit_G_buffer(self, idx): return self.fit[idx]


class FitWindowTests(unittest.TestCase):

    def setUp(self):
        self.w = FakeWorker()
        self.w.ship(0, 5004600.0, 65.0, -8.0, 28e-3, 1.5e-3)
        self.w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3)
        self.w.ship(2, 24972090.0, 1646.0, -24.0, 0.5e-3, 0.3e-3, used=41, fallback=0)
        self.w.ship(3, 34955750.0, 1868.0, -22.5, 0.4e-3, 0.45e-3, source="fallback",
                    reason="rms 7.3 % of range > 5 %", used=40, fallback=1)
        self.w.ship(4, 44941160.0, 2130.0, -27.9, 0.25e-3, 0.7e-3, with_fit=False)
        self.win = W.ImpedanceFitWindow(self.w, 5, theme_name="dark")
        self.win._tick()

    def tearDown(self):
        self.win.close()

    def test_the_window_fits_nothing_and_needs_no_offline_module(self):
        src = open(W.__file__, encoding="utf-8").read()
        code = "\n".join(l for l in src.splitlines() if l.strip() and not l.strip().startswith("#"))
        # no offline module loaded by path, no solver: the window evaluates shipped parameters only
        self.assertNotIn("spec_from_file_location", code)
        self.assertNotIn("import importlib", code)
        self.assertNotIn("least_squares", code)
        self.assertFalse(hasattr(W, "_load_fit_module"))
        self.assertFalse(hasattr(W, "fa"))

    def test_the_drawn_model_is_the_shipped_model(self):
        for idx in (0, 1, 2):
            fit = self.w.fit[idx]
            f = self.w.f[idx]
            curve = self.win.model_curve(idx, f)
            expected = L.rotated_lorentzian(f, fit["fres"], fit["gamma"], fit["phi_deg"],
                                            fit["gmax_mS"], fit["g_off_mS"])
            np.testing.assert_allclose(curve, expected, rtol=0, atol=1e-12)
            # and it lies on the shipped points: the process's rms, not something else
            self.assertLess(np.sqrt(np.mean((curve - self.w.g[idx]) ** 2)) / np.ptp(self.w.g[idx]), 0.01)

    def test_the_table_reports_the_source_and_the_published_pair(self):
        t = self.win.table
        self.assertTrue(t.item(2, 1).text().startswith("fit"))
        self.assertIn("41 fit / 0 fallback", t.item(2, 1).text())
        self.assertEqual(t.item(2, 2).text(), "24972090.0")
        self.assertEqual(t.item(2, 3).text(), "1646.0")
        self.assertEqual(t.item(2, 5).text(), "-24.0")
        self.assertEqual(t.item(2, 6).text(), "0.21")
        self.assertTrue(t.item(3, 1).text().startswith("FALLBACK: rms 7.3 %"))
        self.assertEqual(float(t.item(3, 2).text()), self.w.fr[3])           # the fallback pair is what is published
        self.assertEqual(t.item(4, 1).text(), "maximum of G (no fit shipped)")
        self.assertEqual(t.item(0, 9).text(), "+4.10")
        self.assertEqual(t.item(4, 9).text(), "no fold")

    def test_the_visible_tab_draws_the_published_marker_at_zero_and_the_window(self):
        self.win._tabs.setCurrentIndex(2)
        pane = self.win._panes[2]
        self.assertEqual(pane.markFres.value(), 0.0)
        fit = self.w.fit[2]
        lo, hi = pane.window.getRegion()
        band = Constants.PSL_BAND_GAMMA * fit["gamma_hh"]
        self.assertAlmostEqual(lo, fit["f_argmax"] - band - self.w.fr[2], places=6)
        self.assertAlmostEqual(hi, fit["f_argmax"] + band - self.w.fr[2], places=6)
        self.assertAlmostEqual(pane.markArg.value(), fit["f_argmax"] - self.w.fr[2], places=6)
        x, y = pane.curveFit.getData()
        self.assertGreater(len(x), 100)
        # the no-fit overtone draws the measurement only
        self.win._tabs.setCurrentIndex(4)
        x4, y4 = self.win._panes[4].curveFit.getData()
        self.assertTrue(x4 is None or len(x4) == 0)

    def test_a_tick_without_new_sweeps_changes_nothing(self):
        before = self.win.lblStatus.text()
        self.win._tick()
        self.assertEqual(self.win.lblStatus.text(), before)

    def test_screenshot_if_requested(self):
        path = os.environ.get("SCREENSHOT")
        if not path or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            self.skipTest("set SCREENSHOT=/path.png on the real platform to save a capture")
        self.win.show()
        self.win._tabs.setCurrentIndex(2)
        _app.processEvents()
        self.assertTrue(self.win.grab().save(path))


if __name__ == "__main__":
    unittest.main()
