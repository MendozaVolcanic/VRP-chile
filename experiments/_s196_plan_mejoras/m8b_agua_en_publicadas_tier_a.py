# -*- coding: utf-8 -*-
"""Medición previa de MEJ-8 en los 11 Tier A (plan S196): ¿el agua entra a lo que el tablero publica?

POR QUÉ. S193 (`experiments/_s193_lagos/resumen.txt`) contó el agua por el píxel más caliente: en los Tier A el pico
sobre agua es raro y casi siempre lejos del cráter (Láscar 5, Villarrica 5, Chaitén 4 pasadas, a 10 a 25 km), así que
el tablero, que publica sólo la cumbre, no lo mostraría. Pero la vía publica como VRP la SUMA de todos los alertados
de la escena (D32): un píxel tibio de un lago a 20 km que alerta la misma pasada que la cumbre suma sus MW a la
potencia publicada del volcán. Ése es el efecto de una máscara de agua en el laboratorio de los Tier A: no quita
publicaciones, corrige magnitudes. Este script lo cuenta.

Aproximación (más gruesa que S193): un alertado está «sobre agua» si su centro cae dentro de un polígono de
`frontend/agua/<Volcán>.geojson` (JRC GSW v1.4, ocurrencia >= 50 %, `scripts/generar_capa_agua.py`); no mide la fracción
de la celda. `anomaly_pixels` trae hasta 100 alertados por record (tope anti-bloat), y su `vrp_mw` por píxel es el
que guardó la vía. Sólo pasadas nocturnas que el tablero publica (`banco_paridad.correr_node`), 2026-03-01 a 2026-11-22.

Uso: python experiments/_s196_plan_mejoras/m8b_agua_en_publicadas_tier_a.py
"""
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402

DESDE, HASTA = "2026-03-01", "2026-11-22"


def main():
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    print("ventana %s a %s, data/mirova_equivalent, predicado del tablero, alertado sobre agua = centro dentro de un "
          "polígono de frontend/agua (JRC >= 50 %%)" % (DESDE, HASTA))
    print("%-20s %6s %8s %10s %12s %14s" % ("volcán", "pub", "con_agua", "MW_agua", "MW_pub_tot", "máx %MW agua"))
    tot = collections.Counter()
    for vol in bp.VOLS:
        g = json.loads((ROOT / "frontend" / "agua" / ("%s.geojson" % vol)).read_text(encoding="utf-8"))
        geoms = [shape(f["geometry"]) for f in g["features"]]
        arbol = STRtree(geoms)
        recs, casos = [], []
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b is None or not (DESDE <= t[:10] <= HASTA):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=timezone.utc)):
                continue
            recs.append(r)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
        n_pub = n_agua = 0
        mw_agua = mw_tot = 0.0
        peor = 0.0
        for r, p in zip(recs, bp.correr_node(casos) if casos else []):
            if not p[4]:
                continue
            n_pub += 1
            mw_tot += p[3]
            agua = 0.0
            for px in r.get("anomaly_pixels") or []:
                if px.get("lat") is None:
                    continue
                pt = Point(px["lon"], px["lat"])
                if any(geoms[i].contains(pt) for i in arbol.query(pt)):
                    agua += max(px.get("vrp_mw") or 0.0, 0.0)
            if agua > 0:
                n_agua += 1
                mw_agua += agua
                if p[3] > 0:
                    peor = max(peor, 100.0 * agua / p[3])
        tot.update(pub=n_pub, agua=n_agua)
        tot["mw_agua"] += mw_agua
        tot["mw_tot"] += mw_tot
        print("%-20s %6d %8d %10.2f %12.1f %13.0f%%" % (vol, n_pub, n_agua, mw_agua, mw_tot, peor))
    print("%-20s %6d %8d %10.2f %12.1f" % ("TOTAL", tot["pub"], tot["agua"], tot["mw_agua"], tot["mw_tot"]))

    # Control del instrumento (A116): un cero sólo vale si el mismo cálculo da distinto de cero donde hay agua. Los dos
    # volcanes con lago de S193, en la historia de la vía de los 34, sin predicado del tablero (los 34 no tienen
    # distance_class): records con vrp_mw > 0 y algún alertado dentro de un polígono.
    print("\nCONTROL: data/historia_34 (la vía), records nocturnos con vrp_mw > 0, %s a 2026-11-02" % DESDE)
    for vol in ("LagunaDelMaule", "CarranLosVenados"):
        g = json.loads((ROOT / "frontend" / "agua" / ("%s.geojson" % vol)).read_text(encoding="utf-8"))
        geoms = [shape(f["geometry"]) for f in g["features"]]
        arbol = STRtree(geoms)
        lat, lon = coords[vol]
        n = con = 0
        for r in json.loads((ROOT / "data" / "historia_34" / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            t = r.get("datetime_utc", "")
            b = bp.bucket(r.get("sensor"))
            if b is None or not (DESDE <= t[:10] <= "2026-11-02") or not (r.get("vrp_mw") or 0) > 0:
                continue
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=timezone.utc)):
                continue
            n += 1
            if any(any(geoms[i].contains(Point(px["lon"], px["lat"])) for i in arbol.query(Point(px["lon"], px["lat"])))
                   for px in (r.get("anomaly_pixels") or []) if px.get("lat") is not None):
                con += 1
        print("  %-20s records con detección %4d; con algún alertado sobre agua %4d" % (vol, n, con))


if __name__ == "__main__":
    main()
