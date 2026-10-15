# -*- coding: utf-8 -*-
"""Piezas comunes del sustrato y del evaluador del A/B `vrp_max` contra `vent_anchored` (tarea 1.4 del loop).

POR QUE UN MODULO COMUN. La leccion del verificador de D22 fue que las reglas del pre-registro quedaron sin un
script que las implementara y que el veredicto salio impreso con otra vara. Aca vive UNA sola definicion de
cada cosa que el pre-registro nombra (pasada, etiqueta, alerta protegida, tramo de calidad A119, publicar,
distancia al crater) y la usan los dos scripts. Si una definicion cambia, cambia para los dos.

ORIGEN DE CADA DEFINICION (no se reescribe, se importa):
  * etiquetas por pasada (pos, far_ref, neg_limpio, sin_info) y "publica" = predicado del tablero ejecutado con
    node: `scripts/banco_paridad.py` (indexar_referencia, parear, etiquetar, correr_node, CAMPOS_JS).
  * alerta protegida, lecturas A y B: `scripts/clase_mirova.py::alerta_protegida` (docs/S151_CRITERIO_CLASE_MIROVA.md).
  * referencia: `scripts/referencia_mirova_unificada.py::cargar_referencia_unificada` (union historica, tarea 0.1).
  * tramos A119: hitos de `scripts/calidad_referencia_mirova.py` y A104 (#535, 2026-08-28 23:00 UTC).
  * distancia: SIEMPRE desde el ancla de deteccion del pipeline (`pipeline.geo_utils.get_detection_anchor`,
    el crater), nunca desde las coordenadas de catalogo (`process_viirs.py:754` mide `dist` y
    `anomaly_pixels[].dist_km` desde el catalogo; AUDITOR_F1_PENDIENTES).
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import yaml  # noqa: E402

import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

VOLS = bp.VOLS
BUCKETS = bp.BUCKETS
TEST1_ROI_KM = 3.0  # pipeline.profile.TEST1_ROI_KM en mirova_equivalent (leido de pipeline.profile, 2026-10-14)

# Tramos de calidad de la referencia (A119) y cambio de regimen #535 (A104). Fechas de NOCHE (UTC).
TRAMOS = [
    ("T0_mar", "2026-03-01", "2026-03-31", "tabla decide; VIIRS por pasada no comparable con abril en adelante"),
    ("T1_abr_jun12", "2026-04-01", "2026-06-12", "tabla decide; OCR con geometria sin calibrar, se informa aparte"),
    ("T2_jun13_ago28", "2026-06-13", "2026-08-28", "tabla y OCR deciden; antes de #535"),
    ("T3_ago29_oct08", "2026-08-29", "2026-10-08", "despues de #535; filas solo OCR de Suomi NPP con distancia de otra pasada"),
    ("T4_oct09", "2026-10-09", "2099-12-31", "despues del arreglo Mirova-v1#20"),
]


def tramo(noche: str) -> str:
    for nombre, a, b, _ in TRAMOS:
        if a <= noche <= b:
            return nombre
    return "fuera"


def ocr_decide(noche: str) -> bool:
    """A119: antes del 2026-06-13 la etiqueta positiva que decide es la de la tabla sola."""
    return noche >= "2026-06-13"


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def anclas_y_inner():
    """Ancla de deteccion (crater) por volcan, leida igual que run_pipeline, e inner_radius del yaml y del html."""
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        vs = {v["name"]: v for v in yaml.safe_load(fh)["volcanoes"]}
    ancla = {v: get_detection_anchor(vs[v]) for v in VOLS}
    inner_yaml = {v: float(vs[v]["inner_radius_km"]) for v in VOLS}
    inner_html = bp.inner_desde_html()
    return ancla, inner_yaml, inner_html


def cargar_records(data_dir: Path, ventana, coords):
    """Records de los 11 Tier A en la ventana (fechas de noche, inclusive). Sin filtro diurno: se marca aparte."""
    out = []
    for vol in VOLS:
        p = Path(data_dir) / f"{vol}.json"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            dtu = r.get("datetime_utc", "")
            if b is None or not (ventana[0] <= dtu[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(dtu, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            lat, lon = coords[vol]
            out.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                        "noche_ok": not es_pasada_diurna_descartada(b, lat, lon, dt), "rec": r})
    return out


def clave(x):
    return (x["vol"], x["rec"].get("sensor"), x["rec"].get("datetime_utc"))


def predicado(lista_recs, inner_html, campo="rec"):
    """Predicado del tablero (node sobre frontend/index.html), igual que banco_paridad.cargar_nuestros."""
    return [p for p, _ in predicado_completo(lista_recs, inner_html, campo)]


def predicado_completo(lista_recs, inner_html, campo="rec"):
    """(publica, magnitud que muestra el tablero) por record, del mismo node que banco_paridad."""
    casos = []
    for x in lista_recs:
        r = x[campo]
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner_html[x["vol"]]])
    pred = bp.correr_node(casos) if casos else []
    return [(int(p[4]), float(p[3] or 0.0)) for p in pred]


def etiquetar(recs_noche, filas, coords, ventana):
    """Etiqueta banco_paridad + protegida A y B + si la positiva decide (A119). Muta cada x."""
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
    tmp = [{"vol": x["vol"], "b": x["b"], "dt": x["dt"], "noche": x["noche"]} for x in recs_noche]
    bp.etiquetar(tmp, por_vb, noche_sensor, noche_volcan)
    for x, t in zip(recs_noche, tmp):
        x["lab"] = t["lab"]
        x["dist_ref"] = t["dist_ref"]
        fr = bp.parear(por_vb.get((x["vol"], x["b"]), []), x["dt"])
        x["vrp_ref"] = max([f["vrp_mw"] or 0 for f in fr if f["tipo"] != "RUTINA"], default=None)
        x["prot_A"] = any(alerta_protegida(f, lectura="A") for f in fr)
        x["prot_B"] = any(alerta_protegida(f, lectura="B") for f in fr)
        x["solo_ocr"] = (x["lab"] == "pos" and not any(bp.es_alerta(f["tipo"]) and f["source"] == "CONS" for f in fr))
        # A119: una positiva que viene solo del OCR no decide antes del 2026-06-13 (geometria sin calibrar), ni
        # en Suomi NPP antes del 2026-10-09 (distancia y clase de otra pasada; hito de calidad_referencia_mirova).
        snpp = "SNPP" in (x.get("rec", {}).get("sensor") or x.get("sensor") or "")
        x["decide"] = not (x["solo_ocr"] and (not ocr_decide(x["noche"]) or (snpp and x["noche"] < "2026-10-09")))
        x["tramo"] = tramo(x["noche"])
    return por_vb, n_ref
