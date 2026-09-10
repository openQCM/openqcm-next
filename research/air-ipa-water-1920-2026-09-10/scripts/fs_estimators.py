import sys, os, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
S = sys.argv[1]; D = os.path.join(S, "dump_2026-09-10")
spec = importlib.util.spec_from_file_location("fa", "openQCM/sweep_data/fit_admittance.py"); fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
proc = MultiscanProcess(None)
print("air, board 1920, dump 2026-09-10 16:00 -- f_s by three estimators on the same exact G")
print("%2s | %12s | %12s %+7s | %12s %+7s | %8s %8s %8s" % ("n", "argmax f_G", "midpoint", "d", "Lorentz fs", "d", "Gamma_hh", "Gamma_L", "sd_fs"))
for n in (1, 3, 5, 7, 9):
    g = np.loadtxt(os.path.join(D, "g%d.txt" % n)); freq, Vmag, Vph = g[:, 0], g[:, 1], g[:, 2]
    points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    fr = np.linspace(freq[0], freq[-1], points)
    Vmag_fit = UnivariateSpline(xr, resonance.savitzky_golay(Vmag, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    Vph_fit = UnivariateSpline(xr, resonance.savitzky_golay(Vph, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    folded = proc._phase_raw_V_phase(Vph_fit); p_min = float(np.nanmin(folded))
    decided, _ = proc._phase_fold_decision(fr, Vmag_fit, folded); offset = -p_min if decided else 0.0
    R, X = proc._RX_exact(Vmag_fit, folded + offset); G = proc._G_exact(R, X)
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth)
    f_mid = 0.5 * (band.f_left + band.f_right) if band.f_left is not None and band.f_right is not None else float("nan")
    mask = (fr > f_arg - 3 * gam) & (fr < f_arg + 3 * gam)          # the fit window's own +-3 Gamma
    r = fa.fit2_lorentzian(fr, G, mask, f_arg, gam)
    print("%2d | %12.1f | %12.1f %+7.1f | %12.1f %+7.1f | %8.1f %8.1f %8.2f" % (n, f_arg, f_mid, f_mid - f_arg, r["fs"], r["fs"] - f_arg, gam, r["gamma"], r["sd_fs"]))
