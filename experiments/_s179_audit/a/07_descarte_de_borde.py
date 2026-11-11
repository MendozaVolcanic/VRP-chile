# -*- coding: utf-8 -*-
"""Las pasadas MODIS que la guardia K registra y produccion (la via) no, desde el encendido: que dice MIROVA de ellas.

Pregunta fisica: la via descarta un granulo si el volcan queda mal cubierto (menos de 100 celdas a 45 km o la celda mas
cercana a mas de 5 km, pipeline/mirova_v750_codigo.py). Si MIROVA lista esa misma pasada en su tabla, MIROVA si la
proceso y nosotros mostramos "sin dato" donde MIROVA muestra una pasada.

Preguntas del instrumento:
1. Si MIROVA listara esas pasadas, se veria? Si: se imprimen las filas de la referencia a +-120 s y a +-10 min.
2. Instrumento muerto: control positivo, una pasada que si esta en produccion (Chillan 2026-11-08 08:00) tiene que
   traer fila de MIROVA (alerta de 22,46 MW).
Datos: main 438a60a1e, snapshot de la referencia del repo (tabla y OCR). Denominador: 2 pasadas de borde en 9 noches.
"""
import io, sys, os, json
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE); os.chdir(BASE)
import auto_audit_weekly as aa
from referencia_mirova_unificada import cargar_referencia_unificada
filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
print("filas de referencia:", len(filas), "| ultima fila MODIS:", max(f["fecha_utc"] for f in filas if f.get("sensor_bucket") == "MODIS"))
def cerca(vol, cuando, seg):
    t = datetime.strptime(cuando, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    out = []
    for f in filas:
        if f["volcano"] != vol or f.get("sensor_bucket") != "MODIS": continue
        try: d = datetime.fromisoformat(f["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
        except ValueError: continue
        if abs((d - t).total_seconds()) <= seg: out.append((f["fecha_utc"], f["tipo"], f.get("vrp_mw"), f.get("source"), f.get("dist_km")))
    return out
def guardia(vol, cuando):
    recs = json.load(open(os.path.join(BASE, "data", "guardia_k_modis", vol + ".json"), encoding="utf-8"))["records"]
    return [{k: r.get(k) for k in ("sensor", "datetime_utc", "sensor_zenith_deg", "vrp_mw", "distance_class", "granule", "n_anomalous_pixels")} for r in recs if r["datetime_utc"] == cuando]
for vol, cuando in (("NevadosDeChillan", "2026-11-08 08:00"), ("Villarrica", "2026-11-04 07:10"), ("Chaiten", "2026-11-09 00:55")):
    print(f"\n{vol} {cuando} UTC")
    print("  MIROVA a +-120 s:", cerca(vol, cuando, 120))
    print("  MIROVA a +-10 min:", cerca(vol, cuando, 600))
    print("  record de la guardia K:", guardia(vol, cuando))
    # vecinos: otros volcanes en la misma pasada (mismo minuto +-5 min) con record de produccion
    for v2 in ("Villarrica", "Llaima", "PuyehueCordonCaulle", "Chaiten", "Copahue", "NevadosDeChillan"):
        recs = json.load(open(os.path.join(BASE, "data", "mirova_equivalent", v2 + ".json"), encoding="utf-8"))["records"]
        t = datetime.strptime(cuando, "%Y-%m-%d %H:%M")
        near = [(r["sensor"], r["datetime_utc"], r.get("sensor_zenith_deg"), r.get("via_codigo_mirova")) for r in recs
                if r["sensor"].startswith("MODIS") and abs((datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M") - t).total_seconds()) <= 600]
        if near: print(f"    produccion de {v2} cerca de esa hora:", near)
