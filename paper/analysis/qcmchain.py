# -*- coding: utf-8 -*-
"""
qcmchain.py — independent re-implementation of the openQCM NEXT impedance
measurement chain and of the resonance estimators compared in the paper.

Written from the equations (docs/impedance-analysis/ALGORITHM.md, the AD8302
data sheet and the schematic constants), NOT by importing the instrument code,
so that it can serve as a cross-check of the implementation. The only piece
shared by design with the instrument is the smoothing (Savitzky–Golay 51/3 and
the UnivariateSpline with s = 0.001 on the sample index), reproduced here so
that every estimator sees exactly the conductance the instrument publishes.

Conventions (kept throughout the paper):
  f_res   series resonance frequency (centre of the motional Lorentzian)
  Gamma   HALF bandwidth at half height (HWHM) of the conductance peak [Hz]
  D       dissipation factor = 2*Gamma/f_res (dimensionless; ppm = 1e-6)
  f_Gmax  frequency of the maximum of G (the "argmax" estimator)
  Delta   = f_res - f   (Johannsmann's sign)
  phi     rotation angle of the phase-shifted Lorentzian, model
          Y(f) = A e^{j phi} / (Gamma - j Delta) + offset, so that
          G = A (Gamma cos phi - Delta sin phi)/(Delta^2 + Gamma^2) + G_off.
"""
import math
import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import least_squares

# ----------------------------------------------------------------- constants
R17 = 52.3                 # ohm, series resistor of the divider (schematic)
V_CP = 0.9                 # V, AD8302 centre point of both outputs
MAG_SLOPE = 0.030          # V/dB  (600 mV/decade), AD8302 data sheet eq. 8a
DECADE = 20.0 * MAG_SLOPE  # 0.6 V per decade of |V_INPA/V_INPB|
PHS_SLOPE = 0.010          # V/deg, AD8302 data sheet eq. 9
V_PHS_ZERO = V_CP + 90.0 * PHS_SLOPE   # 1.8 V at |dphi| = 0
R11_ATT, R19_ATT = 47.0, 4.99          # ohm, INPB attenuator
K_ATT = (R11_ATT + R19_ATT) / R19_ATT  # 10.418838 (20.3564 dB)
V_ATT_OFFSET = 20.0 * math.log10(K_ATT) * MAG_SLOPE   # 0.610692 V
ADC_LSB = 3.3 / 4096.0
GAIN_MAG, GAIN_PHS = 2.0, 1.5          # op-amp gains ahead of the ADC
AVERAGE_SAMPLE = 500                   # firmware readings per frequency point

# smoothing (same as the instrument)
SG_WINDOW, SG_ORDER, SPLINE_S = 51, 3, 0.001
# estimator parameters (same as the instrument)
BASELINE_SAMPLES = 100
PSL_BAND_GAMMA = 3.0
FOLD_DEPTH_MIN, FOLD_PEAK_MAX_GAMMA = 0.88, 5.0
# the instrument's acceptance gate for the PSL fit (core/constants.py)
PSL_RMS_MAX, PSL_PHI_MAX_DEG, PSL_GAMMA_RATIO = 0.05, 60.0, (0.3, 3.0)

OVERTONES = (1, 3, 5, 7, 9)


# ------------------------------------------------------- firmware correction
def undo_firmware_carry(V_MAG, V_PHS, first_point="steady"):
    """Undo the 0.1.5a–c sweep-average carry-over: printed v_i = m_i + v_{i-1}/500.

    The recursion is exact on the ADC counts, and both stored voltages are
    affine in the counts, so it is undone on the counts and converted back.
    The first point carried 1/500 of the previous sweep's last point (another
    overtone), which is unknown: 'steady' assumes v_0 = m_0*500/499.
    """
    cm = (np.asarray(V_MAG, float) + V_ATT_OFFSET) / (ADC_LSB / GAIN_MAG)
    cp = np.asarray(V_PHS, float) / (ADC_LSB / GAIN_PHS)
    def fix(v):
        m = v.copy()
        m[1:] = v[1:] - v[:-1] / AVERAGE_SAMPLE
        m[0] = v[0] * (1.0 - 1.0 / AVERAGE_SAMPLE) if first_point == "steady" else v[0]
        return m
    return fix(cm) * ADC_LSB / GAIN_MAG - V_ATT_OFFSET, fix(cp) * ADC_LSB / GAIN_PHS


# ---------------------------------------------------------------- smoothing
def savitzky_golay(y, window_size=SG_WINDOW, order=SG_ORDER):
    """Savitzky–Golay with the instrument's edge padding (values mirrored about
    the end samples), so the smoothed arrays are identical to the published ones."""
    y = np.asarray(y, float)
    half = (window_size - 1) // 2
    b = np.array([[k ** i for i in range(order + 1)] for k in range(-half, half + 1)], float)
    m = np.linalg.pinv(b)[0]
    first = y[0] - np.abs(y[1:half + 1][::-1] - y[0])
    last = y[-1] + np.abs(y[-half - 1:-1][::-1] - y[-1])
    yy = np.concatenate((first, y, last))
    return np.convolve(m[::-1], yy, mode="valid")


def smooth_like_instrument(f, V, window=SG_WINDOW, order=SG_ORDER, s=SPLINE_S):
    """SG + UnivariateSpline on the sample index, resampled on the 1 Hz grid.
    window=0 returns the raw samples on their own grid (no smoothing)."""
    f = np.asarray(f, float)
    if window == 0:
        return f.copy(), np.asarray(V, float).copy()
    n_out = int(round(f[-1] - f[0])) + 1
    xr = np.arange(len(f))
    xs = np.linspace(0, len(f) - 1, n_out)
    fr = np.linspace(f[0], f[-1], n_out)
    filt = savitzky_golay(V, window, order)
    return fr, UnivariateSpline(xr, filt, s=s)(xs)


# ------------------------------------------------------- detector inversion
def phase_reading_deg(V_PHS):
    """r(f) = (1.8 V − V_PHS)/10 mV: the magnitude of the phase difference, in
    degrees, as the AD8302 reports it (before any offset correction)."""
    return (V_PHS_ZERO - np.asarray(V_PHS, float)) / PHS_SLOPE


def divider_magnitude(V_MAG):
    """M = |Z_q + R17| = R17 · 10^((V_CP − V_MAG)/0.6), V_MAG already compensated
    for the INPB attenuator (as stored in g<n>.txt)."""
    return R17 * np.power(10.0, (V_CP - np.asarray(V_MAG, float)) / DECADE)


def impedance_from_detector(V_MAG, phase_deg):
    """Exact inversion of H = R17/(Z_q + R17): Z_q + R17 = M e^{−jφ}."""
    M = divider_magnitude(V_MAG)
    phi = np.deg2rad(np.asarray(phase_deg, float))
    return M * np.cos(phi) - R17, -M * np.sin(phi)      # R_q, X_q


def admittance(R_q, X_q):
    den = np.maximum(R_q * R_q + X_q * X_q, 1e-30)
    return R_q / den, -X_q / den                          # G, B


def fold_decision(freq, V_MAG, r):
    """The instrument's rule: the phase crosses zero (a fold exists) when the
    reading's peak reaches at least 88 % of the way from its off-resonance
    baseline to 0°, and that peak sits within 5 Γ of the conductance maximum."""
    n = len(r)
    n_end = max(20, min(200, n // 8))
    base = float(np.median(np.concatenate([r[:n_end], r[-n_end:]])))
    i_pk = int(np.nanargmin(r))
    p_min = float(r[i_pk])
    info = dict(baseline=base, r_min=p_min, depth=np.nan, off_gamma=np.nan)
    if not np.isfinite(base) or base <= 1.0:
        return False, info
    depth = (base - p_min) / base
    G0, _ = admittance(*impedance_from_detector(V_MAG, r))
    est = argmax_halfheight(freq, G0)
    gam = est["gamma_hh"]
    off = abs(freq[i_pk] - est["f_max"]) / gam if gam > 0 else np.inf
    info.update(depth=depth, off_gamma=off)
    return bool(depth >= FOLD_DEPTH_MIN and off <= FOLD_PEAK_MAX_GAMMA), info


def chain(f, V_MAG, V_PHS, smoothing=True, firmware_fix=False, fold=None, delta_extra=0.0):
    """Raw dump arrays → the published conductance and susceptance.

    Returns a dict with the 1 Hz grid `f`, `G`, `B`, `M`, the corrected phase
    `phase` (deg, unsigned, offset removed), the signed phase used for B, the
    offset `delta`, the fold decision and its diagnostics.
    """
    Vm, Vp = (np.asarray(V_MAG, float), np.asarray(V_PHS, float))
    if firmware_fix:
        Vm, Vp = undo_firmware_carry(Vm, Vp)
    w = SG_WINDOW if smoothing else 0
    fr, Vm_s = smooth_like_instrument(f, Vm, w)
    _, Vp_s = smooth_like_instrument(f, Vp, w)
    r = phase_reading_deg(Vp_s)
    decided, info = fold_decision(fr, Vm_s, r)
    has_fold = decided if fold is None else bool(fold)
    delta = (-float(np.nanmin(r)) if has_fold else 0.0) + delta_extra
    phase = r + delta
    R_q, X_q = impedance_from_detector(Vm_s, phase)
    G, _ = admittance(R_q, X_q)
    signed = phase.copy()
    if has_fold:
        i_flip = int(np.nanargmin(np.abs(phase)))
        signed[i_flip:] = -signed[i_flip:]
    Rb, Xb = impedance_from_detector(Vm_s, signed)
    _, B = admittance(Rb, Xb)
    return dict(f=fr, G=G, B=B, M=divider_magnitude(Vm_s), V_MAG=Vm_s, V_PHS=Vp_s,
                reading=r, phase=phase, phase_signed=signed, R_q=R_q, X_q=X_q,
                delta=delta, fold=has_fold, fold_info=info)


# ------------------------------------------------------------- estimators
def _cross(F, G, i_lo, i_hi, level):
    g0, g1 = G[i_lo], G[i_hi]
    if g1 == g0:
        return F[i_lo]
    return F[i_lo] + (level - g0) * (F[i_hi] - F[i_lo]) / (g1 - g0)


def argmax_halfheight(freq, G, n_base=BASELINE_SAMPLES):
    """The instrument's standard estimator: the sample where G is maximum and the
    two-sided half-height half width, baseline = mean of the first n_base samples,
    crossings linearly interpolated. Also returns the midpoint of the crossings."""
    F = np.asarray(freq, float)
    g = np.asarray(G, float) - np.mean(G[:min(n_base, len(G))])
    i = int(np.nanargmax(g))
    half = g[i] / 2.0
    out = dict(f_max=float(F[i]), i_max=i, g_peak=float(g[i]), baseline=float(np.mean(G[:min(n_base, len(G))])),
               f_left=np.nan, f_right=np.nan, gamma_hh=np.nan, f_mid=np.nan, one_sided=False)
    if not (np.isfinite(half) and half > 0):
        out["gamma_hh"] = 0.0
        return out
    below = np.where(g[:i] < half)[0]
    if len(below):
        k = int(below[-1]); out["f_left"] = _cross(F, g, k, min(k + 1, i), half)
    below = np.where(g[i:] < half)[0]
    if len(below):
        k = i + int(below[0]); out["f_right"] = _cross(F, g, k, max(k - 1, i), half)
    fl, frr = out["f_left"], out["f_right"]
    if np.isfinite(fl) and np.isfinite(frr):
        out["gamma_hh"] = (frr - fl) / 2.0; out["f_mid"] = (fl + frr) / 2.0
    elif np.isfinite(fl):
        out["gamma_hh"] = F[i] - fl; out["one_sided"] = True
    elif np.isfinite(frr):
        out["gamma_hh"] = frr - F[i]; out["one_sided"] = True
    else:
        out["gamma_hh"] = 0.0
    return out


def fit_window(freq, f_seed, gamma_seed, band=PSL_BAND_GAMMA):
    return np.abs(np.asarray(freq, float) - f_seed) <= band * abs(gamma_seed)


def rotated_lorentzian(f, fres, gamma, phi_deg, gmax, g_off):
    d = fres - np.asarray(f, float)
    phi = math.radians(phi_deg)
    return gmax * gamma * (gamma * math.cos(phi) - d * math.sin(phi)) / (d * d + gamma * gamma) + g_off


def _fit_core(freq, G, mask, f_seed, gamma_seed, model, p0, max_points=None):
    """Shared normalised LM fit: x in kHz from the seed, y in mS."""
    idx = np.where(mask & np.isfinite(freq) & np.isfinite(G))[0]
    if max_points and len(idx) > max_points:
        idx = idx[::int(math.ceil(len(idx) / max_points))]
    x = (f_seed - freq[idx]) / 1e3
    y = G[idx] * 1e3
    span = float(np.ptp(y))
    if len(idx) < 8 or not np.isfinite(span) or span <= 0:
        return None
    def residual(p):
        return model(p, x) - y
    try:
        sol = least_squares(residual, p0(span, y, gamma_seed / 1e3), method="lm",
                            xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=4000)
    except Exception:
        return None
    res = residual(sol.x)
    return dict(x=sol.x, rms_rel=float(np.sqrt(np.mean(res * res)) / span), n_fit=len(idx),
                converged=bool(sol.success), residual=res / span, idx=idx, span=span)


def fit_psl(freq, G, f_seed, gamma_seed, band=PSL_BAND_GAMMA, mask=None, max_points=None):
    """Phase-shifted Lorentzian on G alone, 5 parameters (G_max, f_res, Γ, φ, G_off)."""
    freq = np.asarray(freq, float); G = np.asarray(G, float)
    if mask is None:
        mask = fit_window(freq, f_seed, gamma_seed, band)
    def model(p, x):
        gmax, dfr, gam, phi, off = p
        d = x + dfr
        return gmax * gam * (gam * np.cos(phi) - d * np.sin(phi)) / (d * d + gam * gam + 1e-18) + off
    r = _fit_core(freq, G, mask, f_seed, gamma_seed, model,
                  lambda span, y, g: [span, 0.0, g, 0.0, float(y.min())], max_points)
    if r is None:
        return dict(ok=False, fres=np.nan, gamma=np.nan, phi_deg=np.nan, gmax=np.nan, g_off=np.nan,
                    rms_rel=np.inf, n_fit=0, converged=False)
    gmax, dfr, gam, phi, off = [float(v) for v in r["x"]]
    if gmax < 0:
        gmax, phi = -gmax, phi + math.pi
    gam = abs(gam)
    phi = math.atan2(math.sin(phi), math.cos(phi))
    return dict(ok=r["converged"], fres=f_seed + dfr * 1e3, gamma=gam * 1e3, phi_deg=math.degrees(phi),
                gmax=gmax / 1e3, g_off=off / 1e3, rms_rel=r["rms_rel"], n_fit=r["n_fit"],
                converged=r["converged"], residual=r["residual"], idx=r["idx"])


def fit_symmetric(freq, G, f_seed, gamma_seed, band=PSL_BAND_GAMMA, mask=None, linear=False, max_points=None):
    """Symmetric Lorentzian G = G_max Γ²/(Δ²+Γ²) + c (+ b·Δ if linear)."""
    freq = np.asarray(freq, float); G = np.asarray(G, float)
    if mask is None:
        mask = fit_window(freq, f_seed, gamma_seed, band)
    def model(p, x):
        gmax, dfr, gam, off = p[:4]
        d = x + dfr
        y = gmax * gam * gam / (d * d + gam * gam + 1e-18) + off
        return y + p[4] * x if linear else y
    r = _fit_core(freq, G, mask, f_seed, gamma_seed, model,
                  lambda span, y, g: [span, 0.0, g, float(y.min())] + ([0.0] if linear else []), max_points)
    if r is None:
        return dict(ok=False, fres=np.nan, gamma=np.nan, rms_rel=np.inf, n_fit=0, converged=False)
    gmax, dfr, gam, off = [float(v) for v in r["x"][:4]]
    return dict(ok=r["converged"], fres=f_seed + dfr * 1e3, gamma=abs(gam) * 1e3, gmax=gmax / 1e3,
                g_off=off / 1e3, rms_rel=r["rms_rel"], n_fit=r["n_fit"], converged=r["converged"],
                residual=r["residual"], idx=r["idx"])


def psl_gate(fit, gamma_seed, f_lo, f_hi):
    """The instrument's acceptance gate. Returns (accepted, reason)."""
    if fit is None or fit["n_fit"] < 8:
        return False, "too few points"
    if not fit["converged"]:
        return False, "no convergence"
    vals = [fit["fres"], fit["gamma"], fit["phi_deg"], fit["gmax"], fit["g_off"], fit["rms_rel"]]
    if not all(np.isfinite(vals)):
        return False, "non-finite"
    if not (f_lo <= fit["fres"] <= f_hi):
        return False, "f_res outside window"
    ratio = fit["gamma"] / gamma_seed if gamma_seed > 0 else np.inf
    if not (PSL_GAMMA_RATIO[0] <= ratio <= PSL_GAMMA_RATIO[1]):
        return False, "Gamma ratio %.2f" % ratio
    if abs(fit["phi_deg"]) > PSL_PHI_MAX_DEG:
        return False, "|phi| > %.0f" % PSL_PHI_MAX_DEG
    if fit["rms_rel"] > PSL_RMS_MAX:
        return False, "rms %.1f %%" % (100 * fit["rms_rel"])
    return True, "ok"


def magnitude_estimator(freq, V_MAG, threshold_db=0.3):
    """Magnitude-only estimator in the style of the production software: the
    maximum of the divider ratio in dB and its full width `threshold_db` below the
    maximum (main uses 0.3 dB on the calibration-baseline-corrected curve; here no
    calibration polynomial is available, so the uncorrected level is used — the
    polynomial is almost flat over 18 kHz). Also the −3 dB width of |H| from the
    far baseline, for a magnitude 'bandwidth' with a physical definition."""
    F = np.asarray(freq, float)
    dB = (np.asarray(V_MAG, float) - V_CP) / MAG_SLOPE
    i = int(np.nanargmax(dB))
    out = dict(f_max=float(F[i]), peak_db=float(dB[i]))
    for name, level in (("w03", dB[i] - threshold_db), ("w3", dB[i] - 3.0)):
        bl = np.where(dB[:i] < level)[0]; br = np.where(dB[i:] < level)[0]
        fl = _cross(F, dB, int(bl[-1]), int(bl[-1]) + 1, level) if len(bl) else np.nan
        frr = _cross(F, dB, i + int(br[0]), i + int(br[0]) - 1, level) if len(br) else np.nan
        out[name] = float(frr - fl) if np.isfinite(fl) and np.isfinite(frr) else np.nan
        out[name + "_mid"] = float(0.5 * (fl + frr)) if np.isfinite(fl) and np.isfinite(frr) else np.nan
    return out


# ------------------------------------------------------------- Kanazawa–Gordon
RHO_Q, MU_Q = 2648.0, 2.947e10          # AT-cut quartz density [kg/m3] and shear modulus [Pa]
Z_Q = math.sqrt(RHO_Q * MU_Q)            # 8.84e6 kg m^-2 s^-1
# liquid properties at 25 °C (literature; see paper/notes/derivations.md for sources)
LIQUIDS = {
    "water": dict(rho=997.05, eta=0.890e-3),
    "ipa":   dict(rho=781.0,  eta=2.038e-3),
}


def kanazawa_gordon(f_fund, n, rho, eta):
    """Δf_n = −√n f_F^{3/2} √(ρη/(π ρ_q μ_q)); for a Newtonian liquid ΔΓ_n = −Δf_n.
    f_F is the FUNDAMENTAL frequency (the small-load approximation is normalised
    to f_F, which is what makes Δf_n ∝ √n)."""
    n = np.asarray(n, float)
    k = f_fund ** 1.5 * math.sqrt(rho * eta / (math.pi * RHO_Q * MU_Q))
    return -np.sqrt(n) * k


# ----------------------------------------------------------- closed forms
def argmax_bias(gamma, phi_deg):
    """f_Gmax − f_res for the rotated Lorentzian: Γ·tan(φ/2)."""
    return gamma * np.tan(np.deg2rad(phi_deg) / 2.0)


def halfheight_width_factor(phi_deg):
    """Γ_hh/Γ for the rotated Lorentzian with the half level taken from the far
    baseline G_off: √(1 + 2 tan²(φ/2))."""
    t = np.tan(np.deg2rad(phi_deg) / 2.0)
    return np.sqrt(1.0 + 2.0 * t * t)


def midpoint_bias(gamma, phi_deg):
    """f_mid − f_res for the rotated Lorentzian: 2Γ·tan(φ/2)."""
    return 2.0 * gamma * np.tan(np.deg2rad(phi_deg) / 2.0)
