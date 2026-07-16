# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

## [Unreleased] — `main`

### Added
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

### Changed
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
