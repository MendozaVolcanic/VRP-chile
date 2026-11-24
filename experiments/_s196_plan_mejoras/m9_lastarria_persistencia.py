# -*- coding: utf-8 -*-
"""Medición previa de la mejora 9 del plan S196: ¿la persistencia en el lugar puede servir de vara en Lastarria?

POR QUÉ. Lastarria no tiene serie en NHI-v1, y su calor es de fumarolas de baja temperatura, que SWIR ve mal aunque la
tuviera. La vara que queda sin pedirle nada a nadie es la persistencia (diseño S147 §7.3): un campo fumarólico está en
el mismo lugar noche tras noche; el ruido del detector (un píxel que cruza el umbral por azar) cae en cualquier parte de
la ventana. Si las publicaciones de Lastarria ya caen más juntas que posiciones sorteadas en la misma zona, la
persistencia tiene poder ahí y sirve para juzgar el laboratorio; si no, hace falta otra vara (OVDAS o TIR de Landsat).

Qué hace, sin reprocesar: toma las pasadas nocturnas que el tablero publica (`banco_paridad.correr_node`) de
`data/mirova_equivalent/` para un volcán, por familia de sensor; para cada publicación mira si alguna publicación de
las 3 noches previas (cualquier sensor) cayó a 1 km o menos; compara esa fracción con la misma cuenta cuando cada
posición se reemplaza por un punto sorteado uniforme dentro del disco `inner_radius_km` (200 sorteos, semilla fija).
Corre también un volcán de control con foco conocido y persistente (Villarrica, lago de lava) para ver que el
instrumento puede dar distinto del sorteo.

Control de que la persistencia no sea sólo «fuente fija»: el mismo cálculo sobre volcanes de los 34 de la sombra
(`data/historia_34/`, la vía) con el mismo inner que Lastarria. Si también persisten, la persistencia dice «algo fijo
en el lugar» (una ladera, un borde de nieve o el cuantizado de la grilla, D15) y no «calor volcánico».

Uso: python experiments/_s196_plan_mejoras/m9_lastarria_persistencia.py [--volcanes Lastarria,Villarrica]
     python experiments/_s196_plan_mejoras/m9_lastarria_persistencia.py --simple --hasta 2026-11-02 --volcanes Lastarria
     python experiments/_s196_plan_mejoras/m9_lastarria_persistencia.py --simple --data data/historia_34 --inner-km 3
            --volcanes Parinacota,Taapaca,NevadoDeLongavi,Tinguiririca --hasta 2026-11-02   (una sola línea)
"""
import argparse
import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402

RADIO_KM = 1.0
NOCHES = 3
N_SORTEOS = 200


def publicadas(vol, desde, hasta, coords, inner, data, simple=False):
    """simple=True: publica si vrp_mw > 0 y final_hotspot_dist_km <= inner. Los 34 no tienen `distance_class` (no
    tienen inner propio), así que el predicado del tablero no los publica nunca; el simple es el mismo para todos y
    permite comparar Lastarria con los controles."""
    recs, casos = [], []
    for r in json.loads((data / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        t = r.get("datetime_utc", "")
        if b is None or not (desde <= t[:10] <= hasta):
            continue
        try:
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        lat, lon = coords[vol]
        if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=timezone.utc)):
            continue
        recs.append({"b": b, "dt": dt, "lat": r.get("final_hotspot_lat"), "lon": r.get("final_hotspot_lon"),
                     "simple": (r.get("vrp_mw") or 0) > 0 and (r.get("final_hotspot_dist_km") is not None)
                     and r["final_hotspot_dist_km"] <= inner[vol]})
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner[vol]])
    if simple:
        return [r for r in recs if r["simple"] and r["lat"] is not None]
    out = []
    for rec, p in zip(recs, bp.correr_node(casos)):
        if p[4] and rec["lat"] is not None:
            out.append(rec)
    return out


def fraccion_persistente(pubs):
    pubs = sorted(pubs, key=lambda r: r["dt"])
    si = n = 0
    for i, r in enumerate(pubs):
        noche = r["dt"].date()
        previas = [x for x in pubs[:i] if timedelta(days=1) <= noche - x["dt"].date() <= timedelta(days=NOCHES)]
        if not previas:
            continue
        n += 1
        if any(bp._hav_km(r["lat"], r["lon"], x["lat"], x["lon"]) <= RADIO_KM for x in previas):
            si += 1
    return si, n


def sortear(pubs, lat0, lon0, radio_km, rng):
    out = []
    for r in pubs:
        rr = radio_km * math.sqrt(rng.random())
        th = 2 * math.pi * rng.random()
        out.append(dict(r, lat=lat0 + rr * math.cos(th) / 111.0,
                        lon=lon0 + rr * math.sin(th) / (111.0 * math.cos(math.radians(lat0)))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcanes", default="Lastarria,Villarrica")
    ap.add_argument("--desde", default="2026-03-01")
    ap.add_argument("--hasta", default="2026-11-22")
    ap.add_argument("--data", default=str(bp.DATA), help="carpeta de JSON por volcán (por defecto la de producción)")
    ap.add_argument("--inner-km", type=float, default=None,
                    help="radio inner para volcanes que no están en frontend/index.html (los 34): mismo predicado")
    ap.add_argument("--simple", action="store_true", help="predicado simple (vrp > 0 y a <= inner del vent)")
    a = ap.parse_args()
    import yaml
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    for nombre, v in vy.items():
        coords.setdefault(nombre, (v["lat"], v["lon"]))
        if a.inner_km is not None:
            inner.setdefault(nombre, a.inner_km)
    print("datos: %s; predicado: %s" % (a.data, "simple (vrp > 0 y <= inner)" if a.simple else "tablero"))
    print("ventana %s a %s; persistencia: otra publicación a <= %.1f km en las %d noches previas; %d sorteos uniformes "
          "en el disco inner centrado en el vent" % (a.desde, a.hasta, RADIO_KM, NOCHES, N_SORTEOS))
    for vol in a.volcanes.split(","):
        pubs = publicadas(vol, a.desde, a.hasta, coords, inner, Path(a.data), a.simple)
        v = vy[vol]
        lat0, lon0 = v.get("vent_lat") or v["lat"], v.get("vent_lon") or v["lon"]
        por_b = {b: sum(1 for r in pubs if r["b"] == b) for b in bp.BUCKETS}
        si, n = fraccion_persistente(pubs)
        rng = random.Random(196)
        nulos = []
        for _ in range(N_SORTEOS):
            s, m = fraccion_persistente(sortear(pubs, lat0, lon0, inner[vol], rng))
            nulos.append(s / m if m else float("nan"))
        nulos.sort()
        obs = si / n if n else float("nan")
        p = sum(1 for x in nulos if x >= obs) / len(nulos)
        noches = len({r["dt"].date() for r in pubs})
        print("\n%s (inner %.0f km): %d publicaciones nocturnas en %d noches %s" % (vol, inner[vol], len(pubs), noches, por_b))
        print("  con publicación en las %d noches previas: %d; de ellas a <= %.1f km: %d (%.0f %%)" % (
            NOCHES, n, RADIO_KM, si, 100 * obs if n else float("nan")))
        print("  sorteo: mediana %.0f %%, percentil 95 %.0f %%; fracción de sorteos >= observado: %.3f" % (
            100 * nulos[len(nulos) // 2], 100 * nulos[int(0.95 * len(nulos))], p))


if __name__ == "__main__":
    main()
