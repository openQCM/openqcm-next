# Plan — the phase-shifted Lorentzian as the published estimator, B(f) in the main panel, a live fit window that shows only what is published

*Written 2026-09-16 on Marco's four goals for the `impedance-analysis` branch. Analysis first, then the design,
the subtasks and the decisions that are his. Nothing here is implemented yet; each subtask is one commit,
executed after his ok, one at a time.*

## 0. The goals and the rule

1. Main GUI: remove the admittance-circle plot (B against G), put the susceptance B(f) in its place.
2. Live fit window: show only what the acquisition process uses. Everything else is noise.
3. The phase-shifted Lorentzian fitted to G alone becomes the estimator of f_res and Γ in the acquisition
   process and in the live fit window.
4. The maximum of G with the half-height width stays as the fallback, computed exactly as today.

The rule that decides every detail below: **what the live fit window shows is what the process used to
produce the logged numbers** — the same fit, the same parameters, evaluated from the values the process
shipped, never refitted in the GUI.

Out of scope, on purpose: the chain up to G (smoothing, fold decision, offset δ, exact inversion), the
definition of D = 2Γ/f, the sweep window, the saturation mask machinery (off by decision), N-SCALE.

## 1. What the code does today

Read on 2026-09-16; line numbers refer to the branch at `1fad6ee`.

**Acquisition** — `processors/Multiscan.py::elaborate_multi` (846–1300). After the exact inversion, G is read
by `parameters_finder_impedance_exact` (519): `argmax` for f, `_half_bandwidth_G_exact` for the two-sided
half-height Γ, returned as a `GBand`. These feed three things:

- the published pair: `_my_list_f` ← f_argmax, `_my_list_d` ← 2Γ/f·10⁶ (1190–1228), then `robust_mean` over
  the last `environment` sweeps (1233–1247) into the F/D multi messages (1301–1306) and the datalog;
- `freq_res_current_array` (1266–1272), the value the sweep tracker follows;
- the G/B message for the GUI (1156–1180): one overtone per message, eleven fields —
  `[idx, f, G − baseline (mS), B − baseline (mS), f_argmax, Γ, δ, masked %, f_left, f_right, half_level]`,
  clipped to ±3Γ (`IMPEDANCE_PANEL_BAND_GAMMA`). The baseline is the mean of the first 100 samples of each
  curve. The worker (`core/worker.py:675`) unpacks it with `len()` guards, so appended fields are safe.

**Main window, right dock** — `ui/mainWindow_ui.py::_build_impedance_panel` (103–149) builds two
`GraphicsLayoutWidget`s, `pltG` and `pltGB`, in a vertical splitter inside the card "Impedance — exact
formula". `ui/mainWindow.py` draws them: `_pltG` is G against f − f_published for all overtones (2337–2352);
`_pltGB` is the B–G locus with a Taubin-trimmed circle overlay (`_fit_circle_taubin`, 3497–3543, gated by
`IMPEDANCE_PANEL_SHOW_FIT` and `IMPEDANCE_PANEL_FIT_GAMMA`), refreshed in `_update_impedance_panel`
(3545–3671) and rebuilt per acquisition in `_build_impedance_curves` (5912–5945). `_pltGB` is also in two
theme/palette lists (2011, 5765).

**Live fit window** — `ui/impedanceFitWindow.py` (531 lines). Loads `sweep_data/fit_admittance.py` by path on
first open and **refits in the GUI**: FIT 1 (BVD circle, arc-based f_s and Γ, rotation θ) and FIT 2
(symmetric Lorentzian, linear background) on the shipped spectra decimated to 250 points. Three panels per
overtone tab (G + FIT 2, B + FIT 1, locus + FIT 1 circle) and a 12-column table (δ, masked, f_s FIT 1, Γ, D,
R1, L1, rms, f_s FIT 2, dΓ, df_s). **None of these numbers is what the process publishes**: this is the
window that violates the rule, and the reason the estimator work of 2026-09-11…15 had to be done offline.

**Impedance Data View** — `ui/impedanceDataView.py`: reads the worker's buffers, computes nothing, draws
the published f_r and the two half-height crossings (`get_band_G_buffer`), falling back to f_r ∓ Γ where a
crossing is missing. Unaffected in structure by this plan; see 2.5 for the one adaptation.

**Datalog** — `<ts>_multi.csv` (published pair) and, with `DATALOG_AMPLITUDE_TOO`, `<ts>_multi_amplitude.csv`
(main's pair), both through `FileStorage.CSVsave_Multi` with its fixed 14-column header; the amplitude pair
rides as the third element of the F/D messages (`worker.py:536–541, 583–588`) and is written beside the
published one (996–1002, 1043–1049).

**Tests** — no versioned test suite (`grep def test_` finds nothing outside `sweep_data/`); verification on
this repo is static checks plus headless scripts run ad hoc (HANDOFF §6). The estimator module below is the
first piece that can carry a versioned headless test without Qt.

**Measured on 2026-09-16**, the cost of the fit inside the process (research `psl_lib.fit`, TRF, tolerances
10⁻¹⁴), per overtone and sweep:

| sweep | points in ±3Γ | full grid | decimated to ≤ 300 points | result difference |
|---|---|---|---|---|
| air n = 1 | 393 | 17 ms | 16 ms | none |
| air n = 9 | 1219 | 18 ms | 16 ms | none |
| water n = 3 | 7793 | 29 ms | 12 ms | none to the Hz |
| water n = 9 | 12341 | 47 ms | 14 ms | none to the Hz |
| isopropanol n = 9 | 14135 | 53 ms | 11 ms | none to the Hz |

A sweep takes seconds; five overtones add at most 80 ms per cycle on the full grid, 60 ms decimated. Not a
constraint, but the number is printed once at the first fit so it stays measured.

## 2. Design

### 2.1 The estimator lives in one shipped module: `openQCM/core/lorentzian.py`

Pure numpy/scipy, no Qt, no process state — the same contract as `core/resonance.py`, and for the same
reason: one implementation called by the process, by the tests and by the research scripts
(`research/…/scripts/psl_lib.py` will import it instead of carrying its own copy).

```
PSLFit = namedtuple("PSLFit", "fres gamma phi_deg amplitude g_off rms_rel n_fit ok reason cost_ms")

def rotated_lorentzian(freq, fres, gamma, phi, amplitude, g_off)      # Re of A e^{jφ}/(Γ − j(fres − f)) + G_off
def fit_phase_shifted_lorentzian(freq, G, f_seed, gamma_seed,
                                 band=Constants.PSL_BAND_GAMMA,
                                 max_points=Constants.PSL_MAX_POINTS) -> PSLFit
def accept(fit, f_seed, gamma_seed, freq_window) -> (bool, reason)
```

Model: Johannsmann, *Sensors* 2021, 21, 3490, eq. 3, real part, five parameters (A = G_max·Γ, f_res, Γ, φ,
G_off), frequencies in kHz from the seed and G in mS inside the solver (the Jacobian columns otherwise
differ by twenty orders of magnitude). Γ is the half width at half maximum, the datalog's Γ. Seeds are the
values the process already has: f_argmax and the half-height Γ. The fit window is ±band·Γ_seed, decimated
uniformly to at most `max_points` samples.

`accept()` is the fallback gate, every rejection with a reason string:

| check | limit (constant) | measured on the 45 sweeps of 2026-09-11 |
|---|---|---|
| solver converged | — | always |
| f_res inside the fit window | — | always |
| Γ / Γ_seed within `PSL_GAMMA_RATIO` | (0.3, 3.0) | 0.93–1.08 |
| \|φ\| ≤ `PSL_PHI_MAX_DEG` | 60° | 5–28° |
| rms ≤ `PSL_RMS_MAX` of the range of G | 5 % | 0.16–0.5 % liquid, 1.0–2.6 % air |

Constants added: `IMPEDANCE_ESTIMATOR = "lorentzian"` (the other value `"argmax"` restores today's
behaviour in one place), `PSL_BAND_GAMMA = 3.0`, `PSL_MAX_POINTS = 300`, `PSL_RMS_MAX = 0.05`,
`PSL_PHI_MAX_DEG = 60.0`, `PSL_GAMMA_RATIO = (0.3, 3.0)`. (`DATALOG_FIT_TOO` dropped with D2.)

### 2.2 The process publishes the fit, falls back to the maximum, and says which it did

In `elaborate_multi`, right after `parameters_finder_impedance_exact`:

```
fit = fit_phase_shifted_lorentzian(freq_range, G_exact_S, f_argmax, Γ_hh)
ok, why = accept(fit, …) if Constants.IMPEDANCE_ESTIMATOR == "lorentzian" else (False, "estimator=argmax")
f_pub, Γ_pub = (fit.fres, fit.gamma) if ok else (f_argmax, Γ_hh)
```

`_my_list_f`, `_my_list_d` (D = 2Γ_pub/f_pub·10⁶) and `freq_res_current_array` take the published pair;
`robust_mean` and the datalog are untouched.

**The observable of the fallback** (the rule of `dead-code-hidden-by-its-fallback`: a path with a fallback
that gives a plausible number needs a numeric witness):

- per-overtone counters `_psl_used[n]`, `_psl_fallback[n]`, shipped in the G/B message and shown in the fit
  window as "published by: fit — 0 fallbacks in 143 sweeps";
- a System Log line at the first fit of each overtone (with the cost in ms) and at every change of source,
  with the reason and the rms: `overtone 3: published by fallback (rms 7.2 % > 5 %), fit was f_res … Γ …`.

**The G/B message** gains appended fields (the consumer is already `len()`-guarded):
`[…, fit.fres, fit.gamma, fit.phi_deg, fit.rms_rel, fit.amplitude (mS·kHz), fit.g_off − g_baseline (mS),
source (1 fit / 0 fallback), used_count, fallback_count]`. G_off is shipped **relative to the same baseline
as the shipped G**, so the window can draw the curve over the shipped points without knowing the baseline.

~~**A third datalog**~~ — **dropped by Marco (D2)**. What follows was the proposal, kept for the record: `<ts>_multi_fit.csv` (flag `DATALOG_FIT_TOO`, this branch only, like the amplitude
one): `Date, Time, Relative_time, Temperature`, then per overtone `Phi_n, Rms_n, Source_n, Fargmax_n,
GammaHH_n`. It carries what `<ts>_multi.csv` cannot — φ (Marco: "if published, φ must be logged"), the fit
quality, which estimator produced each row, and the fallback pair at the same instant, so the comparison
this week was done by hand stays possible on every run. New `FileStorage.CSVsave_MultiFit` with its own
header; the values ride as the fourth element of the F/D messages the way the amplitude pair rides as the
third.

### 2.3 Main panel: B(f) instead of the locus

`mainWindow_ui`: `pltGB` → `pltB`, same splitter, same card. `mainWindow`: `_pltGB` → `_pltB`, title
"Susceptance B (exact)", x = frequency offset from the published f (the G panel's axis), y = B in mS, x-linked
to `_pltG`; per-overtone curves as for G; `_fit_circle_taubin`, `_pltGB_fitline`, `IMPEDANCE_PANEL_SHOW_FIT`
and `IMPEDANCE_PANEL_FIT_GAMMA` removed; the two palette lists updated; `_build_impedance_curves` rebuilt.

Two things Marco should know before choosing (decision D1):

- **Which B.** Today the shipped B has the mean of its first 100 samples subtracted, like G. In liquid that
  edge value sits 73–140 µS above the circle centre (measured 2026-09-14), which is what made B look
  asymmetric in the live window. Recommendation: ship and draw **B as the chain computes it**, no subtraction
  — the display then shows ωC0 as a level, which is physical, and the zero crossing where it is. G keeps its
  baseline removal because the Data View's half-height marker is defined on that curve.
- **Where the peak of G will appear.** The G panel's x axis is f − f_published. With the fit published, the
  visible maximum of G sits at +Γ·tan(φ/2) from zero: 2–47 Hz in air, 170–700 Hz in liquid. That is the
  measured bias made visible, not a bug; the fit window explains it with the marker of the fallback.

### 2.4 The live fit window rebuilt around the published fit

`ui/impedanceFitWindow.py`, rewritten, keeping its skeleton (own timer started on show and stopped on hide,
per-overtone revision counter, tabs, `PlotMenu`, theme, freeze):

- **one panel per overtone**: the shipped G (points, overtone colour) with the process's fit curve evaluated
  from the shipped parameters (dashed, `FIT_COLOUR`), the published f_res marker, the fallback marker (argmax)
  and the ±3Γ fit window shaded; beneath it a **residual strip** (measured − fit, percent of the range of G)
  — it is the quantity the acceptance gate reads, so it belongs on screen;
- **table**: `n | published by | f_res [Hz] | Γ [Hz] | D [ppm] | φ [°] | rms [%] | f argmax [Hz] | Γ half height [Hz] | δ [°]`
  — every column is a number the process used or produced; rms coloured against `PSL_RMS_MAX`;
- **removed**: FIT 1 and FIT 2, the B and locus panels, R1, L1, dΓ, df_s, the masked column (the mask is off
  by decision; the constant stays), the import of `sweep_data/fit_admittance.py` (the release tree no longer
  needs `sweep_data/` for any live view), `IMPEDANCE_FIT_POINTS`;
- title "openQCM NEXT — live fit (what the acquisition publishes)"; the explanatory note rewritten in four
  sentences.

Nothing in the window computes an estimate: if the process did not ship a fit (older producer, or
`IMPEDANCE_ESTIMATOR = "argmax"`), the window shows the measured G with the argmax marker and says
"published by: maximum of G".

### 2.5 Impedance Data View: the band it draws

Today it draws the two half-height crossings. When the published Γ is the fit's, the consistent band is
f_res ± Γ_fit (the rotated Lorentzian is symmetric about f_res in its own frame). Proposal (decision D4): draw
f_res ± Γ_fit when the source is the fit, the crossings when it is the fallback, and say which in the header.
Ten lines; the view still computes nothing.

### 2.6 Documents

`ALGORITHM.md` gets a section "the published estimator" (model, seeds, window, gate, fallback, what is
logged where); `software/docs/DATA_FORMAT_sweep_data.md` or a sibling gets the `_multi_fit.csv` columns;
`datalog-quantities-2026-09-10.md` gets a dated note that the Frequency column changed estimator on the
date of the merge of T2; HANDOFF §4, CHANGELOG, `SESSION_PROMPT_liquid_frequency_excess.md`.

## 3. Subtasks — one commit each, in this order

| # | what | verification (the number that says it works) |
|---|---|---|
| T1 ✅ `85b1a15` | `core/lorentzian.py` + `software/tests/test_lorentzian.py` (headless, no Qt) + `psl_lib.py` switched to import it | synthetic sweeps: f_s within 4 Hz, Γ within 5 Hz, φ within 0.3°; the 45 dumps of 2026-09-11 reproduce the research numbers to the Hz; the gate rejects a flat G, a NaN-holed G, a window with no peak, each with its reason |
| T2 ✅ | `elaborate_multi` integration, counters and log line, G/B message fields (no third datalog, D2) | a replay tool feeds the 45 dumps' samples to a headless `MultiscanProcess.elaborate_multi` with fake parsers and captures the published pair and the message: equal to the offline fit, source = fit on 45/45, cost printed; a synthetic flat sweep publishes the fallback with the reason |
| T3 ✅ | main panel: `pltSus`, `_pltSus` (not `pltB`, taken by the frequency plot), removal of the circle overlay and its constants | `py_compile`, `setupUi` builds headless, the attribute lists reference no removed name; a screenshot on the real platform by Marco (a `QMainWindow.show()` segfaults offscreen) |
| T4 ✅ | the live fit window rebuilt | the window builds and paints headless from a fake worker holding one dump's shipped arrays and fit fields (QWidget is fine offscreen); the curve drawn equals `rotated_lorentzian` of the shipped parameters to 10⁻⁹; real-platform look by Marco |
| T5 ✅ | Impedance Data View band from the published source | headless as today's view is checked |
| T6 | docs: ALGORITHM, data format, HANDOFF §4, CHANGELOG, session prompt | — |
| T7 | bench: air, then one liquid, with the three datalogs | `_multi.csv` frequency equals `_multi_fit.csv`'s fit when source = 1; fallback count 0 or each case explained; the live window's curve on top of the measured G; the offline `psl_lib` on the same day's dumps agrees to the Hz |

Estimated size: T1 ~250 lines with tests, T2 ~150 lines across four files, T3 ~60 lines removed and ~40 added,
T4 a ~300-line file replacing a 531-line one, T5 ~20 lines, T6 docs.

## 4. Decisions that are Marco's

| | question | recommendation |
|---|---|---|
| D1 | B in the main panel: as the chain computes it, or minus the edge value as today? | as computed (2.3) — **Marco: confirmed** |
| D2 | the third datalog `_multi_fit.csv` with φ, rms, source and the fallback pair? | **Marco: no** — superfluous; φ, rms and the source live in the G/B message (live window) and in the System Log line |
| D3 | fallback thresholds: rms 5 % of range, \|φ\| ≤ 60°, Γ within 0.3–3× the half-height value | as proposed — **Marco: approved**, as parameters to keep in the open: their existence, value and function must stay visible (constants block, ALGORITHM, the fit window shows them beside the values), and they may change |
| D4 | Data View band: f_res ± Γ_fit when the fit is published | yes — **Marco: yes**, f_res and Γ of the fit must be visible there |
| D5 | `IMPEDANCE_ESTIMATOR` default `"lorentzian"` on this branch from T2 on | yes — **Marco: proceed**; earlier datalogs are assumed not comparable |
| D6 | the saturation-mask code (off) and `research/admittance-circle-fit/`: leave as they are | yes — **Marco: confirmed** |

## 5. What changes for whoever reads the datalog

- `Frequency_n` moves by +2…+47 Hz in air and +170…+700 Hz in liquid relative to today's estimator;
  `Dissipation_n` by −7…+8 % (Γ_fit against Γ half height). A datalog before and one after this change are
  not comparable without saying which estimator produced them — the `_multi_fit.csv` file carries both.
- The fit is more stable than the maximum where the fold decision is borderline: on water n = 3, the sweep
  whose fold flipped moved argmax by 92 Hz across the three replicas and f_res by 32 Hz.
- The fundamental keeps its dissipation excess (+29–37 % against the theory) under either estimator.

## 6. Risks and how each is bounded

- **CPU in the process**: +11…16 ms per overtone decimated (measured); printed once. If a board ever makes it
  slow, `PSL_MAX_POINTS` is the knob.
- **A silently wrong fit**: bounded by the gate and made visible by the counters, the log line and the
  residual strip. The thresholds are 10× the measured values.
- **GUI/process disagreement**: impossible by construction — the window evaluates the shipped parameters,
  it fits nothing.
- **Old datalogs**: the estimator change is dated in `datalog-quantities` and the CHANGELOG; the fit file
  carries the fallback pair for comparison.
- **The φ–background degeneracy** seen with a linear background in air (A7): the published model has no
  linear background, and φ is stable to 0.2° across replicas without it.
