# THE ALGORITHM — from AD8302 voltages to resonance frequency and bandwidth

> **This is the one document on this branch that must never be lost.** Everything else — the panel,
> the fit window, the offline scripts, the CHANGELOG — can be rebuilt from the code. This cannot: it
> is the chain of reasoning and of constants that turns two voltages into a measurement, including
> the choices that look arbitrary and are not, and the traps that cost days to find.
>
> Written 2026-07-28 against `processors/Multiscan.py` on `impedance-analysis`. Line numbers are
> given as a hint; the function names are the contract.

---

## 0. What this branch changes with respect to `main`, exactly

Verified by full diff on 2026-07-28 (`main` = `7f80f82`, content of `52a42a9`; branch = `f315229`).

**`main` measures the resonance frequency and the bandwidth from the magnitude channel alone.**
`elaborate_multi()` baseline-corrects the magnitude with the calibration polynomial, smooths it,
splines it, and hands it to `parameters_finder()`, which returns the frequency of the maximum and
the width at `THRESHOLD_DB = 0.3` dB below that maximum. The phase channel is converted and shipped
to the plot, and **never enters a published number**.

**This branch measures both from the complex admittance**, reconstructed from the magnitude *and*
the phase channel. Three lines in `elaborate_multi()` switch the source:

| | `main` | this branch |
|---|---|---|
| `_my_list_f[n]` (logged frequency) | `frequency_resonance` from `parameters_finder` | `frequency_resonance_G` from `parameters_finder_impedance_exact` |
| `_my_list_d[n]` (logged "dissipation") | `Qfac_fit/1e6` — full width at −0.3 dB of the magnitude | `half_bandwidth/1e6` — HWHM of the conductance |
| `freq_res_current_array[n]` | `freq_range[index_peak_fit]` | `freq_range[index_peak_fit_G]` |

That third line is not a logged value: it is the frequency the **next sweep is centred on**. So on
this branch the sweep window tracks the conductance peak, not the magnitude peak. It is part of the
same claim, but it is a feedback path and deserves naming.

**Everything else in the pipeline is the same, and that is not an assumption:**

- `constants.py`: **nothing removed or changed**, only additions.
- `worker.py`, `Parser.py`, `mainWindow_ui.py`: purely additive (one extra queue, its buffers, the
  panel and two menu entries).
- `mainWindow.py`: four changed lines, all of them adding the two new plots to existing collections.
- `Multiscan.py`: 18 changed lines. Four are whitespace. Three are the table above. The rest change
  *what is passed to* `elaborate_multi()`: `main` passes magnitude and phase already converted to
  dB and degrees, this branch passes the **raw ADC bits** and converts them inside.
- The magnitude signal that reaches `parameters_finder()` is therefore **bit-identical** to `main`'s.
  Proven numerically over the whole ADC range: `_mag_bit_mag(bits)` minus `main`'s
  `(bits*ADCtoVolt/2 − V_CP)/0.03` is **0.000e+00** at every one of 20 001 test points. `main`'s
  measurement still runs on this branch, unchanged, alongside the new one.

**Two differences that are real and are not the measurement:**

1. **The phase channel conversion differs.** `main`: `(V_PHS − 0.9)/0.01`. This branch
   (`_phase_bit_phase`): `(1.8 − V_PHS)/0.01`. Their sum is the constant 90, so they are mirror
   conventions: `main` reports `90 − |φ|`, this branch reports `|φ|` in degrees, which is the
   physical quantity (see §3). `main` never uses it for a number, so nothing is wrong there — but
   the *displayed* phase curve differs between the two branches.
2. **This branch writes `g<n>.txt`** (frequency, `V_MAG`, `V_PHS`) on every sweep, which `main` does
   not. Those files are the input of every offline analysis in `sweep_data/`.

---

## 1. The measurement circuit, and what the two voltages mean

The crystal sits in a voltage divider against a series resistor to ground, and an **AD8302
gain/phase detector** compares the two nodes:

```
V_in ──┬── Z_q ──┬── R17 ──┬── GND
       │         │         │
     INPB      INPA       GND
```

- `Z_q` — the quartz impedance, complex, unknown. This is what we want.
- `R17 = 52.3 Ω` — `Constants`… no: `MultiscanProcess.R17_EXACT`, class attribute, `Multiscan.py:395`.
- The divider transfer function is `H = V_INPA/V_INPB = R17/(Z_q + R17)`.

The AD8302 puts out two DC voltages:

- **`V_MAG`** — the magnitude ratio, **30 mV/dB**, centred on `V_CP = 0.9 V`
  (`MultiscanProcess.V_CP_EXACT`, `Multiscan.py:396`):
  `V_MAG = 0.030·20·log10(V_INPB/V_INPA) + V_CP`.
- **`V_PHS`** — the phase difference, **10 mV/deg**, also centred on `V_CP`, and it is a
  **magnitude**: the device cannot tell the sign of the phase difference.
  `V_PHS = −0.010·(|Δφ| − 90°) + V_CP`.

⚠️ **The INPB input is attenuated** by the R11/R19 divider added to the board
(`Constants.R11_ATT = 47.0`, `Constants.R19_ATT = 4.99`). Undoing it is step 1 and it is where a
4 % error hid for months — see §2.

---

## 2. Step 1 — ADC bits to volts

`elaborate_multi()` receives the **raw ADC counts** of both channels (`Xm`, `Xp`) and converts them
four times, for four different purposes. Two matter here.

### 2.1 `V_MAG` — `_Vmag_bit_mag()`, `Multiscan.py:697`

```python
vmax, bitmax = 3.3, 4096
ADCtoVolt = vmax / bitmax
Vmag = bit_mag * ADCtoVolt / 2          # /2: the op-amp in front of the ADC
Vmag = Vmag - Constants.V_MAG_DECADE_OFFSET
```

- `/2` is the buffer gain ahead of the ADC on the magnitude channel. Not a fudge factor.
- **`V_MAG_DECADE_OFFSET = 0.61069 V`**, `constants.py:349`, and this number is the whole point:

  ```python
  K_ATT = (R11_ATT + R19_ATT) / R19_ATT               # = 10.418838
  V_MAG_DECADE_OFFSET = 20.0 * np.log10(K_ATT) * 0.030   # = 0.610692 V
  ```

  The attenuator is **20.3564 dB, not 20 dB**. At 30 mV/dB that is 0.61069 V, not 0.600. The
  hardcoded 0.600 that stood here until 2026-07-28 left a residue of 0.3564 dB, which understates
  `M = |Z_q + R17|` by **4.02 %** — and §4 shows that error is amplified by `(1 + R17/R_m)`, so it
  reached **−22 % on `R_m`** at the fundamental in air. Verified against a synthetic THRU
  (`Z_q = 0.001 Ω`): `M` reads 50.199 Ω with 0.600 and 52.301 Ω with 0.61069, against a true
  52.30 Ω.
- ⚠️ **Do not baseline-correct this channel.** There is a second, baseline-corrected copy
  (`Vmag_result_fit`, built with `baseline_coeffs_Vmag()`), and it must never be fed to §4: the
  inversion needs the **absolute** divider level. Subtracting the calibration polynomial scales `M`
  by `10^(V_baseline/0.6)` — 0.55× at the fundamental on real data — which drives `M(res)` below
  `R17`, makes `R_q` negative over the whole sweep and produces circles of negative conductance.
  That was the 2026-07-23 bug. The variable that goes into §4 is **`Vmag_raw_result_fit`**.

### 2.2 `V_PHS` — `_Vphase_bit_phase()`, `Multiscan.py:710`

```python
Vphase = bit_phase * ADCtoVolt / 1.5    # /1.5: op-amp gain on the phase channel
```

No offset, no baseline correction, ever. The off-resonance phase is the DUT's physics, not a board
artifact.

---

## 3. Step 2 — smoothing and resampling

Both channels get the same two-stage treatment, `Multiscan.py:977…996`:

```python
filt = self.savitzky_golay(V, window_size = SG_window_size, order = Constants.SG_order)
s    = UnivariateSpline(range(len(filt)), filt, s = Constants.SPLINE_FACTOR_G)
xs   = np.linspace(0, len(filt) - 1, points)
V_result_fit = s(xs)
```

- `SG_window_size` comes per overtone from `getMultiscanParameters_5Mhz()` and is
  `Constants.SG_WINDOW_SIZE = 51` samples for every overtone today.
- `Constants.SG_order = 3`.
- `Constants.SPLINE_FACTOR_G = 0.001` — note this is **not** the `SPLINE_FACTOR = 1` used for the
  legacy magnitude path. The impedance path is smoothed far less, deliberately: the conductance peak
  in air is a few tens of hertz wide.
- `points = Spline_points = int(stopF − startF) + 1`, so the output grid is **1 Hz** and has 18 001
  points for the standard −12 kHz/+6 kHz window. `freq_range` is built on exactly the same grid,
  `np.linspace(readFREQ[0], readFREQ[-1], points)`.

The three arrays that leave this step and matter downstream:

| variable | contents |
|---|---|
| `mag_result_fit` | baseline-corrected magnitude in dB — feeds `main`'s legacy measurement, untouched |
| `Vmag_raw_result_fit` | **absolute** `V_MAG` in volts, smoothed — feeds §4 |
| `Vphase_result_fit` | `V_PHS` in volts, smoothed — feeds §4 |

---

## 4. Step 3 — the phase channel: fold, offset, sign

This is the subtlest part of the whole algorithm and it has been got wrong three times. Read all of
it before changing a line.

### 4.1 The reading

`_phase_raw_V_phase()`, `Multiscan.py:348`:

```python
phase = (1.8 - Vph_var) / 0.01
```

which is `(V_CP − V_PHS)/0.010 + 90` — i.e. the **magnitude of the phase in degrees**, as the
detector reports it. Call it `r(f)`.

### 4.2 The model of the reading

The detector emits `|Δφ|`, and the board adds a phase of its own, and the channel has a voltage
offset. The reading is therefore

```
r(f) = | φ(f) + φ_b | − δ
```

- `φ(f)` is the phase we want: `−∠(Z_q + R17)`, the quantity §4.4 needs.
- `φ_b` is a board/cable phase, **inside** the absolute value. Measured at −12…−20° and reproducible
  to 0.2–0.4° across acquisitions, but **not corrected today** — see §9.
- `δ` is a voltage offset of the channel, **outside** the absolute value.

Two consequences that are not obvious:

- Where the argument crosses zero — air, low damping — the reading reaches its minimum, and there
  `min(r) = −δ` **exactly**. On this instrument `min(r)` comes out **negative** (as low as −14°),
  which looks impossible for a magnitude detector and is in fact the signature of `δ`.
- **So `δ` is measured, not fitted.** A fold determines it; there is no freedom left.

### 4.3 Taking `δ` from the fold — `_phase_offset_fold()`, `Multiscan.py:508`

```python
p_min = float(np.nanmin(phase_folded))
if not np.isfinite(p_min) or p_min >= Constants.FOLD_THRESHOLD_DEG_G:
    return 0.0, False          # no fold
return -p_min, True            # delta, fold present
```

`Constants.FOLD_THRESHOLD_DEG_G = 5.0` degrees. `δ` of either sign is legitimate: it is whatever
brings the vertex of the V to zero.

**No fold means a damped load** (liquid): `C0` and strays dominate, the total phase never crosses
zero, its minimum stays 12–44° above it. Then there is nothing to unfold and nothing to offset —
`r` already *is* the signed phase. Applying the offset and the flip anyway inverts half the sweep
and distorts the locus into an "S"; observed on-device in isopropanol, 2026-07-27.

Then, `Multiscan.py:1029`:

```python
phase_corr = phase_folded + phase_offset
```

### 4.4 Two different phases for two different quantities

```python
# G: from phase_corr, WITHOUT the sign flip
R_q_G, X_q_G = self._RX_exact(Vmag_raw_result_fit, phase_corr)
G_exact_S    = self._G_exact(R_q_G, X_q_G)

# B: from phase_corr WITH the sign flip, and only if there is a fold
phase_signed = np.array(phase_corr, dtype=float, copy=True)
if has_fold:
    i_flip = int(np.nanargmin(np.abs(phase_corr)))
    phase_signed[i_flip:] = -phase_signed[i_flip:]
R_q, X_q  = self._RX_exact(Vmag_raw_result_fit, phase_signed)
B_exact_S = self._B_exact(R_q, X_q)
```

Why the asymmetry: **`G` is even in the sign of the phase, `B` is odd.** `R_q = M·cos φ − R17` and
`cos` is even, so flipping the sign leaves `R_q` and therefore `G` untouched; `X_q = −M·sin φ` is
odd, so `B` changes sign. The flip is needed to give `B` the sign the unfolded branch should have,
and it cannot affect the published frequency and bandwidth, which come from `G` alone.

⚠️ **`G` is even in the SIGN but not in the OFFSET.** `δ` matters to `G`. A change on 2026-07-28
dropped the offset correction on the grounds that "G is even in φ" and took the circle residual from
1.6–3.1 % to 4.1–14.6 % of the radius. Reverted.

⚠️ **The flip must be applied only where a fold exists.** Flipping on a damped load makes `B` jump
by up to **80 %** of its own range at the flip point and breaks the locus into two disconnected
arcs. Measured on the 2026-07-28 water run.

⚠️ **Do not estimate `δ` by making the locus round.** It was tried
(`_phase_offset_deg()`, still in the file, unused, documented as superseded). The objective is
computed on the point *cloud* and the sign flip happens *inside* it, so the search buys roundness by
pushing `δ` until the flip lands on the antipode of the circle: `δ` came out up to 12° beyond
`−min(r)`, `B` jumped by up to 77 % of its range, and the *cloud* looked rounder (1.4 % against
4.5 %) while the trajectory was broken. In water it split the locus and the residual metric called
that an improvement (11.1 % against 19.8 %) because a circle through two disconnected arcs can have
a small radial residual and no physical meaning. **A continuous trajectory is not negotiable;
roundness is a diagnostic, never an objective.**

---

## 5. Step 4 — the exact complex-divider inversion

`_RX_exact()`, `Multiscan.py:424`:

```python
M   = self.R17_EXACT * np.power(10.0, (self.V_CP_EXACT - V_mag) / 0.6)
phi = np.deg2rad(phase_signed_deg)
R_q = M * np.cos(phi) - self.R17_EXACT
X_q = -M * np.sin(phi)
```

Derivation, so it can be rebuilt from nothing:

1. The detector measures `|V_INPB/V_INPA| = |Z_q + R17|/R17`. Inverting the 30 mV/dB law:
   `20·log10(|Z_q+R17|/R17) = (V_CP − V_MAG)/0.030`, hence

   ```
   M ≡ |Z_q + R17| = R17 · 10^((V_CP − V_MAG)/0.6)
   ```

   The `0.6` is `20 × 0.030` — the AD8302's own decade. **It is not the attenuator**; the attenuator
   was already removed in §2.1. Mixing the two up is an easy mistake: `g<n>.txt` stores `V_MAG`
   already compensated, so an offline script must use `0.6` here and nothing else.
2. The transfer function phase is `∠H = −∠(Z_q + R17)`, and the reconstruction convention is
   `Z_q + R17 = M·e^{−jφ}`. Therefore

   ```
   R_q = M·cos φ − R17
   X_q = −M·sin φ
   ```

⚠️ **This is where the sensitivity lives.** At resonance `X_q → 0` and `M → R_m + R17`, so
`R_q = M·cos φ − R17` is a **difference of two close numbers**. With `R_m = 12 Ω` and `R17 = 52.3 Ω`,
a 1 mV error on `V_MAG` moves `R_m` by about **2 %**. Two corollaries:

- the attenuator constant of §2.1 is not a detail;
- **the diameter of the fitted admittance circle is a more robust estimator of `R_m` than the peak
  of `G(f)`**, because it averages a well-conditioned arc instead of trusting the single
  worst-conditioned sample.

---

## 6. Step 5 — admittance

`_G_exact()` and `_B_exact()`, `Multiscan.py:432` and `:437`:

```python
den = np.maximum(R_q**2 + X_q**2, 1e-12)
G   =  R_q / den
B   = -X_q / den
```

`Y_q = 1/Z_q = (R_q − jX_q)/(R_q² + X_q²)`, so `G = R_q/|Z_q|²` and `B = −X_q/|Z_q|²`. The floor at
`1e-12` guards the division only; it never binds on real data.

Units: `G` and `B` in siemens. Everything downstream that says mS has been multiplied by 1000
explicitly.

**Why the conductance and not the magnitude.** For a Butterworth–Van Dyke resonator the motional
branch is `Y_m = 1/(R1 + j(ωL1 − 1/ωC1))`, whose **real part is an exact Lorentzian in the
normalised detuning** and whose locus in the complex plane is an exact **circle** that the parallel
`C0` only translates. Neither is true of `|Z|` or of the raw magnitude channel: the peak of the
magnitude sits between the series and parallel resonances and moves with `C0`, which is why the
legacy measurement needed an empirical `−0.3 dB` width and could not give `R_m` at all.

---

## 7. Step 6 — resonance frequency

`_Freq_G()`, `Multiscan.py:643`, called through `parameters_finder_impedance_exact()`:

```python
idx_max     = np.nanargmax(G_conductance)
f_resonance = F_sweep[idx_max]
```

The frequency of the maximum of the conductance, on the 1 Hz grid of §3, with no interpolation. That
is the **series resonance frequency** — the physically meaningful one for Sauerbrey and
Kanazawa–Gordon, and the reason for this whole path.

Resolution is therefore 1 Hz by construction; the smoothing of §3 is what keeps that from being
noise-limited. Sub-sample interpolation of the peak would be the next refinement and is *not* done
today.

---

## 8. Step 7 — the bandwidth

`_half_bandwidth_G_exact()`, `Multiscan.py:604`. Read this in full; every clause is there for a
reason.

```python
n_base = min(100, len(G_conductance))
G = np.asarray(G_conductance, dtype=float) - np.average(G_conductance[:n_base])
F = np.asarray(F_sweep, dtype=float)
idx_max = int(np.nanargmax(G))
half = G[idx_max] / 2.0
if not np.isfinite(half) or half <= 0:
    return 0.0
```

1. **A baseline is removed first**: the mean of the first 100 samples of the sweep, taken as an
   off-resonance level. Necessary because `G` sits on the `C0`/stray pedestal, and half of a peak
   measured from the wrong zero is the wrong half.
2. **Half height of the peak**, on that baseline.

```python
def _cross(i_lo, i_hi):
    g0, g1 = G[i_lo], G[i_hi]
    if g1 == g0:
        return F[i_lo]
    return F[i_lo] + (half - g0) * (F[i_hi] - F[i_lo]) / (g1 - g0)
```

3. **Linear interpolation of the crossing between the two straddling samples.** Snapping to the
   nearest grid point instead quantises `D` by a few percent: at the fundamental in air the half
   width is a few tens of hertz on a 1 Hz grid.

```python
below = np.where(G[:idx_max] < half)[0]
if len(below):
    i = int(below[-1]);            f_left  = _cross(i, min(i + 1, idx_max))
below = np.where(G[idx_max:] < half)[0]
if len(below):
    j = idx_max + int(below[0]);   f_right = _cross(j, max(j - 1, idx_max))
```

4. The crossings are found as the **last sample below half on the left** and the **first below half
   on the right** — searching outwards from the peak, so a noisy shoulder cannot be mistaken for the
   crossing.

```python
if f_left is not None and f_right is not None:
    return (f_right - f_left) / 2.0
if f_left is not None:
    return f_res - f_left
if f_right is not None:
    return f_right - f_res
return 0.0
```

5. **Two-sided, and it returns the HALF width** `(f_right − f_left)/2`. The predecessor
   (`_half_bandwidth_G`, still in the file, unused) measured `f_res − f_left` and called it the
   width: that is only right for a symmetric peak, and the real one is skewed by the residual `C0`
   branch. Going two-sided removed a consistent **~20 %** bias on both air and liquid data.
6. **Fallbacks**, in order: two-sided, then whichever single side exists. A single side is returned
   when the sweep window does not contain the other crossing — which happens on damped loads, where
   the half width reaches kilohertz against a window sized for air (see §9).

---

## 9. Step 8 — what is published, and in which units

`Multiscan.py:1176` and `:1180`:

```python
self._my_list_f[overtone_number].append( frequency_resonance_G )
self._my_list_d[overtone_number].append( (half_bandwidth/1000000) )
```

and `Multiscan.py:1213`:

```python
self.freq_res_current_array[overtone_number] = freq_range[int(index_peak_fit_G)]
```

⚠️ **The column called `Dissipation_n` in the CSV is not a dissipation.** It is
`half_bandwidth/1e6` — the **half width at half maximum, expressed in MHz**. It is dimensional and
it is a half width. To get the dimensionless dissipation:

```
D = 2 · half_bandwidth / f_r          (= FWHM / f_s)
```

The naming is inherited from `main`, where the same column held the full width at −0.3 dB of the
magnitude, also in MHz. That is why the logged numbers dropped 2–4× in air when this branch switched
the source: the quantity changed from "full width at −0.3 dB of `|H|`" to "half width at half
maximum of `G`". **Data logged by `main` and by this branch are not comparable on that column.**

### Open defects that bite exactly here

- **In liquid the baseline of §8.1 is taken on the resonance.** The sweep window is fixed at
  −12 kHz/+6 kHz around the previous peak (`Constants.LEFT`/`RIGHT` through
  `getMultiscanParameters_5Mhz`), sized for air, while `Γ_FWHM` in water is 1.9–5.0 kHz. So the
  first 100 samples sit 2.4–6.3 half-widths from resonance and the "baseline" is **13 % of the peak
  on the 3rd overtone and 66 % on the 9th**. The circle fit does not care — subtracting a constant
  translates the locus and the fit is translation-invariant — but the half-height crossings do:
  measured against a Lorentzian with a free background, the published width is low by **−2.5 %
  (n=1), −4.3 %, −4.3 %, −7.4 %, −13.9 % (n=9)**. Fix by taking the width from a Lorentzian fit, or
  by scaling the sweep window with the measured `Γ`. Changes published values, so it waits.
- **The board phase `φ_b` of §4.2 is not corrected.** With `δ` taken from the fold the locus is
  still 1.2–7.9 % out of round in air, systematically and reproducibly. Fitting the forward model to
  both channels gives `φ_b` = −12…−20°, reproducible to 0.2–0.4° across acquisitions 83 minutes
  apart, and improves both channel residuals 4–5× — but applying it as a rotation *after* unfolding
  restores continuity without recovering roundness, so it is not yet the whole story. Reference-load
  (RLC standard) calibration is the only way to settle whether the two-parameter model is right or
  merely better.
- **Dynamic range.** `R17 = 52.3 Ω` against a liquid load of 0.6–3 kΩ puts the *whole* sweep at
  −23 to −36 dB of divider ratio, against the AD8302's specified ±30 dB, with a resonance contrast
  of about 6 dB. A saturation mask exists (`Constants.RATIO_DB_FLOOR = −28.0`,
  `IMPEDANCE_PANEL_MASK_SATURATED`) and **ships disabled**: at that floor it removes 35–63 % of the
  band in water, which is too much to be a default. The real fix is a larger or switchable reference
  resistor.

---

## 10. Step 9 — what goes to the screen (and why it is not the same arrays)

`Multiscan.py:1183…1215`. The panel and the live fit window receive a **processed copy**, never the
published arrays:

1. `G` and `B` are converted to mS.
2. A constant baseline is removed from **both** (mean of the first 100 samples) so the locus closes
   into a circle centred near the origin. ⚠️ This is why the fit window does not report `C0`:
   translating the circle is exactly what `C0` does, so the fitted offset is no longer `ω·C0`.
   `f_s`, `Γ`, `D` and `R_m` are unaffected — they come from the radius and the arc, both
   translation-invariant.
3. The spectrum is clipped to `Constants.IMPEDANCE_PANEL_BAND_GAMMA = 3.0` half widths around the
   peak, floored at 5 % and capped at 100 % of the sweep span. Off-resonance samples carry no shape
   information — they collapse onto one point of the locus — and on a damped load they are the ones
   measured deepest in the dynamic-range corner.
4. Optionally the saturation mask (disabled today, §9).
5. One overtone per queue message, `[idx, freq, G, B, f_r, Γ, δ, masked_%]`, converted to numpy on
   the consumer side once per sweep rather than once per repaint.

---

## 11. A worked example, end to end

Real numbers, from
[`reference-sweep/g1.txt`](reference-sweep/g1.txt) — a **frozen** copy of one water acquisition
(2026-07-28 17:58), kept in the repository precisely so this example stays reproducible;
`software/openQCM/sweep_data/` is runtime output and is overwritten by every sweep. The sample below
is the one where `G` peaks. Recompute these and you have verified your reimplementation.

| quantity | value |
|---|---|
| sample index | 12 011 of 18 001 |
| frequency `f_i` | 4 998 012 Hz |
| `V_MAG` from the file | 0.194775 V |
| `V_PHS` from the file | 1.769985 V |
| reading `r = (1.8 − V_PHS)/0.01` | +3.0015° |
| `min(r)` over the sweep | +1.2597° → fold present (below 5°) |
| `δ = −min(r)` | −1.2597° |
| corrected phase `φ` | +1.7418° |
| `M = R17·10^((0.9 − V_MAG)/0.6)` | 783.2069 Ω |
| `R_q = M·cos φ − R17` | 730.5450 Ω |
| `X_q = −M·sin φ` | −23.8066 Ω |
| `G = R_q/(R_q²+X_q²)` | 1.367389e−03 S = 1.3674 mS |
| `R_m = 1/G_max` | 731.32 Ω |
| baseline (mean of first 100 `G`) | 6.419370e−06 S |
| half height | 6.804848e−04 S |
| left crossing, interpolated | 4 997 108.558 Hz |
| right crossing, interpolated | 4 999 014.806 Hz |
| `half_bandwidth = (right − left)/2` | 953.124 Hz |
| **logged `Frequency`** | **4 998 012 Hz** |
| **logged `Dissipation`** | **0.000953124** (= 953.124 Hz / 1e6) |
| dimensionless `D = 2·hw/f_r` | 381.40 ppm |

Note `δ` is *negative* here: the reading grazes +1.26° without going below zero, so the offset that
brings the vertex to zero is negative. Legitimate, and a good test case for any reimplementation.

---

## 12. Independent cross-check

`sweep_data/fit_admittance.py` reads the same `g<n>.txt` and fits the same physics **two ways that
share nothing**:

- **FIT 1** — Butterworth–Van Dyke circle on the complex admittance, with `f_s` and `Γ` read off the
  arc geometry by linear least squares (`ψ = −2·arctan x`, `x = (f²−f_s²)/(f·Γ)`, linear in
  `(Γ, f_s²)`), plus a fitted rotation and weights `w = 1/(1+x²)²` derived from the angular
  uncertainty.
- **FIT 2** — Levenberg–Marquardt Lorentzian on `G(f)` with a free linear background.

Their **disagreement is the honest error bar**, and it is the metric to trust when a residual looks
good: in clean air they agree to 1.4–5.4 ppm on `f_s` and a few percent on `Γ`; when they diverge by
20 % something is wrong with the data, not with the fits. The same module is imported by the live fit
window (Tools → Impedance Fit) **by file path**, so the live and offline numbers cannot drift apart —
verified to the 8th significant digit.

Conventions differ by design and this trips everyone: **this script reports `Γ` as FWHM, the pipeline
reports the HALF width.** `D = FWHM/f_s = 2·HWHM/f_s` is the same number in both.

---

## 13. What is in the file but not in this path

Dead or superseded code, kept deliberately. None of it runs:

| symbol | status |
|---|---|
| `parameters_finder_impedance()` | the *approximate* impedance formula (`abs(Z) ≈ R17(10^x − 1)`, phase read as the phase of `Z_q`). Superseded by the exact inversion; no longer called. |
| `_Zabs_Vmag()`, `_G_calc()`, `_B_calc()` | helpers of the approximate formula. Transitively dead. |
| `_phase_offset_deg()` | the roundness-fitted `δ`. Reverted, kept because *how* it fails is instructive (§4.4). |
| `_Freq_G()` | still live — it is what `parameters_finder_impedance_exact()` calls. |
| `_half_bandwidth_G()` | the one-sided predecessor of §8. Dead. |
| `_taubin_circle()` | used only by `_phase_offset_deg()`. Transitively dead. |
| `elaborate_conductance_multi()` | ⚠️ never called, and it calls `matplotlib.pyplot.show()` **inside the acquisition process**. Would block it. Delete on sight. |
| `from scipy.interpolate import PchipInterpolator` | leftover of the reverted local phase repair. Unused import. |
| `print("DEBUG: sweep parameters …")` | left in `run()`; fires only while `k < Constants.environment`, i.e. about ten times at start-up. |

---

## 14. If you have to rebuild this from scratch

The order that matters:

1. Undo the attenuator on `V_MAG` (§2.1) with the **derived** constant, never a literal.
2. Keep the absolute `V_MAG`. Never the baseline-corrected one (§2.1).
3. Convert `V_PHS` to `|φ|` in degrees as `(1.8 − V)/0.01` (§4.1).
4. Take `δ` from the minimum of that reading, and only if the minimum is below 5° (§4.3).
5. Compute `G` from the offset-corrected phase **without** the sign flip; `B` from it **with** the
   flip, and only where a fold exists (§4.4).
6. Invert the divider exactly: `M = R17·10^((V_CP−V_MAG)/0.6)`, `Z_q = M·e^{−jφ} − R17` (§5).
7. `f_r` = argmax of `G` (§7); `Γ_half` = two-sided half-height width of `G`, baseline removed,
   crossings interpolated (§8).
8. Publish `f_r` in Hz and `Γ_half/1e6`, and remember that the second is a half width in MHz (§9).
9. Cross-check against `fit_admittance.py` on the same `g<n>.txt` before believing any of it (§12).
