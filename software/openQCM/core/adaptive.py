# -*- coding: utf-8 -*-
"""
VER 0.1.6G-ADAPTIVE — the adaptive sweep of the conductance analysis
(experimental, branch impedance-analysis-sweep-adaptive, 2026-10-25).

Ported from openQCM Lab (core/src/openqcm_lab/analysis/conductance.py), where it
was developed and validated on a bench board on 2026-10-24/25. The analysis of
each sweep is THIS branch's, unchanged: the methods of MultiscanProcess
(_RX_exact, _G_exact, _B_exact, _phase_fold_decision, _fold_latched,
parameters_finder_impedance_exact) and core/lorentzian.publish(). What this
module adds is where the sweep goes and how its passes are combined.

WHY. The 1 Hz sweep, 83 us a point (12 kHz/s), is fast against the crystal's
decay time tau = 1/(2 pi Gamma): 4 ms on the fundamental in air. The resonance
lags behind the sweep. Measured on the bench board in air: swept up, f reads
+26 Hz and Gamma +18 % on the fundamental (+24 Hz / +11 % on the 3rd, +23 Hz /
+6 % on the 5th); swept down, as much the other way; swept slowly, up and down
agree. The lag scales with kappa = rate / (2 pi Gamma^2).

HOW (Constants.ADAPTIVE_*). One full sweep locates the resonance; it is never
published (it lags). Then each sweep is one 'Z' command of the firmware
(0.1.5d-SEG), its segments in this order:
  1. coarse points (100 Hz) over the rest of the window, for the baselines:
     the phase far from the resonance, G at the low end of the window;
  2. a lead-in of 3 tau below the fine zone, for the jump's transient to die out;
  3. the fine zone, +-4 Gamma of the last resonance, swept UP and straight back
     DOWN at 0.125 * 2 pi Gamma^2 Hz/s (the segment's dwell);
  4. each pass through the chain of elaborate_multi; f and Gamma are the means
     of the two passes, in which the remaining lag cancels.
For the display the two passes are moved back by +-lag and averaged (drawn as
measured, interleaved, they zigzag on the flanks); the measurement does not use
that.

A MOVING RESONANCE (vapour condensing, a film growing; bench run of 2026-10-25,
where the first version left holes in the readings): the fine zone goes where
the resonance will be, from its speed over the last two adaptive sweeps; a
sweep that loses it is not thrown away: its coarse points span the window, so
the peak of G is found among them and the fine zone swept again around it at
once, up to ADAPTIVE_RELOCATE times; only then a full sweep.

Nothing here touches Qt, files or the serial port: the process sweeps, this
module plans and analyses.
"""

from collections import namedtuple
import math
import time

import numpy as np
from scipy.interpolate import UnivariateSpline

from openQCM.core.constants import Constants
from openQCM.core import lorentzian
from openQCM.core.resonance import savitzky_golay
from openQCM.common.logger import Logger as Log

TAG = ""

# The chain's own smoothing kept in HERTZ at any step: SG_WINDOW_SIZE samples of
# the 1 Hz sweep
SG_WINDOW_HZ = Constants.SG_WINDOW_SIZE * Constants.FREQUENCY_STEP
FULL_POINTS = Constants.argument_default_samples      # 18 001: the full sweep's points


def volts(bit_mag, bit_phase):
    """V_MAG (attenuator undone) and V_PHS of the AD8302, as _Vmag_bit_mag and
    _Vphase_bit_phase compute them from the averaged ADC counts."""
    adc_to_volt = 3.3 / 4096
    v_mag = np.asarray(bit_mag, dtype=float) * adc_to_volt / 2 - Constants.V_MAG_DECADE_OFFSET
    v_phs = np.asarray(bit_phase, dtype=float) * adc_to_volt / 1.5
    return v_mag, v_phs


def magnitude_phase(bit_mag, bit_phase):
    """dB and degrees, as run() converts the counts for the amplitude/phase plot."""
    adc_to_volt = 3.3 / 4096
    vcp = 0.9
    mag = (np.asarray(bit_mag, dtype=float) * adc_to_volt / 2 - vcp) / 0.03
    phase = (np.asarray(bit_phase, dtype=float) * adc_to_volt / 1.5 - vcp) / 0.01
    return mag, phase


###############################################################################
# The plan of one adaptive sweep
###############################################################################
class SweepPlan(object):
    """The segments of one adaptive sweep, in the order they are swept: (start,
    stop, step, dwell_us), stop included, upwards (step > 0) or downwards
    (step < 0), with a wait of dwell_us at each of its points. The firmware's 'Z'
    command (0.1.5d-SEG) sweeps exactly these points. `fine` lists the passes of
    the fine zone, each analysed on its own."""

    def __init__(self, segments, fine):
        self.segments = segments
        self.fine = fine

    @classmethod
    def around(cls, f_res, gamma, low, high, point_us=Constants.ADAPTIVE_POINT_US,
               rate_k=Constants.ADAPTIVE_RATE_K, extra_hz=0.0):
        """Coarse points over the window [low, high] first (the first one after a
        wait of ADAPTIVE_SETTLE_TAU decay times), then a lead-in, then the fine
        zone around f_res up and straight back down at rate_k * 2 pi Gamma^2.
        None when there is no room for it."""
        if not gamma > 0:
            return None
        step = max(Constants.FREQUENCY_STEP, int(gamma // Constants.ADAPTIVE_POINTS_PER_GAMMA))
        rate = rate_k * 2 * math.pi * gamma ** 2
        dwell = min(Constants.ADAPTIVE_DWELL_MAX_US, max(0, int(round(step / rate * 1e6 - point_us))))
        lead = max(2, int(math.ceil(Constants.ADAPTIVE_LEAD_TAU / (2 * math.pi * gamma)
                                    / ((point_us + dwell) * 1e-6))))
        half = max(Constants.ADAPTIVE_FINE_GAMMA * gamma, Constants.ADAPTIVE_FINE_MIN_HZ) + extra_hz
        a = max(low + lead * step, int(round(f_res - half)))
        b = min(high, int(round(f_res + half)))
        b = a + (b - a) // step * step
        if b - a < 20 * step:
            return None
        coarse = Constants.ADAPTIVE_COARSE_STEP
        start = a - lead * step                       # the lead-in's first point
        # The window's first point waits ADAPTIVE_SETTLE_TAU decay times far from
        # the resonance before it is read: the crystal rings on from the sweep before
        settle = min(100000, int(round(Constants.ADAPTIVE_SETTLE_TAU / (2 * math.pi * gamma) * 1e6)))
        segments = []
        if start - coarse >= low:
            end = low + (start - coarse - low) // coarse * coarse
            segments.append((low, low, coarse, settle))
            if end >= low + coarse:
                segments.append((low + coarse, end, coarse, 0))
        if b + coarse <= high:
            segments.append((b + coarse, b + coarse + (high - b - coarse) // coarse * coarse, coarse, 0))
        segments += [(start, a - step, step, dwell), (a, b, step, dwell), (b, a, -step, dwell)]
        n = len(segments)
        return cls(segments, [n - 2, n - 1])

    def segment(self, i):
        a, b, s, _ = self.segments[i]
        return np.arange(a, b + (1 if s > 0 else -1), s, dtype=float)

    @property
    def freqs(self):
        """Every point, in the order swept."""
        return np.concatenate([self.segment(i) for i in range(len(self.segments))])

    def indices(self, i):
        start = sum(len(self.segment(j)) for j in range(i))
        return np.arange(start, start + len(self.segment(i)))

    def seconds(self, point_us=Constants.ADAPTIVE_POINT_US):
        """How long the firmware takes to sweep it."""
        return sum(len(self.segment(i)) * (point_us + seg[3])
                   for i, seg in enumerate(self.segments)) * 1e-6

    def command(self):
        """The firmware command, with its newline."""
        fields = [v for seg in self.segments for v in seg]
        return "Z" + ";".join(str(int(v)) for v in fields) + "\n"


###############################################################################
# One pass, one sweep
###############################################################################
# One pass of the fine zone through the chain: the 1 Hz grid and G, B on it (S),
# the seed (maximum of G, half-height width) and its band, what it publishes,
# the fit, the phase offset and fold, G's baseline (S), and whether the band left
# the zone
Pass = namedtuple("Pass", "fine g b f_seed gamma_seed band published fit offset fold g_base lost")

# What one adaptive sweep reads: the published pair (means of the passes), the
# passes, whether the resonance left the fine zone, and what the plots draw
# (see AdaptiveSweep._display)
Reading = namedtuple("Reading", "published passes lost display")


class AdaptiveSweep(object):
    """Per measurement: where each overtone's next sweep looks (the last resonance
    whose band was whole, and its speed over the last two adaptive sweeps), and
    the analysis of its sweeps through the process's chain. `proc` is the
    MultiscanProcess (its methods are the chain)."""

    def __init__(self, proc, clock=time.monotonic):
        self.proc = proc
        self.clock = clock
        self._last = {}       # overtone -> (f_res, Gamma) of the last good sweep
        self._track = {}      # overtone -> [(time, f_res)] of the last two good adaptive sweeps

    # --- where the next sweep looks ------------------------------------------
    def remember(self, overtone, published, band, track=True):
        """Where the next adaptive sweep looks: the last resonance whose band was
        whole. Its speed only from adaptive sweeps (`track`): the full sweep reads
        f higher (its lag)."""
        if (band.f_left is not None and band.f_right is not None and published.gamma > 0
                and np.isfinite(published.fres)):
            self._last[overtone] = (float(published.fres), float(published.gamma))
            points = self._track.setdefault(overtone, [])
            if not track:
                del points[:]
                return
            points.append((self.clock(), float(published.fres)))
            del points[:-2]
        else:
            self.forget(overtone)

    def located(self, overtone):
        """The last sweep of this overtone placed its resonance (its band was whole)."""
        return overtone in self._last

    def forget(self, overtone):
        """The next sweep of this overtone is a full one."""
        self._last.pop(overtone, None)
        self._track.pop(overtone, None)

    def plan(self, overtone, low, high, point_us=Constants.ADAPTIVE_POINT_US):
        """The adaptive sweep of the window [low, high], or None for a full one (no
        resonance known yet)."""
        if overtone not in self._last:
            return None
        f, gamma = self._last[overtone]
        extra = 0.0
        track = self._track.get(overtone, [])
        if len(track) == 2:
            (t1, f1), (t2, f2) = track
            if 0 < t2 - t1 < 60:
                move = (f2 - f1) / (t2 - t1) * (self.clock() - t2)    # where it will be by now
                if abs(move) < Constants.ADAPTIVE_PREDICT_MAX_HZ:
                    f += move
                    extra = Constants.ADAPTIVE_PREDICT_MARGIN * abs(move)
        return SweepPlan.around(f, gamma, int(low), int(high), point_us, extra_hz=extra)

    def relocate(self, overtone, plan, bit_mag, bit_phase, low, high,
                 point_us=Constants.ADAPTIVE_POINT_US):
        """After a lost sweep: where the resonance went and how wide it is now, from
        all its points (the coarse ones span the window): the peak of G, and the
        half width at half height over every point (twice the last Gamma when a
        side is missing: a line that widened past the coarse points). A new plan
        around it, its fine zone wider by a coarse step; None when the peak is at
        the window's edge or no Gamma is known (sweep it all)."""
        if overtone not in self._last:
            return None
        proc = self.proc
        freq = plan.freqs
        order = np.argsort(freq, kind="stable")
        f = freq[order]
        vm, vp = volts(bit_mag, bit_phase)
        vm = vm[order]
        reading = proc._phase_raw_V_phase(vp)[order]
        offset, _ = proc._phase_offset_fold(reading)
        g = proc._G_exact(*proc._RX_exact(vm, reading + offset))
        i = int(np.nanargmax(g))
        f_peak = float(f[i])
        coarse = Constants.ADAPTIVE_COARSE_STEP
        if f_peak - f[0] < coarse or f[-1] - f_peak < coarse:
            return None
        _, gamma = self._last[overtone]
        left = f <= f[0] + Constants.ADAPTIVE_G_BASE_HZ
        band = proc._half_bandwidth_G_exact(g, f, float(np.mean(g[left])) if left.any() else None)
        if band.f_left is not None and band.f_right is not None and band.bandwidth > 0:
            gamma = max(gamma, float(band.bandwidth))    # a line that widened (a liquid, a soft film)
        else:
            gamma *= 2
        # The speed stays: the relocated sweep adds its point to it, and the next
        # plan predicts again (dropping it here lost the resonance every cycle)
        line = ("Adaptive sweep (overtone %d): the resonance left the fine zone, found again at "
                "%.0f Hz, Gamma about %.0f Hz" % (overtone, f_peak, gamma))
        proc._message(line)
        return SweepPlan.around(f_peak, gamma, int(low), int(high), point_us, extra_hz=coarse)

    # --- the analysis ----------------------------------------------------------
    def locate(self, overtone, freq, bit_mag, bit_phase, sg_window, points):
        """The full sweep: elaborate_multi's chain (SG, spline onto 1 Hz, fold, exact
        G, maximum, half height, fit), for where the adaptive sweep goes. Its
        reading is not published: it lags. So its fold decision is not latched
        (the adaptive passes latch their own) and it does not count in the fit's
        statistics (openQCM Lab, review of PR #2). Returns the published pair."""
        proc = self.proc
        vm, vp = volts(bit_mag, bit_phase)
        freq = np.asarray(freq, dtype=float)
        index = range(len(freq))
        fine = np.linspace(freq[0], freq[-1], points)
        xs = np.linspace(0, len(freq) - 1, points)
        vmag_fit = UnivariateSpline(index, savitzky_golay(vm, window_size=sg_window, order=Constants.SG_order),
                                    s=Constants.SPLINE_FACTOR_G)(xs)
        vphs_fit = UnivariateSpline(index, savitzky_golay(vp, window_size=sg_window, order=Constants.SG_order),
                                    s=Constants.SPLINE_FACTOR_G)(xs)
        folded = proc._phase_raw_V_phase(vphs_fit)
        p_min = float(np.nanmin(folded))
        offset, fold = proc._phase_offset_fold(folded)
        if Constants.PHASE_FOLD_BY_PEAK_DEPTH:
            decided, _ = proc._phase_fold_decision(fine, vmag_fit, folded)
            if decided is not None:
                fold = decided
                offset = -p_min if fold else 0.0
        g = proc._G_exact(*proc._RX_exact(vmag_fit, folded + offset))
        _, f_seed, band = proc.parameters_finder_impedance_exact(fine, g)
        published, _ = lorentzian.publish(fine, g, float(f_seed), float(abs(band.bandwidth)),
                                          estimator=proc.estimator_mode())
        self.remember(overtone, published, band, track=False)
        return published

    def _pass(self, overtone, plan, idx, coarse, vm, vp, key):
        """The chain on one pass of the fine zone (its points `idx`): SG over
        SG_WINDOW_HZ, the spline onto 1 Hz with the full sweep's smoothing per
        point, fold (latched under `key`), exact G and B, maximum, half height,
        fit. The coarse points give the baselines."""
        proc = self.proc
        freq = plan.freqs
        idx = idx[np.argsort(freq[idx])]
        ff = freq[idx]
        n = len(ff)
        step = abs(plan.segments[plan.fine[0]][2])
        sg = max(Constants.SG_order + 2, int(round(SG_WINDOW_HZ / step))) | 1
        sg = min(sg, n - 1 if n % 2 == 0 else n)
        points = int(ff[-1] - ff[0]) + 1
        fine = np.linspace(ff[0], ff[-1], points)
        xs = np.linspace(0, n - 1, points)
        s = Constants.SPLINE_FACTOR_G * n / FULL_POINTS     # the full sweep's residual budget per point
        vmag_fit = UnivariateSpline(range(n), savitzky_golay(vm[idx], sg, Constants.SG_order), s=s)(xs)
        vphs_fit = UnivariateSpline(range(n), savitzky_golay(vp[idx], sg, Constants.SG_order), s=s)(xs)
        lo, hi = freq.min(), freq.max()
        reading = proc._phase_raw_V_phase(vp)
        folded = proc._phase_raw_V_phase(vphs_fit)
        p_min = float(np.nanmin(folded))
        offset, fold = proc._phase_offset_fold(folded)
        if Constants.PHASE_FOLD_BY_PEAK_DEPTH:
            # the phase baseline from the window's ends: the fine zone has none
            ends = coarse & ((freq <= lo + Constants.ADAPTIVE_PHASE_BASE_HZ)
                             | (freq >= hi - Constants.ADAPTIVE_PHASE_BASE_HZ))
            base = float(np.median(reading[ends])) if ends.sum() >= 4 else None
            decided, _ = proc._phase_fold_decision(fine, vmag_fit, folded, base)
            if decided is not None:
                fold = proc._fold_latched(key, decided)
                offset = -p_min if fold else 0.0
        corr = folded + offset
        g = proc._G_exact(*proc._RX_exact(vmag_fit, corr))
        # G's baseline from the coarse points at the window's low end, where the
        # full sweep takes it (the mean of its first 100 samples)
        g_raw = proc._G_exact(*proc._RX_exact(vm, reading + offset))
        left = coarse & (freq <= lo + Constants.ADAPTIVE_G_BASE_HZ)
        g_base = float(np.mean(g_raw[left])) if left.any() else None
        _, f_seed, band = proc.parameters_finder_impedance_exact(fine, g, g_base)
        gamma_seed = abs(band.bandwidth)
        published, fit = lorentzian.publish(fine, g, float(f_seed), float(gamma_seed),
                                            estimator=proc.estimator_mode())
        # B needs the sign of the phase, from undoing the fold (as elaborate_multi)
        signed = np.array(corr, dtype=float, copy=True)
        if fold:
            signed[int(np.nanargmin(np.abs(corr))):] *= -1.0
        b = proc._B_exact(*proc._RX_exact(vmag_fit, signed))
        margin = Constants.ADAPTIVE_EDGE_GAMMA * max(gamma_seed, 1.0)
        lost = (band.f_left is None or band.f_right is None
                or f_seed - fine[0] < margin or fine[-1] - f_seed < margin)
        if g_base is None:
            g_base = float(np.average(g[:min(100, len(g))]))
        return Pass(fine, g, b, float(f_seed), float(gamma_seed), band, published, fit,
                    float(offset), bool(fold), g_base, lost)

    def process(self, overtone, plan, bit_mag, bit_phase):
        """One adaptive sweep, its points in the order swept: each pass of the fine
        zone through the chain, f and Gamma the means over the passes. `lost` when
        a band is not whole inside the fine zone: the caller relocates it."""
        proc = self.proc
        freq = plan.freqs
        vm, vp = volts(bit_mag, bit_phase)
        fine_mask = np.zeros(len(freq), dtype=bool)
        for i in plan.fine:
            fine_mask[plan.indices(i)] = True
        # The baselines from the coarse points only: not the fine zone, nor the
        # lead-in just below it (openQCM Lab, review of PR #2)
        coarse = ~fine_mask
        coarse[plan.indices(plan.fine[0] - 1)] = False
        passes = [self._pass(overtone, plan, plan.indices(i), coarse, vm, vp, (overtone, k))
                  for k, i in enumerate(plan.fine)]
        lost = any(p.lost for p in passes)
        f_res = float(np.mean([p.published.fres for p in passes]))
        gamma = float(np.mean([p.published.gamma for p in passes]))
        sources = set(p.published.source for p in passes)
        source = lorentzian.SOURCE_FIT if sources == {lorentzian.SOURCE_FIT} else lorentzian.SOURCE_FALLBACK
        reason = "; ".join(sorted(set(p.published.reason for p in passes)))
        mean = lorentzian.Published(f_res, gamma, source, reason)
        if not lost:            # lost: the caller relocates it, or forgets it
            for p in passes:
                proc._witness_resonance(overtone, p.published, p.fit, p.f_seed, p.gamma_seed)
            self.remember(overtone, mean, passes[0].band)
        return Reading(mean, passes, lost, self._display(plan, passes, mean, bit_mag, bit_phase))

    @staticmethod
    def _display(plan, passes, mean, bit_mag, bit_phase):
        """What the plots draw. The two passes as one curve: what is left of the
        lag shifts the up pass by +lag and the down pass by -lag (lag = half the
        distance between their resonances), so drawn as measured, interleaved in
        frequency, they zigzag on the flanks. Each is moved back by its lag and the
        two are averaged. The measurement does not use this.

        Returns a dict: freq, mag (dB), phase (deg) of the whole sweep in frequency
        order (the coarse points as measured, the fine zone aligned); the 1 Hz grid
        of the fine zone with G and B on it (S, aligned); the band moved back by the
        lag; the fit with the mean f_res and Gamma; G's baseline (S); the lag (Hz)."""
        freq = plan.freqs
        mag, phase = magnitude_phase(bit_mag, bit_phase)
        if len(passes) != 2:
            order = np.argsort(freq, kind="stable")
            p = passes[0]
            return dict(freq=freq[order], mag=mag[order], phase=phase[order], fine=p.fine, g=p.g, b=p.b,
                        band=p.band, fit=p.fit, g_base=p.g_base, lag=0.0)
        pu, pd = passes
        lag = ((pu.published.fres - pd.published.fres) / 2
               if np.isfinite(pu.published.fres) and np.isfinite(pd.published.fres) else 0.0)
        up, down = (plan.indices(i) for i in plan.fine)
        up, down = up[np.argsort(freq[up])], down[np.argsort(freq[down])]
        x = freq[up]

        def aligned(y):
            return (np.interp(x + lag, x, y[up]) + np.interp(x - lag, freq[down], y[down])) / 2

        others = np.ones(len(freq), dtype=bool)
        others[up] = others[down] = False
        f_all = np.concatenate([freq[others], x])
        order = np.argsort(f_all, kind="stable")
        fu = pu.fine
        g = (np.interp(fu + lag, fu, pu.g) + np.interp(fu - lag, pd.fine, pd.g)) / 2
        b = (np.interp(fu + lag, fu, pu.b) + np.interp(fu - lag, pd.fine, pd.b)) / 2
        fit = None
        if pu.fit is not None and pd.fit is not None:
            fit = pu.fit._replace(fres=mean.fres, gamma=mean.gamma,
                                  phi_deg=(pu.fit.phi_deg + pd.fit.phi_deg) / 2)
        band = pu.band._replace(
            bandwidth=mean.gamma,
            f_left=None if pu.band.f_left is None else pu.band.f_left - lag,
            f_right=None if pu.band.f_right is None else pu.band.f_right - lag)
        return dict(freq=f_all[order], mag=np.concatenate([mag[others], aligned(mag)])[order],
                    phase=np.concatenate([phase[others], aligned(phase)])[order],
                    fine=fu, g=g, b=b, band=band, fit=fit, g_base=pu.g_base, lag=float(lag))
