# -*- coding: utf-8 -*-
"""S161: constantes y utilidades del mapa de persistencia (Tupungatito, Cordón Caulle, Isluga). Sólo lectura.

De dónde sale cada número (todos leídos en esta sesión):
- vent, mirova_center, inner_radius_km: volcanoes.yaml de este worktree (main ae29ac91f), iguales a los de
  experiments/_s160_espacial/comun.py (rama loop/activo, commit 98e52517b).
- centro del TIF: bounds de los GeoTIFF VIIRS 375 EPSG:4326 de MIROVA (134 x 134), leídos con rasterio (S160 v01).
- grilla de MIROVA (UTM, celda 750 m, 67 x 67): experiments/_s160_espacial/_censo_s159/objetivos.json, campo `grilla`
  (epsg, ul_x, ul_y). Caja de cumbre = filas y columnas 30 a 36; anillo = filas 22 a 42 por columnas 24 a 42 (forma
  real que midió el verificador S160, VE-03: +8,625 km al N, -7,125 al S, +-7,125 E-O desde la celda 33).
- Datos de producción: copia sólo lectura de experiments/_s160_espacial/data/ (origin/main db0dfe847), no commiteada.
"""
from __future__ import annotations

import io
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Geod, Transformer

AQUI = Path(__file__).resolve().parent
WT = AQUI.parents[2]  # verificador S161: rerun/ es un nivel mas hondo
REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")   # checkout principal (loop/activo)
S160 = REPO / "experiments" / "_s160_espacial"
DATA = WT / "data" / "mirova_equivalent"  # verificador S161: datos de main 3bbd18d2c
TIF_ARCHIVE = REPO.parent / "mirova-tif-archive"
SCRATCH = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-frosty-lamport-3fef52\1599a5b2-2cc5-4d97-aa82-b226df33c7ad\scratchpad")  # verificador S161: scratchpad propio, PNG bajadas de nuevo

G = Geod(ellps="WGS84")
VOLS = ["Tupungatito", "PuyehueCordonCaulle", "Isluga"]
NOMBRE = {"Tupungatito": "Tupungatito", "PuyehueCordonCaulle": "Puyehue-Cordón Caulle", "Isluga": "Isluga"}

GEO = {
    "Tupungatito": {"vent": (-33.389044, -69.826374), "mirova_center": (-33.42694, -69.80039),
                    "tif_centro": (-33.4253, -69.7984), "inner_km": 7.0,
                    "grilla": {"epsg": 32719, "ul_x": 400530.6, "ul_y": 6326186.0}},
    "PuyehueCordonCaulle": {"vent": (-40.525499, -72.146137), "mirova_center": (-40.5903, -72.1187),
                            "tif_centro": (-40.5903, -72.1167), "inner_km": 20.0,
                            "grilla": {"epsg": 32718, "ul_x": 718601.9, "ul_y": 5527633.6}},
    "Isluga": {"vent": (-19.15, -68.83), "mirova_center": (-19.15212, -68.83269),
               "tif_centro": (-19.1504, -68.8304), "inner_km": 5.0,
               "grilla": {"epsg": 32719, "ul_x": 492501.4, "ul_y": 7907440.6}},
}
CELDA_M = 750.0


def utf8_stdout():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def dist_km(lat1, lon1, lat2, lon2):
    return G.inv(lon1, lat1, lon2, lat2)[2] / 1000.0


def rumbo(lat1, lon1, lat2, lon2):
    return G.inv(lon1, lat1, lon2, lat2)[0] % 360


def octante(az):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(((az % 360) + 22.5) % 360 // 45)]


def rect_grilla(vol, f0, f1, c0, c1):
    """Polígono lat/lon del rectángulo de celdas filas f0..f1 x cols c0..c1 (inclusive) de la grilla de MIROVA."""
    g = GEO[vol]["grilla"]
    T = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True)
    xs = [g["ul_x"] + c0 * CELDA_M, g["ul_x"] + (c1 + 1) * CELDA_M]
    ys = [g["ul_y"] - f0 * CELDA_M, g["ul_y"] - (f1 + 1) * CELDA_M]
    pts = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1]), (xs[0], ys[0])]
    out = []
    for x, y in pts:
        lon, lat = T.transform(x, y)
        out.append([round(lat, 6), round(lon, 6)])
    return out


def elevacion_solar(lat, lon, dt: datetime) -> float:
    """Elevación del sol en grados (algoritmo NOAA, precisión ~0,5 grados, suficiente para separar noche y día)."""
    dt = dt.astimezone(timezone.utc)
    doy = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (h - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                    - 0.040849 * math.sin(2 * g))
    tst = h * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cosz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1, min(1, cosz))))


def franja(elev):
    """noche: sol 6 grados o más bajo el horizonte; día: sol sobre el horizonte; crepúsculo: entre ambos."""
    if elev <= -6:
        return "noche"
    if elev > 0:
        return "dia"
    return "crepusculo"


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None
