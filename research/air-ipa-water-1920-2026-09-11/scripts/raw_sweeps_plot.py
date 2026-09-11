"""Raw AD8302 sweeps as dumped (g<n>.txt: V_MAG and V_PHS in volts), no filtering, no spline.

    python raw_sweeps_plot.py <data_root> <out_dir>

One figure per quantity, one row per overtone, one column per phase (air / water / isopropanol), the
three hand-copied replicas of each phase overlaid. A third figure zooms the phase channel on +-3 kHz
around the sample maximum of V_MAG, where the resonance is.
"""
import sys, os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
N = (1, 3, 5, 7, 9); C = ["#2a78d6", "#eb6834", "#1baf7a"]
load = lambda s, n: np.loadtxt(os.path.join(ROOT, s, "g%d.txt" % n))

def panel(a, col, ylab, conv=None, zoom=None, title=None):
    pass

for what, col, ylab in (("vmag", 1, "V_MAG [V]  (attenuator undone)"), ("vphs", 2, "V_PHS [V]")):
    fig, ax = plt.subplots(5, 3, figsize=(17, 16))
    for j, (liq, sets) in enumerate(SETS.items()):
        for i, n in enumerate(N):
            a = ax[i, j]
            for k, s in enumerate(sets):
                g = load(s, n); f = (g[:, 0] - g[0, 0]) / 1e3
                a.plot(f, g[:, col], color=C[k], lw=0.7, alpha=0.85, label="%s  f₀ = %.0f Hz" % (s, g[0, 0]))
            a.set_title("%s, n = %d" % (liq, n), fontsize=9); a.legend(fontsize=7, loc="best"); a.grid(alpha=0.25)
            if j == 0: a.set_ylabel(ylab)
            if what == "vphs":
                a2 = a.secondary_yaxis("right", functions=(lambda v: (1.8 - v) / 0.01, lambda d: 1.8 - 0.01 * d)); a2.set_ylabel("|Δφ| = (1.8 − V)/0.01  [deg]", fontsize=8)
            if i == 4: a.set_xlabel("f − first sample of the sweep [kHz]  (window −12 / +6 kHz around the tracked peak)")
    fig.suptitle("Raw %s, board 1920, 2026-09-11, one sweep per file, 18 001 points at 1 Hz, no processing" % ("V_MAG" if what == "vmag" else "V_PHS"), fontsize=11, y=0.995)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "raw_%s.png" % what), dpi=95); plt.close(fig)

# zoom on the phase channel around the resonance (sample maximum of V_MAG), both channels
fig, ax = plt.subplots(5, 3, figsize=(17, 16))
for j, (liq, sets) in enumerate(SETS.items()):
    for i, n in enumerate(N):
        a = ax[i, j]
        for k, s in enumerate(sets):
            g = load(s, n); i0 = int(np.argmax(g[:, 1])); fc = g[i0, 0]; w = np.abs(g[:, 0] - fc) <= 3000
            a.plot(g[w, 0] - fc, g[w, 2], color=C[k], lw=0.8, label="%s: V_PHS  (max V_MAG at %.0f Hz)" % (s, fc))
            a.plot(g[w, 0] - fc, g[w, 1] + 1.0, color=C[k], lw=0.8, ls=":", label="%s: V_MAG + 1.0 V" % s if k == 0 else None)
        a.axhline(1.8, color="#888", lw=0.6, ls="--"); a.text(-2950, 1.805, "1.8 V = 0°", fontsize=7, color="#666")
        a.set_title("%s, n = %d" % (liq, n), fontsize=9); a.legend(fontsize=6.5, loc="best"); a.grid(alpha=0.25)
        if j == 0: a.set_ylabel("V [V]")
        if i == 4: a.set_xlabel("f − sample maximum of V_MAG [Hz]")
fig.suptitle("Zoom ±3 kHz around the V_MAG maximum: V_PHS solid, V_MAG + 1 V dotted (first replica only)", fontsize=11, y=0.995)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "raw_zoom_phase.png"), dpi=95); plt.close(fig)

# numbers: min / max / value at V_MAG max, per file
print("%-6s n | V_MAG min  max  at-peak | V_PHS min  max  at-peak  |dphi| at-peak [deg] | argmin V_PHS - argmax V_MAG [Hz] | points with V_PHS > 1.8 V" % "set")
for liq, sets in SETS.items():
    for s in sets:
        for n in N:
            g = load(s, n); i0 = int(np.argmax(g[:, 1])); i1 = int(np.argmax(g[:, 2]))
            print("%-6s %d | %+.3f %+.3f %+.3f | %.3f %.3f %.3f  %6.1f | %+6d | %d" % (s, n, g[:, 1].min(), g[:, 1].max(), g[i0, 1], g[:, 2].min(), g[:, 2].max(), g[i0, 2], (1.8 - g[i0, 2]) / 0.01, g[i1, 0] - g[i0, 0], int((g[:, 2] > 1.8).sum())))
