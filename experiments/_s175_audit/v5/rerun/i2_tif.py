# -*- coding: utf-8 -*-
"""I2 vara de posición: píxel más caliente del TIF de MIROVA de la misma pasada contra nuestro punto (lat/lon).

Control de georreferencia (pregunta 2 del instrumento): la distancia del píxel máximo del TIF a mirova_center tiene que
reproducir la Distancia_km de la tabla de esa pasada; si no la reproduce, el píxel máximo no es el alertado o la
georreferencia está mal, y el caso queda (iv).
Uso: python i2_tif.py <carpeta_tifs>. Salida: i2_tif_out.json al lado de este script.
"""
import csv, json, math, os, sys
import numpy as np
import rasterio
from rasterio.warp import transform as rtransform
import yaml
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
V = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
CASOS = [  # (volcán, bucket, hora de nuestra pasada, archivo)
    ("Lastarria", "VIIRS375", "2026-06-12 05:54", "20260612_055401_VIIRS375.tif"),
    ("Lastarria", "VIIRS375", "2026-06-17 06:00", "20260617_060001_VIIRS375.tif"),
    ("Lastarria", "VIIRS375", "2026-07-14 05:54", "20260714_055401_VIIRS375.tif"),
    ("Lastarria", "VIIRS375", "2026-08-09 05:48", "20260809_054800_VIIRS375.tif"),
    ("PuyehueCordonCaulle", "VIIRS750", "2026-07-06 05:54", "20260706_055402_VIIRS750.tif"),
    ("Lascar", "VIIRS375", "2026-06-25 05:12", "20260625_051201_VIIRS375.tif"),
    ("Lascar", "VIIRS750", "2026-06-21 05:30", "20260621_053002_VIIRS750.tif"),
    ("Isluga", "VIIRS375", "2026-09-22 05:42", "20260922_054201_VIIRS375.tif"),
]


def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def main(carpeta):
    pares = {(r["vol"], r["b"], r["dt"]): r for r in csv.DictReader(open(os.path.join(H, "i2_pares.csv"), encoding="utf-8"))}
    out = []
    for vol, b, dt, fn in CASOS:
        r = pares[(vol, b, dt)]
        with rasterio.open(os.path.join(carpeta, fn)) as ds:
            a = ds.read(1).astype(float)
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
            # El máximo global cae en el borde en 4 de 8 TIF (primera corrida, i2_tif_v1_maximo_global.out.txt): se busca el máximo
            # dentro del inner_radius_km de MIROVA medido desde mirova_center (el círculo donde MIROVA cuenta la alerta).
            rr, cc = np.meshgrid(range(a.shape[0]), range(a.shape[1]), indexing="ij")
            xs, ys = rasterio.transform.xy(ds.transform, rr.ravel(), cc.ravel())
            mc0 = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
            dd = np.array([hav(yy, xx, *mc0) for xx, yy in zip(xs, ys)]).reshape(a.shape)
            a[dd > V[vol]["inner_radius_km"]] = np.nan
            iy, ix = np.unravel_index(np.nanargmax(a), a.shape)
            x, y = ds.xy(iy, ix)
            lon, lat = rtransform(ds.crs, "EPSG:4326", [x], [y])
            lon, lat = lon[0], lat[0]
            px_km = abs(ds.transform.a) / (1000.0 if ds.crs.is_projected else 1 / 111.0)
            meta = {"crs": str(ds.crs), "shape": a.shape, "dtype": ds.dtypes[0], "max": float(np.nanmax(a)),
                    "p99": float(np.nanpercentile(a, 99)), "pix_km": round(px_km, 3)}
        mc = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        d_tif_mc = hav(lat, lon, *mc)
        d_tif_nuestro = hav(lat, lon, float(r["our_lat"]), float(r["our_lon"]))
        georef_ok = abs(d_tif_mc - float(r["dist_mirova"])) <= max(TOL[b], meta["pix_km"]) if r["dist_mirova"] else None
        clase = ("iv" if not georef_ok else "i" if d_tif_nuestro <= TOL[b] else "iii")
        o = {"vol": vol, "b": b, "dt": dt, "tif": fn, "tif_max_lat": round(lat, 5), "tif_max_lon": round(lon, 5), **meta,
             "dist_mirova_tabla": r["dist_mirova"], "fuente_dist": r["fuente_dist"], "d_tif_desde_mirova_center": round(d_tif_mc, 2),
             "georef_reproduce_distancia": georef_ok, "nuestro_lat": r["our_lat"], "nuestro_lon": r["our_lon"],
             "d_nuestro_desde_mc": r["d_desde_mirova_center"], "d_tif_a_nuestro_km": round(d_tif_nuestro, 2),
             "clase_radio": r["clase"], "clase_tif": clase}
        out.append(o)
        print(o)
    json.dump(out, open(os.path.join(H, "i2_tif_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
