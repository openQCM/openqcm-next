# HANDOFF — `impedance-analysis` branch (openQCM NEXT)

> Developer notes specific to the experimental **conductance / impedance** branch.
> Working language: Italian in chat, English in the repo. Last updated: 2026-07-21.

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
  - Empirical note (air, real device): the exact formula produced **negative G** on the
    strongest modes (F0/3rd) — catastrophic cancellation `M·cosφ − R17` where `R_m` is small
    vs the nominal-constants error. Concrete evidence for the §3 calibration need. In liquid
    (`R_m ≫ R17`) the exact formula should be much less sensitive to this.

## 3. ⚠️ OPEN POINT — validate the "exact" formula (source of truth not yet trusted)
The "exact" formula was implemented from `conductance-calculation.md`, **but that document
and its assumptions are not yet validated against the real hardware.** The synthetic
Butterworth–Van Dyke test only proved the inversion is the **algebraic inverse of the assumed
forward model** (self-consistency) — it does NOT confirm the model/constants.

Still to validate:
- circuit model & constants: `R17 = 52.3 Ω`, AD8302 slopes `30 mV/dB` & `10 mV/deg`,
  `V_CP = 0.9 V`, divider topology — vs the actual board;
- AD8302 behaviour near **phase ≈ 0°** (nonlinear + sign-folded) and the **phase-unfold
  heuristic** (flip at the phase minimum);
- unmodelled parasitics.

**How to validate:** measure **known reference impedances / RLC standards** with the board,
compare recovered `R_q, X_q` (and `f_s, R_m, Q`) against a calibrated impedance/network
analyzer; then confirm or recalibrate slopes / `R17` / `V_CP`.

## 4. Pending / roadmap (each needs a plan + approval before coding)
1. **Validate the exact formula** (§3) — prerequisite for everything below.
2. **Port the validated formula into the live pipeline** (`parameters_finder_impedance` in
   `Multiscan.py`). ⚠️ **This CHANGES the measured/logged values** (resonance frequency and
   dissipation in `logged_data/*_multi_.csv`) — must be a deliberate, documented step.
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
