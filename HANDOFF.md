# HANDOFF — Developer notes (openQCM NEXT)

> Technical starting point to continue development of the software and of the
> `impedance-analysis` branch. Working language: Italian in chat, English in the repo.
> Last updated: 2026-07-16.

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
- `ui/`: `mainWindow.py` (controller, ~4000 lines), `mainWindow_new_ui.py` (generated UI), `popUp.py`
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
(`Constants.plot_force_yrange`) — all see §5 and CHANGELOG.

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
