# -*- coding: utf-8 -*-
"""F2 M4. Reproduce "desde marzo, 1.398 alertas dentro del radio y 858 detecciones a mediana 20 km (hasta 34,5)
rotuladas FALSO_POSITIVO" (docs/AUDIT_S150.md §8, sin script citado). Fuente: latest_consolidado.csv (CSV vivo).
Pregunta 1 del instrumento: si el conteo estuviera roto (p. ej. contando RUTINA), el desglose por tipo lo mostraria.
Control positivo: el total de filas y de RUTINA tiene que ser >> 0 y distinto de las alertas."""
import csv, sys, io, statistics, collections
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = sys.argv[1] if len(sys.argv) > 1 else "latest_consolidado.csv"
rows = list(csv.DictReader(open(F, encoding="utf-8")))
print("filas totales", len(rows), "| rango", min(r["Fecha_Satelite_UTC"] for r in rows), "a", max(r["Fecha_Satelite_UTC"] for r in rows))
def f(x):
    try: return float(x)
    except: return None
for desde, hasta in (("2026-03-01", "2026-10-09 23:59"), ("2026-03-01", "2026-10-09 12:00"), ("2026-03-01", "2026-09-30 23:59")):
    S = [r for r in rows if desde <= r["Fecha_Satelite_UTC"] <= hasta]
    tip = collections.Counter(r["Tipo_Registro"] for r in S)
    print("\n== ventana", desde, "a", hasta, "| filas", len(S), "| tipos", dict(tip))
    fp = [r for r in S if r["Tipo_Registro"].startswith("FALSO")]
    d = [f(r["Distancia_km"]) for r in fp if f(r["Distancia_km"]) is not None]
    if d: print("  FALSO*: n", len(fp), "| dist mediana %.2f max %.2f min %.2f" % (statistics.median(d), max(d), min(d)))
    print("  FALSO* por sensor", dict(collections.Counter(r["Sensor"] for r in fp)))
    print("  FALSO* por clasificacion MIROVA", dict(collections.Counter(r["Clasificacion Mirova"] for r in fp)))
    noct = [r for r in fp if 0 <= int(r["Fecha_Satelite_UTC"][11:13]) <= 12]
    print("  FALSO* con hora UTC 00-12 (aprox nocturna en Chile):", len(noct), "| resto (diurnas):", len(fp) - len(noct))
    vr = [f(r["VRP_MW"]) or 0 for r in fp]
    print("  FALSO* VRP>0:", sum(v > 0 for v in vr), "| mediana VRP %.3f" % statistics.median(vr))
    al = [r for r in S if r["Tipo_Registro"].startswith("ALERTA")]
    print("  ALERTA*: n", len(al), dict(collections.Counter(r["Tipo_Registro"] for r in al)))
    # duplicados por (volcan, sensor, fecha)
    k = collections.Counter((r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"]) for r in fp)
    print("  FALSO* claves (volcan,sensor,hora) unicas:", len(k), "| repetidas:", sum(1 for v in k.values() if v > 1))
    print("  FALSO* por volcan", dict(collections.Counter(r["Volcan"] for r in fp).most_common()))
    # cuantos de esos FP son en la misma pasada que una ALERTA (mismo volcan/sensor/hora)
    ka = {(r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"]) for r in al}
    print("  FALSO* en la misma pasada que una ALERTA del mismo volcan:", sum(1 for x in k if x in ka))

print("\n== M4b. Clasificacion MIROVA por tipo (desde 2026-03-01) y distancias de las FALSO nocturnas")
S = [r for r in rows if r["Fecha_Satelite_UTC"] >= "2026-03-01"]
for t in ("ALERTA_TERMICA", "FALSO_POSITIVO", "RUTINA"):
    print(" ", t, dict(collections.Counter(r["Clasificacion Mirova"] for r in S if r["Tipo_Registro"] == t).most_common(8)))
fp = [r for r in S if r["Tipo_Registro"] == "FALSO_POSITIVO"]
hrs = collections.Counter(int(r["Fecha_Satelite_UTC"][11:13]) for r in fp)
print("  FALSO por hora UTC", sorted(hrs.items()))
noc = [r for r in fp if 0 <= int(r["Fecha_Satelite_UTC"][11:13]) <= 12]
d = sorted(f(r["Distancia_km"]) for r in noc)
print("  FALSO nocturnas n", len(noc), "| dist mediana %.2f | cuartiles %.2f %.2f" % (statistics.median(d), d[len(d)//4], d[3*len(d)//4]))
print("  FALSO nocturnas por sensor", dict(collections.Counter(r["Sensor"] for r in noc)))
print("  FALSO nocturnas VRP mediana %.3f" % statistics.median(f(r["VRP_MW"]) for r in noc))
print("  FALSO todas: cuantas con Distancia exactamente 20.0:", sum(1 for r in fp if f(r["Distancia_km"]) == 20.0))
al = [r for r in S if r["Tipo_Registro"] == "ALERTA_TERMICA"]
print("  ALERTA por hora UTC 00-12:", sum(1 for r in al if 0 <= int(r["Fecha_Satelite_UTC"][11:13]) <= 12), "de", len(al))
