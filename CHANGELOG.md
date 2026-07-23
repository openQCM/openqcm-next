# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

## [v0.1.6G-test] — branch `impedance-analysis` (from v0.1.6-dev)
- Alternative impedance analysis via **conductance spectrum G(f)** derived from
  the AD8302 MAG/PHASE signals (software post-processing, same firmware).
- Core in `processors/Multiscan.py`; offline script `sweep_data/plot_conductance.py`.
- Note: approximate formula; development/DEBUG state. Not production-ready.

### Unreleased (impedance dev — 2026-07-21)
- **G DATA VIEW / `sweep_data/plot_conductance.py`** — offline-only additions
  (the live `Multiscan.py` pipeline is unchanged):
  - **Susceptance vs conductance (B–G) plots** — admittance locus per overtone.
    A raw `B = sin(phi)/|Z|` version (folded phase → "lens" shape), plus a
    **motional** version that reconstructs the *signed* phase (re-activated the
    unused `_phase_V_phase` unfold) and removes the baseline from G and B so the
    locus closes into the **admittance circle** (1:1 aspect via a new optional
    `_plot(..., aspect_equal=True)`).
  - **Exact complex-divider formula** (`_RX_exact`/`_G_exact`/`_B_exact`, from
    `docs/impedance-analysis/conductance-calculation.md`): inverts the divider
    `Z_q = M·e^{-j·phi} − R17` and computes `Y_q = 1/Z_q`. New "conductance
    (exact formula)" spectrum + exact admittance circle, side by side with the
    approximate ones. On real 5 MHz data the exact G_max is ~5× higher
    (physically plausible R_m), matching the synthetic prediction.
  - **Unit fix**: the "conductance shifted" plots were labelled mS but plotted S;
    now converted to mS.
  - ⚠️ **The "exact" formula is NOT yet validated against hardware** — the source
    doc `conductance-calculation.md` and its constants (R17, AD8302 slopes, V_CP,
    unfold heuristic) still need validation with known reference impedances; the
    synthetic test only proved algebraic self-consistency. See the doc's
    "VALIDATION STATUS" banner and `HANDOFF.md`.
  - ⏳ **Pending**: once validated, port the exact formula into
    `parameters_finder_impedance` (live pipeline) — this **will change the logged
    frequency/dissipation values**.
  - **Conditional phase unfold (liquid fix)** — new `_phase_signed()` used by the
    motional and exact B–G plots. The AD8302 outputs |phase| only; the previous
    always-unfold (`_phase_V_phase`: shift min→0 + flip after the minimum) is
    correct **only when the phase actually crosses zero** (air / low damping).
    In liquid the phase minimum stays 10–40° above zero (heavy damping, C0/stray
    dominated — no zero crossing): unfolding there subtracted a large real offset
    and inverted half the sweep, distorting the admittance locus into an **"S"**
    (observed on-device in liquid). `_phase_signed` unfolds only if
    `min|phase| < fold_threshold_deg` (default 5°; air minima ~0–2°, liquid
    ~10–40°), otherwise the raw phase already is the signed phase. Verified on
    synthetic BVD in both regimes: liquid exact G/B error 55%/121% → **0.000**,
    air unchanged. **Confirmed on-device**: the liquid B–G loci now close into
    circles (no more "S"). ⏳ A *systematic* test across the air→liquid transition
    (validating the `fold_threshold_deg` discrimination) is still to be run.
  - **Exact-formula fix + AIR VALIDATION (2026-07-23)** — root cause of the
    negative-resistance/negative-G circles found: the exact inversion was fed the
    **baseline-corrected** `V_MAG` (relative level; calibration polynomial
    subtracted), which scales `M = R17·10^((0.9−V)/0.6)` by `10^(Vb/0.6)` (0.55×
    at F0 → `M(res) < R17` → `R_q < 0` everywhere). **Fix**: new `amp_a_sp_raw`
    chain (same SG+spline, no baseline subtraction) feeds `_RX_exact`; the
    approximate path is untouched. The phase channel receives no baseline anywhere
    (verified offline + live) — correct for this method. Source PDFs confirm the
    divider topology and the INPB ×10 attenuation already compensated by the
    −0.6 V conversion offset. **On-device air validation (5 MHz)**: all exact
    circles at positive G; `R_m` = 10.6/12.1/40.5/76.5/132.6 Ω (F0→9th), `D` =
    3–10 ppm, circle-fit diameter = `G_max` within ±5% (rms 1–6%). The nominal
    constants are **rehabilitated**; remaining for metrology: phase systematics
    (esp. liquid) via reference-impedance calibration. Docs: rewritten
    "VALIDATION STATUS" banner in `conductance-calculation.md`.

## [v0.1.6-dev-073] — `main`
- GUI: buttons reorganized into an "Add-On" menu, Temperature/PID tab widget.
- Robustness: fallback when reading `PeakFrequenciesRT.txt`; exit confirmation.
- `data_view/main.py` refactor. Measurement logic unchanged.
- Firmware updated to **0.1.5a** (POT_VALUE 240, noise reduction).

## [v0.1.6-dev] — `main`
- **Automatic peak detection**: fundamental + overtones [3,5,7,9], auto-classifies
  the quartz @5MHz/@10MHz.
- **TEC current monitoring** (serial command "A").
- **Dark UI + real-time plot** performance (setData, 50 ms timer, TEC SecondWindow).
- Multi-start bugfix; Linux path separator fix.

## [v0.1.5] — `main`
- Production baseline, working and stable.
