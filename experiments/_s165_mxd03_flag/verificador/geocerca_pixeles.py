# -*- coding: utf-8 -*-
"""Verificador S165 (V165): segundo consumidor del `dist_km` del píxel anómalo que el flag
ENABLE_MODIS_DIST_DESDE_CRATER alcanza y que ni la prueba de cableado ni la medición previa emulan:
`store._filter_pixels_by_distance(record, radius_km)` (activo en producción, ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True)
y la geocerca `hotspot_dist_km > radius_km`.

Mide, sobre los records MODIS de data/mirova_equivalent/ de los 11 Tier A en una ventana, cuántos píxeles anómalos
guardados cambian de lado de la cerca `radius_km` si su distancia se mide desde el ancla de detección (cráter) en vez
del centro del volcán, y cuántos records y publicaciones (summit con vrp>0, proxy; no es el predicado node) toca.

Límite declarado: los anomaly_pixels guardados ya pasaron por el filtro (los que quedaron fuera están en
`discarded_anomaly_pixels` sólo cuando hubo descarte total). Así que mide dos direcciones:
  (a) píxel guardado (dentro con la distancia desde el centro) que quedaría FUERA con la distancia desde el cráter;
  (b) píxel descartado (en discarded_anomaly_pixels) que quedaría DENTRO.
Uso: python geocerca_pixeles.py <raiz_repo> [desde] [hasta]
"""
import json
import sys
from pathlib import Path

RAIZ = Path(sys.argv[1]).resolve()
DESDE = sys.argv[2] if len(sys.argv) > 2 else "2026-03-01"
HASTA = sys.argv[3] if len(sys.argv) > 3 else "2026-10-27"
sys.path.insert(0, str(RAIZ))
import yaml  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.scan_geometry import haversine_km  # noqa: E402

VOLS = ["Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "Tupungatito", "Copahue", "PuyehueCordonCaulle"]
volcanes = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
tot = {"records": 0, "con_pixeles": 0, "pixeles": 0, "pix_salen": 0, "rec_salen": 0, "rec_salen_summit_vrp": 0,
       "pix_entran": 0, "rec_entran": 0, "max_abs_delta_km": 0.0, "pix_cerca_1km": 0}
casos = []
for vol in VOLS:
    v = volcanes[vol]
    ancla = get_detection_anchor(v)
    radio = float(v["radius_km"])
    d = json.loads((RAIZ / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
    for r in d["records"]:
        if not str(r.get("sensor", "")).startswith("MODIS") or not (DESDE <= r.get("datetime_utc", "")[:10] <= HASTA):
            continue
        tot["records"] += 1
        pix = r.get("anomaly_pixels") or []
        if pix:
            tot["con_pixeles"] += 1
        salen = 0
        for p in pix:
            tot["pixeles"] += 1
            dc = float(haversine_km(ancla[0], ancla[1], p["lat"], p["lon"]))
            tot["max_abs_delta_km"] = max(tot["max_abs_delta_km"], abs(dc - p["dist_km"]))
            if abs(p["dist_km"] - radio) < 1.0 or abs(dc - radio) < 1.0:
                tot["pix_cerca_1km"] += 1
            if p["dist_km"] <= radio < dc:
                salen += 1
        if salen:
            tot["pix_salen"] += salen
            tot["rec_salen"] += 1
            if r.get("distance_class") == "summit" and (r.get("vrp_mw") or 0) > 0:
                tot["rec_salen_summit_vrp"] += 1
            casos.append((vol, r["datetime_utc"], "salen", salen, len(pix), r.get("distance_class"), r.get("vrp_mw")))
        entran = 0
        for p in r.get("discarded_anomaly_pixels") or []:
            dc = float(haversine_km(ancla[0], ancla[1], p["lat"], p["lon"]))
            if p["dist_km"] > radio >= dc:
                entran += 1
        if entran:
            tot["pix_entran"] += entran
            tot["rec_entran"] += 1
            casos.append((vol, r["datetime_utc"], "entran", entran, None, r.get("distance_class"), r.get("vrp_mw")))
print(f"ventana {DESDE} a {HASTA}, MODIS, 11 Tier A")
print(json.dumps(tot, ensure_ascii=False))
for c in casos:
    print("  ", c)
