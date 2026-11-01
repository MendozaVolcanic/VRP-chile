# -*- coding: utf-8 -*-
"""S159 frente GEO, parte R: resume el inventario r1 por volcan, sensor y CRS: tamano, celda, centro y extension,
y los compara con `volcanoes.yaml` (lat/lon, mirova_center, radius_km).

Las dos preguntas del instrumento:
1. Si la caja cambiara entre volcanes o en el tiempo, el conteo de "geometrias distintas" por volcan y sensor lo
   mostraria (se agrupa por CRS, tamano y transformada redondeada a 1e-7 grados o 0,1 m).
2. Si la lectura estuviera muerta, las filas con error se cuentan aparte; un volcan sin filas sale SIN DATO.
Denominador: archivos de la muestra de r1 (mayo a septiembre de 2026). md5 repetido se informa (A106).
Uso: python -I r3_resumen_cajas.py <inventario r1 csv> <volcanoes.yaml>
"""
import io
import math
import sys

import pandas as pd
import yaml
from pyproj import Geod, Transformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ALIAS = {"ChillanNevadosde": "NevadosDeChillan"}
G = Geod(ellps="WGS84")


def main(inv_csv, yml):
    inv = pd.read_csv(inv_csv)
    print("archivos:", len(inv), "| con error:", int(inv.get("error", pd.Series(dtype=str)).notna().sum()))
    print("md5 bajado distinto del indice:", int((inv.md5_archivo != inv.md5_indice).sum()))
    inv = inv[inv.epsg.notna()].copy()
    inv["lm"] = pd.to_datetime(inv.last_modified_utc)
    vols = {v["name"]: v for v in yaml.safe_load(open(yml, encoding="utf-8"))["volcanoes"]}
    filas = []
    for _, r in inv.iterrows():
        v = vols[ALIAS.get(r.volcano, r.volcano)]
        w, h = r.ancho, r.alto
        cx, cy = r.c + r.a * w / 2, r.f + r.e * h / 2
        if int(r.epsg) == 4326:
            clon, clat = cx, cy
            ancho_km = G.inv(r.c, clat, r.c + r.a * w, clat)[2] / 1000
            alto_km = G.inv(clon, r.f, clon, r.f + r.e * h)[2] / 1000
        else:
            clon, clat = Transformer.from_crs(int(r.epsg), 4326, always_xy=True).transform(cx, cy)
            ancho_km, alto_km = abs(r.a) * w / 1000, abs(r.e) * h / 1000
        d_yaml = G.inv(clon, clat, v["lon"], v["lat"])[2]
        mc = (v.get("mirova_center_lon"), v.get("mirova_center_lat"))
        d_mc = G.inv(clon, clat, *mc)[2] if mc[0] else math.nan
        filas.append(dict(volcano=r.volcano, sensor=r.sensor, epsg=int(r.epsg), mes=r.lm.strftime("%Y-%m"),
                          lm=r.lm, tam=f"{w}x{h}", celda=round(abs(r.a), 9), ancho_km=round(ancho_km, 2),
                          alto_km=round(alto_km, 2), c_lat=round(clat, 5), c_lon=round(clon, 5),
                          d_yaml_m=round(d_yaml), d_mc_m=round(d_mc), geom=(int(r.epsg), w, h, round(r.c, 7),
                                                                            round(r.f, 7), round(r.a, 9)),
                          md5=r.md5_indice, radio_yaml=v.get("radius_km"), inner_yaml=v.get("inner_radius_km")))
    d = pd.DataFrame(filas)
    print("\n=== por sensor y CRS: periodo (last_modified) y numero de archivos ===")
    print(d.groupby(["sensor", "epsg"]).lm.agg(["min", "max", "size"]).to_string())
    print("\n=== geometrias distintas por volcan y sensor (CRS, tamano, celda, extension, centro, distancia al"
          " lat/lon del yaml y a mirova_center) ===")
    t = (d.groupby(["volcano", "sensor", "geom"])
         .agg(epsg=("epsg", "first"), tam=("tam", "first"), celda=("celda", "first"), ancho_km=("ancho_km", "first"),
              alto_km=("alto_km", "first"), c_lat=("c_lat", "first"), c_lon=("c_lon", "first"),
              d_yaml_m=("d_yaml_m", "first"), d_mc_m=("d_mc_m", "first"), desde=("lm", "min"), hasta=("lm", "max"),
              n=("lm", "size"), radio_yaml=("radio_yaml", "first"), inner_yaml=("inner_yaml", "first"))
         .reset_index().drop(columns="geom"))
    t["desde"] = t.desde.dt.strftime("%m-%d %H:%M")
    t["hasta"] = t.hasta.dt.strftime("%m-%d %H:%M")
    pd.set_option("display.width", 250)
    print(t.sort_values(["volcano", "sensor", "desde"]).to_string(index=False))
    print("\n=== geometrias distintas por volcan y sensor (conteo) ===")
    print(t.groupby(["volcano", "sensor"]).size().unstack().to_string())
    print("\n=== md5 repetidos dentro de la muestra (misma imagen servida dos veces) ===")
    rep = d[d.md5.duplicated(keep=False)]
    print(len(rep), "filas;", rep.groupby(["volcano", "sensor"]).size().to_dict() if len(rep) else "")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
