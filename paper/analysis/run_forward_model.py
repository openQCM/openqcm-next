# -*- coding: utf-8 -*-
"""
run_forward_model.py — synthetic sweeps with a known truth, sent through a
model of the front end and then through the SAME chain and estimators as the
measured data. The question is whether each estimator recovers f_s and Γ when
the instrument has (a) a board/cable phase φ_b entering the AD8302 phase
reading, (b) a phase-channel offset δ and the magnitude fold, (c) a scale error
on the magnitude channel, (d) the firmware carry-over. The truth is a
Butterworth–Van Dyke resonator; nothing in the fit models knows about it.

Model of the measurement (ALGORITHM.md §1–§5, AD8302 data sheet):
  Y_q = 1/(R1 + jωL1 + 1/(jωC1)) + jωC0,   f_s = 1/(2π√(L1C1)),  Γ = R1/(4πL1)
  H = R17/(Z_q + R17)
  reading r = |∠H + φ_b| − δ    (φ_b inside the modulus, δ outside)
  V_PHS = 1.8 − 0.010 r ;  V_MAG = 0.9 + 0.6 log10|H| · k_mag   (k_mag = 1 ideal)
  quantised on the ADC (3.3/4096 V, op-amp gains 2 and 1.5), 500-sample mean,
  optional carry-over v_i = m_i + v_{i-1}/500, Gaussian noise on the counts.
"""
import os, json
import numpy as np, pandas as pd
import qcmchain as q

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "results")
rng = np.random.default_rng(7)


def bvd(f, fs, gamma, R1, C0):
    w = 2 * np.pi * f
    L1 = R1 / (4 * np.pi * gamma)
    C1 = 1.0 / ((2 * np.pi * fs) ** 2 * L1)
    return 1.0 / (R1 + 1j * w * L1 + 1.0 / (1j * w * C1)) + 1j * w * C0


def synth(fs, gamma, R1, C0=5e-12, phi_b=0.0, delta=0.0, k_mag=1.0, noise_counts=0.3, carry=False, mag_rot=False):
    f = np.arange(fs - 12000.0, fs + 6001.0, 1.0)
    Y = bvd(f, fs, gamma, R1, C0)
    Z = 1.0 / Y
    H = q.R17 / (Z + q.R17)
    ang = np.degrees(np.angle(H)) + phi_b                       # board phase enters the measured phase
    r = np.abs(ang) - delta
    V_PHS = q.V_PHS_ZERO - q.PHS_SLOPE * r
    V_MAG = q.V_CP + q.DECADE * np.log10(np.abs(H)) * k_mag
    # ADC: counts = V/(LSB/gain); noise on the 500-sample mean; carry-over
    cm = (V_MAG + q.V_ATT_OFFSET) / (q.ADC_LSB / q.GAIN_MAG) + rng.normal(0, noise_counts, f.size)
    cp = V_PHS / (q.ADC_LSB / q.GAIN_PHS) + rng.normal(0, noise_counts, f.size)
    if carry:
        for v in (cm, cp):
            for i in range(1, len(v)):
                v[i] = v[i] + v[i - 1] / q.AVERAGE_SAMPLE
    cm = np.round(cm, 2); cp = np.round(cp, 2)                  # the firmware prints two decimals
    return f, cm * q.ADC_LSB / q.GAIN_MAG - q.V_ATT_OFFSET, cp * q.ADC_LSB / q.GAIN_PHS


def estimate(f, vm, vp, firmware_fix=False):
    c = q.chain(f, vm, vp, firmware_fix=firmware_fix)
    e = q.argmax_halfheight(c["f"], c["G"])
    p = q.fit_psl(c["f"], c["G"], e["f_max"], e["gamma_hh"])
    s = q.fit_symmetric(c["f"], c["G"], e["f_max"], e["gamma_hh"], linear=True)
    m = q.magnitude_estimator(c["f"], c["V_MAG"])
    return c, e, p, s, m


CASES = [
    # name, fs, gamma, R1, C0, phi_b, delta
    ("air n=1 like",   5004600.0,   65.0,   36.0, 5e-12),
    ("air n=5 like",  24973700.0,  103.0,   95.0, 5e-12),
    ("air n=9 like",  44943150.0,  190.0,  204.0, 5e-12),
    ("water n=1 like", 5003900.0,  935.0,  625.0, 5e-12),
    ("water n=5 like",24972100.0, 1646.0, 1175.0, 5e-12),
    ("water n=9 like",44941170.0, 2135.0, 1125.0, 5e-12),
    ("ipa n=9 like",  44940480.0, 2920.0, 1245.0, 5e-12),
]


def main():
    L = ["# Forward model: known truth through the front end and the chain\n",
         "Truth: BVD resonator (f_s, Γ, R1, C0 = 5 pF); divider R17 = 52.3 Ω; AD8302 laws; board phase φ_b added to ∠H before the modulus; offset δ; ADC quantisation, 0.3 counts rms noise. Estimators as in the paper. Errors are estimate − truth.\n"]
    rows = []
    # A. board phase: does the PSL recover the truth, and is φ_fit = φ_b ?
    L.append("## A. A board phase φ_b on the measured transfer function (δ = 0, ideal magnitude)\n")
    L.append("| case | R1/R17 | φ_b [°] | fold | f_Gmax − f_s [Hz] | Γ_hh − Γ [Hz] | f_sym+lin − f_s [Hz] | f_psl − f_s [Hz] | Γ_psl − Γ [Hz] | φ_fit [°] | rms_psl [%] | f_mag − f_s [Hz] |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, fs, gam, R1, C0 in CASES:
        for phi_b in (0.0, -8.0, -15.0, -25.0):
            f, vm, vp = synth(fs, gam, R1, C0, phi_b=phi_b)
            c, e, p, s, m = estimate(f, vm, vp)
            rows.append(dict(block="A", case=name, R1=R1, ratio=R1 / q.R17, phi_b=phi_b, delta=0.0, k_mag=1.0, fold=c["fold"], fs=fs, gamma=gam,
                             err_argmax=e["f_max"] - fs, err_ghh=e["gamma_hh"] - gam, err_sym=s["fres"] - fs, err_psl=p["fres"] - fs, err_gpsl=p["gamma"] - gam, phi_fit=p["phi_deg"], rms=p["rms_rel"], err_mag=m["f_max"] - fs))
            L.append("| %s | %.1f | %+.0f | %s | %+.0f | %+.1f | %+.0f | %+.1f | %+.1f | %+.1f | %.2f | %+.0f |" % (
                name, R1 / q.R17, phi_b, c["fold"], e["f_max"] - fs, e["gamma_hh"] - gam, s["fres"] - fs, p["fres"] - fs, p["gamma"] - gam, p["phi_deg"], 100 * p["rms_rel"], m["f_max"] - fs))
    # B. offset delta with fold (air-like) and a wrong fold decision
    L.append("\n## B. Phase-channel offset δ (air-like cases fold; δ is measured from the fold and removed)\n")
    L.append("| case | φ_b | δ [°] | fold found | δ found [°] | f_psl − f_s [Hz] | Γ_psl − Γ [Hz] | φ_fit | f_Gmax − f_s | Γ_hh − Γ |\n|---|---|---|---|---|---|---|---|---|---|")
    for name, fs, gam, R1, C0 in CASES[:3] + CASES[3:4]:
        for delta in (-3.0, 0.0, 4.0, 7.0):
            f, vm, vp = synth(fs, gam, R1, C0, phi_b=-20.0, delta=delta)
            c, e, p, s, m = estimate(f, vm, vp)
            rows.append(dict(block="B", case=name, R1=R1, ratio=R1 / q.R17, phi_b=-20.0, delta=delta, k_mag=1.0, fold=c["fold"], fs=fs, gamma=gam, delta_found=c["delta"],
                             err_argmax=e["f_max"] - fs, err_ghh=e["gamma_hh"] - gam, err_sym=s["fres"] - fs, err_psl=p["fres"] - fs, err_gpsl=p["gamma"] - gam, phi_fit=p["phi_deg"], rms=p["rms_rel"], err_mag=m["f_max"] - fs))
            L.append("| %s | −20 | %+.0f | %s | %+.2f | %+.1f | %+.1f | %+.1f | %+.0f | %+.1f |" % (name, delta, c["fold"], c["delta"], p["fres"] - fs, p["gamma"] - gam, p["phi_deg"], e["f_max"] - fs, e["gamma_hh"] - gam))
    # C. a liquid case where delta is NOT removable (no fold): what does an uncorrected delta do?
    L.append("\n## C. Damped load, no fold: an offset δ that cannot be measured stays in the phase\n")
    L.append("| case | φ_b | δ [°] | fold | f_Gmax − f_s | Γ_hh − Γ | f_psl − f_s | Γ_psl − Γ | φ_fit |\n|---|---|---|---|---|---|---|---|---|")
    for name, fs, gam, R1, C0 in CASES[4:7]:
        for delta in (-5.0, 0.0, 5.0):
            f, vm, vp = synth(fs, gam, R1, C0, phi_b=-20.0, delta=delta)
            c, e, p, s, m = estimate(f, vm, vp)
            rows.append(dict(block="C", case=name, R1=R1, ratio=R1 / q.R17, phi_b=-20.0, delta=delta, k_mag=1.0, fold=c["fold"], fs=fs, gamma=gam,
                             err_argmax=e["f_max"] - fs, err_ghh=e["gamma_hh"] - gam, err_sym=s["fres"] - fs, err_psl=p["fres"] - fs, err_gpsl=p["gamma"] - gam, phi_fit=p["phi_deg"], rms=p["rms_rel"], err_mag=m["f_max"] - fs))
            L.append("| %s | −20 | %+.0f | %s | %+.0f | %+.1f | %+.1f | %+.1f | %+.1f |" % (name, delta, c["fold"], e["f_max"] - fs, e["gamma_hh"] - gam, p["fres"] - fs, p["gamma"] - gam, p["phi_deg"]))
    # D. magnitude scale error (M low by 8-14 % as the OSL standards suggest) and the firmware carry
    L.append("\n## D. Magnitude-channel scale error (k_mag ≠ 1 ⇒ M off by a factor) and the firmware carry-over\n")
    L.append("| case | k_mag | M error at f_s [%] | carry | f_Gmax − f_s | Γ_hh − Γ | f_psl − f_s | Γ_psl − Γ | φ_fit | R_m,est/R1 |\n|---|---|---|---|---|---|---|---|---|---|")
    for name, fs, gam, R1, C0 in (CASES[0], CASES[2], CASES[4], CASES[6]):
        for k_mag, carry in ((1.0, False), (1.05, False), (0.95, False), (1.0, True)):
            f, vm, vp = synth(fs, gam, R1, C0, phi_b=-20.0, k_mag=k_mag, carry=carry)
            c, e, p, s, m = estimate(f, vm, vp)
            Hs = np.abs(q.R17 / (1.0 / bvd(np.array([fs]), fs, gam, R1, C0) + q.R17))[0]
            Merr = 100 * (Hs ** (1 - k_mag) - 1)   # M_est/M = |H|^{1-k}
            Rm_est = 1.0 / (e["g_peak"] + e["baseline"])
            rows.append(dict(block="D", case=name, R1=R1, ratio=R1 / q.R17, phi_b=-20.0, delta=0.0, k_mag=k_mag, carry=carry, fold=c["fold"], fs=fs, gamma=gam,
                             err_argmax=e["f_max"] - fs, err_ghh=e["gamma_hh"] - gam, err_sym=s["fres"] - fs, err_psl=p["fres"] - fs, err_gpsl=p["gamma"] - gam, phi_fit=p["phi_deg"], rms=p["rms_rel"], err_mag=m["f_max"] - fs, Rm_ratio=Rm_est / R1))
            L.append("| %s | %.2f | %+.1f | %s | %+.0f | %+.1f | %+.1f | %+.1f | %+.1f | %.3f |" % (name, k_mag, Merr, carry, e["f_max"] - fs, e["gamma_hh"] - gam, p["fres"] - fs, p["gamma"] - gam, p["phi_deg"], Rm_est / R1))
    # E. where does the rotation go when the board phase acts on H? scan R1/R17 at fixed phi_b
    L.append("\n## E. φ_fit against R1/R17 for a fixed board phase φ_b = −20° (f_s = 25 MHz, Γ = 1000 Hz)\n")
    L.append("| R1 [Ω] | R1/R17 | fold | f_psl − f_s [Hz] | Γ_psl − Γ [Hz] | φ_fit [°] | rms_psl [%] | f_Gmax − f_s [Hz] | predicted Γ tan(φ_fit/2) |\n|---|---|---|---|---|---|---|---|---|")
    for R1 in (10, 25, 52.3, 100, 200, 400, 800, 1600, 3200):
        f, vm, vp = synth(25e6, 1000.0, float(R1), 5e-12, phi_b=-20.0)
        c, e, p, s, m = estimate(f, vm, vp)
        rows.append(dict(block="E", case="scan", R1=R1, ratio=R1 / q.R17, phi_b=-20.0, delta=0.0, k_mag=1.0, fold=c["fold"], fs=25e6, gamma=1000.0,
                         err_argmax=e["f_max"] - 25e6, err_ghh=e["gamma_hh"] - 1000, err_sym=s["fres"] - 25e6, err_psl=p["fres"] - 25e6, err_gpsl=p["gamma"] - 1000, phi_fit=p["phi_deg"], rms=p["rms_rel"], err_mag=m["f_max"] - 25e6))
        L.append("| %.1f | %.2f | %s | %+.1f | %+.1f | %+.1f | %.2f | %+.0f | %+.0f |" % (R1, R1 / q.R17, c["fold"], p["fres"] - 25e6, p["gamma"] - 1000, p["phi_deg"], 100 * p["rms_rel"], e["f_max"] - 25e6, q.argmax_bias(p["gamma"], p["phi_deg"])))
    pd.DataFrame(rows).to_csv(os.path.join(R, "forward_model.csv"), index=False)
    open(os.path.join(R, "forward_model.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
