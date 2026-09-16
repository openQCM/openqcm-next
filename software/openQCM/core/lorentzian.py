# -*- coding: utf-8 -*-
"""
VER 0.1.6G — the phase-shifted Lorentzian on the conductance: the published
estimator of the resonance frequency and of the half-bandwidth (2026-09-16).

The exact conductance G(f) of the sensor is not a symmetric Lorentzian on this
instrument. Fitted with one, it leaves an S-shaped residual of 2–4 % of its range
in every sweep, and its maximum sits off the resonance by Γ·tan(φ/2): 2–47 Hz in
air, 170–700 Hz in liquid (research/air-ipa-water-1920-2026-09-11/, 2026-09-14/15).
The model that fits it to 0.2–0.5 % in liquid is the complex Lorentzian rotated
by an angle φ (Johannsmann, Sensors 2021, 21, 3490, eq. 3), of which only the
real part is used here:

    G(f) = G_max · Γ · (Γ·cos φ − Δ·sin φ) / (Δ² + Γ²) + G_off ,   Δ = f_res − f

Five parameters: G_max, f_res, Γ (HALF width at half maximum, the datalog's Γ),
φ, G_off. φ is a property of the instrument, not of the sample: −8 → −27° from
the fundamental to the 9th overtone on board 1920, the same in air and in
liquid, stable to 0.2° across sweeps. With this estimator the frequency and the
half-bandwidth shifts of water and isopropanol both land on Kanazawa–Gordon
within 8 % on overtones 3–9, where the maximum of G was 20–30 % off.

WHAT THIS MODULE IS, AND IS NOT
  * One implementation, called by the acquisition process
    (processors/Multiscan.py), by the live fit window through the values the
    process ships, by the tests and by the research scripts. Nothing here
    touches Qt, files or process state: given the same arrays it returns the
    same numbers.
  * It does NOT decide alone what is published. `publish()` runs the fit, puts it
    through the gate `accept()`, and returns either the fit or the FALLBACK — the
    sample where G is maximum with the two-sided half-height width, exactly as
    the process computed them before this module existed. Every rejection
    carries its reason, and the process counts and logs them: a fallback that
    fires in silence would hide a broken fit behind a plausible number.

⚠️ THE GATE HAS PARAMETERS (Constants.PSL_*). They were set from the 45 sweeps
of 2026-09-11 at about ten times the measured values, so they catch a broken
sweep and not a marginal one. They are parameters, not facts of nature: whoever
changes the front end, the sweep window or the smoothing must look at them
again. Their values and their function are documented next to them in
core/constants.py and in docs/impedance-analysis/ALGORITHM.md.

Units at the interface are SI: frequencies in Hz, conductances in S. Inside the
solver they are kHz around the seed and mS, otherwise the Jacobian columns
differ by twenty orders of magnitude and Levenberg–Marquardt does not move.
"""

from collections import namedtuple
import math
import time

import numpy as np
from scipy.optimize import least_squares

from openQCM.core.constants import Constants


# The fit. `gmax` and `g_off` are in the units G was given in (S from the
# process); `fres` and `gamma` in Hz; `phi_deg` with the rotation's own sign
# convention (negative on board 1920). `rms_rel` is the rms of the residual over
# the range of G on the fit window. `converged` is the solver's word; whether
# the result is USED is `accept()`'s.
PSLFit = namedtuple("PSLFit", "fres gamma phi_deg gmax g_off rms_rel n_fit "
                              "converged cost_ms")

# What the process publishes: the pair, where it came from and why.
Published = namedtuple("Published", "fres gamma source reason")

SOURCE_FIT = "fit"             # the phase-shifted Lorentzian passed the gate
SOURCE_FALLBACK = "fallback"   # maximum of G and half-height width

_FAILED = PSLFit(float("nan"), float("nan"), float("nan"), float("nan"),
                 float("nan"), float("inf"), 0, False, 0.0)


def rotated_lorentzian(freq, fres, gamma, phi_deg, gmax, g_off):
    """The model, in the units of `gmax` and `g_off`. This is what the live fit
    window draws from the parameters the process shipped — the window fits
    nothing."""
    f = np.asarray(freq, dtype=float)
    d = fres - f
    phi = math.radians(phi_deg)
    den = d * d + gamma * gamma
    return gmax * gamma * (gamma * math.cos(phi) - d * math.sin(phi)) / den + g_off


def fit_window(freq, f_seed, gamma_seed, band=None):
    """Boolean mask of the samples within ±band·gamma_seed of the seed."""
    band = Constants.PSL_BAND_GAMMA if band is None else band
    f = np.asarray(freq, dtype=float)
    return np.abs(f - f_seed) <= band * abs(gamma_seed)


def fit_phase_shifted_lorentzian(freq, G, f_seed, gamma_seed, band=None,
                                 max_points=None, mask=None):
    """Least-squares fit of the model to G alone.

    `f_seed` and `gamma_seed` are the maximum of G and the half-height width the
    process already has; they define the window (±band·gamma_seed, or `mask`
    when given) and start the solver. The window is decimated uniformly to at
    most `max_points` samples (Constants.PSL_MAX_POINTS; None = all): measured
    on real sweeps, 300 points give the same f_res, Γ and φ as the full 1 Hz grid
    to the hertz at a fifth of the cost.

    Returns a PSLFit; never raises on bad data — a failed fit comes back with
    converged=False and NaNs, and `accept()` rejects it with a reason.
    """
    t0 = time.perf_counter()
    f = np.asarray(freq, dtype=float)
    g = np.asarray(G, dtype=float)
    if f.shape != g.shape or f.ndim != 1 or not np.isfinite(f_seed) \
            or not np.isfinite(gamma_seed) or gamma_seed <= 0:
        return _FAILED
    sel = (fit_window(f, f_seed, gamma_seed, band) if mask is None
           else np.asarray(mask, dtype=bool))
    sel &= np.isfinite(f) & np.isfinite(g)
    idx = np.where(sel)[0]
    if max_points is None:
        max_points = Constants.PSL_MAX_POINTS
    if max_points and len(idx) > max_points:
        step = int(math.ceil(len(idx) / float(max_points)))
        idx = idx[::step]
    n = len(idx)
    if n < 8:
        return _FAILED._replace(n_fit=n)

    # normalised problem: kHz from the seed, mS
    x = (f_seed - f[idx]) / 1e3
    y = g[idx] * 1e3
    span = float(np.ptp(y))
    if not np.isfinite(span) or span <= 0:
        return _FAILED._replace(n_fit=n)

    def residual(p):
        gmax, dfr, gam, phi, off = p
        d = x + dfr
        den = d * d + gam * gam + 1e-18
        return gmax * gam * (gam * np.cos(phi) - d * np.sin(phi)) / den + off - y

    p0 = [span, 0.0, gamma_seed / 1e3, 0.0, float(y.min())]
    try:
        sol = least_squares(residual, p0, method="lm", xtol=1e-12, ftol=1e-12,
                            gtol=1e-12, max_nfev=4000)
    except Exception:
        return _FAILED._replace(n_fit=n)
    gmax, dfr, gam, phi, off = [float(v) for v in sol.x]
    # the model is invariant under (gmax, phi) -> (-gmax, phi + pi) and under the
    # sign of Gamma: report the representative with gmax > 0, Gamma > 0 and phi
    # in (-pi, pi]
    if gmax < 0:
        gmax, phi = -gmax, phi + math.pi
    gam = abs(gam)
    phi = math.atan2(math.sin(phi), math.cos(phi))
    res = residual(sol.x)
    rms_rel = float(np.sqrt(np.mean(res * res)) / span)
    cost_ms = 1e3 * (time.perf_counter() - t0)
    return PSLFit(fres=f_seed + dfr * 1e3, gamma=gam * 1e3,
                  phi_deg=math.degrees(phi), gmax=gmax / 1e3, g_off=off / 1e3,
                  rms_rel=rms_rel, n_fit=n, converged=bool(sol.success),
                  cost_ms=cost_ms)


def accept(fit, f_seed, gamma_seed, f_lo, f_hi, rms_max=None, phi_max_deg=None,
           gamma_ratio=None):
    """The fallback gate. Returns (ok, reason); `reason` is "ok" when accepted.

    ⚠️ The limits are Constants.PSL_RMS_MAX, PSL_PHI_MAX_DEG and PSL_GAMMA_RATIO
    unless overridden: parameters of the published measurement, kept in view.
    """
    rms_max = Constants.PSL_RMS_MAX if rms_max is None else rms_max
    phi_max_deg = Constants.PSL_PHI_MAX_DEG if phi_max_deg is None else phi_max_deg
    lo, hi = Constants.PSL_GAMMA_RATIO if gamma_ratio is None else gamma_ratio
    if fit is None:
        return False, "no fit"
    if fit.n_fit < 8:
        return False, "too few points in the fit window (%d)" % fit.n_fit
    if not fit.converged:
        return False, "solver did not converge"
    if not all(np.isfinite([fit.fres, fit.gamma, fit.phi_deg, fit.gmax,
                            fit.g_off, fit.rms_rel])):
        return False, "non-finite result"
    if not (f_lo <= fit.fres <= f_hi):
        return False, "f_res %.0f Hz outside the fit window" % fit.fres
    ratio = fit.gamma / gamma_seed if gamma_seed > 0 else float("inf")
    if not (lo <= ratio <= hi):
        return False, ("Gamma %.0f Hz is %.2fx the half-height width, outside %.1f-%.1f"
                       % (fit.gamma, ratio, lo, hi))
    if abs(fit.phi_deg) > phi_max_deg:
        return False, "|phi| = %.1f deg > %.0f deg" % (abs(fit.phi_deg), phi_max_deg)
    if fit.rms_rel > rms_max:
        return False, ("rms %.1f %% of range > %.0f %%"
                       % (100.0 * fit.rms_rel, 100.0 * rms_max))
    return True, "ok"


def publish(freq, G, f_seed, gamma_seed, estimator=None):
    """What the process logs for one sweep: (Published, PSLFit or None).

    estimator: Constants.IMPEDANCE_ESTIMATOR unless given — "argmax" (the
    standard) publishes the seeds untouched without running the fit;
    "lorentzian" (experimental) runs the fit and the gate.
    """
    estimator = Constants.IMPEDANCE_ESTIMATOR if estimator is None else estimator
    if estimator != "lorentzian":
        # the STANDARD estimator: the seed itself, no fit run, not a fallback
        return Published(float(f_seed), float(gamma_seed), SOURCE_FALLBACK,
                         "standard estimator (maximum of G, half-height width)"), None
    fit = fit_phase_shifted_lorentzian(freq, G, f_seed, gamma_seed)
    f = np.asarray(freq, dtype=float)
    w = fit_window(f, f_seed, gamma_seed)
    if w.any():
        f_lo, f_hi = float(f[w].min()), float(f[w].max())
    else:
        f_lo, f_hi = float("nan"), float("nan")
    ok, reason = accept(fit, f_seed, gamma_seed, f_lo, f_hi)
    if ok:
        return Published(fit.fres, fit.gamma, SOURCE_FIT, reason), fit
    return Published(float(f_seed), float(gamma_seed), SOURCE_FALLBACK, reason), fit
