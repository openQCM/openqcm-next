# -*- coding: utf-8 -*-
"""Headless tests of core/lorentzian.py — no Qt, no process.

    cd software && PYTHONPATH=. python -m unittest tests.test_lorentzian -v

The regression test against the 45 sweeps of 2026-09-11 needs the research
folder (the dumps archive and the chain in scripts/psl_lib.py, which must be run
from software/ because MultiscanProcess reads openQCM/config.txt by a relative
path); it is skipped when either is missing.
"""
import json
import math
import os
import sys
import unittest

import numpy as np

from openQCM.core import lorentzian as L
from openQCM.core.constants import Constants

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, "..", "..", "research",
                                         "air-ipa-water-1920-2026-09-11"))


def _seeds(freq, G):
    """argmax and two-sided half-height width, the way the process seeds the fit."""
    base = float(np.mean(G[:100]))
    g = G - base
    i = int(np.argmax(g))
    half = g[i] / 2.0
    left = np.where(g[:i] < half)[0]
    right = np.where(g[i:] < half)[0]
    f_left = freq[left[-1]] if len(left) else freq[0]
    f_right = freq[i + right[0]] if len(right) else freq[-1]
    return float(freq[i]), float((f_right - f_left) / 2.0)


def _synthetic(fres, gamma, phi_deg, gmax, g_off, noise_frac=0.002, seed=1):
    f = np.arange(fres - 12000.0, fres + 6001.0, 1.0)
    g = L.rotated_lorentzian(f, fres, gamma, phi_deg, gmax, g_off)
    g = g + np.random.default_rng(seed).normal(0.0, noise_frac * gmax, f.size)
    return f, g


class RotatedLorentzianTests(unittest.TestCase):

    def test_model_reduces_to_the_symmetric_lorentzian_at_phi_zero(self):
        f = np.linspace(-5.0, 5.0, 11)
        g = L.rotated_lorentzian(f, 0.0, 1.0, 0.0, 2.0, 0.5)
        np.testing.assert_allclose(g, 2.0 / (1.0 + f * f) + 0.5)

    def test_recovers_a_water_like_sweep(self):
        fres, gamma, phi, gmax, off = 24971700.0, 1600.0, -24.0, 0.5e-3, 0.3e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        f_seed, gam_seed = _seeds(f, g)
        fit = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed)
        self.assertTrue(fit.converged)
        self.assertLess(abs(fit.fres - fres), 2.0)
        self.assertLess(abs(fit.gamma - gamma) / gamma, 0.005)
        self.assertLess(abs(fit.phi_deg - phi), 0.3)
        self.assertLess(abs(fit.gmax - gmax) / gmax, 0.01)
        self.assertLess(fit.rms_rel, 0.01)
        ok, reason = L.accept(fit, f_seed, gam_seed, f[0], f[-1])
        self.assertTrue(ok, reason)

    def test_recovers_an_air_like_sweep(self):
        fres, gamma, phi, gmax, off = 24973700.0, 105.0, -21.0, 10.0e-3, 0.2e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        f_seed, gam_seed = _seeds(f, g)
        fit = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed)
        self.assertLess(abs(fit.fres - fres), 2.0)
        self.assertLess(abs(fit.gamma - gamma) / gamma, 0.01)
        self.assertLess(abs(fit.phi_deg - phi), 0.5)

    def test_the_maximum_of_G_is_biased_by_gamma_tan_half_phi(self):
        fres, gamma, phi = 24971700.0, 1600.0, -24.0
        f, g = _synthetic(fres, gamma, phi, 0.5e-3, 0.3e-3, noise_frac=0.0)
        f_seed, _ = _seeds(f, g)
        predicted = gamma * math.tan(math.radians(phi) / 2.0)
        self.assertLess(abs((f_seed - fres) - predicted), 2.0)

    def test_decimation_does_not_move_the_result(self):
        fres, gamma, phi, gmax, off = 44940700.0, 2100.0, -28.0, 0.25e-3, 0.7e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        f_seed, gam_seed = _seeds(f, g)
        full = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed, max_points=None)
        dec = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed, max_points=300)
        self.assertLessEqual(dec.n_fit, 300)
        self.assertLess(abs(full.fres - dec.fres), 2.0)
        self.assertLess(abs(full.gamma - dec.gamma), 3.0)
        self.assertLess(abs(full.phi_deg - dec.phi_deg), 0.2)

    def test_sign_ambiguity_is_resolved_to_positive_gmax(self):
        fres, gamma, phi, gmax, off = 14986800.0, 1700.0, -14.0, 0.6e-3, 0.2e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        f_seed, gam_seed = _seeds(f, g)
        fit = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed)
        self.assertGreater(fit.gmax, 0.0)
        self.assertGreater(fit.gamma, 0.0)
        self.assertTrue(-180.0 < fit.phi_deg <= 180.0)


class GateTests(unittest.TestCase):

    def test_flat_conductance_is_rejected_with_a_reason(self):
        f = np.arange(0.0, 18001.0) + 5.0e6
        g = 1e-3 + np.random.default_rng(2).normal(0.0, 1e-6, f.size)
        pub, fit = L.publish(f, g, f_seed=5.0e6 + 12000.0, gamma_seed=100.0)
        self.assertEqual(pub.source, L.SOURCE_FALLBACK)
        self.assertNotEqual(pub.reason, "ok")
        self.assertEqual(pub.fres, 5.0e6 + 12000.0)     # the fallback is the seed, untouched
        self.assertEqual(pub.gamma, 100.0)

    def test_too_narrow_a_window_is_rejected(self):
        f = np.arange(0.0, 18001.0) + 5.0e6
        g = np.exp(-((f - 5.006e6) / 200.0) ** 2)
        fit = L.fit_phase_shifted_lorentzian(f, g, 5.006e6, 1.0)   # +-3 Hz: 7 points
        ok, reason = L.accept(fit, 5.006e6, 1.0, f[0], f[-1])
        self.assertFalse(ok)
        self.assertIn("too few points", reason)

    def test_bad_seeds_do_not_raise(self):
        f = np.arange(0.0, 100.0)
        g = np.ones_like(f)
        for gam in (0.0, -5.0, float("nan")):
            fit = L.fit_phase_shifted_lorentzian(f, g, 50.0, gam)
            self.assertFalse(fit.converged)
        fit = L.fit_phase_shifted_lorentzian(f, g, float("nan"), 10.0)
        self.assertFalse(fit.converged)

    def test_nan_holes_are_ignored(self):
        fres, gamma, phi, gmax, off = 24971700.0, 1600.0, -24.0, 0.5e-3, 0.3e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        g[5000:5100] = np.nan
        f_seed, gam_seed = _seeds(f, np.nan_to_num(g, nan=off))
        fit = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed)
        self.assertLess(abs(fit.fres - fres), 3.0)

    def test_each_limit_rejects_with_its_own_reason(self):
        fres, gamma, phi, gmax, off = 24971700.0, 1600.0, -24.0, 0.5e-3, 0.3e-3
        f, g = _synthetic(fres, gamma, phi, gmax, off)
        f_seed, gam_seed = _seeds(f, g)
        fit = L.fit_phase_shifted_lorentzian(f, g, f_seed, gam_seed)
        self.assertIn("phi", L.accept(fit, f_seed, gam_seed, f[0], f[-1], phi_max_deg=10.0)[1])
        self.assertIn("rms", L.accept(fit, f_seed, gam_seed, f[0], f[-1], rms_max=1e-6)[1])
        self.assertIn("Gamma", L.accept(fit, f_seed, gam_seed, f[0], f[-1], gamma_ratio=(2.0, 3.0))[1])
        self.assertIn("outside the fit window", L.accept(fit, f_seed, gam_seed, fres + 10.0, f[-1])[1])

    def test_argmax_mode_publishes_the_seeds(self):
        f = np.arange(0.0, 18001.0) + 5.0e6
        g = np.exp(-((f - 5.006e6) / 200.0) ** 2)
        pub, fit = L.publish(f, g, 5.006e6, 150.0, estimator="argmax")
        self.assertIsNone(fit)
        self.assertEqual((pub.fres, pub.gamma, pub.source), (5.006e6, 150.0, L.SOURCE_FALLBACK))

    def test_defaults_are_the_constants(self):
        self.assertEqual(Constants.IMPEDANCE_ESTIMATOR, "lorentzian")
        self.assertEqual(Constants.PSL_RMS_MAX, 0.05)
        self.assertEqual(Constants.PSL_PHI_MAX_DEG, 60.0)
        self.assertEqual(tuple(Constants.PSL_GAMMA_RATIO), (0.3, 3.0))


@unittest.skipUnless(
    os.path.exists(os.path.join(RESEARCH, "data", "sweep_dumps_2026-09-11.npz"))
    and os.path.exists(os.path.join(RESEARCH, "scripts", "psl_lib.py"))
    and os.path.exists(os.path.join(HERE, "data", "psl_expected_2026-09-11.json")),
    "research dumps or psl_lib not available")
class DumpRegressionTests(unittest.TestCase):
    """The module reproduces the research numbers of 2026-09-11..15 on all 45
    sweeps, and the gate accepts every one of them."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(RESEARCH, "scripts"))
        import psl_lib                                    # runs MultiscanProcess(None): needs cwd = software/
        cls.lib = psl_lib
        cls.Z = np.load(os.path.join(RESEARCH, "data", "sweep_dumps_2026-09-11.npz"))
        with open(os.path.join(HERE, "data", "psl_expected_2026-09-11.json")) as fh:
            cls.expected = json.load(fh)["values"]

    def test_all_45_sweeps(self):
        costs = []
        for key, exp in self.expected.items():
            c = self.lib.chain(self.Z[key])
            fr, G = c["fr"], c["G"]
            f_arg, gam0, _ = self.lib.argmax_and_halfwidth(fr, G)
            self.assertAlmostEqual(f_arg, exp["f_argmax"], places=3, msg=key)
            full = L.fit_phase_shifted_lorentzian(fr, G, f_arg, gam0, max_points=None)
            self.assertLess(abs(full.fres - exp["fres"]), 0.5, key)
            self.assertLess(abs(full.gamma - exp["gamma"]), 0.5, key)
            self.assertLess(abs(full.phi_deg - exp["phi_deg"]), 0.05, key)
            pub, fit = L.publish(fr, G, f_arg, gam0)
            self.assertEqual(pub.source, L.SOURCE_FIT, "%s: %s" % (key, pub.reason))
            self.assertLess(abs(pub.fres - exp["fres"]), 2.0, key)
            self.assertLess(abs(pub.gamma - exp["gamma"]), 3.0, key)
            self.assertLess(abs(fit.phi_deg - exp["phi_deg"]), 0.2, key)
            costs.append(fit.cost_ms)
        print("\n  decimated fit cost over 45 sweeps: median %.0f ms, max %.0f ms"
              % (np.median(costs), np.max(costs)))


if __name__ == "__main__":
    unittest.main()
