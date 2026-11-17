# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): script de medición, sólo lectura. No es detección de producción; no escribe en data/.
"""D36 punto 1 (y punto 3 para MODIS): elige las pasadas MODIS que el runner baja y mide. Se corre ANTES de mirar
ningún resultado; la lista queda commiteada (p1_pasadas.json) con su semilla.

POR QUÉ estos estratos: el cambio de umbrales (K1 -0,7 a -0,8 y piso de dNTI fuera de la cumbre 0,02 a 0,01) sólo
puede SUMAR alertados (umbrales más bajos), salvo el efecto de segundo orden en el fondo del primer pase. Entonces lo
que hay que mirar es (1) si recupera alertas de MIROVA que hoy no publicamos o cambia su magnitud, (2) cuánto
sobre-publica en pasadas donde MIROVA no vio nada, y (3) cuánto cambia lo que ya publicamos.
Estratos (ventana: desde DESDE, tabla de MIROVA comparable, hasta el último record):
  mirova     toda pasada nocturna nuestra de MODIS (vía) a ±60 min de una alerta nocturna MODIS de MIROVA (VRP > 0,
             consolidado u OCR)
  nuestra    toda pasada nocturna nuestra de MODIS con vrp_mw > 0
  negativa   15 por volcán, al azar (semilla 190), entre las nocturnas con vrp_mw == 0 y sin alerta MODIS de MIROVA a
             ±60 min
  borde      (punto 3) pasadas MODIS que escribió la guardia K (data/guardia_k_modis) y producción no (la vía devolvió
             None: corte de 5 km al centro o menos de 100 píxeles), hasta 60 al azar (semilla 190)
Uso: python experiments/_s190_d36/p1_seleccion.py <raiz_repo> <salida.json> [DESDE]
"""
import collections
import json
import random
import sys
from datetime import datetime, timedelta

ROOT, OUT = sys.argv[1], sys.argv[2]
DESDE = sys.argv[3] if len(sys.argv) > 3 else "2026-03-01"
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "PlanchonPeteroa", "Tupungatito", "Isluga", "Lastarria", "Chaiten"]
VENT = timedelta(minutes=60)
N_NEG, N_BORDE, SEMILLA = 15, 60, 190


def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


rng = random.Random(SEMILLA)
t0 = t(DESDE + " 00:00")
sel, cont, borde_pool = {}, collections.Counter(), []
for v in TIER_A:
    recs = json.load(open(f"{ROOT}/data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]
    noc = [r for r in recs if str(r.get("sensor", "")).startswith("MODIS") and r.get("via_codigo_mirova") is True
           and (r.get("solar_zenith_deg") or 0) > 90 and t(r["datetime_utc"]) >= t0]
    m = json.load(open(f"{ROOT}/data/mirova/{v}.json", encoding="utf-8"))["records"]
    alertas = sorted({t(a["datetime_utc"]) for a in m if a["sensor"] == "MODIS" and (a.get("VRP_MW") or 0) > 0
                      and not a.get("dia") and t(a["datetime_utc"]) >= t0})
    cont[f"alertas_mirova_{v}"] = len(alertas)
    negs = []
    for r in noc:
        tr = t(r["datetime_utc"])
        cerca = any(abs(tr - ta) <= VENT for ta in alertas)
        clave = (v, r["granule"])
        estr = []
        if cerca:
            estr.append("mirova")
        if (r.get("vrp_mw") or 0) > 0:
            estr.append("nuestra")
        if estr:
            sel[clave] = {"volcan": v, "granule": r["granule"], "sensor": r["sensor"], "dt": r["datetime_utc"],
                          "estratos": estr}
        elif (r.get("vrp_mw") or 0) == 0:
            negs.append(r)
    for r in rng.sample(negs, min(N_NEG, len(negs))):
        sel[(v, r["granule"])] = {"volcan": v, "granule": r["granule"], "sensor": r["sensor"],
                                  "dt": r["datetime_utc"], "estratos": ["negativa"]}
    cont[f"negativas_pool_{v}"] = len(negs)
    # punto 3: K escribió y la vía no
    try:
        gk = json.load(open(f"{ROOT}/data/guardia_k_modis/{v}.json", encoding="utf-8"))["records"]
    except FileNotFoundError:
        gk = []
    prod = {r["granule"] for r in recs if r.get("granule")}
    for r in gk:
        if r.get("granule") and r["granule"] not in prod and t(r["datetime_utc"]) >= t0 \
                and (r.get("solar_zenith_deg") or 0) > 90:
            borde_pool.append({"volcan": v, "granule": r["granule"], "sensor": r["sensor"], "dt": r["datetime_utc"],
                               "estratos": ["borde"]})
cont["borde_pool"] = len(borde_pool)
for b in rng.sample(sorted(borde_pool, key=lambda x: (x["volcan"], x["granule"])), min(N_BORDE, len(borde_pool))):
    clave = (b["volcan"], b["granule"])
    if clave in sel:
        sel[clave]["estratos"].append("borde")
    else:
        sel[clave] = b
lista = sorted(sel.values(), key=lambda x: (x["volcan"], x["dt"]))
for e in lista:
    for s in e["estratos"]:
        cont["sel_" + s] += 1
out = {"desde": DESDE, "semilla": SEMILLA, "n": len(lista), "contadores": dict(sorted(cont.items())), "pasadas": lista}
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(lista), {k: v for k, v in cont.items() if k.startswith("sel_") or k == "borde_pool"})
print("ultima", max(e["dt"] for e in lista))
