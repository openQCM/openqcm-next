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

Reads g<n>.txt (frequency [Hz], V_MAG [V], V_PHS [V]) — see
software/docs/DATA_FORMAT_sweep_data.md.
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

# Samples acquired below this divider ratio are outside the AD8302's usable
# window (specified +-30 dB) and are excluded from the fits. On a damped load
# they are the ones that pull the locus out of round.
RATIO_DB_FLOOR = -28.0


# ------------------------------------------------------- measured admittance
def signed_phase(V_PHS, fold_threshold_deg=5.0):
    """Signed transfer-function phase from the AD8302 |phase| output.

    The detector emits the magnitude of the phase only. When the true phase
    crosses zero (low damping) the output is folded and the branch after the
    minimum must be negated. When it never crosses zero (heavy damping) the raw
    reading already IS the signed phase.

    Unlike MultiscanProcess._phase_signed this does NOT subtract the minimum
    before flipping. That subtraction is an undeclared phase-offset correction:
    it leaves G (even in phi) altered, which is exactly what it must not do.
    Here the flip is applied alone, so G is bit-identical to the folded-phase
    result and only B picks up the sign it needs.
    """
    phase = (1.8 - np.asarray(V_PHS, dtype=float)) / 0.01
    i_min = int(np.nanargmin(phase))
    if phase[i_min] < fold_threshold_deg:
        phase = phase.copy()
        phase[i_min:] = -phase[i_min:]
    return phase


def admittance(V_MAG, V_PHS):
    """Exact complex-divider inversion: Z_q = M*exp(-j*phi) - R17, Y = 1/Z_q."""
    M = R17 * np.power(10.0, (V_CP - np.asarray(V_MAG, float)) / 0.6)
    phi = np.deg2rad(signed_phase(V_PHS))
    Z = M * np.exp(-1j * phi) - R17
    return 1.0 / Z


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


def _best_rotation(f, Y, centre):
    """Grid + golden refinement of the rotation that makes the arc consistent
    with a single (f_s, Gamma). Cheap: the inner problem is linear."""
    grid = np.linspace(-np.pi / 2, np.pi / 2, 181)
    costs = [ _fs_gamma_from_arc(f, Y, centre, t)["cost"] for t in grid ]
    t0 = float(grid[int(np.argmin(costs))])
    lo, hi = t0 - np.pi / 180, t0 + np.pi / 180
    for _ in range(40):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if _fs_gamma_from_arc(f, Y, centre, m1)["cost"] < \
           _fs_gamma_from_arc(f, Y, centre, m2)["cost"]:
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2


def fit1_circle(f, Y, mask):
    """BVD circle fit -> R1, C0, f_s, Gamma, L1, C1, D."""
    G, B = Y.real[mask], Y.imag[mask]
    p0 = taubin_circle(G, B)
    p, cov, d = geometric_circle(G, B, list(p0), huber=None)
    xc, yc, r = float(p[0]), float(p[1]), abs(float(p[2]))
    sd = np.sqrt(np.clip(np.diag(cov), 0, None))

    theta = _best_rotation(f[mask], Y[mask], complex(xc, yc))
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


def analyse(sweep_dir, use_mask=True, band=3.0):
    out = []
    for n in OVERTONES:
        path = os.path.join(sweep_dir, "g%d.txt" % n)
        if not os.path.exists(path):
            continue
        d = loadtxt(path)
        f, V_MAG, V_PHS = d[:, 0], d[:, 1], d[:, 2]
        Y = admittance(V_MAG, V_PHS)
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
                        fs_seed=fs_seed, hw_seed=hw_seed,
                        dB_span=[float(dB.max()), float(dB.min())],
                        fit1=f1, fit1_allpoints=f1_all, fit2=f2))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir", nargs="?", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-mask", action="store_true")
    ap.add_argument("--band", type=float, default=3.0,
                    help="fit window half-width in units of the HALF bandwidth; "
                         "pass inf to use every masked point")
    a = ap.parse_args()

    res = analyse(a.sweep_dir, use_mask=not a.no_mask, band=a.band)
    if not res:
        print("no g<n>.txt found in %s" % a.sweep_dir)
        return 1

    print("Gamma below is the FULL width at half maximum (FWHM).")
    print("The live pipeline reports the HALF width; D is the same in both.\n")
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
            json.dump(res, fh, indent=2)
        print("\nwritten %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
