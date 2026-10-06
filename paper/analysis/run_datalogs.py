# -*- coding: utf-8 -*-
"""
run_datalogs.py — the two acquisition runs' datalogs (2026-09-10, 2026-09-11),
each logged simultaneously by the impedance chain (`_multi.csv`: f = max of G,
D = 2Γ_hh/f in ppm) and by the production magnitude chain (`_multi_amplitude.csv`:
f = max of the baseline-corrected |H| in dB, "Dissipation" = full width at
−0.3 dB below the maximum, in MHz).

Plateau rule (stated before looking at the result): phases are classified from
the fundamental's logged frequency (air > 5 004 000 Hz; water 5 003 700–5 004 000;
isopropanol < 5 003 700). The plateau of a phase is its last PLATEAU_MIN minutes
(10 min on 2026-09-11; 2.5 min on the short run of 2026-09-10). Rows that
duplicate the previous row's F/D values exactly (a datalog artefact: bursts
written within the same second) are dropped before statistics, and counted.
Nothing else is excluded.
"""
import os, json
import numpy as np, pandas as pd
import qcmchain as q, data

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
N = np.array([1, 3, 5, 7, 9])
RUNS = {"2026-09-11": (data.datalogs_0911, 10.0), "2026-09-10": (data.datalogs_0910, 2.5)}


def phases(d):
    f1 = d["Frequency_0"].values
    return np.where(f1 > 5004000, "air", np.where(f1 > 5003700, "water", "ipa"))


def dedup(d):
    cols = [c for c in d.columns if c.startswith(("Frequency", "Dissipation"))]
    same = (d[cols].shift(1) == d[cols]).all(axis=1)
    return d[~same].copy(), int(same.sum())


def plateau_stats(d, ph, minutes, kind):
    F = np.column_stack([d["Frequency_%d" % k] for k in range(5)]).astype(float)
    Dc = np.column_stack([d["Dissipation_%d" % k] for k in range(5)]).astype(float)
    if kind == "impedance":
        GAM = Dc * 1e-6 * F / 2.0            # Γ_hh [Hz] from D [ppm]
        Dppm = Dc
    else:
        GAM = Dc * 1e6                       # the −0.3 dB full width in Hz (NOT a Γ)
        Dppm = np.full_like(Dc, np.nan)
    out = {}
    for p in ("air", "water", "ipa"):
        m = ph == p
        if not m.any():
            continue
        t1 = d.t[m].max(); sel = m & (d.t >= t1 - pd.Timedelta(minutes=minutes))
        out[p] = dict(n=int(sel.sum()), t0=str(d.t[sel].min().time()), t1=str(t1.time()),
                      T=[float(d.Temperature[sel].mean()), float(d.Temperature[sel].min()), float(d.Temperature[sel].max())],
                      f=F[sel].mean(0), f_sd=F[sel].std(0, ddof=1), w=GAM[sel].mean(0), w_sd=GAM[sel].std(0, ddof=1),
                      D=Dppm[sel].mean(0), D_sd=Dppm[sel].std(0, ddof=1))
    return out


def main():
    L = ["# Datalog plateaus: impedance chain against the production magnitude chain\n"]
    summary = {}
    for run, (loader, minutes) in RUNS.items():
        imp, amp = loader()
        imp, dup_i = dedup(imp); amp, dup_a = dedup(amp)
        ph_i, ph_a = phases(imp), phases(amp)
        Pi, Pa = plateau_stats(imp, ph_i, minutes, "impedance"), plateau_stats(amp, ph_a, minutes, "amplitude")
        f0 = float(Pi["air"]["f"][0])
        L.append("## Run %s — plateau = last %.1f min of each phase; duplicate rows dropped: %d (impedance file), %d (amplitude file)\n" % (run, minutes, dup_i, dup_a))
        L.append("| phase | window | rows | T [°C] | n | f_G [Hz] ± sd | Γ_hh [Hz] ± sd | D [ppm] | f_mag [Hz] ± sd | w(−0.3 dB) [Hz] ± sd | f_mag − f_G [Hz] |\n|---|---|---|---|---|---|---|---|---|---|---|")
        for p in ("air", "water", "ipa"):
            if p not in Pi:
                continue
            for i, n in enumerate(N):
                head = "| %s | %s–%s | %d | %.2f (%.2f–%.2f) |" % ((p, Pi[p]["t0"], Pi[p]["t1"], Pi[p]["n"]) + tuple(Pi[p]["T"])) if i == 0 else "| | | | |"
                L.append(head + " %d | %.0f ± %.1f | %.1f ± %.1f | %.1f | %.0f ± %.1f | %.0f ± %.1f | %+.0f |" % (
                    n, Pi[p]["f"][i], Pi[p]["f_sd"][i], Pi[p]["w"][i], Pi[p]["w_sd"][i], Pi[p]["D"][i],
                    Pa[p]["f"][i], Pa[p]["f_sd"][i], Pa[p]["w"][i], Pa[p]["w_sd"][i], Pa[p]["f"][i] - Pi[p]["f"][i]))
        summary[run] = dict(duplicates=[dup_i, dup_a], minutes=minutes, f0=f0, plateaus={}, shifts={})
        for p in Pi:
            summary[run]["plateaus"][p] = dict(imp_f=Pi[p]["f"].tolist(), imp_f_sd=Pi[p]["f_sd"].tolist(), imp_gamma=Pi[p]["w"].tolist(), imp_gamma_sd=Pi[p]["w_sd"].tolist(),
                                              imp_D=Pi[p]["D"].tolist(), amp_f=Pa[p]["f"].tolist(), amp_f_sd=Pa[p]["f_sd"].tolist(), amp_w03=Pa[p]["w"].tolist(), amp_w03_sd=Pa[p]["w_sd"].tolist(),
                                              n=Pi[p]["n"], window=[Pi[p]["t0"], Pi[p]["t1"]], T=Pi[p]["T"])
        for liq in ("water", "ipa"):
            if liq not in Pi:
                continue
            kg = q.kanazawa_gordon(f0, N, **q.LIQUIDS[liq])
            L.append("\n### %s: air → %s shifts against Kanazawa–Gordon (25 °C, f0 = %.0f Hz)\n" % (run, liq, f0))
            L.append("| n | Δf_G [Hz] ± sd | eps_f(G) [%] | ΔΓ_hh [Hz] ± sd | eps_Γ [%] | ρ=\\|Δf\\|/ΔΓ | Δf_mag [Hz] ± sd | eps_f(mag) [%] | Δw(−0.3 dB) [Hz] |\n|---|---|---|---|---|---|---|---|---|")
            rows = []
            for i, n in enumerate(N):
                dfg = Pi[liq]["f"][i] - Pi["air"]["f"][i]; dG = Pi[liq]["w"][i] - Pi["air"]["w"][i]
                dfm = Pa[liq]["f"][i] - Pa["air"]["f"][i]; dw = Pa[liq]["w"][i] - Pa["air"]["w"][i]
                sdf = np.hypot(Pi[liq]["f_sd"][i], Pi["air"]["f_sd"][i]); sdG = np.hypot(Pi[liq]["w_sd"][i], Pi["air"]["w_sd"][i]); sdm = np.hypot(Pa[liq]["f_sd"][i], Pa["air"]["f_sd"][i])
                L.append("| %d | %.0f ± %.0f | %+.1f | %.0f ± %.0f | %+.1f | %.2f | %.0f ± %.0f | %+.1f | %.0f |" % (
                    n, dfg, sdf, 100 * (dfg / kg[i] - 1), dG, sdG, 100 * (dG / -kg[i] - 1), abs(dfg) / dG, dfm, sdm, 100 * (dfm / kg[i] - 1), dw))
                rows.append(dict(n=int(n), df_G=dfg, df_G_sd=sdf, dGamma=dG, dGamma_sd=sdG, df_mag=dfm, df_mag_sd=sdm, dw03=dw, df_KG=float(kg[i]),
                                 eps_f_G=dfg / kg[i] - 1, eps_G=dG / -kg[i] - 1, eps_f_mag=dfm / kg[i] - 1, rho=abs(dfg) / dG))
            summary[run]["shifts"][liq] = rows
        # air drift and D in air (sensor/mounting indicator)
        L.append("\n### %s: air plateau D [ppm] per overtone: %s; air Γ_hh [Hz]: %s\n" % (run, ", ".join("%.1f" % v for v in Pi["air"]["D"]), ", ".join("%.1f" % v for v in Pi["air"]["w"])))
    open(os.path.join(R, "datalogs.md"), "w").write("\n".join(L) + "\n")
    json.dump(summary, open(os.path.join(R, "datalogs.json"), "w"), indent=1, default=float)
    print("\n".join(L))


if __name__ == "__main__":
    main()
