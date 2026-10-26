# -*- coding: utf-8 -*-
"""
VER 0.1.6G-ADAPTIVE — each peak of the peak detection confirmed on finer sweeps
around it (branch impedance-analysis-sweep-adaptive, 2026-10-26).

Ported from openQCM Lab (core/src/openqcm_lab/analysis/peak_detection.py and
Q1Session._refine_peaks, commits 9719141 and d547680 of 2026-10-21).

WHY. The wide sweep (1-51 MHz in 500 Hz steps, about 6 MHz/s) is far too fast
for the crystal: its peaks lag behind the resonances. On the Q-1 bench board
(2026-10-25) the stored peaks were 1.8-3.6 kHz above the resonances the adaptive
sweep then measured; openQCM Lab measured 1.5-5 kHz on a Next. Its 500 Hz step is
also wider than a 5 MHz crystal's line in air (FWHM ~100-340 Hz), so whether it
catches an overtone's phase peak depends on where the line falls on the grid.

HOW (Constants.REFINE_*). Around each candidate:
  1. +-25 kHz at 50 Hz: where the resonance really is (a narrow sweep around a
     peak that far off can miss it). Its maximum at the edge: no resonance here.
  2. +-5 kHz at 10 Hz on that maximum, unless the line is wider than 2/3 of it
     (a liquid): then the +-25 kHz sweep is the one judged.
  3. Confirmed when the magnitude maximum is well inside the sweep, the phase
     maximum is close to it and high enough (both corrected with the wide
     sweep's baselines).

Nothing here touches the serial port: `sweep(start, stop, step)` does.
"""

from collections import namedtuple

import numpy as np

from openQCM.core.constants import Constants


class Cancelled(Exception):
    """The user stopped the peak detection during a refining sweep."""


# What one confirmation found: `frequency` the confirmed peak (None when
# rejected), the magnitude and phase maxima, the phase maximum (deg, baseline
# corrected), the half-power width (Hz, None when the line does not fall to
# half power on both sides), the sweep judged (half span, step) and the reason
# for a rejection
Refined = namedtuple("Refined", "frequency f_mag f_phase phase_peak freq_diff width half_span step rejected")


def half_power_width(freq, mag_db):
    """Width (Hz) of a resonance at half its power over the background: the excess
    amplitude over a straight line through the ends of the sweep, in linear units.
    None when the line does not fall to that level on both sides inside the sweep."""
    freq = np.asarray(freq, dtype=float)
    a = 10 ** (np.asarray(mag_db, dtype=float) / 20)
    k = max(len(a) // 20, 1)
    base = np.interp(freq, [freq[:k].mean(), freq[-k:].mean()], [a[:k].mean(), a[-k:].mean()])
    excess = a - base
    i = int(np.argmax(excess))
    if excess[i] <= 0:
        return None
    level = excess[i] / np.sqrt(2)
    below = np.where(excess[:i] < level)[0]
    above = np.where(excess[i:] < level)[0]
    if not len(below) or not len(above):
        return None
    return float(freq[i + above[0]] - freq[below[-1]])


def judge(freq, mag, phase, mag_coeffs, phase_coeffs, half_span, step):
    """Confirm a resonance on a sweep around its candidate: magnitude and phase
    corrected with the wide sweep's baselines, the magnitude maximum well inside
    the sweep, the phase maximum close to it and high enough."""
    freq = np.asarray(freq, dtype=float)
    mag_c = np.asarray(mag, dtype=float) - np.polyval(mag_coeffs, freq)
    phase_c = np.asarray(phase, dtype=float) - np.polyval(phase_coeffs, freq)
    i, j = int(np.argmax(mag_c)), int(np.argmax(phase_c))
    f_mag, f_phase, phase_peak = float(freq[i]), float(freq[j]), float(phase_c[j])
    diff = abs(f_mag - f_phase)
    width = half_power_width(freq, mag_c)
    max_diff = max(Constants.REFINE_MAX_DIFF, Constants.REFINE_MAX_DIFF_WIDTHS * (width or 0))
    edge = int(len(freq) * Constants.REFINE_EDGE)
    rejected = None
    if not edge <= i < len(freq) - edge:
        rejected = "no resonance on the fine sweep (its maximum is at the edge)"
    elif diff > max_diff:
        rejected = "magnitude and phase peaks %.0f Hz apart (limit %.0f Hz)" % (diff, max_diff)
    elif phase_peak <= Constants.REFINE_PHASE_THRESHOLD:
        rejected = "phase peak %.1f deg at or below %d deg" % (phase_peak, Constants.REFINE_PHASE_THRESHOLD)
    return Refined(None if rejected else f_mag, f_mag, f_phase, phase_peak, diff, width,
                   half_span, step, rejected)


def around(sweep, f, half_span, step):
    """`sweep` over f +- half_span in steps of `step`, on the step's grid: (freq,
    mag dB, phase deg)."""
    start = int(round(f / step)) * step - half_span
    return sweep(start, start + 2 * half_span, step)


def confirm(f, sweep, mag_coeffs, phase_coeffs):
    """A candidate peak f of the wide sweep, confirmed or rejected on finer sweeps
    around it (see the module's HOW). `sweep(start, stop, step)` measures one plain
    sweep and returns (freq, mag dB, phase deg); it raises Cancelled on a Stop."""
    wide = around(sweep, f, Constants.REFINE_WIDE_HALF_SPAN, Constants.REFINE_WIDE_STEP)
    wide_args = wide + (mag_coeffs, phase_coeffs, Constants.REFINE_WIDE_HALF_SPAN, Constants.REFINE_WIDE_STEP)
    corrected = wide[1] - np.polyval(mag_coeffs, wide[0])
    i = int(np.argmax(corrected))
    edge = int(len(corrected) * Constants.REFINE_EDGE)
    if not edge <= i < len(corrected) - edge:
        return judge(*wide_args)            # rejected: no resonance here
    fine = around(sweep, float(wide[0][i]), Constants.REFINE_HALF_SPAN, Constants.REFINE_STEP)
    width = half_power_width(fine[0], fine[1] - np.polyval(mag_coeffs, fine[0]))
    if width is None or width > 2 * Constants.REFINE_HALF_SPAN / 3:
        return judge(*wide_args)            # a line too wide for the fine sweep (a liquid)
    return judge(*fine, mag_coeffs, phase_coeffs, Constants.REFINE_HALF_SPAN, Constants.REFINE_STEP)


def describe(label, f, refined):
    """One line for the terminal: what the wide sweep gave and what the fine one
    decided, with its numbers."""
    r = refined
    seen = ("magnitude max %.0f Hz, phase max %.0f Hz (%.1f deg, %.0f Hz apart), half-power width %s, "
            "on +-%d Hz at %d Hz" % (r.f_mag, r.f_phase, r.phase_peak, r.freq_diff,
                                     "%.0f Hz" % r.width if r.width is not None else "not found",
                                     r.half_span, r.step))
    if r.rejected:
        return "Peak %s: wide sweep %.0f Hz, REJECTED on the fine sweep: %s -- %s" % (label, f, r.rejected, seen)
    return "Peak %s: wide sweep %.0f Hz, confirmed at %.0f Hz (%+.0f Hz) -- %s" % (
        label, f, r.frequency, r.frequency - f, seen)
