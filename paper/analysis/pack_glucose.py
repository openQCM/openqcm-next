# -*- coding: utf-8 -*-
"""Pack the 75 raw <n>.txt sweeps of 2024-05-29 into one compressed archive, and back (model: load_dumps.py).

    python pack_glucose.py pack   <root>  research/glucose-2024-05-29/data/sweep_raw_2024-05-29.npz
    python pack_glucose.py unpack <npz>   <out_root>

<root>/<phase>_<rr>/<n>.txt with phase in air, water, gluc05, gluc075, gluc10; rr in 00 01 02; n in 1 3 5 7 9.
Arrays are stored exactly as read (18001×3: frequency [Hz], col2 = magnitude dB uncompensated, col3 = 90 − |Δφ|);
key '<set>/<n>', mtime as '<set>/<n>/mtime' (ISO, local time of the acquiring machine). Byte-exact round trip
with np.savetxt(fmt='%.18e') is checked after packing.
"""
import sys, os, datetime, numpy as np
import data

def pack(root, out):
    d = {}
    for ph in data.GLUC_PHASES:
        for r in data.GLUC_REPLICAS:
            s = "%s_%s" % (ph, r)
            for n in data.OVERTONES:
                p = os.path.join(root, s, "%d.txt" % n); a = np.loadtxt(p); assert a.shape == (18001, 3), p
                d["%s/%d" % (s, n)] = a
                d["%s/%d/mtime" % (s, n)] = np.array(datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds"))
    os.makedirs(os.path.dirname(out), exist_ok=True); np.savez_compressed(out, **d)
    z = np.load(out); worst = max(float(np.max(np.abs(z[k] - d[k]))) for k in d if not k.endswith("/mtime"))
    print("wrote %s, %.1f MB, %d arrays, max round-trip deviation %g" % (out, os.path.getsize(out) / 1e6, len(d), worst))

def unpack(path, root):
    z = np.load(path)
    for k in z.files:
        if k.endswith("/mtime"): continue
        s, n = k.split("/"); os.makedirs(os.path.join(root, s), exist_ok=True)
        np.savetxt(os.path.join(root, s, n + ".txt"), z[k], fmt="%.18e")
    print("unpacked into", root)

if __name__ == "__main__":
    {"pack": lambda: pack(sys.argv[2], sys.argv[3]), "unpack": lambda: unpack(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
