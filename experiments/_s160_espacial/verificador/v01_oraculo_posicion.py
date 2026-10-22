# -*- coding: utf-8 -*-
"""V01 (verificador S160 espacial): posicion de los pixeles que marca el codigo de MIROVA (oraculo O-sens y O-def del censo
S159) leidos del JSON CRUDO del censo (no del CSV 02a del auditor), con cuenta propia de distancia y rumbo (pyproj.Geod,
elipsoide WGS84; el auditor usa haversine esferica) al vent (volcanoes.yaml leido aqui) y al centro del TIF (leido aqui de
los GeoTIFF con rasterio). Resuelve la incoherencia del mapa de PCC contando cuantos marcadores caen en cada celda.

P1 (si estuviera roto, se veria): la celda (33,33) debe caer a <= 400 m del centro de la grilla del objetivo, y la
   distancia en celdas que el propio oraculo guarda (campo 4 del pixel = hypot(fila-33, col-33)*0.75) debe coincidir con
   la mia medida en metros UTM desde la celda 33 (tolerancia 1 m). Ademas se compara mi lat/lon con la del CSV 02a.
P2 (si el instrumento estuviera muerto): se imprime n de pasadas y pixeles por volcan, estrato y caja; 0 es SIN DATO.
Control positivo: Isluga (vent en el centro) debe dar pixeles a ~1 km del vent; Lascar en O-def debe marcar sus alertas.
Ventana: la del censo (VIIRS 750 nocturno 2026-04-01 a 2026-10-21, sin 18-19 oct).
"""
from __future__ import annotations

import csv
import glob
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import rasterio
import yaml
from pyproj import Geod, Transformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent
ROOT = AUD.parents[1]
CEN = AUD / "_censo_s159"
G = Geod(ellps="WGS84")
VOLS = ["Tupungatito", "PuyehueCordonCaulle", "Isluga"]
OCT = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def octante(az):
    return OCT[int(((az % 360) + 22.5) % 360 // 45)]


def dist_az(lat1, lon1, lat2, lon2):
    az, _, d = G.inv(lon1, lat1, lon2, lat2)
    return d / 1000.0, az % 360


def main():
    vy = yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))
    vy = vy["volcanoes"] if isinstance(vy, dict) else vy
    vent = {v["name"]: (v["vent_lat"], v["vent_lon"]) for v in vy if v["name"] in VOLS}
    # centro del TIF: 3 TIF VIIRS 375 EPSG:4326 por volcan del archivo local
    tc = {}
    for v in VOLS:
        cs = set()
        for f in sorted(glob.glob(str(ROOT.parent / "mirova-tif-archive" / "data" / "tif" / v / "*VIIRS375*.tif")))[:40]:
            with rasterio.open(f) as ds:
                if ds.crs and ds.crs.to_epsg() == 4326:
                    b = ds.bounds
                    cs.add((round((b.top + b.bottom) / 2, 5), round((b.left + b.right) / 2, 5), ds.width, ds.height))
        print(f"centro TIF {v}: valores distintos en hasta 40 TIF 4326: {sorted(cs)}")
        c = sorted(cs)[0]
        tc[v] = (c[0], c[1])
    obj = {(o["volcan"], o["hora_utc"]): o for o in json.load(open(CEN / "objetivos.json", encoding="utf-8"))}
    res = []
    for f in sorted(glob.glob(str(CEN / "censo_39713438252" / "*" / "resultados_*.json"))):
        res += json.load(open(f, encoding="utf-8"))
    csv02a = {}
    for r in csv.DictReader(open(AUD / "02a_oraculo_v750_pixeles.csv", encoding="utf-8")):
        csv02a[(r["volcan"], r["hora_utc"], int(r["fila"]), int(r["col"]))] = (float(r["lat"]), float(r["lon"]))
    out_rows = []
    for v in VOLS:
        g = next(o["grilla"] for (vv, _), o in obj.items() if vv == v)
        T = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True)
        lon33, lat33 = T.transform(g["ul_x"] + 750 * 33.5, g["ul_y"] - 750 * 33.5)
        d33, _ = dist_az(lat33, lon33, g["centro_lat"], g["centro_lon"])
        dvc, azvc = dist_az(*tc[v], *vent[v])
        dvg, azvg = dist_az(g["centro_lat"], g["centro_lon"], *vent[v])
        print(f"\n===== {v}: vent {vent[v]}; centro TIF {tc[v]}; centro grilla objetivo ({g['centro_lat']},{g['centro_lon']})")
        print(f"  P1 celda (33,33) a {d33*1000:.0f} m del centro de la grilla; vent a {dvc:.3f} km rumbo {azvc:.0f} ({octante(azvc)}) "
              f"del centro del TIF; a {dvg:.3f} km rumbo {azvg:.0f} del centro de la grilla")
        for caja in ("geo_linear_anillo_sensible", "geo_linear"):
            agg = defaultdict(list)
            maxdif_cel = maxdif_csv = 0.0
            n_csv = 0
            for r in res:
                if r["volcan"] != v or r.get("estado") != "ok":
                    continue
                o = obj[(v, r["hora_utc"])]
                ora = (r.get("oraculo") or {}).get(caja) or {}
                for a, b, clase, dcel, rad in ora.get("pixeles") or []:
                    x = g["ul_x"] + 750 * (b + 0.5)
                    y = g["ul_y"] - 750 * (a + 0.5)
                    lon, lat = T.transform(x, y)
                    dmy = ((x - (g["ul_x"] + 750 * 33.5)) ** 2 + (y - (g["ul_y"] - 750 * 33.5)) ** 2) ** 0.5 / 1000
                    maxdif_cel = max(maxdif_cel, abs(dmy - dcel))
                    k = (v, r["hora_utc"], a, b)
                    if caja.endswith("sensible") and k in csv02a:
                        n_csv += 1
                        dd, _ = dist_az(lat, lon, *csv02a[k])
                        maxdif_csv = max(maxdif_csv, dd)
                    dv_, azv = dist_az(*vent[v], lat, lon)
                    dt_, azt = dist_az(*tc[v], lat, lon)
                    agg[o["lab"]].append({"hora": r["hora_utc"], "fila": a, "col": b, "clase": clase, "lat": lat, "lon": lon,
                                          "dv": dv_, "azv": azv, "dt": dt_, "azt": azt, "mdist": next((m["dist_km"] for m in o.get("mirova") or []
                                                                                                    if m["tipo"].startswith("ALERTA")), None),
                                          "prot": o.get("protegida")})
                    out_rows.append([v, caja, o["lab"], r["hora_utc"], a, b, clase, round(lat, 5), round(lon, 5), round(dv_, 3), round(azv),
                                     round(dt_, 3), round(azt)])
            print(f"  -- caja {caja}: P1 max |dist celdas oraculo - mi dist UTM| = {maxdif_cel*1000:.1f} m; "
                  f"max |mi lat/lon - CSV 02a| = {maxdif_csv*1000:.1f} m sobre {n_csv} pixeles")
            for lab in ("pos", "neg_limpio"):
                L = agg.get(lab, [])
                if not L:
                    print(f"     {lab}: SIN DATO (0 pixeles)")
                    continue
                pas = sorted(set(x["hora"] for x in L))
                celdas = Counter((x["fila"], x["col"]) for x in L)
                print(f"     {lab}: {len(L)} pixeles en {len(pas)} pasadas; celdas distintas {len(celdas)}; d al vent p50 {median([x['dv'] for x in L]):.2f} km; "
                      f"<=1 km {sum(x['dv']<=1 for x in L)}, 1-1.5 {sum(1<x['dv']<=1.5 for x in L)}, >1.5 km {sum(x['dv']>1.5 for x in L)}")
                for (a, b), n in celdas.most_common():
                    x = next(y for y in L if (y["fila"], y["col"]) == (a, b))
                    print(f"        celda ({a},{b}) clase {x['clase']} x{n}: {x['lat']:.4f},{x['lon']:.4f}  a {x['dv']:.2f} km {octante(x['azv'])} del vent; "
                          f"a {x['dt']:.2f} km {octante(x['azt'])} del centro TIF")
                lejos = [x for x in L if x["dv"] > 1.5]
                if lejos:
                    por_p = defaultdict(list)
                    for x in L:
                        por_p[x["hora"]].append(x)
                    con_vent = sum(1 for h in set(x["hora"] for x in lejos) if any(y["dv"] <= 1.5 for y in por_p[h]))
                    print(f"        pasadas con pixel a >1,5 km del vent: {len(set(x['hora'] for x in lejos))}; de ellas con pixel tambien a <=1,5 km del vent: {con_vent}")
                    for h in sorted(set(x["hora"] for x in lejos)):
                        P = por_p[h]
                        print(f"          {h} MIROVA Distancia_km {P[0]['mdist']} prot {P[0]['prot']} | pixeles (d_vent km, oct, d_centroTIF km): "
                              f"{[(round(y['dv'],2), octante(y['azv']), round(y['dt'],2)) for y in P]}")
    with open(AQUI / "v01_oraculo_posicion_pixeles.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["volcan", "caja", "lab", "hora_utc", "fila", "col", "clase", "lat", "lon", "d_vent_km", "az_vent", "d_centroTIF_km", "az_centroTIF"])
        w.writerows(out_rows)


if __name__ == "__main__":
    main()
