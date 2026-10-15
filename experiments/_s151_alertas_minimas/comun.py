# -*- coding: utf-8 -*-
"""Piezas comunes del estudio D (tarea 1.12 del loop): pasadas de alerta de la referencia unificada.

Una PASADA es (volcan, sensor, hora al minuto), igual que `scripts/clase_mirova.py::clave_pasada`. Su VRP es
el de la fila de alerta del consolidado si existe, si no el del OCR: el mismo orden que usa el evaluador del
A/B (`experiments/_s146_ab_sin_test1/evaluar.py::anotar_vrp_mirova`), para que el umbral corte las mismas
pasadas que el evaluador ve.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for p in (RAIZ, RAIZ / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402

UMBRAL_MINIMA_MW = 0.05
TIPOS_ALERTA = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")

# Tramos de calidad de la referencia (A119, scripts/calidad_referencia_mirova.py HITOS).
TRAMOS = [
    ("T0 hasta 02-28 (tabla incompleta en enero, OCR inestable)", "0000", "2026-03-01"),
    ("T1 03-01 a 06-12 (tabla sana; OCR sin geometria calibrada)", "2026-03-01", "2026-06-13"),
    ("T2 06-13 a 08-05 (OCR con distancia medida)", "2026-06-13", "2026-08-06"),
    ("T3 08-06 en adelante (OCR V30, lee el banner)", "2026-08-06", "9999"),
]


def tramo(fecha: str) -> str:
    for nombre, a, b in TRAMOS:
        if a <= fecha[:10] < b:
            return nombre
    raise ValueError(fecha)


def pasadas_de_alerta(filas=None) -> dict:
    """{(volcan, sensor, minuto): {vrp, source_vrp, solo_ocr, nocturna}} para toda pasada con fila de alerta."""
    filas = cargar_referencia_unificada() if filas is None else filas
    coords = _coords_por_volcan()
    por = {}
    for f in filas:
        if f["tipo"] not in TIPOS_ALERTA or f["vrp_mw"] is None:
            continue
        k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
        por.setdefault(k, []).append(f)
    out = {}
    for k, fs in por.items():
        fs.sort(key=lambda f: f["source"] != "CONS")
        dt = datetime.strptime(fs[0]["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[k[0]]
        out[k] = {"vrp": fs[0]["vrp_mw"], "source_vrp": fs[0]["source"],
                  "solo_ocr": all(f["source"] == "OCR" for f in fs),
                  "nocturna": not es_pasada_diurna_descartada(k[1], lat, lon, dt)}
    return out
