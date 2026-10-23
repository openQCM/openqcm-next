# OPTIMIZATION_PLAN — openQCM NEXT, audit of 2026-10-22

> Read-only audit of `software/` (firmware listed separately). It looks for **unused** code, **inefficient**
> code and code to **restructure**. The plan was approved by Marco on 2026-10-22, and is executed one item at
> a time, each after his OK.
>
> **Baseline**
> - `main` `6a46111`, `impedance-analysis` `be7076e`.
> - Branch suite: 70 tests OK, 1 skipped (22.9 s). `main` has no `software/tests/`.
> - pyflakes: 83 reports on `main`, 107 on the branch.
> - 38 of the `.py` files are byte-identical on the two branches. Only `Multiscan.py`, `mainWindow.py`,
>   `constants.py`, `worker.py`, `mainWindow_ui.py`, `theme.py` and `Parser.py` differ.
>
> **Supersedes as input** `CLEANUP_PLAN.md` (2026-07-20, executed in part) and the untracked `CODE_ANALYSIS.md`
> (2026-08-27). Every item of both was re-checked against HEAD; see "Previous audits" at the end.

## Rules that hold for every item

- **No change of behaviour.**
  - Published quantities, datalog and sweep-dump formats, and the serial protocol stay identical.
  - PyQt5 5.9.2 with the classic `QtGui` namespace.
- **The two branches stay apart.**
  - No merge in either direction, no rebase, no revert of `1b3fe81`.
  - A code commit on `main` reaches `impedance-analysis` by `git cherry-pick`, one commit at a time, run in
    the branch's worktree. If the pick conflicts, stop and show the conflict before resolving it.
  - Documentation commits do not travel: the branch gets a hand-written "Carried from main" entry instead.
  - The branch worktree holds uncommitted MTD415T work in its CHANGELOG. Only the new entry is staged (patch to
    the index); those lines stay as they are (Marco, 2026-10-22).
- **Small, single-topic commits on `main`.** `processors/Multiscan.py` is where the two lines of work meet.
- **Every inefficiency claim carries a number measured on real code.** A dead-code claim is backed by a grep of
  the name, as identifier and as string, across both worktrees, tests and `sweep_data/` included.

## Verification protocol

`main` has no test suite, so each commit there is checked by:

1. `py_compile` of every file, plus `python -c "from openQCM.app import OPENQCM"`.
2. pyflakes: the count may only go down.
3. **Process replay.** The 45 dumps of 2026-09-11 (branch,
   `research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz`) are rebuilt into the inputs of
   `main`'s processes. The relation `g<n>` ↔ `<n>` is exact, see `software/docs/DATA_FORMAT_sweep_data.md`.
   Every parser message is captured, and the hashes before and after the change must be equal.
4. **GUI** (since C5): `guiprobe.py` drives the real `MainWindow` offscreen with the replay records; equal hashes
   before and after.
5. **Worker datalog.** Deterministic messages are fed in, `FileStorage.CSVsave_Multi` is intercepted, and the
   rows are compared byte for byte (the pattern of the branch's `tests/test_datalog_rows.py`).
6. **The instrument** — the NEXT on `/dev/tty.usbmodem88377401`, as Marco confirmed on 2026-10-22. Runs are
   headless with a private cwd and the files outside `software/`; nothing is ever flashed. They are used
   wherever the item's number is a hardware number.

On the branch, after each cherry-pick: the 70 tests, and the item's own check where it applies.

## Items

Status values: `planned`, `in progress`, `done (main <sha>, branch <sha>)`, `dropped`.

### A — measured performance, low risk

| id | what | where | evidence | branch | status |
|---|---|---|---|---|---|
| A1 | The serial read loops spin. They call `inWaiting()` then `read(n)` with no wait, and `read(0)` returns at once. `'s' in buffer` also rescans the whole buffer (up to ~288 kB) on every turn. **Fix:** `sleep(0.001)` when nothing is waiting, and test only the chunk just read. Already in HANDOFF §5 as "Windows serial anti-jitter". | `Multiscan.py` read loop (identical on both branches); `Serial.py`; `Calibration.py` (CRLF) | On a pty, one 18 001-line sweep in 2.2 s: **102 % of a core**, 357 425 turns today. With the sleep: **4 %**, 2 142 turns, same 288 028 characters, same wall time. Peak Detection runs the same loop for ~1 min. **Measured on the board (NEXT, 2026-10-22).** Multiscan, 3 cycles: 78.7 % → 11.9 % of a core, 1.28 → 0.19 s of CPU per sweep, 8.13 s per cycle either way. Single, 5 sweeps: 73.6 % → 15.7 %, 1.40 → 0.29 s per sweep. No USB error flags. Replay (fake firmware on a pty, 45 dumps): parser messages and runtime files **identical** in multiscan (544 messages), single (121) and peak detection (33). | shared; clean pick expected | done (main `438dfbf`, branch `c70b93b`) |
| A2 | `ParserProcess` is started on every START and does nothing. Its `run()` is commented out, so it inherits `BaseProcess.run`, which returns at once with no target. The acquisition child already receives the parser **unstarted** (it is pickled before `parser.start()`). **Fix:** drop `.start()`; the object stays as the holder of queues and Events. | `core/worker.py` `start()` | Spawn measured with `run.py` as main: **1.29–1.36 s of CPU and 94 MB peak per START**, exit 0. (`CODE_ANALYSIS.md` said `NotImplementedError`: false.) **On the board, 25 s multiscan:** children's CPU 6.56–6.64 → 5.11–5.15 s per START; descriptors while running 100 → 98 (main) and 103 on the branch, 6 after `close()`; Read PID during the run still answered through the parser's Event. | shared; region identical, clean | done (main `4c9003e`, branch `1102568`) |
| A3 | Every spawned child imports the whole GUI, because `run.py` and `openQCM/__main__.py` import `openQCM.app` outside the `__main__` guard. **Fix:** move the import inside the guard. | `run.py`, `openQCM/__main__.py` | One child: 1.32 s and 94 MB with the import, ~1.1 s and 67 MB without. **About −0.2–0.27 s of CPU and −27 MB per child per START.** **Measured after:** the acquisition child, 6 runs: 1.32–1.37 → 1.06–1.09 s, 104 → 77 MB, 916 → 655 modules (branch: 1.09–1.14 s, 85 MB); invisible on a 20 s board run (inside the spread). | shared; files identical, clean | done (main `26c178f`, branch `63df818`) |

### B — the 50 ms GUI tick (highest potential, medium risk: measure first)

| id | what | evidence | status |
|---|---|---|---|
| B0 | Measure the GUI process's real CPU and the per-tick time of `_update_plot` during a multiscan on the real platform. No commit. | `setData` on 10 curves of 8192 points costs **8.2–8.7 ms per tick** offscreen at any fill, paint excluded. In multiscan `_update_plot` makes 3N+1 = 16 calls per tick whether or not anything arrived: about 13 ms per tick, ~27 % of a core (an estimate, extrapolated from that measurement). The data change once per overtone sweep, ~1.8 s. | planned |
| B1 | Redraw the time series only when new data arrived: a worker revision counter, plus a dirty flag for SET REF, N-SCALE, overtone chips, theme, CLEAR and the cursors. Fold in the per-tick `loadtxt(PeakFrequencies.txt)` (0.18 ms × 20 Hz) and the discarded `nanmin`/`nanmax`. | Only if B0 justifies it, and only after Marco's OK. Conflicts are likely on the branch, whose `_update_plot` diverges. | conditional |

### C — dead code (zero behaviour; benefit is maintenance)

| id | what | branch | status |
|---|---|---|---|
| C1 | Dead modules: `processors/Sigma_Clip.py`, `Simulator.py`, `SocketClient.py` (with the import at `worker.py:6`, `Constants.SocketClient` and `simulator_default_speed`); `util/ReadLine.py` (with its two imports); `util/embedding_in_qt_sgskip.py`; `res/README.txt`. **Done:** 849 lines; pyflakes 83 → 80 (branch 107 → 104); replay identical on both branches; Worker on the board unchanged. | shared | done (main `72062b6`, branch `7d28821`) |
| C2 | Unused imports (the pyflakes list), and `progressbar` out of `requirements.txt` and `environment.yml` (it is used only in commented code). **Done:** 9 files, 31 lines; pyflakes 80 → 38 (branch 106 → 64, the rest are the branch's own: `PchipInterpolator` under E2, `plot_conductance`, two tests); imports pass with `progressbar` blocked; replay identical on `main` in all three modes and on the branch before/after. One-line conflict on the branch next to `lorentzian`. The branch single-mode baseline (112 messages, 12 sweeps) no longer reproduces even on the pre-C2 tree, which gives 121 (13 sweeps) with its first 112 equal; multiscan matches its baseline exactly. | shared; CRLF files are edited in binary | done (main `736a3a6`, branch `98823c9`) |
| C3 | Dead code in `Serial.py` and `Calibration.py`: `waveletSmooth`, `_TempCtrl`, `get_Temperature_set_Serial`, `write`, `_flag_error`, `_dummy`, `Temperature_Pid_default` (with its `loadtxt`), `_filtered_mag`, the unused phase baseline (a degree-8 polyfit on 100 001 points per START), `FindPeak` and its attributes, `_QCStype_int`, unused locals. **Done:** 86 lines; pyflakes 38 → 33 (branch 64 → 59); the phase polyfit measured at 13.5 ms per START; replay identical on `main` and before/after on the branch. **Moved to C4:** `write` and `get_Temperature_set_Serial`, whose only callers are C4's dead Worker methods. **Kept:** the phase lookup in `peak_detection_qcm_fundamental`, whose `argmax` raises on a sweep with no phase maximum and stops Peak Detection. | shared; files identical | done (main `d869d88`, branch `ab8fa43`) |
| C4 | Dead code in `Worker`: `get_Temperature_set_Worker`; `my_stop` (it calls a nonexistent `serial_close`); `serial_write`; `get_overtone`; `get_frequency_range_multi`; with `Serial.write` and `Serial.get_Temperature_set_Serial` (from C3), the targets of `serial_write` and `get_Temperature_set_Worker`; unread attributes; `_number_of_peaks` and its `loadtxt`; the `loadtxt` in `reset_buffers`. Also `_queue_F_SWEEP_multi`, which is created and never used (~5 descriptors measured per Worker). **Done:** 97 lines; pyflakes 33 → 31 (branch 59 → 57); a Worker opens 71 → 66 descriptors (branch 76 → 71); replay identical on `main` and before/after on the branch; not measured on the board (not attached). **Kept:** the `loadtxt` in `reset_buffers` as a bare call, since it stops START early on a missing or one-row `PeakFrequencies.txt`; `_fStep` and `_overtone_value`, unpacked from `get_frequencies`. **Now dead, for C6:** `Multiscan.get_Temperature_set_Serial` and `get_readFREQ`. | shared; two one-line conflicts on the branch (next to `_queue_GB_multi` and to `_cycle_D_a`) | done (main `457af43`, branch `7bdf01f`) |
| C5 | Dead code in `MainWindow`: `setColumnCount`, `clear_all_plot`, `start_download`, `dummy`, `_set_grid`, `PopUp.question_QCM`, `_my_serial`, six unread ring buffers, `_arr`, `_plt1`, `_labelref1/2`, `_vector_reference_*`, `_ser_err_usb`, `_QCS_installed`, and the per-tick labels that are never shown. Hidden widgets are **not** touched (their objectNames are reachable from QSS). **Done:** 202 lines; pyflakes 31 → 24 (branch 57 → 50). `_plt1` turned out always `None` (its `addPlot` is in a `'''` block), and the per-tick labels are `label1/2/3` (36 assignments, plus the `d1`–`d3` formatting feeding them); `start_download`'s `connect()` is in a `'''` block too. **Kept:** `firmware_version` (its read can raise). **Verified with a new GUI probe** (`guiprobe.py` in the harness: the real `MainWindow` offscreen, fed the replay records, START / reference / STOP, labels and curve data hashed per tick): identical before/after in single, multiscan and peak detection on both branches (branch: 9, 40 and 6 curves). | shared; two conflicts on the branch, on its own lines (`_diss_mode`, the impedance plots in the theme loop) | done (main `9b7a3a8`, branch `a0ef21e`) |
| C6 | Dead code in the shared part of `Multiscan.py`. Includes `get_Temperature_set_Serial` and `get_readFREQ`, dead since C4. **Not** `_frequency_buffer_*_a`/`_my_list_f_a`, which the branch reads. **Done:** 127 lines; pyflakes 24 → 23 (branch 50 → 49); also the phase half of `baseline_coeffs` (~13.5 ms per START), four unused `_temperature_buffer_1..4` and the three ring buffers rebuilt on every START. Replay identical (branch multiscan still equal to its baseline), GUI probe identical in multiscan on both branches, Worker unchanged. | shared; two conflicts on the branch where it rewrote the lines (`baseline_coeffs`, the head of `elaborate_multi`); git delimited the second one differently from the simulation and left one line to drop by hand, the result was then byte-identical to the simulated one | done (main `6288b33`, branch `667ab6f`) |
| C7 | Constants never read (list in the plan). **Kept:** `LEFT`, `RIGHT` and `FREQUENCY_STEP` (read by the branch's research scripts) and the L5/R5 family (read by `switcher`). | shared | planned |
| C8 | Commented-out code, **only in the files identical on both branches**: Serial, Calibration, fileStorage, app, popUp, plot_sweep_spline. | shared | planned |

### D — structure (optional, after A–C)

| id | what | status |
|---|---|---|
| D1 | One `load_frequencies_file`: today there are five AST-identical copies (Serial, Multiscan, worker, mainWindow, plot_sweep_spline). It is the first brick of HANDOFF §5 "Runtime files". The `_RT` variant is excluded, because its copies have already diverged. | planned |
| D2 | The Standby TEC reset in `mainWindow` re-implements `common/tecReset.reset_sequence`. | planned |

### E — `impedance-analysis` only (committed on the branch, when Marco says)

| id | what | evidence | status |
|---|---|---|---|
| E1 | `elaborate_multi` computes three series it never uses: `baseline_coeffs_Vmag()` (a degree-8 polyfit on 100 001 points, **every sweep**, on constant data), `Vmag_corr` → SG → spline, and phase → SG → spline. | **87–134 ms per overtone**, i.e. 0.4–0.7 s per ~9.3 s cycle. Processing is serial between sweeps, so the cycle shortens: published values are unchanged, the row cadence is not. | planned |
| E2 | Dead code: `parameters_finder_impedance` and helpers, `_half_bandwidth_G`, `_phase_signed`, `elaborate_conductance_multi` (it calls missing methods and `plt.show()`), the `PchipInterpolator` import, `get_masked_G_buffer`. `_phase_offset_deg` is kept, as ALGORITHM §13 asks. | — | planned |

## Not worth doing (measured)

- **Per-sweep `loadtxt` of config and PeakFrequencies:** 0.15–0.18 ms each, about 11 per cycle, ~2 ms in 9.3 s.
- **Keeping Qt out of the child processes** by moving `ElapsedTimeAxis` out of `constants.py`: −0.1 s and
  −20 MB per child (scipy dominates), at the cost of 4–5 files on both branches.
- **Vectorised ADC decode:** 24.7 → 12.5 ms per sweep, bit-identical, but 0.6 % of the cycle and inside
  `Multiscan.py`.
- **List pickling in `add_A_multi`/`add_P_multi`:** 2.5 + 3.8 ms per message. Changing it touches the message
  format Raw Data View reads.
- **Single mode, `get_freq_range_RT` on every tick:** 0.22 ms (4.4 ms/s); folded into B1 if ever.
- **Factoring Serial/Multiscan/Calibration, splitting `mainWindow.py`, and purging comments in
  mainWindow/Multiscan/worker/constants:** certain conflicts while the branches live, no runtime gain.
  Deferred until after the merge decision.
- **Firmware** (listed only, separate priority):
  - safe cleanup: dead globals, and eight identical copies of `src/ADC`;
  - bit-identical micro-gains: one print per point, an integer sum;
  - **data-changing**, so not done here: `readSynchronizedContinuous` does not wait for a new conversion; the
    tuning word goes through a 32-bit `float`, so the real step is 0.5–3.7 Hz rather than 1 Hz.

## Defects met on the way (not optimisation — for a separate decision)

- `Calibration.peak_detection_qcm_overtones`: `argrelextrema` without `[0]` (CODE_ANALYSIS #2). Still present.
- A failed `Worker.start()` leaves the serial handle closed (CODE_ANALYSIS #3). Still present.
- Multiscan: `clear()` runs on every tick for the whole cycle in which `_ser_control == environment`. Related
  to "zeros pushed during the warm-up".
- `_update_plot` resets the frequency axis label on every tick, undoing N-SCALE's "/ n".
- `if vector1.any:` without parentheses, in five places: always true.
- `pd.read_html` needs `lxml`, which neither manifest declares.
- `-s/--samples` has no effect.
- The branch's `research/admittance-circle-fit/compare_circle_fits.py` reads constants that were removed.

## Previous audits, re-checked at HEAD

**CLEANUP_PLAN.md**
- Resolved:
  - the Qt-Designer files, `data_view/`, `tab_2`;
  - the `_toggle_grid`/`_plt1` crash;
  - `csv_default_prefix`, now live;
  - the `Serial.py:495` `csv_default_filename` bug, now inside a dead string.
- Still open: Phase 1 dead modules → C1; Phase 4 → C3–C7; Phase 5 banners.

**CODE_ANALYSIS.md**
- #1 is false: the parser exits cleanly. See A2.
- #4 is fixed (`2e313b7`).
- #2, #3, #5 and #6 still stand as described. They are bugs or design choices, not optimisation.
- "No tests" is outdated: the branch has 70.
