# -*- coding: utf-8 -*-
"""The adaptive sweep (core/adaptive.py and its methods in MultiscanProcess), headless,
against a simulated board: a Butterworth-Van Dyke crystal behind the measuring divider
that answers the firmware's commands (the 1 Hz sweep, 'Z', 'F') and LAGS as a real
crystal does (the motional admittance relaxes towards its steady state with the decay
time tau = 1/(2 pi Gamma) while the drive frequency moves).

    cd software && PYTHONPATH=. python -m unittest tests.test_adaptive -v
"""
import contextlib
import io
import math
import unittest

import numpy as np

from openQCM.core.constants import Constants
from openQCM.core import adaptive as A
from openQCM.processors.Multiscan import MultiscanProcess

R17 = MultiscanProcess.R17_EXACT
V_CP = MultiscanProcess.V_CP_EXACT
ADC = 3.3 / 4096


class Crystal(object):
    """BVD: R1, L1, C1 in series, C0 across; G peaks at fs with half width fs / (2 Q)."""

    def __init__(self, fs=4_998_350.0, r1=20.0, gamma=41.0, c0=5e-12, delta=3.0):
        self.fs, self.r1, self.c0, self.delta = fs, r1, c0, delta
        self.q = fs / (2 * gamma)

    def motional(self, f, fs):
        ws = 2 * math.pi * fs
        l1 = self.q * self.r1 / ws
        c1 = 1 / (ws * ws * l1)
        w = 2 * math.pi * f
        return 1 / (self.r1 + 1j * (w * l1 - 1 / (w * c1)))

    @property
    def tau(self):
        return 1 / (2 * math.pi * self.fs / (2 * self.q))


class Board(object):
    """Answers the firmware's commands with the counts of the AD8302 behind the divider.
    `lag`: the motional admittance follows the drive with the crystal's decay time
    (its envelope relaxing and turning with the detuning, as a resonator's does);
    `drift`: the resonance moves (Hz/s of the board's own clock)."""

    def __init__(self, crystal, lag=True, drift=0.0, version="0.1.5d-SEG", refuse_z=False, seed=1):
        self.crystal, self.lag, self.drift, self.version = crystal, lag, drift, version
        self.refuse_z = refuse_z
        self.commands = []        # every command received, as sent
        self.t = 0.0
        self.y = None
        self.rng = np.random.default_rng(seed)

    def now(self):
        return self.t

    def fs(self):
        return self.crystal.fs + self.drift * self.t

    def points(self, freqs, dwell_us, substeps=16):
        """Each point as the firmware measures it: the DDS jumps to f, waits the
        dwell, then the ADC averages the detector's two outputs over the point
        (83.4 us, here in `substeps`)."""
        out = []
        c = self.crystal
        for f, dwell in zip(freqs, dwell_us):
            self._evolve(f, dwell * 1e-6)
            vm = vp = 0.0
            for _ in range(substeps):
                self._evolve(f, Constants.ADAPTIVE_POINT_US * 1e-6 / substeps)
                zq = 1 / (self.y + 1j * 2 * math.pi * f * c.c0)
                z = zq + R17
                m, phi = abs(z), -np.angle(z)
                vm += (V_CP - 0.6 * math.log10(m / R17)) / substeps
                reading = abs(phi * 180 / math.pi) - c.delta
                vp += (1.8 - 0.01 * reading) / substeps
            bm = (vm + Constants.V_MAG_DECADE_OFFSET) * 2 / ADC + self.rng.normal(0, 0.1)
            bp = vp * 1.5 / ADC + self.rng.normal(0, 0.1)
            out.append("%.2f;%.2f" % (bm, bp))
        return out

    def _evolve(self, f, dt):
        """The motional admittance after dt at the drive f: its envelope, in the frame
        of the drive, obeys dA/dt = -(1/tau + j 2 pi (f - fs)) A + drive."""
        self.t += dt
        target = self.crystal.motional(f, self.fs())
        if not self.lag or self.y is None:
            self.y = target
        else:
            k = 1 / self.crystal.tau + 2j * math.pi * (f - self.fs())
            self.y = target + (self.y - target) * np.exp(-k * dt)

    def answer(self, cmd):
        self.commands.append(cmd)
        cmd = cmd.strip()
        end = "25.00;0;0;s"
        if cmd == "F":
            return self.version + "\n"
        if cmd.startswith("Z"):
            if self.refuse_z:
                return "ERR_SEG\n" + end
            v = [int(x) for x in cmd[1:].split(";")]
            freqs, dwell = [], []
            for i in range(0, len(v), 4):
                a, b, s, d = v[i:i + 4]
                seg = list(range(a, b + (1 if s > 0 else -1), s))
                freqs += seg
                dwell += [d] * len(seg)
            return "\n".join(self.points(freqs, dwell)) + "\n" + end
        a, b, s = (int(float(x)) for x in cmd.split(";"))
        freqs = list(range(a, b + 1, s))
        return "\n".join(self.points(freqs, [0] * len(freqs))) + "\n" + end


class FakeSerial(object):
    def __init__(self, board):
        self.board = board
        self.buffer = b""

    def write(self, data):
        self.buffer += self.board.answer(data.decode()).encode()

    def inWaiting(self):
        return len(self.buffer)

    def read(self, n):
        out, self.buffer = self.buffer[:n], self.buffer[n:]
        return out

    def reset_input_buffer(self):
        self.buffer = b""

    def reset_output_buffer(self):
        pass


class Recorder(object):
    """Every parser queue: keeps the messages by method name."""

    def __init__(self):
        self.calls = {}

    def __getattr__(self, name):
        def record(*args):
            self.calls.setdefault(name, []).append(args[0] if args else None)
        return record

    def take_pid_read_request(self):
        return False

    def take_tec_reset_request(self):
        return False


def process(board):
    proc = MultiscanProcess(None)
    rec = Recorder()
    for name in ("_parser1", "_parser2", "_parser3", "_parser4", "_parser5", "_parser6",
                 "_parser_F_multi", "_parser_D_multi", "_parser_A_multi", "_parser_P_multi",
                 "_parser_GB_multi", "_parser_current_tec"):
        setattr(proc, name, rec)
    proc._serial = FakeSerial(board)
    proc._overtones_in_cycle = 1
    proc.set_frequencies_RT = lambda *a: None      # never touch the runtime files from a test
    proc._environment = Constants.environment
    return proc, rec


def window(f0):
    start, stop = f0 - Constants.LEFT, f0 + Constants.RIGHT
    return start, stop, np.arange(Constants.argument_default_samples) * 1.0 + start


def cycles(proc, board, n, f0, overtone=0, coeffs=(0.0,)):
    start, stop, readF = window(f0)
    for k in range(n):
        proc._cycle_failed = set()
        proc._adaptive_overtone(k, overtone, np.array(coeffs), start, stop, readF,
                                Constants.argument_default_samples, Constants.SG_WINDOW_SIZE,
                                Constants.argument_default_samples, Constants.SPLINE_FACTOR, 0)


class PlanTests(unittest.TestCase):

    def test_coarse_first_then_a_lead_in_then_the_fine_zone_up_and_down_slowly(self):
        gamma = 41.0
        plan = A.SweepPlan.around(4_998_350.0, gamma, 4_986_350, 5_004_350)
        segs = plan.segments
        # the first point waits 3 decay times far from the resonance (the crystal
        # rings on from the sweep before), then coarse points over the rest of the
        # window, no dwell, before anything near the resonance
        low = 4_986_350
        self.assertEqual(segs[0][:2], (low, low))
        self.assertAlmostEqual(segs[0][3] * 1e-6, Constants.ADAPTIVE_SETTLE_TAU / (2 * math.pi * gamma), delta=1e-5)
        self.assertEqual(segs[1][0], low + Constants.ADAPTIVE_COARSE_STEP)
        self.assertEqual([s[2] for s in segs[1:3]], [Constants.ADAPTIVE_COARSE_STEP] * 2)
        self.assertEqual([s[3] for s in segs[1:3]], [0, 0])
        lead, up, down = segs[3:]
        self.assertEqual(plan.fine, [4, 5])
        self.assertEqual((up[0], up[1]), (down[1], down[0]))         # straight back down
        self.assertEqual(up[2], -down[2])
        self.assertEqual(lead[1] + lead[2], up[0])                   # the lead-in runs into the zone
        # +-4 Gamma, swept at 0.125 x 2 pi Gamma^2 Hz/s
        self.assertAlmostEqual((up[1] - up[0]) / 2, 4 * gamma, delta=1.0)
        rate = up[2] / ((Constants.ADAPTIVE_POINT_US + up[3]) * 1e-6)
        self.assertAlmostEqual(rate / (2 * math.pi * gamma ** 2), Constants.ADAPTIVE_RATE_K, delta=0.01)
        # the lead-in lasts 3 decay times
        n_lead = (lead[1] - lead[0]) // lead[2] + 1
        self.assertGreaterEqual(n_lead * (Constants.ADAPTIVE_POINT_US + lead[3]) * 1e-6,
                                3 / (2 * math.pi * gamma))
        self.assertTrue(plan.command().startswith("Z%d;" % segs[0][0]))
        self.assertEqual(plan.command().count(";"), 4 * len(segs) - 1)
        self.assertLess(plan.seconds(), 0.7)                          # the full sweep takes 1.5 s

    def test_a_narrow_line_never_asks_for_a_dwell_the_firmware_refuses(self):
        # Gamma 2 Hz at 1 Hz steps would need 0.3 s a point; Z takes 100 ms at most
        plan = A.SweepPlan.around(4_998_350.0, 2.0, 4_986_350, 5_004_350)
        self.assertIsNotNone(plan)
        self.assertEqual(max(seg[3] for seg in plan.segments), Constants.ADAPTIVE_DWELL_MAX_US)

    def test_no_room_no_plan(self):
        self.assertIsNone(A.SweepPlan.around(5e6, 0.0, 4_988_000, 5_006_000))
        self.assertIsNone(A.SweepPlan.around(5_006_200.0, 41.0, 4_988_000, 5_006_000))   # past the window


class AdaptiveSweepTests(unittest.TestCase):

    def setUp(self):
        self.out = contextlib.redirect_stdout(io.StringIO())
        self.out.__enter__()

    def tearDown(self):
        self.out.__exit__(None, None, None)

    def full_sweep(self, crystal, lag):
        """f and Gamma of one full 1 Hz sweep through the chain (locate)."""
        board = Board(crystal, lag=lag)
        proc, _ = process(board)
        sweeper = A.AdaptiveSweep(proc, clock=board.now)
        start, stop, readF = window(round(crystal.fs))
        n = Constants.argument_default_samples
        bm, bp, _ = proc._measure(0, "%d;%d;1\n" % (start, stop), n, 10)
        published = sweeper.locate(0, readF, bm, bp, Constants.SG_WINDOW_SIZE, n)
        return published.fres, published.gamma

    def test_the_simulated_crystal_lags_a_full_sweep_as_the_real_one(self):
        crystal = Crystal()
        f_slow, g_slow = self.full_sweep(crystal, lag=False)
        f_lag, g_lag = self.full_sweep(crystal, lag=True)
        self.assertGreater(f_lag - f_slow, 10.0)          # swept up, f reads high (bench: +26 Hz)
        self.assertGreater(g_lag / g_slow, 1.05)          # and Gamma wide (bench: +18 %)

    def adaptive(self, crystal, lag, n=6):
        board = Board(crystal, lag=lag)
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        self.assertIsNotNone(proc._sweeper)
        proc._sweeper.clock = board.now
        cycles(proc, board, n, round(crystal.fs))
        return proc, rec

    def test_the_adaptive_sweep_reads_as_if_the_crystal_did_not_lag(self):
        """Up and down at 0.125 x 2 pi Gamma^2 and averaged: as the same sweep of a
        crystal that follows the drive at once (bench, 2026-10-24: within 1 Hz and
        0.3 %); and as the full sweep that does not lag within 5 % on Gamma, the
        spline's smoothing (SPLINE_FACTOR_G over 18 001 points) being spent on the
        peak there (+2.7 % on this crystal)."""
        crystal = Crystal()
        _, rec = self.adaptive(crystal, lag=True)
        _, still = self.adaptive(crystal, lag=False)
        rows = rec.calls["add5"]
        self.assertEqual(len(rows), 6 - Constants.ADAPTIVE_WARMUP)        # one row a cycle after the warm-up
        f = np.array([r[4][0] for r in rows])
        f_still = np.array([r[4][0] for r in still.calls["add5"]])
        gamma = np.array([m[5] for m in rec.calls["add_GB_multi"]])[-3:]
        gamma_still = np.array([m[5] for m in still.calls["add_GB_multi"]])[-3:]
        self.assertLessEqual(np.max(np.abs(f - f_still)), 1.0)            # the 1 Hz grid of the maximum
        self.assertLess(abs(gamma.mean() / gamma_still.mean() - 1), 0.01)
        f_full, g_full = self.full_sweep(crystal, lag=False)
        self.assertLessEqual(np.max(np.abs(f - f_full)), 1.0)
        self.assertLess(abs(gamma.mean() / g_full - 1), 0.05)
        # the panel gets the published pair, the aligned G and B on the fine zone
        msg = rec.calls["add_GB_multi"][-1]
        self.assertEqual(len(msg[1]), len(msg[2]))
        self.assertEqual(len(msg[2]), len(msg[3]))
        self.assertAlmostEqual(msg[4], f[-1], delta=1e-6)
        # the amplitude plot gets a 1 Hz sweep over the whole window
        freq, amp = rec.calls["add_A_multi"][-1]
        self.assertEqual(len(freq[0]), Constants.argument_default_samples)

    def test_the_first_point_waits_for_the_ringing_of_the_sweep_before(self):
        """With one overtone the sweep before ends in the fine zone: without the wait
        the first coarse points read the crystal still ringing and G's baseline is off."""
        crystal = Crystal()
        settle = Constants.ADAPTIVE_SETTLE_TAU
        try:
            Constants.ADAPTIVE_SETTLE_TAU = 0.0
            _, rec = self.adaptive(crystal, lag=True)
        finally:
            Constants.ADAPTIVE_SETTLE_TAU = settle
        _, still = self.adaptive(crystal, lag=False)
        _, waited = self.adaptive(crystal, lag=True)
        g = lambda r: np.mean([m[5] for m in r.calls["add_GB_multi"]][-3:])
        self.assertGreater(abs(g(rec) / g(still) - 1), 0.02)
        self.assertLess(abs(g(waited) / g(still) - 1), 0.01)

    def test_a_moving_resonance_leaves_no_hole_in_the_readings(self):
        crystal = Crystal()
        board = Board(crystal, lag=True, drift=-20.0)         # vapour condensing: -20 Hz/s
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        proc._sweeper.clock = board.now
        cycles(proc, board, 12, round(crystal.fs))
        f = np.array([r[4][0] for r in rec.calls["add5"]])
        self.assertEqual(len(f), 12 - Constants.ADAPTIVE_WARMUP)
        self.assertTrue(np.all(np.isfinite(f)))
        self.assertLess(np.max(np.diff(f)), 0.0)              # it follows the resonance down

    def test_the_locating_sweep_latches_no_fold_and_counts_in_no_statistics(self):
        board = Board(Crystal())
        proc, _ = process(board)
        proc.set_estimator("lorentzian")
        latched, witnessed = [], []
        proc._fold_latched = lambda *a: latched.append(a) or a[1]
        proc._witness_resonance = lambda *a: witnessed.append(a)
        sweeper = A.AdaptiveSweep(proc, clock=board.now)
        start, stop, readF = window(round(board.crystal.fs))
        n = Constants.argument_default_samples
        bm, bp, _ = proc._measure(0, "%d;%d;1\n" % (start, stop), n, 10)
        decisions = []
        decide = proc._phase_fold_decision
        proc._phase_fold_decision = lambda *a: decisions.append(decide(*a)) or decisions[-1]
        sweeper.locate(0, readF, bm, bp, Constants.SG_WINDOW_SIZE, n)
        self.assertIsNotNone(decisions[0][0])            # there was a decision to latch
        self.assertTrue(sweeper.located(0))
        self.assertEqual((latched, witnessed), ([], []))

    def test_the_full_sweep_sends_whole_hertz_and_is_analysed_on_them(self):
        crystal = Crystal()
        board = Board(crystal, lag=True)
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        proc._sweeper.clock = board.now
        cycles(proc, board, 4, crystal.fs + 0.6)         # a window from the last f_res, not whole
        plain = [c for c in board.commands if c[0].isdigit()]
        self.assertEqual(len(plain), 1)
        self.assertNotIn(".", plain[0])
        self.assertEqual(len(rec.calls["add5"]), 4 - Constants.ADAPTIVE_WARMUP)

    def test_the_baselines_leave_out_the_lead_in(self):
        crystal = Crystal()
        board = Board(crystal, lag=True)
        proc, _ = process(board)
        proc.set_adaptive(True)
        proc._sweeper = sweeper = proc._start_adaptive()
        seen = []
        original = sweeper._pass
        sweeper._pass = lambda overtone, plan, idx, coarse, *a: (seen.append((plan, coarse.copy()))
                                                                 or original(overtone, plan, idx, coarse, *a))
        cycles(proc, board, 2, round(crystal.fs))
        plan, coarse = seen[-1]
        lead = plan.indices(plan.fine[0] - 1)
        self.assertFalse(coarse[lead].any())
        self.assertTrue(coarse[:lead[0]].all())          # every coarse point before it is kept

    def test_a_failed_sweep_forgets_the_overtone_and_the_next_cycle_locates_it_again(self):
        crystal = Crystal()
        board = Board(crystal, lag=True)
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        cycles(proc, board, 3, round(crystal.fs))
        board.refuse_z = True
        start, stop, readF = window(round(crystal.fs))
        proc._cycle_failed = set()
        proc._adaptive_overtone(3, 0, np.array([0.0]), start, stop, readF, Constants.argument_default_samples,
                                Constants.SG_WINDOW_SIZE, Constants.argument_default_samples,
                                Constants.SPLINE_FACTOR, 0)
        self.assertFalse(proc._sweeper.located(0))
        board.refuse_z = False
        sent = len(board.commands)
        proc._cycle_failed = set()
        proc._adaptive_overtone(4, 0, np.array([0.0]), start, stop, readF, Constants.argument_default_samples,
                                Constants.SG_WINDOW_SIZE, Constants.argument_default_samples,
                                Constants.SPLINE_FACTOR, 0)
        self.assertTrue(board.commands[sent][0].isdigit())    # a full sweep first
        self.assertTrue(np.isfinite(rec.calls["add5"][-1][4][0]))

    def test_a_full_sweep_with_no_whole_band_is_not_published_and_says_so_once(self):
        crystal = Crystal(gamma=20000.0)                 # a damped load: wider than the window
        board = Board(crystal, lag=True)
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        cycles(proc, board, 5, round(crystal.fs))
        self.assertNotIn("add_GB_multi", rec.calls)
        rows = rec.calls["add5"]
        self.assertEqual(len(rows), 5 - Constants.ADAPTIVE_WARMUP)
        self.assertTrue(all(math.isnan(r[4][0]) for r in rows))
        said = [m for m in rec.calls["add_message"] if "no whole resonance band" in m]
        self.assertEqual(len(said), 1)

    def test_without_the_segmented_sweep_the_run_uses_the_full_sweep_and_says_so(self):
        board = Board(Crystal(), version="0.1.5d")
        proc, rec = process(board)
        proc.set_adaptive(True)
        self.assertIsNone(proc._start_adaptive())
        self.assertTrue(any("FULL 1 Hz sweep" in m for m in rec.calls["add_message"]))

    def test_an_overtone_not_read_leaves_its_cell_empty_and_the_row_is_written(self):
        crystal = Crystal()
        board = Board(crystal, lag=True)
        proc, rec = process(board)
        proc.set_adaptive(True)
        proc._sweeper = proc._start_adaptive()
        cycles(proc, board, 3, round(crystal.fs))
        board.refuse_z = True                                # the firmware refuses the next sweeps
        start, stop, readF = window(round(crystal.fs))
        proc._cycle_failed = set()
        proc._adaptive_overtone(3, 0, np.array([0.0]), start, stop, readF, Constants.argument_default_samples,
                                Constants.SG_WINDOW_SIZE, Constants.argument_default_samples,
                                Constants.SPLINE_FACTOR, 0)
        last = rec.calls["add5"][-1]
        self.assertTrue(math.isnan(last[4][0]))
        self.assertTrue(last[3])                             # the end of the cycle: the row is written


if __name__ == "__main__":
    unittest.main()
