"""The phase offset measured in air applied to the liquid sweeps (where the chain uses zero).

    cd software && PYTHONPATH=. python ../research/.../scripts/air_offset_in_liquid.py <data_root> <out_dir>

Rule H3: for every liquid sweep whose peak-depth test says "no fold" (n >= 3 here), corr = r + delta_air(n),
delta_air(n) = mean over the three air replicas of -min(r) (the fold-measured offset). No sign flip. Where the
test says "fold" (n = 1) the chain's own rule is kept. Air is unchanged, so the shifts share the reference.
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
SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
RHO_Q, MU_Q = 2648.0, 2.947e10; LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}

def smooth(path):
    g = np.loadtxt(path); freq = g[:, 0]; points = int(freq[-1] - freq[0]) + 1; xr = range(len(freq)); xs = np.linspace(0, len(freq) - 1, points)
    sm = lambda v: UnivariateSpline(xr, resonance.savitzky_golay(v, window_size=Constants.SG_WINDOW_SIZE, order=Constants.SG_order), s=Constants.SPLINE_FACTOR_G)(xs)
    return np.linspace(freq[0], freq[-1], points), sm(g[:, 1]), sm(g[:, 2])

def run(fr, Vm, Vp, delta_override=None):
    r = proc._phase_raw_V_phase(Vp); rmin = float(np.nanmin(r))
    decided, info = proc._phase_fold_decision(fr, Vm, r); flip = bool(decided) if decided is not None else False
    delta = -rmin if flip else 0.0
    if not flip and delta_override is not None:
        delta = delta_override
    corr = r + delta; R, X = proc._RX_exact(Vm, corr); G = proc._G_exact(R, X)
    sg = corr.copy()
    if flip:
        i = int(np.nanargmin(np.abs(corr))); sg[i:] *= -1
    Rb, Xb = proc._RX_exact(Vm, sg); B = proc._B_exact(Rb, Xb)
    idx, f_arg, band = proc.parameters_finder_impedance_exact(fr, G); gam = abs(band.bandwidth); mask = np.abs(fr - f_arg) <= 3 * gam
    c = fa.fit1_circle(fr, G + 1j * B, mask); lo = fa.fit2_lorentzian(fr, G, mask, f_arg, 2 * gam)
    return dict(G=G, B=B, mask=mask, f_arg=f_arg, gamma=gam, flip=flip, delta=delta, rmin=rmin, fit=c, lor=lo, Gmax=float(np.nanmax(G)))

# air: chain, and the fold-measured delta per overtone
air = {n: [run(*smooth(os.path.join(ROOT, s, "g%d.txt" % n))) for s in SETS["air"]] for n in N}
d_air = {n: float(np.mean([a["delta"] for a in air[n]])) for n in N}
print("delta_air per overtone [deg]:", {n: round(v, 2) for n, v in d_air.items()})
res = {}
for liq in ("water", "ipa"):
    for s in SETS[liq]:
        for n in N:
            fr, Vm, Vp = smooth(os.path.join(ROOT, s, "g%d.txt" % n))
            res[(s, n, "chain")] = run(fr, Vm, Vp); res[(s, n, "H3")] = run(fr, Vm, Vp, delta_override=d_air[n])

def m(vals): v = np.array(vals, float); return v.mean(), (v.std(ddof=1) if len(v) > 1 else 0.0)
f0 = m([a["f_arg"] for a in air[1]])[0]
L = ["| liquid | n | rule | δ used [°] | f (argmax G) [Hz] | Γ [Hz] | D [ppm] | Δf [Hz] | ΔΓ [Hz] | \\|Δf\\|/ΔΓ | Δf/Δf_KG | ΔΓ/ΔΓ_KG | R1 [Ω] | C0 [pF] | circle rms [%] | Lorentz f_s − argmax [Hz] |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
summary = {}
for liq in ("water", "ipa"):
    rho, eta = LIQ[liq]; kg = -np.sqrt(np.array(N)) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q))
    for i, n in enumerate(N):
        fa_m, _ = m([a["f_arg"] for a in air[n]]); ga_m, _ = m([a["gamma"] for a in air[n]])
        for rule in ("chain", "H3"):
            rr = [res[(s, n, rule)] for s in SETS[liq]]
            fl, fl_s = m([x["f_arg"] for x in rr]); gl, gl_s = m([x["gamma"] for x in rr]); df = fl - fa_m; dG = gl - ga_m
            R1, _ = m([x["fit"]["R1"] for x in rr]); C0, _ = m([x["fit"]["C0"] * 1e12 for x in rr]); rms, _ = m([100 * x["fit"]["rms_rel"] for x in rr]); dl, _ = m([x["lor"]["fs"] - x["f_arg"] for x in rr])
            summary[(liq, n, rule)] = dict(ratio=abs(df) / dG, df=df, dG=dG, df_kg=df / kg[i], dG_kg=dG / abs(kg[i]), sd=fl_s / dG)
            L.append("| %s | %d | %s | %+.1f | %.0f ± %.0f | %.0f ± %.0f | %.1f | %.0f | %.0f | **%.2f** | %.2f | %.2f | %.0f | %.1f | %.1f | %+.0f |" % (
                liq, n, rule, rr[0]["delta"], fl, fl_s, gl, gl_s, 2e6 * gl / fl, df, dG, abs(df) / dG, df / kg[i], dG / abs(kg[i]), R1, C0, rms, dl))
open(os.path.join(OUT, "air_offset_tables.md"), "w").write("\n".join(L)); print("\n".join(L))

# figure: loci, middle replica, chain vs H3, water and ipa
fig, ax = plt.subplots(5, 4, figsize=(19, 22))
for j, (liq, s) in enumerate((("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        for k, rule in enumerate(("chain", "H3")):
            o = res[(s, n, rule)]; a = ax[i, 2 * j + k]; mk = o["mask"]; c = o["fit"]
            a.plot(o["G"] * 1e3, o["B"] * 1e3, color="#bbbbbb", lw=0.6); a.plot(o["G"][mk] * 1e3, o["B"][mk] * 1e3, color="#2a78d6" if rule == "chain" else "#9467bd", lw=1.6)
            t = np.linspace(0, 2 * np.pi, 361); a.plot((c["xc"] + c["r"] * np.cos(t)) * 1e3, (c["yc"] + c["r"] * np.sin(t)) * 1e3, "k--", lw=0.8)
            q = int(np.nanargmax(o["G"])); a.plot(o["G"][q] * 1e3, o["B"][q] * 1e3, "v", color="#d62728", ms=7)
            a.set_aspect("equal", adjustable="datalim"); a.grid(alpha=0.25)
            a.set_title("%s n=%d  %s: δ=%+.1f°  R1=%.0f Ω C0=%.1f pF rms=%.1f%%" % (liq, n, rule, o["delta"], c["R1"], c["C0"] * 1e12, 100 * c["rms_rel"]), fontsize=8)
            if i == 4: a.set_xlabel("G [mS]")
            if 2 * j + k == 0: a.set_ylabel("B [mS]")
fig.suptitle("Admittance locus, middle replica: chain (δ = 0 where no fold) against H3 (air-measured δ applied in liquid)", fontsize=11, y=0.998)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "loci_chain_vs_H3.png"), dpi=90); plt.close(fig)

# figure: G curves chain vs H3 and ratio vs n
fig, ax = plt.subplots(2, 2, figsize=(13, 9))
for j, liq in enumerate(("water", "ipa")):
    for rule, c_, mk_ in (("chain", "#2a78d6", "o"), ("H3", "#9467bd", "D")):
        r = [summary[(liq, n, rule)]["ratio"] for n in N]; e = [summary[(liq, n, rule)]["sd"] for n in N]
        ax[0, j].errorbar(N, r, yerr=e, marker=mk_, color=c_, capsize=3, label=rule)
        ax[1, j].plot(N, [summary[(liq, n, rule)]["df_kg"] for n in N], marker=mk_, color=c_, label="%s: Δf/Δf_KG" % rule)
        ax[1, j].plot(N, [summary[(liq, n, rule)]["dG_kg"] for n in N], marker=mk_, mfc="none", ls=":", color=c_, label="%s: ΔΓ/ΔΓ_KG" % rule)
    for k, yl in ((0, "|Δf| / ΔΓ"), (1, "measured / Kanazawa–Gordon")):
        ax[k, j].axhline(1, color="k", ls="--", lw=0.8); ax[k, j].set_xticks(N); ax[k, j].set_xlabel("overtone n"); ax[k, j].set_ylabel(yl); ax[k, j].legend(fontsize=8); ax[k, j].grid(alpha=0.25); ax[k, j].set_title(liq)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "ratio_chain_vs_H3.png"), dpi=110); plt.close(fig)
