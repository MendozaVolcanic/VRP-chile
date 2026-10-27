# -*- coding: utf-8 -*-
"""Verificador S164: (1) estados del censo donde el port NO dio record (lo que la via devolveria None) y si K publico
ahi; (2) la alerta de PCC 2026-03-16 03:10 (id 3933): donde cae respecto de las celdas con dato."""
import glob, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
CENSO = Path("D:/vrp-trabajo/temporales/s162_modd/censo")
est, pubk_sin_port, ejemplos = Counter(), Counter(), []
g3933 = None
for f in glob.glob(str(CENSO / "run_*" / "*" / "ab_*.jsonl")):
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") != "record":
            continue
        e = r.get("estado"); pe = r.get("port_estado"); pg = r.get("port_grilla")
        est[(e, pe, pg)] += 1
        if e == "ok" and pe != "ok":
            k = (r.get("pub") or {}).get("K")
            pubk_sin_port[(pe, k)] += 1
            if k == 1 and len(ejemplos) < 10:
                ejemplos.append((r["vol"], r["dt"], pe, r.get("port_dist_min_km"), (r.get("brazos") or {}).get("K")))
        if r.get("id") == 3933:
            g3933 = (r, Path(f).parent / "grilla_3933.npz")
print("estados (estado, port_estado, port_grilla):")
for k, v in est.most_common():
    print("  ", k, v)
print("\nport sin record (ok pero port_estado != ok), por (port_estado, pub K):")
for k, v in pubk_sin_port.most_common():
    print("  ", k, v)
print("ejemplos con K publicando donde el port no dio record:", *ejemplos, sep="\n   ")
r, gp = g3933
z = np.load(gp); mir = z["mir"]
q = r["port"]["fisica"]["pixeles"][0]
f0, c0 = q[0], q[1]
print(f"\nPCC id 3933 {r['dt']}: alerta en fila {f0} col {c0} zona BOX {q[2]}; celdas NaN en la grilla: {int(np.isnan(mir).sum())} de {mir.size}; port_grilla={r.get('port_grilla')}")
print("vecindario 9 x 9 de MIR (NaN = sin dato):")
sub = mir[max(f0-4,0):f0+5, max(c0-4,0):c0+5]
for fila in sub:
    print("   " + " ".join("  nan " if np.isnan(v) else f"{v:6.3f}" for v in fila))
print("K en esa pasada:", (r.get("brazos") or {}).get("K"), "pub K:", (r.get("pub") or {}).get("K"), "lab:", r.get("lab"), "vrp_mirova:", r.get("vrp_mirova"))
