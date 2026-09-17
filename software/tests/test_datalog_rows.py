# -*- coding: utf-8 -*-
"""One multiscan datalog row per cycle, whatever the drain pattern (main `2da0705`, 2026-09-17).

    cd software && PYTHONPATH=. python -m unittest tests.test_datalog_rows -v

The row used to be written from the temperature handler when the STATUS queue's overtone number
read 0 -- a different queue, consumed later -- so one GUI drain wrote 0, 1 or up to 5 identical
rows per cycle (96 duplicates in 486 rows on 2026-09-11, 19 s gaps). The temperature message now
carries the overtone and an end-of-cycle flag, is posted after that overtone's F and D, and the
worker drains F and D before it. These tests feed the worker's queues the way the process does and
count the rows for three drain patterns; the writer is replaced by a recorder.
"""
import contextlib
import datetime
import io
import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openQCM.core import worker as W
from openQCM.core.constants import Constants, SourceType

N = 5          # overtones per cycle
CYCLES = 3


def _now_us():
    return int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() * 1e6)


def _f(c, k):
    return [1e6 * (2 * i + 1) * 5 + 100 * c + k for i in range(N)]


class _Harness(object):
    """A multiscan worker with the CSV writer replaced by a recorder."""

    def __init__(self, sampling_time=-1):
        self.w = W.Worker(source=SourceType.multiscan, sampling_time=sampling_time)
        with contextlib.redirect_stdout(io.StringIO()):
            self.w.reset_buffers(Constants.argument_default_samples)
        self.w._csv_filename = "datalog_rows_test"
        self.all_rows = []                 # every file: the datalog and, on this branch, its _amplitude twin
        self._saved = W.FileStorage.CSVsave_Multi
        W.FileStorage.CSVsave_Multi = staticmethod(
            lambda fn, path, t, T, F, D: self.all_rows.append((fn, t, T, list(F), list(D))))

    @property
    def rows(self):
        """The rows of the datalog itself (the comparison file gets one per row of it)."""
        return [r for r in self.all_rows if not r[0].endswith("_amplitude")]

    @property
    def amplitude_rows(self):
        return [r for r in self.all_rows if r[0].endswith("_amplitude")]

    def close(self):
        W.FileStorage.CSVsave_Multi = self._saved
        for q in (self.w._queue_F_multi, self.w._queue_D_multi, self.w._queue5, self.w._queue6):
            q.close()

    def post(self, c, k, cycle_fields=True):
        """What the process posts for overtone k of cycle c, in the process's order."""
        t = _now_us() + 2_000_000
        d = [10.0 * (i + 1) + c + 0.1 * k for i in range(N)]
        self.w._queue_F_multi.put([[t] * N, _f(c, k)])
        self.w._queue_D_multi.put([[t] * N, d])
        msg = [t, 25.0 + 0.01 * c]
        if cycle_fields:                   # the datalog clock: overtone, end of cycle, the cycle's F and D
            msg += [k, k == N - 1, list(_f(c, k)), list(d)]
            if Constants.DATALOG_AMPLITUDE_TOO:
                msg += [[v + 0.5 for v in _f(c, k)], list(d)]
        self.w._queue5.put(msg)
        self.w._queue6.put([0, 0, c, 0, k, 0, 0])
        time.sleep(0.02)                   # the feeder threads have to land the messages

    def drain(self):
        # the worker's own order (core/worker.py, the consume block)
        self.w.consume_queue_F_multi()
        self.w.consume_queue_D_multi()
        self.w.consume_queue5()
        self.w.consume_queue6()

    def run(self, pattern):
        for c in range(CYCLES):
            for k in range(N):
                self.post(c, k)
                if pattern == "per overtone":
                    self.drain()
            if pattern == "per cycle":
                self.drain()
        time.sleep(0.05)
        self.drain()                       # "all at once", and the tail of the others


class DatalogRowsTests(unittest.TestCase):

    def _rows_for(self, pattern):
        h = _Harness()
        try:
            h.run(pattern)
            return list(h.rows)
        finally:
            h.close()

    def test_one_row_per_cycle_whatever_the_drain_pattern(self):
        for pattern in ("per overtone", "per cycle", "all at once"):
            rows = self._rows_for(pattern)
            self.assertEqual(len(rows), CYCLES, pattern)
            # every row carries a whole cycle: the last overtone's values of that cycle
            for c, row in enumerate(rows):
                self.assertEqual(row[3], _f(c, N - 1), "%s, cycle %d" % (pattern, c))
            # and the relative times are distinct and increasing: no duplicate rows
            times = [row[1] for row in rows]
            self.assertEqual(times, sorted(times))
            self.assertEqual(len(set(times)), CYCLES, pattern)

    def test_the_comparison_datalog_gets_one_row_per_row_of_the_datalog(self):
        h = _Harness()
        try:
            h.run("per cycle")
            self.assertEqual(len(h.rows), CYCLES)
            self.assertEqual(len(h.amplitude_rows), CYCLES if Constants.DATALOG_AMPLITUDE_TOO else 0)
            for c, row in enumerate(h.amplitude_rows):          # its own cycle's pair, from the same message
                self.assertEqual(row[3], [v + 0.5 for v in _f(c, N - 1)])
        finally:
            h.close()

    def test_the_gate_is_the_message_not_the_status_queue(self):
        """The status queue's overtone number no longer decides anything: with it
        frozen at 0 (the old gate's 'write' value) the rows are still one per cycle."""
        h = _Harness()
        try:
            for c in range(CYCLES):
                for k in range(N):
                    t = _now_us() + 2_000_000
                    h.w._queue_F_multi.put([[t] * N, _f(c, k)])
                    h.w._queue_D_multi.put([[t] * N, [1.0] * N])
                    h.w._queue5.put([t, 25.0, k, k == N - 1, _f(c, k), [1.0] * N])
                    h.w._queue6.put([0, 0, c, 0, 0, 0, 0])          # overtone 0, always
                    time.sleep(0.02)
                    h.drain()
            self.assertEqual(len(h.rows), CYCLES)
        finally:
            h.close()

    def test_a_two_element_temperature_message_writes_no_multiscan_row(self):
        """Serial, Calibration and an older process post [time, T]: no cycle end, no row."""
        h = _Harness()
        try:
            for c in range(2):
                for k in range(N):
                    h.post(c, k, cycle_fields=False)
                    h.drain()
            self.assertEqual(h.rows, [])
        finally:
            h.close()

    def test_the_time_controlled_branch_writes_whole_cycles_too(self):
        """A sampling time of 7 s (the worker's default unit, one buffer slot) with the
        interval forced to have elapsed before every drain: a row still comes only at
        a cycle end, from the averaged stores, never mid-cycle."""
        h = _Harness(sampling_time=7)
        try:
            for c in range(CYCLES):
                for k in range(N):
                    h.post(c, k)
                    h.w.time_pre = 0                   # "the interval has elapsed"
                    h.drain()
            self.assertEqual(len(h.rows), CYCLES)
        finally:
            h.close()


if __name__ == "__main__":
    unittest.main()
