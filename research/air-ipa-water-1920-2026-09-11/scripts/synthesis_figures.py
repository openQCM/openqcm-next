"""Figures and tables for the synthesis page: symmetric against phase-shifted Lorentzian on the same G, and both
against Kanazawa-Gordon.   cd software && PYTHONPATH=. python ../research/.../scripts/synthesis_figures.py <npz> <out_dir>"""
import sys, os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from psl_lib import *
NPZ, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True); Z = np.load(NPZ)
res = {}; curves = {}
for liq, sets in SETS.items():
    for s in sets:
        for n in N:
            c = chain(Z["%s/g%d" % (s, n)]); fr, G = c["fr"], c["G"]; f_arg, gam0, _ = argmax_and_halfwidth(fr, G); mask = np.abs(fr - f_arg) <= 3 * gam0
            sym = fa.fit2_lorentzian(fr, G, mask, f_arg, 2 * gam0); psl = fit(fr, G, c["B"], mask, f_arg, gam0, "G")
            res[(s, n)] = dict(f_arg=f_arg, gam_hh=gam0, sym=dict(fres=sym["fs"], gamma=sym["gamma"] / 2, rms=sym["rms_rel"] * (np.nanmax(G[mask]) - np.nanmin(G[mask])) / np.nanmax(G[mask] - np.nanmin(G[mask])), p=sym), psl=psl); curves[(s, n)] = (fr, G, mask)
def m(liq, n, key):
    v = np.array([res[(s, n)]["psl"][key] if key in ("fres", "gamma", "phi_deg") and False else 0 for s in SETS[liq]]); return v
def st(liq, n, est, key):
    v = np.array([res[(s, n)][est][key] if est != "arg" else res[(s, n)]["f_arg" if key == "fres" else "gam_hh"] for s in SETS[liq]], float); return v.mean(), v.std(ddof=1)
# rms of the symmetric fit as a fraction of the range of G (same definition as the PSL rms)
for k, v in res.items():
    fr, G, mask = curves[k]; g = G[mask] * 1e3; p2 = v["sym"]["p"]; Gs = fa.fit2_curve(fr[mask], {"fit2": p2, "fs_seed": v["f_arg"]}) * 1e3
    v["sym"]["rms"] = float(np.sqrt(np.mean((Gs - g) ** 2)) / np.ptp(g)); v["sym"]["curve"] = Gs
    Gp, _ = model(v["psl"]["p"], fr[mask], v["f_arg"]); v["psl"]["curve"] = Gp

# ---------------- figure 1: both fits on G, residuals beneath, middle replicas
fig = plt.figure(figsize=(18, 21)); gs = fig.add_gridspec(10, 3, height_ratios=[3, 1.3] * 5, hspace=0.35, wspace=0.25)
for j, (liq, s) in enumerate((("air", "air_1"), ("water", "wat_1"), ("ipa", "ipa_1"))):
    for i, n in enumerate(N):
        v = res[(s, n)]; fr, G, mask = curves[(s, n)]; x = fr[mask] - v["f_arg"]; g = G[mask] * 1e3
        a = fig.add_subplot(gs[2 * i, j]); a.plot(x, g, "k-", lw=1.8, label="G measured"); a.plot(x, v["sym"]["curve"], "--", color="#eb6834", lw=1.2, label="symmetric Lorentzian (φ ≡ 0)"); a.plot(x, v["psl"]["curve"], "--", color="#2a78d6", lw=1.2, label="phase-shifted Lorentzian, φ = %+.0f°" % v["psl"]["phi_deg"])
        a.axvline(0, color="#d62728", lw=0.8); a.axvline(v["psl"]["fres"] - v["f_arg"], color="#2a78d6", lw=0.8); a.axvline(v["sym"]["fres"] - v["f_arg"], color="#eb6834", lw=0.8)
        a.set_title("%s n=%d: f_res − argmax = %+.0f Hz (phase-shifted), %+.0f Hz (symmetric)" % (liq, n, v["psl"]["fres"] - v["f_arg"], v["sym"]["fres"] - v["f_arg"]), fontsize=8.5); a.set_ylabel("G [mS]"); a.grid(alpha=0.25); a.legend(fontsize=6.5, loc="lower left"); a.set_xticklabels([])
        a2 = fig.add_subplot(gs[2 * i + 1, j], sharex=a); a2.plot(x, (g - v["sym"]["curve"]) / np.ptp(g) * 100, color="#eb6834", lw=1, label="symmetric: rms %.2f %%" % (100 * v["sym"]["rms"])); a2.plot(x, (g - v["psl"]["curve"]) / np.ptp(g) * 100, color="#2a78d6", lw=1, label="phase-shifted: rms %.2f %%" % (100 * v["psl"]["rmsG"]))
        a2.axhline(0, color="k", lw=0.5); a2.set_ylim(-8, 8); a2.set_ylabel("resid. [%]", fontsize=8); a2.grid(alpha=0.25); a2.legend(fontsize=6.5, loc="upper left", ncol=2)
        if i == 4: a2.set_xlabel("f − argmax G [Hz]")
fig.suptitle("The same G, two Lorentzians: symmetric (orange) and phase-shifted (blue), ±3Γ window, residuals in percent of the range of G — middle replicas", fontsize=11, y=0.995)
fig.savefig(os.path.join(OUT, "S1_two_lorentzians.png"), dpi=85, bbox_inches="tight"); plt.close(fig)

# ---------------- tables and figure 2: against Kanazawa-Gordon
f0 = st("air", 1, "psl", "fres")[0]; NN = np.array(N, float); L = []
L += ["### Where the two fits put f_res and Γ, mean over three replicas\n", "| phase | n | argmax G [Hz] | f_res symmetric − argmax [Hz] | f_res phase-shifted − argmax [Hz] | Γ half height [Hz] | Γ symmetric [Hz] | Γ phase-shifted [Hz] | φ [°] | rms symmetric [% range] | rms phase-shifted [% range] |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for liq in ("air", "water", "ipa"):
    for n in N:
        fa_ = st(liq, n, "arg", "fres")[0]; L.append("| %s | %d | %.0f | %+.0f | %+.0f | %.0f | %.0f | %.0f | %+.1f | %.2f | %.2f |" % (liq, n, fa_, st(liq, n, "sym", "fres")[0] - fa_, st(liq, n, "psl", "fres")[0] - fa_, st(liq, n, "arg", "gamma")[0], st(liq, n, "sym", "gamma")[0], st(liq, n, "psl", "gamma")[0], st(liq, n, "psl", "phi_deg")[0], 100 * np.mean([res[(s, n)]["sym"]["rms"] for s in SETS[liq]]), 100 * np.mean([res[(s, n)]["psl"]["rmsG"] for s in SETS[liq]])))
fig, ax = plt.subplots(2, 2, figsize=(13, 9)); S = {}
for j, liq in enumerate(("water", "ipa")):
    kg = np.array([kg_shift(f0, n, liq) for n in N]); L += ["\n### air → %s against Kanazawa–Gordon (25 °C)\n" % liq, "| n | estimator | Δf [Hz] | Δf/Δf_KG | ΔΓ [Hz] | ΔΓ/ΔΓ_KG | \\|Δf\\|/ΔΓ |", "|---|---|---|---|---|---|---|"]
    for est, lab, c_, mk in (("arg", "argmax + half height", "#d62728", "v"), ("sym", "symmetric Lorentzian", "#eb6834", "s"), ("psl", "phase-shifted Lorentzian", "#2a78d6", "o")):
        df = np.array([st(liq, n, est, "fres")[0] - st("air", n, est, "fres")[0] for n in N]); dG = np.array([st(liq, n, est, "gamma")[0] - st("air", n, est, "gamma")[0] for n in N]); S[(liq, est)] = (df, dG)
        for i, n in enumerate(N): L.append("| %d | %s | %.0f | %.2f | %.0f | %.2f | **%.2f** |" % (n, lab, df[i], df[i] / kg[i], dG[i], dG[i] / abs(kg[i]), abs(df[i]) / dG[i]))
        ax[0, j].plot(NN, np.abs(df) / dG, marker=mk, color=c_, ls=":" if est == "arg" else "-", label=lab); ax[1, j].plot(NN, df / kg, marker=mk, color=c_, ls=":" if est == "arg" else "-", label="%s: Δf/Δf_KG" % lab); ax[1, j].plot(NN, dG / np.abs(kg), marker=mk, mfc="none", color=c_, ls="--", lw=0.8, label="%s: ΔΓ/ΔΓ_KG" % lab)
    for k_, yl, tt in ((0, "|Δf| / ΔΓ", "%s: |Δf|/ΔΓ (Newtonian: 1)" % liq), (1, "measured / theory", "%s: Δf (solid) and ΔΓ (dashed) over Kanazawa–Gordon" % liq)):
        ax[k_, j].axhline(1, color="k", ls="--", lw=0.8); ax[k_, j].set_xticks(N); ax[k_, j].set_xlabel("overtone n"); ax[k_, j].set_ylabel(yl); ax[k_, j].set_title(tt, fontsize=10); ax[k_, j].legend(fontsize=7); ax[k_, j].grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "S2_kanazawa_gordon.png"), dpi=110); plt.close(fig)
open(os.path.join(OUT, "synthesis_tables.md"), "w").write("\n".join(L)); print("\n".join(L))

# ---------------- figure 3: the classic view, one panel per fit and liquid
fig, ax = plt.subplots(2, 2, figsize=(13, 10), sharey="row")
for j, liq in enumerate(("water", "ipa")):
    kg = np.array([kg_shift(f0, n, liq) for n in N])
    for i, (est, lab) in enumerate((("sym", "symmetric Lorentzian"), ("psl", "phase-shifted Lorentzian"))):
        a = ax[i, j]; df, dG = S[(liq, est)]
        dfe = np.array([np.hypot(st(liq, n, est, "fres")[1], st("air", n, est, "fres")[1]) for n in N]); dGe = np.array([np.hypot(st(liq, n, est, "gamma")[1], st("air", n, est, "gamma")[1]) for n in N])
        a.plot(NN, kg / NN, color="#2a78d6", lw=1, label="Kanazawa–Gordon Δf/n"); a.plot(NN, -kg / NN, color="#c0392b", lw=1, label="Kanazawa–Gordon ΔΓ/n")
        MK = ["s", "o", "^", "v", "D"]
        for k_, n in enumerate(N):
            a.errorbar(n, df[k_] / n, yerr=dfe[k_] / n, marker=MK[k_], color="#2a78d6", ms=9, lw=0, elinewidth=1, capsize=3, label="measured Δf/n" if k_ == 0 else None)
            a.errorbar(n, dG[k_] / n, yerr=dGe[k_] / n, marker=MK[k_], color="#c0392b", ms=9, lw=0, elinewidth=1, capsize=3, label="measured ΔΓ/n" if k_ == 0 else None)
        a.axhline(0, color="#888", lw=0.6); a.set_xticks(N); a.set_title("air → %s — %s" % (liq, lab), fontsize=10); a.grid(alpha=0.25); a.legend(fontsize=8, loc="center left")
        if j == 0: a.set_ylabel("Δf/n and ΔΓ/n [Hz]")
        if i == 1: a.set_xlabel("n-th overtone")
fig.suptitle("Frequency and half-bandwidth shift per overtone, normalised by n, against Kanazawa–Gordon (25 °C): symmetric fit (top) and phase-shifted fit (bottom)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "S3_classic_view.png"), dpi=110); plt.close(fig)

# ---------------- figure 4: against sqrt(n)
fig, ax = plt.subplots(2, 2, figsize=(13, 10), sharey="row"); sq = np.sqrt(NN); x = np.linspace(0, 3.2, 50); slopes = ["\n### Slopes in √n through the origin [Hz/√n]\n", "| liquid | fit | k_KG | k from −Δf | k from ΔΓ | ratio |", "|---|---|---|---|---|---|"]
for j, liq in enumerate(("water", "ipa")):
    k_kg = -kg_shift(f0, 1, liq)
    for i, (est, lab) in enumerate((("sym", "symmetric Lorentzian"), ("psl", "phase-shifted Lorentzian"))):
        a = ax[i, j]; df, dG = S[(liq, est)]; kf = float(np.sum(sq * df) / np.sum(sq * sq)); kG = float(np.sum(sq * dG) / np.sum(sq * sq)); slopes.append("| %s | %s | %.0f | %.0f | %.0f | %.2f |" % (liq, lab, k_kg, -kf, kG, -kf / kG))
        a.plot(x, -k_kg * x, color="#2a78d6", lw=1, label="Kanazawa–Gordon Δf = −%.0f·√n" % k_kg); a.plot(x, k_kg * x, color="#c0392b", lw=1, label="Kanazawa–Gordon ΔΓ = +%.0f·√n" % k_kg)
        a.plot(sq, df, "o", color="#2a78d6", ms=8, label="measured Δf"); a.plot(sq, dG, "o", color="#c0392b", ms=8, label="measured ΔΓ")
        a.plot(x, kf * x, ":", color="#2a78d6", lw=1.2, label="fit through origin: %.0f·√n" % kf); a.plot(x, kG * x, ":", color="#c0392b", lw=1.2, label="fit through origin: +%.0f·√n" % kG)
        for k_, n in enumerate(N): a.annotate("n=%d" % n, (sq[k_], df[k_]), textcoords="offset points", xytext=(6, -12), fontsize=8, color="#444")
        a.axhline(0, color="#888", lw=0.6); a.set_xticks(sq); a.set_xticklabels(["√%d" % n for n in N]); a.set_xlim(0, 3.2); a.set_title("air → %s — %s" % (liq, lab), fontsize=10); a.grid(alpha=0.25); a.legend(fontsize=7.5, loc="upper left")
        if j == 0: a.set_ylabel("Δf and ΔΓ [Hz]")
        if i == 1: a.set_xlabel("√n")
fig.suptitle("Shifts against √n: Kanazawa–Gordon predicts Δf = −k√n and ΔΓ = +k√n with one k — symmetric fit (top), phase-shifted fit (bottom)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "S4_sqrt_n.png"), dpi=110); plt.close(fig)
open(os.path.join(OUT, "synthesis_tables.md"), "a").write("\n".join(slopes)); print("\n".join(slopes))
