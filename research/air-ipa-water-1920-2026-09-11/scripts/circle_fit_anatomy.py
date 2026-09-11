"""How fit1_circle reads f_s and Gamma off the admittance locus — the two plots behind the numbers.

    cd software && PYTHONPATH=. python ../research/.../scripts/circle_fit_anatomy.py <data_root> <out_dir>

For the motional branch Y_m = 1/(R1 (1 + jx)), x = (f^2 - f_s^2)/(f Gamma_FWHM), each sample sits on the circle
at an angle psi = -2 atan(x) from the centre (after the rotation theta). fit1_circle fits the circle (Taubin,
then geometric), finds theta, reads psi of every sample, sets x = -tan(psi/2) and solves the LINEAR problem
f^2 = (f x) Gamma + f_s^2 with weights 1/(1+x^2)^2. psi = 0 is f_s, psi = -/+90 deg are f_s +/- Gamma/2.
"""
import sys, os, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software")); sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py")); fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
proc = MultiscanProcess(None); N = (1, 3, 5, 7, 9)

def chain(path):
    g = np.loadtxt(path); freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    fr = np.linspace(freq[0], freq[-1], points); Vm, Vp = sm(g[:, 1]), sm(g[:, 2])
    r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r)); decided, _ = proc._phase_fold_decision(fr, Vm, r); flip = bool(decided) if decided is not None else False
    off = -rmin if flip else 0.0; corr = r + off; R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X); sg = corr.copy()
    if flip: i = int(np.nanargmin(np.abs(corr))); sg[i:] *= -1
    Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb); return fr, G, G + 1j * B

for liq, s in (("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1")):
    fig, ax = plt.subplots(5, 3, figsize=(18, 24))
    for i, n in enumerate(N):
        fr, G, Y = chain(os.path.join(ROOT, s, "g%d.txt" % n))
        idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth); m = np.abs(fr - f_arg) <= 3 * gam
        c = fa.fit1_circle(fr, Y, m); ctr = complex(c["xc"], c["yc"]); th = c["theta"]
        psi = np.angle((Y[m] - ctr) * np.exp(-1j * th)); x = -np.tan(psi / 2); fm = fr[m]
        fs, FW = c["fs"], c["gamma"]; x_model = (fm ** 2 - fs ** 2) / (fm * FW); psi_model = -2 * np.arctan(x_model)
        # --- locus
        a = ax[i, 0]; a.plot(G * 1e3, Y.imag * 1e3, color="#bbb", lw=0.6); a.plot(G[m] * 1e3, Y.imag[m] * 1e3, color="#2a78d6", lw=1.5, label="±3Γ window")
        t = np.linspace(0, 2 * np.pi, 361); a.plot((c["xc"] + c["r"] * np.cos(t)) * 1e3, (c["yc"] + c["r"] * np.sin(t)) * 1e3, "k--", lw=0.8, label="fitted circle")
        a.plot(c["xc"] * 1e3, c["yc"] * 1e3, "k+", ms=10, label="centre")
        for ang, lab, mk in ((0, "ψ = 0 → f_s", "o"), (-np.pi / 2, "ψ = −90° → f_s + Γ", "^"), (np.pi / 2, "ψ = +90° → f_s − Γ", "v")):
            p = ctr + c["r"] * np.exp(1j * (ang + th)); a.plot(p.real * 1e3, p.imag * 1e3, mk, color="#9467bd", ms=9, label=lab)
            a.plot([c["xc"] * 1e3, p.real * 1e3], [c["yc"] * 1e3, p.imag * 1e3], color="#9467bd", lw=0.8)
        k = int(np.nanargmax(G)); a.plot(G[k] * 1e3, Y.imag[k] * 1e3, "v", color="#d62728", ms=8, label="argmax G (sample)")
        a.set_aspect("equal", adjustable="datalim"); a.grid(alpha=0.25); a.set_xlabel("G [mS]"); a.set_ylabel("B [mS]")
        a.set_title("%s n=%d locus: θ = %+.1f°, R1 = %.0f Ω, rms %.1f%% of r" % (liq, n, np.degrees(th), c["R1"], 100 * c["rms_rel"]), fontsize=9)
        if i == 0: a.legend(fontsize=7, loc="best")
        # --- psi against f
        a = ax[i, 1]; a.plot(fm - fs, np.degrees(psi), ".", ms=2, color="#2a78d6", label="ψ of each sample (data)"); a.plot(fm - fs, np.degrees(psi_model), "k--", lw=1, label="BVD: ψ = −2·atan((f²−f_s²)/(f·2Γ))")
        a.axhline(0, color="#9467bd", lw=0.8); a.axvline(0, color="#9467bd", lw=0.8); a.axvline(f_arg - fs, color="#d62728", lw=1, label="argmax G  (%+.0f Hz from f_s)" % (f_arg - fs))
        for yv in (-90, 90): a.axhline(yv, color="#9467bd", lw=0.5, ls=":")
        a.set_xlabel("f − f_s(circle) [Hz]"); a.set_ylabel("ψ [deg]"); a.grid(alpha=0.25); a.set_title("angle on the arc: f_s = %.0f Hz, Γ = %.0f Hz (= gamma/2), sd f_s %.1f Hz" % (fs, FW / 2, c["sd_fs"]), fontsize=9)
        if i == 0: a.legend(fontsize=7, loc="best")
        # --- residual of the linear regression, with weights
        a = ax[i, 2]; w = 1.0 / (1 + x * x) ** 2; res = (fm ** 2 - (fm * x * FW + fs ** 2)) / (2 * fm)   # in Hz: d(f^2)/(2f)
        a.plot(fm - fs, res, ".", ms=2, color="#2a78d6", label="residual of f² = (f·x)·2Γ + f_s², as Hz")
        a2 = a.twinx(); a2.plot(fm - fs, w, color="#eb6834", lw=1, label="weight 1/(1+x²)²"); a2.set_ylim(0, 1.05); a2.set_ylabel("weight", color="#eb6834")
        a.axhline(0, color="k", lw=0.6); a.axvline(f_arg - fs, color="#d62728", lw=1); a.set_xlabel("f − f_s(circle) [Hz]"); a.set_ylabel("residual [Hz]"); a.grid(alpha=0.25)
        a.set_title("regression residual (blue) and weight (orange); %d of %d samples kept" % (c["n_arc"], c["n_fit"]), fontsize=9)
        if i == 0: a.legend(fontsize=7, loc="upper left")
    fig.suptitle("%s (%s): how fit1_circle reads f_s and Γ — locus with centre and rotation, sample angle ψ against f, regression residual" % (liq, s), fontsize=11, y=0.999)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "circle_anatomy_%s.png" % liq), dpi=85); plt.close(fig)
print("ok")
