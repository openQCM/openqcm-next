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
   published, because it lags.
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
   - the baselines come from the coarse points (`_phase_fold_decision` and
     `_half_bandwidth_G_exact` take them as a new optional argument; without it they behave as
     before).

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
of the cycle before. The row is still written.

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
- Each point waits dwell_us (0–100 000) more before its 500 averaged readings.
- Each point is printed as in the sweep, followed by the same end-of-measurement line. On the Next,
  that line comes from the code that closed the sweep, moved unchanged into `end_of_measurement()`.
- `Q` stops it.
- A malformed command answers `ERR_SEG` and the end line.
- The plain `start;stop;step` sweep is untouched.

`Constants.FW_VERSION` is `0.1.5d-SEG`, so the firmware check offers these images (they are in
`software/openQCM/firmware_update/`). The standard sweep runs on either firmware.

At START the process asks the board for its version (`F`).

- **The version has `-SEG`:** the run uses the adaptive sweep.
- **It does not:** the run uses the full sweep and says so in the System Log. A firmware without
  `Z` would read `Z...` as a plain sweep starting at 0 Hz.

Both images were built with arduino-cli, Teensy core 1.59,
`--fqbn teensy:avr:teensy40:usb=serial,speed=600`. The only compiler warning is the unused
`lastByte`, which both base firmwares already had.

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
| same | firmware without `Z` | full sweep, said in the System Log |
| same | a failed overtone | empty cell, row written |

The 70 tests of the branch still pass, with 9 new ones (8 in `tests/test_adaptive.py`, 1 for the Setup card): 79 in all.

**Not yet run:** this Python application on a real board.

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
