# -*- coding: utf-8 -*-
"""S126 — contrastar la conclusion de Villarrica contra la IMAGEN PROPIA de MIROVA.

Hasta aca todo lo que sabemos de Villarrica sale de NUESTRO pipeline: que el cluster
publicado esta a 2,74 km del crater, que el pixel del crater tiene contraste local
-0,09 K, que en el 80 % de las pasadas ni aparece. Es evidencia consistente pero
ENDOGENA: si nuestro procesamiento tuviera un sesgo, todos esos numeros lo compartirian.

El archivo `../mirova-tif-archive` tiene el campo de radiancia **I04 de MIROVA** en
GeoTIFF (134x134, EPSG:4326, ~385 m/pixel) — la misma banda que usamos, procesada por
ellos. Eso permite el chequeo independiente: mirar SU imagen y preguntar donde esta
caliente.

  · Si el crater de Villarrica aparece caliente en el campo de MIROVA -> mi conclusion
    es FALSA: hay senal y nuestro pipeline la esta perdiendo (problema de seleccion).
  · Si el crater es indistinguible en SU campo tambien -> confirmado desde fuera: a
    375 m el lava lake no destaca, y el numero que publicamos no viene del volcan.

LO QUE NO SE HACE (D6/A24): NO se suma el TIF como si fuera VRP. El TIF es el campo de
radiancia para visualizar; el VRP que MIROVA reporta sale de una seleccion de cluster,
no de la suma del raster. Aca se usa SOLO para la pregunta espacial: donde esta caliente.

CONTROL POSITIVO: Lascar, donde el foco es real y esta al crater. Si su crater no
aparece caliente en el TIF de MIROVA, el metodo no sirve y lo de Villarrica no vale.

Persiste en 02_contra_el_tif_de_mirova.json.
"""
import csv
import io
import json
import math
import os
import statistics as st
import sys

import numpy as np
import rasterio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import VENTS, haversine, resumen   # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "..", "mirova-tif-archive")
I04_LAMBDA = 3.740
C1, C2 = 1.19104e8, 1.43877e4
R_LOCAL_KM = 0.8          # corona local, igual que el script 01
OFFSET_ART = 2.8          # distancia del artefacto que publicamos
RUMBO_ART = 267.0         # rumbo medio medido (oeste)

VOLS = {"Villarrica": VENTS["Villarrica"], "Lascar": VENTS["Lascar"]}


def rad_a_bt(L):
    L = np.asarray(L, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return C2 / (I04_LAMBDA * np.log1p(C1 / (I04_LAMBDA ** 5 * L)))


def punto_a(lat, lon, dist_km, rumbo_deg):
    """Destino a `dist_km` con `rumbo_deg` desde (lat, lon)."""
    R = 6371.0
    b, la1, lo1 = map(math.radians, (rumbo_deg, lat, lon))
    d = dist_km / R
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(b))
    lo2 = lo1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(la1),
                           math.cos(d) - math.sin(la1) * math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)


def leer(path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(float)
        a[a <= 0] = np.nan
        return rad_a_bt(a), ds.transform, ds.bounds


def bt_en(bt, tr, lat, lon):
    col, fil = ~tr * (lon, lat)
    f, c = int(round(fil)), int(round(col))
    if not (0 <= f < bt.shape[0] and 0 <= c < bt.shape[1]):
        return None
    v = bt[f, c]
    return None if not np.isfinite(v) else float(v)


def contraste(bt, tr, lat, lon, r_km=R_LOCAL_KM):
    """BT del pixel menos la mediana de su corona local de r_km."""
    col, fil = ~tr * (lon, lat)
    f0, c0 = int(round(fil)), int(round(col))
    if not (0 <= f0 < bt.shape[0] and 0 <= c0 < bt.shape[1]):
        return None
    v = bt[f0, c0]
    if not np.isfinite(v):
        return None
    # radio en pixeles: el tamano de celda en km desde la transform
    km_por_px = abs(tr.a) * 111.32 * math.cos(math.radians(lat))
    rad = max(1, int(round(r_km / km_por_px)))
    vec = []
    for df in range(-rad, rad + 1):
        for dc in range(-rad, rad + 1):
            if df == 0 and dc == 0:
                continue
            f, c = f0 + df, c0 + dc
            if 0 <= f < bt.shape[0] and 0 <= c < bt.shape[1] and np.isfinite(bt[f, c]):
                vec.append(bt[f, c])
    return (float(v) - float(np.median(vec))) if len(vec) >= 5 else None


idx = [r for r in csv.DictReader(open(os.path.join(ARCHIVO, "index.csv"),
                                      encoding="utf-8", errors="replace"))
       if r["sensor"] == "VIIRS375"]

res = {"fuente": "mirova-tif-archive (campo I04 de MIROVA)",
       "nota": "NO se suma como VRP (D6/A24); se usa solo para la pregunta espacial",
       "por_volcan": {}}

print("CONTRA LA IMAGEN PROPIA DE MIROVA — campo I04, %d TIFs VIIRS375\n" % len(idx))
print("%-14s %6s %14s %16s %16s" %
      ("volcan", "tifs", "BT crater", "contraste crater", "contraste 2,8km W"))

for vol, vent in VOLS.items():
    sel = [r for r in idx if r["volcano"] == vol]
    art = punto_a(vent[0], vent[1], OFFSET_ART, RUMBO_ART)
    bts, c_cr, c_ar = [], [], []
    for r in sel:
        p = os.path.join(ARCHIVO, r["tif_path"])
        if not os.path.exists(p):
            continue
        try:
            bt, tr, _ = leer(p)
        except Exception:
            continue
        v = bt_en(bt, tr, *vent)
        if v is not None:
            bts.append(v)
        x = contraste(bt, tr, *vent)
        if x is not None:
            c_cr.append(x)
        y = contraste(bt, tr, *art)
        if y is not None:
            c_ar.append(y)
    if not c_cr:
        print("%-14s %6d   (sin lecturas validas)" % (vol, len(sel)))
        continue
    d = {"tifs": len(sel), "bt_crater_k": resumen(bts, 2),
         "contraste_crater_k": resumen(c_cr, 2),
         "contraste_offset_2_8km_k": resumen(c_ar, 2) if c_ar else None}
    res["por_volcan"][vol] = d
    print("%-14s %6d %14.2f %+16.2f %16s"
          % (vol, len(sel), d["bt_crater_k"]["mediana"], d["contraste_crater_k"]["mediana"],
             ("%+.2f" % d["contraste_offset_2_8km_k"]["mediana"]) if c_ar else "-"))

print("\n" + "=" * 78)
print("LECTURA")
la = res["por_volcan"].get("Lascar")
if la:
    v = la["contraste_crater_k"]["mediana"]
    print("  CONTROL POSITIVO (Lascar): contraste al crater en el campo de MIROVA %+.2f K" % v)
    if v <= 0.5:
        print("  !! el control NO da positivo: el metodo no sirve y lo de abajo no vale.")
vi = res["por_volcan"].get("Villarrica")
if vi and la:
    cr = vi["contraste_crater_k"]["mediana"]
    ar = vi["contraste_offset_2_8km_k"]["mediana"] if vi["contraste_offset_2_8km_k"] else None
    print("\n  VILLARRICA en el campo de MIROVA:")
    print("    contraste al crater        : %+.2f K" % cr)
    if ar is not None:
        print("    contraste a 2,8 km al oeste: %+.2f K" % ar)
    if cr <= 0.5:
        print("\n  -> CONFIRMADO DESDE FUERA: el crater tampoco destaca en la imagen de")
        print("     MIROVA. No es que nuestro pipeline pierda la senal: a 375 m no hay")
        print("     senal que perder. El numero que publicamos no viene del volcan.")
    else:
        print("\n  -> MI CONCLUSION ERA FALSA: el crater SI destaca en el campo de MIROVA,")
        print("     asi que hay senal y nuestro pipeline la esta perdiendo. Es un problema")
        print("     de SELECCION, no de resolucion.")

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "02_contra_el_tif_de_mirova.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
