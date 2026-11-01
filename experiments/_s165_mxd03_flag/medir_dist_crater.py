# -*- coding: utf-8 -*-
"""S165, Tarea 5 paso 1 del plan 2026-10-25-flag-mxd03-modis: ¿cuánto cambia la publicación MODIS si la distancia de la
etiqueta summit/far se mide desde el cráter y no desde el centro del volcán? Sin red, antes de tocar pipeline/ (A116).

POR QUÉ. `enable_modis_dist_desde_crater` cambia el `dist_km` de cada píxel anómalo, y con él `hotspot_dist_km` y el
`final_hotspot_dist_km` que decide summit/far cuando la fuente final es «eruption» (con K el Test 1 integrado y el ancla
honesta están apagados: las otras fuentes no leen esa distancia). El tablero publica sólo `summit`, así que una etiqueta
que cambia puede encender o apagar una publicación. Sin este número el flag no se enciende (A116).

QUÉ EMULA, record por record, sobre los records MODIS de data/mirova_equivalent/ de los 11 Tier A desde la marca de K en
los datos (2026-09-18, S155):
  * fuente «eruption»: nueva distancia = haversine(ancla de detección, final_hotspot) (el final_hotspot es el píxel
    más caliente, el mismo `anomaly_pixels[0]`; redondeado a 1e-5 grados, ~1 m);
  * etiqueta con `derivar_distance_class` (flag de cúmulo apagado, como producción) y la guarda A46 de store.py
    (summit con el cúmulo con magnitud fuera del inner pasa a far), las dos importadas, no copiadas;
  * otras fuentes: sin cambio.
LO QUE NO EMULA, declarado: la geocerca de store.py (`hotspot_dist_km` > radius_km, 25 km en los Tier A) y el filtro de
píxeles por distancia también leen el `dist_km` del píxel; se cuentan aparte los records cuyo píxel queda a menos de
1 km de ese borde con una de las dos mediciones, donde el resultado podría cambiar por esa vía.

PUBLICA = predicado del tablero ejecutado con node desde frontend/index.html (banco_paridad.correr_node). La etiqueta de
la referencia (alerta, negativo limpio) sale de banco_paridad con el snapshot del repo (sin red), y se cuenta en
pasadas y en noches de volcán (A94).

Uso: python experiments/_s165_mxd03_flag/medir_dist_crater.py [--desde 2026-09-18] [--hasta AAAA-MM-DD]
"""
import argparse
import collections
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import yaml  # noqa: E402

import banco_paridad as BP  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.process_modis import derivar_distance_class  # noqa: E402
from pipeline.scan_geometry import haversine_km  # noqa: E402


def guarda_a46(dc, rec, inner):
    """La guarda unidireccional de store.py (summit con cúmulo con magnitud fuera del inner -> far)."""
    pc = rec.get("primary_cluster") or {}
    if dc == "summit" and inner is not None and (pc.get("vrp_mw") or 0) > 0 \
            and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner:
        return "far"
    return dc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-09-18")
    ap.add_argument("--hasta", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    # Control positivo (P1, si estuviera roto lo vería): con el ancla corrida N km al norte, las etiquetas summit de
    # fuente «eruption» tienen que pasar a far y el conteo de cambios tiene que dejar de ser chico.
    ap.add_argument("--control-ancla-km", type=float, default=0.0)
    a = ap.parse_args(argv)
    ventana = (a.desde, a.hasta)
    volcanes = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    coords = BP._coords_por_volcan()
    inner_html = BP.inner_desde_html()

    filas, casos_hoy, casos_crater = [], [], []
    n_fuente = collections.Counter()
    for vol in BP.VOLS:
        v = volcanes[vol]
        ancla = get_detection_anchor(v)
        ancla = (ancla[0] + a.control_ancla_km / 111.0, ancla[1])
        inner = v.get("inner_radius_km")
        radio = v.get("radius_km")
        d = json.loads((BP.DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            if BP.bucket(r.get("sensor")) != "MODIS" or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if BP.es_pasada_diurna_descartada("MODIS", *coords[vol], dt):
                continue
            n_fuente[r.get("final_hotspot_source")] += 1
            r2 = copy.deepcopy(r)
            borde = False
            if r.get("final_hotspot_source") == "eruption" and r.get("final_hotspot_lat") is not None:
                nueva = float(haversine_km(ancla[0], ancla[1], r["final_hotspot_lat"], r["final_hotspot_lon"]))
                r2["final_hotspot_dist_km"] = round(nueva, 3)
                r2["distance_class"] = guarda_a46(
                    derivar_distance_class(nueva, (r.get("primary_cluster") or {}).get("centroid_dist_km"),
                                           inner, False), r, inner)
                vieja = r.get("hotspot_dist_km")
                borde = radio is not None and any(x is not None and abs(x - radio) < 1.0 for x in (vieja, nueva))
            filas.append({"vol": vol, "b": "MODIS", "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                          "fuente": r.get("final_hotspot_source"), "dc": r.get("distance_class"),
                          "dc2": r2.get("distance_class"), "borde_geocerca": borde,
                          "d_vieja": r.get("final_hotspot_dist_km"), "d_nueva": r2.get("final_hotspot_dist_km"),
                          "inner": inner, "pc_vrp": (r.get("primary_cluster") or {}).get("vrp_mw"),
                          "pc_cdist": (r.get("primary_cluster") or {}).get("centroid_dist_km")})
            for caso, rec in ((casos_hoy, r), (casos_crater, r2)):
                slim = {k: rec.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
                if rec.get("f5_core_vrp_mw") is None:
                    slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                              for p in (rec.get("anomaly_pixels") or [])]
                caso.append([slim, inner_html[vol]])

    pred_hoy, pred_crater = BP.correr_node(casos_hoy), BP.correr_node(casos_crater)
    for f, p0, p1 in zip(filas, pred_hoy, pred_crater):
        f["pub"], f["pub2"] = p0[4], p1[4]

    # Etiqueta de la referencia (snapshot del repo, sin red), con el mismo código que el banco de paridad.
    ref = BP.cargar_referencia_unificada(BP.SNAP_CONS, BP.SNAP_OCR)
    por_vb, noche_sensor, noche_volcan, _ = BP.indexar_referencia(ref, coords, ventana)
    BP.etiquetar(filas, por_vb, noche_sensor, noche_volcan)

    print(f"ventana {ventana[0]} a {ventana[1]} | records MODIS nocturnos de los 11 Tier A: {len(filas)}")
    print("fuente final:", dict(n_fuente))
    cambia_dc = [f for f in filas if f["dc"] != f["dc2"]]
    print(f"\netiqueta que cambia: {len(cambia_dc)}  ",
          dict(collections.Counter(f"{f['dc']}->{f['dc2']}" for f in cambia_dc)))
    for f in cambia_dc:
        print(f"   {f['vol']:20s} {f['dt']:%Y-%m-%d %H:%M} {f['dc']}->{f['dc2']} d {f['d_vieja']} -> {f['d_nueva']} "
              f"inner {f['inner']} | publica {f['pub']}->{f['pub2']} | ref {f['lab']}")
    cambia_pub = [f for f in filas if f["pub"] != f["pub2"]]
    print(f"\npublicación que cambia (pasadas): {len(cambia_pub)}  ",
          dict(collections.Counter((f"{f['pub']}->{f['pub2']}", f["lab"]) for f in cambia_pub)))
    noches = collections.defaultdict(lambda: [0, 0, set()])
    for f in filas:
        k = (f["vol"], f["noche"])
        noches[k][0] |= f["pub"]
        noches[k][1] |= f["pub2"]
        noches[k][2].add(f["lab"])
    cambia_noche = {k: v for k, v in noches.items() if v[0] != v[1]}
    print(f"noches de volcán cuya publicación cambia: {len(cambia_noche)} de {len(noches)}")
    for k, v in sorted(cambia_noche.items()):
        print(f"   {k[0]} {k[1]} publica {v[0]}->{v[1]} etiquetas {sorted(v[2])}")
    print(f"\nrecords con el píxel a menos de 1 km de la geocerca (radius_km), no emulado: "
          f"{sum(1 for f in filas if f['borde_geocerca'])}")
    # Control de instrumento (P2, instrumento muerto): con la distancia GUARDADA el emulador tiene que devolver la
    # etiqueta guardada en todos los records «eruption». Si no, el emulador no es el pipeline y el conteo no vale.
    erup = [f for f in filas if f["fuente"] == "eruption" and f["d_vieja"] is not None]
    ident = sum(1 for f in erup if guarda_a46(derivar_distance_class(f["d_vieja"], f["pc_cdist"], f["inner"], False),
                                              {"primary_cluster": {"vrp_mw": f["pc_vrp"],
                                                                   "centroid_dist_km": f["pc_cdist"]}},
                                              f["inner"]) == f["dc"])
    print(f"control de identidad: con la distancia guardada el emulador da la etiqueta guardada en {ident} de "
          f"{len(erup)} records «eruption»")
    return 0 if ident == len(erup) else 1


if __name__ == "__main__":
    sys.exit(main())
