# -*- coding: utf-8 -*-
"""Peak detection: each peak of the wide sweep confirmed on finer sweeps around it
(core/peak_refine.py and CalibrationProcess._refine_peaks / _sweep_section),
against a simulated line: a Lorentzian in magnitude and phase over a flat
background, the same shape whatever sweep asks for it.

    cd software && PYTHONPATH=. python -m unittest tests.test_peak_refine -v
"""
import contextlib
import io
import unittest

import numpy as np

from openQCM.core.constants import Constants
from openQCM.core import peak_refine as R
from openQCM.processors.Calibration import CalibrationProcess

ADC = 3.3 / 4096
FLAT = np.array([0.0])          # the wide sweep's baselines: flat at 0


class Line(object):
    """A resonance at f_res with full width at half power `fwhm`: `db` dB and
    `deg` degrees at its top, over a flat background with a little noise."""

    def __init__(self, f_res, fwhm, db=6.0, deg=40.0, phase_shift=0.0, seed=1):
        self.f_res, self.fwhm, self.db, self.deg, self.phase_shift = f_res, fwhm, db, deg, phase_shift
        self.rng = np.random.default_rng(seed)
        self.sweeps = []

    def lorentz(self, f):
        x = 2 * (f - self.f_res) / self.fwhm
        return 1 / (1 + x * x)

    def __call__(self, start, stop, step):
        self.sweeps.append((start, stop, step))
        f = np.arange(start, stop + 1, step, dtype=float)
        # power Lorentzian: the amplitude excess falls to 1/sqrt(2) at +-fwhm/2
        a = 1 + (10 ** (self.db / 20) - 1) * np.sqrt(self.lorentz(f))
        mag = 20 * np.log10(a) + self.rng.normal(0, 0.01, len(f))
        phase = self.deg * self.lorentz(f - self.phase_shift) + self.rng.normal(0, 0.05, len(f))
        return f, mag, phase


class ConfirmTests(unittest.TestCase):

    def test_a_peak_that_lags_kilohertz_behind_is_found_where_the_resonance_is(self):
        # the Q-1 bench board, 2026-10-25: F5 stored 3.6 kHz above the resonance
        line = Line(24_937_426.0, 150.0)
        r = R.confirm(24_941_000.0, line, FLAT, FLAT)
        self.assertIsNone(r.rejected)
        self.assertLessEqual(abs(r.frequency - line.f_res), Constants.REFINE_STEP)
        self.assertEqual((r.half_span, r.step), (Constants.REFINE_HALF_SPAN, Constants.REFINE_STEP))
        # +-25 kHz at 50 Hz first, then +-5 kHz at 10 Hz on what it found
        (a1, b1, s1), (a2, b2, s2) = line.sweeps
        self.assertEqual((b1 - a1, s1), (2 * Constants.REFINE_WIDE_HALF_SPAN, Constants.REFINE_WIDE_STEP))
        self.assertEqual((b2 - a2, s2), (2 * Constants.REFINE_HALF_SPAN, Constants.REFINE_STEP))
        self.assertLess(abs((a2 + b2) / 2 - line.f_res), Constants.REFINE_WIDE_STEP)

    def test_every_sweep_is_whole_hertz_on_its_step(self):
        line = Line(14_967_158.5, 120.0)
        R.confirm(14_969_000.4, line, FLAT, FLAT)
        for a, b, s in line.sweeps:
            self.assertIsInstance(a, int)
            self.assertIsInstance(b, int)
            self.assertEqual(a % s, 0)

    def test_a_line_wider_than_the_fine_sweep_is_judged_on_the_wide_one(self):
        # The width is read over a straight line through the ends of the +-5 kHz
        # sweep, which a wide line lifts: 4 kHz reads 2.8 kHz and stays on the fine
        # sweep (found within 20 Hz); the switch comes at about 5.5 kHz (as in openQCM Lab)
        line = Line(4_990_000.0, 8_000.0)                 # a liquid
        r = R.confirm(4_992_000.0, line, FLAT, FLAT)
        self.assertIsNone(r.rejected)
        self.assertEqual(r.half_span, Constants.REFINE_WIDE_HALF_SPAN)
        self.assertLessEqual(abs(r.frequency - line.f_res), Constants.REFINE_WIDE_STEP)

    def test_no_resonance_is_rejected(self):
        line = Line(30_000_000.0, 100.0, db=0.0, deg=0.0)   # nothing there
        r = R.confirm(34_910_000.0, line, FLAT, FLAT)
        self.assertIsNotNone(r.rejected)
        self.assertIsNone(r.frequency)

    def test_a_phase_peak_too_low_or_too_far_is_rejected(self):
        low = R.confirm(34_910_000.0, Line(34_906_546.0, 150.0, deg=5.0), FLAT, FLAT)
        self.assertIn("phase peak", low.rejected)
        far = R.confirm(34_910_000.0, Line(34_906_546.0, 150.0, phase_shift=3_000.0), FLAT, FLAT)
        self.assertIn("apart", far.rejected)

    def test_half_power_width(self):
        f = np.arange(-5000, 5001, 10, dtype=float)
        line = Line(0.0, 400.0)
        _, mag, _ = line(-5000, 5000, 10)
        self.assertAlmostEqual(R.half_power_width(f, mag), 400.0, delta=30.0)
        self.assertIsNone(R.half_power_width(f, np.zeros_like(f)))


class FakeSerial(object):
    """Answers a plain sweep with the counts of a set of lines, as the firmware
    prints them, and the end-of-sweep line."""

    def __init__(self, lines):
        self.lines = lines
        self.buffer = b""
        self.commands = []

    def write(self, data):
        cmd = data.decode()
        self.commands.append(cmd)
        if cmd.strip() == "Q":
            return
        a, b, s = (int(x) for x in cmd.strip().split(";"))
        f = np.arange(a, b + 1, s, dtype=float)
        mag, phase = np.zeros(len(f)), np.zeros(len(f))
        for line in self.lines:
            _, m, p = line(a, b, s)
            mag += m
            phase += p
        bm = (mag * 0.03 + 0.9) * 2 / ADC
        bp = (phase * 0.01 + 0.9) * 1.5 / ADC
        out = "\n".join("%.2f;%.2f" % pair for pair in zip(bm, bp)) + "\n25.00;0;0;s"
        self.buffer += out.encode()

    def inWaiting(self):
        return len(self.buffer)

    def read(self, n):
        out, self.buffer = self.buffer[:n], self.buffer[n:]
        return out


class CalibrationTests(unittest.TestCase):

    def setUp(self):
        self.out = contextlib.redirect_stdout(io.StringIO())
        self.printed = self.out.__enter__()

    def tearDown(self):
        self.out.__exit__(None, None, None)

    def process(self, lines):
        proc = CalibrationProcess(None)
        proc._serial = FakeSerial(lines)
        proc._coeffs_all = proc._coeffs_all_phase = FLAT
        return proc

    def test_the_fundamental_and_the_overtones_are_stored_where_the_resonances_are(self):
        # the bench run of 2026-10-25: the wide sweep's peaks and the resonances
        # the adaptive sweep then measured
        wide = [5_000_500, 14_969_000, 24_941_000, 34_910_000, 44_881_000]
        true = [4_998_363.6, 14_967_158.5, 24_937_426.3, 34_906_545.7, 44_877_398.4]
        proc = self.process([Line(f, 150.0, seed=i) for i, f in enumerate(true)])
        proc._overtone_candidates = ([3, 5, 7, 9], np.array(wide[1:], dtype=float))
        f0, overtones = proc._refine_peaks(float(wide[0]))
        found = [f0] + list(overtones)
        self.assertEqual(len(found), 5)
        for f, t in zip(found, true):
            self.assertLessEqual(abs(f - t), Constants.REFINE_STEP)
        # each decision printed with its numbers
        self.assertEqual(self.printed.getvalue().count("confirmed at"), 5)

    def test_an_overtone_the_fine_sweep_rejects_is_left_out_and_said(self):
        true = [4_998_363.6, 14_967_158.5]
        proc = self.process([Line(f, 150.0, seed=i) for i, f in enumerate(true)])
        proc._overtone_candidates = ([3, 5], np.array([14_969_000.0, 24_941_000.0]))   # no F5 there
        f0, overtones = proc._refine_peaks(5_000_500.0)
        self.assertEqual(len(overtones), 1)
        self.assertIn("Peak F5: wide sweep 24941000 Hz, REJECTED", self.printed.getvalue())

    def test_a_fundamental_the_fine_sweep_rejects_keeps_the_wide_value(self):
        proc = self.process([Line(4_998_363.6, 150.0, deg=2.0)])      # no phase peak
        proc._overtone_candidates = ([], np.array([]))
        f0, overtones = proc._refine_peaks(5_000_500.0)
        self.assertEqual(f0, 5_000_500.0)
        self.assertIn("kept", self.printed.getvalue())

    def test_a_stop_during_the_refining_sweeps_stops_the_board_and_cancels(self):
        proc = self.process([Line(4_998_363.6, 150.0)])
        proc._overtone_candidates = ([], np.array([]))
        proc.stop()
        with self.assertRaises(R.Cancelled):
            proc._refine_peaks(5_000_500.0)
        self.assertEqual(proc._serial.commands[-1], Constants.serial_stop_sweep.decode())


if __name__ == "__main__":
    unittest.main()
