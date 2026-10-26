# The adaptive sweep (experimental)

Branch `impedance-analysis-sweep-adaptive`, from `impedance-analysis` at `59e6b47`, 2026-10-25.
Ported from openQCM Lab (`core/src/openqcm_lab/analysis/conductance.py`, where it was developed
and validated on a bench board on 2026-10-24/25). The Python GUI is unchanged apart from one
checkbox; the analysis of each sweep is this branch's (ALGORITHM.md), unchanged.

## Why

The 1 Hz sweep of `elaborate_multi`, 83 µs a point (12 kHz/s), is fast against the crystal's decay
time τ = 1/(2πΓ): 4 ms on the fundamental in air. The resonance lags behind the sweep. Measured on a
bench board in air (openQCM Q-1 hardware running the Next's no-TEC firmware):

| | swept up: f | swept up: Γ | swept down |
|---|---|---|---|
| F0 | +26 Hz | +18 % | as much the other way |
| F3 | +24 Hz | +11 % | as much the other way |
| F5 | +23 Hz | +6 % | as much the other way |

Swept slowly, up and down agree. The lag scales with κ = rate / (2πΓ²): about 1.6 for the full sweep
on the fundamental in air.

## How

`core/adaptive.py` plans and analyses; `MultiscanProcess` sweeps and publishes.

1. **Locate.** One full 1 Hz sweep through the chain of `elaborate_multi`. Its reading is never
   published, because it lags. For the same reason it latches no fold decision (the passes latch
   their own) and does not count in the fit's statistics. It sweeps whole hertz: the window follows
   the last resonance, which is not a whole number, and the firmware truncates what it is sent.
   - **No whole band in the window** (a damped load): nothing is published, and the System Log
     says so once.
   - **A band, but no room for the fine zone** (the resonance at the window's edge): the full sweep
     is published, as the standard sweep would.
2. **Each following sweep** is one `Z` command of the firmware (0.1.5d-SEG), with its segments in
   this order:
   - the window's first point, after a wait of `ADAPTIVE_SETTLE_TAU` = 3 τ (see below);
   - coarse points, 100 Hz apart, over the rest of the −12/+6 kHz window, for the two baselines:
     the phase far from the resonance and G at the window's low end;
   - a lead-in of 3 τ just below the fine zone, so that the jump's transient dies out;
   - the **fine zone**, ±4 Γ of the last resonance (at least ±100 Hz), swept **up and straight back
     down** at 0.125 · 2πΓ² Hz/s. The rate comes from the segment's dwell; the step is Γ/40, at
     least 1 Hz.
3. **Each pass** through the chain of `elaborate_multi`:
   - Savitzky–Golay over 51 Hz, then the spline onto 1 Hz with the full sweep's smoothing per point;
   - fold (latched per pass), exact G, maximum, half height, and the Lorentzian fit when it is
     chosen;
   - the baselines come from the coarse points, not the lead-in, which sits just below the
     resonance (`_phase_fold_decision` and `_half_bandwidth_G_exact` take them as a new optional
     argument; without it they behave as before).

   **f and Γ are the means of the two passes**: the remaining lag cancels.
4. **Display.** The two passes are moved back by ±lag (lag = half the distance between their
   resonances) and averaged. Drawn as measured, interleaved, they zigzag on the flanks. The
   measurement does not use this. The amplitude/phase plot receives the sweep interpolated onto
   1 Hz over the window.

### A moving resonance

Vapour condensing or a film growing moves the resonance between sweeps. On a bench run in openQCM
Lab, the first version left holes in the readings. Now:

- the fine zone goes where the resonance will be, predicted from its speed over the last two
  adaptive sweeps and widened by half the predicted move;
- a sweep that still loses the resonance (its band is not whole inside the zone) is not thrown
  away: its coarse points span the window, so the peak of G is found among them (with a new Γ
  estimate) and the fine zone is swept again around it at once, up to 2 times;
- only then does a full sweep locate the resonance again.

If even that fails, the overtone's cell in that cycle's datalog row is empty (NaN), not the value
of the cycle before. The row is still written. A measurement that fails (a timeout, `ERR_SEG`)
forgets the overtone, so the next cycle locates it again with a full sweep.

### Readings

There is no running mean. Each datalog row is the cycle's own sweep of each overtone (a block of
one), after 2 cycles of warm-up: the first locates every overtone, the second learns how fast each
resonance moves. The standard mode's trimmed mean of the last 8 sweeps smeared every step of the
signal over them.

### The settling wait (this branch only, not in openQCM Lab)

At the end of a sweep the DDS stays at its last frequency, near the resonance in the fine zone, so
the crystal keeps being driven there. When the next sweep jumps to the window's low end, the
crystal rings on at f_s for a few τ, and the first coarse points (G's baseline) read that ringing.

- **Multiscan with several overtones:** another overtone comes in between and nothing happens.
- **One overtone, or a relocation:** on the simulated board, G's baseline comes out 2 mS off and Γ
  3 % too wide.

The window's first point therefore waits 3 τ before it is read: 12 ms on the fundamental in air.
`tests/test_adaptive.py` shows the effect and the fix. **To check on the bench:** compare a
one-overtone run with the same overtone measured in multiscan.

## Firmware

| Folder | Version | For |
|---|---|---|
| `firmware/openQCM_Next_py_0.1.5d_SEG_teensy/` | `0.1.5d-SEG` | Next with TEC: 0.1.5d plus `Z` |
| `firmware/openQCM_Next_py_0.1.5d_SEG_TEST_teensy/` | `0.1.5d-SEG-TEST` | no-TEC boards and the openQCM Q-1 used as a bench board: 0.1.5d-TEST plus `Z`, and the MCP9808's temperature when the board has one |

The command:

    Z<start>;<stop>;<step>;<dwell_us>[;<start>;<stop>;<step>;<dwell_us>...]

- Up to 8 segments, swept in the order given, each from start to stop included: upwards with
  step > 0, downwards with step < 0.
- Each point waits dwell_us (0–100 000) more before its 500 averaged readings. The plan never asks
  for more (`ADAPTIVE_DWELL_MAX_US`): a line narrower than about 3.5 Hz at 1 Hz steps is swept faster
  than 0.125 · 2πΓ².
- Each point is printed as in the sweep, followed by the same end-of-measurement line. On the Next,
  that line comes from the code that closed the sweep, moved unchanged into `end_of_measurement()`.
- `Q` stops it.
- A malformed command answers `ERR_SEG` and the end line. Since 2026-10-26 that includes a field
  that is not a whole number and a start or stop outside 1 Hz–60 MHz.
- The plain `start;stop;step` sweep is untouched.

`Constants.FW_VERSION` is `0.1.5d-SEG`, so the firmware check offers these images (they are in
`software/openQCM/firmware_update/`). The standard sweep runs on either firmware.

With the box checked in multiscan, a board without `-SEG` is **refused**, as openQCM Lab refuses
it. A firmware without `Z` would read `Z...` as a plain sweep starting at 0 Hz. Until 2026-10-26 the
run fell back to the full sweep, but the datalog was still named `_adaptive`.

- **At START, the GUI** checks the version the board gave to `F` at connection
  (`_adaptive_refusal`). Without `-SEG` (or with no answer), START is refused with a pop-up and a
  System Log line. No process starts and no datalog is created.
- **In the process**, `_start_adaptive` asks `F` again on the port it now owns. If the board still
  answers without `-SEG`, nothing is swept and no row is written until STOP, and the System Log
  says so.

Both images were built with arduino-cli, Teensy core 1.59,
`--fqbn teensy:avr:teensy40:usb=serial,speed=600`. The only compiler warning is the unused
`lastByte`, which both base firmwares already had.

## Peak detection: each peak confirmed on finer sweeps (2026-10-26)

Ported from openQCM Lab (`9719141`, `d547680`): `core/peak_refine.py`, plus
`CalibrationProcess._refine_peaks` and `_sweep_section`. It always runs.

**Why.** The wide sweep, 1–51 MHz in 500 Hz steps, runs at about 6 MHz/s, and its peaks lag the
resonances. On 2026-10-25 the bench board's stored peaks sat above the resonances the adaptive sweep
then measured:

| F1 | F3 | F5 | F7 | F9 |
|---|---|---|---|---|
| +2.1 kHz | +1.8 kHz | +3.6 kHz | +3.5 kHz | +3.6 kHz |

openQCM Lab measured 1.5–5 kHz on a Next. The 500 Hz step is also wider than a line in air, so the
wide sweep's phase check could reject real overtones.

**How.** For the fundamental and for every overtone candidate of the wide sweep, including the
ones its own check rejected:

1. Sweep ±25 kHz at 50 Hz. If the maximum is at the edge, there is no resonance here.
2. Sweep ±5 kHz at 10 Hz on that maximum. If the line is too wide for this sweep, the ±25 kHz
   sweep is judged instead.
3. Confirm the peak when all three hold:
   - the magnitude maximum is not within 5 % of either end;
   - the phase maximum is within max(2 kHz, ¾ of the half-power width) of it;
   - the phase maximum is above 10°.

   Both maxima use the wide sweep's baselines.

**Results.**
- **Overtones.** A rejected overtone is left out, as before.
- **Fundamental.** It is refined but never rejected; a rejection keeps the wide sweep's value.
- **Precision.** The stored peaks are on the 10 Hz grid (50 Hz for a wide line).
- **Log.** Every decision is printed with its numbers.
- **Stop.** A Stop during these sweeps sends `Q` and saves nothing, as a Stop during the wide sweep.
- **Failure.** A failed sweep fails the peak detection ("repeat").

Measured on the simulated line:
- **Choosing the sweep.** The ±5 kHz sweep reads the width over a straight line through its own
  ends, which a wide line lifts. A true FWHM of 4 kHz reads 2.8 kHz, and the switch to the
  ±25 kHz sweep comes at about 5.5 kHz. This is openQCM Lab's behaviour, kept. The peak is found
  within 100 Hz either way.
- **Time.** Five peaks take 10 sweeps of about 1 000 points each, about 2 s on the Next.

`tests/test_peak_refine.py` (10 tests) uses the bench run's wide and adaptive frequencies.
**Not yet run on a board.**

## In the GUI and in the files

- **Measurement Setup.** A new checkbox, **Experimental: adaptive sweep**, sits under the
  estimator's. It is chosen before START and locked during a run, like the estimator.
- **Datalog name.** It gets `_adaptive`: `<ts>_multi_adaptive.csv`, or
  `<ts>_multi_lorentzian_adaptive.csv` with the fit.
- **Comparison datalog.** `_amplitude.csv` gets NaN, because this sweep does not measure the
  amplitude pair.
- **System Log.** One line says which sweep governs the run. Others report each relocation, each
  full sweep after a loss, and each failed measurement.

## Validation

| Where | What | Result |
|---|---|---|
| Bench board, air (openQCM Lab, 2026-10-24) | adaptive vs a quasi-static sweep | F0 0.00 ± 0.31 Hz / +0.06 %; F3 −0.30 Hz / −0.10 %; F5 −0.66 Hz / +0.16 % |
| Bench board, air (openQCM Lab) | time per sweep | 0.62 / 0.46 / 0.31 s (F0 / F3 / F5), against 1.57 s for the full sweep |
| Bench board, air, 21 min multiscan F0–F9 (openQCM Lab, 2026-10-25) | noise | f of F0: sd 0.39 Hz, Allan 0.18 Hz at 1.7 s; Γ sd 0.11–0.27 Hz; no reading missing |
| `tests/test_adaptive.py`, simulated BVD crystal with the resonator's lag | adaptive vs the same crystal without lag | f within 1 Hz, Γ within 1 % |
| same | full sweep with lag | f +47 Hz, Γ +29 % (the lag is there) |
| same | resonance moving at −20 Hz/s | a reading every cycle, following it |
| same | firmware without `Z` (or no answer) | refused: nothing swept, no row, said in the System Log; the GUI refuses START first |
| same | a failed overtone | empty cell, row written; the next cycle locates it again |
| same | Γ 2 Hz | the dwell stays within the firmware's 100 ms |
| same | a window that is not whole hertz | the full sweep is sent and analysed on whole hertz |
| same | a load wider than the window | nothing published, said once |
| Q-1 bench board 13131320, 2026-10-25, first run of this application (Lorentzian estimator, F0–F9) | it runs | f_res 4 998 364 / 14 967 159 / 24 937 426 / 34 906 546 / 44 877 398 Hz, Γ 52.5–166 Hz at the first sweep; later relocations on every overtone, not yet analysed |

The 70 tests of the branch still pass, with 17 new ones (16 in `tests/test_adaptive.py`, 1 for the Setup card): 87 in all, 97 with `tests/test_peak_refine.py`.

### Carried from openQCM Lab's review of its PR #2 (`47abfe6`, 2026-10-26)

The dwell cap; a failed sweep forgets the overtone; the locating sweep latches no fold, counts in no
statistics, sweeps whole hertz and is not published without a whole band; the baselines leave out
the lead-in; `Z` refuses fields that are not whole numbers and frequencies outside 1 Hz–60 MHz. Not
carried, because there is nothing like it here: the blocks of Lab's conductance methods, its Swift
GUI and Wi2. The refusal to start without `Z` followed on the same day (see Firmware).

## Remaining, for the test session

- Flash the bench board with `0.1.5d-SEG-TEST`. Run peak detection, then multiscan with the box
  off and with the box on. Compare f and Γ, and look at the panel, the amplitude plot and the
  datalog.
- **Cycle time.** Between two sweeps `_between_sweeps` still waits about 0.2 s (TEC current `A`)
  plus the end-of-sweep pause, on every overtone. With sweeps of 0.15–0.5 s this is now most of
  the cycle. It is unchanged here and is a candidate for the next step.
- **Amplitude plot.** It starts after `Constants.environment` (8) cycles, as before.
- One-overtone run against multiscan (the settling wait).
- A moving resonance on the bench (breath or vapour).
- A Next with TEC, with `0.1.5d-SEG`.
