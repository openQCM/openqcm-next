"""Johannsmann's phase-shifted Lorentzian (Sensors 2021, 21, 3490, eq. 13) on the exact admittance.

    cd software && PYTHONPATH=. python ../research/.../scripts/phase_shifted_lorentzian.py <npz> <out_dir>

  G = Gmax*Gamma*( Gamma*cos(phi) + (fres-f)*sin(phi) ) / ((fres-f)^2 + Gamma^2) + G_off
  B = Gmax*Gamma*( Gamma*sin(phi) + (fres-f)*cos(phi) ) / ((fres-f)^2 + Gamma^2) + B_off
Gamma is the HALF width at half maximum (Johannsmann's convention, same as the datalog's Gamma). Three fits per
sweep on the +-3 Gamma window of the chain's G, all with the rotation form Y = A e^{j phi}/(Gamma - j(fres - f))
(see model()): (a) G alone, 5 parameters; (b) B alone, 5; (c) G and B jointly, 6, each channel weighted by its
own range. phi is reported with the rotation's sign (eq. 13's phi for G is the opposite). G and B come from the process's chain (fold decision per sweep).
Shifts are liquid minus air with the same fit, mean over the three replicas; Kanazawa-Gordon at 25 degC.
"""
import sys, os, importlib.util, numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import least_squares
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.normpath(os.path.join(HERE, "..", "..", "..", "software")); sys.path.insert(0, SW)
from openQCM.core.constants import Constants
from openQCM.core import resonance
from openQCM.processors.Multiscan import MultiscanProcess
spec = importlib.util.spec_from_file_location("fa", os.path.join(SW, "openQCM/sweep_data/fit_admittance.py")); fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
SRC, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True); proc = MultiscanProcess(None); Z = np.load(SRC)
N = (1, 3, 5, 7, 9); SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
RHO_Q, MU_Q = 2648.0, 2.947e10; LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}

def chain(g):
    freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    fr = np.linspace(freq[0], freq[-1], points); Vm, Vp = sm(g[:, 1]), sm(g[:, 2]); r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r))
    decided, _ = proc._phase_fold_decision(fr, Vm, r); flip = bool(decided) if decided is not None else False; corr = r + (-rmin if flip else 0.0)
    R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X); sg = corr.copy()
    if flip: i = int(np.nanargmin(np.abs(corr))); sg[i:] *= -1
    Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb); return fr, G, B

def model(p, f, f0):
    # p = [A (= Gmax*Gamma, mS*kHz), dfres (kHz from f0), Gamma (kHz), phi, G_off (mS), B_off (mS)]
    # Y = A * exp(j*phi) / (Gamma - j*(fres - f)) + offsets: a TRUE rotation of the complex Lorentzian by phi.
    # Its real part is eq. 13's G with phi -> -phi; its imaginary part is eq. 13's B. Eq. 13 as printed (G with
    # +(fres-f) sin(phi), B with +Gamma sin(phi)) is NOT the real and imaginary part of one rotation: fitted
    # separately, the two channels then return phi of opposite sign (measured 2026-09-14), and fitted jointly
    # the model can only satisfy both with phi ~ 0. The rotation form is used for every fit below.
    A, dfr, gam, phi, go, bo = p; d = (f0 - f) / 1e3 + dfr; Y = A * np.exp(1j * phi) / (gam - 1j * d)
    return Y.real + go, Y.imag + bo

def fit(fr, G, B, mask, f_arg, gam0, joint):
    """joint: False -> G alone (5 parameters); True -> G and B jointly (6); "B" -> B alone (5)."""
    which = {False: "G", True: "GB", "B": "B"}[joint]
    f = fr[mask]; g = G[mask] * 1e3; b = B[mask] * 1e3; sg_, sb_ = np.ptp(g) or 1.0, np.ptp(b) or 1.0
    p0 = [float((g.max() - g.min()) * gam0 / 1e3), 0.0, gam0 / 1e3, 0.0, float(g.min()), float(np.median(b))]
    def res(p):
        Gm, Bm = model(p, f, f_arg); r = []
        if "G" in which: r.append((Gm - g) / sg_)
        if "B" in which: r.append((Bm - b) / sb_)
        return np.concatenate(r)
    sol = least_squares(res, p0, method="trf", xtol=1e-14, ftol=1e-14, max_nfev=40000); p = sol.x
    Gm, Bm = model(p, f, f_arg); rmsG = float(np.sqrt(np.mean((Gm - g) ** 2)) / sg_); rmsB = float(np.sqrt(np.mean((Bm - b) ** 2)) / sb_)
    n, k = len(sol.fun), len(sol.x); s2 = float(sol.fun @ sol.fun) / max(n - k, 1)
    try: sd = np.sqrt(np.clip(np.diag(s2 * np.linalg.inv(sol.jac.T @ sol.jac)), 0, None))
    except np.linalg.LinAlgError: sd = np.full(k, np.nan)
    return dict(fres=f_arg + p[1] * 1e3, sd_fres=sd[1] * 1e3, gamma=abs(p[2]) * 1e3, phi_deg=float(np.degrees(np.arctan2(np.sin(p[3]), np.cos(p[3])))), A=p[0], rmsG=rmsG, rmsB=rmsB, p=p, ok=bool(sol.success))

res = {}; curves = {}
for liq, sets in SETS.items():
    for s in sets:
        for n in N:
            fr, G, B = chain(Z["%s/g%d" % (s, n)]); idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam0 = abs(band.bandwidth); mask = np.abs(fr - f_arg) <= 3 * gam0
            c = fa.fit1_circle(fr, G + 1j * B, mask)
            res[(s, n)] = dict(f_arg=f_arg, gam_hh=gam0, G=fit(fr, G, B, mask, f_arg, gam0, False), B=fit(fr, G, B, mask, f_arg, gam0, "B"), GB=fit(fr, G, B, mask, f_arg, gam0, True), theta=np.degrees(c["theta"]), fs_circle=c["fs"]); curves[(s, n)] = (fr, G, B, mask)
def get(d, path):
    for k in path: d = d[k]
    return d
def st(liq, n, path):
    # path is a tuple of keys, e.g. ("G", "fres"); no eval: a name looked up in a comprehension is not the caller's
    v = np.array([get(res[(s, n)], path) for s in SETS[liq]], float); return v.mean(), (v.std(ddof=1) if len(v) > 1 else 0.0)

L = ["### Phase-shifted Lorentzian per phase, mean ± sd over three replicas\n", "| phase | n | fit | f_res [Hz] | f_res − argmax [Hz] | Γ (HWHM) [Hz] | Γ / Γ half height | φ [°] | circle θ [°] | rms G [% range] | rms B [% range] |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for liq in ("air", "water", "ipa"):
    for n in N:
        for k, lab in (("G", "G only"), ("B", "B only"), ("GB", "G and B")):
            fr_, fr_s = st(liq, n, (k, "fres")); ga, _ = st(liq, n, (k, "gamma")); ph, ph_s = st(liq, n, (k, "phi_deg")); fa_, _ = st(liq, n, ("f_arg",)); gh, _ = st(liq, n, ("gam_hh",)); th, _ = st(liq, n, ("theta",))
            rg, _ = st(liq, n, (k, "rmsG")); rb = st(liq, n, (k, "rmsB"))[0]
            L.append("| %s | %d | %s | %.0f ± %.0f | %+.0f | %.0f | %.3f | %+.1f ± %.1f | %+.0f | %.2f | %s |" % (liq, n, lab, fr_, fr_s, fr_ - fa_, ga, ga / gh, ph, ph_s, th, 100 * rg, "%.2f" % (100 * rb)))
f0 = st("air", 1, ("G", "fres"))[0]; summary = {}
for liq in ("water", "ipa"):
    rho, eta = LIQ[liq]; kg = -np.sqrt(np.array(N)) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
    L += ["\n### air → %s: shifts, against Kanazawa–Gordon (25 °C)\n" % liq, "| n | fit | Δf [Hz] | Δf/Δf_KG | ΔΓ [Hz] | ΔΓ/ΔΓ_KG | **\\|Δf\\|/ΔΓ** | for reference: argmax + half height | circle |", "|---|---|---|---|---|---|---|---|---|"]
    for i, n in enumerate(N):
        dfa = st(liq, n, ("f_arg",))[0] - st("air", n, ("f_arg",))[0]; dgh = st(liq, n, ("gam_hh",))[0] - st("air", n, ("gam_hh",))[0]
        dfc = st(liq, n, ("fs_circle",))[0] - st("air", n, ("fs_circle",))[0]
        for k, lab in (("G", "G only"), ("B", "B only"), ("GB", "G and B")):
            df = st(liq, n, (k, "fres"))[0] - st("air", n, (k, "fres"))[0]; dG = st(liq, n, (k, "gamma"))[0] - st("air", n, (k, "gamma"))[0]
            summary[(liq, n, k)] = dict(ratio=abs(df) / dG, df_kg=df / kg[i], dG_kg=dG / abs(kg[i]))
            L.append("| %d | %s | %.0f | %.2f | %.0f | %.2f | **%.2f** | %.2f | Δf %.0f |" % (n, lab, df, df / kg[i], dG, dG / abs(kg[i]), abs(df) / dG, abs(dfa) / dgh, dfc))
L += ["\n### G-only fit: sensitivity to the window (middle replicas), f_res − argmax [Hz] / Γ [Hz] / φ [°]\n", "| set | n | ±2 Γ | ±3 Γ | ±4 Γ | ±6 Γ |", "|---|---|---|---|---|---|"]
for s_ in ("air_1", "wat_1", "ipa_1"):
    for n in N:
        fr, G, B, _ = curves[(s_, n)]; o = res[(s_, n)]; cells = []
        for W in (2, 3, 4, 6):
            mk = np.abs(fr - o["f_arg"]) <= W * o["gam_hh"]; q = fit(fr, G, B, mk, o["f_arg"], o["gam_hh"], False)
            cells.append("%+.0f / %.0f / %+.1f" % (q["fres"] - o["f_arg"], q["gamma"], q["phi_deg"]))
        L.append("| %s | %d | %s |" % (s_, n, " | ".join(cells)))
open(os.path.join(OUT, "psl_tables.md"), "w").write("\n".join(L)); print("\n".join(L))


# Kanazawa-Gordon figure for the G-only fit: classic view, ratio, and sqrt(n) slopes
NN = np.array(N, float); fig, ax = plt.subplots(2, 3, figsize=(17, 9.5)); slopes = ["\n### G-only fit: slopes in √n through the origin [Hz/√n]\n", "| liquid | k_KG | k from −Δf | k from ΔΓ | ratio |", "|---|---|---|---|---|"]
for j, liq in enumerate(("water", "ipa")):
    rho, eta = LIQ[liq]; kg = -np.sqrt(NN) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
    df = np.array([st(liq, n, ("G", "fres"))[0] - st("air", n, ("G", "fres"))[0] for n in N]); dG = np.array([st(liq, n, ("G", "gamma"))[0] - st("air", n, ("G", "gamma"))[0] for n in N])
    dfe = np.array([np.hypot(st(liq, n, ("G", "fres"))[1], st("air", n, ("G", "fres"))[1]) for n in N]); dGe = np.array([np.hypot(st(liq, n, ("G", "gamma"))[1], st("air", n, ("G", "gamma"))[1]) for n in N])
    dfa = np.array([st(liq, n, ("f_arg",))[0] - st("air", n, ("f_arg",))[0] for n in N]); dGh = np.array([st(liq, n, ("gam_hh",))[0] - st("air", n, ("gam_hh",))[0] for n in N])
    a = ax[0, j]; a.plot(NN, kg / NN, color="#2a78d6", lw=1, label="Kanazawa–Gordon Δf/n"); a.plot(NN, -kg / NN, color="#c0392b", lw=1, label="Kanazawa–Gordon ΔΓ/n")
    a.errorbar(NN, df / NN, yerr=dfe / NN, color="#2a78d6", marker="o", ms=8, lw=0, elinewidth=1, capsize=3, label="Δf/n, phase-shifted Lorentzian on G"); a.errorbar(NN, dG / NN, yerr=dGe / NN, color="#c0392b", marker="o", ms=8, lw=0, elinewidth=1, capsize=3, label="ΔΓ/n, phase-shifted Lorentzian on G")
    a.plot(NN, dfa / NN, marker="v", mfc="none", color="#2a78d6", lw=0, ms=8, label="Δf/n, argmax (published)"); a.axhline(0, color="#888", lw=0.6); a.set_xticks(N); a.set_xlabel("overtone n"); a.set_ylabel("Hz"); a.set_title("air → %s: shifts per overtone, normalised by n" % liq, fontsize=10); a.legend(fontsize=7.5); a.grid(alpha=0.25)
    a = ax[1, j]; a.errorbar(NN, np.abs(df) / dG, yerr=dfe / dG, color="#9467bd", marker="o", ms=7, capsize=3, label="phase-shifted Lorentzian on G"); a.plot(NN, np.abs(dfa) / dGh, marker="v", color="#d62728", ls=":", label="argmax + half height (published)")
    a.axhline(1, color="k", ls="--", lw=0.8); a.set_xticks(N); a.set_xlabel("overtone n"); a.set_ylabel("|Δf| / ΔΓ"); a.set_title("%s: |Δf|/ΔΓ (Newtonian: 1)" % liq, fontsize=10); a.legend(fontsize=8); a.grid(alpha=0.25)
    sq = np.sqrt(NN); kf = float(np.sum(sq * df) / np.sum(sq * sq)); kG = float(np.sum(sq * dG) / np.sum(sq * sq)); k_kg = -kg[0]
    slopes.append("| %s | %.0f | %.0f | %.0f | %.2f |" % (liq, k_kg, -kf, kG, -kf / kG))
    a = ax[0, 2] if j == 0 else ax[1, 2]; x = np.linspace(0, 3.2, 50)
    a.plot(x, -k_kg * x, color="#2a78d6", lw=1, label="KG Δf = −%.0f√n" % k_kg); a.plot(x, k_kg * x, color="#c0392b", lw=1, label="KG ΔΓ = +%.0f√n" % k_kg)
    a.errorbar(sq, df, yerr=dfe, color="#2a78d6", marker="o", ms=7, lw=0, elinewidth=1, capsize=3, label="Δf measured"); a.errorbar(sq, dG, yerr=dGe, color="#c0392b", marker="o", ms=7, lw=0, elinewidth=1, capsize=3, label="ΔΓ measured")
    a.plot(x, kf * x, color="#2a78d6", ls=":", lw=1, label="fit through origin: %.0f√n" % kf); a.plot(x, kG * x, color="#c0392b", ls=":", lw=1, label="fit through origin: +%.0f√n" % kG)
    a.axhline(0, color="#888", lw=0.6); a.set_xticks(sq); a.set_xticklabels(["√%d" % n for n in N]); a.set_xlabel("√n"); a.set_ylabel("Hz"); a.set_title("air → %s: against √n" % liq, fontsize=10); a.legend(fontsize=7.5); a.grid(alpha=0.25)
fig.suptitle("Phase-shifted Lorentzian on G against Kanazawa–Gordon (25 °C), mean ± sd over three sweeps per plateau", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "psl_kanazawa_gordon.png"), dpi=110); plt.close(fig)
L += slopes; open(os.path.join(OUT, "psl_tables.md"), "w").write("\n".join(L)); print("\n".join(slopes))

# figure: G and B with the joint fit, middle replicas, water and ipa; plus air
fig, ax = plt.subplots(5, 6, figsize=(24, 17))
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        fr, G, B, m = curves[(s, n)]; o = res[(s, n)]; f_arg = o["f_arg"]; Gm, Bm = model(o["GB"]["p"], fr[m], f_arg); Gg, _ = model(o["G"]["p"], fr[m], f_arg)
        a = ax[i, 2 * j]; a.plot(fr[m] - f_arg, G[m] * 1e3, "k-", lw=1, label="G"); a.plot(fr[m] - f_arg, Gm, "--", color="#9467bd", lw=1.3, label="eq. 13, G and B: φ=%+.0f°" % o["GB"]["phi_deg"]); a.plot(fr[m] - f_arg, Gg, ":", color="#2ca02c", lw=1.3, label="eq. 13, G only: φ=%+.0f°" % o["G"]["phi_deg"])
        a.axvline(0, color="#d62728", lw=0.8); a.axvline(o["GB"]["fres"] - f_arg, color="#9467bd", lw=0.8); a.set_title("%s n=%d: G, f_res − argmax = %+.0f Hz (G&B), %+.0f (G)" % (liq, n, o["GB"]["fres"] - f_arg, o["G"]["fres"] - f_arg), fontsize=8.5); a.legend(fontsize=7); a.grid(alpha=0.25); a.set_ylabel("mS")
        a = ax[i, 2 * j + 1]; a.plot(fr[m] - f_arg, B[m] * 1e3, "k-", lw=1, label="B"); a.plot(fr[m] - f_arg, Bm, "--", color="#9467bd", lw=1.3, label="eq. 13, G and B"); a.axvline(0, color="#d62728", lw=0.8); a.set_title("%s n=%d: B, rms %.1f%% of range" % (liq, n, 100 * o["GB"]["rmsB"]), fontsize=8.5); a.legend(fontsize=7); a.grid(alpha=0.25)
        if i == 4: ax[i, 2 * j].set_xlabel("f − argmax G [Hz]"); ax[i, 2 * j + 1].set_xlabel("f − argmax G [Hz]")
fig.suptitle("Johannsmann's phase-shifted Lorentzian (eq. 13) on the ±3Γ window: G alone (dotted) and G with B jointly (dashed), middle replicas", fontsize=11, y=0.999)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "psl_fits.png"), dpi=80); plt.close(fig)

# clean figure: G and the G-only fit, residual beneath, middle replicas
fig = plt.figure(figsize=(18, 20)); gs = fig.add_gridspec(10, 3, height_ratios=[3, 1] * 5, hspace=0.35, wspace=0.25)
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        fr, G, B, m = curves[(s, n)]; o = res[(s, n)]; f_arg = o["f_arg"]; Gg, _ = model(o["G"]["p"], fr[m], f_arg); x = fr[m] - f_arg; g = G[m] * 1e3
        a = fig.add_subplot(gs[2 * i, j]); a.plot(x, g, "k-", lw=1.6, label="G measured"); a.plot(x, Gg, "--", color="#2ca02c", lw=1.2, label="phase-shifted Lorentzian on G, φ = %+.1f°" % o["G"]["phi_deg"])
        a.axvline(0, color="#d62728", lw=0.8, label="argmax G"); a.axvline(o["G"]["fres"] - f_arg, color="#2ca02c", lw=0.8, label="f_res = argmax %+.0f Hz" % (o["G"]["fres"] - f_arg))
        a.set_title("%s n=%d: Γ = %.0f Hz, rms %.2f %% of range" % (liq, n, o["G"]["gamma"], 100 * o["G"]["rmsG"]), fontsize=9); a.set_ylabel("G [mS]"); a.grid(alpha=0.25); a.legend(fontsize=7, loc="lower left"); a.set_xticklabels([])
        a2 = fig.add_subplot(gs[2 * i + 1, j], sharex=a); a2.plot(x, (g - Gg) / np.ptp(g) * 100, color="#2ca02c", lw=1); a2.axhline(0, color="k", lw=0.5); a2.axvline(0, color="#d62728", lw=0.8)
        a2.set_ylabel("resid. [%]", fontsize=8); a2.set_ylim(-3, 3); a2.grid(alpha=0.25)
        if i == 4: a2.set_xlabel("f − argmax G [Hz]")
fig.suptitle("Phase-shifted Lorentzian fitted to G alone (±3Γ window), with the residual in percent of the range of G — middle replicas", fontsize=11, y=0.995)
fig.savefig(os.path.join(OUT, "psl_G_only.png"), dpi=85, bbox_inches="tight"); plt.close(fig)

# joint fit: G, B and the admittance locus with the six-parameter model, middle replicas of the liquids and air
for liq, s in (("water", "wat_1"), ("ipa", "ipa_1"), ("air", "air_1")):
    fig, ax = plt.subplots(5, 3, figsize=(17, 21))
    for i, n in enumerate(N):
        fr, G, B, m = curves[(s, n)]; o = res[(s, n)]; f_arg = o["f_arg"]; p = o["GB"]["p"]; x = fr[m] - f_arg; g = G[m] * 1e3; b = B[m] * 1e3
        Gm, Bm = model(p, fr[m], f_arg); GmG, _ = model(o["G"]["p"], fr[m], f_arg)
        a = ax[i, 0]; a.plot(x, g, "k-", lw=1.5, label="G measured"); a.plot(x, Gm, "--", color="#9467bd", lw=1.3, label="joint fit, φ = %+.1f°" % o["GB"]["phi_deg"]); a.plot(x, GmG, ":", color="#2ca02c", lw=1.1, label="fit on G alone, φ = %+.1f°" % o["G"]["phi_deg"])
        a.axvline(o["GB"]["fres"] - f_arg, color="#9467bd", lw=0.8); a.axvline(o["G"]["fres"] - f_arg, color="#2ca02c", lw=0.8); a.axvline(0, color="#d62728", lw=0.8)
        a.set_title("%s n=%d  G: joint rms %.1f%%, f_res %+.0f Hz (joint) / %+.0f (G alone) from argmax" % (liq, n, 100 * o["GB"]["rmsG"], o["GB"]["fres"] - f_arg, o["G"]["fres"] - f_arg), fontsize=8.5); a.set_ylabel("G [mS]"); a.grid(alpha=0.25); a.legend(fontsize=7, loc="lower left")
        a = ax[i, 1]; a.plot(x, b, "k-", lw=1.5, label="B measured"); a.plot(x, Bm, "--", color="#9467bd", lw=1.3, label="joint fit"); a.axvline(o["GB"]["fres"] - f_arg, color="#9467bd", lw=0.8); a.axvline(0, color="#d62728", lw=0.8)
        a.set_title("B: joint rms %.1f%% of range, Γ = %.0f Hz (joint) / %.0f (G alone)" % (100 * o["GB"]["rmsB"], o["GB"]["gamma"], o["G"]["gamma"]), fontsize=8.5); a.set_ylabel("B [mS]"); a.grid(alpha=0.25); a.legend(fontsize=7, loc="lower left")
        a = ax[i, 2]; a.plot(g, b, "k-", lw=1.5, label="measured locus (±3Γ)"); a.plot(Gm, Bm, "--", color="#9467bd", lw=1.3, label="joint model")
        A, dfr, gam, phi, go, bo = p; a.plot(go, bo, "+", color="#9467bd", ms=10, mew=1.5, label="offset G_off + iB_off"); cx, cy = go + A / (2 * gam) * np.cos(phi), bo + A / (2 * gam) * np.sin(phi)
        a.plot(cx, cy, "x", color="#9467bd", ms=8, label="centre = offset + (Gmax/2)e^{iφ}"); a.plot([go, go + A / gam * np.cos(phi)], [bo, bo + A / gam * np.sin(phi)], color="#9467bd", lw=0.7)
        a.plot([go, go + A / gam], [bo, bo], color="#888", lw=0.7, ls=":"); k = int(np.nanargmax(G)); a.plot(G[k] * 1e3, B[k] * 1e3, "v", color="#d62728", ms=8, label="argmax G")
        Gf, Bf = model(p, np.array([o["GB"]["fres"]]), f_arg); a.plot(Gf, Bf, "o", color="#9467bd", mfc="none", ms=9, label="f_res on the model")
        a.set_aspect("equal", adjustable="datalim"); a.set_title("locus: diameter rotated by φ = %+.1f° about the offset" % o["GB"]["phi_deg"], fontsize=8.5); a.set_xlabel("G [mS]"); a.set_ylabel("B [mS]"); a.grid(alpha=0.25); a.legend(fontsize=6.5, loc="best")
        if i == 4: ax[i, 0].set_xlabel("f − argmax G [Hz]"); ax[i, 1].set_xlabel("f − argmax G [Hz]")
    fig.suptitle("%s (%s): the six-parameter rotated Lorentzian fitted to G and B jointly — G, B, and the admittance locus" % (liq, s), fontsize=11, y=0.995)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "psl_joint_%s.png" % liq), dpi=85); plt.close(fig)
