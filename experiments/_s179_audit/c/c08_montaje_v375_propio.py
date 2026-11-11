# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c08: C-montaje de VIIRS 375 con codigo propio (la via de D2 contra el port
C13 de V375-E en la quincena DM, 2026-10-01 a 10-16 UTC).

QUE MIDE. Por pasada medida por V375-E en DM: si las celdas alertadas (fila, columna) de la via de D2 son las del
port, y el VRP del cumulo contra (i) el valor puntual del port a 0,001 MW (la declaracion original, opcion A) y
(ii) la banda de triangulacion del port (la decision post hoc, opcion 1), sin y con la holgura de 0,001 MW.

LAS DOS PREGUNTAS. (1) Si la via de D2 fuera otra que la medida en V375-E, lo veria? Solo en las pasadas con celdas
alertadas: se cuenta cuantas son (el resto coincide en vacio y no prueba nada). (2) Instrumento muerto: 0 pasadas
pareadas aborta. Control positivo: la via multiplicada por 1,05 TIENE que salir fuera de la banda en la mayoria de las
pasadas con celdas (se imprime cuantas atrapa la banda y cuantas el valor puntual).

Uso: python c08_montaje_v375_propio.py
"""
import collections, glob, json, statistics, sys
sys.stdout.reconfigure(encoding="utf-8")
T = "D:/vrp-trabajo/temporales/s179-audit/c"
CARPETAS = ["D:/vrp-trabajo/temporales/s167_v375e_far", "D:/vrp-trabajo/temporales/s159_portes",
            "C:/vrp-trabajo/temporales/s162_v375"]
PLAT = {"VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}
via = {}
for f in glob.glob(T + "/insumos/via/*.json"):
    d = json.load(open(f, encoding="utf-8"))
    for r in d["records"]:
        if "2026-10-01" <= r["datetime_utc"][:10] <= "2026-10-16" and r["sensor"].startswith("VIIRS") and not r["sensor"].endswith("_750"):
            via[(d["volcano"], r["sensor"], r["datetime_utc"][:16])] = r
print("pasadas VIIRS 375 de la via de D2 en DM:", len(via))
ab = {}
n_arch = 0
for c in CARPETAS:
    for f in sorted(glob.glob(c + "/**/resultados_VIIRS375_*.json", recursive=True)):
        n_arch += 1
        for e in json.load(open(f, encoding="utf-8")):
            if not ("2026-10-01" <= e["hora_utc"][:10] <= "2026-10-16") or "C13" not in (e.get("port") or {}):
                continue
            k = (e["volcan"], PLAT.get(e["granule"][:3]), e["hora_utc"][:16])
            ab.setdefault(k, (e, f))
print("archivos del port leidos:", n_arch, "| pasadas DM del port C13 (distintas):", len(ab))
com = [(k, via[k], ab[k][0]) for k in sorted(ab) if k in via]
print("pareadas con la via de D2:", len(com), "| del port sin pasada en la via:", sum(1 for k in ab if k not in via))
if not com:
    sys.exit("ABORTA: 0 pasadas pareadas")
res = collections.Counter()
difs, anchos, con_celdas = [], [], 0
atr_banda = atr_punto = 0
for k, r, e in com:
    p = e["port"]["C13"]
    cv = {(x.get("fila"), x.get("col")) for x in (r.get("anomaly_pixels") or [])}
    cp = {(x[0], x[1]) for x in (p.get("pixeles") or [])}
    vv = float((r.get("primary_cluster") or {}).get("vrp_mw") or 0.0)
    vp = float(p.get("vrp_mw") or 0.0)
    b = p.get("vrp_banda") or [vp, vp]
    if cv or cp:
        con_celdas += 1
        anchos.append(b[1] - b[0])
    if cv != cp:
        res["celdas distintas"] += 1
        difs.append((k, "celdas", len(cv), len(cp)))
        continue
    if abs(vv - vp) > 1e-3:
        res["VRP a mas de 0,001 MW del valor puntual del port"] += 1
        fuera0 = not (b[0] <= vv <= b[1])
        fuera1 = max(b[0] - vv, vv - b[1], 0.0) > 1e-3
        res["   de ellas, fuera de la banda sin holgura"] += fuera0
        res["   de ellas, a mas de 0,001 MW de la banda"] += fuera1
        difs.append((k, round(vv, 3), round(vp, 4), [round(b[0], 4), round(b[1], 4)], round(100 * (vv - vp) / vp, 2) if vp else None,
                     e["granule"] == r.get("granule")))
    else:
        res["igual a 0,001 MW"] += 1
    if cv:
        v5 = vv * 1.05
        atr_banda += max(b[0] - v5, v5 - b[1], 0.0) > 1e-3
        atr_punto += abs(v5 - vp) > 1e-3
print("resultado:", dict(res))
print("pasadas con celdas alertadas en alguno de los dos:", con_celdas, "de", len(com))
if anchos:
    print(f"ancho de la banda del port en las pasadas con celdas: mediana {statistics.median(anchos):.4f} MW, maximo {max(anchos):.4f} MW")
print(f"control positivo (via x 1,05 en las pasadas con celdas): la banda con 0,001 MW atrapa {atr_banda}; el valor puntual atrapa {atr_punto}")
for d in difs:
    print("   ", d)
