import sys, json, importlib.util
from pathlib import Path
import numpy as np
S = Path(sys.argv[1]); LOGO = Path(sys.argv[2]); OUT = S / "report"
spec = importlib.util.spec_from_file_location("gtr", S / "generate_test_report_py39.py"); gtr = importlib.util.module_from_spec(spec); spec.loader.exec_module(gtr)

# short-run parameters, stated in the report: 24 water points, 51 IPA, 100 air; baseline drifting ~-20 mHz/s
DET = dict(std_thr=2.0, roll_win=7, min_len=10); WIN = 12; MAX_DRIFT = 40.0
summary = {}
for tag, csv in (("amplitude", S / "tr_amp/2026-09-10_17-10-06_amplitude_multi_.csv"), ("impedance", S / "tr_imp/2026-09-10_17-10-06_impedance_multi_.csv")):
    df = gtr.load_data(csv)
    segs = gtr.detect_plateaus(df, **DET); mapping = gtr.classify_plateaus(df, segs)
    t = df["Relative_time"].values
    print("== %s: plateaus" % tag)
    for k, (a, b) in enumerate(segs):
        print("   #%d [%5.0f-%5.0f s] %-6s f0=%.1f drift=%+.1f mHz/s n=%d" % (k, t[a], t[b-1], mapping.get(k, "?"), df["Frequency_0"].values[a:b].mean(), gtr.plateau_drift(df, a, b), b - a))
    results, first = gtr.compute_differences(df, segs, mapping, win=WIN, max_drift=MAX_DRIFT, manual={})
    phases = gtr.classify_timeline(df, segs, mapping); rep = gtr.compute_repeatability(df, phases, win=WIN)
    pdf = OUT / ("Test_Report_NEXT_ID-1920_%s_2026-09-10.pdf" % tag)
    f1, f2, f3 = pdf.with_suffix(".fig.png"), pdf.with_suffix(".fig2.png"), pdf.with_suffix(".fig3.png")
    gtr.make_figure(df, first["AIR"], f1, phases=phases); gtr.make_overtone_figure(results, f2); gtr.make_ratio_figure(rep, f3)
    temp = float(df["Temperature"].mean())
    try:
        gtr.build_pdf(pdf, "openQCM-NEXT/TP-PTFE-A/F-15A", "1920", temp, f1, results, LOGO)
    except Exception as e:
        print("   (PDF skipped: %s)" % str(e).splitlines()[-1][:80])
    figures = [(f1.name, "time series"), (f2.name, "df, dD vs n"), (f3.name, "dD/|df| per phase")]
    gtr.build_markdown(pdf.with_suffix(".md"), "openQCM-NEXT/TP-PTFE-A/F-15A", "1920", temp, csv.name, results, rep, phases, df, level="pro", figures=figures)
    air_f = [float(np.mean(df["Frequency_%d" % ch].values[first["AIR"][0]:first["AIR"][1]])) for ch in range(5)]
    summary[tag] = {"air_f": air_f, "selected": {c: [float(t[a]), float(t[b-1])] for c, (a, b) in first.items()},
                    "WATER": {"df": [list(map(float, results["WATER"]["df"][ch])) for ch in range(5)], "dD": [list(map(float, results["WATER"]["dD"][ch])) for ch in range(5)]},
                    "IPA":   {"df": [list(map(float, results["IPA"]["df"][ch])) for ch in range(5)],   "dD": [list(map(float, results["IPA"]["dD"][ch])) for ch in range(5)]}}
    print("   selected:", summary[tag]["selected"])
    for liq in ("WATER", "IPA"):
        print("   %-5s " % liq + " | ".join("n%d df %+7.1f dD %7.2f" % (2*ch+1, results[liq]["df"][ch][0], results[liq]["dD"][ch][0]) for ch in range(5)))
json.dump(summary, open(OUT / "summary.json", "w"), indent=1)
