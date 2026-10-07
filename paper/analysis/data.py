# -*- coding: utf-8 -*-
"""Loaders for the raw datasets of the repository (never modified)."""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
D0911 = os.path.join(ROOT, "research", "air-ipa-water-1920-2026-09-11")
D0910 = os.path.join(ROOT, "research", "air-ipa-water-1920-2026-09-10")
D0903 = os.path.join(ROOT, "research", "board-125MHz-air-2026-09-03")
OSL = os.path.join(ROOT, "research", "osl-125MHz-2026-09-03")
REF_G1 = os.path.join(ROOT, "docs", "impedance-analysis", "reference-sweep", "g1.txt")

SETS = {"air": ["air_0", "air_1", "air_2"], "water": ["wat_0", "wat_1", "wat_2"], "ipa": ["ipa_0", "ipa_1", "ipa_2"]}
PHASES = ("air", "water", "ipa")
OVERTONES = (1, 3, 5, 7, 9)


def dumps_0911():
    """The 45 sweeps of 2026-09-11: dict[(set, n)] -> (f, V_MAG, V_PHS), plus write times."""
    z = np.load(os.path.join(D0911, "data", "sweep_dumps_2026-09-11.npz"))
    out, mt = {}, {}
    for ph, sets in SETS.items():
        for s in sets:
            for n in OVERTONES:
                g = z["%s/g%d" % (s, n)]
                out[(s, n)] = (g[:, 0], g[:, 1], g[:, 2])
                mt[(s, n)] = str(z["%s/g%d/mtime" % (s, n)])
    return out, mt


def air_0903():
    return {n: tuple(np.loadtxt(os.path.join(D0903, "g%d.txt" % n)).T) for n in OVERTONES}


def reference_g1():
    return tuple(np.loadtxt(REF_G1).T)


def datalog(path):
    d = pd.read_csv(path)
    d["t"] = pd.to_datetime(d.Date + " " + d.Time)
    return d


def datalogs_0911():
    return (datalog(os.path.join(D0911, "data", "2026-09-11_12-14-42_multi.csv")),
            datalog(os.path.join(D0911, "data", "2026-09-11_12-14-42_multi_amplitude.csv")))


def datalogs_0910():
    return (datalog(os.path.join(D0910, "data", "2026-09-10_17-10-06_multi.csv")),
            datalog(os.path.join(D0910, "data", "2026-09-10_17-10-06_multi_amplitude.csv")))


def osl():
    """Open/short/50 Ω full-band sweeps (1–51 MHz), instrument units -> volts.
    Columns are (V_MAG−0.9)/0.030 and (V_PHS−0.9)/0.010 with the attenuator NOT undone."""
    out = {}
    for name in ("open", "short", "load50"):
        a = np.loadtxt(os.path.join(OSL, "cal_%s.txt" % name))
        out[name] = (a[:, 0], 0.9 + a[:, 1] * 0.030 - 0.610692, 0.9 + a[:, 2] * 0.010)
    return out


# ----------------------------------------------------------- glucose 2024-05-29
GLUC = os.path.join(ROOT, "research", "glucose-2024-05-29")
GLUC_COPY = os.path.join(ROOT, "paper", "data", "glucose-2024-05-29")     # identical copy kept with the paper
GLUC_NPZ = os.path.join(GLUC, "data", "sweep_raw_2024-05-29.npz")
if not os.path.exists(GLUC_NPZ):
    GLUC_NPZ = os.path.join(GLUC_COPY, "data", "sweep_raw_2024-05-29.npz")
GLUC_PHASES = ("air", "water", "gluc05", "gluc075", "gluc10")
GLUC_CONC = {"air": None, "water": 0.0, "gluc05": 5.0, "gluc075": 7.5, "gluc10": 10.0}   # % w/v
GLUC_REPLICAS = ("00", "01", "02")
V_ATT_OFFSET_2024 = 0.600        # the (wrong) attenuator constant of software 0.1.5, used by its g<n>.txt
V_ATT_OFFSET = 0.610692          # the correct one (constants.V_MAG_DECADE_OFFSET)


def convert_n_txt(col2, col3):
    """<n>.txt of software 0.1.5 → (V_MAG compensated, V_PHS) in volts.
    col2 = (counts·3.3/4096/2 − 0.9)/0.03 (attenuator NOT undone); col3 = (counts·3.3/4096/1.5 − 0.9)/0.01 = 90 − |Δφ|
    (software/docs/DATA_FORMAT_sweep_data.md)."""
    V_MAG = 0.9 + 0.030 * np.asarray(col2, float) - V_ATT_OFFSET
    V_PHS = 0.9 + 0.010 * np.asarray(col3, float)
    return V_MAG, V_PHS


def glucose_0529(root=None):
    """The 75 sweeps of 2024-05-29: dict[(set, n)] -> (f, V_MAG, V_PHS) with set = '<phase>_<rr>', plus mtimes.
    Reads the packed archive research/glucose-2024-05-29/data/sweep_raw_2024-05-29.npz (arrays are the <n>.txt
    as written, 18001×3) or, if `root` is given, the directory tree <root>/<phase>_<rr>/<n>.txt."""
    out, mt = {}, {}
    if root is None:
        z = np.load(GLUC_NPZ)
        for ph in GLUC_PHASES:
            for r in GLUC_REPLICAS:
                s = "%s_%s" % (ph, r)
                for n in OVERTONES:
                    a = z["%s/%d" % (s, n)]
                    vm, vp = convert_n_txt(a[:, 1], a[:, 2])
                    out[(s, n)] = (a[:, 0], vm, vp); mt[(s, n)] = str(z["%s/%d/mtime" % (s, n)])
        return out, mt
    import datetime
    for ph in GLUC_PHASES:
        for r in GLUC_REPLICAS:
            s = "%s_%s" % (ph, r)
            for n in OVERTONES:
                p = os.path.join(root, s, "%d.txt" % n)
                a = np.loadtxt(p); assert a.shape == (18001, 3), p
                vm, vp = convert_n_txt(a[:, 1], a[:, 2])
                out[(s, n)] = (a[:, 0], vm, vp)
                mt[(s, n)] = datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")
    return out, mt


def check_g_identity_2024(root, tol=1e-12):
    """The 2024 g<n>.txt are [f, V_MAG_uncompensated − 0.600, V_PHS], i.e. NOT conductances and with the wrong
    attenuator constant. Verifies  g[:,1] == (0.9 + 0.03·col2) − 0.600  and g[:,2] == V_PHS  on every sweep, and
    returns the maximum deviation. The paper excludes those files; this is why."""
    worst = 0.0
    for ph in GLUC_PHASES:
        for r in GLUC_REPLICAS:
            for n in OVERTONES:
                d = os.path.join(root, "%s_%s" % (ph, r))
                a = np.loadtxt(os.path.join(d, "%d.txt" % n)); g = np.loadtxt(os.path.join(d, "g%d.txt" % n))
                vm_u = 0.9 + 0.030 * a[:, 1]; vp = 0.9 + 0.010 * a[:, 2]
                worst = max(worst, float(np.max(np.abs(g[:, 1] - (vm_u - V_ATT_OFFSET_2024)))), float(np.max(np.abs(g[:, 2] - vp))),
                            float(np.max(np.abs(g[:, 0] - a[:, 0]))))
    return worst, worst <= tol
