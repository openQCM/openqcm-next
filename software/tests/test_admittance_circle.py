# -*- coding: utf-8 -*-
"""The circle drawn over an admittance locus: one rule, shared by two windows.

    cd software && PYTHONPATH=. python -m unittest tests.test_admittance_circle -v

Experimental run: the circle IS the published rotated Lorentzian (centre and radius
follow from G_max and φ, nothing estimated). Standard run: a circle fitted in the
view (Taubin, display only) that recovers a synthetic circle to a few per mille.
"""
import unittest
import numpy as np

from openQCM.ui import admittanceCircle as C


def _sweep(fres=14988740.0, gamma=76.0, phi_deg=-14.5, gmax=19.0, g_off=1.0, b_off=9.5):
    f = np.arange(fres - 3 * gamma, fres + 3 * gamma + 1.0, 1.0)
    Y = gmax * gamma * np.exp(1j * np.radians(phi_deg)) / (gamma - 1j * (fres - f))
    return f, Y.real + g_off, Y.imag + b_off


class CircleTests(unittest.TestCase):

    def test_experimental_circle_is_the_published_model(self):
        f, g, b = _sweep()
        fit = dict(mode="lorentzian", gmax_mS=19.0, phi_deg=-14.5, g_off_mS=1.0, gamma_hh=74.0)
        c = C.circle_for(fit, f, g, b, 14988740.0)
        self.assertEqual(c["kind"], C.KIND_PUBLISHED)
        phi = np.radians(-14.5)
        self.assertAlmostEqual(c["r"], 9.5, places=9)
        self.assertAlmostEqual(c["xc"], 1.0 + 9.5 * np.cos(phi), places=9)
        # B_off is anchored on the measured B at f_res, where Y = G_max e^{jφ}
        self.assertAlmostEqual(c["yc"], 9.5 + 9.5 * np.sin(phi), places=6)
        # the measured locus lies ON that circle
        rad = np.hypot(g - c["xc"], b - c["yc"])
        self.assertLess(float(np.max(np.abs(rad - c["r"]))), 1e-6)
        self.assertEqual(len(c["x"]), 361)
        self.assertIn("published fit", c["label"])

    def test_standard_circle_is_fitted_here_and_recovers_the_geometry(self):
        f, g, b = _sweep()
        rng = np.random.default_rng(3)
        g = g + rng.normal(0.0, 0.02, g.size)
        fit = dict(mode="argmax", gmax_mS=float("nan"), phi_deg=float("nan"),
                   g_off_mS=float("nan"), gamma_hh=76.0)
        c = C.circle_for(fit, f, g, b, 14988740.0)
        self.assertEqual(c["kind"], C.KIND_FITTED)
        self.assertAlmostEqual(c["r"], 9.5, delta=0.05)
        self.assertAlmostEqual(c["xc"], 1.0 + 9.5 * np.cos(np.radians(-14.5)), delta=0.05)
        self.assertLess(c["rms"], 1.0)
        self.assertIn("fitted HERE", c["label"])

    def test_no_fit_dict_means_a_fitted_circle_on_the_whole_locus(self):
        f, g, b = _sweep()
        c = C.circle_for(None, f, g, b, 14988740.0)
        self.assertEqual(c["kind"], C.KIND_FITTED)
        self.assertAlmostEqual(c["r"], 9.5, places=6)

    def test_too_few_points_gives_no_circle(self):
        f, g, b = _sweep()
        self.assertIsNone(C.circle_for(None, f[:5], g[:5], b[:5], 14988740.0))
        self.assertIsNone(C.circle_for(None, f, g[:-1], b, 14988740.0))

    def test_union_bounds(self):
        self.assertEqual(C.union_bounds(([1.0, 2.0], [5.0, 6.0]), ([0.0, 3.0], [4.0, 9.0])),
                         (0.0, 3.0, 4.0, 9.0))
        self.assertIsNone(C.union_bounds(([], [])))
        self.assertEqual(C.union_bounds(([np.nan, 1.0], [2.0, np.nan])), (1.0, 1.0, 2.0, 2.0))


class _FakePlot(object):
    def __init__(self):
        self.calls = []

    def setRange(self, xRange=None, yRange=None, padding=None):
        self.calls.append((xRange, yRange, padding))


class FramerTests(unittest.TestCase):

    def test_frames_once_and_again_only_on_a_change_of_scale(self):
        p = _FakePlot()
        fr = C.LocusFramer(p)
        self.assertTrue(fr.frame(0.0, 10.0, 0.0, 10.0))
        self.assertFalse(fr.frame(0.1, 10.1, 0.0, 10.0))     # drift below 20 % of the span
        self.assertEqual(len(p.calls), 1)
        self.assertTrue(fr.frame(0.0, 30.0, 0.0, 30.0))      # a new scale
        self.assertEqual(len(p.calls), 2)
        fr.reset()
        self.assertTrue(fr.frame(0.0, 30.0, 0.0, 30.0))      # after reset it frames again
        self.assertFalse(fr.frame(float("nan"), 1.0, 0.0, 1.0))
        self.assertFalse(fr.frame(1.0, 1.0, 1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
