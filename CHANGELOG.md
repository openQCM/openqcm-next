# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

## [Unreleased] — `impedance-analysis`

### Fixed — ⚠️ MEASURED VALUES: global phase offset of the AD8302 phase channel (2026-07-28)
- **Root cause of the distorted admittance circles, and it is not what the first
  attempt said it was.** The detector's phase output carries a **global
  per-overtone offset** δ ≈ 7…17° (board + cable phase + detector offset):
  it reads `r(f) = |φ_true(f)| − δ`. Where the true phase crosses zero (air, low
  damping) the reading therefore **dives below zero**, down to −12°. That
  "impossible" negative reading is not a local overshoot — it is
  `min(r) = −δ`, the *signature* of the offset.
- **Two of my own earlier changes were wrong and are reverted.** The morning's
  "G from the folded phase" removed a real and necessary offset correction (the
  old `_phase_signed` shift by `−min(r)` was a crude but broadly correct
  estimator of δ). The afternoon's "fold-overshoot repair" (excision + PCHIP
  bridge) treated the *symptom* of a global offset as a local defect and, by
  pairing a raw G with a repaired B, made the displayed locus worse than before:
  circle residual 10–18 % of the radius against 1.6–3.1 % for the untouched old
  code. `_phase_repair` and the `PHASE_REPAIR_*` constants are gone.
- **The fix: estimate δ by requiring the locus to be a circle.** The
  Butterworth–Van Dyke model guarantees the admittance locus *is* a circle, so δ
  is simply the offset that makes it one — a coarse+fine search over closed-form
  Taubin fits on a decimated slice of the resonance band
  (`_phase_offset_deg`, ~3 ms per overtone against a multi-second sweep).
  This subsumes the old shift, its conditional fold threshold, and the offline
  reference fit's "rotation" parameter — which turned out to be the same physical
  quantity, found independently.

  Circle residual, as a fraction of the fitted radius, over five datasets:

  | strategy | air (4 datasets) | isopropanol |
  |---|---|---|
  | no correction (the reverted morning patch) | 4.1–14.6 % | 2.7–10.6 % |
  | `−min(r)` (the old shift) | 1.2–6.6 % | 4.5–17.6 % |
  | **δ from the circle fit** | **0.75–2.1 %** | **1.7–7.7 %** |

- **Guards, so the correction only applies where it is identifiable**: rejected if
  the best residual still exceeds `PHASE_OFFSET_MAX_RMS` (5 % of the radius) or
  if the optimum is pinned to a search bound. On the damped isopropanol overtones
  both fire, so those keep exactly their previously validated values; the
  fundamental there is corrected (δ = +7.5°, residual 1.8 %).
- **Validation.** On ideal synthetic data the estimator returns **−0.00°** and
  leaves accuracy untouched (err D −0.33 %, unchanged). With a **+12° offset
  injected** into the synthetic phase it recovers **+12.00°** and restores full
  accuracy (err f_r +0.0 Hz, err D −0.33 %); without the correction the same data
  gives err f_r −28 Hz and **err D +102 %**. Reproducibility across two
  independent acquisitions of the same hardware: δ within **0.5°**, f_r within
  **7 Hz**, R_m within **2.4 %**.
- **Effect on published values** (air, sensor S3): f_r moves −20…+2 Hz versus the
  broken intermediate state and now agrees with the offline Lorentzian fit to
  1–15 Hz; D = 9.3/2.8/3.6/4.3/5.0 ppm. Sensor S3 measures **0.89–1.07×** the S1
  reference R_m — a healthy crystal; the anomaly was entirely the phase channel.
- Diagnostics: the offset is printed once per overtone and again only on a drift
  above `PHASE_OFFSET_LOG_DEG` (3°), instead of the per-sweep flood the first
  attempt produced.
- **Known limit — δ is only weakly identifiable on some overtones.** On sensor S2
  (the partially recovered module) the reported δ oscillated between consecutive
  sweeps: the fundamental alternated 17.0° / 15.4° / 16.9°, the 3rd 15.8° / 16.7°.
  This is not noise in the data but the shape of the objective: the
  residual-vs-δ valley is **1.25–1.75° wide** where the crystal is clean, and
  **3.5–6.5° wide** where the residual floor is high (S2's F0 floor is 2.4 % of
  the radius against 0.8 % on S1), so ±0.8° of sweep-to-sweep noise moves the
  minimum without meaningfully changing the fit. Consequences on published values
  over the observed 1.6° wander are small — **1 Hz** on `f_r`, **−2.5 %** on `D`,
  **+4.7 %** on `R_m` — and `f_r` still agrees with an independent Lorentzian fit
  to **0.007–0.32 ppm**. Averaging δ across sweeps would remove the jitter and is
  recorded as a roadmap item, not applied: it introduces cross-sweep state and
  shifts published values, so it needs a decision.

### Fixed — ⚠️ MEASURED VALUES (verification round, 2026-07-27)
- **Attenuator compensation was 0.600 V instead of 0.61069 V.** The ADC→V
  conversion has to undo the INPB R11/R19 attenuator, and that is **not** one
  clean decade: k = (47.0 + 4.99)/4.99 = 10.4188 = 20.3564 dB, which at
  30 mV/dB is 0.61069 V. The hardcoded 0.600 undid exactly 20.000 dB and left
  0.3564 dB uncompensated, underestimating M = |Z_q + R17| by **4.02 %**. The
  inversion amplifies that by (1 + R17/R_m), because `R_q = M·cosφ − R17` is a
  difference of close numbers at resonance: up to **−22 %** on R_m at the
  fundamental in air. Now derived from the schematic values in
  `Constants.V_MAG_DECADE_OFFSET` instead of hardcoded, and applied at **both**
  conversion sites — `_Vmag_bit_mag` (the published path) and the one inside
  `run()` that writes `g<n>.txt` (the offline reference), which had drifted apart.
  Confirmed by a synthetic THRU (Z_q = 0.001 Ω through the full forward model):
  M read **50.199 Ω** before and **52.301 Ω** after, against a true 52.30 Ω.
- **The conductance is no longer routed through the phase unfold.** G is *even*
  in φ, so it must be computed from the phase exactly as the AD8302 emits it —
  folded. `_phase_signed` does more than flip the sign: it also **shifts** the
  phase by its minimum, and that shift is not sign-symmetric. Sending G through
  it biased the published dissipation by **+6 to +20 %** in air while doing
  nothing about a sign ambiguity G is already immune to. B keeps the signed
  phase, which is the only quantity that genuinely needs it.

  **Combined effect on the published values**, measured on the frozen datasets.
  The two fixes push D the same way, they do not cancel:

  | n | D air before → after | D isopropanol before → after |
  |---|---|---|
  | 1 | 25.08 → 29.74 ppm | 387.1 → 380.1 ppm |
  | 3 | 5.58 → 6.89 ppm | 194.4 → 194.7 ppm |
  | 5 | 5.42 → 6.71 ppm | 146.1 → 146.3 ppm |
  | 7 | 4.86 → 5.65 ppm | 123.8 → 123.9 ppm |
  | 9 | 5.61 → 6.04 ppm | 112.6 → 112.7 ppm |

  `f_r` moves ≤ 13 Hz. R_m rises 7–11 % in air (the direction the underestimated
  M predicted). In liquid the unfold does not fire for n ≥ 3, so only the
  constant contributes there.

  Verification harness: synthetic BVD through the reference forward model
  (attenuator k, Z2_eff, AD8302 transfer functions, ×2/×1.5 buffers, 12-bit ADC)
  into the real `MultiscanProcess` methods. Isolating the formulas, air now gives
  **f_r 0.00 Hz, D −0.34 %, G_max −1.43 %** against analytic truth; the residual
  G_max offset is the R17-vs-Z2_eff item, still open.

### Changed — ⚠️ MEASURED VALUES
- **The published resonance frequency and dissipation now come from the EXACT
  complex-divider inversion.** `elaborate_multi` computes `Y_q = 1/(M·e^{-jφ} −
  R17)` once from the RAW absolute `V_MAG` and the signed phase, and reads f_r
  and Γ off that conductance via the new
  `parameters_finder_impedance_exact()`. The old
  `parameters_finder_impedance()` (approximate `G = cosφ/|Z|`, fed the
  baseline-corrected `V_MAG`) is no longer called. The panel and the datalog now
  share one computation, so they cannot disagree.
- **The half-bandwidth is measured two-sided and interpolated**
  (`_half_bandwidth_G_exact`). The old one returned `f_r − f_left`, correct only
  for a symmetric peak — the real one is skewed by the residual C0 branch — and
  snapped the crossing to the 1 Hz grid, which quantised D by a few percent when
  Γ is a few tens of hertz. Falls back to one-sided when the sweep window holds
  no crossing on a side, which happens on damped loads.

  **Impact, measured on real data.** `f_r` moves by at most 71 Hz (≤1.6 ppm).
  `D` changes a lot, and for the better:

  | | air, D before → after | isopropanol, D before → after |
  |---|---|---|
  | n=1 | 68.4 → 25.1 ppm | 386 → 387 ppm |
  | n=3 | 24.3 → 5.6 ppm | 227 → 194 ppm |
  | n=5 | 17.0 → 5.4 ppm | 183 → 146 ppm |
  | n=7 | 12.7 → 4.9 ppm | 152 → 124 ppm |
  | n=9 | 11.8 → 5.6 ppm | 140 → 113 ppm |

  In air the formula dominates (D falls 2–3×) and the two-sided window adds a
  further ~20 %; in liquid the formula contributes ~5 % and the window ~15–20 %.
  The new values are the physical ones: ~5 ppm on the overtones in air is
  textbook for a good 5 MHz crystal, and 387 ppm at the fundamental in
  isopropanol matches the Kanazawa–Gordon prediction (~400 ppm). The old
  approximate values were inflated 2–4× in air.
  **A pre-change and a post-change datalog are not comparable.**

### Performance
- **The impedance panel no longer dominates the GUI.** It was recomputing and
  redrawing on every `plot_update_ms` tick (20 Hz) data that only changes once
  per sweep. Three fixes: a per-overtone revision counter so the panel repaints
  only on new data (the selector state is part of the key, so toggling an
  overtone still responds at once); the list→array conversion moved to the
  consumer, done once per sweep instead of 20 times a second; and one overtone
  per queue message instead of re-sending all five lists on every
  `elaborate_multi` call, cutting the queue payload and pickling cost 5×.
  Measured on five overtones × 3000 points: steady-state cost per tick
  **≈5 ms → ≈1 µs**, i.e. from ~10 % of the 50 ms budget to nothing.

### Added
- **Live impedance panel** — a right-hand dock in the main window with two
  real-time views, both computed with the **exact** complex-divider inversion:
  - **Conductance G(f)**, all overtones overlaid, x plotted as the offset from
    the detected peak so every overtone shares one axis;
  - **Admittance circle B vs G**, all overtones overlaid, aspect-locked so a
    circle looks like a circle.

  Per-overtone colours match the frequency/dissipation plots, the scan selector
  is honoured (deselected overtones disappear here too), and both views join the
  existing right-click menu (grid, autoscale, reset zoom) and the light/dark
  theme. The panel is collapsible, and the two plots sit in their own vertical
  splitter so either can take the whole height.

  The exact formula (`_phase_signed` / `_RX_exact` / `_G_exact` / `_B_exact`,
  ported from `sweep_data/plot_conductance.py`) runs in `elaborate_multi` on a
  new RAW absolute `V_MAG` chain. It arrived as a display-only path — at that
  point `parameters_finder_impedance()` still published the logged values from
  the approximate formula, and the offline regression fixture confirmed nothing
  had moved. It is now also the **published** path: see "Changed — MEASURED
  VALUES" above.

  Data path mirrors the existing `A_multi` channel: `Multiscan` →
  `Parser.add_GB_multi` → `Worker.consume_queue_GB_multi` →
  `get_G_exact_buffer` / `get_B_exact_buffer` / `get_F_G_values_buffer` → GUI.
  The queue argument is optional, so an older `ParserProcess` call signature
  still works and `add_GB_multi` degrades to a no-op. The whole computation and
  the panel refresh are wrapped in try/except: a diagnostic view must never take
  down an acquisition.
- `Constants.FOLD_THRESHOLD_DEG_G` (5.0) — the air/liquid discriminator for the
  conditional phase unfold, previously hard-coded in the offline script.
- **Impedance panel tuned for damped (liquid) loads.** On an isopropanol
  acquisition the displayed circles came out visibly distorted. Three changes,
  all display-side:
  - **Adaptive window** (`IMPEDANCE_PANEL_BAND_GAMMA`, default 3.0): the
    producer now clips each spectrum to a few half-bandwidths around resonance
    before shipping it. In air the sweep spans ±50 to ±190 Γ and almost all of
    it piles onto one spot of the locus; in a liquid Γ grows to ~1–2.5 kHz and
    the far points are exactly the ones acquired deepest in the AD8302
    dynamic-range corner. Also cuts the queue payload and the redraw cost.
  - **Fitted-circle overlay** (`IMPEDANCE_PANEL_SHOW_FIT`): a dashed circle per
    overtone, so the circle the data supports stays visible even when the raw
    locus is out of round — and its diameter is a far more robust 1/R_m than
    the peak of G.
  - **The fit runs on the core, not on everything plotted**
    (`IMPEDANCE_PANEL_FIT_GAMMA`, default 1.0). Past about one half-bandwidth
    the deviation from a circle is *systematic*, not sporadic, so on a damped
    load a majority of a ±3 Γ window is off-circle and residual-based outlier
    rejection locks onto the wrong subset (measured: −36 % error on R_m at the
    3rd overtone). Fitting the core instead reproduces the offline reference
    within **+0.5 % to +6.6 %** in air and isopropanol alike. `f_r` and Γ now
    travel with the spectrum so the panel knows where the core is; both are
    optional in the payload, so an older producer still unpacks.

### Validated
- **The 5° conditional-unfold threshold is confirmed across the air→liquid
  transition** — the systematic test left open in the handoff. In isopropanol
  the fundamental sits at min|φ| = 2.04°, the critical intermediate case, and
  the rule correctly unfolds it (circle rms 0.52 % vs 33.4 % if left folded),
  while the 3rd to 9th (12.1° to 43.8°) are correctly left alone (e.g. 1.06 %
  vs 2.49 % on the 7th). Right call on all five overtones, in both regimes.

### Changed
- **Aligned with `main`** (merge of `main` @ 52a42a9, 47 commits; pre-merge state
  tagged `v0.1.6G-pre-merge`). The branch now carries the whole `main` line —
  `run.py` entry point, serial connection Steps 1–2, `requirements.txt` /
  `environment.yml`, the GUI redesign (programmatic UI builder + dark/light theme),
  robust trimmed-mean averaging, responsive calibration cancellation, firmware
  `0.1.5a` and `docs/DATA_FORMAT_sweep_data.md` — on top of the conductance feature.
- ⚠️ **Logged values will shift**: main's `trim_mean` replaces the
  Savitzky-Golay + `np.average` on the acquisition ring buffer, and now averages the
  **conductance-derived** frequency and dissipation. By design, not a regression —
  but a pre-merge and a post-merge `logged_data/*_multi_.csv` are not directly
  comparable.
- **G DATA VIEW moved to the menu bar**: **Tools → Conductance Data**
  (`actionConductance_Data`). The old sidebar button is gone — main's redesign
  removed that whole family of buttons in favour of the menu. The handler
  `_conductance_data_plot` is unchanged.
- **DEBUG state removed** (roadmap item, closed by the merge): `environment` back to
  `10`; `plot_autoscale_yaxis` dropped in favour of main's `plot_force_yrange`,
  which gates the same forced Y-range with inverted polarity.
- `Calibration_{5,10}MHz.txt` and `PeakFrequencies{,RT}.txt` now hold the **5 MHz**
  sensor module currently mounted (they previously described a 10 MHz crystal).
  These are runtime output, rewritten by `Calibration.py` on every calibration run.

### Added
- **`g<n>.txt` documented** in `software/docs/DATA_FORMAT_sweep_data.md`: the second
  sweep family written by this branch — same layout as `<n>.txt`, but columns 2–3 are
  the **raw AD8302 voltages** V_MAG / V_PHS instead of dB / degrees. Includes the ADC→V
  conversion, the divider inversion it feeds, and the two traps (never baseline-correct
  V_MAG before the exact inversion; column 3 is `|phase|`, sign folded).
- Example `g<n>.txt` sweeps versioned alongside main's `<n>.txt`, for the same reason
  main versions those: the Conductance Data view needs input on a fresh clone.

### Removed
- The three dead Qt-Designer UI files (`res/mainWindow_new.ui`,
  `res/mainWindow_new_ui.py`, `ui/mainWindow_new_ui.py`). Nothing has imported them
  since the GUI redesign; they only generated merge conflicts.

### Verified
- Offline path **byte-identical** across the merge (`plot_conductance.py`,
  `fileStorage.py`), and offline results identical to the pre-merge baseline to the
  last digit. `py_compile` clean across the package.
- ⏳ **Not yet verified**: on-device smoke test (acquisition, Tools → Conductance Data)
  and the logged-value comparison.

## [Unreleased] — `main`

### Added
- ⚠️ **TEST-ONLY firmware variant (no-TEC board)** — _internal, temporary; to be removed._
  New Teensy sketch `firmware/openQCM_Next_py_0.1.5a_TEST_teensy/` (version `0.1.5a-TEST`)
  for a special openQCM NEXT board built for testing that **does not mount the
  temperature-control (TEC) section** (no MTD415T on Serial1, no MCP9808, no fan / enable /
  status / control-switch pins). It strips every Serial1/MTD415T interaction (which would
  otherwise block ~250 ms per query on a board with no TEC), keeps the DDS/ADC sweep engine
  identical to production, and **simulates the temperature** (stable `25.00 °C` baseline with
  a slow ±`0.05 °C` wobble; optional real Teensy die temperature via `#define USE_INTERNAL_TEMP`).
  The end-of-measurement line stays fully host-compatible — `temperature;status(0);error(0);s` —
  so **no software change is required**; TEC commands (`T/C/P/I/D/L/X/A/E`) are accepted as
  benign no-ops. Compiles clean for Teensy 4.0. **This is a throwaway variant for internal
  bench testing and will be deleted once the test board is retired — do not build on it.**
- **Pinned dependencies for reproducible setup**: `software/requirements.txt` (pip) and
  `software/environment.yml` (conda). Tested on Python 3.9.12; PyQt5 pinned to 5.9.2
  (the GUI relies on the classic QtGui widget namespace).
- **Serial connection as a separate feature (Step 1)**: dedicated **Connect / Disconnect**
  and **Refresh** buttons (in the Start/Stop row), decoupled from the operation-mode selection.
  - **Refresh** rescans connected devices (serial ports) on demand; disabled while connected.
  - Multi-instance protection via a per-port lock file (`fcntl` on Unix, skipped on
    Windows where COM ports are natively exclusive).
  - On connect the port is validated (open/close probe) and the **firmware version
    check runs here** (moved from the blind call at application startup).
  - **START is now gated on an active connection** (`_enable_ui`), and the port
    combo box is disabled while connected. Connection status shown in `label_COM_status`.
- **Serial connection — Step 2**: the connection now holds a **persistent, exclusive**
  serial handle (`_serial_lock`) while idle (Standby). The GUI serial queries (set
  temperature, TEC on/off, PID, firmware version) go through it via `_serial_write` /
  `_serial_query` instead of opening the port ad-hoc; the port is **handed over** to the
  acquisition process on START (handle closed) and **re-acquired** on STOP.
- **GUI theme system (dark/light)** — first phase (Phase 0) of the GUI redesign inspired by
  openQCM Q-1 v3.0. New `ui/theme.py` (`LIGHT`/`DARK` palettes + a parameterised Qt Style Sheet
  builder + per-theme pyqtgraph plot colors) and a **View → Theme → Light/Dark** menu in
  `ui/mainWindow.py` (`_setup_theme_menu`, `_apply_theme`, `_apply_plot_theme`). The whole window
  (controls, group boxes, tabs, menus, readout fields) and the plots (background, axes, titles)
  follow the active theme; accent blue `#008EC0` and dissipation brown `#DD8E6B` stay fixed on both.
  The choice persists in `QSettings('openQCM','NEXT')` (default light on first run). The per-overtone
  readout fields (`F0`..`D9`, temperature indicator) were migrated from hardcoded white inline styles
  to QSS objectName rules so they theme correctly.
- **GUI single-window shell (QSplitter)** — Phase 1 of the GUI redesign. `_build_shell()` in
  `ui/mainWindow.py` (called at the end of `__init__`) re-parents the fixed two-column grid into a
  horizontal `QSplitter`: a scrollable, collapsible left sidebar of control groups (brand, connection,
  F/D readouts, overtone selector, sampling, Temperature/PID tab, with the action row + status pinned
  to the bottom) and the plots on the right. Widgets are moved as-is (objectNames + signal wiring
  preserved), so it composes with the theme and all existing behaviour; commenting out the
  `_build_shell()` call reverts to the old layout. **⚠️ Visual layout tuning is still pending** (see
  HANDOFF §5): the action-button row is cramped in the narrow sidebar and needs rearranging.
- **Scientific menu wiring (GUI redesign Phase 5)** — completes the File/View/Tools/Help menu.
  `Help → Help` now opens the openQCM NEXT software webpage (replacing the `dummy` placeholder) and a
  new `Help → About openQCM NEXT` dialog shows name/version/description + link; `View` gained
  show/hide toggles for the **Sidebar** (`sidebarScroll`) and the bottom **Status bar**
  (`statusBarFrame`). File→Quit, View→Theme/Δ Cursors, Tools→Raw/Log/Tec, Help→Firmware/Software were
  already wired. This closes the phased GUI redesign (Phases 0–5).
- **GUI refinement pass (main window)** — visual/UX polish on top of the phased redesign:
  - Single **temperature ON/OFF toggle** replacing the two buttons: blue "ON" (enable) / brown "OFF"
    (disable), enabled only while the serial port is connected, kept in sync with the firmware TEC
    status during acquisition (`_toggle_temperature_control` / `_update_tec_toggle` / `_tec_on`).
  - Unified **"secondary" outline button style** (blue outline; brown for a toggle's deactivate state
    — Disconnect, temperature OFF; grey outline when disabled) applied to Connect/Disconnect, Refresh,
    the plot controls, T SET and TEC Reset; each sized to its label (trailing stretch) so it no longer
    fills the sidebar width.
  - **Renames**: Autoscale → AUTO, Set/Clear Reference → SET REF / UNSET REF, Clear Plots → CLEAR,
    Temperature Set → T SET.
  - **Card titles** rendered bold (set on the `QGroupBox` widget font — Qt ignores font-weight on the
    `::title` subcontrol — with the card content reset to normal weight).
  - **Start / Stop** button: larger (17 px, not bold) with minimalist outline glyphs (▷ play / □ stop).
  - **Plot Controls** card anchored just below Temperature (the sidebar stretch now sits between it
    and the Start/Stop button).
  - Removed redundant sidebar captions ("Serial COM Port", the "Connected: …" status label,
    "Operation mode", "Frequency (single mode)"); the **frequency selector is shown only in Single
    Measurement**.
  - **Sidebar**: correct default width (300 px), smoothly resizable (260–400 px); the rich-text brand
    label now wraps so it no longer forces a ~459 px minimum that clipped the column.
  - **Temperature card** redistributed: the setpoint spinbox and the live temperature indicator are
    aligned to the right margin with an expanding gap.
- **GUI System Log tab (Phase 2 of the GUI redesign)** — the center pane is now a `QTabWidget`
  (`centerTabs`) with **Plots** and **System Log** tabs. The plots are re-parented as-is into the
  Plots tab (no widget recreated); the System Log tab hosts a read-only `QTextEdit` (`systemLog`)
  fed by a new `LogStream` class that mirrors the **main process's** `stdout`/`stderr` into the
  widget with `[HH:MM:SS]` timestamps while still forwarding to the original streams (terminal +
  rotating log file unaffected). Installed in `__init__` right after `_build_shell()`, restored in
  `closeEvent`. Theme-aware, monospace (`QTextEdit#systemLog` rule added to `ui/theme.py`). Scope:
  captures main-process `print()`; child-process (Serial/Multiscan/Calibration) prints and
  `logging`-module messages are not intercepted (they keep going to terminal / log file). Adapted
  from openQCM Q-1 v3.0.
- **GUI single Start/Stop toggle (Phase 3a of the GUI redesign)** — the separate Start and Stop
  buttons are merged into one toggle on `pButton_Start`: it runs `_toggle_start_stop()` (Stop if
  acquiring, else Start), stays enabled while running (gated only on an active serial connection),
  and shows **Start** (green) / **Stop** (red) via a `running` dynamic property + `unpolish/polish`
  and theme QSS (`#pButton_Start` in `ui/theme.py`). The visual state flips inside `_enable_ui`, so
  it tracks every idle↔running transition (start / stop / normal completion / calibration cancel).
  The old `pButton_Stop` is hidden and the inline stylesheet on `pButton_Start` is dropped so the
  toggle follows the theme. Adapted from openQCM Q-1 v3.0.
- **GUI datalog filename display (Phase 3d of the GUI redesign)** — while acquiring, the active
  CSV filename is shown in the sidebar (new runtime `lblLogFile` label, middle-elided with the full
  name as tooltip, accent-colored via theme QSS) and appended to the window title; both are cleared
  on Stop. A new `Worker.get_csv_filename()` getter mirrors the names composed by the datalog loop
  (serial: `<ts>_<overtone>.csv`, multiscan: `<ts>_multi_.csv`; calibration returns an empty string
  → label hidden). Adapted from openQCM Q-1 v3.0.
- **GUI theme-aware program status pill (Phase 3c of the GUI redesign)** — the `infostatus` label
  is now styled through a `_status_pill(key)` helper (`standby`/`warn`/`err`/`ok`): the standby
  state follows the active theme palette (fixing the light pill stuck on the dark theme), while the
  warning/error/ok states keep their yellow/red/green backgrounds with forced dark text; all 15
  inline `setStyleSheet` call sites were converted. Status texts drop the hardcoded black
  `<font>` HTML in favour of a `● Program Status: …` prefix whose dot/text color comes from the
  pill stylesheet. A theme switch re-applies the current pill (`_apply_theme` remembers the last
  state via `_status_key`); the "Stanby" typo is fixed. `infobar` message colors are unchanged.
- **GUI overtone quick-select buttons F0–F9 (Phase 3b of the GUI redesign)** — five compact
  checkable buttons replace the legacy overtone radio row visually (the hidden radios remain the
  source of truth for `scan_selector`, so the plotting/readout logic is untouched). Behaviour by
  mode: **multiscan** = multi-select, purely-visual curve filter, live during acquisition (all
  overtones are always acquired); **serial** = exclusive selection that drives `cBox_Speed` (the
  combo lists the calibrated overtones in reverse order) with bidirectional sync, idle-only;
  **calibration** = disabled. Styled via `overtoneBtn` property QSS (accent when checked, kept on
  `:checked:disabled`). Adapted from openQCM Q-1 v3.0 with the NEXT-specific multiscan semantics.
- **GUI sidebar action-area layout (Phase 3e of the GUI redesign)** — resolves the cramped
  action row flagged in Phase 1: **Refresh + Connect** move into the connection card as its bottom
  row (`gridLayout`), styled by theme QSS objectName rules instead of their former inline
  stylesheets; in `_build_shell` the legacy action row is decomposed — the plot controls
  (Reference / Clear) keep the old row, while the **Start/Stop toggle gets its own prominent
  full-width row** (min-height 34) with the **progress bar underneath**, followed by the status
  labels at the sidebar bottom.
- **Responsive, clean cancellation of Peak Detection (calibration)** — ported and adapted
  from the more mature openQCM Q-1 v3.0. The peak-detection sweep can now be stopped mid-run
  without a hard process kill or a corrupt serial state, replacing the previous behaviour where
  the **Stop** button was disabled for the whole (~1 min) sweep.
  - `processors/Calibration.py`: the inner sweep-read loop now polls `self._exit`
    (`while not self._exit.is_set()`) with a short `0.1 s` serial read timeout, so a Stop
    interrupts within ~0.1 s instead of blocking on `serial_timeout_ms` (4 s). On cancellation
    mid-sweep (`_exit` set with `k < calib_sections` and no acquisition error) it emits a `-1`
    sentinel on `parser5` and returns, skipping peak detection / file storage. On start it drains
    any bytes left over from a previously interrupted run before sweeping.
  - `core/worker.py`: latches the `-1` sentinel in `_queue_data5` into `_calibration_cancelled`
    (exposed via `is_calibration_cancelled()`, reset each `start()`); `stop()` now shuts the
    peak-detection process down gracefully (`join` first, `terminate()` only as a fallback) so the
    serial port is released cleanly. Measurement modes (serial/multiscan) keep the direct terminate.
  - `ui/mainWindow.py`: the **Stop** button is no longer disabled during peak detection; the
    calibration branch of `_update_plot` checks `is_calibration_cancelled()` first and tears down
    once; `stop()` reports **"Peak Detection Cancelled"** when invoked during calibration.
    Fixed a latent `AttributeError` this exposed: `stop()`'s legend-removal loop read
    `self._overtones_number_all`, which was only set for serial/multiscan — undefined in
    calibration mode, where `stop()` was previously unreachable (Stop disabled). It is now
    initialised to `0` in `__init__` (and in the calibration `start()` branch), so the loop is a
    no-op. Without this, pressing Stop mid-peak-detection raised before `worker.stop()` ran and the
    sweep continued to completion.

### Added
- **GUI plot interactions (Phase 4 of the GUI redesign)** — adapted from openQCM Q-1 v3.0, on
  NEXT's **two separate** frequency / dissipation panels (single dual-axis panel explicitly
  rejected):
  - **Grid off by default** everywhere (the phase overlay's grid was the only one still on) with a
    per-plot **Show/Hide grid** toggle (`alpha 0.3`; the amplitude and phase-twin grids toggle
    together).
  - **Custom right-click menu** on all four plots (amplitude/phase, temperature, frequency,
    dissipation): Auto-scale, Reset zoom, mouse pan/select-zoom mode switch, grid toggle — one
    `sigMouseClicked` handler per pyqtgraph scene with viewbox hit-testing (the default pyqtgraph
    menus were already suppressed).
  - **Δ cursors on the frequency and dissipation panels**: two movable time cursors per panel
    (amber/green) with a live readout of `Δt` (the axis carries epoch µs → seconds) and `ΔF` (Hz)
    or `ΔD` (ppm) computed by nearest-sample lookup on the plotted buffers (multiscan → the
    fundamental, single mode → the measured overtone, same convention as the status bar). Toggled
    per-panel from the right-click menu or globally via the new **View → Δ Cursors (F / D)**
    checkable action (state kept in sync). Cursor items are parented to the ViewBox with
    `ignoreBounds` so they survive `clear()` and never drive the autorange.
  - Min-Y-scale enforcement deferred by decision.

### Changed
- **GUI palette reduction — Start/Stop toggle now blue/brown** — moving toward a two-color palette
  (openQCM blue `#008EC0` + brown `#DD8E6B`): the Start/Stop toggle is **blue when idle (Start)**
  and **brown when running (Stop)** instead of red. Added `brown` / `brown_hover` palette keys
  (`ui/theme.py`, `#DD8E6B` on both themes). The remaining state colors (status pill yellow/red/
  green) are left for a follow-up pass.
- **GUI center: collapsible amplitude/temperature pane + per-plot readout cards** — the Plots tab
  is now a vertical `QSplitter` (`plotSplitter`): the amplitude/phase-sweep + temperature canvases
  sit on top and can be **collapsed/hidden by dragging the handle** (`setCollapsible(0, True)`);
  the frequency and dissipation plots take the bottom pane. The per-overtone F/D readouts moved out
  of the sidebar "Current Readings" card into two **horizontal cards above their plots**:
  "Frequency (Hz)" above the frequency plot (F0..F9 + color swatches) and "Dissipation (ppm)" above
  the dissipation plot (D0..D9 + swatches). Readout widget names are unchanged (`F0..F9` / `D0..D9`
  / `label_F*_col`; new `label_D*_col` swatches wired into the controller), so the update logic is
  untouched. The now-empty sidebar "Current Readings" card was removed (also helps the sidebar stay
  narrow).
- **GUI Plot Controls card + Autoscale button** — the plot-control buttons moved from a plain
  row into a titled **"Plot Controls"** sidebar card holding **Autoscale**, **Set/Clear Reference**
  (the toggle) and **Clear Plots**. The new **Autoscale** button (`pButton_Autoscale` →
  `autoscale()` → `_autoscale_plot_all(True)`) re-enables **X and Y autorange on all four plots**
  (amplitude/sweep, frequency, dissipation, temperature); it follows the other plot controls'
  enable state (usable during acquisition). Styled as a card via `#groupPlotControls` QSS.
- **GUI Temperature card simplified — removed the inner tab container** — the Temperature card
  wrapped its controls in a single-tab `QTabWidget` whose bordered `::pane` drew a redundant box
  inside the card. The `QTabWidget` is gone; the Temperature Control widgets now sit directly in
  the `groupTempPID` card (borderless `tab` container + `gridLayout_4`, top separator `line_4`
  hidden). The PID widgets stay created on a hidden standalone `tab_2` (kept for the controller /
  future advanced-temperature window). The center Plots/System Log tab widget is unaffected.
- **GUI sidebar horizontal compaction (fine-tuning)** — several changes to narrow the sidebar:
  F0–F9 overtone chips shrunk to the minimum (tight padding, `min-width: 0`, 3px row spacing);
  the TEC **ON / OFF / RESET** buttons moved onto a single compact equal-width row (tight padding);
  **Set Reference / Clear Reference merged into one toggle** on `pButton_Reference`
  (`_toggle_reference` calls `reference()` / `reference_not()` by `_reference_flag` and relabels
  the button; the label is re-synced on Start; `pButton_Reference_Not` is hidden but kept alive);
  the Temperature Control state banner now word-wraps so its longer state strings no longer force
  the card wide; the sidebar scroll `minimumWidth` lowered 220 → 170. The current-readings F/D grid
  is deliberately left for a later pass (now the main remaining width driver).
- **GUI fine-tuning: hide datalog sampling time and the PID section** — the datalog
  sampling-time selector is hidden from the sidebar (kept created/functional — acquisition uses
  the default sampling time; "Time elapsed" stays). The Temperature card is simplified to
  Temperature Control only: the PID Control tab is removed and the now single-tab bar hidden, card
  renamed "Temperature". Everything is **hidden-only** — the PID widgets (`cBox_PID`,
  `spinBox_Cycling_Time/P/I/D_Share`, `pButton_PID_Set` on the still-alive `tab_2`) and
  `cBox_sampling_time` stay created and referenced by the controller, so no logic changed. Advanced
  temperature/PID control is planned as a **dedicated window** (see HANDOFF §5).
- **GUI: programmatic UI builder (redesign R1, structural parity)** — the Qt-Designer generated
  `ui/mainWindow_new_ui.py` is replaced by a hand-written `ui/mainWindow_ui.py` (same
  `Ui_MainWindow` class name, one-line import switch in `ui/mainWindow.py`), in the style of
  openQCM Q-1 v3.0. The builder constructs the single-window shell **directly** — splitter
  [scrollable sidebar | center tabs (Plots | System Log)] — making the whole `_build_shell()`
  re-parenting layer obsolete (method deleted). It also absorbs every widget previously created at
  runtime: Connect/Refresh (connection-card bottom row), the F0–F9 overtone quick-select buttons
  (legacy radios created hidden, still the `scan_selector` source of truth), `systemLog`,
  `lblLogFile`, and the hidden legacy `pButton_Stop`. New **File / View / Tools / Help menu
  skeleton** (File→Quit; Tools→Raw Data / Log Data / Tec Current; Help→Help / Firmware Info /
  Software Info; the theme submenu now populates the builder's View menu). The controller keeps
  all behaviour and only wires signals (`_setup_serial_connection_ui`, `_setup_overtone_buttons`,
  `_setup_log_filename_label`, `_install_system_log` reduced to wiring/aliases). Verified by an
  attribute-contract check (every `self.ui.<name>` the controller references exists on the new
  builder) plus an offscreen `QT_QPA_PLATFORM=offscreen` instantiation; widget properties
  (spinbox ranges/defaults, combo policies, texts, brand header, tab titles) replicated from the
  generated file, which stays in the repo as reference. Visual-style pass (mockup cards, bottom
  status bar) is the follow-up R2 step.
- **GUI: mockup style pass (redesign R2)** — on top of the R1 programmatic builder:
  - **Full-width bottom status bar** (`statusBarFrame`): the program-status pill (`infostatus`) and
    message (`infobar`) move out of the sidebar to the bar's left; compact live readings
    **F / D / T / S** (`statusFreqValue`/`statusDissValue`/`statusTempValue`/`statusSampValue`) and
    the **progress bar** (fixed 160 px) sit on the right. Readings are mirrored from the existing
    update paths: fundamental in multiscan / measured overtone in single mode
    (`_update_indicator_F/_D[_single]`), temperature via a new `_set_indicator_temperature`
    helper, elapsed time next to `time_indicator`; reset to `--` on Stop
    (`_reset_status_readings`).
  - **Card-style sidebar**: "Serial Connection" (COM row + Refresh/Connect) and "Measurement
    Setup" (mode, single-mode frequency, F0–F9 quick-select, datalog sampling + elapsed time)
    become titled group boxes; the readouts card and the Temperature/PID tabs follow; the datalog
    filename sits right above a prominent Start toggle at the sidebar bottom. Brand header
    restyled (left-aligned title + muted subtitle, no hardcoded black).
  - **Dark-theme fix**: the sidebar container and scroll-area viewport now follow the theme
    palette (they defaulted to the platform light palette, leaving gray-on-gray labels on dark).
- **GUI: R2 mockup-fidelity fixes** (after the first on-device check):
  - **Status-bar height bug fixed**: `statusBarFrame` had no fixed height and swallowed half the
    window (squeezing the sidebar into a scroll). Now `setFixedHeight(36)` + the splitter takes
    all extra vertical space (`outer.addWidget(mainSplitter, 1)`).
  - **Mockup styling**: card titles rendered **inside** the rounded cards (bold, objectName-scoped
    QSS); the Temperature/PID tabs wrapped in a **"Temperature & PID"** card; readouts card
    retitled "Current Readings — F (Hz) · D (ppm)"; Start toggle idle color switched to the
    **accent blue** of the mockup (running stays red); F0–F9 restyled as rounded chips;
    status-bar readings use full text color.
  - **Theme quick-toggle** in the menu-bar top-right corner (`themeToggleButton`, shows the theme
    it switches to), wired alongside the View → Theme menu.
  - **Plot canvas order** per the mockup: amplitude/phase sweep + temperature on top, then the
    resonance-frequency and dissipation time series.
- **GUI: dark-theme completeness fixes** (after the second on-device check): generic
  `QPushButton` base style (the untargeted buttons — TEC ON/OFF/RESET, PID Set, Reference/Clear —
  fell back to the native light style on dark), themed scroll bars, themed horizontal separator
  lines, themed splitter handle. **Menu bar forced in-window** (`setNativeMenuBar(False)`): on
  macOS the native system bar swallowed the File/View/Tools/Help row and the corner theme toggle
  (mockup layout restored). Fixed "Temperature _PID" card title — the `&` needed escaping (`&&`).
- **GUI: QSS refinement pass (mockup fidelity)** — refined light/dark palettes (softer window,
  borders and field fills), 10px rounded cards with 13px bold inside titles and wider sidebar
  spacing, restyled inputs (rounded, padded, min-height), **Connect primary / Refresh outline**
  button pair, larger Start toggle (40px, 14px bold), pill-shaped F0–F9 chips, **borderless bold
  readout values** (F/D grid, temperature, elapsed time), themed tabs (accent bold on the selected
  tab, rounded pane), slim rounded progress bar, padded in-window menu items, muted infobar. The
  TEC state banner's six inline styles are replaced by a theme-aware `_tec_state_pill` helper
  (off follows the theme; warn amber / active translucent accent / err red), re-applied on theme
  switch. Note: frequency and dissipation keep **two separate plot panels** by explicit decision.
- **Entry point unified into `run.py`**: added a thin `software/run.py` launcher and
  removed the duplicate root `software/app.py`; the `OPENQCM` class now lives only in
  `openQCM/app.py`. Launch with `python run.py` (or `python -m openQCM`).
- Firmware version check no longer runs automatically at startup; it runs on connect.
- **Robust anti-outlier averaging of the raw acquisition buffer**: every physical observable
  averaged from the 10-sample circular buffer — resonance frequency and dissipation (per
  overtone) and temperature — is now aggregated with `scipy.stats.trim_mean` (proportion
  `Constants.trim_mean_proportiontocut = 0.10`) instead of Savitzky-Golay + `np.average`,
  consistently across **both** acquisition processors (`processors/Multiscan.py`, multi-overtone,
  and `processors/Serial.py`, single-overtone). The former SG (window=3, order=1) was a linear
  3-point moving average with no outlier rejection — a single bad sweep leaked almost fully into
  the logged value (and was amplified at the buffer edges by the SG reflective padding).
  `trim_mean` drops the min/max sample before averaging, staying as smooth as the mean (no median
  "staircase"). The per-sweep Savitzky-Golay (sweep-curve smoothing, Stage A) is unchanged; the
  datalog-decimation average in `core/worker.py` is a separate, pending change.
- **Development: observable plots default to Y autorange** (`ui/mainWindow.py`,
  `core/constants.py`): the per-update forced (padded) Y-range on the frequency, dissipation and
  temperature plots is now gated behind `Constants.plot_force_yrange` (default `False`), applied
  through a new `_set_yrange_forced` helper. With the flag off the plots autoscale tight to the
  data; the forced range — introduced so autoscale would not over-emphasise small signal
  variations — can be restored and its paddings (`y_f_range` / `y_d_range` / `y_t_range`) tuned
  for distribution by setting the flag `True`. The sweep-spectrum plot's own fixed range is
  unchanged.

### Fixed
- **Application icon now loads on all platforms** — it was set from non-resolving paths:
  `app.py` used the Windows-only `'\icon\favicon.ico'`, and the window icon + sidebar brand logo
  used the cwd-relative `"favicon.png"`, so no icon appeared on macOS/Linux (or whenever the app
  was launched from another directory). All three now use an absolute, module-relative path to
  `openQCM/res/icon/favicon.png`: `QApplication.setWindowIcon` (dock / taskbar + default window
  icon), the `MainWindow` window icon, and the sidebar brand logo (guarded by `os.path.exists`).
- **Long serial-port name widened the sidebar** — on Connect, `label_COM_status` showed
  "Connected: <port>" and a long port name forced the whole (scroll-bar-off) sidebar wider. The
  label now has an `Ignored` horizontal size policy and `minimumWidth 0`, so its content never
  dictates the sidebar width (the full "Connected: <port>" is kept in its tooltip).
- **Peak-detection / calibration plot was invisible on the light theme** — the live amplitude
  sweep drawn during peak detection (and the serial-mode amplitude sweep and the temperature
  curve) used a hardcoded **white** pen (`Constants.plot_colors[0]` / `plot_color_temperature`),
  which vanished once the theme system set the light theme's plot background to white. These
  single curves now use a theme-aware foreground color (new `theme.PLOT[theme]["curve"]`, dark on
  light / light on dark) via a `_curve_color()` helper, applied at every plot/setData site and
  re-applied on theme switch in `_apply_plot_theme`. The colored multi-overtone
  frequency/dissipation curves were unaffected. Regression from the GUI theme system (Phase 0).

### Docs
- Rewrote `README.md` with a full structure (badges, TOC, features, architecture,
  version history, roadmap).
- Removed internal development references from the README.
- Expanded the Repository Structure (full software package tree) and aligned Quick Start /
  Features / Roadmap with the serial-connection flow (Connect/Disconnect/Refresh).
- Added a developer `HANDOFF.md` (architecture, branches incl. impedance-analysis, planned
  tasks, conventions/gotchas) so the project can be resumed from any clone.

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
