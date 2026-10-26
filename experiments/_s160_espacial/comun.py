# -*- coding: utf-8 -*-
"""Constantes y utilidades compartidas de la auditoria espacial S160 (solo lectura).

Fuentes de cada numero (todas leidas en esta sesion):
- vent_lat/lon, mirova_center_lat/lon, inner_radius_km, lat/lon: volcanoes.yaml (Tupungatito,
  PuyehueCordonCaulle, Isluga; impreso con yaml.safe_load en la sesion).
- centro del TIF: centro del BoundingBox de los GeoTIFF EPSG:4326 de VIIRS 375 (134 x 134), igual en
  los 370 (Tupungatito), 410 (PCC) y 362 (Isluga) TIF leidos con rasterio en esta sesion.
- caja de cumbre y anillo de MIROVA VIIRS 750: BOX == 2 es 7 x 7 celdas (filas 30-36 de 67), BOX == 1
  es el rectangulo 21 x 19 celdas (filas 22-42, cols 24-42) menos la caja; celda 750 m
  (experiments/_s158_audit_r2/a113/m01_box_matriz.txt y m08_box_forma.txt en origin/main).
  Media anchura: caja 3,5 x 0,75 = 2,625 km (esquina 3,71 km); anillo 10,5 x 0,75 = 7,875 km
  (esquina ~11,1 km con 9,5 x 0,75 = 7,125 en la otra direccion).
"""
from __future__ import annotations

import math
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
DATA = AQUI / "data"
SHA_ORIGIN_MAIN = (DATA / "SHA_ORIGIN_MAIN.txt").read_text().strip()

VOLS = ["Tupungatito", "PuyehueCordonCaulle", "Isluga"]
NOMBRE_CSV = {"Tupungatito": "Tupungatito", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "Isluga": "Isluga"}

# volcanoes.yaml (leido en la sesion); el centro del TIF sale de rasterio.
GEO = {
    "Tupungatito": {"lat": -33.4, "lon": -69.8, "vent": (-33.389044, -69.826374),
                    "mirova_center": (-33.42694, -69.80039), "tif_centro": (-33.4253, -69.7984),
                    "inner_km": 7.0, "vent_radius_km": 5.0},
    "PuyehueCordonCaulle": {"lat": -40.59, "lon": -72.117, "vent": (-40.525499, -72.146137),
                            "mirova_center": (-40.5903, -72.1187), "tif_centro": (-40.5903, -72.1167),
                            "inner_km": 20.0, "vent_radius_km": 3.0},
    "Isluga": {"lat": -19.15, "lon": -68.83, "vent": (-19.15, -68.83),
               "mirova_center": (-19.15212, -68.83269), "tif_centro": (-19.1504, -68.8304),
               "inner_km": 5.0, "vent_radius_km": 2.0},
}

CAJA_KM = 3.5 * 0.75       # 2.625: media anchura de la caja de cumbre 7 x 7 (VIIRS 750)
CAJA_ESQUINA_KM = CAJA_KM * math.sqrt(2)
ANILLO_KM = 10.5 * 0.75    # 7.875: media anchura mayor del anillo 21 x 19
ANILLO_ESQUINA_KM = math.hypot(10.5 * 0.75, 9.5 * 0.75)
PROTEGIDA_MW = 1.0
MINIMA_MW = 0.05            # D-9 SN, solo VIIRS 375


def hav_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def rumbo_deg(lat1, lon1, lat2, lon2):
    """Rumbo geografico de 1 a 2, grados desde el norte en sentido horario."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def octante(b):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(((b + 22.5) % 360) // 45)]


def dxy_km(lat0, lon0, lat, lon):
    """Desplazamiento (este, norte) en km de (lat0, lon0) a (lat, lon), plano local."""
    dn = (lat - lat0) * 111.195
    de = (lon - lon0) * 111.195 * math.cos(math.radians((lat + lat0) / 2))
    return de, dn


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def tramo_a119(fecha_utc: str, source: str) -> str:
    """Tramos de calidad de la referencia (A119, CLAUDE.md del proyecto; docs/audit_s139/MAPA_BASES_MIROVA_V1.md §2).

    CONS: ene-feb (cobertura incompleta), desde marzo (sana).
    OCR: hasta 2026-06-13 (sin distancia / geometria mal calibrada), 2026-06-13 a 2026-08-05, desde 2026-08-06 (v30).
    """
    d = fecha_utc[:10]
    if source == "CONS":
        return "CONS_ene-feb" if d < "2026-03-01" else "CONS_desde-mar"
    if d < "2026-06-13":
        return "OCR_antes-0613"
    if d < "2026-08-06":
        return "OCR_0613-0805"
    return "OCR_desde-0806"
