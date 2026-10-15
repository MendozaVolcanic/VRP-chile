# Donde pone MIROVA el pixel caliente del crater en sus GeoTIFF MODIS, segun el lado del barrido y el cenit.
# Solo lectura: el archivo de TIF se lee por raw.githubusercontent (nunca pull ni clone, A106 y regla S143).
#
# POR QUE: si el corrimiento hacia el sensor es de nuestra geolocalizacion (`_interp_geo`), en las imagenes
# de MIROVA de las MISMAS pasadas el crater debe quedar en su sitio con el volcan a cualquier lado de la
# traza. Si MIROVA muestra el mismo corrimiento, el defecto no es nuestro.
#
# Como se encuentra el crater en el TIF: el TIF de MIROVA es un campo de radiancia en grilla de 0,01 grados
# (A24, no es VRP por pixel). El pixel mas brillante de la escena suele ser un valle tibio (A69), asi que se
# busca el maximo LOCAL con mayor contraste contra sus 8 vecinos dentro de 5 km del crater. El contraste
# separa un foco puntual de un gradiente suave.
#
# La hora: se usa `acquisition_utc` del indice del archivo, y de cada md5 solo la primera aparicion (A106:
# MIROVA a veces vuelve a servir una imagen vieja bajo una hora nueva). La geometria (cenit, acimut, lado)
# sale de nuestro record de produccion de la misma pasada.
#
# Uso: python mirova_tif.py --tmp <carpeta temporal>
import argparse
import csv
import datetime as dt
import json
import math
import statistics as st
import sys
import urllib.request
from pathlib import Path

import numpy as np

import comun

sys.stdout.reconfigure(encoding="utf-8")
RAW = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
VOLCANES = ("Lascar", "Villarrica", "NevadosDeChillan")
VENTANA_KM = 5.0
CONTRASTE_MIN = 0.02


def bajar(rel, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        with urllib.request.urlopen(RAW + rel, timeout=60) as r:
            destino.write_bytes(r.read())
    return destino


def pico_local(path, la, lo):
    import rasterio
    with rasterio.open(path) as s:
        if str(s.crs) != "EPSG:4326":
            return None, str(s.crs)
        a = s.read(1).astype(float)
        T = s.transform
    best = None
    for i in range(1, a.shape[0] - 1):
        for j in range(1, a.shape[1] - 1):
            v = a[i, j]
            if not np.isfinite(v):
                continue
            vec = a[i - 1:i + 2, j - 1:j + 2].copy()
            if not np.all(np.isfinite(vec)):
                continue
            vec[1, 1] = np.nan
            if v <= np.nanmax(vec):
                continue
            lon_c, lat_c = T * (j + 0.5, i + 0.5)
            dn, de = comun.ne_km(la, lo, lat_c, lon_c)
            if math.hypot(dn, de) > VENTANA_KM:
                continue
            c = v - np.nanmean(vec)
            if best is None or c > best[0]:
                best = (c, dn, de, v)
    return best, "EPSG:4326"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    args = ap.parse_args()
    tmp = Path(args.tmp)
    idx = bajar("index.csv", tmp / "index.csv")
    filas_idx = list(csv.DictReader(open(idx, encoding="utf-8")))
    vents = comun.vents()
    out = []
    for vol in VOLCANES:
        la, lo = vents[vol]
        recs = {}
        for r in comun.cargar_records(vol):
            if r["sensor"].startswith("MODIS") and r.get("sensor_zenith_deg") is not None:
                recs[dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")] = r
        vistos = set()
        for f in filas_idx:
            if f["volcano"] != vol or f["sensor"] != "MODIS" or not f["acquisition_utc"] or f["md5"] in vistos:
                continue
            vistos.add(f["md5"])
            t = dt.datetime.strptime(f["acquisition_utc"][:16], "%Y-%m-%dT%H:%M")
            r = recs.get(t)
            if r is None or (r.get("solar_zenith_deg") or 0) <= 90:
                continue
            p = bajar(f["tif_path"], tmp / f["tif_path"])
            best, crs = pico_local(p, la, lo)
            if best is None or best[0] < CONTRASTE_MIN:
                continue
            sat = comun.satelite(r["sensor"])
            az = r["sensor_azimuth_deg"]
            ld = comun.lado(sat, t, lo, az)
            u, v = comun.hacia_sensor(best[1], best[2], az)
            out.append({"volcan": vol, "tif": f["tif_path"], "adquisicion": f["acquisition_utc"], "sat": sat, "lado": ld,
                        "cenit": r["sensor_zenith_deg"], "acimut": az % 360, "contraste": round(best[0], 4),
                        "dn_km": round(best[1], 3), "de_km": round(best[2], 3), "u_km": round(u, 3), "v_km": round(v, 3),
                        "pred_interp_km": round(comun.pred_interp_km(r["sensor_zenith_deg"], ld == "der"), 3)})
    json.dump(out, open(comun.SALIDAS / "mirova_tif_picos.json", "w", encoding="utf-8"), indent=1)
    res = open(comun.SALIDAS / "mirova_tif_resumen.txt", "w", encoding="utf-8")

    def p(s=""):
        print(s)
        res.write(s + "\n")
    p("Pico local de mayor contraste a <= %.0f km del crater en los TIF MODIS de MIROVA (grilla 0,01 grados)," % VENTANA_KM)
    p("pasadas nocturnas con contraste >= %.2f. u + = hacia el sensor. 'pred' es lo que corre NUESTRA geolocalizacion." % CONTRASTE_MIN)
    for vol in VOLCANES:
        for sat in ("AQUA", "TERRA"):
            for ld in ("der", "izq"):
                for z0, z1 in ((0, 25), (25, 45), (45, 66)):
                    s = [x for x in out if x["volcan"] == vol and x["sat"] == sat and x["lado"] == ld and z0 <= x["cenit"] < z1]
                    if len(s) >= 3:
                        p("%-17s %-5s %-3s cenit %2d-%2d n=%3d  dN med %+.2f  dE med %+.2f | u med %+.2f  pred nuestra %+.2f" % (
                            vol, sat, ld, z0, z1, len(s), st.median(x["dn_km"] for x in s), st.median(x["de_km"] for x in s),
                            st.median(x["u_km"] for x in s), st.median(x["pred_interp_km"] for x in s)))
    p()
    p("Mismo satelite, lado del frame 0 contra el otro (todos los cenit): si MIROVA tuviera nuestro defecto, el dE")
    p("de Aqua del lado del frame 0 (sensor al este) quedaria varios km al ESTE del otro lado; el de Terra, al OESTE.")
    for vol in VOLCANES:
        for sat in ("AQUA", "TERRA"):
            a = [x for x in out if x["volcan"] == vol and x["sat"] == sat and x["lado"] == "der"]
            b = [x for x in out if x["volcan"] == vol and x["sat"] == sat and x["lado"] == "izq"]
            if len(a) >= 3 and len(b) >= 3:
                pa = [comun.pred_interp_km(x["cenit"], True) * math.sin(math.radians(x["acimut"])) for x in a]
                pb = [comun.pred_interp_km(x["cenit"], False) * math.sin(math.radians(x["acimut"])) for x in b]
                p("%-17s %-5s dE med lado frame 0 %+.2f (n=%d), otro lado %+.2f (n=%d): diferencia MIROVA %+.2f km;"
                  " diferencia que daria nuestra geolocalizacion %+.2f km" % (
                      vol, sat, st.median(x["de_km"] for x in a), len(a), st.median(x["de_km"] for x in b), len(b),
                      st.median(x["de_km"] for x in a) - st.median(x["de_km"] for x in b), st.median(pa) - st.median(pb)))
    der = [x for x in out if x["lado"] == "der" and x["cenit"] >= 30]
    izq = [x for x in out if x["lado"] == "izq" and x["cenit"] >= 30]
    if der and izq:
        p()
        p("Cenit >= 30, todos los volcanes: lado del frame 0 n=%d u med %+.2f (nuestra pred %+.2f); otro lado n=%d u med %+.2f (pred %+.2f)"
          % (len(der), st.median(x["u_km"] for x in der), st.median(x["pred_interp_km"] for x in der),
             len(izq), st.median(x["u_km"] for x in izq), st.median(x["pred_interp_km"] for x in izq)))
    res.close()


if __name__ == "__main__":
    main()
