# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

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
  (serial: `<ts>_F<n>.csv`, multiscan: `<ts>_multi.csv`; calibration returns an empty string
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
- **Raw Data View — live amplitude and phase sweeps per overtone** (`ui/rawDataView.py`, new;
  **Tools → Raw Data View**). Ported from openQCM Q-1 v3.0 and extended from Q-1's single
  overtone to NEXT's five, as a non-modal pyqtgraph dialog: one tab per overtone, amplitude
  over phase with the **X axes linked**, and the resonance peak (red diamond), the
  **dissipation band** (shaded region between the two crossings the dissipation is actually
  computed from) and the `peak − THRESHOLD_DB` threshold line drawn on the fit.
  - **Pull model, not push**: the dialog owns a 300 ms `QTimer` and asks the acquisition object
    for its buffers. No `set_data()`, no signal, no registration — which is what makes a closed
    dialog cost *nothing* rather than merely idle, and keeps the acquisition from ever waiting on
    the GUI. The worker is re-resolved (`getattr(host, 'worker', None)`) on **every tick** and
    never cached at construction: START/STOP replace the object and a cached reference would
    silently freeze the view.
  - **Memory only, never a file** — see the sweep-dump entry below for the constraint and how it
    was verified.
  - The band comes from `core/resonance.py` at **full sample resolution** (18001 points for the
    current 18 kHz span), so what is drawn is what is logged. Only the arrays handed to the plot
    are decimated (`Constants.FREQ_STEP_PLOT`), exactly as the main sweep panel already does;
    the fit is never decimated and `spline_points` is never clamped, since either would draw a
    band disagreeing with the instrument. Beyond an absurd span the fit is skipped and says so.
    Only the **visible tab** is analysed: one spline per tick, not five.
  - Q-1 traps corrected rather than inherited: narrow exception handling instead of the
    `except Exception` that hid Q-1's hundreds-of-megabytes `linspace`; one
    `sigMouseClicked` per `QGraphicsScene` plus a hit test (the plots of one
    `GraphicsLayoutWidget` share a scene); default menus off on both `PlotItem` and `ViewBox`;
    grid off by default; and the host clears its reference on `destroyed` and guards the close,
    since `WA_DeleteOnClose` otherwise lets `closeEvent` reach a deleted C++ object.
  - Each tab **frames the resonance once**, on its first successful fit (±20× the measured band,
    ~2.5 kHz), then never again: at full sweep scale a 62 Hz band inside an 18 kHz span is an
    invisible sliver, but a view that re-framed itself every 300 ms would be unusable.
- **Raw sweep dump behind a development flag, isolated in one module**
  (`common/sweepDump.py`, new; `Constants.dev_sweep_dump`, default `False`). The dump to
  `sweep_data/<n>.txt` used to run unconditionally on every sweep, as two copies of an inline
  block (each with its own OS-separator logic) in `MultiscanProcess` and `SerialProcess`.
  Enable it for one session without editing anything: `OPENQCM_SWEEP_DUMP=1 python3 run.py`.
  **The point of the separation is that Raw Data View must not depend on it**, and that was
  verified rather than asserted: deleting `sweepDump.py` and every reference to it (17 lines
  across three files) and driving the dialog in the amputated tree gives the same bands, peaks,
  threshold and info text, with identical SHA-256 of the fitted, sample and phase arrays. So the
  dump can be deleted outright whenever it stops being useful. **Tools → Raw Data (from sweep
  files)** — the older matplotlib viewer, renamed to tell the two apart — is hidden while the
  dump is off, since it could only open an empty or stale window.
- **The phase sweep reaches the GUI process** (`core/worker.py`): `consume_queue_P_multi()`,
  `_P_multi_buffer` and `get_P_values_buffer(idx)`, mirroring the amplitude side (the frequency
  axis is not stored twice — the amplitude queue carries the same one). Drained from
  `_update_plot` and from `stop()`. See ### Fixed for the leak this also closes.
- **`core/resonance.py`** (new) — the single source of truth for the filtering/fitting chain and
  the band walk: `savitzky_golay`, `spline_fit`, `find_peak_and_band` and an `analyze_sweep`
  convenience wrapper. Imported by both acquisition processes and by every viewer, so a viewer
  can no longer draw a band the instrument did not measure. See ### Changed and ### Fixed.
- **`core/averaging.py`** (new) — `trim_count(n, proportiontocut)` and `robust_mean(values,
  proportiontocut)`, replacing `scipy.stats.trim_mean` at the six places that average the raw
  frequency, dissipation and temperature buffers. See ### Fixed for why.
- **Datalog View** (`ui/dataLogView.py`, new; **File → Open Log…**, Ctrl/Cmd+O) — opens a log the
  instrument wrote and plots it, in the same menu position openQCM Q-1 v3.0 uses. Q-1 draws resonance
  frequency and dissipation against a hh:mm:ss axis; this adds the **temperature** channel, logged in
  the same file and what a drift usually has to be read against. Three panels on one time base.
  - **Not a singleton**, unlike the other views: comparing two runs side by side is the reason to open
    a log at all, so each invocation opens a new window.
  - ⚠️ **The log format has a trap, and it dictated the parser.** `FileStorage.CSVsave_Multi` always
    writes a **14-column header**, but the data rows **skip** every overtone whose frequency or
    dissipation is zero. Measured across all 33 logs in `logged_data/`: the 10 MHz sensor writes
    **10-column** rows under that 14-column header, the 5 MHz one writes 14. Reading columns by header
    name would have invented two overtones on every 10 MHz run. Pairs are therefore taken
    **positionally**, the row width decides how many there are, and rows of a different width are
    counted and reported rather than guessed at — none occurred in the 33 files.
  - The **harmonic order is derived** from the frequencies (the ratio to the first pair rounds to
    1, 3, 5, …) because the file does not record which overtones were selected. Verified on all 33
    logs: `F1,F3,F5` for the 10 MHz runs, `F1,F3,F5,F7,F9` for the 5 MHz ones.
  - Frequency is drawn as the **shift** from each overtone's first sample, with the starting value in
    the legend. Found by looking at the rendered output: five overtones on one absolute axis span 5 to
    45 MHz against a signal of a few hundred Hz, so the panel showed five flat lines and hid the only
    thing worth reading — the same reason the main window has SET REF.
  - Its own time axis rather than `Constants.DateAxis`, which reads epoch microseconds while a log
    records relative seconds. Grid off and the shared right-click menu. A file that is not a datalog
    is refused with a message. ⚠️ `Tools → Log Data` still opens the older matplotlib viewer; Q-1
    retired its equivalent when it added this entry, and doing the same here is a separate call.
  - **Movable zero.** A draggable cursor on both shift panels, kept in step, sets where the reference
    is taken; it snaps to a real sample, since the reference is a mean of real samples. Moving it
    re-zeroes every curve and readout and leaves the Y axes alone, so what moves is the zero and not
    the scale. The reference is the mean of `REFERENCE_SAMPLES = 5` points from the cursor, not one:
    adjacent samples of a real run differ by a few Hz.
  - **Dissipation is referenced too**, in ppm as the main window's readout card reports it. Absolute
    dissipation put five overtones at 90–360 ppm on one axis and showed five flat lines.
  - **Control panel top-left**: per overtone the colour swatch and the two values the plots are
    referenced to — so the numbers reading zero on screen stay legible — plus the **overtone pills**,
    the same widgets and `overtoneBtn` QSS property as the main window's quick-select row, showing or
    hiding that overtone on both panels. The dialog applies `theme.qss` to itself, since the main
    window sets it on itself rather than on the application.
  - **Temperature** moves to its own small panel top-right and stays **absolute** in degrees: it is
    what a drift is read against.
  - Labels are `F1, F3, F5, F7, F9` — the harmonic order. The main window calls the fundamental `F0`;
    that is the side that changes next.
- **Peak Data View** (`ui/peakDataView.py`, new; **Tools → Peak Data View**) — ported from openQCM
  Q-1 v3.0's `ui/calibrationPlot.py` and extended from Q-1's plots to NEXT's five overtones. It
  answers one question — is that really a resonance, or did the detector latch onto a bump in the
  baseline? — by drawing three things together on each channel: the raw full-span sweep as dots, the
  polynomial baseline subtracted from it, and the corrected curve the peaks were found in, with the
  detected peaks marked and labelled by harmonic order.
  - A **snapshot, not a live view**, and that is why reading files is right here where it would be
    wrong in Raw Data View: Peak Detection runs once and writes the two files, there is nothing in
    memory to read, and those files are the record of the calibration in use. Loaded on open, never
    polled. The newer of the 5 MHz and 10 MHz calibration files wins, since both can exist from
    different sessions.
  - It reconstructs the **baseline** with `Constants.BASELINE_POLY_ORDER` on the same arrays and the
    same estimator the detection used — only the peak frequencies are stored, not the correction —
    verified byte-identical to the previous literal `8`.
  - It also reconstructs the **phase peak**, because `PeakFrequencies.txt` holds the amplitude peak
    **twice** (`np.column_stack([f, f])` in `Calibration.py`), not amplitude and phase. Re-derived as
    the maximum of the corrected phase within 200 kHz of each amplitude peak and drawn as a star
    beside the circle marking where the amplitude peak falls in the phase channel. Their
    disagreement is the diagnostic: −500, −500, +500, −2500, −2000 Hz on the sensor at hand.
  - Grid off and the shared right-click menu; `setClipToView` plus **peak** downsampling, because
    each channel is 100001 samples and panning a full-span sweep is otherwise visibly slow — `peak`
    mode keeps the extremes, which are exactly what must not be smoothed away here. A missing or
    unreadable file is reported rather than raised, and a window that would only show an error is not
    opened.
- **`ui/plotMenu.py`** (new) — one implementation of the plot right-click menu (Auto-scale, Reset
  zoom, pan/select, Show/Hide grid, Export) and of the grid state, which pyqtgraph offers no
  reliable read-back of. The decision to switch pyqtgraph's own menu off was made once and
  implemented twice, in `mainWindow.py` and again in `rawDataView.py`; a third panel wanting it
  would have been a third copy. It also holds the two pyqtgraph facts that cost time to find:
  `setMenuEnabled(False)` is needed on the `PlotItem` **and** its `ViewBox`, and the plots of one
  `GraphicsLayoutWidget` share a `QGraphicsScene`, so `sigMouseClicked` is connected once per scene
  with the plot found by hit test. Two hooks keep it general: `extra_actions` for items only one
  window has (the main window's Δ cursors) and `apply_grid` for panels where more than one plot must
  follow (the main window's phase twin). `build_menu()` is separate from `show()` so the items can be
  asserted without entering a modal loop. `rawDataView` adopts it, verified identical — same seven
  items in the same order, both default menus off on all ten plots, ten plots across five tabs
  registered as five scene connections. **`mainWindow` keeps its own copy for now**: its version
  carries the cursors and four different plot targets, so converting the production window is worth
  doing on its own.

### Changed
- **The overtone chips keep their width; the sidebar buys spacing instead** — `F1 F3 F5 F7 F9` grew
  with the sidebar (50 px at a 260 px row, 78 at 400) while the gaps between them stayed at 3.
  Each chip is now pinned at `OVERTONE_CHIP_WIDTH` = 64 with a **`Fixed`** size policy, and a
  stretch between one chip and the next takes the slack: measured by driving the row layout
  directly, 64 px chips with gaps of 3 / 10 / 20 at rows of 330 / 360 / 400.
  - 64 px is what the row already gave each chip at 330, so nothing ends up smaller than it was.
  - ⚠️ **`setFixedWidth` alone does not pin them**, which is what defeated the first attempt (tried
    and reverted in `1e587d7`): `theme.qss` carries `min-width: 0px` on the chip rule, a style-sheet
    min-width beats the widget's own minimum, and the layout item's minimum stays at 8 px however
    wide the button claims to be. The `Fixed` policy is what stops the row stretching them.
  - ⚠️ **Below a 330 px row they still shrink**, deliberately: the alternative is a row that refuses
    to fit, and this sidebar clips rather than scrolls. At 260 the chips are 50 px, before and
    after — no regression at the narrow end, which is where the previous attempt died.
  - The row's minimum drops from 387 px to 332 and the sidebar container's from 435 to 380, so the
    clipping known since 2026-08-27 is **reduced by 55 px, not fixed**: the pane still allows 260.
- **The real-time plots use the openQCM Q-1 elapsed-time axis** — the four live axes (frequency,
  dissipation, temperature, TEC current) printed bare seconds under a `Time (Sec)` label; they now
  print `0 / 45 / 2:00 / 5:00 / 1:02:05` under **`Time (hh:mm:ss)`**, byte-identical to what Q-1's
  `ElapsedTimeAxis` produces on the same inputs. The plotted x values are unchanged — still epoch
  microseconds — so the buffers, the datalog and the Δ cursors do not move; only the tick labels are
  relative. `Constants.DateAxis` (and the older commented-out copy of it above, which was **inside a
  `'''` string** and never shadowed anything, contrary to the note in HANDOFF) is replaced by
  `Constants.ElapsedTimeAxis`; `import time` / `import datetime` go with it, as nothing else in
  `constants.py` used them. Two `CLEANUP_PLAN.md` items are closed by this.
  - ⚠️ **The axis draws empty labels until its reference is latched.** The seconds axis printed
    `int(value/1e6)` in that state — the raw epoch, measured as `1787904318` — and in single mode
    the reference is only taken when `_ser_control` reaches `Constants.environment`, so that is what
    the whole warm-up showed.
  - ⚠️ **The reference is cleared in `start()`, not in `stop()`** (a commented-out block in `stop()`
    proposed the latter). The finished run stays on screen after STOP and its ticks have to keep
    meaning something. Without any reset a second acquisition counted from the first one's start.
  - ⚠️ **`set_start_time()` ignores `None` and NaN and latches once.** The previous code assigned
    `.start_time` directly; a NaN reference made `tickStrings` raise `ValueError` out of the paint
    path, verified on the old class.
  - ⚠️ **The reference is `np.nanmin(buffer)`, not `buffer[0]`.** `RingBuffer.get_all()` returns the
    **newest** sample at index 0 and pads the tail with NaN (measured: three appends into a buffer
    of five give `[30 20 10 nan nan]`), so index 0 was the most recent point, not the oldest. The
    multiscan path already used `nanmin`; single mode now does too.
  - ⚠️ **`self.start_time` is in microseconds in both modes.** It was seconds in single mode and
    microseconds in multiscan, and two of the four `SecondWindow.update_plot` calls divided by 1e6
    to compensate. One unit, four identical call sites.
- **Datalog View prints the same times as the live plots** — its `RelativeTimeAxis` formatted through
  `datetime.timedelta` (`0:00:45`, `0:05:00`) while the plots of the same run now print `45`, `5:00`.
  The axis class stays separate, because a log holds relative **seconds** and feeding
  `ElapsedTimeAxis` would mean scaling the data by 1e6 into a unit nothing else in that window uses;
  the **format** does not. Both, and the "zero at …" readout under the reference cursor, call the new
  `Constants.format_elapsed_seconds` — one definition rather than the third copy of the same six
  lines. Q-1 makes the same split, with a second axis class for its log viewer.
- **Datalog file names follow the openQCM Q-1 v3.0 rule** — `2026-Jul-29_17-03-49_multi_.csv`
  becomes `2026-08-28_09-48-00_multi.csv`, and a single-overtone run
  `2026-Jul-28_19-34-16_fundamental.csv` becomes `2026-08-28_09-48-00_F0.csv`. Three changes,
  the first two ported from Q-1 `b6fd052`:
  - `Constants.csv_default_prefix` `%Y-%b-%d_%H-%M-%S` → **`%Y-%m-%d_%H-%M-%S`**: a numeric month
    makes the alphabetical order the chronological one, which `Jul` before `Jun` did not.
  - `common/switcher.py` overtone labels `fundamental` / `3th Overtone` / … → **`F0 F3 F5 F7 F9`**,
    so the name no longer carries a space. In NEXT these labels reach nothing but the file names —
    `Worker.get_overtone()` has no caller in the UI — so the rename is confined to storage.
  - the multiscan label `multi_` → **`multi`** (the trailing underscore was a separator with
    nothing after it). Not covered by the Q-1 rule: Q-1 has no multiscan mode.
  Older logs keep their names and stay readable: nothing parses a datalog file name — Datalog View
  decides the format from the row width, not from the file it was given.
- ⚠️ **The datalog timestamp is composed in one place again** — `Worker.start()` read a **local
  copy** of the format string (`csv_default_prefix = "%Y-%b-%d_%H-%M-%S"` in `worker.py`) rather
  than `Constants.csv_default_prefix`, so changing the constant alone renamed nothing. It now reads
  the constant. Related: `Constants.csv_filename` and `Constants.csv_sweeps_export_path` were built
  by an `strftime` **in the class body**, i.e. at import time, and carried the moment the app was
  launched instead of the moment START was pressed; both are removed, and the raw-sweep dump path
  (development only, `export_enabled=False`) is composed in `store_data` from the run's own
  timestamp — as Q-1 does.
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
- **Peak detection and the dissipation band unified into `core/resonance.py`** — behaviour
  preserved exactly. `savitzky_golay` and `parameters_finder` existed in **three** copies:
  `processors/Multiscan.py`, `processors/Serial.py` and `sweep_data/plot_sweep_spline.py`. In
  openQCM Q-1 that same duplication reached the GUI and the copies drifted, so the band on
  screen stopped being the band measured; in NEXT the third copy had **already** drifted (see
  ### Fixed). The two acquisition copies were **token-identical** (488 tokens, differing only in
  whitespace and comments), so unifying them is safe by construction — verified anyway against a
  frozen verbatim copy of `Multiscan.py` at `491925b`, with **exact equality** rather than a
  tolerance: the pure functions over 12 quantities on the five real sweeps of the 2026-07-29
  snapshot, on all five `overtone_number` branches and on the edge cases that raise
  `err_left`/`err_right` (including the historical division by zero on a flat signal);
  `elaborate_multi` over 65 calls and 260 parser payloads plus every ring buffer, trimmed mean
  and error flag; `Serial.elaborate` over 13 cycles and 42 payloads. Net −309 lines.
  - Quirks deliberately preserved and now documented in one place: the fundamental and overtone
    branches of `parameters_finder` have been **numerically identical since VER 0.1.4**, so the
    shared function has a single path; the `err` flags stay **sticky** (cleared only once `run()`
    has pushed them to `parser6`, so they still report every overtone of the cycle); `Qfac`
    remains an **alias for the bandwidth**, and the logged dissipation remains the **bandwidth in
    MHz, not `1/Q`** — worth knowing before drawing either number in a viewer. The threshold is a
    **drop in dB below the maximum** (`Constants.THRESHOLD_DB = 0.3`), not a fraction of it as in
    Q-1: on a baseline-corrected sweep, which crosses zero, a proportional threshold would move
    with the baseline instead of the peak.
  - Four locals `parameters_finder` returned were never read (`max_peak_fit`, `bandwidth_fit`,
    `index_f1_fit`, `index_f2_fit`); they are gone with the call.
- **The baseline polynomial order stops being a literal** — `np.polyfit`'s order for the full-span
  calibration baseline was a bare `8` in **seven** call sites (both `baseline_coeffs`, both channels
  of the peak detection, and the offline sweep viewer). Now `Constants.BASELINE_POLY_ORDER`, because
  Peak Data View has to correct the baseline the same way the detection did and a viewer with its own
  copy of that `8` is a viewer that can correct a baseline the instrument never used. Value
  unchanged, so no measurement moves. ⚠️ Still duplicated and not addressed: the three-line
  `polyfit` itself exists as `Multiscan.baseline_correction`, `Serial.baseline_correction` and
  `Calibration.baseline_estimation`.
- ⚠️ **DEV ONLY — accumulation warm-up shortened to 3 sweeps** (`Constants.environment`, 10 → 3)
  so test runs reach steady state almost immediately. **Must go back to 10 before any production
  build.** The reason is now **purely metrological** — how many sweeps go into each logged point,
  and how long the instrument takes to settle. It was briefly more than that: shortening the
  buffer also switched off the outlier rejection, which is the defect fixed below, so that part of
  the warning no longer applies. The constant carries a banner explaining both.
- **Sidebar: Plot Controls in two rows, and the overtone chips stop stretching**
  (`ui/mainWindow_ui.py`, `ui/theme.py`). AUTO / CLEAR on one row, SET REF / N-SCALE on the next, in
  a `QGridLayout` so the second button of each row lines up with the first; the slack goes to an
  empty third column, which is what keeps the four at their label width instead of letting them grow
  with the sidebar.
  - **N-SCALE is brown while off and blue while on.** That reads the other way round from Connect
    and the temperature toggle, where brown marks a "press me to undo" affordance — deliberately:
    N-SCALE is a checkable state, so brown means the plots are showing measured hertz and blue means
    they are divided by n. Same reading as the overtone chips, where accent means engaged. SET REF
    and the other outline buttons keep the family rule untouched.
  - The overtone chips are **unchanged**: they still share the row and still grow with the sidebar.
- ⚠️ **Known, deferred: the sidebar cards are clipped at the default width.** Its scroll area is
  `widgetResizable` with the horizontal bar **off**, so a container wider than the viewport is not
  scrolled — it is silently **clipped**, and the cards lose their right edge: the port combo, F9, the
  temperature spin box. Measured, `sidebarContainer.minimumSizeHint().width()`:

  | | |
  |---|---|
  | before N-SCALE (`da0f457`) | 371 |
  | N-SCALE in a single row (`2c0c062`) | **545** |
  | Plot Controls 2×2 (`45da71c`) | 371 |

  The pane's minimum is **260** and the splitter opens it at **300**, both below 371, so this is
  older than any of today's work. Raising the minimum to 380 does fix it and costs the ability to
  narrow the sidebar at all — the worse trade, so it was tried and reverted. Left as it is on
  purpose, with the numbers in the comment at the min/max.
  - ⚠️ **Pinning them was tried and reverted.** A fixed width has to fit the *narrowest* sidebar the
    pane allows — about 44 px at 260, too small to read — while a comfortable width stops the row
    shrinking and clips the cards. The two requirements conflict; the chips share the row again,
    62 px at a 300 px sidebar and 68 at 400. Along the way: `setFixedWidth` did nothing while the
    chip rule carried `min-width: 0px` (⚠️ **a style-sheet min-width overrides the widget's own
    minimum** — the buttons reported 75 and rendered at 42), and a first width of 75 px came from a
    harness that measured a card in isolation, where it takes its own size hint rather than the
    width the sidebar gives it.
- **Plot Controls gains N-SCALE** (`ui/mainWindow.py`, `ui/mainWindow_ui.py`). Pressed, each
  overtone's frequency is drawn divided by **n** — 1, 3, 5, 7, 9 — so the five can be read against
  one another instead of against their own multiples. A toggle, not a one-shot: it changes what the
  panel means for as long as it is held down.
  - It scales **whatever is drawn**. With a reference set that is the shift, Δf_n/n; without one it
    is the absolute frequency, f_n/n, and the five curves collapse onto the fundamental. One rule,
    no hidden state.
  - ⚠️ **Display only.** The buffers, the datalog and the status bar keep the measured values. The
    readout cards *do* follow, and only because they are handed the same arrays as the curves — a
    card disagreeing with the line above it is the defect this codebase keeps producing, so that
    coupling is deliberate.
  - `_update_plot` builds the plotted frequency at **four** points (single and multiscan, each with
    and without a reference); all four go through `_nscaled()`. The Δ-cursor readout needed it
    separately: `_cursor_series` reads the worker buffers directly, so ΔF would have printed
    unscaled hertz under a scaled curve.
  - While the control is off, `_nscaled` returns **the very object it was given** — same identity,
    same type — so the ordinary path is exactly what it was before. Gated, not assumed.
  - ⚠️ **Dissipation is not scaled here, and is on `impedance-analysis`.** The difference is
    deliberate and specified: what the dissipation panel holds is not the same quantity on the two
    branches. It must not be reconciled by a cherry-pick in either direction. The verification suite
    reads which behaviour it is checking from the environment, so the same gates run on both
    worktrees and each asserts its own contract.
- ⚠️ **The plot right-click menu acted on whatever plot came first, not the one clicked**
  (`ui/plotMenu.py`, `ui/mainWindow.py`). Both handlers walked a flat list of targets and took the
  first whose rectangle contained the click. `sceneBoundingRect()` is in the coordinates of the
  item's **own** scene, and every `GraphicsLayoutWidget` owns a separate one whose origin is its own
  top-left corner — rectangles from two canvases all start near (0, 0) and overlap almost
  completely, so the test was matching a click in one scene against rectangles measured in another.
  Measured:
  - main window, four panels over three canvases: right-clicking **Resonance Frequency** or
    **Dissipation** opened a menu that drove the **Temperature** plot. Two of four wrong, and the
    two panels a user actually reads were unreachable from their own menu.
  - Datalog View, three plots over two canvases: the centre of the temperature panel, scene point
    (188, 100), is inside `plt_freq`'s rectangle in the *other* scene, and `plt_freq` won.
  - the tabbed viewers (Raw Data View, and Impedance Fit on the branch) attach one canvas per tab,
    so every tab after the first hit tab 0's plots. Reasoned from the same code path, not measured:
    the offscreen platform segfaults on a `QTabWidget` full of `GraphicsLayoutWidget`s.
  - The connection was already made once per scene, correctly, and the module docstring said so.
    What was missing is that the **hit test** must be scoped to the scene that fired it. It is now,
    through a partial bound at connect time — kept in a list, because a connection to a callable
    nothing else references dies at the next collection.
  - The rectangle tested is now the `PlotItem`'s rather than the `ViewBox`'s: on Datalog View's
    dissipation panel those are `[9, 303, 1090, 261]` and `[67, 334, 1031, 187]`, so a right-click
    on the left axis opened **nothing at all**. Q-1 tested the `PlotItem`, which is why this read as
    a regression against it. Where two candidates in one scene both contain the point, the smaller
    wins.
  - `QMenu` was reached through `QtGui`, which works only because pyqtgraph's shim copies the
    widgets there for Qt4 compatibility. Imported from `QtWidgets` now; the same assumption raised a
    `NameError` elsewhere in this GUI.
- **The main window drops its own plot menu for the shared one** (`ui/mainWindow.py`). The defect
  above existed twice because the menu existed twice. `_on_scene_mouse_clicked`, `_show_plot_menu`
  and the private `_grid_on` bookkeeping are gone; `ui/plotMenu.py` does the work through the two
  hooks that were added for exactly this conversion and had no caller until now — `extra_actions`
  for the Δ-cursor item, which only two of the four panels carry, and `apply_grid` so the phase twin
  overlaying the amplitude plot still follows its grid. **View > Grid** goes through
  `set_grid_all`, so the checkbox and the per-plot menu labels read one state instead of two
  dictionaries. Closes the "`mainWindow.py` keeps its own copy" item.
- **Tools > Log Data opens the Datalog View; the matplotlib copy retires** (`ui/mainWindow.py`,
  `ui/mainWindow_ui.py`, `openQCM/data_view/` **removed**). Two viewers read the same log files. The
  one behind Tools > Log Data drew them with matplotlib on a hard-coded `#191919` that ignored the
  theme, labelled the overtones `F_0..F_9` in the numbering corrected everywhere else last month,
  kept the grid on against this GUI's convention, carried a matplotlib toolbar instead of the shared
  right-click menu, and put its x axis in bare seconds. **The Tools entry is gone too**: it was kept
  for a few commits because that is where the habit was, but it opened exactly what
  `File > Open Log…` opens — two menu items, one window, no difference between them. Also gone: a
  `MatplotlibWidget` built and hidden at start-up whether or not anyone ever opened the window, and
  the line in the commented-out button block that wired `logData_btn` to the handler.
  - Nothing is lost, and that was the condition for deleting the package rather than an
    afterthought: its two-window analysis moved first, to `core/logAnalysis.py` and into Datalog
    View's own panel.
- **Datalog View gains the two-window analysis** (`ui/dataLogView.py`, `ui/theme.py`). The
  comparison of a starting stretch of a run against a final one now sits beside the plots it is
  about. The windows are **draggable bands, not four spin boxes**: typing 300 and 80 into boxes
  means reading the times off the plot and then describing them, while a band goes where the reader
  is already looking. Each band is mirrored on both shift panels — they are x-linked, so a band on
  one would leave the other reader guessing — and kept in step by the same re-entry guard the
  reference cursors use. Pane and bands are hidden until the button in the Reference card is
  pressed, and they travel together.
  - ⚠️ The report is **deliberately blind to the reference cursor**: shift, standard deviation and
    Hadamard deviation all survive a constant subtracted from the series, which is what lets the
    cursor stay free while the analysis is on screen. Gated by moving the reference and requiring
    the rendered report to be character-for-character identical.
  - `theme.qss`'s monospace console rule covered `QTextEdit#systemLog` only, so the report pane came
    up white on the dark theme. Both names are in the rule now.
- **The two-window log analysis becomes a module, with four fixes** (`core/logAnalysis.py`, new).
  ~350 lines of per-overtone copy-paste inside the legacy viewer become a Qt-free module the viewer
  imports. ⚠️ **Four defects went with it, and the numbers the old window printed were wrong, not
  differently rounded.** Measured on a probe with a quiet 7th overtone and a noisy 9th, over two
  windows of deliberately different lengths:
  - the **9th overtone reported the 7th's** Hadamard deviation (`f_3_hadamard` for `f_4_hadamard`,
    `data_view/main.py:508` and `:516`, in both the initial and the final block): the window showed
    **0.03** where the answer is **1.30**;
  - the **final window was normalised by the initial window's length**, `6*(j-i)` instead of
    `6*(l-k)`: 1.639 against the correct 1.296. Harmless only while the two windows happen to be the
    same length, which nothing enforced;
  - the Hadamard loop read `x[i-1]`, so a window **starting at sample 0 folded the last sample of
    the run** into its first term through negative indexing: 129099 against 0 on a probe with one
    large value at the end;
  - a window **reaching past the end of the run lost its last sample** — the index search was a
    `for`/`break` loop that fell out holding the last index rather than one past it. Not an edge
    case: it is what happens every time a final window is asked to run to the end of the run.
  - Everything else is the legacy behaviour on purpose, and gated: window selection is identical
    wherever the old rule was defined, and the fundamental's Hadamard over the initial window agrees
    to 1e-12 (0.477485550623). Degenerate windows and NaN in the data now report NaN rather than a
    zero that reads as a perfectly quiet instrument.
  - ⚠️ The harness comparing the module against the legacy code is pinned to **`600a33b`**, the last
    commit where `data_view/main.py` exists; it cannot run against HEAD.
- **The compact plot card is opt-in by property, not only by name** (`ui/theme.py`). The rounded
  card with the small bold title inside it — the one the frequency and dissipation readouts wear
  above their plots — was reachable only through the two hard-coded object names
  `groupFreqReadout` and `groupDissReadout`. A card built where this file cannot see it, on a
  branch for instance, had no way to ask for the look short of adding a `#name` selector here for a
  widget that does not exist on `main`. `QGroupBox[cardCompact="true"]` now joins both rules.
  Measured on this Qt (5.9.7), not assumed: a group box that sets the property renders
  **pixel-identical** to one named `groupFreqReadout`, and differs from one that sets neither.
  ⚠️ Qt evaluates property selectors at **polish** time — set the property before the style sheet
  reaches the widget, or unpolish/polish it afterwards. No existing widget changes; nothing on
  `main` sets the property yet (`impedance-analysis` does, for its impedance panel).
- **The dissipation curves get their own colour family, and the plot panels a grey**
  (`Constants.plot_color_multi_diss` new, `plot_color_multi` last two entries, `ui/theme.py`,
  `ui/mainWindow.py`, `ui/dataLogView.py`). Both plots drew the same five blues, so a screenshot
  of the dissipation panel was indistinguishable from one of the frequency panel. Dissipation now
  carries the interface brown's family, on a ramp **specified in luminance rather than copied**:
  a first attempt that reused the blues' fractions of the way to white failed on the instrument,
  because brown starts light (Rec. 709 luminance 156 against pure blue's 18) and the five landed
  inside a 58-point band with steps of 10-13 that the eye could not separate. The ramp now locks
  the hue at the interface brown's 18.4 deg, drops saturation 0.85 -> 0.26 and solves V per entry
  so the luminances land on **70, 105, 140, 176, 211** -- steps of 35.
  - Both ends are bounded by the panels they have to survive, which pulled in the rest:
    `theme.PLOT["light"]["bg"]` was `"w"`, and on pure white the palest overtone of each series
    all but vanished. **Both panels now read the interface's own window colour** instead of
    carrying private constants -- the dark one was already `(43,43,43)` = `DARK["window"]` and is
    unchanged bit-for-bit, the light one becomes `LIGHT["window"]`, `#f2f4f7` at luminance 244.
  - On that panel the palest blue, `#BFFFFF` at 241, cleared it by **three points** and read by
    its cyan tint alone; F9 was barely there on the instrument. The last two blues come down to
    `#60CCEF` (184) and `#92E4EB` (211). Entry 4 had to move as well: capping entry 5 at 211 while
    leaving 4 at 205 would have put six points between F7 and F9, trading one defect for another.
    The three identity blues are untouched. Both series now clear the panel by 33.
  - Datalog View used **one** colour for both of its panels, so its control rows now carry **two**
    swatches, each beside the value it belongs to. Raw Data View and `plot_sweep_spline` draw
    amplitude sweeps, where the blue is correct, and are unchanged; the legacy `data_view`
    matplotlib viewer still used the blues for both of its plots; it was retired later the
    same day, see below.
  - Verified by reading the colours back **out of the live Qt objects** -- `PlotDataItem` pens and
    swatch stylesheets -- not out of `Constants`, which would only prove the constant equals
    itself. Gated on: both ramps monotonically lightening, brown steps 35 +- 0, minimum blue step
    >= 25, the three identity blues pinned, the dark panel still exactly `(43,43,43)`, and both
    series' palest entry a measured distance from the light panel.

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
- **Combo boxes and spin boxes lost the platform chrome** (`ui/widgets.py`, new; `ui/theme.py`,
  `ui/mainWindow_ui.py`, `ui/mainWindow.py`). Qt gives a `QComboBox` a square arrow button with a hard
  divider down its right edge, which is what made the dropdowns look dated. `ChevronComboBox` paints a
  thin chevron instead and the style sheet switches the platform arrow off.
  - ⚠️ **Painted, not styled.** The pure-QSS route is the CSS-triangle trick on `::down-arrow`;
    **Qt 5.9.7 does not honour it** — it paints the box, so the arrow comes out as a small dark
    rectangle. Rendered and looked at on this build before choosing. An image would mean one asset per
    theme times one per pixel density, regenerated whenever a palette colour moves. Painting costs ten
    lines, follows the palette and is sharp at any scale.
  - **Spin boxes** get the same treatment — same dated chrome, same cards, the temperature setpoint
    among them. Their buttons stay **clickable**: the sheet removes the border and the arrow, not the
    sub-control. Verified with a synthetic click in the now-invisible up button: 7 becomes 8. All ten
    widgets converted; the controller-facing API is untouched.
  - The chevron colours are class attributes on a shared mixin, since a style sheet cannot reach a
    `paintEvent`; `_apply_theme` sets them from the palette and repaints the three classes explicitly
    rather than through `QtGui.QWidget` — those widgets are only reachable there because pyqtgraph
    injects them, and leaning on that is what broke File → Open Log.
  - ⚠️ **The popup was never reached by the theme.** Its container is a separate top-level window, so a
    `QComboBox QAbstractItemView` rule in the window's sheet styles the list but not the container:
    on macOS it kept the platform frame, and its colours did not follow a theme switch. Nothing in the
    dark palette is white, which gave it away. `theme.popup_qss()` plus
    `ChevronComboBox._style_popup()` now set the sheet **and** the QPalette on the container and the
    list directly, re-applied on every `showPopup`. The list also loses its border radius: the popup is
    an opaque window, so a rounded background leaves the window's own colour at the corners. Whether
    this removes the macOS frame is unconfirmed — the platform frame is not drawn offscreen.
- **The status bar said the state three times** (`ui/mainWindow.py`, `ui/mainWindow_ui.py`,
  `ui/theme.py`). openQCM Q-1 v3.0 ends up with **one coloured dot** carrying the machine state and
  plain text beside it; NEXT had a coloured pill behind the status text, a `<font color>` tag inside
  every message, and the literal word **"Infobar"** printed in front of each one. (The hex colours
  still in Q-1's source are never drawn — its `_update_status_indicator` sniffs those stylesheet
  strings to choose the dot's colour.)
  - New `statusIndicator` label holds the dot, the only coloured thing in the bar; `infostatus` and
    `infobar` become plain text. `_status_pill` → `_status_dot` with Q-1's five states: grey
    disconnected, yellow connected-and-idle, orange processing or recoverable warning, green
    monitoring, red error. Two helpers, `_set_status(key, text)` and `_set_message(text)`, so a call
    site states the state once instead of pairing a `setText` with a stylesheet. Absolute colours, not
    palette ones — these are state semantics and must mean the same on both themes.
  - The message moves from `muted` to the plain text colour: it is now the only place a warning is
    written.
  - **Messages rewritten into Q-1's register**: `Warning: unable to apply half-power bandwidth method,
    lower and upper cut-off frequency not found` → `Warning: -3dB frequencies not found`; the
    calibration ones → `peak not found - retry`, `empty buffer - reconnect the device and retry`,
    `peak detection completed - ready for baseline correction`. The per-overtone one keeps its detail
    and gains the label — `bandwidth not measurable on F5` — because on NEXT it is genuinely ambiguous
    which overtone failed.
  - **Two gaps closed**: the connection lifecycle never reached the message line, which is what Q-1
    uses it for (select a port and click Connect / ready to connect / connected to <port> (exclusive) /
    port locked by another instance / port busy or unavailable / disconnected / acquisition stopped);
    and **in multiscan the state colour was never set at all**, not by the dot now nor by the pill
    before. All four branches now say which state they are in.
  - The 18 assignments of `color_err` are gone with the `<font>` tags that consumed them.
- **The fundamental was called the 0th harmonic in the main window** (`ui/mainWindow_ui.py`,
  `core/constants.py`) — pills, both readout cards, the hidden legacy radios and the plot legend all
  read `F0` / `0th`, while Datalog View names overtones by harmonic order. The same resonance read
  `F0` in one window and `F1` in another. Now `F1` / `D1` / `1st` everywhere it is displayed.
  ⚠️ **Displayed text only**: the widget names keep the historical `F0`, because the controller reaches
  `radioBtn_F0`, `overtoneBtn_F0`, `label_F0_col`, `F0` and `D0` as strings and renaming them is a
  separate job that could break a lookup no import would catch. The loops now carry identifier and
  label separately. Checked that nothing parses the displayed text back into an index. The log
  filename keeps its `_fundamental` suffix — changing it would split comparability with every log
  already on disk.
- **File → Open Log raised `NameError` on every click** (`ui/mainWindow.py`). `_open_datalog_view`
  called `QtWidgets.QFileDialog`, but that module imports `QtCore` and `QtGui` only. ⚠️ **Worth
  knowing beyond this bug**: the file subclasses `QtGui.QMainWindow`, which does not exist in PyQt5
  either — pyqtgraph's `Qt.py` copies every `QtWidgets` member into `QtGui` for Qt4 compatibility
  (line 299 of 0.11.0), and `mainWindow.py` imports pyqtgraph before `QtGui`. Measured:
  `QtGui.QFileDialog` is `False` before importing pyqtgraph and `True` after. So widgets reached
  through `QtGui` in that file work **by side effect of a third-party import**. The dialog is imported
  explicitly from `QtWidgets` instead, as Q-1 does at the same spot.
- ⚠️ **`Calibration.py`'s CRLF line endings were normalised by accident** in `8c40c58` and restored in
  `da81e2b`. The script that made that edit read the file with universal newlines and wrote it back
  with `'\n'`, turning all 799 lines from CRLF to LF and burying a two-line change in a 1598-line
  diff. Only the endings were restored: `git diff --ignore-all-space` against `8c40c58` is empty. **The
  repository has no `.gitattributes` and mixed endings** — 42 `.py` files are LF and five are CRLF
  (`fileStorage`, `switcher`, `Sigma_Clip`, `ReadLine`, `Calibration`). Normalising them is a
  reasonable thing to do, as its own decision; a Windows clone should set
  `core.autocrlf false` first, or git rewrites every one of them at checkout.
- **The auxiliary views did not follow the theme** (`ui/theme.py`). The window-background rule
  covered `QMainWindow` and `#centralwidget` only, and the three auxiliary views are `QDialog`s, so
  their pyqtgraph canvases went dark while the frame around them stayed at the platform default —
  with the grey info label on top of it barely readable. `QDialog` joins the rule, which fixes Raw
  Data View, Peak Data View and Datalog View at once.
- **Single-overtone mode dropped its first nine sweeps in silence** (`processors/Serial.py`).
  `elaborate()` read `freq_range_mean`, `diss_mean` and `temperature_mean` unconditionally in
  `add3`/`add4`/`add5`, but assigned them only inside the `k >= environment` branch. For every
  sweep before the circular buffer filled the method raised `UnboundLocalError`, which the caller
  swallowed with a bare `except:` — so in single-overtone mode frequency, dissipation and
  temperature never reached the plots for the first nine sweeps, and it looked like warm-up.
  `MultiscanProcess` does not have the bug because there the means are instance attributes. The
  three now start as **NaN**, which is what the ring buffers already use for "no datum yet" and
  what matters beyond tidiness: the GUI decides it is still warming up by testing whether the
  newest frequency is NaN, so pushing zeros would have replaced "processing..." with a point
  drawn at zero. Verified against `491925b`: raises for k in 1..9 before and never after, pushes
  NaN throughout warm-up, and from `k >= environment` every payload, buffer and
  `freq_res_current` identical. (`_flag_error`, which the swallowing handler set, is written in
  three places and read in none, so the spurious flag had no effect.)
- **`_queue_P_multi` was filled forever and drained by nobody** (`core/worker.py`).
  `MultiscanProcess` has always pushed the per-overtone phase sweep onto it once per sweep via
  `elaborate_ampli_phase_multi()`, but there was no `consume_queue_P_multi` and `stop()` drained
  every other queue except that one, so the queue grew for the whole life of the process holding
  five arrays of `Constants.SAMPLES` floats per sweep. Now drained on every GUI update and on
  stop.
- **Outlier rejection depended on the ring buffer being exactly 10 samples long**
  (`core/averaging.py`, new; six call sites in `processors/Multiscan.py` and
  `processors/Serial.py`). The robust average introduced in VER 0.1.6 rejected outliers **by
  accident, not by construction**: `scipy.stats.trim_mean` drops `int(proportiontocut * N)`
  samples per tail, which with `proportiontocut = 0.10` is **zero for every N below ten**. The
  rejection existed only because `Constants.environment` happened to equal 10, and any future
  resizing of the buffer would have switched it off in silence — nothing in the logged output
  would have shown that the average had become a plain arithmetic mean. Found while shortening
  the buffer for test runs.
  - `trim_count(n, proportiontocut)` keeps the proportion but adds a **floor of one sample per
    tail** and a **ceiling of `(n - 1) // 2`** — the ceiling because dropping one per tail of a
    two-sample buffer would leave nothing to average; below three samples nothing is trimmed.
    `robust_mean()` cuts k per tail and averages the rest. `scipy.stats.trim_mean` is no longer
    imported in either processor.
  - **Production values do not move**, and that was the gate rather than an afterthought: exact
    equality against scipy on the snapshot's real buffers at N=10 and N=50, across constant,
    per-overtone and jittered-with-outlier shapes for all three quantities. ⚠️ The first run of
    that gate **failed**: two buffers differed in the last bit (`25.045000000000002` against
    `25.044999999999998`) because `np.mean` adds in array order and a full `np.sort` leaves the
    retained samples ordered differently from `trim_mean`'s `np.partition`. `robust_mean` now
    partitions with the same kth arguments, which makes the agreement exact rather than probable;
    since k equals `int(proportiontocut * n)` for every n ≥ 10, anywhere the old code trimmed at
    all the result is **bit-identical**. Confirmed end to end by replaying `elaborate_multi` and
    `Serial.elaborate` against `491925b` at N=10 (260 and 42 payloads unchanged).
  - What changes is small N, which is the point. Replay with real sweep-to-sweep jitter and one
    40 Hz bad sweep: at N=10 both averages give `4998877.500000` (the outlier trimmed by both);
    at N=3 the old average leaks it and reports `4998891` — **12 Hz off** — while the new one
    lands on the median at `4998879`.
  - **Behaviour change on NaN**: NaN orders above every real number, so a single NaN is now
    discarded as the high extreme instead of poisoning the average. With `trim_mean` at N=3 one
    NaN made the logged value NaN; at N ≥ 10 it was already dropped, so this differs only on a
    short buffer. More NaNs than k still give NaN.
- **The file-based sweep viewer drew a band the instrument had not measured**
  (`sweep_data/plot_sweep_spline.py`, the third copy of the band walk — exactly the openQCM Q-1
  divergence, already present here). Two defects, both measured:
  - Its `get_left_index`/`get_right_index` returned the **index of the last sample above the
    threshold** instead of interpolating between the two samples the crossing falls between, so
    the band was quantised to the spline grid and always **too wide**: +0.75%, +1.02%, +1.02%,
    +1.64%, +2.03% on the five sweeps of the 2026-07-29 snapshot. It now draws 62.362, 61.377,
    67.889, 68.610 and 83.376 Hz — the numbers the acquisition path logs — and the edge markers
    sit exactly on the threshold, because that is where the crossing is by definition.
  - The right-hand guard read `if INDEX_OVERTONE_RIGHT > len(signal-1)`: `signal-1` subtracts one
    from every **element** and `len()` of that is `len(signal)`, so the guard was `> len(signal)`
    and could never fire before the indexing did. A sweep that never dropped below the threshold
    on the right raised `IndexError` instead of printing the warning. Measured:
    `len(signal-1) = 501` against `len(signal)-1 = 500`.
  - Verified by running `script()` headless on both versions and reading the markers off the
    figures: five panels, no exception either side, peak markers unchanged, bands narrowed to the
    measured values.

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
