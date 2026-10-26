# -*- coding: utf-8 -*-
"""Pregunta 2 (VIIRS 750): DONDE marca pixeles el codigo de MIROVA (oraculo O-sens del censo S159) respecto del
centro del TIF, del crater (vent) y de nuestro cumulo primario (K = produccion) en la MISMA pasada.

Fuente: experiments/_s159/oraculo_censo/resultados_crudos.tar.gz (rama s159-oraculo-censo, run 39713438252) y
objetivos.json de la misma rama, copiados a _censo_s159/. Cada pixel del oraculo viene como
[fila, col, clase_caja, dist_celdas*0.75, radiancia] en la grilla UTM de 67 x 67 celdas de 750 m
(probe_n.py: xs = ul_x + 750*(col+0.5), ys = ul_y - 750*(fila+0.5); centro = celda 33).

A109: el oraculo y K corren sobre el mismo granulo. Aqui eso no infla nada porque no se pregunta "hay algo", se
pregunta "donde esta lo que cada codigo marco"; pero la coincidencia de posicion entre ambos NO es independiente del
granulo (nube, ruido), y se declara.

Las dos preguntas del instrumento:
  P1: si la conversion fila/col -> lat/lon estuviera rota, la celda central (33,33) no caeria en centro_lat/lon del
      objetivo (se comprueba, tolerancia 400 m) y los pixeles de Isluga (crater = centro) no caerian en el crater.
  P2: se imprime n de pasadas con pixeles por volcan; 0 pixeles en un volcan es SIN DATO para la direccion.
Ventana: VIIRS 750 nocturno 2026-04-01 a 2026-10-21 (la del censo), sin el 18 ni el 19 de octubre.
"""
from __future__ import annotations

import glob
import json
from collections import Counter, defaultdict
from statistics import median

from pyproj import Transformer

import comun as C

CEN = C.AQUI / "_censo_s159"
SAL = C.AQUI / "02a_oraculo_v750_posicion_salida.txt"
CSV = C.AQUI / "02a_oraculo_v750_pixeles.csv"
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


import sys
CAJA = sys.argv[1] if len(sys.argv) > 1 else "geo_linear_anillo_sensible"
SAL = C.AQUI / f"02a_oraculo_v750_posicion_salida{'' if CAJA.endswith('sensible') else '_odef'}.txt"
CSV = C.AQUI / f"02a_oraculo_v750_pixeles{'' if CAJA.endswith('sensible') else '_odef'}.csv"


def main():
    p("caja del oraculo:", CAJA)
    obj = {(o["volcan"], o["hora_utc"]): o for o in json.load(open(CEN / "objetivos.json", encoding="utf-8"))}
    res = []
    for f in sorted(glob.glob(str(CEN / "censo_39713438252" / "*" / "resultados_*.json"))):
        res += json.load(open(f, encoding="utf-8"))
    p(f"censo: {len(res)} pasadas, {len(obj)} objetivos; estados {dict(Counter(r.get('estado') for r in res))}")
    filas = ["volcan,hora_utc,lab,protegida,mirova_vrp,mirova_dist_km,caja,fila,col,clase,lat,lon,d_centro_km,rumbo_centro,"
             "d_vent_km,rumbo_vent,radiancia,K_pc_lat,K_pc_lon,K_pc_dist_vent_km,K_dc,K_pub,K_pc_vrp"]
    tr = {}
    for v in C.VOLS:
        g = next(o["grilla"] for o in obj.values() if o["volcan"] == v)
        tr[v] = (Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True), g)
        lon, lat = tr[v][0].transform(g["ul_x"] + 750 * 33.5, g["ul_y"] - 750 * 33.5)
        d = C.hav_km(lat, lon, g["centro_lat"], g["centro_lon"])
        dt = C.hav_km(g["centro_lat"], g["centro_lon"], *C.GEO[v]["tif_centro"])
        p(f"P1 {v:22s} celda central (33,33) -> {lat:.5f},{lon:.5f}; a {d*1000:.0f} m del centro_lat/lon del objetivo "
          f"({'OK' if d < 0.4 else 'FALLA'}); centro del objetivo a {dt*1000:.0f} m del centro del TIF 4326 de VIIRS 375")
    agg = defaultdict(list)
    for r in res:
        v = r["volcan"]
        if v not in C.VOLS or r.get("estado") != "ok":
            continue
        o = obj.get((v, r["hora_utc"]), {})
        ora = (r.get("oraculo") or {}).get(CAJA) or {}
        pix = ora.get("pixeles") or []
        K = ((r.get("brazos") or {}).get("K") or {}).get("record") or {}
        pc = K.get("primary_cluster") or {}
        mir = [m for m in (o.get("mirova") or []) if m["tipo"].startswith("ALERTA")]
        mdist = mir[0]["dist_km"] if mir else ""
        T, g = tr[v]
        vent = C.GEO[v]["vent"]
        kd = C.hav_km(pc["centroid_lat"], pc["centroid_lon"], *vent) if pc.get("centroid_lat") is not None else None
        for a, b, clase, dcel, rad in pix:
            lon, lat = T.transform(g["ul_x"] + 750 * (b + 0.5), g["ul_y"] - 750 * (a + 0.5))
            dc = C.hav_km(lat, lon, g["centro_lat"], g["centro_lon"])
            rc = C.rumbo_deg(g["centro_lat"], g["centro_lon"], lat, lon)
            dv = C.hav_km(lat, lon, *vent)
            rv = C.rumbo_deg(vent[0], vent[1], lat, lon)
            filas.append(",".join(str(x) for x in [v, r["hora_utc"], o.get("lab"), o.get("protegida"), o.get("mirova_vrp"),
                                                     mdist, CAJA, a, b, clase, round(lat, 5), round(lon, 5), round(dc, 2),
                                                     round(rc), round(dv, 2), round(rv), rad,
                                                     pc.get("centroid_lat", ""), pc.get("centroid_lon", ""),
                                                     "" if kd is None else round(kd, 2), K.get("distance_class", ""),
                                                     o.get("pub_prod", ""), pc.get("vrp_mw", "")]))
            agg[(v, o.get("lab"))].append((dc, rc, dv, rv, kd, lat, lon, pc, r["hora_utc"], mdist))
    CSV.write_text("\n".join(filas), encoding="utf-8")
    for v in C.VOLS:
        p(f"\n== {v}: vent a {C.hav_km(*C.GEO[v]['tif_centro'], *C.GEO[v]['vent']):.2f} km del centro del TIF, inner {C.GEO[v]['inner_km']:g} km")
        for lab in ("pos", "neg_limpio", "far_ref", "minima", "sin_info", "sin_geometria"):
            L = agg.get((v, lab), [])
            if not L:
                p(f"  {lab:14s} SIN DATO (0 pixeles del oraculo)")
                continue
            pas = len(set(x[8] for x in L))
            dcs = [x[0] for x in L]
            dvs = [x[2] for x in L]
            oc = Counter(C.octante(x[1]) for x in L)
            ov = Counter(C.octante(x[3]) for x in L)
            p(f"  {lab:14s} {len(L)} pixeles en {pas} pasadas | d al centro TIF p50 {median(dcs):.2f} km (p10 {sorted(dcs)[int(0.1*(len(dcs)-1))]:.2f}, "
              f"p90 {sorted(dcs)[int(0.9*(len(dcs)-1))]:.2f}); octante desde el centro {dict(oc.most_common())} | "
              f"d al VENT p50 {median(dvs):.2f} km, <=1,5 km {100*sum(d<=1.5 for d in dvs)/len(dvs):.0f}%, "
              f"<=inner {100*sum(d<=C.GEO[v]['inner_km'] for d in dvs)/len(dvs):.0f}%; octante desde el vent {dict(ov.most_common())}")
            # coincidencia con nuestro cumulo K en la misma pasada
            con_k = [x for x in L if x[4] is not None]
            if con_k:
                dd = [C.hav_km(x[5], x[6], x[7]["centroid_lat"], x[7]["centroid_lon"]) for x in con_k]
                p(f"     con cumulo K en la misma pasada: {len(con_k)} pixeles; d pixel-oraculo a centroide K p50 {median(dd):.2f} km, "
                  f"<=1,1 km (una celda diagonal) {100*sum(d<=1.1 for d in dd)/len(dd):.0f}%; K centroide a vent p50 {median([x[4] for x in con_k]):.2f} km")
            sin_k = [x for x in L if x[4] is None]
            if sin_k:
                p(f"     sin cumulo K (produccion no detecto nada): {len(sin_k)} pixeles en {len(set(x[8] for x in sin_k))} pasadas; "
                  f"d al vent p50 {median([x[2] for x in sin_k]):.2f} km; ejemplos {[(x[8], round(x[2],2), C.octante(x[3])) for x in sin_k[:6]]}")
            # comparacion con la Distancia_km de MIROVA en pos (radio vs radio, A93: cota, no identidad)
            md = [(x[0], float(x[9])) for x in L if x[9] not in ("", None)]
            if md:
                dif = [a - b for a, b in md]
                p(f"     Distancia_km de MIROVA vs d(pixel oraculo, centro TIF): n {len(md)}, mediana de la diferencia {median(dif):+.2f} km, "
                  f"|dif|<=0,8 km {100*sum(abs(d)<=0.8 for d in dif)/len(dif):.0f}%")
    SAL.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
