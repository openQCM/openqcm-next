"""Objective analysis of the impedance datalog of 2026-09-11 (air -> water -> isopropanol, board 1920).

    python datalog_analysis.py <data_dir> <out_dir>

Reads <ts>_multi.csv (this branch's quantities: f = argmax of the exact G, D = 2*Gamma/f in ppm),
splits the run into phases by the level of the fundamental, takes the LAST 10 MINUTES of each phase
as its plateau, and writes: tables.md, summary.json and four figures. No model beyond
Kanazawa-Gordon at 25 degC; no plateau detection beyond the fixed rule stated above.
"""
import sys, os, json, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

DATA, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
N = np.array([1, 3, 5, 7, 9]); COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]; MK = ["o", "s", "D", "^", "v"]
RHO_Q, MU_Q = 2648.0, 2.947e10
LIQ = {"water": (997.05, 0.890e-3), "ipa": (781.0, 2.038e-3)}          # 25 degC, as scripts/kanazawa_gordon.py
PLATEAU_MIN = 10.0

csv = sorted(glob.glob(os.path.join(DATA, "*_multi.csv")))[0]
d = pd.read_csv(csv); d["t"] = pd.to_datetime(d.Date + " " + d.Time); d["min"] = (d.t - d.t.iloc[0]).dt.total_seconds() / 60.0
F = np.column_stack([d["Frequency_%d" % k] for k in range(5)]); D = np.column_stack([d["Dissipation_%d" % k] for k in range(5)])
GAM = D * 1e-6 * F / 2.0                                                # Gamma [Hz] = D * f / 2

# phases from the level of the fundamental (the sequence is air -> water -> ipa)
f1 = F[:, 0]; phase = np.where(f1 > 5004000, "air", np.where(f1 > 5003700, "water", "ipa"))
d["phase"] = phase
bounds = {p: (d.t[phase == p].min(), d.t[phase == p].max()) for p in ("air", "water", "ipa")}
plateau = {p: (d.t >= bounds[p][1] - pd.Timedelta(minutes=PLATEAU_MIN)) & (phase == p) for p in bounds}

def stats(mask, arr): return arr[mask].mean(axis=0), arr[mask].std(axis=0, ddof=1)
P = {p: dict(f=stats(plateau[p], F), D=stats(plateau[p], D), gamma=stats(plateau[p], GAM), n=int(plateau[p].sum()),
             t0=str(d.t[plateau[p]].min().time()), t1=str(d.t[plateau[p]].max().time()),
             T=(float(d.Temperature[plateau[p]].mean()), float(d.Temperature[plateau[p]].min()), float(d.Temperature[plateau[p]].max()))) for p in bounds}

f_air, gam_air = P["air"]["f"][0], P["air"]["gamma"][0]; f0 = f_air[0]
KG = {liq: -np.sqrt(N) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * RHO_Q * MU_Q)) for liq, (rho, eta) in LIQ.items()}

dups = int(d.duplicated(subset=[c for c in d.columns if c.startswith(("Freq", "Diss"))]).sum())
dt = np.diff(d.t.values).astype("timedelta64[ms]").astype(float) / 1e3
L = []
L.append("### Run\n")
L.append("| rows | duplicate F/D rows | median row spacing [s] | temperature min / max [°C] | air | water | isopropanol |\n|---|---|---|---|---|---|---|")
L.append("| %d | %d | %.1f | %.2f / %.2f | %s – %s | %s – %s | %s – %s |" % (len(d), dups, np.median(dt), d.Temperature.min(), d.Temperature.max(),
         *(str(bounds[p][i].time()) for p in ("air", "water", "ipa") for i in (0, 1))))
L.append("\n### Plateaus: last %.0f minutes of each phase, mean ± sd\n" % PLATEAU_MIN)
L.append("| phase | window | rows | T [°C] mean (min–max) | n | f [Hz] | D [ppm] | Γ = D·f/2 [Hz] |\n|---|---|---|---|---|---|---|---|")
for p in ("air", "water", "ipa"):
    for i, n in enumerate(N):
        head = ("| %s | %s–%s | %d | %.2f (%.2f–%.2f) |" % (p, P[p]["t0"], P[p]["t1"], P[p]["n"], *P[p]["T"])) if i == 0 else "|  |  |  |  |"
        L.append(head + " %d | %.0f ± %.0f | %.1f ± %.1f | %.1f ± %.1f |" % (
            n, P[p]["f"][0][i], P[p]["f"][1][i], P[p]["D"][0][i], P[p]["D"][1][i], P[p]["gamma"][0][i], P[p]["gamma"][1][i]))
summary = dict(file=os.path.basename(csv), rows=len(d), duplicates=dups, f0_air=f0, plateaus={p: dict(f=P[p]["f"][0].tolist(), f_sd=P[p]["f"][1].tolist(), D=P[p]["D"][0].tolist(), D_sd=P[p]["D"][1].tolist(),
               gamma=P[p]["gamma"][0].tolist(), window=[P[p]["t0"], P[p]["t1"]], n=P[p]["n"]) for p in P}, shifts={})
SH = {}
for liq in ("water", "ipa"):
    rho, eta = LIQ[liq]
    df = P[liq]["f"][0] - f_air; dG = P[liq]["gamma"][0] - gam_air
    df_sd = np.hypot(P[liq]["f"][1], P["air"]["f"][1]); dG_sd = np.hypot(P[liq]["gamma"][1], P["air"]["gamma"][1])
    SH[liq] = dict(df=df, dG=dG, df_sd=df_sd, dG_sd=dG_sd, kg=KG[liq])
    summary["shifts"][liq] = dict(df=df.tolist(), dGamma=dG.tolist(), df_sd=df_sd.tolist(), dGamma_sd=dG_sd.tolist(), df_KG=KG[liq].tolist(), ratio=(np.abs(df) / dG).tolist())
    L.append("\n### air → %s: shifts against Kanazawa–Gordon (ρ = %.1f kg/m³, η = %.3f mPa·s, 25 °C, f₀ = %.0f Hz)\n" % (liq, rho, eta * 1e3, f0))
    L.append("| n | Δf [Hz] | Δf/n [Hz] | Δf_KG [Hz] | Δf / Δf_KG | ΔΓ [Hz] | ΔΓ/n [Hz] | ΔΓ_KG = \\|Δf_KG\\| [Hz] | ΔΓ / ΔΓ_KG | \\|Δf\\| / ΔΓ |\n|---|---|---|---|---|---|---|---|---|---|")
    for i, n in enumerate(N):
        L.append("| %d | %.0f ± %.0f | %.0f | %.0f | %.2f | %.0f ± %.0f | %.0f | %.0f | %.2f | %.2f |" % (
            n, df[i], df_sd[i], df[i] / n, KG[liq][i], df[i] / KG[liq][i], dG[i], dG_sd[i], dG[i] / n, abs(KG[liq][i]), dG[i] / abs(KG[liq][i]), abs(df[i]) / dG[i]))
open(os.path.join(OUT, "tables.md"), "w").write("\n".join(L)); print("\n".join(L))
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)

# ------------------------------------------------------------------ figures
def shade(a):
    for p, c in (("air", "#f2f2f0"), ("water", "#e3eefb"), ("ipa", "#fbeae3")):
        a.axvspan(d["min"][phase == p].min(), d["min"][phase == p].max(), color=c, zorder=0, lw=0)
    for p in bounds:
        m = plateau[p]; a.axvspan(d["min"][m].min(), d["min"][m].max(), facecolor="none", hatch="///", edgecolor="#bbbbbb", lw=0, zorder=0)
tm = d["min"].values

# 1. raw: f_n and D_n against time, one row per overtone
fig, ax = plt.subplots(5, 2, figsize=(14, 15), sharex=True)
for i, n in enumerate(N):
    for j, (arr, yl) in enumerate(((F, "f [Hz]"), (D, "D [ppm]"))):
        a = ax[i, j]; shade(a); a.plot(tm, arr[:, i], color=COL[i], lw=1.2, marker=MK[i], ms=2.5, label="n = %d" % n)
        a.set_ylabel(yl); a.legend(loc="upper right", fontsize=8); a.grid(alpha=0.25)
        if i == 0: a.set_title("Frequency, argmax of exact G" if j == 0 else "Dissipation D = 2Γ/f")
for a in ax[-1]: a.set_xlabel("time from start [min]")
fig.suptitle("%s — raw logged values; grey air, blue water, orange isopropanol; hatched = plateau windows" % os.path.basename(csv), y=0.995, fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_raw_timeseries.png"), dpi=100); plt.close(fig)

# 2. scaled by n: (f - f_air)/n, (Gamma - Gamma_air)/n, and D itself
fig, ax = plt.subplots(3, 1, figsize=(13, 12), sharex=True)
for i, n in enumerate(N):
    ax[0].plot(tm, (F[:, i] - f_air[i]) / n, color=COL[i], lw=1.2, marker=MK[i], ms=2.5, label="n = %d" % n)
    ax[1].plot(tm, (GAM[:, i] - gam_air[i]) / n, color=COL[i], lw=1.2, marker=MK[i], ms=2.5, label="n = %d" % n)
    ax[2].plot(tm, D[:, i], color=COL[i], lw=1.2, marker=MK[i], ms=2.5, label="n = %d" % n)
for a, yl, tt in ((ax[0], "(f − f_air)/n [Hz]", "frequency shift from the air plateau, divided by n"), (ax[1], "(Γ − Γ_air)/n [Hz]", "half-bandwidth shift from the air plateau, divided by n"), (ax[2], "D [ppm]", "D = 2Γ/f as logged (already overtone-normalised)")):
    shade(a); a.set_ylabel(yl); a.set_title(tt, fontsize=10); a.legend(fontsize=8, ncol=5); a.grid(alpha=0.25)
ax[-1].set_xlabel("time from start [min]"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_scaled_timeseries.png"), dpi=100); plt.close(fig)

# 3. Kanazawa-Gordon: -df/n and dGamma/n against n with the theory, and -df/n against dGamma/n
fig, ax = plt.subplots(1, 3, figsize=(17, 5.2))
for j, liq in enumerate(("water", "ipa")):
    s = SH[liq]; a = ax[j]
    a.plot(N, -s["kg"] / N, "k--", lw=1, label="Kanazawa–Gordon  −Δf_KG/n = ΔΓ_KG/n")
    a.errorbar(N, -s["df"] / N, yerr=s["df_sd"] / N, color="#2a78d6", marker="o", ms=6, lw=1.5, capsize=3, label="−Δf/n measured")
    a.errorbar(N, s["dG"] / N, yerr=s["dG_sd"] / N, color="#eb6834", marker="s", ms=6, lw=1.5, capsize=3, label="ΔΓ/n measured")
    a.set_xticks(N); a.set_xlabel("overtone n"); a.set_ylabel("Hz"); a.set_title("air → %s: shifts per overtone, scaled by n" % liq, fontsize=10); a.legend(fontsize=8); a.grid(alpha=0.25)
a = ax[2]
for liq, c, m in (("water", "#2a78d6", "o"), ("ipa", "#eb6834", "s")):
    s = SH[liq]; a.errorbar(s["dG"] / N, -s["df"] / N, xerr=s["dG_sd"] / N, yerr=s["df_sd"] / N, color=c, marker=m, ms=6, lw=0, elinewidth=1, capsize=3, label="%s measured" % liq)
    a.plot(-s["kg"] / N, -s["kg"] / N, marker=m, mfc="none", mec=c, ms=9, lw=0, label="%s Kanazawa–Gordon" % liq)
    for i, n in enumerate(N): a.annotate("n=%d" % n, (s["dG"][i] / N[i], -s["df"][i] / N[i]), textcoords="offset points", xytext=(5, 4), fontsize=8, color="#444")
lim = [0, max(np.max(-SH[l]["df"] / N) for l in SH) * 1.1]; a.plot(lim, lim, "k--", lw=1, label="Newtonian: −Δf = ΔΓ"); a.set_xlim(lim); a.set_ylim(lim)
a.set_xlabel("ΔΓ/n [Hz]"); a.set_ylabel("−Δf/n [Hz]"); a.set_title("−Δf/n against ΔΓ/n (filled: measured, open: theory)", fontsize=10); a.legend(fontsize=8); a.grid(alpha=0.25); a.set_aspect("equal")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_kanazawa_gordon.png"), dpi=110); plt.close(fig)

# 4. ratios against n
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
for liq, c, m in (("water", "#2a78d6", "o"), ("ipa", "#eb6834", "s")):
    s = SH[liq]; r = np.abs(s["df"]) / s["dG"]; r_sd = r * np.hypot(s["df_sd"] / np.abs(s["df"]), s["dG_sd"] / s["dG"])
    ax[0].errorbar(N, r, yerr=r_sd, color=c, marker=m, ms=6, lw=1.5, capsize=3, label=liq)
    ax[1].plot(N, s["df"] / s["kg"], color=c, marker=m, ms=6, lw=1.5, label="%s: Δf / Δf_KG" % liq)
    ax[1].plot(N, s["dG"] / np.abs(s["kg"]), color=c, marker=m, mfc="none", ms=6, lw=1.5, ls=":", label="%s: ΔΓ / ΔΓ_KG" % liq)
for a, yl, tt in ((ax[0], "|Δf| / ΔΓ", "|Δf| / ΔΓ per overtone (Newtonian liquid: 1)"), (ax[1], "measured / Kanazawa–Gordon", "measured shifts over the theory (1 = agreement)")):
    a.axhline(1.0, color="k", ls="--", lw=0.8); a.set_xticks(N); a.set_xlabel("overtone n"); a.set_ylabel(yl); a.set_title(tt, fontsize=10); a.legend(fontsize=8); a.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_ratios.png"), dpi=110); plt.close(fig)

# 5. the classic view: df/n below, dGamma/n above, theory as lines, one panel per liquid
fig, ax = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
for j, liq in enumerate(("water", "ipa")):
    s = SH[liq]; a = ax[j]
    a.plot(N, s["kg"] / N, color="#2a78d6", lw=1, label="Kanazawa–Gordon Δf/n")
    a.plot(N, -s["kg"] / N, color="#c0392b", lw=1, label="Kanazawa–Gordon ΔΓ/n")
    for i, n in enumerate(N):
        a.errorbar(n, s["df"][i] / n, yerr=s["df_sd"][i] / n, color="#2a78d6", marker=MK[i], ms=9, lw=0, elinewidth=1, capsize=3, label="measured Δf/n" if i == 0 else None)
        a.errorbar(n, s["dG"][i] / n, yerr=s["dG_sd"][i] / n, color="#c0392b", marker=MK[i], ms=9, lw=0, elinewidth=1, capsize=3, label="measured ΔΓ/n" if i == 0 else None)
    a.axhline(0, color="#888", lw=0.6); a.set_xticks(N); a.set_xlabel("n-th overtone"); a.set_title("air → %s" % liq, fontsize=11); a.legend(fontsize=8, loc="center right"); a.grid(alpha=0.25)
ax[0].set_ylabel("Δf/n and ΔΓ/n [Hz]")
fig.suptitle("Frequency and half-bandwidth shift per overtone, normalised by n, against Kanazawa–Gordon (25 °C)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_df_dGamma_over_n.png"), dpi=110); plt.close(fig)

# 6. against sqrt(n): Kanazawa-Gordon is a straight line through the origin, slope f0^1.5 sqrt(rho eta / pi rho_q mu_q)
fig, ax = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
sq = np.sqrt(N); x = np.linspace(0, 3.2, 50)
for j, liq in enumerate(("water", "ipa")):
    s = SH[liq]; a = ax[j]; slope = -s["kg"][0]           # |df_KG| at n = 1 = the slope in sqrt(n)
    a.plot(x, -slope * x, color="#2a78d6", lw=1, label="Kanazawa–Gordon Δf = −%.0f·√n Hz" % slope)
    a.plot(x, slope * x, color="#c0392b", lw=1, label="Kanazawa–Gordon ΔΓ = +%.0f·√n Hz" % slope)
    for i, n in enumerate(N):
        a.errorbar(sq[i], s["df"][i], yerr=s["df_sd"][i], color="#2a78d6", marker=MK[i], ms=9, lw=0, elinewidth=1, capsize=3, label="measured Δf" if i == 0 else None)
        a.errorbar(sq[i], s["dG"][i], yerr=s["dG_sd"][i], color="#c0392b", marker=MK[i], ms=9, lw=0, elinewidth=1, capsize=3, label="measured ΔΓ" if i == 0 else None)
        a.annotate("n=%d" % n, (sq[i], s["df"][i]), textcoords="offset points", xytext=(6, -12), fontsize=8, color="#444")
    # least-squares slope through the origin on the measured points, printed for the tables
    kf = float(np.sum(sq * s["df"]) / np.sum(sq * sq)); kG = float(np.sum(sq * s["dG"]) / np.sum(sq * sq))
    kf3 = float(np.sum(sq[1:] * s["df"][1:]) / np.sum(sq[1:] ** 2)); kG3 = float(np.sum(sq[1:] * s["dG"][1:]) / np.sum(sq[1:] ** 2))
    a.plot(x, kf * x, color="#2a78d6", lw=1, ls=":", label="fit through origin, n = 1…9: %.0f·√n" % kf)
    a.plot(x, kG * x, color="#c0392b", lw=1, ls=":", label="fit through origin, n = 1…9: +%.0f·√n" % kG)
    summary["shifts"][liq]["sqrt_n_slopes"] = dict(kg=slope, df_all=kf, dGamma_all=kG, df_3to9=kf3, dGamma_3to9=kG3)
    a.axhline(0, color="#888", lw=0.6); a.set_xticks(sq); a.set_xticklabels(["√%d = %.2f" % (n, v) for n, v in zip(N, sq)], fontsize=8)
    a.set_xlabel("√n"); a.set_title("air → %s" % liq, fontsize=11); a.legend(fontsize=7.5, loc="upper left"); a.grid(alpha=0.25); a.set_xlim(0, 3.2)
ax[0].set_ylabel("Δf and ΔΓ [Hz]")
fig.suptitle("Shifts against √n: Kanazawa–Gordon predicts Δf_n = −k√n and ΔΓ_n = +k√n with the same k", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig6_vs_sqrt_n.png"), dpi=110); plt.close(fig)

L2 = ["\n### Slopes in √n (least squares through the origin, Hz per √n)\n", "| liquid | k_KG | k from Δf, n = 1…9 | k from Δf, n = 3…9 | k from ΔΓ, n = 1…9 | k from ΔΓ, n = 3…9 |", "|---|---|---|---|---|---|"]
for liq in ("water", "ipa"):
    q = summary["shifts"][liq]["sqrt_n_slopes"]; L2.append("| %s | %.0f | %.0f | %.0f | %.0f | %.0f |" % (liq, q["kg"], -q["df_all"], -q["df_3to9"], q["dGamma_all"], q["dGamma_3to9"]))
open(os.path.join(OUT, "tables.md"), "a").write("\n".join(L2)); print("\n".join(L2))
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
print("written", OUT)
