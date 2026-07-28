#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline admittance fits for the openQCM NEXT conductance method.

Two independent estimators of the same two physical quantities, so they can be
cross-checked against each other:

  FIT 1 — Butterworth-Van Dyke circle fit on the complex admittance
      Y(f) = j*w*C0 + 1/(R1 + j*w*L1 + 1/(j*w*C1))
      The motional branch traces a circle in the complex plane; C0 only
      TRANSLATES it. So an algebraic circle fit separates C0 from the motional
      part instead of letting it contaminate f_s and Gamma, and it uses the whole
      sweep rather than the peak region alone.
      f_s and Gamma then come out of a LINEAR least squares (closed form, with a
      covariance matrix) via the circle's own geometry - see _fs_gamma_from_arc.

  FIT 2 — Levenberg-Marquardt Lorentzian on the conductance
      G(f) = Gmax / (1 + ((f^2 - f_s^2)/(f*Gamma))^2) + a + b*f
      with the linear background left free.

CONVENTION, and it differs between the two worlds - read this before comparing
numbers with the live pipeline:
  * this script reports Gamma as the FULL width at half maximum (FWHM), which is
    the convention the two formulae above are written in;
  * MultiscanProcess._half_bandwidth_G_exact returns the HALF width (HWHM).
  * D = FWHM / f_s = 2*HWHM / f_s is the same number in both. Only the symbol
    Gamma differs, by a factor 2.

Usage:
    python fit_admittance.py [sweep_dir] [--json out.json] [--no-mask]
                             [--band N] [--offset fold|circle|none]
                             [--no-plot] [--save fig.png]

Reads g<n>.txt (frequency [Hz], V_MAG [V], V_PHS [V]) — see
software/docs/DATA_FORMAT_sweep_data.md.

Besides the numbers it draws one row of three panels per overtone: the raw
detector voltages as acquired, G(f) with the FIT 2 curve on top, and the
admittance plane with the FIT 1 circle. Look at the figure before trusting a
number: a bad fit here is visible long before it is obvious in the table.
"""

import argparse
import json
import os
import sys

import numpy as np
from numpy import loadtxt
from scipy.optimize import least_squares

# ----------------------------------------------------------------- constants
R17 = 52.3            # series resistor of the measuring divider (ohm)
V_CP = 0.9            # AD8302 center point (V)
MAG_SLOPE = 0.030     # V per dB
OVERTONES = (1, 3, 5, 7, 9)

# NOTE on the /0.6 below: that is the AD8302's own decade (20 * 30 mV/dB), NOT
# the INPB attenuator. The attenuator compensation (Constants.V_MAG_DECADE_OFFSET
# = 0.61069 V) is applied by the acquisition, so V_MAG as stored in g<n>.txt is
# already at the correct absolute level. g<n>.txt written before 2026-07-28 sits
# 10.7 mV high and will read R1 up to 22 % low.

# Samples acquired below this divider ratio are outside the AD8302's usable
# window (specified +-30 dB) and are excluded from the fits. On a damped load
# they are the ones that pull the locus out of round.
RATIO_DB_FLOOR = -28.0


# ------------------------------------------------------- measured admittance
# Search range and acceptance threshold for the global phase offset. Mirrors
# Constants.PHASE_OFFSET_{MIN,MAX}_DEG / _MAX_RMS.
PHASE_OFFSET_MIN_DEG = -5.0
PHASE_OFFSET_MAX_DEG = 30.0
PHASE_OFFSET_MAX_RMS = 0.05
FOLD_THRESHOLD_DEG = 5.0


def folded_phase(V_PHS):
    """The detector reading in degrees, as it comes out: |phase| minus a global
    offset. (1.8 - V_PHS)/0.01 is (V_CP - V_PHS)/0.01 + 90."""
    return (1.8 - np.asarray(V_PHS, dtype=float)) / 0.01


def RX(V_MAG, phase_deg):
    """Exact complex-divider inversion: Z_q = M*exp(-j*phi) - R17."""
    M = R17 * np.power(10.0, (V_CP - np.asarray(V_MAG, float)) / 0.6)
    Z = M * np.exp(-1j * np.deg2rad(np.asarray(phase_deg, float))) - R17
    return Z.real, Z.imag


def _Y(R, X):
    d = R * R + X * X
    return (R - 1j * X) / np.maximum(d, 1e-30)


def phase_offset_deg(f, V_MAG, ph_folded):
    """SUPERSEDED by fold_offset_deg. Kept for `--offset circle` and for the
    record, because how it fails is instructive.

    delta fitted by minimising the out-of-roundness of the locus. The flaw is
    that the objective is computed on the point CLOUD and the sign flip happens
    INSIDE it, so the search can buy roundness by pushing delta until the flip
    lands on the antipode of the circle - which it did, returning delta up to
    12 deg beyond -min(r). The cloud came out rounder (1.4 % of the radius
    against 4.5 %) while B jumped by up to 77 % of its range at the flip point:
    a round set of points that is not a continuous trajectory. And delta is not
    free to begin with - a fold measures it exactly (see fold_offset_deg).

    The detector reads r(f) = |phi_true(f)| - delta, with delta the board+cable+
    detector phase (7...17 deg on this instrument). Note this is NOT a rotation
    of the admittance locus, so the rotation theta that _fs_gamma_from_arc fits
    cannot absorb it: the error rotates (Z_q + R17) about -R17, which in the
    admittance plane is a radial distortion near resonance - the spur that used
    to stick out of the circle at f_r.
    """
    R0, X0 = RX(V_MAG, ph_folded)
    G0 = _Y(R0, X0).real
    i0 = int(np.nanargmax(G0 - np.average(G0[:min(100, len(G0))])))
    _, hw = _seed(f, G0, np.ones_like(f, bool))
    band = np.abs(f - f[i0]) <= max(3.0 * hw, 60.0)
    if band.sum() < 40:
        return 0.0, np.nan
    idx = np.where(band)[0]
    idx = idx[::max(1, len(idx) // 150)]
    f_b, Vm_b, ph_b = f[idx], V_MAG[idx], ph_folded[idx]

    def residual(delta):
        ps = _flip(ph_b + delta, always=True)
        Y = _Y(*RX(Vm_b, ps)) * 1e3
        try:
            xc, yc, r = taubin_circle(Y.real, Y.imag)
        except RuntimeError:
            return np.inf
        if not np.isfinite(r) or r <= 0:
            return np.inf
        d = np.hypot(Y.real - xc, Y.imag - yc) - r
        return float(np.sqrt(np.mean(d * d)) / r)

    grid = np.arange(PHASE_OFFSET_MIN_DEG, PHASE_OFFSET_MAX_DEG + 0.01, 1.0)
    costs = [residual(d) for d in grid]
    k = int(np.nanargmin(costs))
    if not np.isfinite(costs[k]):
        return 0.0, np.nan
    fine = np.arange(grid[k] - 1.0, grid[k] + 1.001, 0.1)
    cf = [residual(d) for d in fine]
    kf = int(np.nanargmin(cf))
    best = float(fine[kf])
    at_bound = (best <= PHASE_OFFSET_MIN_DEG + 0.5 or
                best >= PHASE_OFFSET_MAX_DEG - 0.5)
    if not np.isfinite(cf[kf]) or at_bound or cf[kf] > PHASE_OFFSET_MAX_RMS:
        return 0.0, float(cf[kf]) if np.isfinite(cf[kf]) else np.nan
    return best, float(cf[kf])


def fold_offset_deg(ph_folded):
    """delta from the fold, which is where it is MEASURED rather than fitted.

    The reading is r(f) = |phi(f) + phi_b| - delta. Where the argument crosses
    zero, r reaches its minimum and equals -delta. So a fold determines delta
    exactly; there is no freedom left for a fit. min(r) < 0 on this instrument -
    that is the signature of the offset, not an impossible measurement - but delta
    of either sign is legitimate: it is whatever brings the vertex of the V to zero.

    Returns (delta, has_fold). No fold (min(r) at or above the threshold) means a
    damped load whose phase never crosses zero: the reading already IS the signed
    phase, so no offset and no flip.
    """
    ph = np.asarray(ph_folded, dtype=float)
    p_min = float(np.nanmin(ph))
    if not np.isfinite(p_min) or p_min >= FOLD_THRESHOLD_DEG:
        return 0.0, False
    return -p_min, True


def _flip(phase_deg, always=True):
    """Undo the fold: negate the branch past the minimum of |phase|.

    Call it ONLY where a fold exists. On a damped load the phase never crosses
    zero and flipping invents a sign change: measured on the 2026-07-28 water
    run, B jumps by up to 80 % of its whole range at the flip point and the locus
    breaks into two disconnected arcs.

    `always=False` skips the flip unless the corrected phase actually reaches
    zero. It exists for `--offset circle`, where delta is fitted and can leave
    the corrected minimum well above zero.
    """
    p = np.array(phase_deg, dtype=float, copy=True)
    j = int(np.nanargmin(np.abs(p)))
    if always or abs(p[j]) < FOLD_THRESHOLD_DEG:
        p[j:] = -p[j:]
    return p


def admittance(f, V_MAG, V_PHS, offset="fold"):
    """Y(f) from the raw detector voltages. Returns (Y, delta, delta_rms).

    offset:
      "fold"   delta from the fold (the default, and what the live pipeline does)
      "circle" delta fitted by minimising the out-of-roundness of the locus.
               SUPERSEDED - see phase_offset_deg for why it flatters itself.
      "none"   no correction, for comparison

    G is computed from the offset-corrected phase WITHOUT the sign flip and B
    with it: G is even in the sign of phi, so the flip cannot touch it - but it
    is not even in the OFFSET, which is why delta matters to G at all.
    """
    ph = folded_phase(V_PHS)
    if offset == "circle":
        delta, rms = phase_offset_deg(f, V_MAG, ph)
        fold = bool(delta)
    elif offset == "none":
        delta, rms, fold = 0.0, np.nan, False
    else:
        delta, fold = fold_offset_deg(ph)
        rms = np.nan
    ph_corr = ph + delta
    G = _Y(*RX(V_MAG, ph_corr)).real
    # the fold gate already decides whether to flip at all; once we do flip, we
    # flip at the minimum unconditionally
    B = (_Y(*RX(V_MAG, _flip(ph_corr, always=True))).imag
         if fold else _Y(*RX(V_MAG, ph_corr)).imag)
    return G + 1j * B, delta, rms


def ratio_dB(V_MAG):
    """Measured |V_INPA/V_INPB| in dB, for the saturation mask."""
    return (np.asarray(V_MAG, float) - V_CP) / MAG_SLOPE


# ------------------------------------------------------------ FIT 1: circle
def taubin_circle(x, y):
    """Taubin algebraic circle fit — bias-corrected, closed form."""
    mx, my = x.mean(), y.mean()
    u, v = x - mx, y - my
    z = u * u + v * v
    Muu, Mvv, Muv = (u * u).mean(), (v * v).mean(), (u * v).mean()
    Muz, Mvz = (u * z).mean(), (v * z).mean()
    Mz = Muu + Mvv
    cov = Muu * Mvv - Muv * Muv
    if abs(cov) < 1e-30:
        raise RuntimeError("degenerate circle fit")
    xc = (Muz * Mvv - Mvz * Muv) / cov / 2.0
    yc = (Mvz * Muu - Muz * Muv) / cov / 2.0
    return xc + mx, yc + my, np.sqrt(xc * xc + yc * yc + Mz)


def geometric_circle(x, y, p0, huber=None):
    """Orthogonal-distance refinement, optionally with a Huber loss so a few
    bad samples cannot drag the estimate."""
    def res(p):
        return np.hypot(x - p[0], y - p[1]) - p[2]

    kw = dict(xtol=1e-14, ftol=1e-14)
    if huber is None:
        sol = least_squares(res, p0, method="lm", **kw)
    else:
        sol = least_squares(res, p0, loss="huber", f_scale=huber, **kw)
    d = res(sol.x)
    n, k = len(x), 3
    # covariance from the Jacobian, scaled by the residual variance
    s2 = float(d @ d) / max(n - k, 1)
    try:
        cov = s2 * np.linalg.inv(sol.jac.T @ sol.jac)
    except np.linalg.LinAlgError:
        cov = np.full((3, 3), np.nan)
    return sol.x, cov, d


def _fs_gamma_from_arc(f, Y, centre, theta=0.0):
    """f_s and Gamma (FWHM) from the position of each sample ON the circle.

    For the motional branch Y_m = 1/(R1(1 + j*x)) the sample sits on the circle
    at an angle psi from the centre with

        psi = -2*arctan(x)        =>   x = -tan(psi/2)

    and x is the normalised detuning x = (f^2 - f_s^2)/(f*Gamma), Gamma = FWHM.
    Rearranged that is LINEAR in the two unknowns (Gamma, f_s^2):

        f^2 = (f * x) * Gamma + f_s^2

    so one least squares gives both in closed form, with a covariance matrix.

    theta rotates the arc before the angles are read. A residual board/cable
    phase rotates the whole locus, and on this instrument it demonstrably does
    (the fitted centres sit 15-28 % of a radius low in B in air). Leaving it at
    zero makes psi wrong by a constant and the linear fit absorbs the error into
    f_s and Gamma - which is exactly how this returned Gamma = 9 Hz and
    C0 = -27 pF before the angle was fitted.
    """
    psi = np.angle((Y - centre) * np.exp(-1j * theta))
    x = -np.tan(psi / 2.0)
    keep = np.abs(x) < 20.0
    if keep.sum() < 50:
        keep = np.ones_like(x, dtype=bool)

    # WEIGHTS, derived rather than chosen. The radial scatter of the locus turns
    # into a roughly uniform angular uncertainty sigma_psi, and
    #     x = -tan(psi/2)  =>  sigma_x = (1 + x^2)/2 * sigma_psi
    # so the error this contributes to the regression residual (which lives in
    # units of f^2) is f*Gamma*(1 + x^2)*sigma_psi/2. Hence w = 1/(1 + x^2)^2.
    # Without it the far-off-resonance samples - where the locus has collapsed
    # onto the offset point and psi is pure noise - carry enormous leverage.
    # That was what left the 9th overtone 2.5 kHz off.
    w = 1.0 / (1.0 + x * x) ** 2
    A = np.column_stack([f * x, np.ones_like(f)])[keep]
    b = (f * f)[keep]
    sw = np.sqrt(w[keep])[:, None]
    sol, *_ = np.linalg.lstsq(A * sw, b * sw[:, 0], rcond=None)
    gamma, fs2 = float(sol[0]), float(sol[1])
    resid = (b - A @ sol) * sw[:, 0]
    s2 = float(resid @ resid) / max(len(b) - 2, 1)
    try:
        cov = s2 * np.linalg.inv((A * sw).T @ (A * sw))
    except np.linalg.LinAlgError:
        cov = np.full((2, 2), np.nan)
    fs = np.sqrt(max(fs2, 0.0))
    sd_fs = np.sqrt(max(cov[1, 1], 0.0)) / (2.0 * fs) if fs > 0 else np.nan
    return dict(fs=fs, sd_fs=float(sd_fs), gamma=abs(gamma),
                sd_gamma=float(np.sqrt(max(cov[0, 0], 0.0))),
                n_used=int(keep.sum()),
                cost=float(np.sqrt(s2)))


def _best_rotation(f, Y, centre, theta0=None, span_deg=6.0):
    """Grid + golden refinement of the rotation that makes the arc consistent
    with a single (f_s, Gamma). Cheap: the inner problem is linear.

    theta0 skips the coarse grid and searches +-span_deg around it instead. The
    grid is 181 linear solves and dominates the cost, which matters only for the
    live window: there theta moves by a fraction of a degree between consecutive
    sweeps, so the previous value is a good bracket. Measured on five overtones of
    a real air sweep, decimated to 250 points: 123 ms for the full grid against
    13 ms from a cached bracket. Offline, leave it None.
    """
    if theta0 is None:
        grid = np.linspace(-np.pi / 2, np.pi / 2, 181)
        costs = [ _fs_gamma_from_arc(f, Y, centre, t)["cost"] for t in grid ]
        t0 = float(grid[int(np.argmin(costs))])
        lo, hi = t0 - np.pi / 180, t0 + np.pi / 180
        n_iter = 40
    else:
        lo, hi = theta0 - np.deg2rad(span_deg), theta0 + np.deg2rad(span_deg)
        # 14 thirds-bisections take a 12 deg bracket down to 0.007 deg, which is
        # far below the sweep-to-sweep movement of theta. 40 (the offline value,
        # on a 2 deg bracket) would be three quarters of the live fit's cost
        # spent on digits that do not exist.
        n_iter = 14
    for _ in range(n_iter):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if _fs_gamma_from_arc(f, Y, centre, m1)["cost"] < \
           _fs_gamma_from_arc(f, Y, centre, m2)["cost"]:
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2


def fit1_circle(f, Y, mask, theta0=None):
    """BVD circle fit -> R1, C0, f_s, Gamma, L1, C1, D."""
    G, B = Y.real[mask], Y.imag[mask]
    p0 = taubin_circle(G, B)
    p, cov, d = geometric_circle(G, B, list(p0), huber=None)
    xc, yc, r = float(p[0]), float(p[1]), abs(float(p[2]))
    sd = np.sqrt(np.clip(np.diag(cov), 0, None))

    theta = _best_rotation(f[mask], Y[mask], complex(xc, yc), theta0=theta0)
    arc = _fs_gamma_from_arc(f[mask], Y[mask], complex(xc, yc), theta)

    R1 = 1.0 / (2.0 * r)
    sd_R1 = sd[2] / (2.0 * r * r)
    # C0 translates the circle vertically: the offset is w*C0 at the resonance
    C0 = yc / (2.0 * np.pi * arc["fs"]) if arc["fs"] > 0 else np.nan
    # motional branch from R1 and Gamma (FWHM): Gamma = R1/(2*pi*L1)
    L1 = R1 / (2.0 * np.pi * arc["gamma"]) if arc["gamma"] > 0 else np.nan
    C1 = 1.0 / ((2 * np.pi * arc["fs"]) ** 2 * L1) if L1 and L1 > 0 else np.nan

    rms = float(np.sqrt(np.mean(d ** 2)))
    return dict(theta=float(theta), xc=xc, yc=yc, r=r, sd_xc=float(sd[0]), sd_yc=float(sd[1]),
                sd_r=float(sd[2]), R1=R1, sd_R1=float(sd_R1), C0=float(C0),
                L1=float(L1), C1=float(C1),
                fs=arc["fs"], sd_fs=arc["sd_fs"],
                gamma=arc["gamma"], sd_gamma=arc["sd_gamma"],
                D=arc["gamma"] / arc["fs"] if arc["fs"] > 0 else np.nan,
                rms=rms, rms_rel=rms / r if r else np.nan,
                n_fit=int(mask.sum()), n_arc=arc["n_used"], cov=cov.tolist())


# --------------------------------------------------------- FIT 2: Lorentzian
def fit2_lorentzian(f, G, mask, fs0, gamma0):
    """LM fit of G(f) = Gmax/(1 + ((f^2-fs^2)/(f*Gamma))^2) + a + b*f.

    Parameters are NORMALISED before being handed to the solver (frequencies in
    kHz relative to fs0, G in mS): with SI magnitudes the Jacobian columns differ
    by ~20 orders of magnitude and the solver simply does not move some of them.
    """
    fk, Gk = f[mask], G[mask]
    s_G = float(np.nanmax(Gk) - np.nanmin(Gk)) or 1.0
    df = (fk - fs0) / 1e3                      # kHz
    y = Gk / s_G

    def model(p):
        gmax, dfs, gam_k, a, b = p
        fs = fs0 + dfs * 1e3
        gam = gam_k * 1e3
        ff = fs0 + df * 1e3
        x = (ff * ff - fs * fs) / (ff * gam)
        return gmax / (1.0 + x * x) + a + b * df

    p0 = [float(np.nanmax(Gk) - np.nanmin(Gk)) / s_G, 0.0, gamma0 / 1e3,
          float(np.nanmin(Gk)) / s_G, 0.0]
    sol = least_squares(lambda p: model(p) - y, p0, method="lm",
                        xtol=1e-14, ftol=1e-14, max_nfev=20000)
    d = sol.fun
    n, k = len(y), len(p0)
    s2 = float(d @ d) / max(n - k, 1)
    try:
        cov = s2 * np.linalg.inv(sol.jac.T @ sol.jac)
    except np.linalg.LinAlgError:
        cov = np.full((k, k), np.nan)
    sd = np.sqrt(np.clip(np.diag(cov), 0, None))

    fs = fs0 + sol.x[1] * 1e3
    gamma = abs(sol.x[2]) * 1e3
    return dict(fs=float(fs), sd_fs=float(sd[1] * 1e3),
                gamma=float(gamma), sd_gamma=float(sd[2] * 1e3),
                Gmax=float(sol.x[0] * s_G), a=float(sol.x[3] * s_G),
                b=float(sol.x[4] * s_G / 1e3),
                D=float(gamma / fs),
                rms=float(np.sqrt(np.mean(d ** 2)) * s_G),
                rms_rel=float(np.sqrt(np.mean(d ** 2)) / abs(sol.x[0]))
                if sol.x[0] else np.nan,
                n_fit=int(mask.sum()), success=bool(sol.success))


# --------------------------------------------------------------------- main
def _seed(f, G, mask):
    """Robust seed for f_s and the HALF width, straight off the conductance peak.
    Only used to place the fit window; the fits themselves re-estimate both."""
    Gs = G - np.median(G[mask][:200]) if mask.sum() > 200 else G - np.median(G)
    idx = np.where(mask)[0]
    i0 = idx[int(np.nanargmax(Gs[idx]))]
    half = Gs[i0] / 2.0
    lo = idx[idx < i0]; hi = idx[idx > i0]
    fl = f[lo[Gs[lo] < half][-1]] if np.any(Gs[lo] < half) else f[idx[0]]
    fh = f[hi[Gs[hi] < half][0]] if np.any(Gs[hi] < half) else f[idx[-1]]
    return float(f[i0]), max((fh - fl) / 2.0, 1.0)


def analyse(sweep_dir, use_mask=True, band=3.0, offset="fold"):
    out = []
    for n in OVERTONES:
        path = os.path.join(sweep_dir, "g%d.txt" % n)
        if not os.path.exists(path):
            continue
        d = loadtxt(path)
        f, V_MAG, V_PHS = d[:, 0], d[:, 1], d[:, 2]
        Y, delta, delta_rms = admittance(f, V_MAG, V_PHS, offset=offset)
        dB = ratio_dB(V_MAG)
        mask = (dB > RATIO_DB_FLOOR) if use_mask else np.ones_like(f, bool)
        if mask.sum() < 100:                    # nothing usable: take it all
            mask = np.ones_like(f, bool)

        fs_seed, hw_seed = _seed(f, Y.real, mask)

        # FIT.md asks for all 18001 points. On this instrument that premise does
        # not hold: past a few half-widths the locus has collapsed onto the
        # offset point, psi is noise, and the samples are also the ones acquired
        # deepest in the AD8302's dynamic-range corner. Restricting to a band
        # around resonance is what makes the circle estimator agree with the
        # Lorentzian one. Both variants are computed so the cost is visible.
        band_mask = mask
        if band and np.isfinite(band):
            band_mask = mask & (np.abs(f - fs_seed) <= band * hw_seed)
            if band_mask.sum() < 200:
                band_mask = mask

        f1 = fit1_circle(f, Y, band_mask)
        f1_all = fit1_circle(f, Y, mask)
        f2 = fit2_lorentzian(f, Y.real, band_mask, fs_seed, 2.0 * hw_seed)
        out.append(dict(n=n, n_total=int(len(f)), n_masked=int(mask.sum()),
                        n_band=int(band_mask.sum()), band=band,
                        delta=float(delta), delta_rms=float(delta_rms),
                        fs_seed=fs_seed, hw_seed=hw_seed,
                        dB_span=[float(dB.max()), float(dB.min())],
                        fit1=f1, fit1_allpoints=f1_all, fit2=f2,
                        # the arrays, for the figure. Underscore-prefixed keys are
                        # stripped before the JSON dump - 18001 points per
                        # overtone have no business in a results file.
                        _f=f, _V_MAG=V_MAG, _V_PHS=V_PHS, _Y=Y,
                        _mask=mask, _band_mask=band_mask))
    return out


# -------------------------------------------------------------------- figures
def fit2_curve(f, r):
    """The fitted Lorentzian evaluated on an arbitrary frequency axis."""
    a2 = r["fit2"]
    x = (f * f - a2["fs"] ** 2) / (f * a2["gamma"])
    return a2["Gmax"] / (1.0 + x * x) + a2["a"] + a2["b"] * (f - r["fs_seed"])


def plot(res, sweep_dir, save=None, show=True):
    """One row of three panels per overtone: raw voltages, G(f) + FIT 2,
    admittance plane + FIT 1."""
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nrow = len(res)
    fig, axes = plt.subplots(nrow, 3, figsize=(15.5, 3.3 * nrow),
                             constrained_layout=True, squeeze=False)
    fig.suptitle("openQCM NEXT admittance fits — %s" % os.path.abspath(sweep_dir),
                 fontsize=11)
    v_floor = V_CP + RATIO_DB_FLOOR * MAG_SLOPE      # V_MAG at the mask threshold

    for row, r in enumerate(res):
        f, Y = r["_f"], r["_Y"]
        mask, band = r["_mask"], r["_band_mask"]
        a1, a2 = r["fit1"], r["fit2"]
        # kHz of detuning, not absolute MHz: at 1 Hz resolution on a 45 MHz
        # carrier an absolute axis is all offset notation and no information.
        dkHz = (f - a2["fs"]) / 1e3
        col = plt.get_cmap("viridis")(row / max(nrow - 1, 1) * 0.8)

        # --- raw detector voltages, exactly as acquired -----------------------
        ax = axes[row][0]
        ax.plot(dkHz, r["_V_MAG"], lw=0.8, color="tab:blue")
        ax.axhline(v_floor, ls=":", lw=0.8, color="tab:blue")
        ax.set_ylabel("n = %d\nV_MAG [V]" % r["n"], color="tab:blue")
        ax.tick_params(axis="y", labelcolor="tab:blue")
        ax.locator_params = None
        axp = ax.twinx()
        axp.plot(dkHz, r["_V_PHS"], lw=0.8, color="tab:red")
        axp.set_ylabel("V_PHS [V]", color="tab:red")
        axp.tick_params(axis="y", labelcolor="tab:red")
        if band.sum() and band.sum() < len(f):
            ax.axvspan(dkHz[band].min(), dkHz[band].max(), color="gold",
                       alpha=0.18, zorder=0)
        excl = ~mask
        if excl.any():
            ax.plot(dkHz[excl], r["_V_MAG"][excl], ".", ms=1.2,
                    color="0.6", zorder=1)
        ax.text(0.02, 0.04, "f_s = %.0f Hz\ndelta = %s"
                % (a2["fs"],
                   ("%+.1f deg" % r["delta"]) if r["delta"] else "rejected"),
                transform=ax.transAxes, va="bottom", ha="left", fontsize=7.5,
                family="monospace")
        if row == 0:
            ax.set_title("raw detector voltages   (blue V_MAG, red V_PHS;\n"
                         "dotted = mask floor, shaded = fit band)", fontsize=9)

        # --- conductance and the Lorentzian ----------------------------------
        ax = axes[row][1]
        ax.plot(dkHz[mask], Y.real[mask] * 1e3, lw=0.7, color="0.65",
                label="G, masked")
        ax.plot(dkHz[band], Y.real[band] * 1e3, lw=1.1, color=col,
                label="G, in band")
        ff = np.linspace(f[band].min(), f[band].max(), 800) if band.sum() > 2 else f
        ax.plot((ff - a2["fs"]) / 1e3, fit2_curve(ff, r) * 1e3, lw=1.2, ls="--",
                color="crimson", label="FIT 2")
        ax.axvline(0.0, lw=0.7, ls=":", color="crimson")
        if band.sum() > 2:
            ax.set_xlim(dkHz[band].min(), dkHz[band].max())
        ax.set_ylabel("G [mS]")
        ax.legend(fontsize=7, loc="upper right", framealpha=0.9)
        ax.text(0.02, 0.95,
                "FIT 2  f_s   = %.1f Hz\n       Gamma = %.1f Hz (FWHM)\n"
                "       D     = %.2f ppm\n       rms   = %.2f %% of Gmax"
                % (a2["fs"], a2["gamma"], a2["D"] * 1e6, 100 * a2["rms_rel"]),
                transform=ax.transAxes, va="top", ha="left", fontsize=7.5,
                family="monospace")
        if row == 0:
            ax.set_title("conductance G(f) and FIT 2", fontsize=9)

        # --- admittance plane and the circle ---------------------------------
        ax = axes[row][2]
        ax.axhline(0.0, lw=0.5, color="0.85")
        out_of_band = mask & ~band
        if out_of_band.any():
            ax.plot(Y.real[out_of_band] * 1e3, Y.imag[out_of_band] * 1e3, ".",
                    ms=1.0, color="0.75", label="masked, out of band")
        ax.plot(Y.real[band] * 1e3, Y.imag[band] * 1e3, ".", ms=1.6, color=col,
                label="in band (fitted)")
        th = np.linspace(0, 2 * np.pi, 400)
        ax.plot((a1["xc"] + a1["r"] * np.cos(th)) * 1e3,
                (a1["yc"] + a1["r"] * np.sin(th)) * 1e3,
                lw=1.1, ls="--", color="crimson", label="FIT 1 circle")
        ax.plot(a1["xc"] * 1e3, a1["yc"] * 1e3, "x", color="crimson", ms=6)
        # the arc angle psi = 0 is the fitted resonance; where it lands shows the
        # rotation theta the fit had to absorb
        ax.plot((a1["xc"] + a1["r"] * np.cos(a1["theta"])) * 1e3,
                (a1["yc"] + a1["r"] * np.sin(a1["theta"])) * 1e3,
                "o", mfc="none", mec="crimson", ms=8, label="f_s on the arc")
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_xlabel("G [mS]")
        ax.set_ylabel("B [mS]")
        ax.legend(fontsize=7, loc="lower right", framealpha=0.9)
        ax.text(0.02, 0.95,
                "FIT 1  f_s = %.1f Hz\n       Gamma = %.1f Hz\n"
                "       R1 = %.2f ohm\n       rms = %.2f %% of r\n"
                "       theta = %+.1f deg"
                % (a1["fs"], a1["gamma"], a1["R1"], 100 * a1["rms_rel"],
                   np.rad2deg(a1["theta"])),
                transform=ax.transAxes, va="top", ha="left", fontsize=7.5,
                family="monospace")
        if row == 0:
            ax.set_title("admittance plane and FIT 1", fontsize=9)

    for row in range(nrow):
        for c in range(2):
            axes[row][c].xaxis.set_major_locator(
                matplotlib.ticker.MaxNLocator(5))
    for c in range(3):
        axes[-1][c].set_xlabel(["f - f_s [kHz]", "f - f_s [kHz]", "G [mS]"][c])

    if save:
        fig.savefig(save, dpi=130)
        print("\nwritten %s" % save)
    if show:
        plt.show()
    else:
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir", nargs="?", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-mask", action="store_true")
    ap.add_argument("--band", type=float, default=3.0,
                    help="fit window half-width in units of the HALF bandwidth; "
                         "pass inf to use every masked point")
    ap.add_argument("--offset", choices=("fold", "circle", "none"), default="fold",
                    help="source of the global phase offset: 'fold' (default, "
                         "delta = -min(reading), what the pipeline does), 'circle' "
                         "(fitted on roundness - superseded), 'none'")
    ap.add_argument("--no-plot", action="store_true",
                    help="numbers only, do not open the figure")
    ap.add_argument("--save", default=None,
                    help="also write the figure to this path (png/pdf/svg)")
    a = ap.parse_args()

    res = analyse(a.sweep_dir, use_mask=not a.no_mask, band=a.band,
                  offset=a.offset)
    if not res:
        print("no g<n>.txt found in %s" % a.sweep_dir)
        return 1

    print("Gamma below is the FULL width at half maximum (FWHM).")
    print("The live pipeline reports the HALF width; D is the same in both.\n")
    if a.offset == "none":
        print("phase offset NOT corrected (--offset none)\n")
    else:
        print("global phase offset delta per overtone (--offset %s):" % a.offset)
        print("  " + "   ".join(
            "n=%d %s" % (r["n"], ("%+.1f deg" % r["delta"]) if r["delta"]
                         else ("no fold" if a.offset == "fold" else "rejected"))
            for r in res) + "\n")
    hdr = ("%2s | %-34s | %-34s | %-17s" %
           ("n", "FIT 1  BVD circle", "FIT 2  Lorentzian on G", "difference"))
    print(hdr)
    print("%2s | %14s %10s %8s | %14s %10s %8s | %8s %8s" %
          ("", "f_s [Hz]", "Gamma[Hz]", "D[ppm]", "f_s [Hz]", "Gamma[Hz]",
           "D[ppm]", "df_s[Hz]", "dGam[%]"))
    for r in res:
        a1, a2 = r["fit1"], r["fit2"]
        print("%2d | %14.2f %10.2f %8.2f | %14.2f %10.2f %8.2f | %8.2f %+7.2f%%"
              % (r["n"], a1["fs"], a1["gamma"], a1["D"] * 1e6,
                 a2["fs"], a2["gamma"], a2["D"] * 1e6,
                 a2["fs"] - a1["fs"],
                 100 * (a2["gamma"] - a1["gamma"]) / a1["gamma"]))

    print("\nFIT 1 — band-restricted vs every masked point (why the band matters)")
    print("%2s | %-26s | %-26s | %8s" % ("n", "band +-%.1f half-widths" % a.band,
                                         "all masked points", "pts"))
    for r in res:
        b, al = r["fit1"], r["fit1_allpoints"]
        print("%2d | f_s %12.2f  G %8.2f | f_s %12.2f  G %8.2f | %5d/%5d"
              % (r["n"], b["fs"], b["gamma"], al["fs"], al["gamma"],
                 r["n_band"], r["n_masked"]))

    print("\nFIT 1 detail — motional parameters and circle quality")
    print("%2s | %9s %9s %9s %9s | %9s %8s %7s" %
          ("n", "R1[ohm]", "L1[mH]", "C1[fF]", "C0[pF]", "rms[%r]",
           "pts fit", "pts arc"))
    for r in res:
        a1 = r["fit1"]
        print("%2d | %9.2f %9.2f %9.3f %9.3f | %9.3f %8d %7d" %
              (r["n"], a1["R1"], a1["L1"] * 1e3, a1["C1"] * 1e15,
               a1["C0"] * 1e12, 100 * a1["rms_rel"], a1["n_fit"], a1["n_arc"]))

    print("\nuncertainties (1 sigma, from the covariance matrices)")
    print("%2s | %-28s | %-28s" % ("n", "FIT 1", "FIT 2"))
    for r in res:
        a1, a2 = r["fit1"], r["fit2"]
        print("%2d | f_s %8.3f  Gamma %8.3f | f_s %8.3f  Gamma %8.3f" %
              (r["n"], a1["sd_fs"], a1["sd_gamma"], a2["sd_fs"], a2["sd_gamma"]))

    if a.json:
        with open(a.json, "w") as fh:
            json.dump([{k: v for k, v in r.items() if not k.startswith("_")}
                       for r in res], fh, indent=2)
        print("\nwritten %s" % a.json)

    if not a.no_plot or a.save:
        try:
            plot(res, a.sweep_dir, save=a.save, show=not a.no_plot)
        except ImportError:
            print("\nmatplotlib not available: numbers only "
                  "(pass --no-plot to silence this)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
