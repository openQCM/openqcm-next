# Exact Conductance Calculation for QCM Impedance Analysis

> ## ⚠️ VALIDATION STATUS — NOT YET VALIDATED (2026-07-21)
>
> This document is the **source of truth used to implement the "exact" formula**
> in `sweep_data/plot_conductance.py` (`_RX_exact` / `_G_exact` / `_B_exact`), but
> **the formula itself and its assumptions are not yet validated against the real
> hardware.**
>
> **What HAS been checked:** a synthetic Butterworth–Van Dyke resonance was fed
> through the *assumed* forward model (divider `H = R17/(Z_q+R17)` + the nominal
> AD8302 equations below) and then inverted with `_RX_exact`. It recovered `Z_q`
> essentially perfectly (G_max error ~0.002 %, vs ~87 % for the approximate
> formula). This proves only that **the algebra/code correctly inverts the assumed
> model** — it is a self-consistency check, **not** an independent validation.
>
> **What is STILL unvalidated:**
> - the circuit model & constants — `R17 = 52.3 Ω`, AD8302 slopes `30 mV/dB` and
>   `10 mV/deg`, `V_CP = 0.9 V`, and the divider topology — vs the actual board;
> - the AD8302 behaviour near **phase ≈ 0°** (nonlinear + sign-folded output), and
>   the **phase-unfold heuristic** (flip at the phase minimum) used to recover the
>   signed phase;
> - unmodelled parasitics (board strays, connector, static branch beyond C0).
>
> **To validate (TODO):** measure **known reference impedances / RLC standards**
> with the board and compare the recovered `R_q, X_q` (and `f_s, R_m, Q`) against a
> calibrated impedance/network analyzer; from that, confirm or recalibrate the
> slopes / `R17` / `V_CP`.
>
> **Consequence:** until validated, the live measurement pipeline
> (`processors/Multiscan.py::parameters_finder_impedance`) intentionally still uses
> the **approximate** formula. The exact formula lives only in the offline
> `plot_conductance.py` (G DATA VIEW) for inspection. **If/when validated, porting
> it to the live pipeline will change the logged frequency/dissipation values.**

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
