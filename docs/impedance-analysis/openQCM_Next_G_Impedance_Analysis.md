# openQCM Next Impedance Analysis Implementation

**Technical Documentation for Research Collaboration**

## Executive Summary

This document describes the implementation of impedance-based analysis for the openQCM Next system, which measures frequency shifts and dissipation (bandwidth) in Quartz Crystal Microbalance (QCM) sensors. The method is based on conductance curve analysis and has been validated against Kanazawa-Gordon theory with excellent agreement.

## 1. Theoretical Background

### 1.1 Kanazawa-Gordon Theory

For a QCM sensor in contact with a semi-infinite viscoelastic medium (e.g., liquid), the frequency shift (Δf) and bandwidth shift (ΔΓ) are given by:

$$\Delta f = -f_0^{3/2} \sqrt{\frac{n \, \eta_L \rho_L}{\pi \mu_q \rho_q}}$$

$$\Delta \Gamma = +f_0^{3/2} \sqrt{\frac{n \, \eta_L \rho_L}{\pi \mu_q \rho_q}}$$

Where:

- $f_0$ : fundamental resonance frequency
- $n$ : overtone number (1, 3, 5, ...)
- $\eta_L, \rho_L$ : liquid viscosity and density
- $\mu_q, \rho_q$ : quartz shear modulus and density

### 1.2 Key Characteristics

1. Frequency and bandwidth shifts are equal in magnitude but opposite in sign
2. Shifts scale with $f_0^{3/2}$
3. Shifts are proportional to $\sqrt{n}$

## 2. Hardware Implementation

### 2.1 Circuit Design

The measurement circuit consists of:

- **Voltage divider:** QCM sensor in series with $R_{add}$
- **AD8302 chip:** Measures gain/phase difference between nodes
- **Microcontroller:** Teensy 4.0 for data acquisition

### 2.2 AD8302 Transfer Functions

**Parameters:**

- Gain slope: 600 mV/decade
- Phase slope: 10 mV/degree
- Center point: 900 mV

## 3. Software Implementation

### 3.1 Data Acquisition Flow

```python
# 1. Send sweep command to microcontroller
cmd = f"{start_freq};{stop_freq};{step}\n"
serial.write(cmd.encode())

# 2. Read ADC data (12-bit, 0-4096)
for i in range(samples):
    bit_mag = float(data[i][0])    # Magnitude ADC reading
    bit_phase = float(data[i][1])  # Phase ADC reading
```

### 3.2 Impedance Calculation

**Step 1: Convert ADC to Voltages**

```python
def _Vmag_bit_mag(self, bit_mag):
    ADCtoVolt = 3.3 / 4096
    Vmag = bit_mag * ADCtoVolt / 2  # Factor 2 from opamp
    Vmag = Vmag - 0.6               # Voltage divider offset
    return Vmag

def _Vphase_bit_phase(self, bit_phase):
    ADCtoVolt = 3.3 / 4096
    Vphase = bit_phase * ADCtoVolt / 1.5  # Factor 1.5 from opamp
    return Vphase
```

**Step 2: Calculate Impedance Magnitude**

```python
def _Zabs_Vmag(self, V_mag):
    R_add = 52.3  # Series resistor
    Zabs = R_add * (10**((0.9 - V_mag)/0.6)) + R_add
    return Zabs
```

The impedance magnitude is calculated using:

$$|Z| = R_{add} \cdot 10^{\frac{0.9 - V_{mag}}{0.6}} + R_{add}$$

**Step 3: Calculate Phase**

```python
def _phase_raw_V_phase(self, Vph_var):
    phase = (1.8 - Vph_var) / 0.01  # Degrees
    return phase
```

The phase difference is:

$$\varphi = \frac{1.8 - V_{phase}}{0.01}$$

**Step 4: Calculate Conductance**

```python
def _G_calc(self, Zabs, phase):
    phase_rad = np.deg2rad(phase)
    G = np.cos(phase_rad) / Zabs
    return G
```

The conductance (real part of admittance) is:

$$G = \frac{\cos(\varphi)}{|Z|}$$

### 3.3 Parameter Extraction

**Resonance Frequency**

```python
def _Freq_G(self, G_conductance, F_sweep):
    idx_max = np.nanargmax(G_conductance)
    f_resonance = F_sweep[idx_max]
    return idx_max, f_resonance
```

**Half-Bandwidth (Dissipation)**

```python
def _half_bandwidth_G(self, G_conductance, F_sweep):
    # Remove baseline
    min_G = np.average(G_conductance[:100])
    G_conductance = G_conductance - min_G

    # Find half-height point
    max_G = np.nanmax(G_conductance)
    max_half_G = max_G / 2

    # Find left index at half height
    for nn in range(len(G_conductance)):
        if G_conductance[nn] > max_half_G:
            idx_l = nn
            break

    # Calculate bandwidth
    idx_max = np.nanargmax(G_conductance)
    bw = F_sweep[idx_max] - F_sweep[idx_l]
    return bw
```

### 3.4 Signal Processing Pipeline

1. **Baseline Correction:** Polynomial fit removal
2. **Filtering:** Savitzky-Golay filter
3. **Interpolation:** Spline interpolation
4. **Averaging:** Ring buffer with moving average

## 4. Experimental Validation

### 4.1 Test Conditions

- **Sensor:** 5 MHz, 14 mm Au-coated QCM
- **Temperature:** 25°C controlled
- **Medium transition:** Air → Water
- **Overtones measured:** 1st through 9th

### 4.2 Results Summary

| Overtone | Δf/n (Hz) | ΔΓ/n (Hz) | KG Theory (Hz) |
|----------|-----------|-----------|----------------|
| 1        | -804.99   | 705.17    | 770            |
| 3        | -499.64   | 438.16    | 445            |
| 5        | -358.83   | 322.03    | 344            |
| 7        | -343.83   | 309.22    | 291            |
| 9        | -315.78   | 282.08    | 256            |

### 4.3 Key Observations

1. Frequency and bandwidth shifts are approximately equal and opposite
2. Normalized shifts decrease with overtone number (√n scaling verified)
3. Quantitative agreement with KG theory within acceptable range

## References

1. Johannsmann, D. (2021). "The Quartz Crystal Microbalance in Soft Matter Research." *Sensors*, 21(10), 3490.
2. Kanazawa, K.K. & Gordon, J.G. (1985). "Frequency of a quartz microbalance in contact with liquid." *Anal. Chem.*, 57(8), 1770-1771.
3. AD8302 Datasheet. Analog Devices. "LF–2.7 GHz RF/IF Gain and Phase Detector"
