# HANDOFF — Developer notes (openQCM NEXT)

> Technical starting point to continue development of the software and of the
> `impedance-analysis` branch. Working language: Italian in chat, English in the repo.
> Last updated: 2026-07-17.

---

## 1. Software architecture

**Multiprocessing** pipeline that keeps acquisition separate from the UI:

```
Serial/Multiscan/Calibration process  →  Worker (queues → ring buffers)  →  MainWindow (Qt, 50 ms timer)
        (child process)                                                        PyQtGraph + CSV
```

Package `software/openQCM/`:
- `core/`: `constants.py` (config), `worker.py` (multiprocessing, ring buffers), `ringBuffer.py`
- `processors/`: `Serial.py` (SerialProcess), `Multiscan.py` (multi-overtone; conductance on the impedance branch), `Calibration.py` (peak detection), `Parser.py`
- `ui/`: `mainWindow.py` (controller, ~4000 lines), `mainWindow_ui.py` (**programmatic UI builder**,
  GUI redesign R1; the old generated `mainWindow_new_ui.py` stays as reference only), `theme.py`, `popUp.py`
- `data_view/`: standalone CSV viewer
- Entry point: `run.py` → `openQCM.app.OPENQCM().run()`

## 2. Branches

- **`main`**: development line. Reconstructed history (`v0.1.5` → `v0.1.6-dev` → `v0.1.6-dev-073`)
  plus all current development (entry point, serial connection, dependencies, README, fixes).
- **`impedance-analysis`** (tag `v0.1.6G-test`): experimental conductance-based impedance feature.
- ⚠️ **The impedance branch is behind `main`**: it was branched from `v0.1.6-dev` and only carries
  the conductance feature; it does **not** have the later work on `main` (run.py, serial connection
  Steps 1–2, requirements/environment, new README, Raw Data fix). To align it, run `git merge main`
  **from** the impedance branch and resolve conflicts (mainly in `ui/mainWindow.py` and
  `processors/Multiscan.py`, touched by both lines). The two branches stay separate until a merge
  `impedance-analysis → main` is decided.

## 3. Current state on `main`

### Serial connection (refactored) — how it works now
The serial connection is a **dedicated feature** (explicit connect, independent from the operation
mode). Methods in `software/openQCM/ui/mainWindow.py`:
- `_setup_serial_connection_ui()` — creates the **Connect/Disconnect** and **Refresh** buttons at
  runtime (in the Start/Stop row) plus the connection state.
- `_toggle_serial_connection()` — Connect: per-port lock file (`_acquire_port_lock`, `fcntl` on Unix)
  + open a **persistent exclusive** handle `_serial_lock` (`_open_serial_lock`), then firmware check.
  Disconnect: close `_serial_lock` + release the lock file.
- `_serial_write()` / `_serial_query()` — the GUI queries (set temperature, TEC on/off, PID, firmware)
  write/read on `_serial_lock` instead of opening the port ad-hoc.
- **Hand-off**: `start()` closes `_serial_lock` (gives the port to the acquisition process);
  `stop()` calls `_reacquire_serial_lock()` before the shutdown queries.
- `_refresh_ports()` — rescans devices; **Start** is enabled only once connected (`_enable_ui`).

### Also done on main
`run.py` entry point; full README; `requirements.txt` / `environment.yml`; Raw Data fix
(restored the functional `sweep_data/*.txt`); **robust trimmed-mean averaging** of the raw
acquisition buffer; **observable plots default to Y autorange** in development
(`Constants.plot_force_yrange`); **responsive peak-detection (calibration) cancellation**
(ported from Q-1 v3.0 — Stop now interruptible mid-sweep, clean shutdown); **GUI theme system
dark/light** (`ui/theme.py` + View → Theme menu, Phase 0 of the GUI redesign) — all see §5 and CHANGELOG.

## 4. `impedance-analysis` branch (0.1.6G) — detail

**What it is**: impedance measurement via the **conductance spectrum G(f)** derived from the AD8302
MAG/PHASE signals (software post-processing; same firmware/protocol as the classic method).

**Where in the code (on the branch)**:
- `software/openQCM/processors/Multiscan.py`: `parameters_finder_impedance()` (~:328), `_Zabs_Vmag`,
  `_phase_raw_V_phase`, `_G_calc`, `_B_calc`, `_Freq_G`, `_half_bandwidth_G`. Wired into
  `elaborate_multi()` (~:626): it runs **both** the classic and the conductance method but
  **publishes the conductance** results (the classic lines are commented out).
- `software/openQCM/sweep_data/plot_conductance.py`: offline validation script (uses `g*.txt`).
- `docs/impedance-analysis/`: documentation (`conductance-calculation.md`,
  `openQCM_Next_G_Impedance_Analysis.md`, 3 PDFs).

**State / limitations**:
- Implements the **approximate** formula (`G = cosφ/|Z|`); the **exact** complex-impedance version is
  documented only, not implemented.
- **DEBUG** state (`constants.py`: `environment = 4`, `plot_autoscale_yaxis = True`).
- The method is **always on, not selectable** from the UI (hard-wired in `elaborate_multi`). The only
  added control is the **"G DATA VIEW (BETA)"** button (launches the offline plot).
- `elaborate_conductance_multi()` is **dead code** (UNUSED).

**To stabilize / merge**:
1. Make the measurement **selectable** (classic vs conductance) instead of hard-wired.
2. Implement the **exact** formula (complex impedance in the divider).
3. Remove the DEBUG state.
4. **Align with `main`** via `git merge main` (the branch lacks the recent development).

## 5. Planned technical tasks (on `main`)

Done (raw-data robustness — see CHANGELOG):
- **`trim_mean` anti-outlier averaging**: replaced Savitzky-Golay + `np.average` with
  `scipy.stats.trim_mean(0.10)` on the 10-sample circular buffer for frequency and dissipation
  (per overtone) **and temperature**, in **both** processors (`Multiscan.py` multi-overtone,
  `Serial.py` single-overtone). Added `Constants.trim_mean_proportiontocut`. The replaced
  SG (window=3, order=1) was a linear 3-point moving average with no outlier rejection.
  - **Still pending — Stage C**: the datalog-decimation average in `core/worker.py:767-769`.
    There, average over `get_partial()` (NaN-safe) and note that `trim_mean(0.10)` degenerates
    to the plain mean for buffers < 10 samples (choose proportion or estimator accordingly).

Done (dev plotting — see CHANGELOG):
- **Observable plots Y autorange** (`ui/mainWindow.py`, `Constants.plot_force_yrange`): the forced
  padded Y-range on frequency/dissipation/temperature is gated behind the flag (default `False`,
  routed through the `_set_yrange_forced` helper) so development runs autoscale tight to the data.
  - **Distribution follow-up**: set `plot_force_yrange = True` and tune the paddings
    `y_f_range` / `y_d_range` / `y_t_range` for a stable user-facing view.

Done (responsive peak-detection cancellation — ported from Q-1 v3.0, see CHANGELOG):
- Peak detection (calibration) is now **interruptible cleanly** instead of blocking the Stop button
  for the whole ~1 min sweep. `processors/Calibration.py`: inner sweep-read loop polls `self._exit`
  with a `0.1 s` serial read timeout (Stop acts in ~0.1 s), emits a `-1` cancellation sentinel on
  `parser5` + `return` on mid-sweep cancel, drains stale serial bytes on start. `core/worker.py`:
  `_calibration_cancelled` flag (`is_calibration_cancelled()`), `stop()` joins-then-terminates the
  peak-detection process (graceful) while measurement modes keep the direct terminate.
  `ui/mainWindow.py`: Stop stays enabled during peak detection; `_update_plot` checks the flag first;
  `stop()` shows "Peak Detection Cancelled" and clears the real-time amplitude trace; init
  `_overtones_number_all = 0` (fix for the latent `AttributeError` that Stop-during-calibration exposed).
  - **Note (dormant scaffolding)**: the `-1` sentinel + flag path mirrors Q-1 but rarely fires in
    NEXT — the GUI `stop()` stops the plot timer before the sentinel is consumed, so the user-facing
    "Cancelled" comes from `stop()` and the real cancellation from the responsive loop + graceful join.
  - **Reference sibling repo**: `/Users/marco/claude_code/openQCM_Q-1/OPENQCM` (git; remote
    `github.com/openQCM/openQCM_Q-1`; **v3.0**). This is the authoritative Q-1 roadmap codebase.

GUI redesign (phased, inspired by openQCM Q-1 v3.0 — reference repo `/Users/marco/claude_code/openQCM_Q-1/OPENQCM`):
- **Fase 0 — Theme dark/light — DONE** (see CHANGELOG): `ui/theme.py` (LIGHT/DARK palettes + QSS +
  per-theme plot colors) + `_setup_theme_menu`/`_apply_theme`/`_apply_plot_theme` + `QSettings`
  persistence (default light). Readout fields migrated from inline white to QSS objectName rules.
  - Known Phase-0 limitation: `infostatus` standby stays a light pill on the dark theme (uses HTML
    `<font color=#000000>` text on a white inline background) — harmonise the neutral state in Phase 4.
- **Fase 1 — Single-window QSplitter shell — IMPLEMENTED, ⚠️ VISUAL TUNING PENDING** (committed on
  `main`; the user reported the visual layout is *not correct yet* and will iterate off-session):
  `ui/mainWindow.py::_build_shell()` (called at the very end of `__init__`, after the runtime
  Connect/Refresh buttons exist) re-parents the old two-column `gridLayout_2` into a horizontal
  `QSplitter` **[ scrollable collapsible sidebar | plots ]**. Sidebar order (top→bottom): brand
  (`groupBox_2`), connection (`gridLayout`), F/D readouts (`groupBox_data`), overtone radios
  (`gridLayout_D`), sampling/time (`gridLayout_5`), `line_3`, Temperature/PID tab (`tabWidget`),
  `addStretch`, then **bottom**: action row (`horizontalLayout`) + status (`verticalLayout`, `infobar`).
  Plots (`verticalLayout_plt`) go in the center pane. No widget recreated → objectNames + signal
  wiring preserved (theme Phase 0 and all logic still work).
  - **Re-parenting recipe (KEEP THIS — a subtle Qt gotcha)**: widget → `dest.addWidget(w)` (re-parents);
    bare sub-layout → wrap in a fresh `QWidget` via `container.setLayout(subLayout)` then
    `dest.addWidget(container)`. Do **NOT** use `layout.addItem(takenItem)` for widgets — it does not
    re-parent, leaving controls owned by the old `centralwidget` → mis-rendered. The central layout is
    swapped with the `QtGui.QWidget().setLayout(oldGrid)` throwaway trick.
  - **Revert instantly**: comment out the `self._build_shell()` call in `__init__` → old grid returns.
  - **What to fix on-device** (not verifiable headless): the action row packs 6 buttons + progress bar
    horizontally into a ~360px sidebar → likely overflows/wraps and looks cramped. Candidate fixes: lay
    the acquisition controls vertically (or a 2-col grid), give the sidebar groups real "card"
    styling/spacing, revisit sidebar min/max width (currently 220–360) and splitter initial sizes
    (`[240, 900]`). Note much of the action row is superseded by **Phase 3** (single StartStop toggle +
    status dock) — decide whether to polish now or fold into Phase 3. `QtGui.*` widget classes are
    available in `mainWindow.py` via the matplotlib `qt_compat` shim (so keep using `QtGui.QWidget` etc.).
- **Fase 2 — Tab centrale [ Plots | System Log ] — IMPLEMENTED (pending on-device smoke test)**
  (see CHANGELOG): center pane is a `QTabWidget` (`centerTabs`); the plots are re-parented into the
  Plots tab; module-level `LogStream` mirrors the main process's stdout/stderr into a read-only
  `QTextEdit` (`systemLog`) with `[HH:MM:SS]` timestamps, forwarding to the originals; installed
  after `_build_shell()` (`_install_system_log`), restored in `closeEvent` (`_restore_system_log`);
  theme-aware monospace via `QTextEdit#systemLog` in `ui/theme.py`. **Scope**: captures `print()`
  of the main process only — child-process prints and `logging`-module messages stay on the
  terminal / log file (a `logging.StreamHandler(LogStream)` would add them; optional Phase 2-bis).
- **Fase 3 — Consolidated controls — DONE** (sub-steps below; see CHANGELOG):
  3. Consolidated controls **+ sidebar layout tuning (folded in here)** — sub-steps:
     - **3a single Start/Stop toggle — DONE** (see CHANGELOG): `pButton_Start` toggles Start/Stop
       (`_toggle_start_stop`, uses `worker.is_running()`), green/red via a `running` dynamic
       property + theme QSS (`#pButton_Start`), stays enabled while running, visual state flipped
       inside `_enable_ui`; `pButton_Stop` hidden, inline style dropped.
     - **3d log-filename display — DONE** (see CHANGELOG): runtime `lblLogFile` in the sidebar
       status area (elided + tooltip) + window title suffix; `Worker.get_csv_filename()` mirrors
       the datalog names (serial `<ts>_<overtone>.csv`, multiscan `<ts>_multi_.csv`, calibration "").
     - **3c status pill theme-aware + state dot — DONE** (see CHANGELOG): `_status_pill(key)`
       helper (standby follows the theme; warn/err/ok keep yellow/red/green with dark text),
       `● Program Status: …` texts, re-applied on theme switch via `_status_key`.
     - **3b overtone quick-select F0–F9 — DONE** (see CHANGELOG): checkable proxy buttons over the
       hidden legacy radios (`scan_selector` untouched); multiscan = multi-select visual filter,
       live during acquisition; serial = exclusive, drives `cBox_Speed` (reverse-order mapping
       `combo_index = count-1-idx`), idle-only; calibration = disabled.
     - **3e sidebar action-area layout — DONE** (see CHANGELOG): Refresh+Connect moved into the
       connection card (bottom row, theme QSS instead of inline styles); action row decomposed —
       plot controls keep the old row, Start/Stop toggle gets a prominent full-width row with the
       progress bar underneath. This resolves the Phase-1 "cramped action row" note. Remaining
       fine-tuning (spacing/polish) deferred to the user's visual pass after the block phases.
- **Riscrittura programmatica GUI (approved follow-up to Phases 0–3)**:
  - **R1 — programmatic builder, structural parity — DONE** (see CHANGELOG): `ui/mainWindow_ui.py`
    (hand-written `Ui_MainWindow`) replaces the generated Designer UI; `_build_shell()` deleted;
    runtime widgets absorbed; File/View/Tools/Help menu skeleton. Contract-checked (all
    `self.ui.<name>` refs exist) + offscreen instantiation verified. Old generated file kept as
    reference. **Pending: user visual check.**
  - **R2 — mockup style pass — DONE + fidelity fixes** (see CHANGELOG): full-width bottom status
    bar (36 px fixed — the unbounded height bug from the first check is fixed; pill + message
    left; F/D/T/S live readings + progress right, reset on Stop); titled cards with the title
    inside (Serial Connection, Measurement Setup, Current Readings, Temperature & PID); Start
    idle = accent blue (running red); F0–F9 chips; menu-bar corner theme toggle; plot canvases
    reordered [sweep+temp, frequency, dissipation].
  - **R2-bis — QSS refinement pass — DONE** (see CHANGELOG): refined palettes (softer borders /
    fields), rounded cards (10px) with 13px bold inside titles, restyled inputs, primary Connect /
    outline Refresh, larger Start (40px, 14px bold), pill chips, borderless bold readout values,
    themed tabs (accent on selected), slim rounded progress, in-window menu polish; TEC state
    banner converted to a theme-aware `_tec_state_pill` helper (off/warn/active/err, re-applied
    on theme switch). **Pending: user visual check.**
  - ⚠️ **Frequency and dissipation stay in TWO separate panels** — the user explicitly rejected
    the mockup's single dual-axis panel. Do not merge them.
    Other accepted deltas vs the mockup: per-overtone readings grid kept (NEXT is multi-overtone);
    Add-On menu superseded by Tools.
- **Fase 4 — plot interactions — DONE (pending user visual check; see CHANGELOG)**: grid off by
  default + per-plot toggle; custom right-click menu on all four plots (auto-scale, reset zoom,
  pan/select mouse mode, grid); **Δ cursors on the separate F and D panels** (Δt in s — axis is
  epoch µs —, ΔF Hz / ΔD ppm via nearest-sample on the fundamental (multiscan) or measured
  overtone (single); right-click per panel or View → Δ Cursors global toggle; items parented to
  the ViewBox with ignoreBounds so they survive clear() and don't drive autorange).
  **Deferred by decision**: min-Y-scale enforcement (to be integrated with `plot_force_yrange`).
  Next: Fase 5 (menu wiring: Tools/Help actions already exist) and the user's GUI fine-tuning pass.
- **GUI fine-tuning — DONE this session (2026-07-17; all committed & pushed, see CHANGELOG)**:
  - **Sidebar compaction**: minimal F0–F9 chips; TEC ON/OFF/RESET on one compact row; **Set/Clear
    Reference merged into a single toggle** (`_toggle_reference`); Temperature state banner
    word-wraps; sidebar scroll `minimumWidth` 220 → 170; a long "Connected: <port>" no longer widens
    the sidebar (`label_COM_status` size policy `Ignored` + full name in tooltip).
  - **Temperature card**: datalog sampling-time selector + whole PID section **hidden** (widgets
    kept alive on a hidden standalone `tab_2`); the redundant inner `QTabWidget` container removed —
    controls sit directly in the card.
  - **Plot Controls card** (Autoscale · Set/Clear Reference · Clear) + new **Autoscale** button
    (`autoscale()` → X+Y autorange on all plots).
  - **Center layout**: vertical `QSplitter` (`plotSplitter`) — amplitude/phase-sweep + temperature
    on top, **collapsible/hideable** via the handle; per-overtone **readout cards moved above the
    plots** ("Frequency (Hz)" / "Dissipation (ppm)"); sidebar "Current Readings" card removed.
  - **Palette reduction** toward blue `#008EC0` + brown `#DD8E6B`: Start/Stop toggle **blue (idle) /
    brown (running)** (added `brown` / `brown_hover` palette keys).
  - **App icon** now loads from an absolute module-relative path (`res/icon/favicon.png`).
  - **Fix**: peak-detection / amplitude-sweep / temperature curves were white → invisible on the
    light theme's white plot background; now theme-aware (`theme.PLOT[theme]["curve"]` +
    `_curve_color()`, re-applied on theme switch).
- **Fase 5 — scientific menu wiring — DONE** (see CHANGELOG): `Help → Help` opens the software
  webpage + new `Help → About`; `View → Sidebar` / `View → Status bar` show/hide toggles
  (`_open_help_website`, `_show_about`, `_toggle_sidebar`, `_toggle_statusbar` in the controller).
  **The phased GUI redesign (Phases 0–5) is complete.**
- **GUI — remaining / TODO** (polish / optional, after the block phases):
  - **Harmonise the remaining state colors** (status pill yellow/red/green) toward the blue+brown
    palette (deferred by the user during the palette-reduction step).
  - **min-Y-scale** enforcement (integrate with `Constants.plot_force_yrange`).
  - **Dedicated "Advanced Temperature Control" window** — re-expose PID (`cBox_PID`, `spinBox_*`,
    `pButton_PID_Set`, hidden `tab_2`) + optionally the datalog sampling time. See memory
    `advanced-temperature-pid-window`.
  - **Confirmed UX decisions**: single StartStop toggle; **TEC/PID kept in the sidebar** (advanced
    window later); System Log as a tab; default theme light; **frequency & dissipation stay TWO
    separate panels** (single dual-axis panel rejected).
  - ⚠️ **Preserve (do NOT copy Q-1 blindly)**: Q-1 v3.0 has *no* temperature control — NEXT's
    **TEC/Peltier + PID** must stay; and NEXT's **multiscan** multi-overtone selection differs from
    Q-1's single-overtone measurement.

Quick wins:
- **Disconnected-sensor detection** (ported from openQCM Q-1; detailed plan ready, awaiting go):
  add `Constants.min_valid_q_factor = 100` and, in `parameters_finder` — **both** `Multiscan.py`
  (before the `return` ~:317) and `Serial.py` (~:319) — set `self._err1 = self._err2 = 1` when the
  true Q is below the threshold, so amplifier noise from a detached sensor is not logged as a peak.
  **Adaptation — do NOT blind-copy Q-1**: our `parameters_finder` returns `Qfac` = *bandwidth*
  (consumed by the dissipation calc), not a Q-factor. Compute a separate local
  `q_factor = freq_resonance / bandwidth` (inside `np.errstate(divide='ignore', invalid='ignore')`,
  so `bandwidth == 0` → `inf` → passes) **only** for the guard; leave the returned `Qfac` and the
  dissipation untouched. Reuses the existing `_err1/_err2` → `parser6.add6(...)` "-3dB not found"
  pipeline (no new plumbing). Threshold `100` is Q-1's (its bandwidth is FWHM `0.707·f_max`); ours
  uses `f_max - THRESHOLD_DB` (0.3 dB), so the value **must be validated/tuned on hardware** with a
  physically disconnected sensor. Optional first step: synthetic Lorentzian-vs-noise check offline.
- **Robust firmware query**: add range-priming (`1;1;1\n`) + reply-format validation in
  `ui/mainWindow.py` (adapt the regex to the `0.1.5a` version format) to survive older firmware.
- **Firmware updater .hex fix**: `firmware_update/` ships the `0.1.5` image (POT 180) while the
  software expects `0.1.5a` (POT 240) → ship the `0.1.5a` image (already in `firmware/`).

Backend backlog ported from the more mature **openQCM Q-1** sibling codebase (its CHANGELOG is the
roadmap). ⚠️ Each Q-1-inspired change needs a **detailed plan + explicit approval before coding**
(code must be adapted to this repo, not copied verbatim — see the Q-factor example above):
- **Tracking safety (auto-disable / auto-resume)**: disable auto-tracking after N consecutive
  sweeps with the peak lost, auto-resume when it returns. Backend = a `_consecutive_edge_errors`
  counter in the acquisition process + tracking events on a parser queue + Worker→GUI notifications
  (Q-1: disable after 10, resume after 5). Builds on the disconnected-sensor guard (same `_err`
  pipeline). GUI status-bar notification part deferred.
- **Peak-detection validations**: validate the fundamental is a plausible QCM frequency
  (4-6 / 9-11 MHz), flag when all expected overtones are zero, auto-detect QCM type (5/10 MHz),
  tune the magnitude/phase cross-validation threshold. Two-phase detection already exists in
  `processors/Calibration.py` (`peak_detection_qcm_fundamental` / `..._overtones`).
- **Windows serial anti-jitter**: add `sleep(0.001)` inside the `inWaiting()` read loop
  (`Serial.py:826`, currently a tight busy-wait) to reduce Windows scheduler jitter.
- **Minor / defensive**: `FileManager.create_dir(None)` raises `TypeError`; `file_exists(None)`
  returns `None`. `Constants.environment = 50` for production (currently `10`, development).

Later (GUI / firmware / packaging — deferred): UI (System Log tab, measurement cursors, light
theme, overtone quick-select); packaging (`common/resources.py` + hardcoded-icon fix, PyInstaller);
cross-platform validation; merge the impedance feature once stable (make the conductance method
selectable).

## 6. Conventions and gotchas

- **PyQt5 = 5.9.2 is mandatory**: the GUI uses the classic `QtGui` widget namespace
  (`QtGui.QMainWindow`, `QtGui.QPushButton`…); PyQt5 ≥5.11 moves widgets to `QtWidgets` and breaks the
  app. **Python 3.9.12**. Tested on macOS Intel and Apple Silicon. Conda is the reproducible route
  (see `software/environment.yml`).
- **Runtime-rewritten data files** (`Calibration_5MHz/10MHz.txt`, `PeakFrequencies*.txt`,
  `sweep_data/1-9.txt`): the program overwrites them. They are versioned as **defaults** (the Raw Data
  view / calibration need them in a fresh clone) but should be marked **`skip-worktree`** on each
  machine so runtime rewrites do not pollute git — it is a **local, per-clone** setting:

  ```bash
  git update-index --skip-worktree \
    software/openQCM/Calibration_5MHz.txt software/openQCM/Calibration_10MHz.txt \
    software/openQCM/PeakFrequencies.txt software/openQCM/PeakFrequenciesRT.txt \
    software/openQCM/sweep_data/1.txt software/openQCM/sweep_data/3.txt \
    software/openQCM/sweep_data/5.txt software/openQCM/sweep_data/7.txt \
    software/openQCM/sweep_data/9.txt
  ```

- **GUI can't be tested headless**: run static checks (`python -m py_compile ...` and
  `python -c "from openQCM.app import OPENQCM"` from `software/`), then leave the on-device smoke test
  to a human.
- **Every change goes into `CHANGELOG.md`** (unless explicitly told not to, e.g. a fix that just
  restores pre-existing behavior); keep the **README** aligned with substantial changes. Commits use
  Conventional Commits + a `Co-Authored-By` trailer.
- Propose a plan and wait for approval before invasive changes.
