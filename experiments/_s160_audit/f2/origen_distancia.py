#!/usr/bin/env python
"""El mismo punto medido desde dos orígenes: centro del volcán (volcanoes.yaml lat/lon) y cráter
(vent_lat/vent_lon). El `inner_radius_km` se aplica a distancias que en el pipeline salen del
cráter (clustering.py:104, `centroid_dist_km`) y en `anomaly_pixels[].dist_km` salen del centro
(process_viirs.py:1530, process_viirs_mod.py:1075, process_modis.py:1143, `dist` de
haversine(volcano_lat, ...)). Acá se toma el centroide publicado del cúmulo y se mide desde los dos
orígenes: cuántos records cambiarían de clase (summit/far) si el inner se aplicara a la distancia
desde el centro. Además mide la VRE del tablero: records por volcán y día en la ventana K, contra
las 6 h por record que supone frontend/index.html:2490.

Pregunta 1: si los dos orígenes coincidieran, la fracción sería 0 en todos los volcanes (control
negativo: Copahue, Llaima, Lastarria, Isluga, Chillán tienen centro = cráter en el yaml). Control
positivo: PCC, con 7,58 km entre centro y cráter e inner de 20 km, tiene que mostrar cambios.
Pregunta 2: n se imprime; 0 pares es SIN DATO.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
DATA = RAIZ / "data" / "mirova_equivalent"
K_DESDE = "2026-09-18 00:00"


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    y = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vols = {v["name"]: v for v in (y["volcanoes"] if isinstance(y, dict) else y)}
    c = Counter()
    dias = defaultdict(set)
    recs_k = Counter()
    out = []
    for fp in sorted(DATA.glob("*.json")):
        vol = fp.stem
        v = vols.get(vol)
        if not v or v.get("inner_radius_km") is None:
            continue
        inner = v["inner_radius_km"]
        vlat, vlon = v["vent_lat"] if v.get("vent_lat") is not None else v["lat"], v["vent_lon"] if v.get("vent_lon") is not None else v["lon"]
        d = json.load(open(fp, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        for r in recs:
            dt = r.get("datetime_utc") or ""
            if dt >= K_DESDE:
                dias[vol].add(dt[:10])
                recs_k[vol] += 1
            pc = r.get("primary_cluster") or {}
            if not pc.get("vrp_mw") or pc.get("centroid_lat") is None:
                continue
            d_vent = hav(pc["centroid_lat"], pc["centroid_lon"], vlat, vlon)
            d_cen = hav(pc["centroid_lat"], pc["centroid_lon"], v["lat"], v["lon"])
            for w in ["todo"] + (["K"] if dt >= K_DESDE else []):
                c[(w, vol, "pares")] += 1
                if abs(d_vent - (pc.get("centroid_dist_km") or d_vent)) > 0.05:
                    c[(w, vol, "centroid_dist_km no es desde el crater (>50 m)")] += 1
                if (d_vent <= inner) != (d_cen <= inner):
                    c[(w, vol, "clase cambia centro vs crater")] += 1
                    if r.get("distance_class") == "summit" and d_cen > inner:
                        c[(w, vol, "summit hoy, far desde el centro")] += 1
                    if r.get("distance_class") != "summit" and d_cen <= inner:
                        c[(w, vol, "far hoy, summit desde el centro")] += 1
    lineas = ["== clase summit/far del centroide publicado, inner aplicado desde el crater (hoy) y desde el centro"]
    for w in ("K", "todo"):
        lineas.append(f"-- ventana {w}")
        for vol in sorted(vols):
            n = c[(w, vol, "pares")]
            if not n:
                continue
            resto = {k[2]: v for k, v in c.items() if k[0] == w and k[1] == vol and k[2] != "pares"}
            lineas.append(f"  {vol:22s} pares={n:5d} dist_centro_crater={hav(vols[vol]['lat'], vols[vol]['lon'], vols[vol].get('vent_lat', vols[vol]['lat']), vols[vol].get('vent_lon', vols[vol]['lon'])):.2f} km  {resto}")
    lineas.append("== VRE del tablero: records por volcan y dia en la ventana K (index.html:2490 supone 6 h por record)")
    tot_r = tot_d = 0
    for vol in sorted(dias):
        nr, nd = recs_k[vol], len(dias[vol])
        tot_r += nr
        tot_d += nd
        lineas.append(f"  {vol:22s} records={nr:5d} dias={nd:3d} records/dia={nr / nd:5.2f}  horas integradas/dia={6 * nr / nd:6.1f}")
    lineas.append(f"  TOTAL                  records={tot_r} dias-volcan={tot_d} records/dia={tot_r / tot_d:.2f} horas/dia={6 * tot_r / tot_d:.1f}")
    txt = "\n".join(lineas)
    print(txt)
    Path(__file__).with_name("origen_distancia_salida.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
