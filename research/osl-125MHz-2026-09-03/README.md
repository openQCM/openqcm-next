# Open / Short / 50 Ω characterisation — 125 MHz board, 2026-09-03

Three full-band sweeps of the openQCM NEXT front end with **known terminations in place of the
sensor**, acquired through the Peak Detection path (1–51 MHz) on a board whose DDS system clock is
125 MHz.

| file | termination | ideal `Z_x` |
|---|---|---|
| `cal_open.txt` | open circuit | ∞ |
| `cal_short.txt` | short, 0 Ω | 0 |
| `cal_load50.txt` | 50 Ω resistor | 50 + j0 |

`_before-sensor/` holds the calibration files as they were with the real sensor mounted, kept so the
instrument can be put back without re-acquiring.

---

## 1. File format

Plain text, whitespace-separated, **100 001 rows**, no header:

```
<frequency Hz>  <magnitude "dB">  <phase "deg">
1.000000000000000000e+06 -1.550677490234375355e+01 -1.049853515625009948e+00
```

- **column 1** — frequency in Hz: 1 000 000 to 51 000 000 in steps of 500 Hz.
- **column 2** — the magnitude channel, in the instrument's own "dB" units.
- **column 3** — the phase channel, in the instrument's own "deg" units.

⚠️ **Columns 2 and 3 are not physical dB and degrees.** They are the ADC voltages after a linear
rescaling, and you must undo it before doing anything else.

## 2. Recovering the detector voltages

The AD8302 gain/phase detector sits behind the divider. Its two outputs were converted with

```
column2 = (V_MAG − 0.9) / 0.030          column3 = (V_PHS − 0.9) / 0.010
```

so:

```python
V_MAG = 0.9 + column2 * 0.030      # volts at the ADC
V_PHS = 0.9 + column3 * 0.010      # volts at the ADC
```

## 3. Detector transfer functions

**Phase.** The AD8302 emits the **magnitude** of the phase difference, 1.8 V at 0° and 0.9 V at 90°:

```python
abs_phi_deg = (1.8 - V_PHS) / 0.010
```

⚠️ It is `|Δφ|`. The sign is not measured and cannot be recovered from one point; it changes where
the true phase crosses zero, which is the **peak** of `V_PHS`.

⚠️ Note the two conventions in circulation: `column3` is `90 − |Δφ|`, while the impedance code works
with `|Δφ|` itself. They differ by a sign and 90°, and mixing them is the single easiest mistake to
make with this data.

**Magnitude.** 30 mV/dB around 0.9 V, **and there is an attenuator to undo first**:

```python
K_ATT = (47.0 + 4.99) / 4.99                    # 10.418838, from the schematic
V_MAG_OFFSET = 20 * log10(K_ATT) * 0.030        # 0.61069 V
V_MAG_corrected = V_MAG - V_MAG_OFFSET
M = 52.3 * 10 ** ((0.9 - V_MAG_corrected) / 0.6)   # |Z_x + R17| in ohm
```

⚠️ **Do not skip the attenuator term.** Without it `M` comes out about **12× too small** and the
whole reconstruction is nonsense — the short reads 4 Ω instead of 52. It is 20.3564 dB, *not* one
clean decade; a hardcoded 0.600 V leaves 0.3564 dB uncompensated, which is 4 % on `M` and up to 22 %
on the reconstructed motional resistance.

## 4. Reconstructing the impedance

`R17 = 52.3 Ω` is the series resistor of the measuring divider. `M` above is `|Z_x + R17|` and
`|Δφ|` is the phase of that same sum:

```python
phi = deg2rad(abs_phi_deg)          # sign ambiguous, see above
Z_x = M * exp(-1j * phi) - 52.3     # R_x = M cos(phi) - 52.3 ;  X_x = -M sin(phi)
Y_x = 1 / Z_x                       # G = real, B = imag
```

## 5. What each standard is worth

⚠️ **`short` and `load50` are purely resistive, so the true phase is exactly 0° at every
frequency.** Every degree measured on them is the instrument. That is what makes them the useful
pair — the open is dominated by stray capacitance and tells you mostly about the dynamic-range
floor.

Expected, ideally:

| | `M` | `|Δφ|` | `Re(Z_x)` | `Im(Z_x)` |
|---|---|---|---|---|
| short | 52.3 Ω | 0° | 0 | 0 |
| load50 | 102.3 Ω | 0° | 50 | 0 |
| open | → ∞ | → 90° | → ∞ | capacitive |

## 6. Traps, in the order they will catch you

0. ⚠️ **The two dump formats are NOT on the same scale.** `cal_*.txt` (this folder) holds
   `data_mag`/`data_ph` straight from the ADC, **attenuator not compensated** — apply §3. The
   `g<n>.txt` sweeps from the multiscan dump hold `V_MAG` **already compensated** by
   `_Vmag_bit_mag` (it subtracts `V_MAG_DECADE_OFFSET` itself). Subtracting it again puts the
   crystal at 10.4× its true impedance — above an open circuit, which is impossible — and that
   is exactly what happened in the first analysis of these files. Mix the two only after putting
   both on the compensated scale.
1. **The attenuator** (§3). Costs a factor of 12.
2. **The two phase conventions** (§3). Costs a sign and 90°.
3. **The sign of `Δφ`** is not in the data. On a resistive standard the true phase is 0, so it does
   not matter; on a resonator it does, and it flips at the peak of `V_PHS`.
4. **The top of the band.** The DDS is clocked at 125 MHz and the practical guidance for a clock
   generator is to keep the output below ~40 % of it, i.e. ~50 MHz. The sweep runs to 51 MHz, so the
   last megahertz is at or past that limit and its residuals should not be read as physics.
5. **1 MHz.** The first point or two sit at the edge of the detector's useful range and are visibly
   worse than the rest; start fits at 3 MHz.

## 7. What the three standards can and cannot do

The general linear one-port model is **bilinear**, `W = (aZ + b)/(cZ + d)`: three complex unknowns
per frequency, hence three standards. In closed form:

```
Z_x = R_L · (W − W_s)(W_o − W_L) / ((W_L − W_s)(W_o − W))
```

which reduces to the two-standard **affine** form `R_L·(W − W_s)/(W_L − W_s)` as `W_o → ∞`. Check
before trusting an implementation: it must return exactly 0 for `W = W_s` and `R_L` for `W = W_L`. A
sign slip in the denominator returns `−Z` and makes the conductance negative at resonance.

⚠️ **No linear one-port calibration can change the roundness of the admittance locus.** A bilinear
map is a Möbius transformation, and Möbius transformations map circles to circles: the circle-fit
residual is **invariant** under any OSL. Measured on the crystal sweeps of this board: 9.67 % before,
9.74 % after. So the 6–15 % out-of-round seen on this front end is **not** a linear error network. It
is non-linearity, noise or drift in the detector, and OSL is the wrong tool for it — the right tools
are a standard in the operating range and, if it persists, a change of `R17`.

What OSL **does** change is the absolute values: on this board it raises Γ by 10–50 % (73→82,
31→47, 56→69, 91→102, 151→167 Hz on n = 1…9) and gives `R_m` = 52, 21, 35, 58, 110 Ω. Which of the
two Γ is right needs a reference the data cannot provide — that is what a 4th, validated standard
is for.

## 8. What a first analysis found

Fitting `|Δφ|` against frequency over 3–51 MHz on the two resistive standards:

| | slope | → delay | residual rms |
|---|---|---|---|
| `short` | 0.2722 °/MHz | **0.76 ns** | **0.57°** |
| `load50` | 0.3972 °/MHz | **1.10 ns** | **0.52°** |

⚠️ **The phase error is a delay, to within about half a degree over 48 MHz.** It is linear, not
shaped: whatever else the front end does, its phase is not distorted in a way that a single delay
constant fails to describe.

The two standards disagree on that delay by 46 % (0.34 ns ≈ 10 cm of cable), which is what one would
expect if they have different mechanical offset delays of their own. Separating the board's own
delay from the standards' requires their specifications, or a third measurement.

Magnitude, with the attenuator undone: `M` reads **6–11 % low** and the error is
frequency-dependent, improving toward the top of the band. A 50 Ω resistor reconstructs as
**41–43 Ω** with a reactance that grows to **−23 Ω at 45 MHz** — the reactance is the uncorrected
delay showing up as apparent capacitance, the 17 % on the real part is not.

Acquired with `OPENQCM_CAL_DUMP=<label>`, which writes `sweep_data/cal_<label>.txt` before the peak
logic runs — the ordinary `Calibration_5MHz.txt` is only written when a 4–6 MHz fundamental is
found, so an open or a short produces nothing at all.
