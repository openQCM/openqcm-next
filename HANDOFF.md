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
acquisition buffer (see §5 and CHANGELOG).

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

Quick wins:
- **Disconnected-sensor detection**: guard on a minimum Q-factor (`min_valid_q_factor`) in
  `processors` (`parameters_finder`), so noise is not logged as a real peak.
- **Robust firmware query**: add range-priming (`1;1;1\n`) + reply-format validation in
  `ui/mainWindow.py` (adapt the regex to the `0.1.5a` version format) to survive older firmware.
- **Firmware updater .hex fix**: `firmware_update/` ships the `0.1.5` image (POT 180) while the
  software expects `0.1.5a` (POT 240) → ship the `0.1.5a` image (already in `firmware/`).

Later: peak-detection validations; UI (System Log tab, measurement cursors, light theme, overtone
quick-select); packaging (`common/resources.py` + hardcoded-icon fix, PyInstaller); cross-platform
validation; merge the impedance feature once stable (make the conductance method selectable).

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
