"""
Regenerate the data figures of README.md.

Every number drawn here comes from the production code path: the baseline
polynomial order, the Savitzky-Golay window and order, the spline factor and
the -0.3 dB band threshold are read from ``Constants``, the chain is
``core/resonance.analyze_sweep`` and the wide-sweep peaks are found by
``CalibrationProcess``'s own detection functions.

Input: a directory of raw sweep dumps as written with OPENQCM_SWEEP_DUMP=1,
i.e. ``Calibration_5MHz.txt`` (1-51 MHz, 500 Hz step) and one sub-directory per
snapshot (``air_0`` ... ``ipa_2``) holding ``1.txt, 3.txt, ... 9.txt``
(frequency Hz, magnitude "dB", phase "deg"; 18 001 points, 1 Hz step).
The figures in the repository were made from the 2026-09-11 air -> water ->
isopropanol run: 5 MHz AT-cut sensor, TEC set point 25 degC, firmware 0.1.5c.

    cd software
    python ../docs/figures/make_readme_figures.py <dump directory>

Tested with the pinned environment (Python 3.9, numpy 1.21, scipy 1.7,
matplotlib 3.5).
"""

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "software"))

from openQCM.core import resonance                       # noqa: E402
from openQCM.core.constants import Constants as C        # noqa: E402
from openQCM.processors.Calibration import CalibrationProcess  # noqa: E402

OVERTONES = [1, 3, 5, 7, 9]
# Palette and rcParams of the impedance-analysis README figures
# (docs/impedance-analysis/figures/method/make_conductance_figure.py on that branch),
# media colours of its paper figures (research/paper/analysis/make_figures_v2b.py).
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SERIES = "#2a78d6"
SURFACE = "#ffffff"
RAW = MUTED
MEDIA = [("air", "Air", "#929292"),
         ("wat", "Water", "#2a78d6"),
         ("ipa", "Isopropanol", "#159570")]
OUT = HERE

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "mathtext.fontset": "dejavusans",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.linewidth": 0.8, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "path",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "legend.frameon": False, "legend.fontsize": 8.5, "legend.labelcolor": INK2,
    "lines.linewidth": 1.6,
})


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08, dpi=200)
    plt.close(fig)
    print("wrote", os.path.relpath(path))


def panel_label(ax, text):
    ax.set_title(text, loc="left", color=INK, fontsize=10, fontweight="bold", pad=8)


def header(fig, text, y=1.0):
    fig.text(0.0, y, text, color=INK2, fontsize=9, va="bottom", ha="left",
             transform=fig.transFigure)


def envelope(x, y, n):
    """Min/max decimation that keeps one-sample peaks visible."""
    m = len(y) // n * n
    xb = x[:m].reshape(-1, n)
    yb = y[:m].reshape(-1, n)
    xo = np.repeat(xb.mean(axis=1), 2)
    yo = np.column_stack([yb.min(axis=1), yb.max(axis=1)]).ravel()
    return xo, yo


def load_sweep(d, snap, n):
    return np.loadtxt(os.path.join(d, snap, "%d.txt" % n), unpack=True)


def chain(f, mag, coeffs):
    """The acquisition chain, as MultiscanProcess.elaborate_multi runs it."""
    corrected = mag - np.polyval(coeffs, f)
    filtered = resonance.savitzky_golay(corrected, window_size=C.SG_WINDOW_SIZE,
                                        order=C.SG_order)
    points = int(f[-1] - f[0]) + 1
    f_fine, fit = resonance.spline_fit(f, filtered, C.SPLINE_FACTOR, points)
    band = resonance.find_peak_and_band(f_fine, fit, C.THRESHOLD_DB)
    return corrected, filtered, f_fine, fit, band


def main(d):
    fc, mc, pc = np.loadtxt(os.path.join(d, "Calibration_5MHz.txt"), unpack=True)
    coeffs = np.polyfit(fc, mc, C.BASELINE_POLY_ORDER)
    coeffs_ph = np.polyfit(fc, pc, C.BASELINE_POLY_ORDER)
    mag_bc = mc - np.polyval(coeffs, fc)
    ph_bc = pc - np.polyval(coeffs_ph, fc)
    f1 = CalibrationProcess.peak_detection_qcm_fundamental(None, fc, mag_bc, ph_bc)
    fov = CalibrationProcess.peak_detection_qcm_overtones(None, fc, mag_bc, ph_bc, f1)
    peaks = np.concatenate([[f1], fov])

    # ---------------------------------------------------------------- Fig. 1
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.6), sharex=True,
                                 gridspec_kw={"hspace": 0.28})
    x, y = envelope(fc / 1e6, mc, 25)
    a1.plot(x, y, color=RAW, lw=0.6, rasterized=True, label="raw magnitude")
    a1.plot(fc / 1e6, np.polyval(coeffs, fc), color=INK2, lw=1.1, ls=(0, (4, 3)),
            label="polynomial baseline, order %d" % C.BASELINE_POLY_ORDER)
    a1.set_ylabel("magnitude (dB)")
    a1.legend(loc="upper left", ncol=2)
    panel_label(a1, "a  Raw magnitude and survey baseline")
    x, y = envelope(fc / 1e6, mag_bc, 25)
    a2.plot(x, y, color=RAW, lw=0.6, rasterized=True)
    for n, fp in zip(OVERTONES, peaks):
        i = np.argmin(abs(fc - fp))
        a2.plot(fp / 1e6, mag_bc[i], "o", ms=5, mfc="white", mec=SERIES, mew=1.4)
        a2.annotate("n = %d\n%.4f MHz" % (n, fp / 1e6), (fp / 1e6, mag_bc[i]),
                    xytext=(6, 2), textcoords="offset points", fontsize=8, color=INK)
    a2.set_ylabel("baseline-corrected (dB)")
    a2.set_xlabel("frequency (MHz)")
    a2.set_xlim(0, 52)
    a2.set_ylim(-7, 27)
    panel_label(a2, "b  Baseline-corrected magnitude and detected resonances")
    header(fig, "Peak Detection survey, 5 MHz sensor in air:  1–51 MHz,  500 Hz step,  %d points" % len(fc), 0.965)
    save(fig, "fig1_peak_detection.svg")

    # ---------------------------------------------------------------- Fig. 2
    f, mag, ph = load_sweep(d, "air_0", 1)
    corrected, filtered, f_fine, fit, band = chain(f, mag, coeffs)
    fc0 = f[0] + C.LEFT                      # tracking-window centre
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.4), sharex=True,
                                 gridspec_kw={"hspace": 0.28})
    a1.plot((f - fc0) / 1e3, mag, color=RAW, lw=0.5, rasterized=True, label="raw")
    a1.plot((f - fc0) / 1e3, np.polyval(coeffs, f), color=INK2, lw=1.1, ls=(0, (4, 3)),
            label="baseline (from the peak-detection sweep)")
    a1.set_ylabel("magnitude (dB)")
    a1.legend(loc="upper left")
    panel_label(a1, "a  AD8302 magnitude output, fundamental, air")
    a2.plot((f - fc0) / 1e3, ph, color=RAW, lw=0.5, rasterized=True)
    a2.set_ylabel("phase output (deg)")
    a2.set_xlabel("f − f$_c$ (kHz)     window: f$_c$ − %d kHz … f$_c$ + %d kHz, 1 Hz step, %d points"
                  % (C.LEFT / 1e3, C.RIGHT / 1e3, len(f)))
    panel_label(a2, "b  AD8302 phase output (reads 90° − |Δφ| + offset: maximum at resonance)")
    header(fig, "One tracking sweep of the fundamental in air, as received from the board:  %d points,  1 Hz step" % len(f), 0.965)
    save(fig, "fig2_raw_sweep.svg")

    # ---------------------------------------------------------------- Fig. 3
    fig = plt.figure(figsize=(8.6, 3.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[2.2, 1],
                          wspace=0.25, hspace=0.12)
    a1 = fig.add_subplot(gs[0, 0])
    a0 = fig.add_subplot(gs[1, 0], sharex=a1)
    a2 = fig.add_subplot(gs[:, 1])
    xr = (f - band.peak_frequency)
    a1.plot(xr / 1e3, corrected, ".", ms=1.2, color=RAW, rasterized=True,
            label="baseline-corrected")
    a1.plot(xr / 1e3, filtered, color=SERIES, lw=1.0,
            label="Savitzky–Golay (%d, %d)" % (C.SG_WINDOW_SIZE, C.SG_order))
    a1.set_ylabel("magnitude (dB)")
    a1.legend(loc="upper left", markerscale=6)
    plt.setp(a1.get_xticklabels(), visible=False)
    panel_label(a1, "a  Filtering over the whole window")
    a0.plot(xr / 1e3, corrected - filtered, color=RAW, lw=0.5, rasterized=True)
    a0.set_ylim(-0.25, 0.25)
    a0.set_ylabel("residual (dB)")
    a0.set_xlabel("f − f$_r$ (kHz)")

    w = 160
    sel = abs(xr) <= w
    selF = abs(f_fine - band.peak_frequency) <= w
    a2.plot(xr[sel], corrected[sel], ".", ms=2.5, color=RAW, label="baseline-corrected")
    a2.plot(f_fine[selF] - band.peak_frequency, fit[selF], color=SERIES, lw=2,
            label="spline fit (s = %g)" % C.SPLINE_FACTOR)
    thr = band.peak_value - C.THRESHOLD_DB
    a2.hlines(thr, -160, 160, color=INK2, lw=1, ls=(0, (3, 2)))
    a2.axvspan(band.leading_frequency - band.peak_frequency,
               band.trailing_frequency - band.peak_frequency,
               color=SERIES, alpha=0.10, lw=0)
    for fe in (band.leading_frequency, band.trailing_frequency):
        a2.plot(fe - band.peak_frequency, thr, "o", ms=5, mfc="white",
                mec=INK, mew=1.2)
    a2.plot(0, band.peak_value, "o", ms=6, mfc=SURFACE, mec=INK, mew=1.4)
    a2.annotate("f$_r$ = %.0f Hz" % band.peak_frequency, (0, band.peak_value),
                xytext=(8, 4), textcoords="offset points", fontsize=8, color=INK)
    a2.annotate("max − %.1f dB" % C.THRESHOLD_DB, (w, thr), xytext=(-2, 4),
                textcoords="offset points", ha="right", fontsize=8, color=MUTED)
    a2.annotate("", xy=(band.leading_frequency - band.peak_frequency, thr - 0.35),
                xytext=(band.trailing_frequency - band.peak_frequency, thr - 0.35),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    a2.text((band.leading_frequency + band.trailing_frequency) / 2 - band.peak_frequency,
            thr - 0.5, "Δf$_{0.3\\,dB}$ = %.1f Hz" % band.bandwidth,
            ha="center", va="top", fontsize=8, color=INK)
    a2.set_xlim(-w, w)
    a2.set_ylim(band.peak_value - 2.2, band.peak_value + 0.5)
    a2.set_xlabel("f − f$_r$ (Hz)")
    a2.legend(loc="upper left", markerscale=2)
    panel_label(a2, "b  Spline fit, peak and −%.1f dB band" % C.THRESHOLD_DB)
    header(fig, "Fundamental in air:  $f_r$ = %.0f Hz,  $\\Delta f_{0.3\\,dB}$ = %.1f Hz,  logged $D$ = %.2f$\\times10^{-6}$"
           % (band.peak_frequency, band.bandwidth, band.bandwidth), 0.965)
    save(fig, "fig3_processing_chain.svg")

    # ------------------------------------------------- results per medium
    res = {}
    curves = {}
    for key, _, _ in MEDIA:
        for s in range(3):
            snap = "%s_%d" % (key, s)
            for n in OVERTONES:
                fs, ms, _ = load_sweep(d, snap, n)
                _, _, ff, fit_, b = chain(fs, ms, coeffs)
                res[(key, s, n)] = (b.peak_frequency, b.bandwidth)
                if s == 0:
                    curves[(key, n)] = (ff, fit_, b)

    # ---------------------------------------------------------------- Fig. 4
    fig, axes = plt.subplots(1, 5, figsize=(10.5, 2.9), sharey=False,
                             gridspec_kw={"wspace": 0.32})
    for ax, n in zip(axes, OVERTONES):
        f_air = np.mean([res[("air", s, n)][0] for s in range(3)])
        for key, label, col in MEDIA:
            ff, fit_, b = curves[(key, n)]
            ax.plot((ff - f_air) / 1e3, fit_, color=col, lw=1.3, label=label)
        ax.set_xlim(-10, 4)
        ax.set_title("n = %d" % n, loc="left", fontsize=10, fontweight="bold", color=INK, pad=6)
        ax.set_xlabel("f − f$_{n,air}$ (kHz)")
    axes[0].set_ylabel("baseline-corrected,\nfitted magnitude (dB)")
    axes[0].legend(loc="upper left", fontsize=8)
    header(fig, "One sensor in air, water and isopropanol, TEC at 25 °C:  fitted, baseline-corrected magnitude of each overtone", 1.0)
    save(fig, "fig4_overtones_media.svg")

    # ---------------------------------------------------------------- Fig. 5
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.2), gridspec_kw={"wspace": 0.3})
    n_arr = np.array(OVERTONES)
    for key, label, col in MEDIA[1:]:
        df, dw = [], []
        for n in OVERTONES:
            fa = np.mean([res[("air", s, n)][0] for s in range(3)])
            wa = np.mean([res[("air", s, n)][1] for s in range(3)])
            df.append([(res[(key, s, n)][0] - fa) / n for s in range(3)])
            dw.append([(res[(key, s, n)][1] - wa) for s in range(3)])
        for ax, v in ((a1, np.array(df)), (a2, np.array(dw))):
            m = v.mean(axis=1)
            ax.errorbar(n_arr, m, yerr=[m - v.min(axis=1), v.max(axis=1) - m],
                        color=col, marker="o", ms=5, mfc="white", mew=1.4,
                        lw=1.2, capsize=2, label=label)
    a1.set_ylabel("Δf$_n$ / n (Hz)")
    a2.set_ylabel("Δ(Δf$_{0.3\\,dB}$) (Hz)")
    for ax in (a1, a2):
        ax.set_xlabel("overtone order n")
        ax.set_xticks(OVERTONES)
    a1.legend(loc="lower right")
    panel_label(a1, "a  Normalised frequency shift vs. air")
    panel_label(a2, "b  Band-width change vs. air")
    header(fig, "Published quantities, shift from the mean of three sweeps in air;  markers: mean of three sweeps,  bars: range", 0.965)
    save(fig, "fig5_liquid_loading.svg")

    # printed for the README text
    for key, label, _ in MEDIA:
        row = []
        for n in OVERTONES:
            fv = [res[(key, s, n)][0] for s in range(3)]
            wv = [res[(key, s, n)][1] for s in range(3)]
            row.append("n=%d f=%.0f bw=%.1f" % (n, np.mean(fv), np.mean(wv)))
        print(label, " | ".join(row))
    print("detected peaks (Hz):", peaks)
    print("air n=1 band:", band)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
