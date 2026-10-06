# Novelty assessment: openQCM NEXT impedance-analysis method

Reference numbers refer to `literature_review.md`; verification grades (V/I/U) as defined there. Full texts could not be retrieved in this session, so every "no prior work found" statement below means "not found by web search of titles, abstracts and indexed extracts on 2026-10-06"; it is not a database-complete claim and should be re-checked in Scopus/Web of Science before submission.

## (a) Is the phase-shifted Lorentzian new?

**No.** It is Johannsmann's standard fit function for admittance traces. Verified facts:

- Johannsmann, Langhoff and Leppin (Sensors 2021, eq. 13) give G_fit = G_max Γ [Γ cos φ + (f_res − f) sin φ]/((f_res − f)² + Γ²) + G_off, with B_fit analogous, and state that "the phase shift φ accounts for an asymmetry of the resonance curve. Imperfect calibration causes such an asymmetry" [5] (V).
- Leppin et al. (Sensors 2020) fit the same function to 32 simultaneous admittance channels at 10 ms resolution [35] (V).
- The 2024 *Nature Reviews Methods Primers* primer repeats "a suitable fit function is the phase-shifted Lorentzian" with "an additional set of three fit parameters (a phase, φ, and a complex offset)" [7] (V).
- The function is implemented in the group's QTZ impedance-analysis software; the companion QTM modelling software is free to download [5] (I).
- The 2015 Springer monograph [36] very probably describes it (I, chapter not retrieved). Whether the 1999 *Macromol. Chem. Phys.* [37] and 2004 *Langmuir* [38] papers already included the phase term could **not** be confirmed (U); the manuscript should not assert a first-use year without checking them.
- The same mathematics (Lorentzian multiplied by a complex constant, i.e. a rotated resonance circle, appearing as an asymmetric "Fano-like" line in one quadrature) is standard in microwave resonator metrology: Kajfez and Hwan 1984 [39], Petersan and Anlage 1998 [33], Khalil et al. 2012 [40], Probst et al. 2015 [41]. A reviewer from that community will expect this link to be acknowledged.

Recommendation: cite [5] as the definition, [36] and [35] as prior use, mention [33,40,41] as the equivalent treatment in the microwave literature, and state the manuscript's sign convention relative to eq. 13 (the indexed extract of [5] has "+ Δ sin φ" with Δ = f_res − f; the manuscript's "(Γ cos φ − Δ sin φ)" is the same function with φ → −φ). The manuscript's contribution concerning this function can only be its *application* to data produced by an AD8302 divider inversion, its *comparison* with argmax/half-height on the same data, and any *interpretation* of the fitted φ in terms of the specific calibration errors of the divider/AD8302 chain (residual R17 error, V_CP offset, phase-slope error). The last point is genuinely useful and, as far as could be found, has not been made for this hardware.

## (b) Have AD8302-based QCM or impedance systems been published, and did they reconstruct complex admittance?

**AD8302 impedance systems: yes.** Bioimpedance spectrometers built around the AD8302 appear from 2006 onward (Yang et al., *Physiol. Meas.* [45]; later accuracy-enhancement conference papers [46]) and a 2026 *Measurement* paper (Zompanti et al.) presents an AD8302 "polar demodulator" for impedance spectroscopy from 100 Hz to >10 MHz with 14.4 % modulus and 5.7° phase error [47] (V from abstract). These convert the dB ratio and the phase to complex Z, so **complex impedance reconstruction from AD8302 outputs is prior art in general**. None treats a resonator, and the phase-fold ambiguity is handled (where mentioned) by restricting to a known-sign regime rather than by using resonance structure (I).

**AD8302 + QCM: one peer-reviewed conference paper.** Sakti (2019, IOP Conf. Ser. 546, 042040) measured QCM gain and phase with an AD8302 and compared it with a digital oscilloscope, concluding that the AD8302 output can be processed directly by a microcontroller [49] (V from abstract). From the abstract it cannot be determined whether complex Z/Y was reconstructed, whether a divider was inverted, or whether any liquid was tested (U); the balance of evidence is that it is a scalar gain/phase feasibility study in air.

**openQCM Q-1/NEXT: vendor documentation only.** The AD9851 + AD8302 + Teensy 4.0 architecture is the published openQCM Q-1/NEXT hardware [51,52] (V) and has been reused by Horst et al. (HardwareX 2022) [53] and, probably, by Muñoz et al. (HardwareX 2023) [54] (I). The vendor describes the Q-1 as a "scalar network analyser" and the software as tracking frequency and dissipation from "the resonance curve" [51,52]. No source found describes an exact inversion of the divider to Z_q and Y = G + jB, nor a Lorentzian fit, in the Q-1/NEXT software (I; the public Q-1 repository should be checked and cited to make this statement precise). Horst et al. validated electrochemically, not against Kanazawa–Gordon [53] (V).

## (c) Have DDS + gain/phase-detector QCM systems been validated in liquid against Kanazawa–Gordon?

**Not in a peer-reviewed paper that could be found.** Liquid-phase Kanazawa–Gordon validations exist for other architectures: bench impedance analysers [8,29,30,31,14], the Siena custom QCM-D/QCM-R front ends with a reference impedance analyser [13], phase-detector fixed-frequency systems calibrated in viscosity series [15,28,32], and water–glycerol calibration of commercial EQCM [12]. For the DDS + AD8302 class, the only liquid data found are vendor web pages for openQCM (I, not peer-reviewed) and the electrochemical validations of [53]. A multi-overtone (n = 1–9) air/water/isopropanol comparison with Kanazawa–Gordon, including the n^{1/2} collapse of Δf and ΔΓ, therefore appears to be new for this hardware class.

## (d) What combination is plausibly novel?

The defensible novelty is the **complete, documented signal chain and its metrological validation**, specifically:

1. Exact analytical inversion of the R17 voltage divider from the AD8302 outputs (M = R17·10^((V_CP − V_MAG)/0.6); R_q = M cos φ − R17; X_q = −M sin φ) to obtain Z_q and Y = G + jB on a low-cost (< €1 k class) multi-overtone instrument — as opposed to treating the scalar gain curve as a conductance proxy.
2. A resolution of the AD8302 unsigned-phase fold that uses the resonance itself (the sign of X_q changes through series resonance), which has not been described for a resonator (I).
3. Application of Johannsmann's phase-shifted Lorentzian to G(f) obtained this way, with a side-by-side comparison against argmax + half-height on the same sweeps, and with the fitted φ interpreted as a diagnostic of residual calibration error of the AD8302/divider chain.
4. Validation on overtones 1–9 in air, water and isopropanol against Kanazawa–Gordon, including n^{1/2} scaling and the ΔΓ/(−Δf) ratio, with the error definitions aligned to [13] and [5].
5. Full open-source release (firmware + host), so the result is reproducible — this is what *HardwareX*/*Hardware*/*Sensors* reviewers weigh heavily.

Items 1–2 are the only *technical* elements for which no prior QCM publication was found; items 3–5 are *methodological* and *validation* contributions on known elements.

## (e) Which prior work a reviewer would cite to say "this was done"

- "Impedance QCM with G-peak and half-width is standard": Schröder et al. 2001 [26]; MicroVacuum/Gamry QCM-I [27]; Kasper et al. 2016 [29]; Burda 2022 [30,31].
- "The phase-shifted Lorentzian is Johannsmann's": [5,7,35,36]; and "rotation = background phase, see circle fit": [33,39,40,41].
- "DDS + AD8302 QCM is openQCM Q-1/NEXT, already published as open hardware and reused": [51,52,53,54]; "AD8302 + QCM was shown by Sakti": [49].
- "Complex impedance from AD8302 magnitude/phase is known": [45,47]; hobbyist AD9851 + AD8302 analyser [48].
- "Liquid validation with reference analyser and several viscosities was done better by Fort et al.": [13]; "√n scaling was shown by Yoshimoto et al.": [8].
- "Robust f/Q estimation for damped resonators with background": Niedermayer et al. [34]; Petersan and Anlage [33].

The manuscript should pre-empt each of these by citing them and stating precisely what differs (Section d).

## (f) Draft novelty statement (3–5 sentences)

"We describe and validate an impedance-analysis mode for the open-source openQCM NEXT in which the outputs of an AD8302 gain/phase detector are inverted analytically through the known series-resistor divider to recover the complex impedance of the quartz, and hence its conductance and susceptance, at every point of a DDS frequency sweep; the unsigned phase of the detector is disambiguated using the change of sign of the reactance through series resonance. Resonance frequency and half-bandwidth are then obtained both by the conventional conductance-maximum/half-height estimator and by fitting the phase-shifted Lorentzian of Johannsmann et al., whose phase parameter we use as a diagnostic of residual calibration error in the detector chain. The two estimators are compared on the same sweeps, and the instrument is validated on overtones 1–9 in air, water and isopropanol against the Kanazawa–Gordon prediction, including the n^{1/2} scaling of frequency and bandwidth shifts. To our knowledge this is the first peer-reviewed demonstration that a sub-€1 k DDS/gain-phase-detector QCM reconstructs complex admittance and yields Kanazawa–Gordon-consistent frequency and dissipation across multiple overtones; the fit function and the hardware architecture themselves are not new and are attributed to prior work."

## (g) Journal shortlist and arXiv category

| Journal | Fit rationale | Typical scope | Open access | Notes |
|---|---|---|---|---|
| **HardwareX** (Elsevier) | Open-source instrument with validation; expects BOM, build instructions, repository; the two closest prior openQCM-derived papers [53,54] are here | Open hardware for science | Full OA (APC, often waived/discounted) | Reviewers will want the repository, BOM, and validation data; novelty bar is "useful, reproducible, validated" rather than "first" |
| **Sensors** (MDPI) | Home of [5,13,23,30,31,35]; QCM instrumentation and metrology regularly published | Sensors, instrumentation, signal processing | Full OA (APC) | Fast; reviewers likely from the Johannsmann/Arnau/Siena circles — cite them carefully |
| **Measurement** (Elsevier) | Metrological framing (estimator bias, validation against theory, uncertainty) fits; AD8302 impedance work [47] appears here | Measurement science and instrumentation | Hybrid | Emphasise uncertainty budget and estimator comparison |
| **Review of Scientific Instruments** (AIP) | Classical venue for QCM electronics [21,26,32] and resonator fitting [41] | Instruments and methods | Hybrid | Expects a complete instrument description; good for the divider inversion + phase disambiguation + fit comparison |
| **IEEE Transactions on Instrumentation and Measurement** | Estimator comparison, calibration, uncertainty; electronics detail welcome | Instrumentation, measurement, signal processing | Hybrid | Higher bar on metrological rigor; long review cycle |
| **Measurement Science and Technology** (IOP) | Resonator parameter estimation under damping published here [34] | Measurement science | Hybrid | Good fit if the paper leans on estimator bias analysis |
| **Sensors and Actuators A: Physical** (Elsevier) | Rodríguez-Pardo group's QCM electronics [14,15] | Physical sensors and actuators | Hybrid | Expects sensor-performance characterisation (resolution, drift, noise) |
| **IEEE Sensors Journal** | Low-cost sensor systems with validation | Sensor systems | Hybrid | Alternative to Sensors (MDPI) with IEEE formatting |
| *Analytical Chemistry* (ACS) | Only warranted if a chemical/biological application result is included; pure instrumentation without an analytical demonstration is usually redirected | Analytical methods | Hybrid | Not recommended for the present scope |

**arXiv category:** primary `physics.ins-det` (Instrumentation and Detectors); cross-list `eess.SP` (Signal Processing) for the estimator/fit comparison and, optionally, `physics.app-ph` (Applied Physics). The two 2026 impedance-QCM preprints found [61] were posted under arXiv (category not verified) and Preprints.org, so an arXiv preprint is consistent with current practice in this niche.
