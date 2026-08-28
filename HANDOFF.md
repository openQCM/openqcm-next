# HANDOFF — Developer notes (openQCM NEXT)

> Technical starting point to continue development of the software and of the
> `impedance-analysis` branch. Working language: Italian in chat, English in the repo.
> Last updated: 2026-08-28.
>
> Starting a new session: paste [`docs/SESSION_PROMPT.md`](docs/SESSION_PROMPT.md)
> as the first message. It is a shortcut into this file, not a replacement for it.

---

## 1. Software architecture

**Multiprocessing** pipeline that keeps acquisition separate from the UI:

```
Serial/Multiscan/Calibration process  →  Worker (queues → ring buffers)  →  MainWindow (Qt, 50 ms timer)
        (child process)                                                        PyQtGraph + CSV
```

Package `software/openQCM/`:
- `core/`: `constants.py` (config), `worker.py` (multiprocessing, ring buffers), `ringBuffer.py`,
  **`resonance.py`** (peak detection, dissipation band, SG filter + spline — see below),
  **`averaging.py`** (robust averaging of the ring buffers — see below)
- `processors/`: `Serial.py` (SerialProcess), `Multiscan.py` (multi-overtone; conductance on the impedance branch), `Calibration.py` (peak detection), `Parser.py`
- `ui/`: `mainWindow.py` (controller, ~4000 lines), `mainWindow_ui.py` (**programmatic UI builder**,
  GUI redesign R1; the old generated `mainWindow_new_ui.py` stays as reference only), `theme.py`,
  `popUp.py`, **`rawDataView.py`** (live Raw Data View), **`peakDataView.py`** (last Peak
  Detection), **`dataLogView.py`** (File > Open Log), **`plotMenu.py`** (the one plot right-click
  menu), **`widgets.py`** (combo/spin boxes that paint their own chevron)
- `common/`: `fileStorage.py`, `logger.py`, `architecture.py`, `switcher.py`,
  **`sweepDump.py`** (development-only raw sweep dump, off by default)
- Entry point: `run.py` → `openQCM.app.OPENQCM().run()`

### `core/logAnalysis.py` — the two-window comparison, and the four numbers it fixed

The statistics behind Tools > Log Data — a starting stretch of a run against a final one — used to
live inside `data_view/main.py` as ~350 lines of per-overtone copy-paste. That package is **gone**
(retired 2026-08-27); the analysis is here, without Qt, and Datalog View's panel reads it rather
than deriving its own.

⚠️ **Four defects went out with the move, and the numbers the old window printed for them were
wrong, not differently rounded.** Measured on a probe with a quiet 7th overtone and a noisy 9th:

| | old | correct |
|---|---|---|
| 9th overtone Hadamard, final window | 0.03 | 1.30 |

- the 9th overtone read `f_3_hadamard` — the **7th's** — divided by 9, in both blocks;
- the final window was normalised by the initial window's length, `6*(j-i)` for `6*(l-k)`;
- the Hadamard loop read `x[i-1]`, so a window starting at sample 0 folded the **last** sample of
  the run into its first term through negative indexing (129099 against 0 on a probe with one large
  value at the end);
- a window reaching past the end of the run lost its last sample, because the index search was a
  `for`/`break` that fell out holding the last index rather than one past it. Not an edge case: it
  is what happens whenever a final window is asked to run to the end.

Everything else is the legacy behaviour on purpose — window selection is identical wherever the old
rule was defined, and the fundamental's Hadamard over the initial window agrees to 1e-12.

⚠️ **Three of the four reported quantities are independent of the caller's reference**: `shift`
(a difference of means), `std` and `hadamard` all survive a constant subtracted from the series.
Only the per-window `mean` moves with it. That is what lets Datalog View keep a draggable zero
while the analysis is on screen, and it is gated — moving the reference leaves the rendered report
character-for-character identical. Do not add a reference-dependent number to `format_report`
without revisiting that.

⚠️ The harness comparing this module against the legacy implementation is pinned to **`600a33b`**,
the last commit where `data_view/main.py` exists. It cannot run against HEAD.

### ⚠️ `core/resonance.py` is the only place the band may be computed

`savitzky_golay` + `parameters_finder` used to exist in **three** copies (`Multiscan.py`,
`Serial.py`, `sweep_data/plot_sweep_spline.py`). That is how openQCM Q-1 ended up drawing a band
that was not the measured one, and in NEXT the third copy **had already drifted**: it returned the
index of the last sample above the threshold instead of interpolating, overstating the band by up
to 2%. Everything — both acquisition processes and every viewer — now calls this module.

**If you need the band, import it. Do not re-derive it.** A viewer that quietly disagrees with the
instrument is worse than one that does not draw the band at all.

Things about the chain that surprise people, all commented in the module:
- The threshold is a **drop in dB below the maximum** (`Constants.THRESHOLD_DB = 0.3`), *not* a
  fraction of it as in Q-1. The sweep is baseline-corrected and crosses zero, so a proportional
  threshold would track the baseline rather than the peak.
- It applies to `spline(SG(mag − polynomial baseline))`, never to the raw amplitude.
- The two edges are **linearly interpolated** between adjacent spline points, so they are
  frequencies in Hz despite the historical `i_leading` / `i_trailing` names.
- `Qfac` is an **alias for the bandwidth**, and the logged dissipation is the **bandwidth in MHz,
  not `1/Q`**. Check this before you put either number on screen.
- The fundamental and overtone branches have been numerically identical since VER 0.1.4, hence the
  single code path.
- The polynomial order of the full-span baseline is `Constants.BASELINE_POLY_ORDER` (8). It was a bare
  literal in **seven** call sites, which is how a viewer ends up correcting a baseline the instrument
  never used. Anything that reproduces the measurement reads it from there.

## 2. Branches

- **`main`**: development line. Reconstructed history (`v0.1.5` → `v0.1.6-dev` → `v0.1.6-dev-073`)
  plus all current development (entry point, serial connection, dependencies, README, fixes).
- **`impedance-analysis`** (tag `v0.1.6G-test`): conductance-based impedance analysis. It is *ahead*
  of `main` on that feature and aligned with `main` on everything else.

### ⚠️ Moving work between `main` and `impedance-analysis` (updated 2026-07-28)

`main` **does not carry the impedance analysis.** It was merged in twice (PRs #1 and #2) and then
reverted by `1b3fe81`, which restored `main` byte-for-byte to `52a42a9`. A merge
`impedance-analysis → main` is planned for the future but is Marco's decision, not a routine step.

That revert leaves a trap in **both** directions, because the merge base between the two branches is
`c83a820` — a commit that *had* the impedance code. Git therefore reads `main` as "deleted the
impedance code" and propagates that deletion. So:

- **`main` → branch: cherry-pick, never `git merge main`.**

      git fetch origin
      git --no-pager log --oneline 1b3fe81..origin/main   # what is new on main
      git cherry-pick 1b3fe81..origin/main

  A plain `git merge main` conflicts on nine files and, where there is no textual conflict,
  **silently** deletes `sweep_data/plot_conductance.py` from the branch, restores the three dead
  Qt-Designer UI files and re-tracks `Calibration_5MHz.txt`. Verified with
  `git merge-tree --write-tree`.

- **branch → `main`: revert the revert FIRST**, then merge:

      git checkout main && git revert --no-edit 1b3fe81

  Resolving a direct merge by hand instead keeps `main`'s deletions wherever there is no textual
  conflict, leaving a hybrid that compiles and measures wrong.

- **Keep commits on `main` small and single-topic**: cherry-pick operates per commit, so one commit
  mixing three unrelated changes forces all three conflicts to be resolved at once.
  `processors/Multiscan.py` is where the two lines of work actually meet.

Full reasoning, measurements and the file-by-file list: `HANDOFF.md` on the `impedance-analysis`
branch, section "Working with `main`".

⚠️ Note the instruction that stood here before 2026-07-28 — "to align the impedance branch, run
`git merge main` from it" — is now **wrong**: it is precisely the operation that silently deletes the
branch's work.

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

### Raw Data View, and the two things it must never become

`ui/rawDataView.py` (**Tools → Raw Data View**) shows the live amplitude and phase sweep per
overtone, with the peak, the dissipation band and the threshold drawn on the fit. Ported from Q-1
v3.0 and extended to NEXT's five overtones as tabs. Two design rules hold it up, and both are easy
to break by accident:

1. **It pulls; nothing pushes into it.** The dialog owns a 300 ms timer and asks the acquisition
   object for its buffers. Do not add a `set_data()` or a signal from the worker: the pull model is
   the only reason a closed dialog costs *nothing* instead of merely being idle, and the reason the
   acquisition never waits on the GUI.
2. **It reads memory only, never a file.** The sweep dump is a separate development tool
   (`common/sweepDump.py`, below) and shares no state and no code with it. Verified by deleting the
   dump module and every reference to it and checking the dialog draws byte-identical arrays.

⚠️ **Re-resolve the worker on every tick** — `getattr(host, 'worker', None)`. START/STOP replace
that object; a reference cached at construction leaves the view frozen with nothing to say so. This
is the classic porting bug and it is silent.

The analysis runs in the GUI thread at **full sample resolution** so the band drawn is the band
logged; only what goes into the plot is decimated (`Constants.FREQ_STEP_PLOT`). Never clamp
`spline_points` or decimate the fit to save time — that draws a band the instrument did not
measure, which is exactly the failure this module exists to prevent. Only the visible tab is
analysed, so the cost is one spline per tick. Each tab frames the resonance once on its first fit
and then leaves the axes alone: at full scale a 62 Hz band inside an 18 kHz span is invisible, but
re-framing every tick would be unusable.

### The other two views: Peak Data View and Datalog View

Three auxiliary windows now, and the difference between them is the thing to keep straight.

| window | menu | reads | live? |
|---|---|---|---|
| Raw Data View | Tools | the acquisition buffers, in memory | yes, 300 ms pull |
| Peak Data View | Tools | `Calibration_*MHz.txt` + `PeakFrequencies.txt` | no, snapshot on open |
| Datalog View | File > Open Log… | a `logged_data/*.csv` the user picks | no, snapshot on open |

**Reading files is right in the last two and wrong in the first.** Peak Detection runs once and writes
its two files; a datalog is a finished run. There is nothing in memory to read in either case, and
those files *are* the record. Raw Data View is the opposite: the sweeps are in memory, and reading the
dump instead is what coupled Q-1's viewer to a debugging tool.

⚠️ **Peak Data View reconstructs two things**, because neither is stored: the baseline (from
`BASELINE_POLY_ORDER`, on the same arrays the detector used) and the phase peak. The second is not an
oversight to fix — `PeakFrequencies.txt` holds the amplitude peak **twice**
(`np.column_stack([f, f])` in `Calibration.py`), so the phase peak has to be re-derived. It is drawn
beside the amplitude peak on purpose: their disagreement is the diagnostic.

⚠️ **Datalog View has a format trap.** `FileStorage.CSVsave_Multi` always writes a **14-column
header**, but the data rows **skip** every overtone whose frequency or dissipation is zero. Measured
across 33 logs: a 10 MHz sensor writes **10-column** rows under that header. Reading columns by header
name invents two overtones on every such run. Pairs are therefore taken positionally, the row width
decides how many there are, and the harmonic order is derived from the frequencies because the file
does not record which overtones were selected.

Frequency and dissipation are shown as the shift from a **movable reference cursor** (the mean of
`REFERENCE_SAMPLES` = 5 samples). Absolute values are unreadable: five overtones on one axis span
5 to 45 MHz against a signal of a few hundred Hz.

Each control row carries **two** colour swatches, one beside the frequency value and one beside the
dissipation value. It carried one until 2026-08-27, when the two panels stopped sharing a colour;
a single swatch would now claim a curve it does not match.

**`File > Open Log…` is the only way in.** Until 2026-08-27 `Tools > Log Data` raised a second,
matplotlib viewer of the same files (`data_view/`, now removed); the entry was kept for a few
commits, then dropped as well — it opened this same window, so it was two menu items for one thing.
The old viewer's two-window comparison came along, as the panel below.

The **Two-window analysis** pane is hidden until the button in the Reference card is pressed, and
the two shaded bands on the plots appear and disappear with it — bands with no report say nothing,
and a report whose extent the reader cannot see is worse than none. Each band is mirrored on both
shift panels and kept in step by the same re-entry guard as the reference cursors, because the
panels are x-linked and a band on one of them would leave the other reader guessing. The numbers
come from `core/logAnalysis.py`; see §1 for what they mean and what they deliberately ignore.

### Datalog file names — the Q-1 rule, and the copy that defeated it

`YYYY-MM-DD_hh-mm-ss_<label>.csv` in `logged_data/`, where the label is `F0 F3 F5 F7 F9` for a
single-overtone run and `multi` for a multiscan. Ported from Q-1 v3.0 (`b6fd052`) on 2026-08-28;
before that the format was `%Y-%b-%d` with the label spelled `fundamental` / `3th Overtone`, which
put `Jul` before `Jun` in a directory listing and put a **space inside the file name**.

- The labels come from `common/switcher.py` and, in NEXT, reach **nothing but the file names**:
  `Worker.get_overtone()` has no caller in the UI (in Q-1 it fed the `info2` readout). Renaming
  them is a storage change, not a display change.
- ⚠️ **The format string lives in `Constants.csv_default_prefix` and nowhere else.** `Worker.start()`
  used to declare its own copy of it, so editing the constant renamed nothing — the kind of defect
  that reads as "the change did not work" rather than as a second definition.
- ⚠️ **Nothing composes a datalog name at import time.** `Constants.csv_filename` and
  `csv_sweeps_export_path` were `strftime` calls in the class body: they carried the moment the
  module was imported, not the moment START was pressed. Both are gone; the timestamp is taken once
  per START in `Worker.start()` and the raw-sweep dump path derives from it in `store_data`.
- Old logs keep their old names and stay readable — **nothing parses a datalog file name.** Datalog
  View decides the column layout from the row width (see its format trap above), and the harmonic
  order from the frequencies.

### Plot Controls > N-SCALE, and the one thing that differs between the branches

Pressed, every plotted frequency is divided by its harmonic order (1, 3, 5, 7, 9), so the overtones
can be read against one another. It divides **whatever is drawn**: the shift when a reference is
set, the absolute frequency when it is not.

⚠️ **Display only.** `_nscaled()` is applied where the plotted series is built and nowhere else —
the buffers, the datalog and the status bar keep the measured values. The readout cards follow
because they are handed the same arrays as the curves; that coupling is deliberate and worth
keeping, since a card that disagrees with the line above it is the recurring defect here.

Five places apply it, and a sixth would be easy to miss: `_update_plot` builds the plotted frequency
at **four** points (single / multiscan × reference / no reference), and `_cursor_series` reads the
worker buffers **directly**, so the Δ readout has to divide too or it prints unscaled hertz under a
scaled curve.

While the control is off, `_nscaled` returns the object it was given unchanged — same identity, same
type — so nothing about the ordinary path moved.

⚠️ **`main` scales frequency only; `impedance-analysis` scales dissipation as well.** This is the
one place the two branches are meant to behave differently. It is specified, not drift, and must not
be reconciled by a cherry-pick in either direction — the dissipation panel does not hold the same
quantity on the two. The divisor's docstring repeats this at the point where someone would be
tempted to "fix" it, and the verification suite reads which contract it is checking from the
environment so the same gates run on both worktrees.

### The time axis of the real-time plots

`Constants.ElapsedTimeAxis`, ported from Q-1 v3.0 on 2026-08-28. The plotted x values stay **epoch
microseconds** — buffers, datalog and Δ cursors are untouched; only the tick labels are relative:

    0    45    2:00    5:00    1:02:05        (SS under a minute, M:SS under an hour, H:MM:SS above)

The reference is latched **once** per run with `set_start_time()` (which ignores `None` and NaN) and
cleared in `start()` with `reset_start_time()`. Four axes use it: frequency, dissipation,
temperature and the TEC-current window.

⚠️ **Before the reference is latched the axis draws empty labels, and that is the point.** The
previous axis (`DateAxis(time_format='seconds')`, now removed) printed `int(value/1e6)` in that
state — the raw epoch, `1787904318` — for the whole warm-up, because in single mode the reference is
only taken when `_ser_control` reaches `Constants.environment`. An axis that says nothing is better
than an axis that says 1787904318.

⚠️ **The reset belongs to `start()`, not to `stop()`.** The finished run stays on screen after STOP
and its ticks have to keep meaning something; clearing there would blank the labels of the plot the
user is still reading. There was a commented-out block in `stop()` proposing exactly that.

⚠️ **`self.start_time` is in microseconds in both modes now.** It used to be seconds in single mode
and microseconds in multiscan, and the four calls to `SecondWindow.update_plot` compensated by
dividing by 1e6 in two of them. One unit, four identical call sites.

⚠️ **The reference is `np.nanmin(buffer)`, not `buffer[0]`.** `RingBuffer.get_all()` returns the
**newest** sample at index 0 and pads the tail with NaN — measured: three appends into a buffer of
five give `[30 20 10 nan nan]`, and its own comment saying "from the oldest to the newest" is wrong.
Q-1 takes the first non-NaN in array order, which is the newest valid sample; it works there because
it runs when the buffer holds one point. `nanmin` is the oldest timestamp actually present, which is
what the label means, and it is what the multiscan path already did. An all-NaN buffer yields NaN,
which the setter ignores.

Datalog View keeps its own `RelativeTimeAxis` — a log records relative time in seconds already, so
it would have to be scaled by 1e6 to feed this axis — but **not its own format**: both call
`Constants.format_elapsed_seconds`, the one definition, and so does the "zero at …" readout under
the reference cursor. The two windows show the same run, and a reader who has just seen `5:00` on
the instrument should not have to translate `0:05:00`. Q-1 makes the same split, with a second axis
class for its log viewer and the same format in it.

### `ui/plotMenu.py` — the plot right-click menu, once

Grid off, then Auto-scale / Reset zoom / mouse mode / grid / Export. **Every panel in the
application uses this module** — the main window included, since 2026-08-27; it had its own copy
until then, and the hooks `extra_actions` (the Δ cursors) and `apply_grid` (the phase twin's grid)
exist so that it needs no second implementation.

Three pyqtgraph facts live in that module because they cost time to find:

- `setMenuEnabled(False)` is needed on the `PlotItem` **and** its `ViewBox`; either one left enabled
  still pops pyqtgraph's own menu.
- the plots of one `GraphicsLayoutWidget` share a `QGraphicsScene`, so `sigMouseClicked` is
  connected **once per scene**, with the plot found by hit test.
- ⚠️ **and the hit test has to be scoped to the scene that fired it.** `sceneBoundingRect()` is in
  the coordinates of the item's own scene, and every `GraphicsLayoutWidget` owns a separate one
  whose origin is its own top-left corner, so rectangles from two canvases are **not comparable** —
  they all start near (0, 0) and overlap almost completely. Testing a click against every target
  regardless of scene is what made this menu act on the wrong plot for months: right-clicking the
  main window's dissipation panel drove the **temperature** plot, because that one sits in the first
  canvas and its rectangle covered the same coordinates. Measured before the fix: two of the main
  window's four panels answered with the wrong plot, and Datalog View's temperature panel answered
  with the frequency one.

The rectangle tested is the **`PlotItem`'s**, not the `ViewBox`'s — axes, title and legend margin
are part of the plot to the eye and outside the `ViewBox`, and a right-click on the axis strip used
to open nothing at all. Where two candidates in one scene both contain the point, the smaller wins.

### `ui/widgets.py` — why the chevrons are painted

`ChevronComboBox` / `ChevronSpinBox` / `ChevronDoubleSpinBox` draw their own chevron; the style sheet
switches the platform arrow off. **Do not "simplify" this into pure QSS**: the CSS-triangle trick on
`::down-arrow` is not honoured by Qt 5.9.7 — it paints the box, so the arrow comes out a rectangle,
measured on this build. An image would mean one asset per theme times one per pixel density.

⚠️ The spin buttons are **invisible, not gone**: the sheet removes their border and arrow, not the
sub-control, so clicking where the glyphs are still steps the value.

⚠️ **A combo popup is two widgets**, the list and a `QFrame` container, and the container is a separate
top-level window: a `QComboBox QAbstractItemView` rule in the window's sheet **does not reach it**. Its
colours ignored theme switches until `_style_popup()` started setting the sheet and the QPalette on
both objects directly. The popup list is deliberately square-cornered — it is an opaque window, so a
rounded background leaves the window's own colour showing at the corners. On macOS a light native
frame may still show around it; on Windows it does not.

### The overtone chips: a fixed width, and gaps that grow

`F1 F3 F5 F7 F9` in the Measurement Setup card. Widening the sidebar adds **spacing between them**,
not width: each chip is pinned at `OVERTONE_CHIP_WIDTH` = 72 px with a `Fixed` size policy, and a
stretch sits between one chip and the next so the slack lands in the gaps. Measured by driving the
row layout directly (`QLayout.setGeometry`, no `show()`, which segfaults offscreen):

| row width | before | after |
|---|---|---|
| 330 | chips 64, gaps 3 | chips 64, gaps 3 |
| 372 | chips 72, gaps 3 | chips 72, gaps 3 |
| 400 | chips 78, gaps 3 | chips 72, **gaps 10** |
| 440 | chips 86, gaps 3 | chips 72, **gaps 20** |
| 480 | chips 94, gaps 3 | chips 72, **gaps 30** |

⚠️ **The width is honoured only while `5*W + 12 <= row`.** Below that the style sheet's
`min-width: 0px` lets the layout squeeze the chips back down, so raising the constant on its own
changes nothing: at 72 the row has to be at least 372 px, which is why `sidebarPane`'s maximum went
from 400 to **520**. It is a maximum, not a default — the splitter still opens at
`setSizes([300, 900])`, so the sidebar has to be dragged wider before the extra width appears.

⚠️ **`setFixedWidth` alone does not pin these buttons.** `theme.qss` carries `min-width: 0px` on the
chip rule, and a style-sheet min-width beats the widget's own minimum — measured, the layout item
reports a minimum of 8 px however wide the button says it is, which is how the first attempt
(reverted) came to report 75 and render 42. What stops the row **stretching** them is the `Fixed`
size policy, and that is the half that matters here.

⚠️ **They still shrink below a 330 px row, on purpose.** The alternative is a row that refuses to
fit, and this sidebar clips rather than scrolls (below). Narrow sidebar, small chips, exactly as
before; wide sidebar, chips at 64 and air between them.

At 72 px the row's minimum is 372 and the sidebar container's 420, against 387 and 435 for the
stretching row it replaced — so the clipping described in §5 is slightly looser, not fixed: the pane
still allows 260. Every extra pixel of chip costs five of container minimum, which is the budget to
spend when tuning this.

### The status bar: one dot, plain text

The machine state is the **colour of one dot** (`statusIndicator`), as in Q-1 v3.0: grey disconnected,
yellow connected and idle, orange processing or recoverable warning, green monitoring, red error.
`infostatus` and `infobar` are plain text beside it. Write through `_set_status(key, text)` and
`_set_message(text)` rather than pairing a `setText` with a stylesheet.

It used to say the state three times — a coloured pill, a `<font color>` inside the message, and the
literal word "Infobar" printed in front of it. The dot colours are absolute, not palette entries: they
are state semantics and must mean the same on both themes.

### ⚠️ Sweep dump: development only, off by default

`common/sweepDump.py` is the only writer of `sweep_data/<n>.txt`, gated by
`Constants.dev_sweep_dump` (default `False`). Enable it for a session without touching source:

```bash
OPENQCM_SWEEP_DUMP=1 python3 run.py
```

**Tools → Raw Data (from sweep files)** — the older matplotlib viewer — is hidden while the dump is
off, since it would only open an empty or stale window. It is kept working (it now calls
`resonance.py`), but the live view is the one to build on.

⚠️ **`sweep_data/` is overwritten on every acquisition.** Copy the files somewhere else before
analysing them.

### `core/averaging.py` — why the buffer length no longer decides robustness

`robust_mean()` replaces `scipy.stats.trim_mean` at the six places that average the raw frequency,
dissipation and temperature buffers. The estimator is the same (sort, drop k per tail, average the
rest); what changed is how k is chosen.

`trim_mean` drops `int(proportiontocut * N)` samples per tail, which with `proportiontocut = 0.10`
is **zero for every N below ten**. The outlier rejection VER 0.1.6 was introduced for therefore
existed only because `Constants.environment` happened to equal exactly 10 — a coincidence, not a
property, and one that any resizing of the buffer would have destroyed **in silence**, with nothing
in the logged output to show that the average had become a plain arithmetic mean.
`trim_count()` adds a floor of one sample per tail and a ceiling of `(n-1)//2`.

⚠️ **If you touch this, the gate is exact equality against `scipy.stats.trim_mean` at N=10 and
N=50 on real buffers.** Production values must not move. Two things learned by tripping over them:
- k equals `int(proportiontocut * n)` for every n ≥ 10, so wherever the old code trimmed at all the
  result must be **bit-identical**, not merely close.
- ⚠️ `np.mean` adds in array order, so `np.sort` and `np.partition` give results differing in the
  last bit even on the same retained samples (measured: 25.045000000000002 against
  25.044999999999998). `robust_mean` partitions with the same kth arguments as `trim_mean` for
  exactly this reason. Do not "simplify" it to a full sort.

**NaN is trimmed, not propagated**: it orders above every real number, so one NaN goes out with the
high tail. With more NaNs than k the result is still NaN. This differs from the old behaviour only
on a short buffer (at N ≥ 10 `trim_mean` already dropped it).

### The two curve palettes, and why the light panel is grey

`Constants.plot_color_multi` (frequency, blue) and `Constants.plot_color_multi_diss`
(dissipation, brown) are **two ramps specified in luminance**, not two lists picked by eye. Read
them from `Constants`; nothing may hard-code a curve colour.

Rec. 709 luminance, the number every decision below is made on:

| # | frequency | Y | dissipation | Y |
|---|---|---|---|---|
| 1 | `#0000FF` | 18 | `#873814` | 70 |
| 2 | `#007FFF` | 109 | `#AE5A34` | 105 |
| 3 | `#00BFFF` | 155 | `#CE7E5B` | 140 |
| 4 | `#60CCEF` | 184 | `#E5A487` | 176 |
| 5 | `#92E4EB` | 211 | `#F7CBB7` | 211 |

⚠️ **A ramp that mirrors another ramp's *shape* is not a ramp that can be read.** The
first brown series reused the blues' fractions of the way to white. Because brown starts light
(156 against pure blue's 18), the five landed inside a 58-point band with steps of 10-13, and on
the instrument the middle overtones were not separable. The brown is now hue-locked at 18.4 deg
with saturation falling 0.85 -> 0.26 and V solved per entry for the target luminance: steps of 35.

⚠️ **Both ramps are bounded by the panels they are drawn on**, so the panels are not
free either. `theme.PLOT[*]["bg"]` reads the interface's **own window colour** — `DARK["window"]`
(43,43,43) and `LIGHT["window"]` `#f2f4f7` at 244. One dict, four canvases: the main
window and all three auxiliary views set their background from it. The light panel was `"w"`, and against pure
white the palest entry of each series all but vanished. Two consequences worth knowing:
- The ceiling of both ramps is **211**, which clears the light panel by 33. The palest blue used to
  be `#BFFFFF` at 241 — three points from the panel — and read by its cyan tint alone.
- Entry 4 of the blue moved too. Capping entry 5 at 211 while leaving 4 at 205 would have left six
  points between F7 and F9: one defect for another. The **three identity blues (1-3) do not move**.

Still on the blues in both panels: `plot_color_multi_g`, the branch-only hex mirror used by the
conductance plots — a copy of an *older* blue palette that has never tracked this one. (The legacy
`data_view` viewer was the other one; it was retired on 2026-08-27.)

Raw Data View and `plot_sweep_spline` draw amplitude sweeps; blue is correct there.

### ⚠️ `Constants.environment` is currently a development value

It is **3**, not the production **10**, so test runs leave warm-up almost immediately.
**Restore 10 before any production build.** The reason is now **purely metrological** — how many
sweeps go into each logged point, and how long the instrument takes to settle. It used to be more
than that (shortening the buffer switched off the outlier rejection); `core/averaging.py` removed
that dependency, so do not repeat the old warning. The constant carries a banner explaining both.

### Also done on main
`run.py` entry point; full README; `requirements.txt` / `environment.yml`; Raw Data fix
(restored the functional `sweep_data/*.txt`); **robust trimmed-mean averaging** of the raw
acquisition buffer; **observable plots default to Y autorange** in development
(`Constants.plot_force_yrange`); **responsive peak-detection (calibration) cancellation**
(ported from Q-1 v3.0 — Stop now interruptible mid-sweep, clean shutdown); **GUI theme system
dark/light** (`ui/theme.py` + View → Theme menu, Phase 0 of the GUI redesign); **phase sweep
plumbed into the GUI process** (`consume_queue_P_multi`, which also closed an unbounded
`mp.Queue`); **single-overtone warm-up bug fixed** (the first nine sweeps used to be dropped by a
swallowed `UnboundLocalError`); **outlier rejection made a property of the average instead of a
coincidence of the buffer length** (`core/averaging.py`) — all see §5 and CHANGELOG.

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


> 📌 **Source-code cleanup**: a full plan already exists in
> [`CLEANUP_PLAN.md`](CLEANUP_PLAN.md) — produced by a read-only audit on
> 2026-07-20 (baseline `main` @ `630e898`), not yet executed. Dead code, unused
> structures, redundancies, with a per-item confidence tag and a verification
> protocol. Read its §0 before touching anything: PyQt5 5.9.2 with the classic
> `QtGui` namespace must not be "modernised", and Qt reaches methods through
> `connect()`, objectName and overrides, so nothing gets deleted without grepping
> its name as a string across all of `software/`.

### Runtime files: the application must survive their absence

Deciding what is versioned turned out to be the easy half. On 2026-07-28 the runtime
data was untracked (`Calibration_*MHz.txt`, `PeakFrequencies*.txt`,
`sweep_data/*.txt`) and the PeakFrequencies part had to be reverted the same evening,
because the application **does not start** without them and the tool that writes them
lives inside the window that will not open. Two work items, in order:

1. **Make the reading side tolerant, and its errors actionable.** ~30 call sites read
   runtime files with a bare `loadtxt`, which today produces a traceback in whichever
   process happens to hit it first:

   | file | `loadtxt` call sites | read from |
   |---|---|---|
   | `PeakFrequencies.txt` | 11 | `mainWindow`, `worker`, `Multiscan`, `Serial` |
   | `PeakFrequenciesRT.txt` | 2 | `Multiscan`, `Serial` |
   | `Calibration_*MHz.txt` | ~4, through a `filename` variable | `Multiscan`, `Serial` |
   | `config.txt` | 14 | `mainWindow`, `Multiscan`, `Serial` |

   One helper rather than thirty try/except: `FileStorage.load_runtime(path, what,
   remedy)` raising a `MissingRuntimeFile` that carries the remedy. Then two
   behaviours, and the distinction is the point — **start-up paths degrade**
   (`load_frequencies_file()` returns `None`, the legend draws defaults, the status
   bar says what is missing, Peak Detection stays reachable), while **paths inside a
   running measurement raise and stop cleanly**, because there the file must exist and
   carrying on would publish meaningless numbers.
   Verification: rename the files, start the GUI, check it comes up and shows the
   message instead of dying.
2. **Then `config.txt` can follow.** It is the last tracked runtime file, read at
   start-up by both `MultiscanProcess` and `SerialProcess`, and it is the reason every
   pull needs a stash. Once item 1 is in, untrack it — and only then.

⚠️ Whoever does item 1: do not untrack `PeakFrequencies*.txt` before it is finished
and tested. The `.gitignore` says so too, next to those two lines.

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
       the datalog names (serial `<ts>_F<n>.csv`, multiscan `<ts>_multi.csv`, calibration "").
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
  app.
  ⚠️ **And `QtGui` does not actually contain those widgets** — not even in 5.9.2. It works because
  pyqtgraph's `Qt.py` copies every `QtWidgets` member into `QtGui` for Qt4 compatibility (line 299 of
  0.11.0), and `mainWindow.py` imports pyqtgraph *before* `QtGui`. Measured: `QtGui.QFileDialog` is
  `False` before importing pyqtgraph and `True` after. So every widget reached through `QtGui` in that
  file works **by side effect of a third-party import**. It already cost one traceback in production
  (`File > Open Log`, fixed in `badd438`). In new code import from `QtWidgets` explicitly. **Python 3.9.12**. Tested on macOS Intel and Apple Silicon. Conda is the reproducible route
  (see `software/environment.yml`).
- ⚠️ **A QSS property selector is evaluated at polish time, not continuously.**
  `QGroupBox[cardCompact="true"]` in `theme.qss` lets a card opt into the compact look without this
  file knowing its object name — useful for widgets built on a branch. But `setProperty` after the
  style sheet has been applied changes nothing on screen: set it in the builder (which runs at
  `setupUi()`, before `_apply_theme()`), or call `style().unpolish(w)` then `polish(w)`. Qt maps a
  Python `True` to the string `"true"` the selector matches.

- **Runtime-rewritten data files.** Only three are still tracked: `PeakFrequencies.txt`,
  `PeakFrequenciesRT.txt` and `config.txt`. `Calibration_5MHz/10MHz.txt` and `sweep_data/*.txt` were
  untracked on 2026-07-28/29 and are regenerated by Peak Detection and by an acquisition; the
  PeakFrequencies pair had to **stay** versioned, because `load_frequencies_file()` reads them while
  the window is being built and the only thing that writes them is a button inside that window, so a
  clone without them does not start. Same reason for `config.txt` (`loadtxt` at start-up in both
  `MultiscanProcess` and `SerialProcess`). Mark the tracked ones **`skip-worktree`** on each machine
  so runtime rewrites do not pollute git — a **local, per-clone** setting:

  ```bash
  git update-index --skip-worktree software/openQCM/PeakFrequencies.txt software/openQCM/PeakFrequenciesRT.txt
  ```

  ⚠️ Untracking a file **deletes it** on every other clone that pulls; `.gitignore` does not protect
  an already-tracked file. Before untracking anything, ask what reads it. And if you ever see the
  three symptoms together — clean `git status`, `git checkout --` saying "did not match any file(s)
  known to git", and a merge complaining about local modifications to those same files — that is the
  `skip-worktree` bit: diagnose with `git ls-files -v | grep ^S`.

- â ï¸ **Mixed line endings, and no `.gitattributes`.** 42 `.py` files are LF and five are CRLF
  (`fileStorage`, `switcher`, `Sigma_Clip`, `ReadLine`, `Calibration`). Two consequences. **On
  Windows**, set `git config --global core.autocrlf false` *before cloning*, or git rewrites every
  file at checkout and the clone looks entirely modified. **When editing with a script**, read and
  write in binary: `open(p).read()` uses universal newlines and `write()` emits `'\n'`, which
  silently converts a CRLF file whole â it happened in `8c40c58` and had to be undone in `da81e2b`,
  where a two-line change arrived as a 1598-line diff. Normalising all five is a reasonable decision
  to take deliberately; it has not been taken.
- **The GUI *can* be exercised headless** — the old "leave it all to a human" is only half true, and
  the difference matters because logic bugs are cheap to catch this way. Static checks first
  (`python -m py_compile ...`, `python -c "from openQCM.app import OPENQCM"` from `software/`), then
  drive real widgets under `QT_QPA_PLATFORM=offscreen`: build `Ui_MainWindow` on a bare
  `QMainWindow`, or instantiate a dialog against a stub host and call its refresh directly (this is
  how Raw Data View's bands, worker re-resolution, one-shot framing and closed-dialog behaviour were
  verified before any on-device run). Three traps, all found the hard way:
  - **hold the `QApplication` in a name.** `QApplication.instance() or QApplication([])` as a bare
    expression leaves it unreferenced, it is collected at once, and the process segfaults with no
    output at all — buffered stdout dies with it, so it looks like the script did nothing.
  - **do not call `show()`** on the dialog; it segfaults offscreen. Capture with pyqtgraph's
    `ImageExporter` on `canvas.scene()` instead, which needs no visible window.
  - **do not re-import two copies of `openQCM`** from different trees into one Qt process; it
    segfaults. Use a subprocess per tree.
  Fonts are missing offscreen (`QFontDatabase: Cannot find font directory`), so rendered captures
  have no text — expected, not a bug. The on-device smoke test still belongs to a human.
- **Every change goes into `CHANGELOG.md`** (unless explicitly told not to, e.g. a fix that just
  restores pre-existing behavior); keep the **README** aligned with substantial changes. Commits use
  Conventional Commits + a `Co-Authored-By` trailer.
- Propose a plan and wait for approval before invasive changes.
