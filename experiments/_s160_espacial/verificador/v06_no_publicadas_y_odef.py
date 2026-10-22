# -*- coding: utf-8 -*-
"""V06 (verificador S160 espacial): afirmaciones 2 (las 58 no publicadas) y 3 (E-01, O-def contra O-sens).

Parte A, afirmacion 2: describe, desde el JSON de produccion (no desde el CSV 03), cada alerta pareada no publicada que 03
clasifica como perdida_geometria (cualquier subclase): n de pixeles del cumulo primario, su VRP sin redondear, distancia
del cumulo y del pixel anomalo MAS CERCANO al vent, y si el cumulo elegido es el pixel cercano o otro. Prueba el enunciado
"58 cumulos de 1 pixel en el crater con 0,0 MW" y "0 de 876 por etiqueta, radio o eleccion de cumulo".
  P1: la subclase "cumulo_elegido_lejos_o_0MW" y "far" existen en el clasificador de 03; si alguna fila cae ahi, el
      instrumento PUEDE dar distinto de cero. P2: n por subclase impreso.
Parte B, afirmacion 3: cuenta directamente en el JSON crudo del censo, para las pasadas pos de Tupungatito y PCC, que dice
el oraculo con la caja por defecto (geo_linear): npix, motivo_vacio, n_abs, n_p1, n_p2; y con el anillo sensible. Control
positivo: Lascar e Isluga con la caja por defecto deben marcar sus alertas.
Ventanas: A, la de 03 (nocturno 2026-01-10 a 2026-10-21); B, la del censo (V750 nocturno 2026-04-01 a 2026-10-21).
"""
from __future__ import annotations

import csv
import glob
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Geod

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent
G = Geod(ellps="WGS84")
VENT = {"PuyehueCordonCaulle": (-40.525499, -72.146137), "Tupungatito": (-33.389044, -69.826374), "Isluga": (-19.15, -68.83)}
INNER = {"PuyehueCordonCaulle": 20.0, "Tupungatito": 7.0, "Isluga": 5.0}


def dkm(a, b):
    return G.inv(a[1], a[0], b[1], b[0])[2] / 1000


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    return "VIIRS375" if s.startswith("VIIRS") else None


def parte_a():
    pas = list(csv.DictReader(open(AUD / "03_pareo_geometria_pasadas.csv", encoding="utf-8")))
    pos = [r for r in pas if r["lab"] == "pos"]
    print(f"A. alertas pareadas (lab pos) en 03: {len(pos)}; clases {dict(Counter(r['clase'] for r in pos))}")
    recs = {}
    for v in VENT:
        for r in json.load(open(AUD / "data" / f"{v}.json", encoding="utf-8"))["records"]:
            recs[(v, r["datetime_utc"], bucket(r.get("sensor")))] = r
    geo = [r for r in pos if r["clase"].startswith("perdida_geometria")]
    print(f"   perdidas por geometria (todas las subclases): {len(geo)}; {dict(Counter(r['clase'] for r in geo))}")
    filas = []
    tipo = Counter()
    for r in geo:
        rec = recs[(r["vol"], r["hora"], r["b"])]
        pc = rec.get("primary_cluster") or {}
        ap = [x for x in rec.get("anomaly_pixels") or [] if x.get("lat") is not None]
        v = r["vol"]
        dpc = dkm((pc["centroid_lat"], pc["centroid_lon"]), VENT[v]) if pc.get("centroid_lat") is not None else None
        cerca = sorted(ap, key=lambda x: dkm((x["lat"], x["lon"]), VENT[v]))
        dmin = dkm((cerca[0]["lat"], cerca[0]["lon"]), VENT[v]) if cerca else None
        vrp_cerca = [x.get("vrp_mw") for x in ap if dkm((x["lat"], x["lon"]), VENT[v]) <= INNER[v]]
        es_1px_crater_0 = (pc.get("n_pixels") == 1 and (pc.get("vrp_mw") or 0) == 0 and dpc is not None and dpc <= 1.5)
        cat = ("1px, <=1,5 km del vent, pc 0 MW" if es_1px_crater_0 else
               f"pc n={pc.get('n_pixels')}, d_vent {dpc:.2f} km, pc vrp {pc.get('vrp_mw')}, dc {rec.get('distance_class')}")
        tipo["cumple" if es_1px_crater_0 else "NO cumple"] += 1
        filas.append((r["vol"], r["b"], r["hora"], r["clase"], pc.get("n_pixels"), pc.get("vrp_mw"), None if dpc is None else round(dpc, 2),
                      rec.get("distance_class"), None if dmin is None else round(dmin, 2), vrp_cerca, r["mir_vrp"], r["mir_src"]))
        if not es_1px_crater_0:
            print(f"     NO cumple '1 pixel en el crater con 0,0 MW': {r['vol']} {r['b']} {r['hora']} [{r['clase']}] {cat}; "
                  f"pixel anomalo mas cercano al vent a {dmin:.2f} km; VRP de pixeles dentro del inner {vrp_cerca}; MIROVA {r['mir_vrp']} MW [{r['mir_src']}]")
    print(f"   de las {len(geo)}: {dict(tipo)}")
    # VRP exacto del cumulo en las que si cumplen
    vals = Counter(f[5] for f in filas)
    print(f"   valores exactos de pc.vrp_mw en esas {len(geo)} filas: {dict(vals)}")
    with open(AQUI / "v06_perdidas_geometria.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["vol", "sensor", "hora", "clase03", "pc_n", "pc_vrp_mw", "pc_d_vent_km", "dc", "ap_min_d_vent_km", "vrp_pixeles_dentro_inner", "mir_vrp", "mir_src"])
        w.writerows(filas)


def parte_b():
    cen = AUD / "_censo_s159"
    obj = {(o["volcan"], o["hora_utc"]): o for o in json.load(open(cen / "objetivos.json", encoding="utf-8"))}
    res = []
    for f in sorted(glob.glob(str(cen / "censo_39713438252" / "*" / "resultados_*.json"))):
        res += json.load(open(f, encoding="utf-8"))
    print("\nB. oraculo en las pasadas pos (alerta de MIROVA) del censo, por caja")
    for v in ("Tupungatito", "PuyehueCordonCaulle", "Isluga", "Lascar"):
        c = defaultdict(Counter)
        npos = nprot = 0
        for r in res:
            if r["volcan"] != v:
                continue
            o = obj[(v, r["hora_utc"])]
            if o["lab"] != "pos":
                continue
            if r.get("estado") != "ok":
                c["estado"][r.get("estado")] += 1
                continue
            npos += 1
            nprot += bool(o.get("protegida"))
            for caja in ("geo_linear", "geo_linear_anillo_sensible"):
                ora = (r.get("oraculo") or {}).get(caja)
                if ora is None:
                    c[caja]["SIN_ORACULO"] += 1
                    continue
                c[caja]["marca" if ora.get("npix", 0) > 0 else f"vacio:{ora.get('motivo_vacio')}"] += 1
                if caja == "geo_linear" and ora.get("npix", 0) == 0:
                    c["odef_nabs_np1_np2"][(ora.get("n_abs"), ora.get("n_p1"), ora.get("n_p2"))] += 1
        print(f"  {v}: pasadas pos con estado ok {npos} (protegidas {nprot}); fuera de ok {dict(c['estado'])}")
        print(f"     caja por defecto: {dict(c['geo_linear'])}")
        print(f"     anillo sensible : {dict(c['geo_linear_anillo_sensible'])}")
        if c["odef_nabs_np1_np2"]:
            print(f"     O-def vacio, (n_abs, n_p1, n_p2) mas frecuentes: {c['odef_nabs_np1_np2'].most_common(6)}")


if __name__ == "__main__":
    parte_a()
    parte_b()
