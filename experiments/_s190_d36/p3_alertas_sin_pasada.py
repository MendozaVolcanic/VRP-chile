# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): script de medición sobre los records, sólo lectura.
"""D36 punto 3, costo contra MIROVA de los descartes de la vía (corte de 5 km al centro, mínimo de 100 píxeles).

POR QUÉ: cuando la vía devuelve None la pasada no deja record (VIIRS 375 y MODIS la borran sin rastro). Si alguno de
esos descartes cayera en una pasada donde MIROVA sí publicó, perderíamos esa alerta. Se cuenta, por sensor, cada
alerta nocturna de MIROVA (VRP > 0; VIIRS 375 sobre 0,05 MW, D-9) sin NINGÚN record nuestro de la vía del mismo
sensor a ±60 min, y si la guardia K (que no tiene esos cortes) sí escribió esa pasada. Las protegidas (>= 1 MW) se
cuentan aparte.
Ventana: desde DESDE (2026-03-01) hasta la última pasada nuestra de cada sensor.
Uso: python experiments/_s190_d36/p3_alertas_sin_pasada.py <raiz_repo> <salida.json> [DESDE]
"""
import collections
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT, OUT = sys.argv[1], sys.argv[2]
DESDE = sys.argv[3] if len(sys.argv) > 3 else "2026-03-01"
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "PlanchonPeteroa", "Tupungatito", "Isluga", "Lastarria", "Chaiten"]
FAM_MIROVA = {"MODIS": "MODIS", "VIIRS375": "V375", "VIIRS": "V750"}
GUARDIA = {"MODIS": "guardia_k_modis", "V375": "guardia_k_viirs", "V750": "guardia_k_viirs"}
VENT = timedelta(minutes=60)
ESTRICTA = timedelta(minutes=10)   # misma pasada (A109): el otro satélite pasa ~50 min antes o después


def fam(s):
    s = s.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "V750"
    if s.startswith("VIIRS"):
        return "V375"
    return None


def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def cargar(sub, v):
    p = Path(ROOT) / "data" / sub / (v + ".json")
    return json.load(open(p, encoding="utf-8"))["records"] if p.exists() else []


cont, casos = collections.Counter(), []
for v in TIER_A:
    nuestros = collections.defaultdict(list)
    for r in cargar("mirova_equivalent", v):
        f = fam(r.get("sensor", ""))
        if f and r.get("via_codigo_mirova") is True:
            nuestros[f].append(t(r["datetime_utc"]))
    guard = collections.defaultdict(list)
    for sub in set(GUARDIA.values()):
        for r in cargar(sub, v):
            f = fam(r.get("sensor", ""))
            if f:
                guard[f].append((t(r["datetime_utc"]), r))
    ded = {}
    for a in cargar("mirova", v):
        k = (a["datetime_utc"][:16], a["sensor"])
        if k not in ded or (ded[k]["source"] != "consolidado" and a["source"] == "consolidado"):
            ded[k] = a
    for a in ded.values():
        f = FAM_MIROVA.get(a["sensor"])
        vrp = a.get("VRP_MW") or 0
        if f is None or vrp <= 0 or a.get("dia") or (f == "V375" and vrp <= 0.05):
            continue
        ta = t(a["datetime_utc"])
        if ta < t(DESDE + " 00:00") or not nuestros[f] or ta > max(nuestros[f]) + VENT:
            continue
        cont["alertas_" + f] += 1
        cont["protegidas_" + f] += vrp >= 1
        if not any(abs(x - ta) <= ESTRICTA for x in nuestros[f]):
            gk10 = [r for x, r in guard[f] if abs(x - ta) <= ESTRICTA]
            cont["sin_misma_pasada_10min_" + f] += 1
            cont["sin_misma_pasada_10min_protegida_" + f] += vrp >= 1
            cont["sin_misma_pasada_10min_con_guardia_k_" + f] += bool(gk10)
            casos.append({"criterio": "10min", "volcan": v, "fam": f, "t": str(ta), "vrp_mirova": vrp,
                          "fuente": a["source"], "guardia_k": [{"dt": r["datetime_utc"], "sensor": r["sensor"],
                                                                 "vrp_mw": r.get("vrp_mw")} for r in gk10]})
        if any(abs(x - ta) <= VENT for x in nuestros[f]):
            continue
        gk = [r for x, r in guard[f] if abs(x - ta) <= VENT]
        cont["sin_pasada_" + f] += 1
        cont["sin_pasada_protegida_" + f] += vrp >= 1
        cont["sin_pasada_con_guardia_k_" + f] += bool(gk)
        casos.append({"criterio": "60min", "volcan": v, "fam": f, "t": str(ta), "vrp_mirova": vrp, "fuente": a["source"],
                      "guardia_k": [{"dt": r["datetime_utc"], "sensor": r["sensor"], "vrp_mw": r.get("vrp_mw"),
                                     "sensor_zenith_deg": r.get("sensor_zenith_deg")} for r in gk]})
res = {"desde": DESDE, "contadores": dict(sorted(cont.items())), "casos": casos}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res["contadores"]))
for c in casos:
    print(c["criterio"], c["volcan"], c["fam"], c["t"], c["vrp_mirova"], c["fuente"], "guardiaK:", len(c["guardia_k"]))
