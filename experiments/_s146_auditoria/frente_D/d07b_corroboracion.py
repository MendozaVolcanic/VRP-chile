# -*- coding: utf-8 -*-
"""d07b: el '1,5 % corroborado por MIROVA' del cierre S126 de la divergencia D13 parea (fecha, MISMO sensor). El 95 % de lo
apagado es MODIS y MIROVA casi no alerta en MODIS. Aca: el mismo pareo, mas el pareo por NOCHE de volcan con cualquier
sensor, y el NULO: la misma tasa entre los records que la cerca SI deja pasar (summit), por sensor.
Instrumento: (1) control: pareo mismo-sensor debe dar ~41/2.694. (2) el nulo sobre 'summit' dice cuanto vale 1,5 %: sin el no se interpreta."""
import io, sys, json
from collections import defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
W = ("2026-05-01", "2026-08-28"); mir, _ = cargar_mirova(W); D = cargar()
T = defaultdict(lambda: defaultdict(int))
for v in VOLS:
    ks = set(mir.get(v) or {}); fechas = {d for d, b in ks}
    for r in D[v]:
        f = r["datetime_utc"][:10]
        if not (W[0] <= f <= W[1]) or pcv(r) <= 0: continue
        b = bucket(r["sensor"]); g = "apagado" if r.get("distance_class") != "summit" else "publicado"
        for kk in ((g, b), (g, "todos")):
            T[kk]["n"] += 1; T[kk]["mismo_sensor"] += ((f, b) in ks); T[kk]["noche_cualquier_sensor"] += (f in fechas)
out = {}
for (g, b), d in sorted(T.items()):
    out[f"{g}|{b}"] = {"n": d["n"], "mismo_sensor": d["mismo_sensor"], "pct_mismo_sensor": round(100*d["mismo_sensor"]/d["n"], 1),
                       "noche_cualquier_sensor": d["noche_cualquier_sensor"], "pct_noche": round(100*d["noche_cualquier_sensor"]/d["n"], 1)}
json.dump(out, open("d07b_corroboracion.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
