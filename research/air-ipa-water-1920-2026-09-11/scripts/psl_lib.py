"""Shared pieces for the phase-shifted-Lorentzian analysis: the process's chain on a g<n>.txt array, the
rotated complex Lorentzian, and its least-squares fit on G, on B or on both. Import from software/ with
PYTHONPATH=. (MultiscanProcess reads openQCM/config.txt by a relative path)."""
import os, sys, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software"))
if SW not in sys.path: sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
_spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py")); fa = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fa)
proc = MultiscanProcess(None)
N = (1, 3, 5, 7, 9); SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
RHO_Q, MU_Q = 2648.0, 2.947e10; LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}; R17 = 52.3

def smooth_channels(g, window=None, spline=True):
    """The process's smoothing: Savitzky-Golay (51/3 by default) then UnivariateSpline s = 0.001 on the sample
    index, resampled on the span + 1 grid. window=None -> Constants.SG_WINDOW_SIZE; window=0 -> no smoothing at
    all (raw samples on their own 1 Hz grid, spline skipped)."""
    freq = g[:, 0]
    if window == 0:
        return freq.copy(), g[:, 1].copy(), g[:, 2].copy()
    w = Constants.SG_WINDOW_SIZE if window is None else window
    points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points); fr = np.linspace(freq[0], freq[-1], points)
    def sm(v):
        f = resonance.savitzky_golay(v, window_size=w, order=Constants.SG_order)
        return UnivariateSpline(xr, f, s=Constants.SPLINE_FACTOR_G)(xs) if spline else np.interp(fr, freq, f)
    return fr, sm(g[:, 1]), sm(g[:, 2])

def chain(g, window=None, spline=True, delta_extra=0.0, fold=None):
    """G, B, and the fold info from one dump array, exactly as the process does it (fold decision per sweep).
    delta_extra adds a constant to the phase after the chain's own offset (a perturbation for tests);
    fold overrides the decision when not None."""
    fr, Vm, Vp = smooth_channels(g, window, spline); r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r))
    if fold is None:
        decided, _ = proc._phase_fold_decision(fr, Vm, r); fold = bool(decided) if decided is not None else False
    delta = (-rmin if fold else 0.0) + delta_extra; corr = r + delta
    R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X); sg = corr.copy()
    if fold: i = int(np.nanargmin(np.abs(corr))); sg[i:] *= -1
    Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb)
    return dict(fr=fr, G=G, B=B, fold=fold, delta=delta, Vm=Vm, Vp=Vp)

def argmax_and_halfwidth(fr, G):
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); return float(f_arg), float(abs(band.bandwidth)), band

def model(p, f, f0):
    """Rotated complex Lorentzian: Y = A e^{j phi} / (Gamma - j (fres - f)) + G_off + j B_off. p in kHz / mS units:
    [A = Gmax*Gamma, dfres (kHz from f0), Gamma (kHz), phi (rad), G_off (mS), B_off (mS)]."""
    A, dfr, gam, phi, go, bo = p; d = (f0 - f) / 1e3 + dfr; Y = A * np.exp(1j * phi) / (gam - 1j * d); return Y.real + go, Y.imag + bo

def model_lin(p, f, f0):
    """The same with a linear background on G: p[6] = slope (mS/kHz)."""
    G, B = model(p[:6], f, f0); return G + p[6] * (f - f0) / 1e3, B

def fit(fr, G, B, mask, f_arg, gam0, which="G", linear=False):
    """which: "G", "B" or "GB". Returns fres, gamma (HWHM, Hz), phi_deg (rotation sign), rms per channel (fraction
    of that channel's range on the window), sd_fres from the covariance, and the parameter vector."""
    f = fr[mask]; g = G[mask] * 1e3; b = B[mask] * 1e3; sg_, sb_ = np.ptp(g) or 1.0, np.ptp(b) or 1.0
    p0 = [float(np.ptp(g) * gam0 / 1e3), 0.0, gam0 / 1e3, 0.0, float(g.min()), float(np.median(b))] + ([0.0] if linear else [])
    mdl = model_lin if linear else model
    def res(p):
        Gm, Bm = mdl(p, f, f_arg); r = []
        if "G" in which: r.append((Gm - g) / sg_)
        if "B" in which: r.append((Bm - b) / sb_)
        return np.concatenate(r)
    sol = least_squares(res, p0, method="trf", xtol=1e-14, ftol=1e-14, max_nfev=40000); p = sol.x; Gm, Bm = mdl(p, f, f_arg)
    # covariance on the parameters the residual actually depends on (B_off is absent from a G-only fit, G_off from a
    # B-only one: their Jacobian columns are zero and the full matrix is singular)
    used = [i for i in range(len(p)) if not ((i == 5 and "B" not in which) or (i == 4 and "G" not in which))]
    n, k = len(sol.fun), len(used); s2 = float(sol.fun @ sol.fun) / max(n - k, 1); J = sol.jac[:, used]
    sd = np.full(len(p), np.nan)
    try: sd[used] = np.sqrt(np.clip(np.diag(s2 * np.linalg.pinv(J.T @ J)), 0, None))
    except np.linalg.LinAlgError: pass
    return dict(fres=f_arg + p[1] * 1e3, sd_fres=float(sd[1] * 1e3), gamma=abs(p[2]) * 1e3, sd_gamma=float(sd[2] * 1e3), phi_deg=float(np.degrees(np.arctan2(np.sin(p[3]), np.cos(p[3])))),
                rmsG=float(np.sqrt(np.mean((Gm - g) ** 2)) / sg_), rmsB=float(np.sqrt(np.mean((Bm - b) ** 2)) / sb_), p=p, n_fit=int(mask.sum()), ok=bool(sol.success))

def psl_G(fr, G, B=None, band=3.0):
    """The estimator as used: argmax + half height for the window, then the fit on G alone on +-band*Gamma."""
    f_arg, gam0, _ = argmax_and_halfwidth(fr, G); mask = np.abs(fr - f_arg) <= band * gam0
    r = fit(fr, G, B if B is not None else np.zeros_like(G), mask, f_arg, gam0, "G"); r.update(f_arg=f_arg, gam_hh=gam0); return r

def kg_shift(f0, n, liq):
    rho, eta = LIQ[liq]; return -np.sqrt(n) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
