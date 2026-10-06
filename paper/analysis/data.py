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
