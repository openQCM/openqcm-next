# -*- coding: utf-8 -*-
"""Headless tests of the published estimator inside the process and of the worker's
side of the G/B message (T2 of docs/impedance-analysis/PLAN_psl_live_estimator.md).

    cd software && PYTHONPATH=. python -m unittest tests.test_publish_process -v

MultiscanProcess(None) reads openQCM/config.txt by a relative path: run from software/.
"""
import contextlib
import io
import json
import os
import sys
import unittest

import numpy as np

from openQCM.core import lorentzian as L
from openQCM.core.constants import Constants
from openQCM.processors.Multiscan import MultiscanProcess
from openQCM.core.worker import Worker
from openQCM.core.constants import Constants, SourceType

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, "..", "..", "research",
                                         "air-ipa-water-1920-2026-09-11"))
HAVE_DUMPS = (os.path.exists(os.path.join(RESEARCH, "data", "sweep_dumps_2026-09-11.npz"))
              and os.path.exists(os.path.join(RESEARCH, "scripts", "psl_lib.py"))
              and os.path.exists(os.path.join(HERE, "data", "psl_expected_2026-09-11.json")))


def _synthetic(fres, gamma, phi_deg, gmax, g_off, seed=3):
    f = np.arange(fres - 12000.0, fres + 6001.0, 1.0)
    g = L.rotated_lorentzian(f, fres, gamma, phi_deg, gmax, g_off)
    return f, g + np.random.default_rng(seed).normal(0.0, 0.002 * gmax, f.size)


class PublishResonanceTests(unittest.TestCase):

    def setUp(self):
        self.proc = MultiscanProcess(None)
        self.proc.set_estimator("lorentzian")          # the experimental mode; the default is "argmax"

    def _run(self, idx, f, g, f_seed, gam_seed):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pub, fit = self.proc._publish_resonance(idx, f, g, f_seed, gam_seed)
        return pub, fit, out.getvalue()

    def test_a_good_sweep_is_published_by_the_fit_and_logged_once(self):
        f, g = _synthetic(24971700.0, 1600.0, -24.0, 0.5e-3, 0.3e-3)
        idx, f_seed, gam_seed = 2, float(f[np.argmax(g)]), 1580.0
        pub, fit, text = self._run(idx, f, g, f_seed, gam_seed)
        self.assertEqual(pub.source, L.SOURCE_FIT)
        self.assertLess(abs(pub.fres - 24971700.0), 3.0)
        self.assertIn("published by the phase-shifted Lorentzian fit", text)
        self.assertIn("overtone 2", text)
        self.assertEqual(self.proc.psl_counts(idx), (1, 0))
        # the second sweep of the same overtone with the same outcome: counted, not logged again
        pub2, fit2, text2 = self._run(idx, f, g, f_seed, gam_seed)
        self.assertEqual(text2, "")
        self.assertEqual(self.proc.psl_counts(idx), (2, 0))

    def test_a_flat_sweep_falls_back_with_the_reason_and_the_change_is_logged(self):
        f = np.arange(0.0, 18001.0) + 5.0e6
        g = 1e-3 + np.random.default_rng(4).normal(0.0, 1e-6, f.size)
        pub, fit, text = self._run(0, f, g, 5.012e6, 100.0)
        self.assertEqual(pub.source, L.SOURCE_FALLBACK)
        self.assertEqual((pub.fres, pub.gamma), (5.012e6, 100.0))
        self.assertIn("FALLBACK", text)
        self.assertIn(pub.reason, text)
        self.assertEqual(self.proc.psl_counts(0), (0, 1))
        # same outcome again: silent
        _, _, text2 = self._run(0, f, g, 5.012e6, 100.0)
        self.assertEqual(text2, "")
        self.assertEqual(self.proc.psl_counts(0), (0, 2))
        # a good sweep on the same overtone: the change of source is logged
        f2, g2 = _synthetic(5.006e6, 60.0, -8.0, 20e-3, 1e-3)
        _, _, text3 = self._run(0, f2, g2, float(f2[np.argmax(g2)]), 60.0)
        self.assertIn("published by the phase-shifted Lorentzian fit", text3)
        self.assertEqual(self.proc.psl_counts(0), (1, 2))

    def test_standard_mode_publishes_the_seed_and_runs_no_fit(self):
        self.proc.set_estimator("argmax")
        f, g = _synthetic(24971700.0, 1600.0, -24.0, 0.5e-3, 0.3e-3)
        pub, fit, text = self._run(1, f, g, 24971380.0, 1580.0)
        self.assertIsNone(fit)
        self.assertEqual((pub.fres, pub.gamma, pub.source), (24971380.0, 1580.0, L.SOURCE_FALLBACK))
        self.assertIn("STANDARD estimator", text)
        self.assertNotIn("FALLBACK", text)
        self.assertEqual(self.proc.psl_counts(1), (0, 0))          # nothing to count: no fit ran
        _, _, text2 = self._run(1, f, g, 24971380.0, 1580.0)
        self.assertEqual(text2, "")

    def test_the_default_mode_is_the_standard(self):
        proc = MultiscanProcess(None)                              # no set_estimator()
        self.assertEqual(proc.estimator_mode(), "argmax")
        self.assertEqual(Constants.IMPEDANCE_ESTIMATOR, "argmax")

    def test_counts_start_at_zero_for_an_unseen_overtone(self):
        self.assertEqual(self.proc.psl_counts(4), (0, 0))


@unittest.skipUnless(HAVE_DUMPS, "research dumps or psl_lib not available")
class ReplayDumpsThroughTheProcessTests(unittest.TestCase):
    """The 45 sweeps of 2026-09-11 through the process's own _publish_resonance:
    every one published by the fit, equal to the offline research numbers."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(RESEARCH, "scripts"))
        import psl_lib
        cls.lib = psl_lib
        cls.Z = np.load(os.path.join(RESEARCH, "data", "sweep_dumps_2026-09-11.npz"))
        with open(os.path.join(HERE, "data", "psl_expected_2026-09-11.json")) as fh:
            cls.expected = json.load(fh)["values"]

    def test_all_45_sweeps_publish_the_fit(self):
        proc = MultiscanProcess(None)
        proc.set_estimator("lorentzian")
        n_of = {"g1": 0, "g3": 1, "g5": 2, "g7": 3, "g9": 4}
        with contextlib.redirect_stdout(io.StringIO()):
            for key, exp in self.expected.items():
                c = self.lib.chain(self.Z[key])
                fr, G = c["fr"], c["G"]
                f_arg, gam0, _ = self.lib.argmax_and_halfwidth(fr, G)
                pub, fit = proc._publish_resonance(n_of[key.split("/")[1]], fr, G, f_arg, gam0)
                self.assertEqual(pub.source, L.SOURCE_FIT, "%s: %s" % (key, pub.reason))
                self.assertLess(abs(pub.fres - exp["fres"]), 2.0, key)
                self.assertLess(abs(pub.gamma - exp["gamma"]), 3.0, key)
                self.assertLess(abs(fit.phi_deg - exp["phi_deg"]), 0.2, key)
        for idx in range(5):
            self.assertEqual(proc.psl_counts(idx), (9, 0), "overtone index %d" % idx)


class WorkerMessageTests(unittest.TestCase):

    def setUp(self):
        self.w = Worker(sampling_time=7, estimator="lorentzian")     # reset_buffers divides by the sampling time
        self.w.reset_buffers(Constants.argument_default_samples)

    @staticmethod
    def _message(idx, with_fit=True):
        f = list(np.linspace(24969000.0, 24974000.0, 51))
        g = list(np.linspace(0.0, 1.0, 51)); b = list(np.linspace(-0.5, 0.5, 51))
        msg = [idx, f, g, b, 24972088.0, 1646.0, 0.0, 0.0, 24970200.0, 24973300.0, 0.4]
        if with_fit:
            msg += [24971737.0, 1582.0,                         # seed = fallback
                    24972088.0, 1646.0, -24.0, 0.0017, 0.55, -0.02, 1.4,   # fit
                    1.0, 12.0, 0.0, "ok", "lorentzian"]
        return msg

    def test_the_published_pair_and_the_fit_fields_are_unpacked(self):
        self.w._queue_data_GB_multi(self._message(2))
        self.assertEqual(self.w.get_fr_G_buffer(2), 24972088.0)
        self.assertEqual(self.w.get_gamma_G_buffer(2), 1646.0)
        fit = self.w.get_fit_G_buffer(2)
        self.assertEqual(fit["source"], "fit")
        self.assertEqual((fit["used"], fit["fallback"]), (12, 0))
        self.assertEqual(fit["f_argmax"], 24971737.0)
        self.assertEqual(fit["gamma_hh"], 1582.0)
        self.assertAlmostEqual(fit["phi_deg"], -24.0)
        self.assertEqual(fit["reason"], "ok")
        self.assertEqual(fit["mode"], "lorentzian")
        self.assertEqual(self.w.get_GB_seq(2), 1)

    def test_the_datalog_name_says_which_estimator_wrote_it(self):
        for mode, suffix in (("lorentzian", "multi_lorentzian"), ("argmax", "multi"), (None, "multi")):
            w = Worker(sampling_time=7, estimator=mode)
            w._csv_filename = "2026-09-16_10-00-00"; w._source = SourceType.multiscan
            self.assertEqual(w.get_csv_filename(), "2026-09-16_10-00-00_%s.csv" % suffix, mode)
            self.assertEqual(w._amplitude_datalog_name(), "2026-09-16_10-00-00_%s_amplitude" % suffix, mode)
            self.assertEqual(w.get_estimator(), mode or "argmax")

    def test_an_older_message_leaves_the_fit_buffer_empty(self):
        self.w._queue_data_GB_multi(self._message(1, with_fit=False))
        self.assertIsNone(self.w.get_fit_G_buffer(1))
        self.assertEqual(self.w.get_fr_G_buffer(1), 24972088.0)

    def test_a_fallback_message_is_read_as_such(self):
        msg = self._message(3)
        msg[20], msg[21], msg[22], msg[23] = 0.0, 3.0, 1.0, "rms 7.1 % of range > 5 %"
        self.w._queue_data_GB_multi(msg)
        fit = self.w.get_fit_G_buffer(3)
        self.assertEqual(fit["source"], "fallback")
        self.assertEqual((fit["used"], fit["fallback"]), (3, 1))
        self.assertIn("rms", fit["reason"])


if __name__ == "__main__":
    unittest.main()
