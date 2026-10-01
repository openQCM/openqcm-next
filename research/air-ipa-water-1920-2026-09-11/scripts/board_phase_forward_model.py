"""Table 7 — a board phase phi_b inside the absolute value of the phase reading, fitted with a forward model to
both detector channels, on the 45 sweeps of 2026-09-11.

    cd software && PYTHONPATH=. python ../research/air-ipa-water-1920-2026-09-11/scripts/board_phase_forward_model.py

Forward model (the July script that first did this was never versioned; this one is written from the model HANDOFF
states). Crystal: BVD, Z_q = 1 / (j w C0 + 1/(R1 + j w L1 + 1/(j w C1))). Divider, as fit_admittance.RX inverts it:
W = Z_q + R17 = M exp(-j phi), so M = |W| and phi = -arg W. The two channels the detector reports:
    V_MAG = V_CP - 0.6 log10(M / R17)            (stored V_MAG, attenuator already undone)
    r     = |phi + phi_b| - delta                 (reading in degrees, fit_admittance.folded_phase(V_PHS))
Two models on the same samples: A with phi_b = 0 (delta free), B with phi_b free. Both channels in volts at the
detector (30 mV/dB is already in V_MAG; the phase residual is degrees x 10 mV/deg), raw samples over +-3 half widths
of the fold-rule seed, BVD seeds from FIT 1. Where the phase never crosses -phi_b, |.| is a sign and phi_b and delta
enter only as a difference: the fit reports their correlation, and |rho| > 0.99 is marked not identifiable.
"""
import numpy as np
from scipy.optimize import least_squares
from offline_fits_lib import sweeps, analyse_arrays, window, fa, rng, write, PHASES, N

R17, V_CP = fa.R17, fa.V_CP


def model(p, f, free_phib):
    R1, L1, dfs, C0pF, delta = p[:5]
    phib = p[5] if free_phib else 0.0
    fs = p_fs0 + dfs; w = 2 * np.pi * f
    C1 = 1.0 / ((2 * np.pi * fs) ** 2 * L1)
    Zm = R1 + 1j * w * L1 + 1.0 / (1j * w * C1)
    Zq = 1.0 / (1j * w * C0pF * 1e-12 + 1.0 / Zm)
    W = Zq + R17
    vmag = V_CP - 0.6 * np.log10(np.abs(W) / R17)
    phi = -np.degrees(np.angle(W))
    r = np.abs(phi + phib) - delta
    return vmag, r


def fit(f, Vm, r_meas, p0, free_phib):
    def res(p):
        vm, rr = model(p, f, free_phib)
        return np.concatenate([vm - Vm, 0.010 * (rr - r_meas)])
    lo = [1e-3, 1e-6, -2000.0, -200.0, -45.0] + ([-90.0] if free_phib else [])
    hi = [1e6, 10.0, 2000.0, 200.0, 45.0] + ([90.0] if free_phib else [])
    sol = least_squares(res, p0, bounds=(lo, hi), x_scale="jac", xtol=1e-12, ftol=1e-12, max_nfev=20000)
    d = sol.fun; n = len(f)
    J = sol.jac; s2 = float(d @ d) / max(len(d) - len(p0), 1)
    try:
        cov = s2 * np.linalg.inv(J.T @ J)
    except np.linalg.LinAlgError:
        cov = np.full((len(p0), len(p0)), np.nan)
    rho = cov[4, 5] / np.sqrt(cov[4, 4] * cov[5, 5]) if free_phib and cov[4, 4] > 0 and cov[5, 5] > 0 else np.nan
    return sol.x, 1e3 * np.sqrt(np.mean(d[:n] ** 2)), 1e3 * np.sqrt(np.mean(d[n:] ** 2)), rho


res = {}
for phase, s, n, f, Vm, Vp, _ in sweeps():
    a = analyse_arrays(f, Vm, Vp)
    sel = window(f, a["fs_seed"], a["hw_seed"])
    fk, Vk, rk = f[sel], Vm[sel], fa.folded_phase(Vp)[sel]
    c = a["fit1"]; p_fs0 = c["fs"]
    pA = [c["R1"], c["L1"], 0.0, c["C0"] * 1e12 if np.isfinite(c["C0"]) else 5.0, a["delta"]]
    xA, mA, rA, _ = fit(fk, Vk, rk, pA, False)
    best = None
    for phib0 in (-20.0, -10.0, 0.0, 10.0, 20.0):         # phi_b is a sign-sensitive parameter: try both sides
        xB, mB, rB, rho = fit(fk, Vk, rk, list(xA) + [phib0], True)
        cost = mB ** 2 + rB ** 2
        if best is None or cost < best[0]:
            best = (cost, xB, mB, rB, rho)
    _, xB, mB, rB, rho = best
    res[(phase, s, n)] = dict(phib=xB[5], dB_=xB[4], dA=xA[4], mA=mA, rA=rA, mB=mB, rB=rB, rho=rho,
                              ident=bool(np.isfinite(rho) and abs(rho) <= 0.99))

L = ["## Table 7 — board phase φ_b from the forward model, range over the three replicas", "",
     "| phase | n | φ_b [°] | δ, model B [°] | δ, model A (φ_b = 0) [°] | rms V_MAG A → B [mV] | rms V_PHS A → B [mV] | ρ(φ_b, δ) | identifiable |",
     "|---|---|---|---|---|---|---|---|---|"]
for phase, sets in PHASES:
    for n in N:
        g = lambda k: [res[(phase, s, n)][k] for s in sets]
        idf = g("ident"); tag = "yes" if all(idf) else ("no" if not any(idf) else "%d/3" % sum(idf))
        L.append("| %s | %d | %s | %s | %s | %s → %s | %s → %s | %s | %s |" % (
            phase, n, rng(g("phib"), "%+.1f"), rng(g("dB_"), "%+.1f"), rng(g("dA"), "%+.1f"), rng(g("mA"), "%.2f"), rng(g("mB"), "%.2f"),
            rng(g("rA"), "%.2f"), rng(g("rB"), "%.2f"), rng(g("rho"), "%+.3f"), tag))
L += ["", "Replicas within a phase are 4–25 minutes apart (dump write times: air 12:25, 12:46, 12:50; water 12:57, 13:08, 13:15;",
      "isopropanol 13:20, 13:24, 13:30)."]
write("table7_board_phase.md", "\n".join(L))
