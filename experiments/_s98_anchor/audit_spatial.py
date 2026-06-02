"""S98 — Auditoría ESPACIAL del fix del ancla de detección (A61).

Compara baseline (data/mirova_equivalent/, ancla = mirova_center) vs fix
(data/_s98_anchor/, ancla = cráter vent_lat) sobre la ventana mayo 2026.

Criterio central (A61, NO número-vs-número): recomputamos la distancia de la
UBICACIÓN de nuestra detección (primary_cluster.centroid_lat/lon) al CRÁTER
FÍSICO (vent_lat/lon de volcanoes.yaml), independiente del ancla con que se
reportó `centroid_dist_km`. Así "det→cráter" es comparable entre A y B.

Criterios de aceptación (docs/.../detection-anchor-crater-design.md):
- Tupungatito: mediana det→cráter baja de ~5.9 a <2 km.
- ratio magnitud hacia 0.5-2.0 (medido aparte si hay ground truth MIROVA).
- los 8 de offset chico: SIN cambio observable.
- recall (n_records con detección) NO cae.

Salida: escribe JSON a experiments/_s98_anchor/audit_spatial_result.json y un
resumen legible a stdout. Integridad (§0.5): los números salen del script, no
se transcriben a mano.
"""
import json
import math
import statistics as st
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]
WINDOW = ("2026-05-01", "2026-05-31")  # mayo (TIF + ground truth)

OFFSET_VOLS = ["Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"]
CONTROL_VOLS = ["Lascar", "Villarrica"]
SMALL_VOLS = ["Lastarria", "Isluga", "Copahue", "Chaiten", "Llaima", "NevadosDeChillan"]
ALL_VOLS = OFFSET_VOLS + CONTROL_VOLS + SMALL_VOLS


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _load_volcanoes():
    data = yaml.safe_load(open(_REPO / "volcanoes.yaml", encoding="utf-8"))
    return {v["name"]: v for v in data["volcanoes"]}


def _load_records(subdir, name):
    p = _REPO / "data" / subdir / f"{name}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding="utf-8"))
    recs = d if isinstance(d, list) else d.get("records", [])
    return recs


def _in_window(dt):
    if not dt:
        return False
    day = str(dt)[:10]
    return WINDOW[0] <= day <= WINDOW[1]


def _key(r):
    return (str(r.get("datetime_utc")), r.get("sensor"))


def _det_to_crater(r, vent_lat, vent_lon):
    """Distancia (km) de la UBICACIÓN de la detección al cráter físico.
    Usa el centroide del primary_cluster si tiene VRP>0; si no, final_hotspot.
    Devuelve (dist_km, vrp_mw, distance_class) o None si no hay detección."""
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    vrp = pc.get("vrp_mw", 0.0) or 0.0
    if clat is None or clon is None:
        clat, clon = r.get("final_hotspot_lat"), r.get("final_hotspot_lon")
    if clat is None or clon is None:
        return None
    d = _haversine_km(clat, clon, vent_lat, vent_lon)
    return (d, vrp, r.get("distance_class"))


def audit_volcano(name, vols):
    v = vols[name]
    vlat, vlon = v["vent_lat"], v["vent_lon"]
    base = _load_records("mirova_equivalent", name) or []
    fix = _load_records("_s98_anchor", name)
    out = {"volcano": name, "vent": [vlat, vlon],
           "mirova_center": [v.get("mirova_center_lat"), v.get("mirova_center_lon")],
           "fix_data_present": fix is not None}
    if fix is None:
        return out

    base_w = {_key(r): r for r in base if _in_window(r.get("datetime_utc"))}
    fix_w = {_key(r): r for r in fix if _in_window(r.get("datetime_utc"))}
    common = sorted(set(base_w) & set(fix_w))
    out["n_base_window"] = len(base_w)
    out["n_fix_window"] = len(fix_w)
    out["n_common"] = len(common)

    def _summ(recs_map, keys):
        dists, vrps, n_det, n_summit = [], [], 0, 0
        for k in keys:
            res = _det_to_crater(recs_map[k], vlat, vlon)
            if res is None:
                continue
            d, vrp, dclass = res
            if vrp > 0:
                n_det += 1
                dists.append(d)
                vrps.append(vrp)
            if dclass == "summit":
                n_summit += 1
        return {
            "n_detections_vrp_pos": n_det,
            "median_det_to_crater_km": round(st.median(dists), 3) if dists else None,
            "median_vrp_mw": round(st.median(vrps), 4) if vrps else None,
            "n_summit_class": n_summit,
        }

    out["baseline"] = _summ(base_w, common)
    out["fix"] = _summ(fix_w, common)
    # recall proxy: detecciones vrp>0 sobre los comunes
    return out


def main():
    vols = _load_volcanoes()
    results = []
    for name in ALL_VOLS:
        if name not in vols:
            continue
        results.append(audit_volcano(name, vols))

    outp = _REPO / "experiments" / "_s98_anchor" / "audit_spatial_result.json"
    json.dump(results, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # resumen legible
    lines = []
    lines.append(f"=== S98 audit espacial del ancla — ventana {WINDOW[0]}..{WINDOW[1]} ===")
    lines.append(f"{'volcano':<20} {'present':>7} {'common':>6} "
                 f"{'base_d2c':>9} {'fix_d2c':>9} {'base_det':>8} {'fix_det':>8} "
                 f"{'base_vrp':>9} {'fix_vrp':>9} {'base_sm':>7} {'fix_sm':>7}")
    for r in results:
        if not r.get("fix_data_present"):
            lines.append(f"{r['volcano']:<20} {'NO':>7}  (sin data _s98_anchor todavía)")
            continue
        b, f = r["baseline"], r["fix"]
        lines.append(
            f"{r['volcano']:<20} {'yes':>7} {r['n_common']:>6} "
            f"{str(b['median_det_to_crater_km']):>9} {str(f['median_det_to_crater_km']):>9} "
            f"{b['n_detections_vrp_pos']:>8} {f['n_detections_vrp_pos']:>8} "
            f"{str(b['median_vrp_mw']):>9} {str(f['median_vrp_mw']):>9} "
            f"{b['n_summit_class']:>7} {f['n_summit_class']:>7}")
    lines.append("")
    lines.append("d2c = mediana det→cráter (km, recomputada al cráter físico). "
                 "det = n detecciones vrp>0. vrp = mediana pc.vrp_mw. sm = n distance_class=summit.")
    lines.append("CRITERIO: Tupungatito fix_d2c < 2.0 (baseline ~5.9); offset chico sin cambio; det no cae.")
    txt = "\n".join(lines)
    print(txt)
    (_REPO / "experiments" / "_s98_anchor" / "audit_spatial_summary.txt").write_text(
        txt, encoding="utf-8")


if __name__ == "__main__":
    main()
