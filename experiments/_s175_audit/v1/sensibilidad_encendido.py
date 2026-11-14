#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175), afirmación 158: ¿cuánto se mueve el encendido (menor processed_utc de un record MODIS de la vía) si se
re-escribe 1, k o todos los records de la vía? Usa la función real encendido_desde_datos de
scripts/vigilancia_guardia_modis.py (root_base), sobre los JSON de producción de una carpeta.
Pregunta 1: si el encendido dependiera de un solo record, quitar el primero lo movería; se mide cuánto.
Pregunta 2 (control): con los datos tal cual, la función tiene que dar el encendido publicado
(2026-11-02 20:11:43 en guardia_modis_latest.json de e75a7d52d); si no, el lector no es el de la vigilancia.
Escenario «--overwrite»: todos los records de la vía con processed_utc = 2026-11-08T00:00:00Z (un reproceso que
re-escribe toda la ventana con la vía); se informa el encendido resultante y qué pasadas de alerta quedarían del lado
retrospectivo (sólo se cuentan records de la vía entre el encendido viejo y el nuevo).
Uso: python sensibilidad_encendido.py <root_base> <carpeta mirova_equivalent>
"""
import copy, json, os, sys
root, carpeta = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts")); sys.path.insert(0, root)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import vigilancia_guardia_modis as vgm
raw = {}
for v in vgm.aa.VOLS:
    with open(os.path.join(carpeta, v + ".json"), encoding="utf-8") as fh:
        raw[v] = json.load(fh).get("records") or []
base = vgm.encendido_desde_datos(raw)
print("CONTROL encendido tal cual:", base["encendido_utc"], "primera observacion:", base["primera_observacion"],
      "n claves via:", len(base["via"]))
via = sorted(((r.get("processed_utc"), v, r.get("sensor"), str(r.get("datetime_utc"))[:16], r.get("product_version"))
              for v, recs in raw.items() for r in recs
              if r.get("via_codigo_mirova") is True and str(r.get("sensor") or "").startswith("MODIS")))
print("los 12 primeros processed_utc de la vía:")
for t in via[:12]:
    print("  ", t)
# quitar (re-escribir hacia adelante) los k primeros
for k in (1, 2, 5, 11, 22, len(via)):
    r2 = copy.deepcopy(raw)
    quitar = set((t[1], t[2], t[3]) for t in via[:k])
    for v, recs in r2.items():
        for r in recs:
            if (v, r.get("sensor"), str(r.get("datetime_utc"))[:16]) in quitar:
                r["processed_utc"] = "2026-11-08T00:00:00Z"
    e = vgm.encendido_desde_datos(r2)
    print(f"re-escritos los {k} primeros -> encendido {e['encendido_utc']}")
