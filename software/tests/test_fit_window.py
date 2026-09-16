# -*- coding: utf-8 -*-
"""Headless test of the live fit window (T4): it draws what the process shipped and computes nothing.

    cd software && PYTHONPATH=. python -m unittest tests.test_fit_window -v

Runs on the offscreen Qt platform WITHOUT rendering the window: a QTabWidget full of
GraphicsLayoutWidgets segfaults offscreen (HANDOFF §6, the known list) -- measured 2026-09-16, exit 139 on
both `show()` AND `grab()`, so there is no way to capture this window headless at all. The tests build it,
feed it and read its items back, which is where the numbers are anyway. Set SCREENSHOT=/path.png on the
real platform (QT_QPA_PLATFORM unset) to show it and save a capture.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest

import numpy as np
from PyQt5 import QtCore, QtWidgets

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
        self.b = [None] * n
        self.fr = [0.0] * n
        self.gam = [0.0] * n
        self.delta = [0.0] * n
        self.fit = [None] * n

    def ship(self, idx, fres, gamma, phi_deg, gmax_S, g_off_S, source="fit", reason="ok",
             used=7, fallback=0, with_fit=True, mode="lorentzian"):
        f = np.arange(fres - 12000.0, fres + 6001.0, 1.0)
        # the same rotated Lorentzian in the complex plane: G is its real part (what
        # the process fits), B its imaginary part plus a C0-like offset (what the
        # chain computes and ships untouched)
        Y = gmax_S * gamma * np.exp(1j * np.radians(phi_deg)) / (gamma - 1j * (fres - f))
        G = Y.real + g_off_S + np.random.default_rng(idx).normal(0.0, 0.002 * gmax_S, f.size)
        B = Y.imag + 0.5 * gmax_S
        f_arg = float(f[np.argmax(G)]); gam_hh = gamma * 0.98
        # what the process ships: the +-3 Gamma clip in mS, G with the edge baseline
        # removed and B as computed (T3)
        G_mS = G * 1e3; baseline = float(np.mean(G_mS[:100])); keep = np.abs(f - f_arg) <= 3 * gam_hh
        self.f[idx] = f[keep]; self.g[idx] = (G_mS - baseline)[keep]; self.b[idx] = (B * 1e3)[keep]
        pub_f, pub_g = (fres, gamma) if source == "fit" else (f_arg, gam_hh)
        self.fr[idx] = pub_f; self.gam[idx] = pub_g; self.delta[idx] = 4.1 if idx < 3 else 0.0
        nan = float("nan")
        if mode == "argmax":          # a STANDARD run: the process shipped no fit numbers, but G and B as always
            self.fit[idx] = dict(f_argmax=f_arg, gamma_hh=gam_hh, fres=nan, gamma=nan, phi_deg=nan,
                                 rms_rel=nan, gmax_mS=nan, g_off_mS=nan, cost_ms=nan, source="fallback",
                                 used=0, fallback=0, reason="standard estimator (maximum of G, half-height width)",
                                 mode="argmax")
            return
        self.fit[idx] = None if not with_fit else dict(
            f_argmax=f_arg, gamma_hh=gam_hh, fres=fres, gamma=gamma, phi_deg=phi_deg,
            rms_rel=0.0021, gmax_mS=gmax_S * 1e3, g_off_mS=g_off_S * 1e3 - baseline, cost_ms=1.3,
            source=source, used=used, fallback=fallback, reason=reason, mode=mode)
        self.seq[idx] += 1

    def get_GB_seq(self, idx): return self.seq[idx]
    def get_G_exact_buffer(self, idx): return self.g[idx]
    def get_B_exact_buffer(self, idx): return self.b[idx]
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

    def test_a_standard_run_shows_the_maximum_and_no_fit(self):
        w = FakeWorker(); w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3, mode="argmax")
        win = W.ImpedanceFitWindow(w, 5, theme_name="light"); win._tick()
        try:
            self.assertTrue(win.table.item(1, 1).text().startswith("STANDARD"))
            self.assertEqual(win.table.item(1, 5).text(), "-")           # no phi in a standard run
            self.assertEqual(float(win.table.item(1, 2).text()), w.fr[1])
            win._tabs.setCurrentIndex(1)
            x, y = win._panes[1].curveFit.getData()
            self.assertTrue(x is None or len(x) == 0)
            self.assertIn("STANDARD estimator", win._panes[1].pG.titleLabel.text)
        finally:
            win.close()

    def test_the_susceptance_and_the_locus_are_the_shipped_arrays(self):
        idx = 2
        self.win._tabs.setCurrentIndex(idx)
        self.win._draw_selected()
        pane = self.win._panes[idx]
        xb, yb = pane.curveB.getData()
        step = max(1, len(self.w.f[idx]) // W.DRAW_POINTS)
        np.testing.assert_allclose(yb, self.w.b[idx][::step][:len(yb)], rtol=0, atol=1e-12)
        np.testing.assert_allclose(xb, (self.w.f[idx][::step] - self.w.fr[idx])[:len(yb)],
                                   rtol=0, atol=1e-9)
        # the locus is B against G, both shipped
        xl, yl = pane.curveLocus.getData()
        np.testing.assert_allclose(xl, self.w.g[idx][::step][:len(yl)], rtol=0, atol=1e-12)
        np.testing.assert_allclose(yl, self.w.b[idx][::step][:len(yl)], rtol=0, atol=1e-12)
        # and it closes into something circular: the radial spread of the +-Gamma core
        # around its own centre is a few per cent
        core = np.abs(self.w.f[idx] - self.w.fr[idx]) <= self.w.gam[idx]
        gc, bc = self.w.g[idx][core], self.w.b[idx][core]
        xc, yc = 0.5 * (gc.max() + gc.min()), 0.5 * (bc.max() + bc.min())
        r = np.hypot(gc - xc, bc - yc)
        self.assertLess(r.std() / r.mean(), 0.25)

    def test_the_markers_on_the_locus_are_lookups_on_the_measurement(self):
        idx = 2
        self.win._tabs.setCurrentIndex(idx)
        self.win._draw_selected()
        pane = self.win._panes[idx]
        xf, yf = pane.markLocusFres.getData()
        self.assertEqual(len(xf), 1)
        self.assertAlmostEqual(xf[0], float(np.interp(self.w.fr[idx], self.w.f[idx], self.w.g[idx])), places=9)
        self.assertAlmostEqual(yf[0], float(np.interp(self.w.fr[idx], self.w.f[idx], self.w.b[idx])), places=9)
        xa, ya = pane.markLocusArg.getData()
        f_arg = self.w.fit[idx]["f_argmax"]
        self.assertAlmostEqual(xa[0], float(np.interp(f_arg, self.w.f[idx], self.w.g[idx])), places=9)

    def test_no_model_curve_is_drawn_over_B(self):
        """The estimator fits G alone: B carries the measurement and nothing else."""
        pane = self.win._panes[2]
        self.assertTrue(hasattr(pane, "curveB"))
        self.assertFalse(any(n.startswith("curveBfit") for n in vars(pane)))

    def test_in_an_experimental_run_the_circle_is_the_published_fit(self):
        """Diameter G_max, centre at offset + (G_max/2)e^{jphi}, vertical position
        anchored on the measured B at f_res -- the published model, not a new fit."""
        idx = 2
        self.win._tabs.setCurrentIndex(idx); self.win._draw_selected()
        x, y = self.win._panes[idx].curveCircle.getData()
        self.assertGreater(len(x), 100)
        fit = self.w.fit[idx]
        gmax, phi = fit["gmax_mS"], np.radians(fit["phi_deg"])
        b_at = float(np.interp(self.w.fr[idx], self.w.f[idx], self.w.b[idx]))
        xc_exp = fit["g_off_mS"] + 0.5 * gmax * np.cos(phi)
        yc_exp = (b_at - gmax * np.sin(phi)) + 0.5 * gmax * np.sin(phi)
        xc, yc = 0.5 * (x.max() + x.min()), 0.5 * (y.max() + y.min())
        r = 0.5 * (x.max() - x.min())
        self.assertAlmostEqual(xc, xc_exp, places=6)
        self.assertAlmostEqual(yc, yc_exp, places=6)
        self.assertAlmostEqual(r, 0.5 * abs(gmax), places=6)
        # what the anchor buys: the MODEL's own point at f_res, (G_off + G_max cos φ,
        # B measured at f_res), lies on the circle -- the vertical freedom is what was
        # anchored, so the measured G at f_res only lands on it to within its noise
        g_model = fit["g_off_mS"] + gmax * np.cos(phi)
        self.assertAlmostEqual(np.hypot(g_model - xc, b_at - yc), r, places=9)
        g_at = float(np.interp(self.w.fr[idx], self.w.f[idx], self.w.g[idx]))
        self.assertLess(abs(np.hypot(g_at - xc, b_at - yc) - r) / r, 0.01)
        self.assertIn("circle of the published fit", self.win._panes[idx].pC.titleLabel.text)

    def test_in_a_standard_run_the_circle_is_fitted_here_and_says_so(self):
        w = FakeWorker(); w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3, mode="argmax")
        win = W.ImpedanceFitWindow(w, 5, theme_name="light"); win._tick()
        try:
            win._tabs.setCurrentIndex(1); win._draw_selected()
            pane = win._panes[1]
            x, y = pane.curveCircle.getData()
            self.assertGreater(len(x), 100)
            xc, yc = 0.5 * (x.max() + x.min()), 0.5 * (y.max() + y.min())
            r = 0.5 * (x.max() - x.min())
            # the measured core sits on it: radial spread a few per cent of the radius
            core = np.abs(w.f[1] - w.fr[1]) <= w.fit[1]["gamma_hh"]
            rad = np.hypot(w.g[1][core] - xc, w.b[1][core] - yc)
            self.assertLess(abs(rad.mean() - r) / r, 0.05)
            self.assertLess(rad.std() / r, 0.10)
            self.assertIn("fitted HERE", pane.pC.titleLabel.text)
            self.assertIn("display only", pane.pC.titleLabel.text)
        finally:
            win.close()

    def test_the_table_sits_under_a_movable_divider_and_can_be_collapsed(self):
        sp = self.win._splitter
        self.assertEqual(sp.orientation(), QtCore.Qt.Vertical)
        self.assertEqual(sp.count(), 2)
        self.assertIs(sp.widget(0), self.win._tabs)
        self.assertTrue(sp.isCollapsible(1))          # the table can be dragged shut
        self.assertFalse(sp.isCollapsible(0))         # the plots cannot
        sp.setSizes([760, 0])
        self.assertEqual(sp.sizes()[1], 0)

    def test_a_standard_run_still_draws_B_and_the_locus(self):
        w = FakeWorker(); w.ship(1, 14988740.0, 76.0, -14.5, 19e-3, 1.0e-3, mode="argmax")
        win = W.ImpedanceFitWindow(w, 5, theme_name="light"); win._tick()
        try:
            win._tabs.setCurrentIndex(1); win._draw_selected()
            pane = win._panes[1]
            self.assertGreater(len(pane.curveB.getData()[0]), 50)
            self.assertGreater(len(pane.curveLocus.getData()[0]), 50)
            self.assertEqual(len(pane.markLocusFres.getData()[0]), 1)
        finally:
            win.close()

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
