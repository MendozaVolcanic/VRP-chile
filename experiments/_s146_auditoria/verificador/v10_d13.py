# -*- coding: utf-8 -*-
"""V-10: el '1,5 % corroborado' de D13 (S126). Camino propio: vlib (sin _s126_lib ni dlib).
Mide, sobre records con pc.vrp_mw>0 en 2026-05-01..2026-08-28: reparto por sensor de lo apagado (distance_class != summit),
y la corroboracion por ALERTA de MIROVA con tres pareos: mismo sensor+fecha (el de S126), cualquier sensor+fecha, y lo mismo para lo PUBLICADO (tasa base).
(1) roto? control positivo: lo publicado de Lascar v375 debe dar corroboracion alta (volcan con alertas casi diarias). (2) muerto? imprime n de alertas cargadas.
Nota A76: S126 solo cuenta alertas con hora UTC 3..9 y VRP>0; se reporta con y sin ese filtro."""
import io, sys
from collections import Counter, defaultdict
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
V0, V1 = "2026-05-01", "2026-08-28"
D = cargar(); R = [f for f in referencia() if f["tipo"].startswith("ALERTA") and V0 <= f["fecha"] <= V1 and f["b"]]
for filtro in ("hora 3-9 UTC y VRP>0 (S126)", "sin filtro horario"):
    A = [f for f in R if (3 <= int(f["dt"][11:13]) <= 9 and (f["vrp"] or 0) > 0)] if filtro.startswith("hora") else R
    ms = {(f["vol"], f["fecha"], f["b"]) for f in A}; cs = {(f["vol"], f["fecha"]) for f in A}
    print("\n== alertas MIROVA:", filtro, "n =", len(A), "por sensor", dict(Counter(f["b"] for f in A)))
    tot = defaultdict(Counter)
    for v in VOLS:
        for r in D[v]:
            b = bucket(r.get("sensor")); f = r["datetime_utc"][:10]
            pc = r.get("primary_cluster") or {}
            if b is None or not (V0 <= f <= V1) or not pc.get("vrp_mw"): continue
            g = "publicado(summit)" if r.get("distance_class") == "summit" else ("apagado" if pc.get("centroid_lat") is not None else "apagado sin centroide")
            for k in ((g, "todos"), (g, b), (g, v) if filtro.startswith("hora") and g != "apagado sin centroide" and False else None):
                if k is None: continue
                tot[k]["n"] += 1; tot[k]["mismo_sensor"] += (v, f, b) in ms; tot[k]["cualquier_sensor"] += (v, f) in cs
    for k in sorted(tot):
        c = tot[k]; print(f"  {k[0]:22s} {k[1]:6s} n={c['n']:5d}  mismo sensor {c['mismo_sensor']:4d} ({100*c['mismo_sensor']/c['n']:5.1f} %)  cualquier sensor esa fecha {c['cualquier_sensor']:4d} ({100*c['cualquier_sensor']/c['n']:5.1f} %)")
# por NOCHE (unidad del operador): noches-volcan con algo apagado vs con algo publicado
A = [f for f in R if 3 <= int(f["dt"][11:13]) <= 9 and (f["vrp"] or 0) > 0]; cs = {(f["vol"], f["fecha"]) for f in A}
na, npub = set(), set()
for v in VOLS:
    for r in D[v]:
        f = r["datetime_utc"][:10]; pc = r.get("primary_cluster") or {}
        if bucket(r.get("sensor")) is None or not (V0 <= f <= V1) or not pc.get("vrp_mw"): continue
        (npub if r.get("distance_class") == "summit" else na).add((v, f))
print("\nnoches-volcan con algo apagado", len(na), "con alerta MIROVA", len(na & cs), f"({100*len(na&cs)/len(na):.1f} %)")
print("noches-volcan con algo publicado", len(npub), "con alerta MIROVA", len(npub & cs), f"({100*len(npub&cs)/len(npub):.1f} %)")
print("noches SOLO apagadas (nada publicado esa noche)", len(na - npub), "con alerta", len((na - npub) & cs))
