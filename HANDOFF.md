# HANDOFF — Developer notes (openQCM NEXT)

> Technical starting point to continue development of the software and of the
> `impedance-analysis` branch. Working language: Italian in chat, English in the repo.
> Last updated: 2026-08-27.
>
> Starting a new session: paste [`docs/SESSION_PROMPT.md`](docs/SESSION_PROMPT.md)
> as the first message. It is a shortcut into this file, not a replacement for it.

---

## Working with `main` — read this before touching either branch

`main` is the production software and **does not carry the impedance analysis**. The two merges that
put it there (PRs #1 and #2) were reverted by `1b3fe81`, which restored `main` byte-for-byte to
`52a42a9`. Merging this branch into `main` is planned for the future, when the metrology is settled;
it is Marco's decision and nobody else's.

That revert leaves a trap in **both** directions, because the merge base between `main` and this
branch is `c83a820` — a commit that *had* the impedance code. Git therefore reads `main` as "deleted
the impedance code" and propagates that deletion.

### Bringing `main`'s changes INTO this branch — cherry-pick, never `git merge main`

Rehearsed end to end on 2026-07-28 with commit `251599d`; these are the commands that were actually
run, not a sketch.

**1. See what is new on `main`.** Use `git cherry`, not `git log`: it compares *contents*, so a
commit already carried over shows as `-` and one still missing shows as `+`. That keeps the list
honest even though cherry-pick gives every commit a new SHA.

```bash
git fetch origin
git --no-pager cherry -v HEAD origin/main 1b3fe81
```

**2. Decide what should travel.** This step is yours, not the command's.

- **Travels:** code, and documentation that describes something both branches share.
- **Does not travel:** documentation about one branch only. `7f80f82` is `main`'s own HANDOFF fix and
  this branch has its own equivalent section — cherry-picking it gives `UU HANDOFF.md` for nothing.

**3. Bring only what you chose**, one SHA at a time rather than a range, so a commit that should be
skipped cannot stop the whole run:

```bash
git cherry-pick 251599d
```

**4. Verify.** `status` empty, the commit on top, this branch's own content still there, and the
commit now marked `-`:

```bash
git status --short
git --no-pager log --oneline -2
git --no-pager cherry -v HEAD origin/main 1b3fe81
```

**5. Push.** `git push origin impedance-analysis`.

#### If a cherry-pick conflicts

```bash
git status --short                 # files marked UU need resolving
# edit the file, keep both sides where both are wanted, delete the <<<<<<< ======= >>>>>>> markers
git add <file>
git cherry-pick --continue
```

`git cherry-pick --skip` drops this commit and continues with the rest; **`git cherry-pick --abort`
is always safe** — it returns everything to the state before the attempt. If the conflict is not
obvious, abort rather than guess.

#### Deliberately NOT ported from `main`

`git cherry` will keep listing these with `+` forever, which is correct but looks like an oversight.
Add a line here whenever you decide to skip one, so the next person can tell "chosen not to" from
"forgotten".

| main commit | why it stays on `main` |
|---|---|
| `7f80f82` | `main`'s own HANDOFF §2 rewrite. This branch documents the same rules in this very section. |
| `d23333e` | removes the three dead Qt-Designer UI files — this branch never had them. |
| `439fc9e` | untracks `Calibration_*MHz.txt` — already untracked and ignored here. |
| `da81e2b` | restores `Calibration.py`'s CRLF endings, which a script on `main` had normalised by accident. This branch never had them normalised -- the same mistake was caught here before the commit -- so the file is already CRLF and the patch has nothing to do. |
| `e39c0ca`, `a855587` | `main`'s own CHANGELOG for the Datalog View round. |
| `ab3722a`, `6935826` | `main`'s own CHANGELOG/HANDOFF for the 2026-07-29 round. Branch-specific notes live here instead. |

⚠️ **`git cherry` also keeps showing `+` for a commit that was ported but needed conflict
resolution**, because it compares patch-ids and the resolved patch is not the original one. On
2026-07-28 `273c6a9` and `a165b40` were both carried over and both still list as `+`; only
`b19f987`, which applied cleanly, flipped to `-`. So `+` means one of three things — not ported, or
ported with a resolved conflict, or genuinely forgotten — and the table above is what separates the
first from the third. Note the second when it happens:

⚠️ **And a fourth case, found on 2026-07-29:** a commit can apply with **no conflict at all** and
still keep showing `+`. `git cherry` compares patch-ids, which hash the diff *including its context
lines* — and the context differs here wherever this branch has extra neighbours, such as the two extra
entries in the Tools menu. `c06963f` (Peak Data View) and `dd5fb37` (Datalog View) both applied
cleanly and both still list as `+` for that reason alone. So do not read `+` as "needs attention"
without checking the tables first.

| ported with conflict resolution | what had to be reconciled |
|---|---|
| `273c6a9` | `_plot_menu_targets` — kept this branch's six-plot list (so View > Grid covers the two impedance views) and dropped the right-click handler loop. |
| `a165b40` | sidebar pane wrapping, against the three-pane splitter of this branch. |
| `9694d89` | `core/resonance.py` extraction. `elaborate_multi` is where the two lines of work meet, as predicted. Kept `UnivariateSpline`/`PchipInterpolator` (the conductance splines still need them), pointed **all five** SG calls at the shared module — the impedance work added four beyond `main`'s one — and kept the branch's own appends of `frequency_resonance_G` / `half_bandwidth`. The magnitude-path band is now computed only for the error flags, so `index_peak_fit`, `frequency_resonance` and `Qfac_fit` are dead here; left in place rather than editorialising inside a cherry-pick. Verified the substituted spline is bit-identical on the snapshot sweeps. |
| `066757f` | both `consume_queue_GB_multi` (branch) and `consume_queue_P_multi` (`main`) drained, in `worker.stop()` and in `_update_plot`. |
| `4265f75` | Tools menu: kept `Conductance Data` and `Impedance Fit (live)`, added `Raw Data View` first as on `main`. |
| `0ce8a69` | the sweep dump. This branch writes a **second** series, `g<n>.txt` with the divider's raw `V_MAG`/`V_PHS`, which the shared module could not name. Rather than fork `sweepDump.py`, the `prefix` parameter was added on `main` first (`0b6c6c3`) and `sweepDump.py` taken in its final form here, so **`0b6c6c3` is already carried inside this commit** and `git cherry-pick`ing it separately reports nothing to do. Both writes now sit inside the one `if SweepDump.is_enabled():` guard. |
| `b6061b0` | `core/averaging.py`. Kept this branch's scipy interpolate imports and dropped `from scipy.stats import trim_mean`, which had no other user here. `environment` was left at 10 at this point and lowered separately by `92ce817` below. |
| `92ce817` | `Constants.environment` 10 → 3, development only. ⚠️ This commit **predates** `b6061b0`, so it carries the superseded banner — the one blaming the buffer length for the lost outlier rejection, which `b6061b0` had already made false. Resolved by taking `main`'s current text instead of the commit's own, so the block is byte-identical on both branches and both say the true thing: the reason to restore 10 is purely metrological. **Restore `environment = 10` before any production build, here as well as on `main`.** |

#### Why not `git merge main`

It conflicts on CHANGELOG.md, HANDOFF.md, README.md, conductance-calculation.md, constants.py,
Multiscan.py, worker.py, mainWindow.py and the PeakFrequencies files — and, where there is no
textual conflict, it **silently** deletes `sweep_data/plot_conductance.py`, restores the three dead
Qt-Designer UI files and re-tracks `Calibration_5MHz.txt`. Verified with
`git merge-tree --write-tree`.

Cherry-pick conflicts, by contrast, are the real ones only: where work on `main` touches the same
lines as the impedance work. `processors/Multiscan.py` is where the two lines of work actually meet.

**Corollary for whoever works on `main`: small, single-topic commits.** Cherry-pick operates per
commit, so one commit mixing three unrelated changes forces all three conflicts to be resolved at
once.

⚠️ **And one trap that has nothing to do with the two branches: untracking a file DELETES it on
every other clone.** `git rm --cached` leaves the file on the machine where you ran it, but the
commit records a deletion, so every checkout that pulls it removes the file — `.gitignore` does not
protect it. It already happened once with `data_test/`. It is also why
`software/openQCM/config.txt` is still tracked even though it is per-machine noise: it is read with
`loadtxt` at start-up by both `MultiscanProcess` and `SerialProcess`, so a clone without it does not
run. Before untracking anything, ask what reads it.

### Merging this branch into `main`, when the day comes

Revert the revert **first**, then merge:

```bash
git checkout main && git revert --no-edit 1b3fe81   # puts PR #1/#2 content back
# then merge the PR, which becomes clean
```

Resolving a direct merge by hand instead is dangerous: wherever there is no textual conflict git
keeps `main`'s deletions, leaving a hybrid that compiles and measures wrong.

## 1. Software architecture

**Multiprocessing** pipeline that keeps acquisition separate from the UI:

```
Serial/Multiscan/Calibration process  →  Worker (queues → ring buffers)  →  MainWindow (Qt, 50 ms timer)
        (child process)                                                        PyQtGraph + CSV
```

Package `software/openQCM/`:
- `core/`: `constants.py` (config), `worker.py` (multiprocessing, ring buffers), `ringBuffer.py`,
  `resonance.py`, `averaging.py`
- `processors/`: `Serial.py` (SerialProcess), `Multiscan.py` (multi-overtone; conductance on the impedance branch), `Calibration.py` (peak detection), `Parser.py`
- `ui/`: `mainWindow.py` (controller, ~4000 lines), `mainWindow_ui.py` (**programmatic UI builder**,
  GUI redesign R1; the old generated `mainWindow_new_ui.py` stays as reference only), `theme.py`,
  `popUp.py`, `rawDataView.py`, `peakDataView.py`, `dataLogView.py`, `plotMenu.py`, `widgets.py`,
  **`impedanceFitWindow.py`** (branch only)
- `common/`: `fileStorage.py`, `logger.py`, `architecture.py`, `switcher.py`, `sweepDump.py`
- Entry point: `run.py` → `openQCM.app.OPENQCM().run()`

### The shared modules are documented on `main`, not here

`core/resonance.py`, `core/averaging.py`, `ui/plotMenu.py`, `ui/widgets.py`, `common/sweepDump.py` and
the three auxiliary views all arrived from `main` on 2026-07-29. **Their rules live in `main`'s
`HANDOFF.md` §1 and §3** — the band may only be computed in `resonance.py`, the chevrons are painted
because Qt 5.9.7 ignores the CSS-triangle trick, a combo popup is two widgets and the container is not
reached by the window's style sheet, and so on. Documentation about shared code does not travel, so it
is not repeated here; read it in the other worktree.

What is specific to this branch:

- ⚠️ **N-SCALE divides dissipation here and only frequency on `main`.** The one place the two
  branches are meant to behave differently. Specified, not drift; do not reconcile it in either
  direction. `main`'s HANDOFF §3 carries the rest of the control's rules, and the shared gate reads
  which contract to assert from the environment so it runs on both worktrees.

- **Six plot targets over five scenes**, against `main`'s four over three: `_pltG` and `_pltGB`, the
  impedance dock's two views, join `_plot_menu_targets` and their canvases join the right-click
  connections. Worth knowing because the scene-scoping rule in `main`'s HANDOFF §3 bites harder the
  more canvases a window has — and `ui/impedanceFitWindow.py` attaches `PlotMenu` **per tab**, which
  is five more scenes again.

- ⚠️ **`_conductance_data_plot` was the only caller of `window_pro` left after the log-viewer
  retirement** (2026-08-27). It had copied `_raw_data_plot`'s `self.window_pro.hide()`, which
  `main` removed in the same port without being able to see this copy. Worth remembering as the
  shape of the risk: a branch-only method that begins as a copy of a `main` method keeps its bugs
  and loses its fixes.

- **`elaborate_multi` is where the two lines of work meet.** The impedance work added **four** more
  Savitzky-Golay call sites beyond `main`'s one (the phase, `Vmag_corr`, `Vphase`, the raw `Vmag`); all
  five go through `resonance.savitzky_golay`. The magnitude-path band is computed only for the error
  flags: what gets logged is the conductance-derived pair, so `index_peak_fit`,
  `frequency_resonance` and `Qfac_fit` are dead here.
- **Two extra baseline sites** read `Constants.BASELINE_POLY_ORDER` that `main` could not know about:
  `baseline_coeffs_Vmag()` in `Multiscan.py` and the same V_MAG baseline in
  `sweep_data/plot_conductance.py`.
- **The sweep dump writes a second series** here, `g<n>.txt` with the divider's raw `V_MAG`/`V_PHS`.
  It goes through the shared module via its `prefix` parameter, which was added on `main` first
  (`0b6c6c3`) precisely so this branch needs no copy of `sweepDump.py`.
- **`ui/impedanceFitWindow.py`** is branch-only: one tab per overtone like Raw Data View, all overtones
  refitted per tick because the table shows them all, only the visible tab drawn.
- ⚠️ **`Constants.plot_color_multi_g` does not track the curve palettes.** The two ramps
  (`plot_color_multi` blue, `plot_color_multi_diss` brown) arrived from `main` on 2026-08-27 and are
  specified in luminance; their rules are in `main`'s HANDOFF §3. `plot_color_multi_g` is
  branch-only, feeds 26 call sites in `sweep_data/plot_conductance.py` — conductance, phase and raw
  magnitude alike — and is a copy of an **older** blue list that was never the current one. Do not
  assume a figure from that script uses the same colours as the GUI.
- ⚠️ **`sweep_data/plot_conductance.py` still has its own `savitzky_golay`.** It differs from
  `resonance.py` only in its docstring and the wording of its exception messages — the numerical body
  is identical, so it is a benign duplicate, unlike the `plot_sweep_spline.py` copy that was removed.
  Worth folding in next time that file is touched.

## 2. Branches

- **`main`**: development line. Reconstructed history (`v0.1.5` → `v0.1.6-dev` → `v0.1.6-dev-073`)
  plus all current development (entry point, serial connection, dependencies, README, fixes).
- **`impedance-analysis`** (tags `v0.1.6G-test`, `v0.1.6G-pre-merge`): experimental
  conductance-based impedance feature.
- ✅ **The impedance branch is aligned with `main`** (merge of 2026-07-27, from `main` at 52a42a9).
  It now carries the full `main` line — `run.py`, serial connection Steps 1–2,
  requirements/environment, GUI redesign, trimmed-mean averaging, responsive calibration
  cancellation, firmware 0.1.5a — on top of the conductance feature. Repeat with `git merge main`
  **from** the impedance branch; git only replays what is new since this merge.
  The two branches stay separate until a merge `impedance-analysis → main` is decided.

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

### ⚠️ TEST-ONLY firmware variant (no-TEC board) — temporary, will be removed
`firmware/openQCM_Next_py_0.1.5a_TEST_teensy/` (`0.1.5a-TEST`) is a **throwaway internal
variant** for a special bench board that **does not mount the TEC section**. It is a copy of the
production `0.1.5a` firmware with all MTD415T/Serial1, MCP9808, fan and TEC-pin code removed (on a
no-TEC board those blocking Serial1 reads stall the sweep), and the temperature field **simulated**
(`25.00 °C` baseline + slow ±`0.05 °C` wobble; `#define USE_INTERNAL_TEMP` switches to the real
Teensy 4.0 die temperature). The DDS/ADC sweep engine and the host wire format are unchanged
(`temperature;status(0);error(0);s`), so **no software change is needed** and TEC commands are
accepted as no-ops. **Do not build features on this variant — it exists only for the current test
board and will be deleted once that board is retired.** Production firmware stays
`firmware/openQCM_Next_py_0.1.5a_teensy/`.

## 4. `impedance-analysis` branch (0.1.6G) — detail

**What it is**: impedance measurement via the **conductance spectrum G(f)** derived from the AD8302
MAG/PHASE signals (software post-processing; same firmware/protocol as the classic method).

**Where in the code (on the branch)**:
- `software/openQCM/processors/Multiscan.py` — the **exact** complex-divider inversion:
  `_phase_signed` (conditional unfold), `_RX_exact`, `_G_exact`, `_B_exact`,
  `parameters_finder_impedance_exact()` and `_half_bandwidth_G_exact()`. Wired into
  `elaborate_multi()`: the exact spectra are computed **once** and used both for the
  **published** resonance frequency / dissipation and for the live panel, so the two can
  never disagree. The RAW absolute `V_MAG` chain (`Vmag_raw_result_fit`) feeds the inversion;
  the baseline-corrected one is only kept for the classic amplitude path.
- `software/openQCM/ui/mainWindow.py` + `ui/mainWindow_ui.py` — the **live impedance panel**
  (right-hand dock): `_build_impedance_panel`, `_update_impedance_panel`,
  `_fit_circle_taubin`, plus **Tools → Conductance Data** (`actionConductance_Data`).
- Data path `Multiscan → Parser.add_GB_multi → Worker.consume_queue_GB_multi → GUI`, one
  overtone per message, `f_r` and Γ travelling with each spectrum.
- `software/openQCM/sweep_data/plot_conductance.py`: offline analysis script — the reference
  implementation everything above was validated against. Reads the `g<n>.txt` sweeps (same
  3-column layout as `<n>.txt`, but columns 2–3 are the **raw AD8302 voltages** V_MAG / V_PHS
  in volts, not dB/degrees), documented in `software/docs/DATA_FORMAT_sweep_data.md`.
- `docs/impedance-analysis/`: method documentation (`conductance-calculation.md`,
  `openQCM_Next_G_Impedance_Analysis.md`, 3 PDFs).

**State (2026-07-28)**:
- ✅ The **exact** complex-divider inversion is the **published** path. `f_r` and Γ come from
  `Y_q = 1/(M·e^{-jφ} − R17)` on the raw absolute `V_MAG`. Γ is measured **two-sided** and
  interpolated sub-sample. The old approximate `parameters_finder_impedance()` and its helpers
  (`_Zabs_Vmag`, `_G_calc`, `_B_calc`) are kept but **no longer called**.
- ✅ **Attenuator compensation fixed**: the ADC→V conversion undoes the INPB R11/R19 attenuator
  with `Constants.V_MAG_DECADE_OFFSET = 0.61069 V` (= 20.3564 dB × 30 mV/dB), derived from the
  schematic values, applied at **both** conversion sites — `_Vmag_bit_mag` and the copy inside
  `run()` that writes `g<n>.txt`. The previous hardcoded `0.600` undid exactly 20 dB and
  underestimated `M` by 4.02 %, i.e. R_m by up to 22 % at the fundamental. Verified by a synthetic
  THRU: M reads 52.301 Ω against a true 52.30 (was 50.199).
- ✅ **Phase-channel offset measured, not guessed** (`_phase_offset_deg`). The AD8302 phase output
  reads `r(f) = |φ_true(f)| − δ`, δ ≈ 7…17° per overtone. δ is estimated at runtime by requiring
  the admittance locus to be a circle (closed-form Taubin, ~3 ms/overtone), with guards that
  reject an unidentifiable estimate. See the dedicated section below — this replaced two wrong
  attempts and is the single most consequential correction of the 2026-07-28 session.
- ✅ **Live impedance panel**: G(f) and the B–G admittance circle, all overtones, matching
  colours, fitted-circle overlay. See the three `Constants.IMPEDANCE_PANEL_*` knobs.
- ✅ Validated in **air and isopropanol**, on **three central bodies and three sensor modules**.
  In air `f_r` agrees with the offline Lorentzian fit to **0.007–0.32 ppm**; circle residual
  **0.75–2.1 %** of the radius.
- The method is **always on, not selectable** (hard-wired in `elaborate_multi`).
- `elaborate_conductance_multi()` is **dead code** (UNUSED).
- The DEBUG state is gone (2026-07-27 merge): `environment` back to `10`,
  `plot_autoscale_yaxis` dropped for main's `Constants.plot_force_yrange`.

> 📌 **The step-by-step algorithm — every constant, every guard, a worked numerical example and
> the traps — is in [`docs/impedance-analysis/ALGORITHM.md`](docs/impedance-analysis/ALGORITHM.md).
> That is the document to read first, and the one that must never be lost.**

### The phase-channel offset δ — what it is and how it was found

The detector emits `|Δφ|` only, and its output carries a **global per-overtone offset**:
`r(f) = |φ_true(f)| − δ`. Two consequences that cost this session two wrong diagnoses:

- Where the true phase crosses zero (air, low damping) the **reading goes negative**, down to
  −14°. That is impossible for a magnitude detector, and it is not a local overshoot: it is
  `min(r) = −δ`, the *signature* of the offset.
- The original `_phase_signed` estimated δ as `−min(r)` and flipped the sign after the minimum.
  That is a crude but broadly **correct** estimator when a true crossing exists, and its
  conditional fold threshold (`FOLD_THRESHOLD_DEG_G = 5°`) was the guard for when it does not —
  in liquid C0 dominates, the total susceptance never reaches zero, and `−min(r)` is then
  actively wrong.

⚠️ **Two changes made on 2026-07-28 were wrong and were reverted** — recorded here so nobody
repeats them:
1. *"G from the folded phase, because G is even in φ."* True and beside the point: G is even in
   the **sign**, but the **offset** still has to be removed. Dropping the shift took the circle
   residual from 1.6–3.1 % to 4.1–14.6 %.
2. *"Local fold-overshoot repair: excise the sub-zero core, bridge with PCHIP."* Treated the
   symptom of a global offset as a local defect, and by shipping a **raw** G with a **repaired**
   B it produced a hybrid locus nobody had validated — 10–18 % residual, worse than doing
   nothing. `_phase_repair` and the `PHASE_REPAIR_*` constants are gone.

⚠️ **A third change, on the same day, was also wrong and is reverted** — this one lasted longer
because it produced a *better-looking* number.

*"Estimate δ by minimising the out-of-roundness of the locus."* The Butterworth–Van Dyke model
does guarantee the locus is a circle, so the idea is sound. The implementation is not:

- **The objective is computed on the point CLOUD, and the sign flip happens INSIDE it.** So the
  search can buy roundness by pushing δ until the flip lands on the *antipode* of the circle.
  That is exactly what it did — it returned δ up to 12° beyond `−min(r)`.
- **The consequence is a broken trajectory.** With the corrected phase sitting at +12° where it
  should be 0, the flip makes **B jump by up to 77 % of its own range** at the flip point. In air
  the jump is a chord *along* the circle, so the cloud stays round while B(f) is discontinuous.
  In water the flip fires with no fold at all and the locus **breaks into two disconnected arcs**;
  the fitted circle then comes out four times too large.
- **The rms was fooling me both ways.** It said the water fragmentation was an *improvement*
  (11.1 % against 19.8 %) because a circle through two disconnected arcs can have a small radial
  residual and no physical meaning. A continuous trajectory is not negotiable; roundness is a
  diagnostic, not an objective.
- **δ is not free to begin with.** If a fold exists, the argument of the absolute value is zero
  there, so `min(r) = −δ` *exactly*. It is measured, not fitted.

**What the published path does now** (`_phase_offset_fold`, and `--offset fold` offline):
δ = `−min(r)` when a fold exists, and **no offset and no flip** when it does not — the original
`_phase_signed` behaviour, plus the independently verified attenuator constant. Measured across
11 datasets:

| | continuity: max step of B between adjacent samples, % of B range | circle residual, air | circle residual, water |
|---|---|---|---|
| δ from the circle fit | **20–86 %** | 0.8–2.5 % | 3.1–11.1 % (meaningless) |
| **δ from the fold** | **0.5–7.5 %** | 1.2–7.9 % | 3.8–19.8 % |

An **independent** check, which does not involve circularity at all: the disagreement between the
two estimators of Γ (FIT 1 circle vs FIT 2 Lorentzian, which share nothing). Median over 55
overtones: **3.78 %** with δ from the fold against **5.03 %** from the circle fit, and on the
fundamentals the circle fit is catastrophic (setK n=1: 0.37 % against 37.6 %).

**What this leaves open, and it is the real question.** With δ pinned by the fold, the locus is
still **1.2–7.9 %** out of round in air. That residual is systematic and reproducible, not noise,
and a two-parameter reading model explains it: `r(f) = |φ(f) + φ_b| − δ`, with a board phase φ_b
*inside* the absolute value. Fitting the forward model to both channels gives φ_b = −12…−20°,
reproducible to **0.2–0.4°** across two acquisitions 83 minutes apart, and improves both channel
residuals 4–5×. But applying φ_b as a rotation *after* unfolding restores continuity without
recovering roundness (4.3 % against 4.5 %) — so φ_b as measured is not yet the whole story. See
the 2026-07-28 investigation report for the full evidence and the three options on the table.

**What the offline campaign established** (2026-07-27; datasets at
`~/claude_code/openqcm-next-impedance-datasets/2026-07-27/`, five configurations A–E):
- **The loci are circles.** 0.5–2 % rms of the fitted radius on the flanks in air.
- **A radial bulge at f_r** survives every hardware configuration: +5 % to +34 % of the radius,
  explained by a **2–6 mV** error in the V_MAG channel (no phase error reproduces it), well
  inside the AD8302's own magnitude accuracy. Near resonance `R_q = M·cosφ − R17` is a
  difference of close numbers, so `dR_m/R_m ≈ 2 % per mV` — **the circle diameter is a more
  robust R_m than the peak of G(f)**.
- **Circle centres sit low in B** (`B_c/r` = −15 % to −28 %) in every air configuration — the
  phase/reactive systematic that still needs reference-load de-embedding. In liquid the large
  ωC0 offset makes this ratio meaningless as a metric.
- ✅ **The 5° unfold threshold is validated across the air→liquid transition.** In isopropanol
  the fundamental sits at min|φ| = 2.04°, the critical intermediate case, and the rule
  correctly unfolds it (rms 0.52 % vs 33.4 % if left folded); the 3rd–9th (12.1°–43.8°) are
  correctly left alone. Right call on all five, in both regimes.
- **Savitzky–Golay bias**: with a 1 Hz sweep step, `SG_WINDOW_SIZE_G = 51` is wider than the
  FWHM of the fundamental and 3rd overtone **in air**, inflating Γ by +9 % and +16 %. `f_r` is
  unaffected (≤ 4 Hz). Irrelevant in liquid, where Γ is kilohertz.
- **Hardware diagnosis** (swap experiment): excess motional resistance follows the **sensor
  module**, not the central body (module swap → R_m ×3.4–11.2; body swap → ×0.94–1.39, with
  L_m = R_m/(4πΓ) invariant). Cleaning the crystal recovered R_m by 3.7–8.1× on the overtones
  (7th and 9th back to reference within 8 %); the **fundamental stays ~2.8× the reference**.
  Frequencies rose (Δf/n = 142…97 Hz ⇒ ~1.6–2.5 µg/cm² of a soft, non-rigid deposit).
- ⚠️ **Standing hardware limitation.** `R17 = 52.3 Ω` against a liquid load of 0.8–3.4 kΩ puts
  the whole sweep at **−23 to −36 dB** of divider ratio, against the AD8302's specified ±30 dB,
  with a resonance contrast of only 2–12 dB. Past ~1 half-bandwidth the deviation from a circle
  becomes systematic and **neither a magnitude-only nor a phase-only error explains it** — both
  channels degrade together down there. This is why the panel fits the core and not the wings.
  A larger R17 would recentre the ratio; it also changes loading and calibration, so it is a
  measurement-design decision.
- ⚠️ **Sweep window sized for air.** `LEFT = 12000 / RIGHT = 6000 Hz` around the peak. In
  isopropanol Γ reaches 2.5 kHz, so ±3Γ no longer fits above resonance on the 7th and 9th, and
  the "off-resonance" baseline (mean of the first 100 samples) is taken on the resonance skirt.

**Roadmap** (each needs a plan + approval):
1. Make the measurement **selectable** (classic vs conductance) instead of hard-wired.
2. Remove the dead `elaborate_conductance_multi()`.
3. **Reference-load / RLC-standard calibration** for metrological use — characterise δ per
   frequency on the bench instead of estimating it per sweep, which would turn the runtime
   estimate into a *check* rather than a correction. Note the "2–6 mV V_MAG systematic at
   resonance" of the 2026-07-27 analysis is now understood to be this same phase offset seen
   through the then-current pipeline.
4. Widen the sweep window for liquid work, and revisit `SG_WINDOW_SIZE_G` for the low overtones
   in air (both move Γ, hence D).
5. **How to apply a saturation mask without throwing away the band.** Implemented
   and measured on 2026-07-28, then **disabled** by decision: at a −28 dB floor it
   drops 35–63 % of the band in water and 20 % on the 9th overtone in air. It does
   fix the shape where the shape is broken (water 3rd overtone: circle residual
   18.1 % → 4.7 %, and the two Γ estimators from −5.5 % to −0.6 % apart), but the
   cost is not acceptable as a default. Directions: (a) **weight** samples by their
   expected error rather than dropping them; (b) mask **only the circle fit**,
   leaving the Lorentzian the tails that pin its background; (c) set the floor from
   the measured noise on the ratio instead of a fixed number; (d) the real fix is
   hardware — `R17 = 52.3 Ω` is far too small for a liquid load, and a switchable
   reference would put the sweep back inside the detector's window.
   `Constants.IMPEDANCE_PANEL_MASK_SATURATED` turns it back on for experiments.
6. **The liquid baseline is taken ON the resonance — biases the published Γ.**
   The sweep window is fixed at −12 kHz/+6 kHz (sized for air) while in water
   Γ_FWHM is 1.9–5.0 kHz, so `G − average(G[:100])` subtracts 13 % of the peak on
   the 3rd overtone and **66 % on the 9th**. The circle fit does not care
   (translation-invariant) but `_half_bandwidth_G_exact` does: measured against the
   Lorentzian, Γ is low by −2.5 % to **−13.9 %**, growing with overtone. Fix by
   taking the width from a Lorentzian with a free background, or by scaling the
   sweep window with the measured Γ. Changes published values, so it needs a
   decision.
7. **Decide on averaging δ across sweeps** (see the identifiability note above): removes the
   residual jitter from D and R_m on overtones with a shallow residual valley, at the cost of
   cross-sweep state and a small shift in published values. Needs two consecutive datalog CSVs
   from one run to size the benefit against the intrinsic scatter.
8. **Port FIT 1 (Taubin circle + arc-based Γ, saturation/core-masked) into the
   pipeline** for Γ and R_m: on deep fold-overshoot boards (body 3) the literal
   half-height/G_max readings measure the artifact, and the circle fit on the
   flanks is the only unbiased estimator (~ms per overtone per sweep). The
   offline reference is `sweep_data/fit_admittance.py`.
9. **Fit tooling** (`sweep_data/fit_admittance.py`, offline; the same module is
   imported by the live window at Tools > *Impedance Fit*): FIT 1 = BVD
   circle with rotation + weighted arc regression, FIT 2 = Levenberg–Marquardt Lorentzian on
   G. In clean air the two agree to 1.4–5.4 ppm on f_s and 2.5–6.4 % on Γ, both with sub-Hz
   covariance on f_s. Note their premise that all 18 001 points can be used does **not** hold
   on this hardware: past a few half-widths the locus has collapsed onto the offset point and
   the samples sit deepest in the AD8302's dynamic-range corner — without band restriction the
   9th overtone's Γ is wrong by 3–5×.

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
- **GUI refinement pass — DONE (2026-07-17, see CHANGELOG)**: single **temperature ON/OFF toggle**
  (blue/brown, gated on the serial connection, synced to firmware TEC status;
  `_toggle_temperature_control`/`_update_tec_toggle`/`_tec_on`); unified **secondary outline button
  style** in `theme.py` (Connect/Disconnect, Refresh, AUTO/SET REF/CLEAR, T SET, TEC Reset — blue
  outline, brown for the deactivate state, grey outline disabled) with widths sized to the label
  (HBox + trailing stretch); renames **AUTO / SET REF↔UNSET REF / CLEAR / T SET**; **bold card titles**
  via the QGroupBox widget font (Qt ignores font-weight on `::title`; card content reset to normal);
  **Start/Stop** larger, not bold, with ▷/□ glyphs; **Plot Controls** anchored under Temperature
  (sidebar stretch moved below it); removed redundant captions; **frequency selector shown only in
  Single Measurement** (`_source_changed` `setVisible`); **sidebar** default 300 px, resizable 260–400
  (brand `label_2` set to word-wrap to stop it pinning a ~459 px minimum); temperature setpoint +
  indicator right-aligned. ⚠️ A few small visual refinements remain (per the user, to do later).
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
