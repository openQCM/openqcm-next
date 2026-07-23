# Exact Conductance Calculation for QCM Impedance Analysis

> ## VALIDATION STATUS — VALIDATED IN AIR, on-device (2026-07-23)
>
> This document is the source of the "exact" formula implemented in
> `sweep_data/plot_conductance.py` (`_RX_exact` / `_G_exact` / `_B_exact`).
>
> **History of the validation:**
> - *2026-07-21*: synthetic Butterworth–Van Dyke self-consistency check passed
>   (G_max error ~0.002 % vs ~87 % for the approximate formula) — algebra correct,
>   model/constants still unproven. First on-device air tests showed **negative
>   conductance** on the strongest modes (F0/3rd) — initially blamed on the
>   nominal constants.
> - *2026-07-23*: **root cause found — a pipeline mismatch, not the formula/constants.**
>   The exact inversion was fed the **baseline-corrected** `V_MAG` (calibration
>   polynomial subtracted — a *relative* level, appropriate only for the
>   approximate/relative G). The inversion `M = R17·10^((V_CP−V_MAG)/0.6)` needs
>   the **absolute** divider level: the subtraction scaled `M` by `10^(Vb/0.6)`
>   (0.55× at F0 on real data → `M(res) < R17` → `R_q < 0` everywhere → the
>   negative-G circles). **Fixed**: the exact block now uses the raw (absolute)
>   `V_MAG` (`amp_a_sp_raw`, same SG+spline smoothing, no baseline subtraction).
>   The **phase** channel receives no baseline correction anywhere — which is
>   *correct* for this method (off-resonance phase is DUT physics, not board
>   artifact).
> - The source PDFs confirm the assumed topology (divider `Z_q` + `R17` to ground)
>   and document the **INPB ×10 attenuation** (R11/R19 mod), which is already
>   compensated by the −0.6 V decade offset in the ADC→V conversion — so the raw
>   sweep files are at the correct absolute level for this inversion.
>
> **Quantitative air validation (5 MHz crystal, on-device, 2026-07-23):**
> physically consistent across all overtones — `R_m` = 10.6/12.1/40.5/76.5/132.6 Ω
> (F0→9th), `D` = 3–10 ppm, and the admittance-circle fit diameter matches
> `G_max` within **±5 %** (circle rms 1–6 %).
>
> **Still open (metrological refinement, mainly for liquid):** second-order
> systematics — board/cable **phase offsets** (no fold to re-anchor the phase in
> liquid), AD8302 nonlinearity near 0°, residual `ωC0` beyond the constant
> baseline; visible as a slight B/G span excess (≤17 %) and a slightly negative
> circle center. Refine via **known reference impedances / RLC standards** vs a
> calibrated impedance analyzer.
>
> **Consequence:** the live pipeline (`processors/Multiscan.py::
> parameters_finder_impedance`) still uses the **approximate** formula. Porting
> the exact formula there is now a realistic option — it **will change the logged
> frequency/dissipation values** and must be a deliberate, documented step.

## Circuit Configuration

Voltage divider topology:
- **Z_q**: QCM sensor impedance (unknown, complex)
- **R_17 = 52.3 Ω**: Series resistor to ground
- **AD8302**: Measures gain and phase between input (V_in) and divider node (V_out)

```
V_in ──┬── Z_q ──┬── R_17 ──┬── GND
       │         │          │
     INPB      INPA       GND
```

## AD8302 Output Characteristics

**Magnitude output (V_MAG):**
$$V_{MAG} = 30 \text{ mV/dB} \cdot 20\log_{10}\left(\frac{V_{INPB}}{V_{INPA}}\right) + V_{CP}$$

**Phase output (V_PHS):**
$$V_{PHS} = -10 \text{ mV/deg} \cdot (|\phi_{meas}| - 90°) + V_{CP}$$

Where $V_{CP} = 0.9$ V (center point).

## Transfer Function Analysis

The voltage divider transfer function:
$$H = \frac{V_{INPA}}{V_{INPB}} = \frac{R_{17}}{Z_q + R_{17}}$$

AD8302 measures:
- $|H|^{-1} = |Z_q + R_{17}| / R_{17}$
- $\angle H = -\angle(Z_q + R_{17})$

## Exact Calculation Procedure

### Step 1: Extract |Z_q + R_17| from V_MAG

$$M = |Z_q + R_{17}| = R_{17} \cdot 10^{\frac{V_{CP} - V_{MAG}}{0.6}}$$

### Step 2: Extract measured phase from V_PHS

$$\phi_{meas} = \frac{V_{CP} - V_{PHS}}{0.01} + 90° \quad \text{[degrees]}$$

This is the phase of the transfer function H, equal to $-\angle(Z_q + R_{17})$.

### Step 3: Reconstruct Z_q components

Since $Z_q + R_{17} = M \cdot e^{-j\phi_{meas}}$:

$$R_q = M \cos(\phi_{meas}) - R_{17}$$
$$X_q = -M \sin(\phi_{meas})$$

Where:
- $R_q$: Resistance (real part of $Z_q$)
- $X_q$: Reactance (imaginary part of $Z_q$)

### Step 4: Calculate conductance

$$G = \frac{R_q}{R_q^2 + X_q^2}$$

## Compact Formula

$$\boxed{G = \frac{M\cos\phi - R_{17}}{(M\cos\phi - R_{17})^2 + (M\sin\phi)^2}}$$

With:
- $M = 52.3 \cdot 10^{(0.9 - V_{MAG})/0.6}$
- $\phi = (0.9 - V_{PHS})/0.01 + 90°$ converted to radians

## Comparison with Approximate Method

**Previous (approximate):**
$$|Z_q|_{approx} = R_{17}\left(10^{\frac{V_{CP}-V_{MAG}}{0.6}} - 1\right)$$
$$G_{approx} = \frac{\cos\phi}{|Z_q|_{approx}}$$

**Issues:**
1. Assumes $|Z_q + R_{17}| \approx |Z_q| + R_{17}$ (valid only for real $Z_q$)
2. Interprets measured phase as $Z_q$ phase (incorrect)

**Exact method** properly accounts for:
- Complex impedance addition in the divider
- Phase transformation through the transfer function

## Implementation

```python
def calculate_conductance(V_MAG, V_PHS, R17=52.3):
    V_CP = 0.9
    
    # Step 1: |Z_q + R17|
    M = R17 * 10**((V_CP - V_MAG) / 0.6)
    
    # Step 2: Measured phase [rad]
    phi = np.deg2rad((V_CP - V_PHS) / 0.01 + 90.0)
    
    # Step 3: Z_q components
    R_q = M * np.cos(phi) - R17
    X_q = -M * np.sin(phi)
    
    # Step 4: Conductance
    denom = R_q**2 + X_q**2
    G = R_q / np.maximum(denom, 1e-12)
    
    return G
```

## Physical Interpretation

At series resonance:
- $X_q \approx 0$, $Z_q \approx R_m$ (motional resistance)
- $G_{max} = 1/R_m$ (conductance peak)
- Half-bandwidth $\Gamma$ extracted at $G_{max}/2$

The conductance spectrum $G(f)$ directly yields:
- **Resonance frequency** $f_r$: peak of $G(f)$
- **Half-bandwidth** $\Gamma$: HWHM of $G(f)$
- **Dissipation**: $D = 2\Gamma/f_r$
