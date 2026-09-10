import json, sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
S = sys.argv[1]; summ = json.load(open(S + "/report/summary.json"))
rho_q, mu_q = 2648.0, 2.947e10                     # AT-cut quartz
liquids = {"WATER": (997.05, 0.890e-3), "IPA": (781.0, 2.038e-3)}   # 25 degC: rho [kg/m3], eta [Pa s]
n_list = [1, 3, 5, 7, 9]
lines = []; fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for j, liq in enumerate(("WATER", "IPA")):
    rho, eta = liquids[liq]
    f_air = np.array(summ["impedance"]["air_f"])          # measured f_n in air, impedance file
    f0 = f_air[0]
    kg_df = -np.sqrt(np.array(n_list)) * f0 ** 1.5 * np.sqrt(rho * eta / (np.pi * rho_q * mu_q))   # Kanazawa-Gordon, sqrt(n) scaling
    kg_dD_ppm = 2.0 * np.abs(kg_df) / (np.array(n_list) * f0) * 1e6                                # Newtonian: dGamma = |df|, D = 2 Gamma / f_n
    lines.append("### %s (rho = %.1f kg/m3, eta = %.3f mPa s at 25 degC)\n" % (liq, rho, eta * 1e3))
    lines.append("| n | KG df [Hz] | df impedance [Hz] | ratio | df amplitude [Hz] | ratio | KG dD [ppm] | dD impedance [ppm] | ratio | 'dD' amplitude (= width change at -0.3 dB, Hz) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, n in enumerate(n_list):
        di, ei = summ["impedance"][liq]["df"][i]; da, ea = summ["amplitude"][liq]["df"][i]
        Di, Ei = summ["impedance"][liq]["dD"][i]; Da, Ea = summ["amplitude"][liq]["dD"][i]
        lines.append("| %d | %.0f | %.0f ± %.0f | %.2f | %.0f ± %.0f | %.2f | %.1f | %.1f ± %.1f | %.2f | %.1f ± %.1f |" % (
            n, kg_df[i], di, ei, di / kg_df[i], da, ea, da / kg_df[i], kg_dD_ppm[i], Di, Ei, Di / kg_dD_ppm[i], Da, Ea))
    lines.append("")
    di = np.array([summ["impedance"][liq]["df"][i][0] for i in range(5)]); da = np.array([summ["amplitude"][liq]["df"][i][0] for i in range(5)])
    Di = np.array([summ["impedance"][liq]["dD"][i][0] for i in range(5)])
    a = ax[j]; a.plot(n_list, -kg_df, "k--", label="Kanazawa-Gordon -df"); a.plot(n_list, -di, "o-", color="#1f77b4", label="-df impedance (max of G)")
    a.plot(n_list, -da, "s-", color="#ff7f0e", label="-df amplitude (max of |Y|)"); a.plot(n_list, Di * (np.array(n_list) * f0) / 2e6, "^-", color="#2ca02c", label="dGamma from dD impedance (= dD f_n / 2)")
    a.set_title("%s: shifts vs overtone" % liq); a.set_xlabel("overtone n"); a.set_ylabel("Hz"); a.legend(fontsize=8); a.set_xticks(n_list)
fig.tight_layout(); fig.savefig(S + "/report/KG_comparison.png", dpi=110)
open(S + "/report/kg_tables.md", "w").write("\n".join(lines)); print("\n".join(lines))
