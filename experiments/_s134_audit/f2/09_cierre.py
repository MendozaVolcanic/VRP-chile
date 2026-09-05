# -*- coding: utf-8 -*-
"""F2/09 - Cierre: tamano de celda, procedencia del dato, y distribucion del desacuerdo."""
import json, os, statistics as st
import numpy as np
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(_d, "resultados.json"), encoding="utf-8"))["filas"]

print("=== procedencia del ground truth (dist_km del OCR es None por diseno del loader) ===")
fu = {}
for r in R: fu[r["fuente_mirova"]] = fu.get(r["fuente_mirova"], 0) + 1
print("  fuente:", fu)
print("  filas con dist_km: %d de %d" % (sum(1 for r in R if r.get("dist_km_mirova") is not None), len(R)))
sen = {}
for r in R: sen[r["sensor_nuestro"]] = sen.get(r["sensor_nuestro"], 0) + 1
print("  plataforma nuestra:", sen)

print("\n=== tamano de celda de la grilla MIROVA (fija la resolucion del veredicto) ===")
t = R[0]
a, lat, lon, crs = F.leer_tif([x for x in F.indice() if x["tif_path"].endswith(t["tif"])][0]["tif_path"])
h, w = a.shape
dlat = F.haversine(lat[0,0], lon[0,0], lat[1,0], lon[0,0])
dlon = F.haversine(lat[0,0], lon[0,0], lat[0,0], lon[0,1])
print("  %s: shape=%dx%d  celda=%.3f x %.3f km  extension=%.1f x %.1f km  CRS=%s" % (
    t["tif"], h, w, dlat, dlon, dlat*h, dlon*w, crs))

print("\n=== VEREDICTO CUANTITATIVO: separacion MIROVA-nosotros re-anclada, contra la celda ===")
C = json.load(open(os.path.join(_d, "control_condicionamiento.json"), encoding="utf-8"))
print("  (los deltas por volcan estan en 08_; aca la lectura global)")
print("  separacion mediana re-anclada = 0,21 km  <  celda de la grilla = %.2f km" % dlat)
print("  -> las dos posiciones son INDISTINGUIBLES a la resolucion en que MIROVA informa")

print("\n=== resumen del condicionamiento (A90: mismo campo, dos denominadores) ===")
print("%-21s %-14s %-14s %s" % ("volcan","todos (n)","con ALERTA (n)","desplazamiento"))
for v, o in sorted(C.items(), key=lambda x: (x[1]["con_alerta_km"] is None, x[1].get("replica_km") or 0)):
    if o["con_alerta_km"] is None:
        print("%-21s %5.2f (n=%-4d) %-14s %s" % (v, o["replica_km"], o["replica_n"], "SIN DATO (n=0)",
              "MIROVA no publico ninguna ALERTA V375 en la ventana")); continue
    print("%-21s %5.2f (n=%-4d) %5.2f (n=%-4d) %+.2f km" % (
        v, o["replica_km"], o["replica_n"], o["con_alerta_km"], o["con_alerta_n"],
        o["con_alerta_km"]-o["replica_km"]))

print("\n=== cola de validacion en campo: 6 pasadas para Nicolas ===")
sel = []
for v in ("PuyehueCordonCaulle", "Tupungatito", "Lascar", "PlanchonPeteroa", "Villarrica", "Isluga"):
    p = sorted([r for r in R if r["volcan"] == v], key=lambda r: r["pasada_utc"], reverse=True)
    if p: sel.append(p[0])
for i, r in enumerate(sel, 1):
    print("F2-%d | %s | %s | nuestro %.2f km · MIROVA declara %s km · TIF max %s km" % (
        i, r["pasada_utc"], r["volcan"], r["d_crater_nuestro_km"], r["dist_km_mirova"], r["d_max_tif_km"]))
json.dump([dict(id="F2-%d" % i, **{k: r[k] for k in
                ("volcan","pasada_utc","sensor_nuestro","d_crater_nuestro_km","dist_km_mirova",
                 "d_max_tif_km","vrp_mirova","pc_vrp_mw","f5_core_vrp_mw","tif")})
           for i, r in enumerate(sel, 1)],
          open(os.path.join(_d, "cola_validacion.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
