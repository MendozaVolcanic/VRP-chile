# -*- coding: utf-8 -*-
"""d06: A82 ('recall dashboard VIIRS375 99 % / VIIRS750 86 % / MODIS 16 %; el pipeline encuentra el crater 90 %').
Fuente: AUDIT_S114, ventana 2026-05-01..06-30, MODIS n=19 noches-sensor. Remide sobre (a) esa ventana, (b) todo el GT con
corpus (2026-01-29 en adelante), (c) regimen actual. Unidad: NOCHE-SENSOR-volcan con ALERTA nocturna de MIROVA (CONS u OCR).
'dashboard' = algun record de ese sensor esa fecha con distance_class summit y (vrp_mw>0 o triggered_test1).
'crater' = algun record de ese sensor con pc.vrp>0 y pc.centroid_dist<=inner (sin mirar la etiqueta).
Instrumento: (1) roto => recall 0 o 100 en todo; el contraste MODIS dashboard vs crater es el control interno.
(2) denominadores impresos. SIN DATO si tot=0."""
import io, sys, json
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
D = cargar()
def medir(w):
    mir, _ = cargar_mirova(w); dash = set(); crat = set(); hay = set()
    for vol in VOLS:
        for r in D[vol]:
            b = bucket(r.get("sensor")); f = r["datetime_utc"][:10]; hay.add((vol, f, b))
            if r.get("distance_class") == "summit" and ((r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1")): dash.add((vol, f, b))
            pc = r.get("pc") or {}
            if (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER[vol]: crat.add((vol, f, b))
    res = {}
    for b in ("v375", "v750", "modis"):
        ks = [(vol, d, bb) for vol in VOLS for (d, bb) in (mir.get(vol) or {}) if bb == b]
        con = [k for k in ks if k in hay]
        res[b] = {"alertas_noche_sensor": len(ks), "sin_pasada_nuestra": len(ks)-len(con),
                  "dashboard": (sum(k in dash for k in ks), round(100*sum(k in dash for k in ks)/len(ks), 1) if ks else "SIN DATO"),
                  "crater": (sum(k in crat for k in ks), round(100*sum(k in crat for k in ks)/len(ks), 1) if ks else "SIN DATO")}
    return res
out = {"S114(05-01..06-30)": medir(("2026-05-01", "2026-06-30")), "GT_con_corpus(01-29..08-28)": medir(("2026-01-29", "2026-08-28")),
       "actual(09-01..09-19)": medir(("2026-09-01", "2026-09-19"))}
json.dump(out, open("d06_recall_por_sensor.json", "w"), indent=1)
print(json.dumps(out, indent=1))
