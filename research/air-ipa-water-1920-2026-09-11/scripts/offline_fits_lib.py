"""Shared plumbing for the HANDOFF §4 tables re-derived on the nine dumps of 2026-09-11.

The offline tool of record is software/openQCM/sweep_data/fit_admittance.py: FIT 1 (BVD circle), FIT 2
(Lorentzian on G), the two phase-offset rules (`fold`, the published one, and `circle`, the roundness fit
reverted on 2026-07-28) and the -28 dB saturation mask. This module runs its `analyse()` recipe on arrays
instead of directories, so the dumps are read straight from data/sweep_dumps_2026-09-11.npz.

Raw samples, as fit_admittance reads g<n>.txt: no Savitzky-Golay, no spline (the live chain smooths first;
scripts that need the chain say so). Gamma from fit_admittance is the FULL width (FWHM); the chain's is the
half width. Every table states which one it shows.
"""
import os, sys, importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.normpath(os.path.join(HERE, ".."))
SW = os.path.normpath(os.path.join(STUDY, "..", "..", "software"))
NPZ = os.path.join(STUDY, "data", "sweep_dumps_2026-09-11.npz")
OUT = os.path.join(STUDY, "figures", "handoff")

spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM", "sweep_data", "fit_admittance.py"))
fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
sys.path.insert(0, HERE)
from load_dumps import load  # noqa: E402

N = (1, 3, 5, 7, 9)
PHASES = (("air", ("air_0", "air_1", "air_2")),
          ("water", ("wat_0", "wat_1", "wat_2")),
          ("isopropanol", ("ipa_0", "ipa_1", "ipa_2")))


def sweeps():
    """Yield (phase, set, n, f, V_MAG, V_PHS, mtime) for all 45 sweeps."""
    d = load(NPZ)
    for phase, sets in PHASES:
        for s in sets:
            for n in N:
                g = d["%s/g%d" % (s, n)]
                yield phase, s, n, g[:, 0], g[:, 1], g[:, 2], str(d["%s/g%d/mtime" % (s, n)])


def analyse_arrays(f, V_MAG, V_PHS, offset="fold", use_mask=True, band=3.0):
    """fit_admittance.analyse() for one overtone, on arrays. Same steps, same defaults."""
    Y, delta, delta_rms = fa.admittance(f, V_MAG, V_PHS, offset=offset)
    dB = fa.ratio_dB(V_MAG)
    mask = (dB > fa.RATIO_DB_FLOOR) if use_mask else np.ones_like(f, bool)
    if mask.sum() < 100:
        mask = np.ones_like(f, bool)
    fs_seed, hw_seed = fa._seed(f, Y.real, mask)
    band_mask = mask
    if band and np.isfinite(band):
        band_mask = mask & (np.abs(f - fs_seed) <= band * hw_seed)
        if band_mask.sum() < 200:
            band_mask = mask
    f1 = fa.fit1_circle(f, Y, band_mask)
    f2 = fa.fit2_lorentzian(f, Y.real, band_mask, fs_seed, 2.0 * hw_seed)
    return dict(Y=Y, delta=float(delta), delta_rms=float(delta_rms), dB=dB, mask=mask, band_mask=band_mask,
                fs_seed=fs_seed, hw_seed=hw_seed, fit1=f1, fit2=f2)


def window(f, fs_seed, hw_seed, band=3.0):
    """The +-band half-widths window around the seed, mask NOT applied (the stretch of sweep the fits look at)."""
    return np.abs(f - fs_seed) <= band * hw_seed


def max_step_pct(B, sel):
    """Largest jump of B between adjacent samples inside `sel`, in % of the range of B there."""
    b = B[sel]
    rng = float(np.nanmax(b) - np.nanmin(b))
    return 100.0 * float(np.nanmax(np.abs(np.diff(b)))) / rng if rng > 0 else np.nan


def rng(vals, fmt="%.1f"):
    v = [x for x in vals if np.isfinite(x)]
    return (fmt + "–" + fmt) % (min(v), max(v)) if v else "—"


def write(name, text):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    open(p, "w").write(text + "\n")
    print(text); print("\nwrote", os.path.relpath(p, STUDY))
