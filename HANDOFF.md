# HANDOFF — `impedance-analysis` branch (openQCM NEXT)

> Developer notes specific to the experimental **conductance / impedance** branch.
> Working language: Italian in chat, English in the repo. Last updated: 2026-07-23.

---

## 0. Working context
- This is the **`impedance-analysis`** branch (tag `v0.1.6G-test`), checked out in a
  **git worktree** at `/Users/marco/claude_code/openqcm-next-impedance` (the `main`
  checkout lives separately at `/Users/marco/claude_code/openqcm-next`).
- ⚠️ **This branch is behind `main`**: it was branched from `v0.1.6-dev` and carries
  only the conductance feature. It does **not** have the later `main` work (serial
  connection refactor, responsive peak-detection cancellation, the whole **GUI
  redesign**, etc.). Aligning means `git merge main` from here — conflicts likely in
  `ui/mainWindow.py` and `processors/Multiscan.py`; plan it separately.

## 1. What the feature is
Impedance measurement via the **conductance spectrum G(f)** (and susceptance B) derived
from the AD8302 MAG/PHASE signals — pure software post-processing, same firmware/protocol
as the classic method.
- Live pipeline: `processors/Multiscan.py` — `parameters_finder_impedance()`, `_G_calc`,
  `_B_calc`, `_Zabs_Vmag`, `_phase_raw_V_phase`, wired in `elaborate_multi()` (publishes
  the conductance result; the classic lines are commented out). `elaborate_conductance_multi()`
  is dead code.
- Offline inspection: `sweep_data/plot_conductance.py`, launched by the **G DATA VIEW**
  button (`ui/mainWindow.py::_conductance_data_plot`).
- Docs: `docs/impedance-analysis/` — `conductance-calculation.md` (the "exact" formula,
  now carrying a VALIDATION STATUS banner), `openQCM_Next_G_Impedance_Analysis.md`, `sources/`.

## 2. Done this session (2026-07-21) — offline script only
In `sweep_data/plot_conductance.py` (the live `Multiscan.py` pipeline is UNCHANGED):
- **B–G admittance-locus plots**: raw (folded phase → "lens") + **motional** (signed phase
  via the re-activated `_phase_V_phase` unfold, baselines removed → closes into the
  **admittance circle**; 1:1 aspect via the new optional `_plot(..., aspect_equal=True)`).
- **Exact complex-divider formula** `_RX_exact`/`_G_exact`/`_B_exact` (from
  `conductance-calculation.md`): `Z_q = M·e^{-j·phi} − R17`, `Y_q = 1/Z_q`. New "conductance
  (exact formula)" + exact circle, shown alongside the approximate ones. On real 5 MHz data
  the exact `G_max` is ~5× the approximate → physically plausible `R_m`.
- **Unit fix**: "conductance shifted" plots were labelled mS but plotted S → converted to mS.
- **Conditional phase unfold — liquid fix** (`_phase_signed`, used by the motional and exact
  B–G plots): the always-unfold distorted the admittance locus into an "S" **in liquid**,
  where the phase minimum stays 10–40° above zero (no zero crossing → no fold to undo; the
  raw phase already is the signed phase). Unfold now happens only if `min|phase| <
  fold_threshold_deg` (default 5°, tunable). Verified on synthetic BVD in both regimes
  (liquid exact-G/B error 55%/121% → 0.000; air unchanged). **Confirmed on-device: the
  liquid B–G loci now close into circles** (no more "S"). ⏳ Still to do: a *systematic*
  test across the air→liquid transition to validate the `fold_threshold_deg` cut-off
  (air minima ~0–2°, liquid ~10–40°; the critical case is intermediate/viscous loads
  with min|phase| near the 5° threshold) — user is setting up that experiment.
  - ~~Empirical note: negative G on F0/3rd blamed on the nominal constants~~ — **superseded
    2026-07-23**: the real cause was a pipeline mismatch (see next bullet), the constants are fine.
- **Exact-formula fix + AIR VALIDATION (2026-07-23)**: the exact inversion was being fed the
  **baseline-corrected** `V_MAG` (relative level) while `M = R17·10^((0.9−V)/0.6)` needs the
  **absolute** divider level — the calibration-polynomial subtraction scaled `M` by `10^(Vb/0.6)`
  (0.55× at F0 → `M(res) < R17` → `R_q < 0` everywhere → the negative-G circles, reproduced to the
  decimal). **Fix**: `amp_a_sp_raw` chain (same SG+spline, no baseline subtraction) → `_RX_exact`;
  approximate path untouched. The **phase** gets no baseline correction anywhere (offline: SG+spline
  only; live: computed but never applied) — and that is *correct* for this method (off-resonance
  phase is DUT physics; board-phase systematics belong to reference-load calibration instead).
  Source PDFs confirm the divider topology; the INPB ×10 attenuation is already compensated by the
  −0.6 V decade offset in the ADC→V conversion. **On-device air validation (5 MHz)**: all exact
  circles at positive G; `R_m` = 10.6/12.1/40.5/76.5/132.6 Ω (F0→9th), `Γ` = 24–124 Hz,
  `D` = 3–10 ppm, circle-fit diameter = `G_max` within **±5%** (rms 1–6%), B/G span 0.98–1.17.

## 3. Validation status of the "exact" formula — VALIDATED IN AIR; metrological refinement open
The exact formula (from `conductance-calculation.md`) is now **validated on-device in air**
(2026-07-23, see §2): the earlier "negative G" evidence against it was a pipeline mismatch
(baseline-corrected `V_MAG`), not the model. Model topology and conversion levels are also
confirmed by the source PDFs (divider `Z_q`+`R17`; INPB ×10 attenuation compensated by the
−0.6 V conversion offset). The nominal constants (`R17 = 52.3 Ω`, 30 mV/dB, 10 mV/deg,
`V_CP = 0.9 V`) produce textbook-physical results in air.

**Still open (second-order systematics, mainly for liquid / metrological use):**
- board/cable **phase offsets** — in air the fold-unfold re-anchors the phase at resonance;
  in liquid there is no fold, so any constant phase error propagates into `R_q/X_q`;
- AD8302 nonlinearity near **phase ≈ 0°**; residual `ωC0` beyond the constant baseline
  (visible as B/G span ≤1.17 and slightly negative circle centers);
- the `fold_threshold_deg = 5°` cut-off across the air→liquid transition (systematic
  experiment planned by the user).

**How to refine:** measure **known reference impedances / RLC standards** vs a calibrated
impedance/network analyzer; de-embed board phase via a reference load.

## 4. Pending / roadmap (each needs a plan + approval before coding)
1. **Complete the validation** (§3): systematic air→liquid transition test (fold threshold)
   + reference-load calibration for metrological use. Air: DONE (2026-07-23).
2. **Port the exact formula into the live pipeline** (`parameters_finder_impedance` in
   `Multiscan.py`) — now a realistic option after the air validation. ⚠️ **This CHANGES the
   measured/logged values** (resonance frequency and dissipation in
   `logged_data/*_multi_.csv`) — must be a deliberate, documented step. Note it needs the
   RAW `V_MAG` (not the baseline-corrected one) exactly as fixed in the offline script.
3. Make the measurement **selectable** (classic vs conductance) instead of hard-wired in
   `elaborate_multi`.
4. Remove the **DEBUG** state (`constants.py`: `environment = 4`, `plot_autoscale_yaxis = True`).
5. Remove the dead `elaborate_conductance_multi`.
6. **Align with `main`** (`git merge main`).

## 5. Conventions
- PyQt5 **5.9.2**, Python 3.9.12; conda env. GUI not testable headless — static checks
  (`py_compile`, import) + on-device smoke test.
- Every change into `CHANGELOG.md`; commits use Conventional Commits + `Co-Authored-By`.
- Propose a plan and wait for approval before invasive changes (especially anything that
  changes the published/logged measurement).
