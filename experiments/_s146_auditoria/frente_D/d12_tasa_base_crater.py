# -*- coding: utf-8 -*-
"""d12: A82 / S130 ('en MODIS el pipeline SI encuentra el crater el 90 % / 97,6 % de las noches con ALERTA'). Falta la tasa base:
en que fraccion de las noches-sensor SIN alerta de MIROVA hay tambien un cumulo con magnitud dentro del inner? Si es parecida, el 90 %
no mide 'encontrar el crater' sino 'casi siempre hay un cumulo ahi'. Ventana 2026-01-29..08-28 (GT con corpus, regimen previo) y actual.
OJO: 'sin alerta' aca = sin fila ALERTA en CONS u OCR; NO es el 'negativo limpio' del banco de paridad (no exige que MIROVA haya mirado).
Instrumento: (1) roto => 0 o 100 en ambas filas por igual; el contraste v375 (donde si hay diferencia) es el control. (2) n impresos."""
import io, sys, json
from collections import defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
D = cargar()
def medir(w):
    mir, _ = cargar_mirova(w); hay = defaultdict(bool)
    for v in VOLS:
        for r in D[v]:
            f = r["datetime_utc"][:10]
            if not (w[0] <= f <= w[1]) or not es_noche(r): continue
            b = bucket(r["sensor"]); pc = r.get("pc") or {}
            c = (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER[v]
            hay[(v, f, b)] = hay[(v, f, b)] or c
    res = {}
    for b in ("modis", "v750", "v375"):
        ks = [k for k in hay if k[2] == b]; al = [k for k in ks if (k[1], b) in (mir.get(k[0]) or {})]; no = [k for k in ks if (k[1], b) not in (mir.get(k[0]) or {})]
        res[b] = {"con_alerta": (sum(hay[k] for k in al), len(al), round(100*sum(hay[k] for k in al)/len(al), 1) if al else "SIN DATO"),
                  "sin_alerta": (sum(hay[k] for k in no), len(no), round(100*sum(hay[k] for k in no)/len(no), 1) if no else "SIN DATO")}
    return res
out = {"previo(01-29..08-28)": medir(("2026-01-29", "2026-08-28")), "actual(09-01..09-19)": medir(("2026-09-01", "2026-09-19"))}
json.dump(out, open("d12_tasa_base_crater.json", "w"), indent=1); print(json.dumps(out, indent=1))
