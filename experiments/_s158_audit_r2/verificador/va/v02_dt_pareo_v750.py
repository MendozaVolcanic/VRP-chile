# -*- coding: utf-8 -*-
"""VA: que tolerancia de tiempo es "la misma pasada" entre nuestros records VIIRS 750 y las filas VIIRS de MIROVA.

Pregunta del instrumento 1: si 8 min fuera demasiado estricto (MIROVA con hora corrida), la distribucion de |dt|
al vecino mas cercano lo mostraria con masa entre 8 y 60 min. Pregunta 2: si el lector estuviera muerto daria 0
pares; se imprime n. Ventana: obs >= 2026-03-01 (A119: tabla sana desde marzo), records V750 de los 11 Tier A.
Ademas: para los 11 ceros con alerta protegida a <= 60 min de RA1, de que pasada sale la alerta.
"""
import csv, glob, json, os, sys
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
NOM = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
import yaml
inner = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}

ref = defaultdict(list)
for path, canal in (("latest_consolidado.csv", "tabla"), ("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", "ocr")):
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["Sensor"] != "VIIRS":
            continue
        try:
            v = float(row["VRP_MW"] or 0)
        except ValueError:
            v = 0.0
        ref[row["Volcan"]].append((datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M"), row["Tipo_Registro"], v, canal))
for k in ref:
    ref[k].sort()

hist = Counter()
n = 0
ceros = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    vol = d["volcano"]
    L = ref.get(NOM.get(vol, vol))
    if not L:
        continue
    ts = [x[0] for x in L]
    for r in d["records"]:
        if not r.get("sensor", "").endswith("_750") or r["datetime_utc"] < "2026-03-01":
            continue
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        i = bisect_left(ts, t)
        best = min((abs((ts[j] - t).total_seconds()) / 60 for j in (i - 1, i) if 0 <= j < len(ts)), default=None)
        if best is None:
            continue
        n += 1
        b = "0" if best == 0 else ("<=2" if best <= 2 else ("<=8" if best <= 8 else ("<=20" if best <= 20 else ("<=60" if best <= 60 else ">60"))))
        hist[b] += 1
        pc = r.get("primary_cluster")
        if pc and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inner[vol] and (pc.get("vrp_mw") or 0) == 0:
            m = [x for x in L if abs((x[0] - t).total_seconds()) <= 3600 and x[1].startswith("ALERTA_TERMICA") and x[2] >= 1]
            if m:
                same = [x for x in L if abs((x[0] - t).total_seconds()) <= 480]
                ceros.append((vol, r["datetime_utc"], r["sensor"], [(str(x[0])[11:16], x[2], x[3]) for x in m],
                              [(str(x[0])[11:16], x[1], x[2]) for x in same]))
print("records V750 obs >= 2026-03-01 con alguna fila VIIRS de MIROVA del volcan: n=%d" % n)
print("|dt| al vecino mas cercano (min):", dict(hist))
print("\nceros de cumbre con alerta >=1 MW a <=60 min (obs >= 2026-03-01): %d" % len(ceros))
for c in ceros:
    print("  ", c[0], c[1], c[2], "alerta>=1MW:", c[3], "| fila de la MISMA pasada (<=8 min):", c[4])
