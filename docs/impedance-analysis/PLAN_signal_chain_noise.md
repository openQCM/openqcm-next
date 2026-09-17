# Plan — the signal chain from the ADC to the logged f and D: where the noise is, and what could reduce it

*Written 2026-09-17 on Marco's ask: the post-processing (exact inversion, phase-shifted Lorentzian) is where he
wants it; the next subject is the quality of the signal that feeds it. This is a plan of ANALYSIS, not of
changes: every candidate below is tied to the measurement that accepts or rejects it. Nothing here is decided;
§5 is Marco's. Facts in §1 are read from the code today; numbers in §2 are measured today on data already in
the repo, and are a first look, not a result.*

## 0. The question, stated so it can be measured

"Less noise on the logged f and D" has two very different meanings, and the data already say that they do not
have the same cause:

- **sweep-to-sweep noise** (white, seconds): what the ADC, the sweep and the estimator leave on one value;
- **drift** (minutes): what temperature, the sensor and the electronics do between one value and the next.

§2.2 measures both on the 2026-09-11 datalog. The ratio between them decides where the effort goes: the levers
of §4 A–D act on the first, and none of them acts on the second.

## 1. The chain as it is (read 2026-09-17)

| stage | where | what it does | numbers |
|---|---|---|---|
| 1 DDS step | firmware `openQCM_Next_py_0.1.5c_teensy.ino`, sweep loop ~l. 1010 | `SetFreq(count)` then immediate ADC reads, **no settling wait** (`WAIT = false`, `WAIT_DELAY_US = 200` unused) | step 1 Hz, 18 001 points per overtone (`LEFT = 12000`, `RIGHT = 6000`) |
| 2 ADC | same, l. 451–476 and 1021–1029 | Teensy 4.0, two ADCs in `startSynchronizedContinuous`, **12 bit**, hardware averaging **1**, `HIGH_SPEED` conversion and sampling; per point `AVERAGE_SAMPLE = 500` calls to `readSynchronizedContinuous()`, summed and divided | ⚠️ `readSynchronizedContinuous()` **returns the last completed conversion, it does not wait for a new one**. A sweep of 18 001 points takes ≈ 2 s (dump write times: g3 12:46:24, g5 :26, g7 :28, g9 :30, g1 :32), i.e. **≈ 110 µs per point including `SetFreq`**. 500 fresh 12-bit conversions do not fit in 110 µs; the 500 reads must contain many repeats of the same conversion. **How many fresh conversions per point is the first number to measure (§3 C1).** |
| 3 serial | same, l. 1032–1036 | `Serial.print(double)` → **2 decimals** of an ADC count | resolution 0.01 count = 8 µV at the pin; not a lever (a mean of ≤ 500 counts has no finer content) |
| 4 bits → volts | `Multiscan._Vmag_bit_mag`, `_Vphase_bit_phase` (l. 717–740) | 3.3/4096 V per count, /2 (V_MAG op-amp), /1.5 (V_PHS op-amp), attenuator undone | 1 count = 0.40 mV on V_MAG = **0.013 dB**; 0.54 mV on V_PHS = **0.054°** |
| 5 smoothing | `elaborate_multi` l. 963–1013, `resonance.savitzky_golay` | Savitzky–Golay **51 points, order 3**, on the 1 Hz grid, on five series (mag, phase, Vmag_corr, Vphase, raw Vmag) | window 51 Hz against FWHM 130 Hz (n = 1 air) … 5 kHz (liquid). Known bias on Γ: +9 % / +16 % on n = 1 / 3 in air (HANDOFF §4) |
| 6 resampling | l. 998–1017 | `UnivariateSpline(s = SPLINE_FACTOR_G = 0.001)` evaluated on `points = argument_default_samples` = 18 001 | same grid in, same grid out: an interpolating spline through the smoothed points. Cost only? To measure (§3 A3) |
| 7 exact inversion | `_phase_offset_fold`, `_RX_exact`, `_G_exact`, `_B_exact` | fold decision, δ, Y = 1/(M e^{−jφ} − R17) | `ALGORITHM.md` §4–6 |
| 8 estimator | `parameters_finder_impedance_exact`, `_half_bandwidth_G_exact`, `_publish_resonance` | STANDARD: **argmax of G on the 1 Hz grid** (quantised to 1 Hz) and Γ from the **two half-height crossings**, each linearly interpolated between two samples; EXPERIMENTAL: the phase-shifted Lorentzian on ±3Γ decimated to 300 points | `ALGORITHM.md` §7–8 |
| 9 baseline of G | `_half_bandwidth_G_exact` l. 619 | mean of the **first 100 samples** | in liquid on the resonance skirt: −2.5 … −13.9 % on Γ (HANDOFF §4, roadmap 6) |
| 10 buffer | `RingBuffer(environment)`, `averaging.robust_mean(…, 0.10)` | trimmed mean, floor one per tail | `environment = 3` today → **median of 3**; = 10 in production → mean of the central 8. One value every cycle of ≈ 9.3 s (five overtones), so the buffer spans 28 s today, 93 s in production |
| 11 datalog | `FileStorage.CSVsave_Multi` | one row per GUI update | ⚠️ the 2026-09-11 datalog has **95 duplicate F/D rows out of 486** (README): rows written with no new value. They flatten any noise statistic taken on the file. |

## 2. What the data already say (first look, 2026-09-17)

### 2.1 Raw sample noise, off resonance, per point on the 1 Hz grid

From the 45 dumps of 2026-09-11 (`data/sweep_dumps_2026-09-11.npz`), σ of adjacent-sample differences /√2 on
the first 3000 points of the sweep (the flat wing), middle replica of each phase:

| set | n | V_MAG σ [mV] | [counts] | [dB] | V_PHS σ [mV] | [counts] | [°] |
|---|---|---|---|---|---|---|---|
| air | 1 | 0.47 | 0.59 | 0.016 | 1.53 | 1.9 | 0.15 |
| air | 3 | 0.43 | 0.53 | 0.014 | 1.18 | 1.5 | 0.12 |
| air | 5 | 0.38 | 0.47 | 0.013 | 0.98 | 1.2 | 0.10 |
| air | 7 | 0.43 | 0.54 | 0.014 | 0.65 | 0.8 | 0.065 |
| air | 9 | 0.32 | 0.40 | 0.011 | 0.66 | 0.8 | 0.066 |
| water | 1–9 | 0.25–0.44 | 0.31–0.55 | 0.008–0.015 | 0.64–1.28 | 0.8–1.6 | 0.064–0.13 |
| isopropanol | 1–9 | 0.24–0.45 | 0.30–0.55 | 0.008–0.015 | 0.58–1.29 | 0.7–1.6 | 0.058–0.13 |

- The per-point noise is **half an ADC count on V_MAG and one to two counts on V_PHS**, the same in air and in
  liquid. A mean of 500 independent 12-bit samples would sit far below one count; this is consistent with the
  suspicion of stage 2 (few fresh conversions per point) and with the ADC's own quantisation being the floor.
  Which of the two it is, only the bench can say (§3 C1).
- The V_MAG counts printed with two decimals take 14 795 distinct values over 18 001 samples: the mean is
  sub-count, so the 500 reads do average *something*; the question is how many independent samples they are.

### 2.2 The logged f and D on a plateau: white noise against drift

Datalog `2026-09-11_12-14-42_multi.csv` (standard estimator, `environment = 3`), the quietest 60-row windows
(≈ 9–10 min) per overtone; σ_white = σ(first differences)/√2, std = plain standard deviation of the window.
⚠️ Duplicate rows (§1, stage 11) are still in: σ_white is biased **low** by roughly 10 %.

| phase | n | f mean [Hz] | f σ_white [Hz] | f std [Hz] | f ptp [Hz] | D mean [ppm] | D σ_white [ppm] | D std [ppm] |
|---|---|---|---|---|---|---|---|---|
| air | 1 | 5 004 597 | 0.2–0.3 | 0.3–0.5 | 1 | 26.1 | 0.03–0.04 | 0.05 |
| air | 3 | 14 988 737 | 0.1–0.2 | 0.5–2.0 | 1–7 | 10.4 | 0.005 | 0.008 |
| air | 5 | 24 973 685 | 0.3 | 0.8–3.1 | 2–11 | 8.6 | 0.005–0.007 | 0.013–0.024 |
| air | 7 | 34 957 563 | 0.8 | 1.6 | 6 | 9.1 | 0.009 | 0.028 |
| air | 9 | 44 943 106 | 0.5–0.6 | 1.2–6.2 | 4–22 | 9.05 | 0.002 | 0.003–0.016 |
| water | 3 | 14 987 329 | 1.6 | 3.7 | 13 | 173 | 0.03 | 0.05 |
| water | 5 | 24 971 734 | 0.5 | 3.6 | 9 | 127 | 0.03 | 0.06 |
| water | 7 | 34 955 388 | 0.5 | 2.1 | 9 | 104 | 0.05 | 0.11 |
| ipa | 1 | 5 003 555 | 0.3 | 0.8 | 2 | 514 | 0.10 | 0.16 |
| ipa | 7 | 34 954 651 | 1.6 | 2.8 | 12 | 136 | 0.05 | 0.14 |
| ipa | 9 | 44 939 785 | 2.1 | 3.3 | 16 | 121 | 0.06 | 0.14 |

- **The sweep-to-sweep noise of the logged frequency is 0.1–0.8 Hz in air and 0.5–2 Hz in liquid**, i.e.
  2–5·10⁻⁸ relative, at the quantisation floor of an argmax on a 1 Hz grid passed through a median of 3.
- **Over ten minutes the spread is 2–10 times larger than the white noise** on every overtone (std/σ_white:
  1.5–2 on the fundamental, up to 10 on n = 5 and 9 in air). What limits f over minutes is **drift, not
  noise**. The same holds for D (std/σ_white 1.5–8).
- The drift is not resolvable against the logged temperature: it reads 25.00 °C on every plateau row, i.e.
  the TEC holds the block to the 0.01 °C the log resolves. Whether it is the sensor, the liquid, the board or
  the DDS clock is exactly what §3 B2 is for.

**Consequence for the plan.** If Marco's target is the value logged every ten seconds, the chain is already
at the floor its grid allows and the levers are A–D of §4. If the target is the stability of a plateau over
minutes, none of A–D helps and the work is B2 and E. The Allan analysis of §3 B1 puts a number on where the
crossover between the two regimes sits.

### 2.3 Two answers measured the same day, on Marco's questions

**The stage-6 spline is a smoother, not a cost.** `UnivariateSpline(s = 0.001)` takes `s` as an absolute bound on
the sum of squared residuals, in V². On 18 001 points that is a permitted residual of √(0.001/18001) = **0.236 mV
rms whatever the signal**, and the spline uses all of it: measured rms(spline − SG) = 0.236 mV on every channel of
every dump tried, with 8–82 knots over the 18 001 points. After the SG (which leaves ≈ 0.1 mV of the raw 0.4 mV:
its white-noise gain is 0.210, measured), the spline is the **stronger** of the two smoothers. What it moves, value
with spline minus without, 25 sweeps of 2026-09-11:

| | argmax f [Hz] | half-height Γ [Hz] | PSL f_res [Hz] | PSL Γ [Hz] | PSL φ [°] |
|---|---|---|---|---|---|
| air, n = 1–9 | 0 … −4 | −0.3 … +2.5 | ≤ 0.7 | ≤ 1.0 | ≤ 0.24 |
| water / isopropanol, n = 1–3 | ±7 | −1 … +2.4 | ≤ 0.1 | ≤ 0.6 | — |
| water / isopropanol, n = 5–9 | −45 … +49 | +3.6 … **+27.6** | ≤ 5.4 | +0.8 … **+31.2** | — |

In liquid on the high overtones it shifts Γ by up to 1 % and the argmax by tens of hertz. Its strength depends on
the units of the channel and on the number of points, not on the noise: a second smoother with an arbitrary knob,
applied after a first one that was tuned. Lever E of §4 is therefore "decide what smoothing the chain should have,
once", not "remove a no-op".

**The duplicate datalog rows: mechanism found, on both branches.** A row is written by `Worker.store_data()`, called
from the handler of the **temperature** queue (`_queue_data5`), which the process feeds once per overtone (5 per
cycle); the write is gated on `self._overtone_number == 0`, a value that comes from a *different* queue (queue6,
the status message) and is consumed **after** queue5 in the drain (`consume_queue5` then `consume_queue6`, then F
and D). So within one drain every pending temperature message is judged against a stale overtone number: if it is
0, each one writes a row, at the same `time_current` and with the same F/D store — runs of 2–5 identical rows with
identical `Relative_time` (measured: the time step before a duplicate is 0.00 s, 96 of 486 rows); if it is not 0,
the cycle writes nothing — the 19.5 s gaps at the 95th percentile of the row spacing. The number of rows per cycle
is a race between the GUI timer and the process, not a rule. Same code, same order on `main`
(`core/worker.py` 357–360, 705, 881). Lever G is a fix on `main`, cherry-picked: one row per cycle, keyed on the
cycle itself (the arrival of the cycle's F and D, or a "cycle done" message from the process), never on a
cross-queue flag.
**Done the same day**: main `2da0705` + `ab33541`, on this branch `ef8491c` + `22089e6` + the branch-only
follow-up for the comparison datalog; `tests/test_datalog_rows.py`. Lever G is closed; the datalogs written
from here on carry one row per cycle with that cycle's values.

## 3. The analysis, in blocks

Each block produces one page in `research/signal-chain-noise-2026-09/` with its figures embedded, one hypothesis
per page, Marco's verdict dated (the rule of `objective-analysis-doc-first`). Blocks A and B run offline on
data already in the repo; C, D and E need the bench.

### A — Offline noise budget through the chain (the 45 dumps of 2026-09-11)

The three replicas per phase are the only repeatability the dumps give; the budget therefore comes mostly
from **injecting the measured raw noise** (§2.1, or bootstrapped from the wings) into one sweep and propagating
it through the chain as the process runs it, 500 draws per configuration, σ of f and Γ at the output.

| # | measurement | the number that decides |
|---|---|---|
| A1 | σ(f), σ(Γ) of the STANDARD estimator (argmax + crossings) and of the PSL fit, per overtone and phase, from injected noise | how much of the 0.2–2 Hz of §2.2 is estimator noise and how much is the 1 Hz grid |
| A2 | the same with the SG window at 0 (none), 11, 21, 51, 101, and the SG bias on Γ (against the fit, which does not smooth) — for argmax and for the fit separately | the window that minimises σ² + bias² for the standard estimator; whether the fit needs any smoothing at all (psl-validation already says f_res moves < 5 Hz without it) |
| A3 | the spline of stage 6 in and out: difference of G, of f, of Γ, and its cost in ms | if the differences are below 10⁻³ of the noise, the stage is cost only |
| A4 | the two crossings against the fit's Γ, σ under injected noise | how much Γ noise the four-sample estimator adds |
| A5 | decimation: the same σ(f), σ(Γ) when the sweep is thinned to 2, 5, 10, 20 Hz steps with the per-point noise divided by √(step) (the averaging the freed time would buy if the fresh conversions of C1 allow it) | whether a coarser grid with a longer dwell beats the 1 Hz grid — the premise of lever B |
| A6 | the baseline of G (first 100 samples) in liquid: its noise and bias into Γ against a fitted offset | whether roadmap item 6 of HANDOFF §4 is also a noise item |

### B — Time domain, on the datalogs

| # | measurement | the number that decides |
|---|---|---|
| B1 | **Allan deviation** of f and D per overtone on each plateau of the 2026-09-10 and 2026-09-11 datalogs, duplicate rows removed, τ from one cycle (9.3 s) to the plateau length | the τ at which white noise stops falling and drift takes over. Averaging beyond that τ (a larger `environment`) buys nothing and adds lag |
| B2 | drift against temperature: needs the temperature at better than 0.01 °C (the MTD415T reports millikelvin: `Serial.print(... / 1000.0)` prints two decimals — a firmware print, not a sensor limit), and a long air run (E1) | whether the plateau spread of §2.2 is thermal |
| B3 | the buffer: σ_white and lag of the median of 3 against the trimmed mean of 10 and against no buffer, on the same rows | the actual gain of `environment = 10` against its 93 s of lag, given B1 |
| B4 | the duplicate rows: where in the GUI/worker path a row is written with no new value, and whether it is on `main` too | a datalog defect, to fix on `main` and cherry-pick; also a prerequisite for any statistic on a datalog |

### C — Bench, firmware (Teensy, one board)

| # | measurement | the number that decides |
|---|---|---|
| C1 | **fresh conversions per point**: a test build that counts, inside the 500-read loop, how many reads return a *new* conversion (ADC library: `adc->adc0->isComplete()` or the conversion counter), and prints the count with the point; plus `micros()` around `SetFreq` and around the loop | N_eff. If N_eff ≪ 500 the "500 averages" are largely the same sample read repeatedly, and the real lever is to wait for conversions (or hardware averaging) rather than to loop faster |
| C2 | ADC noise floor: with the DDS at a fixed frequency (no `SetFreq`), 18 001 reads of both channels at N = 1, 4, 16, 64 hardware averages, σ in counts | the ADC's own σ against §2.1's 0.5–1.9 counts; whether the noise is quantisation, ADC, or the AD8302 outputs |
| C3 | settling after `SetFreq`: at a 1 kHz step, read the ADC every 2 µs for 200 µs after the write, plot the transient | the settling time of DDS + AD8302 video filter + op-amps, i.e. the dwell a coarser grid (lever B) would need |
| C4 | sweep timing: `micros()` per point split into `SetFreq`, ADC loop, `Serial.print` | where the 110 µs go; how much time a coarser grid frees |

### D — Bench, end to end

| # | measurement | the number that decides |
|---|---|---|
| D1 | 20 consecutive dumps on one air plateau (`OPENQCM_SWEEP_DUMP=1`, copied out per dump) | real sweep-to-sweep σ of raw V_MAG/V_PHS and of f, Γ for both estimators — the ground truth A1 is calibrated against |
| D2 | the same with a test firmware at N_eff maximised (C1's fix) | the gain of lever A on real data |

### E — Bench, drift

| # | measurement | the number that decides |
|---|---|---|
| E1 | a 2 h air run at 25 °C with millikelvin temperature in the log (B2's print) and the room temperature beside it | the drift's spectrum and its correlation with T; whether the sensor or the electronics carry it (swap the sensor module and repeat: the 2026-07 swap protocol) |

## 4. The candidate improvements, ranked by the gain the numbers above make plausible

| lever | what | acts on | expected gain (to be measured) | decided by | cost / risk |
|---|---|---|---|---|---|
| **A** | **Real averaging in the firmware**: wait for fresh conversions (or hardware averaging 8–32) instead of re-reading the last result 500 times | white noise of every point, hence of f and Γ per sweep | if N_eff is ~30 today, σ per point falls by up to √(500/30) ≈ 4× at the same sweep time — or the same σ in a quarter of the time | C1, C2, D2 | firmware change, needs the two boards' regression; `AVERAGE_SAMPLE` and averaging are already parameters |
| **B** | **A coarser grid with a longer dwell**: 18 001 points at 1 Hz spend > 95 % of the sweep on wings the estimator never uses (±3Γ is 400 points in air); 5–10 Hz steps with the dwell multiplied accordingly, or a window scaled to the tracked Γ | white noise per point (√10 at 10 Hz) or cycle time (9.3 s → ~1 s) | A5 sizes it offline; C3 says the dwell a step can afford | A5, C3, D2 | changes the sweep contract (`FREQUENCY_STEP`, `LEFT/RIGHT`, the fold baseline of the first 100 samples, the 1 Hz quantum of argmax); the tracker must still catch jumps between cycles. The largest lever and the most invasive |
| **C** | **Estimator noise**: the standard argmax is quantised to the grid and the two crossings use four samples; the PSL fit uses 300 and is unbiased by the SG window | σ(f), σ(Γ) per sweep | A1/A4 quantify; the fit's σ is the floor of what the sweep contains | A1, A4, D1 | none in the chain: the fit exists as the experimental mode; the decision is Marco's and stays his (D8) |
| **D** | **SG window** for the standard estimator: 51 at 1 Hz biases Γ in air (+9/+16 %) and buys noise reduction that a fit does not need | bias of Γ; σ of argmax | A2 gives the window that minimises σ² + bias² | A2 | one constant; changes published Γ on n = 1, 3 in air → needs the opt-in rule or Marco's dated decision |
| **E** | **Stage 6 spline**: an interpolating spline through smoothed points onto the same grid | cost only, if A3 confirms | ms per overtone, nothing on noise | A3 | removal, if confirmed no-op to 10⁻³ σ |
| **F** | **Buffer size** (`environment`): 3 → 10 lowers σ_white by ≈ 1.6 (median of 3 → trimmed mean of 8) at 93 s of lag | white noise of the logged value | only if B1 shows white noise still falling at τ ≈ 90 s; §2.2 suggests drift already dominates at 60 rows | B1, B3 | the production value is 10 anyway (memory: restore before build); this block decides whether 10 is right, not whether to restore it |
| **G** | **Duplicate datalog rows** | the file, not the measurement | a clean statistic; possibly a smaller file | B4 | a fix on `main`, cherry-picked |
| **H** | **Drift**: temperature at millikelvin in the log, then E1 | the minutes-scale spread, which is what the plateau tables of every README report as "± sd" | unknown until measured; §2.2 says it is the larger term | B2, E1 | firmware print + datalog column; the physics after that is hardware |

Not proposed, and why: a 13/16-bit ADC (the Teensy 4.0 ADC is 12-bit; hardware averaging is the only way
up); serial resolution (stage 3 is already below the content of the mean); `SPLINE_FACTOR_G` tuning (E says
remove or keep, not tune); anything on the published quantities without the opt-in switch of
`new-estimators-are-experimental-opt-in`.

## 5. Decisions that are Marco's

| | question |
|---|---|
| D1 | Which noise is the target: the value logged every cycle (levers A–F), the plateau over minutes (H), or both? §2.2 says they are different problems. |
| D2 | Order of the blocks. Recommendation: **B1 and A first** (offline, a day, no bench), then **C1** (one test build, one number, decides A and the premise of B), then D1. E1 only if D1 says drift is the target. |
| D3 | Whether a test firmware build for C1–C4 may go on the prototype board (the `-TEST` variant without TEC is the natural host). |
| D4 | Whether the datalog may gain a millikelvin temperature column (B2) — a format change, on `main` first. |
| D5 | Whether lever B (grid and dwell) is on the table at all: it changes the sweep the instrument has always made. |

**Marco, 2026-09-17 (chat), on the levers:** A — later, not now. B — asked what it means (a denser grid around the
maximum, sparser on the wings): yes, that or the same grid with a longer dwell where the estimator reads. F — he
would increase `environment`; the answer he wanted is whether that smooths the signal: it does, in time (a moving
trimmed mean with a lag of half the buffer, 46 s at N = 10; white noise down ≈ 1.6×, drift untouched, a real step
smeared over 93 s). G — investigate immediately: done, §2.3. H — 0.01 °C is enough for him: B2/E1 stay as written
but the millikelvin column is **not** wanted.

## 6. What this plan does not touch

The exact inversion, the fold decision and δ, D = 2Γ/f, the published estimator and its experimental mode,
N-SCALE, the sweep window's role in peak tracking. A change that moves a published value goes through a
Measurement Setup switch chosen before START and its own datalog suffix, as the estimator did.
