# PROBE PROPUESTO, NO CORRIDO (no habia EARTHDATA_TOKEN en el entorno local; regla A71: nunca usuario y
# clave). Compara, en 4 granulos MODIS sobre Lascar, la geolocalizacion que usa hoy el pipeline
# (`_interp_geo` sobre la grilla de 5 km de MxD021KM) contra la de MxD03 (1 km, corregida por terreno, sin
# interpolar), que el pipeline YA baja y le pasa a `calculate_vrp` como `geo_path` sin leerla.
#
# Corre en Linux (pyhdf). Solo lectura del repo; escribe un JSON y un texto en --out.
# Uso: EARTHDATA_TOKEN=... python probe_mod03.py --out salida_probe
#
# Que debe salir si el diagnostico es correcto: en el pixel del crater, la diferencia interp - MxD03 a lo
# largo del barrido debe parecerse a `comun.pred_interp_km` (Aqua 03-14 ~2,9 km y 03-27 ~2,4 km hacia el
# sensor; Terra 03-16 ~0,2 km alejandose), y el pixel caliente medido con MxD03 debe caer a menos de ~1 km
# del crater en las cuatro pasadas.
import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))
import comun  # noqa: E402

PASADAS = [  # (L1B, GEO, short_name version, nombre comun del granulo)
    ("MYD021KM", "MYD03", "A2026073.0705"),   # Aqua, frame 0, cenit 44,6: el pixel de K a 3,47 km E
    ("MYD021KM", "MYD03", "A2026086.0710"),   # Aqua, frame 0, cenit 39,9: la perdida del veto de la caja
    ("MOD021KM", "MOD03", "A2026075.0135"),   # Terra, otro lado, cenit 10,4
    ("MOD021KM", "MOD03", "A2026078.0155"),   # Terra, frame 0, cenit 31,2
]


def bajar(short, patron, dest):
    import earthaccess
    dest.mkdir(parents=True, exist_ok=True)
    res = earthaccess.search_data(short_name=short, version="6.1", granule_name=f"{short}.{patron}*")
    if not res:
        return None
    paths = earthaccess.download(res[:1], str(dest))
    return Path(paths[0]) if paths else None


def leer_geo(path):
    from pyhdf.SD import SD, SDC
    sd = SD(str(path), SDC.READ)
    lat = sd.select("Latitude").get().astype(np.float64)
    lon = sd.select("Longitude").get().astype(np.float64)
    h = sd.select("Height").get().astype(np.float64)
    sd.end()
    return lat, lon, h


def leer_l1b(path):
    from pyhdf.SD import SD, SDC
    from pipeline.process_modis import _interp_geo
    sd = SD(str(path), SDC.READ)
    latc = sd.select("Latitude").get().astype(np.float32)
    lonc = sd.select("Longitude").get().astype(np.float32)
    ev = sd.select("EV_1KM_Emissive")
    data = ev.get()
    attrs = ev.attributes()
    sd.end()
    # Banda 22 es el indice 2 de EV_1KM_Emissive (bandas 20, 21, 22, 23, ...). Radiancia escalada.
    i22 = 2
    rad = (data[i22].astype(np.float64) - attrs["radiance_offsets"][i22]) * attrs["radiance_scales"][i22]
    rad[data[i22] > 32767] = np.nan
    n_l, n_s = data.shape[1], data.shape[2]
    return _interp_geo(latc, n_l, n_s).astype(np.float64), _interp_geo(lonc, n_l, n_s).astype(np.float64), rad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    import earthaccess
    earthaccess.login(strategy="environment")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    la, lo = comun.vents()["Lascar"]
    filas = []
    for l1b_sn, geo_sn, pat in PASADAS:
        l1b = bajar(l1b_sn, pat, out / "hdf")
        geo = bajar(geo_sn, pat, out / "hdf")
        if l1b is None or geo is None:
            filas.append({"granulo": pat, "error": "no encontrado"})
            continue
        glat, glon, gh = leer_geo(geo)
        ilat, ilon, rad = leer_l1b(l1b)
        d2 = (glat - la) ** 2 + ((glon - lo) * math.cos(math.radians(la))) ** 2
        i, j = np.unravel_index(np.nanargmin(d2), d2.shape)
        dn, de = comun.ne_km(glat[i, j], glon[i, j], ilat[i, j], ilon[i, j])
        # pixel mas brillante en banda 22 a <= 8 km del crater, ubicado con cada geolocalizacion
        dist = np.hypot(*comun.ne_km(la, lo, glat, glon))
        m = np.where(dist <= 8, rad, np.nan)
        k = np.unravel_index(np.nanargmax(m), m.shape)
        filas.append({
            "granulo": f"{l1b_sn}.{pat}", "frame_crater": int(j), "linea_crater": int(i),
            "altura_mxd03_m": float(gh[i, j]),
            "interp_menos_mxd03_dn_km": round(dn, 3), "interp_menos_mxd03_de_km": round(de, 3),
            "pixel_caliente_mxd03_dn_de_km": [round(x, 3) for x in comun.ne_km(la, lo, glat[k], glon[k])],
            "pixel_caliente_interp_dn_de_km": [round(x, 3) for x in comun.ne_km(la, lo, ilat[k], ilon[k])],
        })
        for f in (l1b, geo):
            f.unlink(missing_ok=True)       # no dejar HDF en el runner ni en el artefacto
    json.dump(filas, open(out / "probe_mod03.json", "w", encoding="utf-8"), indent=1)
    for f in filas:
        print(f)


if __name__ == "__main__":
    main()
