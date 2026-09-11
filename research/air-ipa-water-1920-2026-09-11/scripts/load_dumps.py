"""The nine sweep dumps of 2026-09-11 as one compressed archive, and back.

    python load_dumps.py pack   <dump_root> data/sweep_dumps_2026-09-11.npz     # done once, 2026-09-11
    python load_dumps.py unpack data/sweep_dumps_2026-09-11.npz <out_root>      # recreates <out_root>/<set>/g<n>.txt

Sets: air_0 air_1 air_2 wat_0 wat_1 wat_2 ipa_0 ipa_1 ipa_2; overtones 1 3 5 7 9. Each array is the
g<n>.txt as written by the process: 18001 x 3, frequency [Hz] at 1 Hz step, V_MAG [V] with the INPB
attenuator already undone, V_PHS [V]. Key "<set>/g<n>"; "<set>/g<n>/mtime" is the file's write time
(ISO, local), i.e. when that sweep was dumped. The uncompensated <n>.txt of the same sweep is
    col2 = ((V_MAG + 0.610692) - 0.9) / 0.030      # dB, attenuator NOT undone
    col3 = (V_PHS - 0.9) / 0.010                   # degrees, = 90 - |dphi|
(software/docs/DATA_FORMAT_sweep_data.md, verified to 0.00e+00 on a real pair).

    from load_dumps import load
    d = load("data/sweep_dumps_2026-09-11.npz"); f, V_MAG, V_PHS = d["wat_1/g3"].T
"""
import sys, os, datetime, numpy as np
SETS = ["air_0", "air_1", "air_2", "wat_0", "wat_1", "wat_2", "ipa_0", "ipa_1", "ipa_2"]; N = (1, 3, 5, 7, 9)

def load(path):
    z = np.load(path); return {k: z[k] for k in z.files}

def pack(root, out):
    d = {}
    for s in SETS:
        for n in N:
            p = os.path.join(root, s, "g%d.txt" % n); g = np.loadtxt(p); assert g.shape == (18001, 3), p
            d["%s/g%d" % (s, n)] = g
            d["%s/g%d/mtime" % (s, n)] = np.array(datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds"))
    np.savez_compressed(out, **d); print("wrote %s, %.1f MB, %d arrays" % (out, os.path.getsize(out) / 1e6, len(d)))

def unpack(path, root):
    d = load(path)
    for k, v in d.items():
        if k.endswith("/mtime"): continue
        s, g = k.split("/"); os.makedirs(os.path.join(root, s), exist_ok=True)
        np.savetxt(os.path.join(root, s, g + ".txt"), v, fmt="%.18e")
    print("unpacked into", root)

if __name__ == "__main__":
    {"pack": lambda: pack(sys.argv[2], sys.argv[3]), "unpack": lambda: unpack(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
